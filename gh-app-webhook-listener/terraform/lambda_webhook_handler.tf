# --- Webhook Handler Lambda Packaging and Function ---

# Clean and prepare webhook handler build directory
resource "null_resource" "webhook_handler_prep" {
  triggers = {
    src_hash = sha256(join("", [
      fileexists("${local.src_dir}/webhook_handler/handler.py") ? filesha256("${local.src_dir}/webhook_handler/handler.py") : "",
      fileexists("${local.src_dir}/webhook_handler/requirements.txt") ? filesha256("${local.src_dir}/webhook_handler/requirements.txt") : ""
    ]))
  }

  provisioner "local-exec" {
    command = <<-EOT
      rm -rf "${local.build_root}/webhook_handler_build"
      mkdir -p "${local.build_root}/webhook_handler_build"
    EOT
    interpreter = ["bash", "-c"]
  }
}

# Copy webhook handler sources
resource "null_resource" "webhook_handler_copy" {
  depends_on = [null_resource.webhook_handler_prep]

  triggers = {
    src_hash = null_resource.webhook_handler_prep.triggers.src_hash
  }

  provisioner "local-exec" {
    command = <<-EOT
      cp -r "${local.src_dir}/webhook_handler" "${local.build_root}/webhook_handler_build/"
      cp -r "${local.src_dir}/common" "${local.build_root}/webhook_handler_build/"
    EOT
    interpreter = ["bash", "-c"]
  }
}

# Install webhook handler dependencies
resource "null_resource" "webhook_handler_deps" {
  depends_on = [null_resource.webhook_handler_copy]

  triggers = {
    src_hash = null_resource.webhook_handler_prep.triggers.src_hash
  }

  provisioner "local-exec" {
    command = <<-EOT
      if [ -f "${local.src_dir}/webhook_handler/requirements.txt" ]; then
        python -m pip install -r "${local.src_dir}/webhook_handler/requirements.txt" \
          -t "${local.build_root}/webhook_handler_build" \
          --platform manylinux2014_x86_64 \
          --only-binary :all: \
          --upgrade
      fi
    EOT
    interpreter = ["bash", "-c"]
  }
}

# Create webhook handler ZIP
data "archive_file" "webhook_handler" {
  type        = "zip"
  source_dir  = "${local.build_root}/webhook_handler_build"
  output_path = "${local.build_root}/webhook_handler.zip"

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

  depends_on = [null_resource.webhook_handler_deps]
}

# Lambda function for webhook handler
resource "aws_lambda_function" "webhook_handler" {
  filename         = data.archive_file.webhook_handler.output_path
  function_name    = "${var.app_name}-webhook-handler"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "webhook_handler.handler.handler"
  source_code_hash = data.archive_file.webhook_handler.output_base64sha256
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory

  environment {
    variables = {
      GITHUB_APP_ID         = var.github_app_id
      WEBHOOK_SECRET_ARN    = aws_secretsmanager_secret.webhook_secret.arn
      GITHUB_PRIVATE_KEY_ARN = aws_secretsmanager_secret.github_private_key.arn
      SQS_QUEUE_URL        = aws_sqs_queue.check_suite.url
      CHECK_SUITE_QUEUE_URL = aws_sqs_queue.check_suite.url
      CONFIG_BUCKET_NAME   = aws_s3_bucket.app_config.id
      ENVIRONMENT          = terraform.workspace
      LOG_LEVEL           = "INFO"
    }
  }

  tags = var.tags
}

# CloudWatch Log Group for webhook handler
resource "aws_cloudwatch_log_group" "webhook_handler_logs" {
  name              = "/aws/lambda/${aws_lambda_function.webhook_handler.function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.webhook_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.webhook_api.execution_arn}/*/*"
}