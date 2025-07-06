# Target groups for Application Load Balancer
resource "aws_lb_target_group" "finance_trading" {
  name     = "${var.project_name}-${var.environment}-finance-tg"
  port     = var.finance_app_config.container_port
  protocol = "HTTP"
  vpc_id   = var.vpc_id
  target_type = "ip"
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = var.finance_app_config.health_check_path
    matcher             = "200"
    port                = "traffic-port"
    protocol            = "HTTP"
  }
  
  # Deregistration delay for zero-downtime deployments
  deregistration_delay = 60
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-finance-trading-tg"
    Application = "finance-trading"
  })
}

resource "aws_lb_target_group" "pharma_manufacturing" {
  name     = "${var.project_name}-${var.environment}-pharma-tg"
  port     = var.pharma_app_config.container_port
  protocol = "HTTP"
  vpc_id   = var.vpc_id
  target_type = "ip"
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 10
    interval            = 60
    path                = var.pharma_app_config.health_check_path
    matcher             = "200"
    port                = "traffic-port"
    protocol            = "HTTP"
  }
  
  # Longer deregistration delay for critical manufacturing systems
  deregistration_delay = 120
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-pharma-manufacturing-tg"
    Application = "pharma-manufacturing"
  })
}