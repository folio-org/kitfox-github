resource "aws_secretsmanager_secret" "github_app_key" {
  name                    = "eureka-ci-github-app-key-${var.environment}"
  description             = "GitHub App private key for Eureka CI"
  recovery_window_in_days = 7

  tags = merge(var.tags, {
    Name        = "eureka-ci-github-app-key-${var.environment}"
    Environment = var.environment
  })
}

resource "aws_secretsmanager_secret_version" "github_app_key" {
  secret_id     = aws_secretsmanager_secret.github_app_key.id
  secret_string = var.github_private_key
}

resource "aws_secretsmanager_secret" "github_webhook_secret" {
  name                    = "eureka-ci-webhook-secret-${var.environment}"
  description             = "GitHub webhook secret for signature validation"
  recovery_window_in_days = 7

  tags = merge(var.tags, {
    Name        = "eureka-ci-webhook-secret-${var.environment}"
    Environment = var.environment
  })
}

resource "aws_secretsmanager_secret_version" "github_webhook_secret" {
  secret_id     = aws_secretsmanager_secret.github_webhook_secret.id
  secret_string = var.github_webhook_secret
}