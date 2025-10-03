# Terraform Deployment Guide

## Prerequisites

1. Create your own environment configuration file by copying the example:
```bash
cp environments/example.tfvars environments/your-app.tfvars
```

2. Edit `environments/your-app.tfvars` with your specific values:
- Update `app_name` to your application instance name
- Set your `github_app_id`
- Set your `github_installation_id`
- Configure the path to your GitHub App private key
- Optionally configure Route 53 DNS settings

## Passing Sensitive Variables

There are multiple ways to pass sensitive variables to Terraform without storing them in tfvars files:

### Method 1: Environment Variables
```bash
export TF_VAR_github_webhook_secret="your-webhook-secret"
export TF_VAR_github_private_key="$(cat path/to/private-key.pem)"

terraform plan -var-file=environments/your-app.tfvars
terraform apply -var-file=environments/your-app.tfvars
```

### Method 2: Command Line Variables
```bash
terraform plan \
  -var-file=environments/your-app.tfvars \
  -var="github_webhook_secret=your-webhook-secret" \
  -var="github_private_key=$(cat path/to/private-key.pem)"

terraform apply \
  -var-file=environments/your-app.tfvars \
  -var="github_webhook_secret=your-webhook-secret" \
  -var="github_private_key=$(cat path/to/private-key.pem)"
```

### Method 3: Using a Separate Secrets File (gitignored)
Create a file `secrets.auto.tfvars` (which is automatically loaded by Terraform):
```hcl
github_webhook_secret = "your-webhook-secret"
github_private_key    = file("path/to/private-key.pem")
```

Add to `.gitignore`:
```
secrets.auto.tfvars
*.pem
```

Then run:
```bash
terraform plan -var-file=environments/your-app.tfvars
terraform apply -var-file=environments/your-app.tfvars
```

### Method 4: Interactive Input
Simply run terraform without providing the variables, and it will prompt you:
```bash
terraform plan -var-file=environments/your-app.tfvars
# Terraform will prompt for github_webhook_secret and github_private_key
```

## Recommended Approach for CI/CD

For CI/CD pipelines, use environment variables or AWS Secrets Manager:

```bash
# Get secrets from AWS Secrets Manager
WEBHOOK_SECRET=$(aws secretsmanager get-secret-value \
  --secret-id your-app-webhook-secret \
  --query SecretString --output text)

PRIVATE_KEY=$(aws secretsmanager get-secret-value \
  --secret-id your-app-github-private-key \
  --query SecretString --output text)

# Apply with variables
terraform apply \
  -var-file=environments/your-app.tfvars \
  -var="github_webhook_secret=$WEBHOOK_SECRET" \
  -var="github_private_key=$PRIVATE_KEY" \
  -auto-approve
```

## Route 53 DNS Configuration (Optional)

If you want to use a custom domain for your webhook endpoint, you can enable Route 53 integration:

### 1. Enable Route 53 in your configuration

Add the following to your `environments/your-app.tfvars`:

```hcl
# Route 53 DNS configuration (optional)
enable_route53      = true
route53_zone_name   = "example.com"    # Your existing hosted zone
route53_record_name = "webhooks"       # Creates webhooks.example.com
```

### 2. Deploy with Route 53 enabled

```bash
terraform apply \
  -var-file=environments/your-app.tfvars \
  -var="github_webhook_secret=$WEBHOOK_SECRET"
```

### 3. Update your GitHub App

Once deployed, update your GitHub App webhook URL to use the custom domain:
- Webhook URL: `https://webhooks.example.com/webhook`

The DNS record will automatically point to your API Gateway endpoint.

### Important Notes

- **Existing Zone Required**: Route 53 integration requires an existing hosted zone in your AWS account
- **Record Type**: Creates a CNAME record pointing to your API Gateway endpoint
- **DNS Propagation**: DNS changes may take a few minutes to propagate
- **TTL**: The TTL is set to 300 seconds (5 minutes) by default

### Example with Custom Domain

```hcl
# environments/my-app.tfvars
app_name                = "my-app"
github_app_id           = "123456"
github_installation_id  = "567890"
github_private_key_path = "~/.ssh/my-app.pem"

# Enable Route 53 DNS
enable_route53      = true
route53_zone_name   = "ci.folio.org"
route53_record_name = "my-app"  # Creates my-app.ci.folio.org

tags = {
  AppName   = "my-app"
  Project   = "GitHub Webhook Listener"
  ManagedBy = "Terraform"
}
```

## Example Commands for Testing

```bash
# Initialize
terraform init

# Plan with test values
terraform plan \
  -var-file=environments/your-app.tfvars \
  -var="github_webhook_secret=test-secret" \
  -var="github_private_key=test-key"

# Apply (production)
terraform apply \
  -var-file=environments/your-app.tfvars \
  -var="github_webhook_secret=$REAL_WEBHOOK_SECRET" \
  -var="github_private_key=$REAL_PRIVATE_KEY"

# Apply with Route 53 enabled
terraform apply \
  -var-file=environments/your-app.tfvars \
  -var="github_webhook_secret=$REAL_WEBHOOK_SECRET" \
  -var="github_private_key=$REAL_PRIVATE_KEY" \
  -var="enable_route53=true" \
  -var="route53_zone_name=example.com" \
  -var="route53_record_name=webhooks"
```

## Note on Environment Files

The `environments/` directory contains:
- `example.tfvars` - Template file to copy for your own configuration
- `eureka-ci.tfvars` - Example production configuration for Eureka CI
- `github_events_config.json` - Event-to-workflow mapping configuration

Always create your own `.tfvars` file based on `example.tfvars` for your specific deployment.
