# Development Environment Configuration
environment = "dev"

# Maximum cost optimization for dev
enable_spot_instances = true
ecs_desired_capacity = 1
ecs_min_capacity    = 0
ecs_max_capacity    = 3

# Minimal dev application configuration
finance_app_config = {
  cpu                = 512
  memory             = 1024
  desired_count      = 1
  min_capacity       = 0
  max_capacity       = 2
  health_check_path  = "/health/ready"
  container_port     = 8080
  enable_autoscaling = false
}

pharma_app_config = {
  cpu                = 1024
  memory             = 2048
  desired_count      = 1
  min_capacity       = 0
  max_capacity       = 2
  health_check_path  = "/health/ready"
  container_port     = 8080
  enable_autoscaling = false
}

# Fast dev CI/CD
build_timeout = 10

# Minimal monitoring for dev
enable_business_metrics = false

# No security features for dev cost optimization
enable_waf = false
enable_vpc_flow_logs = false

# Minimal compliance for dev
compliance_required = "false"
audit_log_retention_days = 7