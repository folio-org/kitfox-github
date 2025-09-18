app_name                = "my-github-app"  # Your application instance name
github_app_id           = "123456"  # Your GitHub App ID
github_installation_id  = "567890"  # Your GitHub App Installation ID (on a specific org or user account)
github_private_key_path = "../keys/github-app.pem"  # Path to your GitHub App private key

tags = {
  AppName   = "my-github-app"
  Project   = "GitHub Webhook Listener"
  ManagedBy = "Terraform"
}

lambda_timeout = 30
lambda_memory  = 256

# Route 53 DNS configuration (optional)
enable_route53      = false                # Change to true to create a Route 53 DNS record
route53_zone_name   = "example.com"        # Your existing hosted zone domain
route53_record_name = "webhooks"           # Will create webhooks.example.com