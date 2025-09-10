resource "aws_iam_role" "lambda_execution" {
  name = "eureka-ci-lambda-execution-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = merge(var.tags, {
    Name        = "eureka-ci-lambda-execution-${var.environment}"
    Environment = var.environment
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_execution.name
}

resource "aws_iam_role_policy" "lambda_sqs" {
  name = "eureka-ci-lambda-sqs-${var.environment}"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          aws_sqs_queue.check_suite.arn,
          aws_sqs_queue.check_suite_dlq.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_s3" {
  name = "eureka-ci-lambda-s3-${var.environment}"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.eureka_ci_config.arn,
          "${aws_s3_bucket.eureka_ci_config.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_secrets" {
  name = "eureka-ci-lambda-secrets-${var.environment}"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.github_app_key.arn,
          aws_secretsmanager_secret.github_webhook_secret.arn
        ]
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "webhook_handler" {
  name              = "/aws/lambda/eureka-ci-webhook-handler-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name        = "eureka-ci-webhook-handler-logs-${var.environment}"
    Environment = var.environment
  })
}

resource "aws_cloudwatch_log_group" "check_processor" {
  name              = "/aws/lambda/eureka-ci-check-processor-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name        = "eureka-ci-check-processor-logs-${var.environment}"
    Environment = var.environment
  })
}

data "archive_file" "lambda_code" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/../build/lambda.zip"
}

resource "aws_lambda_function" "webhook_handler" {
  filename      = data.archive_file.lambda_code.output_path
  function_name = "eureka-ci-webhook-handler-${var.environment}"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "handlers.webhook_handler.handler"
  runtime       = "python3.11"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory

  source_code_hash = data.archive_file.lambda_code.output_base64sha256

  environment {
    variables = {
      ENVIRONMENT          = var.environment
      SQS_QUEUE_URL        = aws_sqs_queue.check_suite.url
      CONFIG_BUCKET        = aws_s3_bucket.eureka_ci_config.id
      GITHUB_APP_ID        = var.github_app_id
      WEBHOOK_SECRET_ARN   = aws_secretsmanager_secret.github_webhook_secret.arn
    }
  }

  tracing_config {
    mode = "Active"
  }

  depends_on = [
    aws_cloudwatch_log_group.webhook_handler
  ]

  tags = merge(var.tags, {
    Name        = "eureka-ci-webhook-handler-${var.environment}"
    Environment = var.environment
  })
}

resource "aws_lambda_function" "check_processor" {
  filename      = data.archive_file.lambda_code.output_path
  function_name = "eureka-ci-check-processor-${var.environment}"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "handlers.check_processor.handler"
  runtime       = "python3.11"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory

  source_code_hash = data.archive_file.lambda_code.output_base64sha256

  environment {
    variables = {
      ENVIRONMENT        = var.environment
      CONFIG_BUCKET      = aws_s3_bucket.eureka_ci_config.id
      GITHUB_APP_ID      = var.github_app_id
      GITHUB_KEY_ARN     = aws_secretsmanager_secret.github_app_key.arn
    }
  }

  tracing_config {
    mode = "Active"
  }

  depends_on = [
    aws_cloudwatch_log_group.check_processor
  ]

  tags = merge(var.tags, {
    Name        = "eureka-ci-check-processor-${var.environment}"
    Environment = var.environment
  })
}

resource "aws_lambda_event_source_mapping" "sqs_to_check_processor" {
  event_source_arn = aws_sqs_queue.check_suite.arn
  function_name    = aws_lambda_function.check_processor.arn
  batch_size       = 1
}