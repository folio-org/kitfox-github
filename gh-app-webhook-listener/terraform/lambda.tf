# IAM role for Lambda functions
resource "aws_iam_role" "lambda_execution_role" {
  name = "${var.app_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM policy for Lambda functions
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.app_name}-lambda-policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.check_suite.arn
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.webhook_secret.arn,
          aws_secretsmanager_secret.github_private_key.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.app_config.arn,
          "${aws_s3_bucket.app_config.arn}/*"
        ]
      }
    ]
  })
}

# Data sources
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# Create deployment package
data "archive_file" "lambda_package" {
  type        = "zip"
  source_dir  = "../src"
  output_path = "../build/lambda_package.zip"
}

# Lambda function for webhook handler
resource "aws_lambda_function" "webhook_handler" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = "${var.app_name}-webhook-handler"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "handlers.webhook_handler.handler"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
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

# Lambda function for check processor
resource "aws_lambda_function" "check_processor" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = "${var.app_name}-check-processor"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "handlers.check_processor.handler"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
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

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "webhook_handler_logs" {
  name              = "/aws/lambda/${aws_lambda_function.webhook_handler.function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "check_processor_logs" {
  name              = "/aws/lambda/${aws_lambda_function.check_processor.function_name}"
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

# Lambda event source mapping for SQS
resource "aws_lambda_event_source_mapping" "check_processor_sqs" {
  event_source_arn                   = aws_sqs_queue.check_suite.arn
  function_name                      = aws_lambda_function.check_processor.arn
  batch_size                         = 1
  maximum_batching_window_in_seconds = 0
}