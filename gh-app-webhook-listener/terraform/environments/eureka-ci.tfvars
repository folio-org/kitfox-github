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

# Route 53 DNS configuration (optional)
enable_route53      = true                # Change to true to create a Route 53 DNS record
route53_zone_name   = "ci.folio.org"       # Your existing hosted zone domain
route53_record_name = "eureka-ci"    # Will create eureka-webhooks.ci.folio.org