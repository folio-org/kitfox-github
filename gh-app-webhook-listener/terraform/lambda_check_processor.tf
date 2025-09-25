# --- Check Processor Lambda Packaging and Function ---

locals {
  lambda_runtime = "python3.12"
  lambda_arch    = "x86_64" # change to "arm64" if using Graviton
  pip_platform   = local.lambda_arch == "arm64" ? "manylinux_2_17_aarch64" : "manylinux_2_17_x86_64"
  py_ver         = "312"
  py_abi         = "cp312"
  python_bin     = "python"
}

# Clean and prepare check processor build directory
resource "null_resource" "check_processor_prep" {
  triggers = {
    src_hash = sha256(join("", [
      fileexists("${local.src_dir}/check_processor/handler.py") ? filesha256("${local.src_dir}/check_processor/handler.py") : "",
      fileexists("${local.src_dir}/check_processor/requirements.txt") ? filesha256("${local.src_dir}/check_processor/requirements.txt") : "",
      sha256(join("", [for f in fileset("${local.src_dir}/common", "*.py") : filesha256("${local.src_dir}/common/${f}")])),
      local.lambda_runtime,
      local.lambda_arch
    ]))
  }

  provisioner "local-exec" {
    command = <<-EOT
      rm -rf "${local.build_root}/check_processor_build" "${local.build_root}/check_processor_wheels"
      mkdir -p "${local.build_root}/check_processor_build" "${local.build_root}/check_processor_wheels"
    EOT
    interpreter = ["bash", "-c"]
  }
}

# Copy check processor sources
resource "null_resource" "check_processor_copy" {
  depends_on = [null_resource.check_processor_prep]

  triggers = {
    src_hash = null_resource.check_processor_prep.triggers.src_hash
  }

  provisioner "local-exec" {
    command = <<-EOT
      cp -r "${local.src_dir}/check_processor" "${local.build_root}/check_processor_build/"
      cp -r "${local.src_dir}/common" "${local.build_root}/check_processor_build/"
    EOT
    interpreter = ["bash", "-c"]
  }
}

# Copy configuration file if not using S3
resource "null_resource" "check_processor_config_copy" {
  count = var.github_events_config_s3_enabled ? 0 : 1
  depends_on = [null_resource.check_processor_copy]

  triggers = {
    src_hash = null_resource.check_processor_prep.triggers.src_hash
    config_hash = filesha256(var.github_events_config_file)
  }

  provisioner "local-exec" {
    command = <<-EOT
      mkdir -p "${local.build_root}/check_processor_build/config"
      cp "${var.github_events_config_file}" "${local.build_root}/check_processor_build/config/github_events_config.json"
    EOT
    interpreter = ["bash", "-c"]
  }
}

# Install check processor dependencies
resource "null_resource" "check_processor_deps" {
  depends_on = [null_resource.check_processor_copy]

  triggers = {
    src_hash = null_resource.check_processor_prep.triggers.src_hash
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -euo pipefail
      export MSYS2_ARG_CONV_EXCL="*"

      WHEEL_DIR="${local.build_root}/check_processor_wheels"
      BUILD_DIR="${local.build_root}/check_processor_build"
      REQ_FILE="${local.src_dir}/check_processor/requirements.txt"

      if [ -f "$REQ_FILE" ]; then
        ${local.python_bin} -m pip download --only-binary=:all: \
          --platform ${local.pip_platform} \
          --python-version ${local.py_ver} \
          --implementation cp \
          --abi ${local.py_abi} \
          -d "$WHEEL_DIR" -r "$REQ_FILE"
      fi

      ${local.python_bin} - "$WHEEL_DIR" "$BUILD_DIR" <<'PY'
import sys, os, glob, zipfile
wheel_dir, build_dir = sys.argv[1], sys.argv[2]
os.makedirs(build_dir, exist_ok=True)
for whl in glob.glob(os.path.join(wheel_dir, '*.whl')):
    with zipfile.ZipFile(whl) as z:
        z.extractall(build_dir)
PY
    EOT
    interpreter = ["bash", "-c"]
  }
}

# Create check processor ZIP using null_resource
resource "null_resource" "check_processor_zip" {
  depends_on = [
    null_resource.check_processor_deps,
    null_resource.check_processor_config_copy
  ]

  triggers = {
    src_hash = null_resource.check_processor_prep.triggers.src_hash
  }

  provisioner "local-exec" {
    command = <<-EOT
      if [ ! -d "${local.build_root}/check_processor_build" ]; then
        echo "Build directory missing, creating placeholder..."
        exit 0
      fi

      cd "${local.build_root}/check_processor_build" && \
      zip -r "../check_processor.zip" . \
        -x "__pycache__/*" \
        -x "*.pyc" \
        -x "*.pyd" \
        -x "*.dll" \
        -x "*.dylib" \
        -x ".git/*" \
        -x ".venv/*" \
        -x "venv/*" \
        -x ".pytest_cache/*"
    EOT
    interpreter = ["bash", "-c"]
  }
}

# Lambda function for check processor
resource "aws_lambda_function" "check_processor" {
  filename          = "${local.build_root}/check_processor.zip"
  function_name     = "${var.app_name}-check-processor"
  role              = aws_iam_role.lambda_execution_role.arn
  handler           = "check_processor.handler.handler"
  source_code_hash  = null_resource.check_processor_zip.triggers.src_hash
  runtime           = local.lambda_runtime
  architectures     = [local.lambda_arch]
  timeout           = var.lambda_timeout
  memory_size       = var.lambda_memory

  environment {
    variables = {
      GITHUB_APP_ID           = var.github_app_id
      GITHUB_INSTALLATION_ID  = var.github_installation_id
      GITHUB_PRIVATE_KEY_ARN  = aws_secretsmanager_secret.github_private_key.arn
      CONFIG_BUCKET_NAME      = var.github_events_config_s3_enabled ? aws_s3_bucket.app_config.id : ""
      CONFIG_FILE_KEY         = var.github_events_config_s3_enabled ? "github_events_config.json" : ""
      LOCAL_CONFIG_PATH       = var.github_events_config_s3_enabled ? "" : "/var/task/config/github_events_config.json"
      ENVIRONMENT             = terraform.workspace
      LOG_LEVEL               = "INFO"
    }
  }

  depends_on = [null_resource.check_processor_zip]

  tags = var.tags
}

# CloudWatch Log Group for check processor
resource "aws_cloudwatch_log_group" "check_processor_logs" {
  name              = "/aws/lambda/${aws_lambda_function.check_processor.function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# Lambda event source mapping for SQS
resource "aws_lambda_event_source_mapping" "check_processor_sqs" {
  event_source_arn                   = aws_sqs_queue.check_suite.arn
  function_name                      = aws_lambda_function.check_processor.arn
  batch_size                         = 1
  maximum_batching_window_in_seconds = 0
}