# --- Shared Lambda Resources ---

# Build paths (used by both Lambda functions)
locals {
  base_dir   = abspath("${path.module}/..")
  src_dir    = "${local.base_dir}/src"
  build_root = "${local.base_dir}/build"
}

# IAM role for Lambda functions
resource "aws_iam_role" "lambda_execution_role" {
  count = local.create_lambda_role ? 1 : 0

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
  count = local.create_lambda_role ? 1 : 0

  name = "${var.app_name}-lambda-policy"
  role = aws_iam_role.lambda_execution_role[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [for statement in [
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
      local.use_secrets_manager ? {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          one(aws_secretsmanager_secret.webhook_secret[*].arn),
          one(aws_secretsmanager_secret.github_private_key[*].arn)
        ]
      } : null,
      local.use_secrets_manager ? null : {
        Effect   = "Allow"
        Action   = ["ssm:GetParameter"]
        Resource = local.credential_ssm_parameter_arns
      },
      !local.use_secrets_manager && var.ssm_kms_key_arn != "" ? {
        Effect   = "Allow"
        Action   = ["kms:Decrypt"]
        Resource = var.ssm_kms_key_arn
      } : null,
      !local.use_secrets_manager && var.ssm_kms_key_arn == "" ? {
        Effect   = "Allow"
        Action   = ["kms:Decrypt"]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = "ssm.${var.aws_region}.amazonaws.com"
          }
        }
      } : null,
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
    ] : statement if statement != null]
  })
}

# Data sources
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}