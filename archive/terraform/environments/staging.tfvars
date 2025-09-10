# Staging Environment Configuration
environment = "staging"

# Cost optimization for staging
enable_spot_instances = true
ecs_desired_capacity = 2
ecs_min_capacity    = 1
ecs_max_capacity    = 6

# Staging application configuration
finance_app_config = {
  cpu                = 1024
  memory             = 2048
  desired_count      = 2
  min_capacity       = 1
  max_capacity       = 6
  health_check_path  = "/health/ready"
  container_port     = 8080
  enable_autoscaling = true
}

pharma_app_config = {
  cpu                = 2048
  memory             = 4096
  desired_count      = 1
  min_capacity       = 1
  max_capacity       = 4
  health_check_path  = "/health/ready"
  container_port     = 8080
  enable_autoscaling = true
}

# Staging CI/CD
build_timeout = 20

# Basic monitoring for staging
enable_business_metrics = false

# Reduced security for cost optimization
enable_waf = false
enable_vpc_flow_logs = false

# Basic compliance for staging
compliance_required = "false"
audit_log_retention_days = 30