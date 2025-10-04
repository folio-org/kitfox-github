output "webhook_url" {
  description = "The URL for the GitHub webhook endpoint"
  value       = "${aws_api_gateway_stage.app.invoke_url}/webhook"
}

output "api_gateway_id" {
  description = "The ID of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.webhook_api.id
}

output "lambda_webhook_handler_arn" {
  description = "The ARN of the webhook handler Lambda function"
  value       = aws_lambda_function.webhook_handler.arn
}

output "lambda_check_processor_arn" {
  description = "The ARN of the check processor Lambda function"
  value       = aws_lambda_function.check_processor.arn
}

output "sqs_queue_url" {
  description = "The URL of the SQS queue for check suite events"
  value       = aws_sqs_queue.check_suite.url
}

output "config_bucket_name" {
  description = "The name of the S3 bucket for configuration"
  value       = aws_s3_bucket.app_config.id
}

output "app_name" {
  description = "The application name"
  value       = var.app_name
}

output "webhook_secret_arn" {
  description = "The ARN of the webhook secret in Secrets Manager"
  value       = aws_secretsmanager_secret.webhook_secret.arn
  sensitive   = true
}

output "github_private_key_arn" {
  description = "The ARN of the GitHub private key in Secrets Manager"
  value       = aws_secretsmanager_secret.github_private_key.arn
  sensitive   = true
}

# Route 53 DNS outputs
output "custom_domain_url" {
  description = "The custom domain URL for the webhook endpoint (if Route53 is enabled)"
  value       = var.enable_route53 ? "https://${var.route53_record_name}.${var.route53_zone_name}/webhook" : "Not configured"
}

output "dns_record_fqdn" {
  description = "The fully qualified domain name created in Route53"
  value       = var.enable_route53 ? "${var.route53_record_name}.${var.route53_zone_name}" : "Not configured"
}