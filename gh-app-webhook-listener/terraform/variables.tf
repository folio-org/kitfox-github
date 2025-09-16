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
  description = "GitHub App ID"
  type        = string
  sensitive   = true
}

variable "github_webhook_secret" {
  description = "GitHub webhook secret for signature validation"
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
  description = "GitHub App private key in PEM format (use this OR github_private_key_path)"
  type        = string
  sensitive   = true
  default     = ""
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