environment          = "dev"
github_app_id        = "1141251"  # Eureka CI App ID
webhook_secret_name  = "eureka-ci-webhook-secret"
github_key_name      = "eureka-ci-github-key"
s3_config_bucket     = "eureka-ci-config-dev"
allowed_repositories = [
  "folio-org/*"
]

tags = {
  Environment = "dev"
  Project     = "EurekaCI"
  ManagedBy   = "Terraform"
}

lambda_timeout = 30
lambda_memory  = 256