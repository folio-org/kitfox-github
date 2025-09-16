# Data source to look up the existing Route 53 hosted zone
data "aws_route53_zone" "selected" {
  count = var.enable_route53 ? 1 : 0
  name  = var.route53_zone_name
}

# Data source to find existing ACM certificate for the domain
data "aws_acm_certificate" "existing" {
  count  = var.enable_route53 ? 1 : 0
  domain = "*.${var.route53_zone_name}"

  statuses = ["ISSUED"]
}

# API Gateway custom domain name using existing certificate
resource "aws_api_gateway_domain_name" "webhook_domain" {
  count = var.enable_route53 ? 1 : 0

  domain_name              = "${var.route53_record_name}.${var.route53_zone_name}"
  regional_certificate_arn = data.aws_acm_certificate.existing[0].arn

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.app_name}-webhook-domain"
    }
  )
}

# Map the custom domain to the API Gateway stage
resource "aws_api_gateway_base_path_mapping" "webhook_mapping" {
  count = var.enable_route53 ? 1 : 0

  api_id      = aws_api_gateway_rest_api.webhook_api.id
  stage_name  = aws_api_gateway_stage.app.stage_name
  domain_name = aws_api_gateway_domain_name.webhook_domain[0].domain_name
}

# Create ALIAS A record pointing to API Gateway custom domain
resource "aws_route53_record" "webhook_dns" {
  count = var.enable_route53 ? 1 : 0

  zone_id = data.aws_route53_zone.selected[0].zone_id
  name    = var.route53_record_name
  type    = "A"

  alias {
    name                   = aws_api_gateway_domain_name.webhook_domain[0].regional_domain_name
    zone_id                = aws_api_gateway_domain_name.webhook_domain[0].regional_zone_id
    evaluate_target_health = false
  }
}