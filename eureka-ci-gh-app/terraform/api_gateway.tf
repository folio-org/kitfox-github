resource "aws_api_gateway_rest_api" "eureka_ci_webhook" {
  name        = "eureka-ci-webhook-${var.environment}"
  description = "API Gateway for Eureka CI GitHub App webhooks"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = merge(var.tags, {
    Name        = "eureka-ci-webhook-${var.environment}"
    Environment = var.environment
  })
}

resource "aws_api_gateway_resource" "webhook" {
  rest_api_id = aws_api_gateway_rest_api.eureka_ci_webhook.id
  parent_id   = aws_api_gateway_rest_api.eureka_ci_webhook.root_resource_id
  path_part   = "webhook"
}

resource "aws_api_gateway_method" "webhook_post" {
  rest_api_id   = aws_api_gateway_rest_api.eureka_ci_webhook.id
  resource_id   = aws_api_gateway_resource.webhook.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "webhook_lambda" {
  rest_api_id = aws_api_gateway_rest_api.eureka_ci_webhook.id
  resource_id = aws_api_gateway_resource.webhook.id
  http_method = aws_api_gateway_method.webhook_post.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.webhook_handler.invoke_arn
}

resource "aws_api_gateway_deployment" "eureka_ci" {
  depends_on = [
    aws_api_gateway_integration.webhook_lambda
  ]

  rest_api_id = aws_api_gateway_rest_api.eureka_ci_webhook.id
  stage_name  = var.environment

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "eureka_ci" {
  deployment_id = aws_api_gateway_deployment.eureka_ci.id
  rest_api_id   = aws_api_gateway_rest_api.eureka_ci_webhook.id
  stage_name    = var.environment

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      error          = "$context.error.message"
    })
  }

  xray_tracing_enabled = true

  tags = merge(var.tags, {
    Name        = "eureka-ci-webhook-${var.environment}"
    Environment = var.environment
  })
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/api-gateway/eureka-ci-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name        = "eureka-ci-api-gateway-logs-${var.environment}"
    Environment = var.environment
  })
}

resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.webhook_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.eureka_ci_webhook.execution_arn}/*/*"
}