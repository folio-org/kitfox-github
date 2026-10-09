app_name                = "my-github-app"          # Your application instance name
github_app_id           = "123456"                 # Your GitHub App ID
github_installation_id  = "567890"                 # Your GitHub App Installation ID (on a specific org or user account)
github_private_key_path = "../keys/github-app.pem" # Path to your GitHub App private key

tags = {
  AppName   = "my-github-app"
  Project   = "GitHub Webhook Listener"
  ManagedBy = "Terraform"
}

lambda_timeout = 30
lambda_memory  = 256

# Route 53 DNS configuration (optional)
enable_route53      = false         # Change to true to create a Route 53 DNS record
route53_zone_name   = "example.com" # Your existing hosted zone domain
route53_record_name = "webhooks"    # Will create webhooks.example.com

# Credentials in SSM Parameter Store instead of Secrets Manager (optional).
# With a value (github_private_key_path above, github_webhook_secret) the stack writes the parameter;
# without one the parameter must already exist. The Lambdas read the SecureString parameters at runtime.
# credentials_store                    = "ssm"
# github_private_key_ssm_parameter     = "/my-github-app/github-app-private-key"  # default: /<app_name>/github-app-private-key
# github_webhook_secret_ssm_parameter  = "/my-github-app/webhook-secret"          # default: /<app_name>/webhook-secret
# github_app_id_ssm_parameter          = "/my-github-app/github-app-id"           # instead of github_app_id
# github_installation_id_ssm_parameter = "/my-github-app/github-installation-id"  # instead of github_installation_id
# ssm_kms_key_arn                      = ""                                       # empty = alias/aws/ssm

# Existing IAM roles (optional)
# lambda_execution_role_arn       = "arn:aws:iam::123456789012:role/my-github-app-lambda"
# api_gateway_cloudwatch_role_arn = "arn:aws:iam::123456789012:role/my-github-app-apigw-logs"
# manage_api_gateway_account      = false  # account-level API Gateway logging setting is managed elsewhere