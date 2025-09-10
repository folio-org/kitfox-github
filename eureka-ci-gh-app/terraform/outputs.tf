output "webhook_url" {
  description = "The URL for the GitHub webhook endpoint"
  value       = "${aws_api_gateway_deployment.eureka_ci.invoke_url}/webhook"
}

output "api_gateway_id" {
  description = "The ID of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.eureka_ci_webhook.id
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
  value       = aws_s3_bucket.eureka_ci_config.id
}

output "environment" {
  description = "The deployment environment"
  value       = var.environment
}