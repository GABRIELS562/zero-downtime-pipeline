output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = aws_lb.main.zone_id
}

output "alb_arn" {
  description = "ARN of the load balancer"
  value       = aws_lb.main.arn
}

output "alb_arn_suffix" {
  description = "ARN suffix of the load balancer"
  value       = aws_lb.main.arn_suffix
}

output "alb_hosted_zone_id" {
  description = "The ID of the Amazon Route 53 hosted zone associated with the load balancer"
  value       = aws_lb.main.zone_id
}

output "certificate_arn" {
  description = "ARN of the SSL certificate"
  value       = aws_acm_certificate.main.arn
}

output "trading_domain" {
  description = "Domain name for trading application"
  value       = aws_route53_record.trading.name
}

output "manufacturing_domain" {
  description = "Domain name for manufacturing application"
  value       = aws_route53_record.manufacturing.name
}

output "waf_arn" {
  description = "ARN of the WAF web ACL"
  value       = var.enable_waf ? aws_wafv2_web_acl.main[0].arn : null
}