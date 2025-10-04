# AWS Secrets Manager secret for webhook secret
resource "aws_secretsmanager_secret" "webhook_secret" {
  name                    = "${var.app_name}-webhook-secret"
  description            = "GitHub webhook secret for signature validation"
  recovery_window_in_days = 0

  tags = var.tags
}

# AWS Secrets Manager secret version for webhook secret
resource "aws_secretsmanager_secret_version" "webhook_secret_version" {
  secret_id     = aws_secretsmanager_secret.webhook_secret.id
  secret_string = var.github_webhook_secret != "" ? var.github_webhook_secret : random_password.webhook_secret.result
}

# Generate random webhook secret if not provided
resource "random_password" "webhook_secret" {
  length  = 32
  special = true
}

# AWS Secrets Manager secret for GitHub App private key
resource "aws_secretsmanager_secret" "github_private_key" {
  name                    = "${var.app_name}-github-private-key"
  description            = "GitHub App private key for authentication"
  recovery_window_in_days = 0

  tags = var.tags
}

# AWS Secrets Manager secret version for GitHub App private key
resource "aws_secretsmanager_secret_version" "github_private_key_version" {
  secret_id     = aws_secretsmanager_secret.github_private_key.id
  secret_string = var.github_private_key != "" ? var.github_private_key : (var.github_private_key_path != "" ? file(var.github_private_key_path) : "")
}

# AWS Secrets Manager secret policy for webhook secret
resource "aws_secretsmanager_secret_policy" "webhook_secret_policy" {
  secret_arn = aws_secretsmanager_secret.webhook_secret.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.lambda_execution_role.arn
        }
        Action   = "secretsmanager:GetSecretValue"
        Resource = "*"
      }
    ]
  })
}

# AWS Secrets Manager secret policy for GitHub private key
resource "aws_secretsmanager_secret_policy" "github_private_key_policy" {
  secret_arn = aws_secretsmanager_secret.github_private_key.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.lambda_execution_role.arn
        }
        Action   = "secretsmanager:GetSecretValue"
        Resource = "*"
      }
    ]
  })
}