app_name                = "my-github-app"  # Your application instance name
github_app_id           = "123456"  # Your GitHub App ID
github_private_key_path = "../keys/github-app.pem"  # Path to your GitHub App private key

tags = {
  AppName   = "my-github-app"
  Project   = "GitHub Webhook Listener"
  ManagedBy = "Terraform"
}

lambda_timeout = 30
lambda_memory  = 256