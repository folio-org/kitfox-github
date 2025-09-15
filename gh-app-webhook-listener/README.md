# GitHub Application Webhook Listener

A generic, lightweight GitHub App webhook listener that orchestrates GitHub Actions workflows. This serverless application acts as a bridge between GitHub webhooks and GitHub Actions, enabling workflows to respond to events that GitHub Actions cannot directly handle.

## Architecture Overview

This webhook listener acts as a **thin orchestrator** between GitHub webhooks and GitHub Actions workflows. It receives webhook events and triggers appropriate workflows to perform the actual business logic.

```
GitHub Event → Webhook → AWS Lambda → Trigger Workflow → GitHub Actions
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

### 2. GitHub App Configuration
- **Permissions Required**:
  - Checks: Read & Write
  - Actions: Read & Write
  - Pull Requests: Read
  - Contents: Read
- **Events**: Configurable (e.g., `check_suite`, `pull_request`, etc.)

### 3. Workflow Orchestration
The app triggers workflows in your specified repository to handle all business logic and update check run status.

## How It Works

### 1. Event Reception
When a GitHub event occurs (e.g., PR created/updated), GitHub sends a webhook to the configured endpoint.

### 2. Webhook Processing
```python
# Lambda receives webhook
webhook_handler → validate signature → queue to SQS → return 200 OK
```

### 3. Workflow Triggering
```python
# Process from SQS
check_processor → create check run → trigger workflow → monitor status
```

### 4. Status Updates
The triggered workflow updates the check run status as it progresses.

## Installation

### Prerequisites
- AWS Account with appropriate permissions
- GitHub App created and configured
- Terraform installed (>= 1.0)
- Python 3.11+ for local development

### Quick Start

1. **Clone the repository**
```bash
git clone <repository>
cd gh-app-webhook-listener
```

2. **Install dependencies**
```bash
pip install -r src/requirements.txt
```

3. **Configure your deployment**
```bash
cp terraform/environments/example.tfvars terraform/environments/your-app.tfvars
# Edit your-app.tfvars with your configuration
```

4. **Deploy with Terraform**
```bash
cd terraform
terraform init
terraform plan -var-file=environments/your-app.tfvars \
               -var="github_webhook_secret=your-secret"
terraform apply -var-file=environments/your-app.tfvars \
                -var="github_webhook_secret=your-secret"
```

5. **Configure GitHub App**
- Update webhook URL with the API Gateway endpoint from Terraform output
- Set webhook secret to match your configuration

## Configuration

### Terraform Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `app_name` | Your application instance name | `my-app`, `folio-app` |
| `github_app_id` | GitHub App ID | `123456` |
| `github_private_key_path` | Path to GitHub App private key | `../keys/github-app.pem` |
| `github_webhook_secret` | Webhook secret (pass via CLI) | `your-secret-here` |

### Workflow Configuration

Configure which workflows to trigger in `config/workflows.json`:

```json
{
  "workflows": [
    {
      "name": "your-workflow-name",
      "file": ".github/workflows/your-workflow.yml",
      "description": "Description of what this workflow does",
      "enabled": true,
      "triggers": ["pull_request", "check_suite"]
    }
  ]
}
```

## Development

### Local Testing
```bash
python tests/test_local.py
```

### Package Lambda Functions
```bash
python scripts/package_lambda.py
```

### Project Structure
```
gh-app-webhook-listener/
├── src/
│   ├── handlers/         # Lambda function handlers
│   ├── services/         # Business logic services
│   └── utils/           # Utility functions
├── terraform/           # Infrastructure as code
│   ├── environments/    # Environment-specific configs
│   └── *.tf            # Terraform resources
├── config/             # Application configuration
└── scripts/           # Build and deployment scripts
```

## Monitoring

- **CloudWatch Logs**: All Lambda executions are logged
- **SQS Metrics**: Monitor queue depth and processing rate
- **API Gateway Metrics**: Track webhook delivery success

## Security

- Webhook signatures are validated using HMAC-SHA256
- GitHub App private key stored in AWS Secrets Manager
- All sensitive data encrypted at rest and in transit
- IAM roles follow least privilege principle

## Customization

This is a generic webhook listener that can be adapted for various use cases:

1. **Different GitHub Events**: Modify the webhook handler to process different event types
2. **Custom Workflows**: Update the workflow orchestrator to trigger your specific workflows
3. **Additional Processing**: Add custom logic in the services layer
4. **Multiple Apps**: Deploy multiple instances with different `app_name` values

## Examples

### Deploy for Your Application

1. Create a new tfvars file:
```hcl
# terraform/environments/my-app.tfvars
app_name      = "my-app"
github_app_id = "987654"
github_private_key_path = "../keys/my-app.pem"

tags = {
  AppName   = "my-app"
  Project   = "GitHub Webhook Listener"
  ManagedBy = "Terraform"
}
```

2. Deploy:
```bash
terraform apply -var-file=environments/my-app.tfvars \
                -var="github_webhook_secret=$SECRET"
```

### Multiple Environment Deployment

You can deploy multiple instances for different environments or applications:

```bash
# Development environment
terraform workspace new dev
terraform apply -var-file=environments/dev-app.tfvars

# Production environment
terraform workspace new prod
terraform apply -var-file=environments/prod-app.tfvars
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python tests/test_local.py`
5. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions, please open an issue in the GitHub repository.