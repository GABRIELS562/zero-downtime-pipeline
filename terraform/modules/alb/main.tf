# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = var.security_group_ids
  subnets            = var.public_subnet_ids
  
  enable_deletion_protection = var.enable_deletion_protection
  enable_http2              = true
  
  # Cost optimization: Access logs only for production
  dynamic "access_logs" {
    for_each = var.environment == "production" ? [1] : []
    content {
      bucket  = aws_s3_bucket.alb_logs[0].bucket
      prefix  = "alb"
      enabled = true
    }
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-alb"
  })
}

# ALB Listeners
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"
  
  # Redirect HTTP to HTTPS for security
  default_action {
    type = "redirect"
    
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
  
  tags = var.tags
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.main.arn
  
  # Default action - return 404 for unmatched requests
  default_action {
    type = "fixed-response"
    
    fixed_response {
      content_type = "text/plain"
      message_body = "Not Found"
      status_code  = "404"
    }
  }
  
  tags = var.tags
  
  depends_on = [aws_acm_certificate_validation.main]
}

# Listener rules for applications
resource "aws_lb_listener_rule" "finance_trading" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100
  
  action {
    type             = "forward"
    target_group_arn = var.finance_target_group_arn
  }
  
  condition {
    path_pattern {
      values = ["/api/trading/*", "/health/*"]
    }
  }
  
  condition {
    host_header {
      values = ["trading.${local.domain_name}"]
    }
  }
  
  tags = merge(var.tags, {
    Application = "finance-trading"
  })
}

resource "aws_lb_listener_rule" "pharma_manufacturing" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 200
  
  action {
    type             = "forward"
    target_group_arn = var.pharma_target_group_arn
  }
  
  condition {
    path_pattern {
      values = ["/api/manufacturing/*", "/health/*"]
    }
  }
  
  condition {
    host_header {
      values = ["manufacturing.${local.domain_name}"]
    }
  }
  
  tags = merge(var.tags, {
    Application = "pharma-manufacturing"
  })
}

# SSL Certificate
resource "aws_acm_certificate" "main" {
  domain_name               = local.domain_name
  subject_alternative_names = ["*.${local.domain_name}"]
  validation_method         = "DNS"
  
  lifecycle {
    create_before_destroy = true
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-certificate"
  })
}

# Certificate validation (requires Route53 hosted zone)
resource "aws_acm_certificate_validation" "main" {
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
  
  timeouts {
    create = "5m"
  }
}

# Route53 hosted zone and records
data "aws_route53_zone" "main" {
  count = var.create_route53_zone ? 0 : 1
  name  = local.domain_name
}

resource "aws_route53_zone" "main" {
  count = var.create_route53_zone ? 1 : 0
  name  = local.domain_name
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-zone"
  })
}

locals {
  hosted_zone = var.create_route53_zone ? aws_route53_zone.main[0] : data.aws_route53_zone.main[0]
  domain_name = var.domain_name != "" ? var.domain_name : "${var.project_name}-${var.environment}.example.com"
}

resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }
  
  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = local.hosted_zone.zone_id
}

# A records for applications
resource "aws_route53_record" "trading" {
  zone_id = local.hosted_zone.zone_id
  name    = "trading.${local.domain_name}"
  type    = "A"
  
  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "manufacturing" {
  zone_id = local.hosted_zone.zone_id
  name    = "manufacturing.${local.domain_name}"
  type    = "A"
  
  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# S3 bucket for ALB access logs (production only)
resource "aws_s3_bucket" "alb_logs" {
  count         = var.environment == "production" ? 1 : 0
  bucket_prefix = "${var.project_name}-${var.environment}-alb-logs"
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-alb-logs"
  })
}

resource "aws_s3_bucket_lifecycle_configuration" "alb_logs" {
  count  = var.environment == "production" ? 1 : 0
  bucket = aws_s3_bucket.alb_logs[0].id
  
  rule {
    id     = "log_lifecycle"
    status = "Enabled"
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    
    expiration {
      days = 365
    }
  }
}

resource "aws_s3_bucket_policy" "alb_logs" {
  count  = var.environment == "production" ? 1 : 0
  bucket = aws_s3_bucket.alb_logs[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_elb_service_account.main.id}:root"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.alb_logs[0].arn}/alb/AWSLogs/${data.aws_caller_identity.current.account_id}/*"
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "delivery.logs.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.alb_logs[0].arn}/alb/AWSLogs/${data.aws_caller_identity.current.account_id}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "delivery.logs.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.alb_logs[0].arn
      }
    ]
  })
}

resource "aws_s3_bucket_public_access_block" "alb_logs" {
  count  = var.environment == "production" ? 1 : 0
  bucket = aws_s3_bucket.alb_logs[0].id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# AWS WAF for additional security
resource "aws_wafv2_web_acl" "main" {
  count = var.enable_waf ? 1 : 0
  
  name  = "${var.project_name}-${var.environment}-waf"
  scope = "REGIONAL"
  
  default_action {
    allow {}
  }
  
  # Rate limiting rule
  rule {
    name     = "RateLimitRule"
    priority = 1
    
    override_action {
      none {}
    }
    
    statement {
      rate_based_statement {
        limit          = 2000
        aggregate_key_type = "IP"
        
        scope_down_statement {
          geo_match_statement {
            country_codes = ["US", "CA", "MX"]
          }
        }
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }
    
    action {
      block {}
    }
  }
  
  # AWS Managed Rules
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 2
    
    override_action {
      none {}
    }
    
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }
  
  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project_name}-${var.environment}-waf"
    sampled_requests_enabled   = true
  }
  
  tags = var.tags
}

resource "aws_wafv2_web_acl_association" "main" {
  count = var.enable_waf ? 1 : 0
  
  resource_arn = aws_lb.main.arn
  web_acl_arn  = aws_wafv2_web_acl.main[0].arn
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_elb_service_account" "main" {}