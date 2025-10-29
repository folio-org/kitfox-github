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
- **S3**: Configuration storage (optional for event mappings)
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

2. **Configure your deployment**
```bash
cp terraform/environments/example.tfvars terraform/environments/your-app.tfvars
# Edit your-app.tfvars with your configuration
```

3. **Deploy with Terraform**
```bash
cd terraform
terraform init
terraform plan -var-file=environments/your-app.tfvars \
               -var="github_webhook_secret=your-secret"
terraform apply -var-file=environments/your-app.tfvars \
                -var="github_webhook_secret=your-secret"
```

Note: Terraform will automatically package the Lambda functions during deployment.

4. **Configure GitHub App**
- Update webhook URL with the API Gateway endpoint from Terraform output
- Set webhook secret to match your configuration

## Configuration

### Terraform Variables

#### Core Variables
| Variable                  | Description                    | Example                 |
|---------------------------|--------------------------------|-------------------------|
| `app_name`                | Your application instance name | `my-app`, `eureka-ci`   |
| `github_app_id`           | GitHub App ID                  | `123456`                |
| `github_installation_id`  | GitHub App Installation ID     | `567890`                |
| `github_private_key_path` | Path to GitHub App private key | `~/.ssh/github-app.pem` |
| `github_webhook_secret`   | Webhook secret (pass via CLI)  | `your-secret-here`      |

#### GitHub Events Configuration Variables
| Variable                          | Description                                   | Default                                    |
|-----------------------------------|-----------------------------------------------|--------------------------------------------|
| `github_events_config_file`       | Path to events configuration JSON             | `./environments/github_events_config.json` |
| `github_events_config_s3_enabled` | Upload config to S3 (vs bundling with Lambda) | `true`                                     |

#### Route 53 DNS Configuration (Optional)
| Variable              | Description                          | Example           | Default  |
|-----------------------|--------------------------------------|-------------------|----------|
| `enable_route53`      | Enable Route 53 DNS record creation  | `true` or `false` | `false`  |
| `route53_zone_name`   | Existing Route 53 hosted zone domain | `ci.folio.org`    | `""`     |
| `route53_record_name` | DNS record name to create            | `eureka-ci`       | `""`     |

When Route 53 is enabled, it will create a CNAME record in your existing hosted zone. For example:
- Zone: `ci.folio.org`
- Record: `eureka-ci`
- Result: `eureka-ci.ci.folio.org` → Your API Gateway endpoint

### GitHub Events Configuration

Configure event-to-workflow mappings in your events configuration file (e.g., `terraform/environments/github_events_config.json`):

```json
{
  "version": "1.0.0",
  "description": "GitHub events to workflow mapping configuration",
  "event_mappings": [
    {
      "event_type": "check_suite",
      "actions": ["requested", "rerequested"],
      "repository_patterns": [
        {
          "owner": "folio-org",
          "repository": "app-*",
          "branches": "*",
          "workflows": [
            {
              "owner": "{owner}",
              "repository": "{repository}",
              "workflow_file": "pr-check.yml",
              "ref": "master",
              "inputs": {
                "pr_number": "{pr_number}",
                "head_sha": "{head_sha}"
              }
            }
          ]
        }
      ]
    },
    {
      "event_type": "pull_request",
      "actions": ["opened", "reopened", "synchronize"],
      "repository_patterns": [
        {
          "owner": "folio-org",
          "repository": "app-*",
          "branches": "*",
          "workflows": [
            {
              "owner": "{owner}",
              "repository": "{repository}",
              "workflow_file": "pr-check.yml",
              "ref": "master",
              "inputs": {
                "pr_number": "{pr_number}",
                "head_sha": "{head_sha}"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

## Development

### Local Testing
```bash
python tests/test_local.py
```

### Lambda Packaging

#### Method 1: Terraform-native packaging (Recommended)
Terraform automatically packages Lambda functions during deployment using the `archive_file` data source and `null_resource` provisioners. No manual steps required.

#### Method 2: Manual packaging
```bash
python scripts/package_lambda.py
```
This creates optimized packages for each Lambda function in the `build/` directory.

### Project Structure
```
gh-app-webhook-listener/
├── src/
│   ├── webhook_handler/   # Webhook handler Lambda
│   │   ├── handler.py     # Main handler function
│   │   └── requirements.txt
│   ├── check_processor/   # Check processor Lambda
│   │   ├── handler.py     # Main handler function
│   │   └── requirements.txt
│   └── common/           # Shared utilities
│       ├── github_client.py      # GitHub API client
│       └── workflow_trigger.py   # Workflow triggering logic
├── terraform/            # Infrastructure as code
│   ├── environments/     # Environment-specific configs
│   │   ├── example.tfvars
│   │   ├── eureka-ci.tfvars
│   │   └── github_events_config.json
│   ├── lambda.tf        # Shared Lambda resources
│   ├── lambda_webhook_handler.tf  # Webhook handler config
│   ├── lambda_check_processor.tf  # Check processor config
│   ├── api_gateway.tf   # API Gateway configuration
│   ├── sqs.tf           # SQS queue configuration
│   ├── s3.tf            # S3 bucket for config storage
│   ├── secrets.tf       # Secrets Manager configuration
│   ├── route53.tf       # Route 53 DNS configuration
│   └── *.tf             # Other Terraform resources
├── config/              # Application configuration templates
│   └── github_events_config.example.json
├── scripts/             # Build and deployment scripts
│   └── package_lambda.py # Manual packaging script
└── build/               # Generated Lambda packages (gitignored)
```

### Lambda Function Architecture

The Lambda functions are separated for optimal performance:

1. **webhook_handler**: Lightweight function that validates incoming webhooks
   - Dependencies: boto3 only
   - Responsibilities: Webhook signature validation, SQS queuing

2. **check_processor**: Processes events and interacts with GitHub API
   - Dependencies: boto3, requests, PyJWT
   - Responsibilities: GitHub API calls, workflow triggering, check run management

3. **common**: Shared utilities used by both functions
   - `github_client.py`: GitHub API client with JWT authentication
   - `workflow_trigger.py`: Workflow dispatch logic and event mapping

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

1. **Different GitHub Events**: Modify the events configuration to process different event types
2. **Custom Workflows**: Update the event mappings to trigger your specific workflows
3. **Additional Processing**: Add custom logic in the Lambda functions
4. **Multiple Apps**: Deploy multiple instances with different `app_name` values

## Examples

### Deploy for Your Application

1. Create a new tfvars file:
```hcl
# terraform/environments/my-app.tfvars
app_name                = "my-app"
github_app_id           = "987654"
github_installation_id  = "123456"
github_private_key_path = "~/.ssh/my-app.pem"

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

### Deploy with Custom Domain (Route 53)

To use a custom domain for your webhook endpoint:

1. Update your tfvars file:
```hcl
# Enable Route 53 DNS
enable_route53      = true
route53_zone_name   = "ci.folio.org"       # Your existing hosted zone
route53_record_name = "my-app"             # Creates my-app.ci.folio.org
```

2. Deploy:
```bash
terraform apply -var-file=environments/your-app.tfvars \
                -var="github_webhook_secret=$SECRET"
```

3. Use the custom domain in your GitHub App:
   - Webhook URL: `https://my-app.ci.folio.org/webhook`

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

## Support

For issues and questions, please open an issue in the GitHub repository.
