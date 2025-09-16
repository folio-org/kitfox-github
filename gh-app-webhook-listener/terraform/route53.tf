# Data source to look up the existing Route 53 hosted zone
data "aws_route53_zone" "selected" {
  count = var.enable_route53 ? 1 : 0
  name  = var.route53_zone_name
}

# Create CNAME record pointing to API Gateway
resource "aws_route53_record" "webhook_dns" {
  count = var.enable_route53 ? 1 : 0

  zone_id = data.aws_route53_zone.selected[0].zone_id
  name    = var.route53_record_name
  type    = "CNAME"
  ttl     = 300

  records = [
    replace(aws_api_gateway_stage.app.invoke_url, "https://", "")
  ]
}

# Alternative A record with ALIAS (works better with API Gateway)
resource "aws_route53_record" "webhook_dns_alias" {
  count = 0  # Disabled by default, enable if you prefer ALIAS over CNAME

  zone_id = data.aws_route53_zone.selected[0].zone_id
  name    = var.route53_record_name
  type    = "A"

  alias {
    name                   = aws_api_gateway_domain_name.webhook_domain[0].cloudfront_domain_name
    zone_id                = aws_api_gateway_domain_name.webhook_domain[0].cloudfront_zone_id
    evaluate_target_health = false
  }
}