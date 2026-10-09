# AWS Secrets Manager secret for webhook secret
resource "aws_secretsmanager_secret" "webhook_secret" {
  count = local.use_secrets_manager ? 1 : 0

  name                    = "${var.app_name}-webhook-secret"
  description             = "GitHub webhook secret for signature validation"
  recovery_window_in_days = 0

  tags = var.tags
}

# AWS Secrets Manager secret version for webhook secret
resource "aws_secretsmanager_secret_version" "webhook_secret_version" {
  count = local.use_secrets_manager ? 1 : 0

  secret_id     = aws_secretsmanager_secret.webhook_secret[0].id
  secret_string = var.github_webhook_secret != "" ? var.github_webhook_secret : random_password.webhook_secret[0].result
}

# Generate random webhook secret if not provided
resource "random_password" "webhook_secret" {
  count = local.use_secrets_manager ? 1 : 0

  length  = 32
  special = true
}

# AWS Secrets Manager secret for GitHub App private key
resource "aws_secretsmanager_secret" "github_private_key" {
  count = local.use_secrets_manager ? 1 : 0

  name                    = "${var.app_name}-github-private-key"
  description             = "GitHub App private key for authentication"
  recovery_window_in_days = 0

  tags = var.tags
}

# AWS Secrets Manager secret version for GitHub App private key
resource "aws_secretsmanager_secret_version" "github_private_key_version" {
  count = local.use_secrets_manager ? 1 : 0

  secret_id     = aws_secretsmanager_secret.github_private_key[0].id
  secret_string = local.github_private_key
}

# AWS Secrets Manager secret policy for webhook secret
resource "aws_secretsmanager_secret_policy" "webhook_secret_policy" {
  count = local.use_secrets_manager ? 1 : 0

  secret_arn = aws_secretsmanager_secret.webhook_secret[0].arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = local.lambda_role_arn
        }
        Action   = "secretsmanager:GetSecretValue"
        Resource = "*"
      }
    ]
  })
}

# AWS Secrets Manager secret policy for GitHub private key
resource "aws_secretsmanager_secret_policy" "github_private_key_policy" {
  count = local.use_secrets_manager ? 1 : 0

  secret_arn = aws_secretsmanager_secret.github_private_key[0].arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = local.lambda_role_arn
        }
        Action   = "secretsmanager:GetSecretValue"
        Resource = "*"
      }
    ]
  })
}
