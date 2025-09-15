# Terraform Deployment Guide

## Prerequisites

1. Create your own environment configuration file by copying the example:
```bash
cp environments/example.tfvars environments/your-app.tfvars
```

2. Edit `environments/your-app.tfvars` with your specific values:
- Update `app_name` to your application instance name
- Set your `github_app_id`
- Configure the path to your GitHub App private key

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
```

## Note on Environment Files

The `environments/` directory contains:
- `example.tfvars` - Template file to copy for your own configuration

Always create your own `.tfvars` file based on `example.tfvars` for your specific deployment.