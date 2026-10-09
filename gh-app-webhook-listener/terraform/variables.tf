variable "aws_region" {
  description = "AWS region where resources will be created"
  type        = string
  default     = "us-west-2"
}

variable "app_name" {
  description = "Application name (e.g., eureka-ci, folio-app)"
  type        = string
  default     = "github-webhook-listener"
}

variable "github_app_id" {
  description = "GitHub App ID. Required unless github_app_id_ssm_parameter is set."
  type        = string
  sensitive   = true
  default     = ""
}

variable "github_installation_id" {
  description = "GitHub App Installation ID. Required unless github_installation_id_ssm_parameter is set."
  type        = string
  sensitive   = true
  default     = ""
}

variable "github_webhook_secret" {
  description = "GitHub webhook secret for signature validation. With credentials_store = \"ssm\", written to the github_webhook_secret_ssm_parameter parameter when set."
  type        = string
  sensitive   = true
  default     = ""
}

variable "github_private_key_path" {
  description = "Path to GitHub App private key file in PEM format"
  type        = string
  default     = ""
}

variable "github_private_key" {
  description = "GitHub App private key in PEM format (use this OR github_private_key_path). With credentials_store = \"ssm\", written to the github_private_key_ssm_parameter parameter when set."
  type        = string
  sensitive   = true
  default     = ""
}

variable "credentials_store" {
  description = "Where the GitHub App private key and webhook secret live: \"secretsmanager\" (created and populated by this stack) or \"ssm\" (existing SecureString parameters, read by the Lambdas at runtime)."
  type        = string
  default     = "secretsmanager"

  validation {
    condition     = contains(["secretsmanager", "ssm"], var.credentials_store)
    error_message = "credentials_store must be \"secretsmanager\" or \"ssm\"."
  }
}

variable "github_private_key_ssm_parameter" {
  description = "SSM parameter name (SecureString) holding the GitHub App private key in PEM format, used with credentials_store = \"ssm\". Empty means /<app_name>/github-app-private-key. Written by the stack when github_private_key or github_private_key_path is set; otherwise it must already exist."
  type        = string
  default     = ""
}

variable "github_webhook_secret_ssm_parameter" {
  description = "SSM parameter name (SecureString) holding the webhook secret configured in the GitHub App, used with credentials_store = \"ssm\". Empty means /<app_name>/webhook-secret. Written by the stack when github_webhook_secret is set; otherwise it must already exist."
  type        = string
  default     = ""
}

variable "github_app_id_ssm_parameter" {
  description = "Optional SSM parameter name holding the GitHub App ID; used instead of github_app_id when set."
  type        = string
  default     = ""
}

variable "github_installation_id_ssm_parameter" {
  description = "Optional SSM parameter name holding the GitHub App installation ID; used instead of github_installation_id when set."
  type        = string
  default     = ""
}

variable "ssm_kms_key_arn" {
  description = "KMS key ARN used to encrypt the SecureString parameters, for the Lambda role policy. Empty means the AWS managed key (alias/aws/ssm)."
  type        = string
  default     = ""
}

variable "lambda_execution_role_arn" {
  description = "Existing IAM role for both Lambda functions. When set, the stack does not create the Lambda role or its inline policy; the role must already grant what the functions need (see README)."
  type        = string
  default     = ""
}

variable "api_gateway_cloudwatch_role_arn" {
  description = "Existing IAM role for API Gateway CloudWatch logging. When set, the stack does not create that role or its policy attachment."
  type        = string
  default     = ""
}

variable "manage_api_gateway_account" {
  description = "Whether this stack manages the account-level API Gateway setting (CloudWatch logging role). It is shared by all REST APIs in the account and region."
  type        = bool
  default     = true
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory" {
  description = "Lambda function memory in MB"
  type        = number
  default     = 256
}

variable "sqs_visibility_timeout" {
  description = "SQS visibility timeout in seconds"
  type        = number
  default     = 300
}

variable "sqs_max_receive_count" {
  description = "Maximum number of times a message can be received from the queue"
  type        = number
  default     = 3
}

variable "dlq_alarm_emails" {
  description = "Email addresses subscribed to the DLQ alarm SNS topic. Empty list skips the subscription."
  type        = list(string)
  default     = []
}

variable "log_retention_days" {
  description = "CloudWatch logs retention in days"
  type        = number
  default     = 7
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Terraform   = "true"
    Project     = "github-webhook-listener"
    Application = "github-app"
  }
}

# Route 53 DNS Configuration
variable "enable_route53" {
  description = "Enable Route 53 DNS record creation"
  type        = bool
  default     = false
}

variable "route53_zone_name" {
  description = "Existing Route 53 hosted zone domain name (e.g., ci.folio.org)"
  type        = string
  default     = ""
}

variable "route53_record_name" {
  description = "DNS record name to create in the zone (e.g., ci-eureka will create ci-eureka.ci.folio.org)"
  type        = string
  default     = ""
}

# GitHub Events Configuration
variable "github_events_config_file" {
  description = "Full path to the GitHub events configuration JSON file"
  type        = string
  default     = "./environments/github_events_config.json"
}

variable "github_events_config_s3_enabled" {
  description = "Whether to upload and use configuration from S3 (if false, config is bundled with Lambda)"
  type        = bool
  default     = true
}