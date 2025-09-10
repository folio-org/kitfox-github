# Eureka CI GitHub App

A lightweight GitHub App that orchestrates check suite workflows for the FOLIO Eureka platform.

## Architecture Overview

The Eureka CI GitHub App acts as a **thin orchestrator** between GitHub webhooks and GitHub Actions workflows. It receives webhook events that GitHub Actions cannot directly handle and triggers appropriate workflows to perform the actual validation logic.

```
GitHub PR → check_suite webhook → AWS Lambda → Trigger Workflow → kitfox-github workflows
                                       ↓
                                  Update Check Run
```

## Key Components

### 1. AWS Infrastructure (Serverless)
- **API Gateway**: Receives GitHub webhooks
- **Lambda Functions**: 
  - `webhook_handler`: Validates webhooks and queues events
  - `check_processor`: Processes events and triggers workflows
- **SQS**: Async message queue for reliable processing
- **S3**: Configuration storage
- **Secrets Manager**: GitHub App credentials

### 2. GitHub App
- **App Name**: Eureka CI
- **Permissions**: 
  - Checks: Read & Write
  - Actions: Read & Write
  - Pull Requests: Read
  - Contents: Read
- **Events**: `check_suite`

### 3. Workflow Orchestration
The app triggers workflows in the `folio-org/kitfox-github` repository that handle all validation logic and update check run status.

## How It Works

### 1. Check Suite Creation
When a PR is created/updated, GitHub automatically creates a check suite and sends a webhook to the app.

### 2. Webhook Processing
```python
# Lambda receives webhook
webhook_handler → validate signature → queue to SQS → return 200 OK
```

### 3. Workflow Triggering
```python
# SQS triggers check processor
check_processor → create check_run → trigger workflow → pass context
```

### 4. Workflow Execution
The triggered workflow handles all business logic and updates the check run status via GitHub API.

## Configuration

### S3 Configuration (`config/workflows.json`)
```json
{
  "kitfox_repo": "folio-org/kitfox-github",
  "check_suite_workflow": ".github/workflows/eureka-ci-check.yml",
  "check_run_settings": {
    "name": "Eureka CI Release Check"
  }
}
```

### Repository Configuration (`release-config.yml`)
Each repository contains its own configuration that workflows use to determine processing rules.

## Deployment

### Prerequisites
1. **AWS Account** with appropriate permissions
2. **Terraform** >= 1.6.1 ([Download](https://www.terraform.io/downloads))
3. **AWS CLI** ([Download](https://aws.amazon.com/cli/))
4. **Python** 3.11 (for Lambda packaging)
5. **GitHub App** created with the following settings:
   - **Webhook URL**: Will be provided after deployment
   - **Webhook Secret**: Generate a secure random string
   - **Permissions**:
     - Checks: Read & Write
     - Actions: Read & Write  
     - Pull Requests: Read
     - Contents: Read
   - **Subscribe to events**: `check_suite`

### Step-by-Step Deployment

#### 1. Prepare GitHub App Credentials
```bash
# Save your GitHub App private key to a file
echo "-----BEGIN RSA PRIVATE KEY-----
YOUR_PRIVATE_KEY_HERE
-----END RSA PRIVATE KEY-----" > github-app-private-key.pem

# Create secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name eureka-ci-github-app-key-dev \
  --secret-string file://github-app-private-key.pem

aws secretsmanager create-secret \
  --name eureka-ci-webhook-secret-dev \
  --secret-string "your-webhook-secret-here"
```

#### 2. Create Terraform Variables
Create `terraform/environments/dev.tfvars`:
```hcl
environment            = "dev"
github_app_id         = "YOUR_APP_ID"
github_webhook_secret = "your-webhook-secret-here"
github_private_key    = "contents-of-your-private-key"
```

#### 3. Package Lambda Functions
```bash
# Create build directory
mkdir -p build

# Package Python code
cd src
zip -r ../build/lambda.zip . -x "*.pyc" -x "__pycache__/*"
cd ..
```

#### 4. Deploy Infrastructure
```bash
# Initialize Terraform
cd terraform
terraform init

# Review planned changes
terraform plan -var-file=environments/dev.tfvars

# Deploy infrastructure
terraform apply -var-file=environments/dev.tfvars

# Note the output webhook URL
terraform output webhook_url
```

#### 5. Upload Configuration
```bash
# Get the bucket name from Terraform
BUCKET=$(cd terraform && terraform output -raw config_bucket_name)

# Upload workflow configuration
aws s3 cp config/workflows.json s3://$BUCKET/config/workflows.json
```

#### 6. Configure GitHub App
1. Go to your GitHub App settings
2. Update the **Webhook URL** with the URL from `terraform output webhook_url`
3. Ensure the webhook secret matches what you configured
4. Save changes

#### 7. Verify Deployment
```bash
# Check Lambda functions
aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'eureka-ci')].[FunctionName,State]"

# View logs
aws logs tail /aws/lambda/eureka-ci-webhook-handler-dev --follow
```

### Environment Variables (Set by Terraform)
- `GITHUB_APP_ID`: GitHub App ID
- `GITHUB_KEY_ARN`: AWS Secrets Manager ARN for private key
- `WEBHOOK_SECRET_ARN`: AWS Secrets Manager ARN for webhook secret
- `CONFIG_BUCKET`: S3 bucket for configuration

## Why This Architecture?

### Separation of Concerns
- **App (Lambda)**: Handles webhooks, manages check runs, triggers workflows
- **Workflows (GitHub Actions)**: Contains all business logic, validation rules

### Benefits
1. **No Logic Duplication**: Validation logic stays in GitHub Actions
2. **Easy Updates**: Change workflows without redeploying Lambda
3. **Visibility**: All processing visible in GitHub Actions UI
4. **Reliability**: SQS ensures webhook processing even during spikes
5. **Security**: Webhook signature validation, least-privilege IAM

### What the App Does NOT Do
- Does NOT implement validation logic
- Does NOT make decisions about what to check
- Does NOT send notifications directly

All business logic remains in GitHub Actions workflows, making the app a stable, rarely-changed component.

## Development

### Local Testing
```bash
# Install dependencies
cd src
pip install -r requirements.txt

# Run tests
python -m pytest tests/
```

### Adding New Workflows
1. Create workflow in `kitfox-github` repository
2. Update `config/workflows.json` if needed
3. No Lambda changes required!

## Monitoring

- **CloudWatch Logs**: `/aws/lambda/eureka-ci-*`
- **SQS DLQ**: Failed messages for debugging
- **GitHub Actions**: Workflow run logs in `kitfox-github`

## Security Considerations

- Webhook signatures validated using HMAC-SHA256
- GitHub App private key stored in AWS Secrets Manager
- IAM roles with least privilege
- All secrets encrypted at rest

## License

Apache 2.0