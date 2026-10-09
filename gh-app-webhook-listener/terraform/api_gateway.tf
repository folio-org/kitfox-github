# API Gateway REST API
resource "aws_api_gateway_rest_api" "webhook_api" {
  name        = "${var.app_name}-api"
  description = "API Gateway for GitHub webhook handler"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = var.tags
}

# API Gateway Resource - /webhook
resource "aws_api_gateway_resource" "webhook" {
  rest_api_id = aws_api_gateway_rest_api.webhook_api.id
  parent_id   = aws_api_gateway_rest_api.webhook_api.root_resource_id
  path_part   = "webhook"
}

# API Gateway Method - POST /webhook
resource "aws_api_gateway_method" "webhook_post" {
  rest_api_id   = aws_api_gateway_rest_api.webhook_api.id
  resource_id   = aws_api_gateway_resource.webhook.id
  http_method   = "POST"
  authorization = "NONE"
}

# API Gateway Integration
resource "aws_api_gateway_integration" "webhook_lambda" {
  rest_api_id = aws_api_gateway_rest_api.webhook_api.id
  resource_id = aws_api_gateway_resource.webhook.id
  http_method = aws_api_gateway_method.webhook_post.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.webhook_handler.invoke_arn
}

# API Gateway Method Response
resource "aws_api_gateway_method_response" "webhook_response" {
  rest_api_id = aws_api_gateway_rest_api.webhook_api.id
  resource_id = aws_api_gateway_resource.webhook.id
  http_method = aws_api_gateway_method.webhook_post.http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }
}

# API Gateway Integration Response
resource "aws_api_gateway_integration_response" "webhook_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.webhook_api.id
  resource_id = aws_api_gateway_resource.webhook.id
  http_method = aws_api_gateway_method.webhook_post.http_method
  status_code = aws_api_gateway_method_response.webhook_response.status_code

  depends_on = [
    aws_api_gateway_integration.webhook_lambda
  ]
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "webhook_deployment" {
  rest_api_id = aws_api_gateway_rest_api.webhook_api.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.webhook.id,
      aws_api_gateway_method.webhook_post.id,
      aws_api_gateway_integration.webhook_lambda.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_method.webhook_post,
    aws_api_gateway_integration.webhook_lambda,
  ]
}

# API Gateway Stage
resource "aws_api_gateway_stage" "app" {
  deployment_id = aws_api_gateway_deployment.webhook_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.webhook_api.id
  stage_name    = terraform.workspace == "default" ? "prod" : terraform.workspace

  tags = var.tags
}

# API Gateway CloudWatch Logs
resource "aws_api_gateway_account" "app" {
  count = var.manage_api_gateway_account ? 1 : 0

  cloudwatch_role_arn = local.apigw_cw_role_arn
}

# IAM role for API Gateway CloudWatch logging
resource "aws_iam_role" "api_gateway_cloudwatch" {
  count = local.create_apigw_cw_role && var.manage_api_gateway_account ? 1 : 0

  name = "${var.app_name}-api-gateway-cloudwatch-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM policy attachment for API Gateway CloudWatch logging
resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch" {
  count = local.create_apigw_cw_role && var.manage_api_gateway_account ? 1 : 0

  role       = aws_iam_role.api_gateway_cloudwatch[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}