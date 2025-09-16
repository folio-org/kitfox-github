# --- Check Processor Lambda Packaging and Function ---

# Clean and prepare check processor build directory
resource "null_resource" "check_processor_prep" {
  triggers = {
    src_hash = sha256(join("", [
      fileexists("${local.src_dir}/check_processor/handler.py") ? filesha256("${local.src_dir}/check_processor/handler.py") : "",
      fileexists("${local.src_dir}/check_processor/requirements.txt") ? filesha256("${local.src_dir}/check_processor/requirements.txt") : ""
    ]))
  }

  provisioner "local-exec" {
    command = <<-EOT
      rm -rf "${local.build_root}/check_processor_build"
      mkdir -p "${local.build_root}/check_processor_build"
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

# Install check processor dependencies
resource "null_resource" "check_processor_deps" {
  depends_on = [null_resource.check_processor_copy]

  triggers = {
    src_hash = null_resource.check_processor_prep.triggers.src_hash
  }

  provisioner "local-exec" {
    command = <<-EOT
      if [ -f "${local.src_dir}/check_processor/requirements.txt" ]; then
        python -m pip install -r "${local.src_dir}/check_processor/requirements.txt" \
          -t "${local.build_root}/check_processor_build" \
          --platform manylinux2014_x86_64 \
          --only-binary :all: \
          --upgrade
      fi
    EOT
    interpreter = ["bash", "-c"]
  }
}

# Create check processor ZIP
data "archive_file" "check_processor" {
  type        = "zip"
  source_dir  = "${local.build_root}/check_processor_build"
  output_path = "${local.build_root}/check_processor.zip"

  excludes = [
    "__pycache__/**",
    "**/*.pyc",
    "**/*.pyd",
    "**/*.dll",
    "**/*.so",
    "**/*.dylib",
    ".git/**",
    ".venv/**",
    "venv/**",
    ".pytest_cache/**"
  ]

  depends_on = [null_resource.check_processor_deps]
}

# Lambda function for check processor
resource "aws_lambda_function" "check_processor" {
  filename         = data.archive_file.check_processor.output_path
  function_name    = "${var.app_name}-check-processor"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "check_processor.handler.handler"
  source_code_hash = data.archive_file.check_processor.output_base64sha256
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory

  environment {
    variables = {
      GITHUB_APP_ID         = var.github_app_id
      GITHUB_PRIVATE_KEY_ARN = aws_secretsmanager_secret.github_private_key.arn
      CONFIG_BUCKET_NAME   = aws_s3_bucket.app_config.id
      ENVIRONMENT          = terraform.workspace
      LOG_LEVEL           = "INFO"
    }
  }

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