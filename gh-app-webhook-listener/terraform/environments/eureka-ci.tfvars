app_name                = "eureka-ci"
github_app_id           = "1671958"
github_private_key_path = "~/.ssh/eureka-ci.pem"  # Path to GitHub App private key

tags = {
  AppName   = "eureka-ci"
  Project   = "GitHub Webhook Listener"
  ManagedBy = "Terraform"
}

lambda_timeout = 30
lambda_memory  = 256