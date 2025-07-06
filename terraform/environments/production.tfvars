# Production Environment Configuration
environment = "production"

# Cost optimization for production
enable_spot_instances = false  # Use On-Demand for production stability
ecs_desired_capacity = 4
ecs_min_capacity    = 2
ecs_max_capacity    = 20

# Production application configuration
finance_app_config = {
  cpu                = 2048
  memory             = 4096
  desired_count      = 6
  min_capacity       = 3
  max_capacity       = 20
  health_check_path  = "/health/ready"
  container_port     = 8080
  enable_autoscaling = true
}

pharma_app_config = {
  cpu                = 4096
  memory             = 8192
  desired_count      = 4
  min_capacity       = 2
  max_capacity       = 12
  health_check_path  = "/health/ready"
  container_port     = 8080
  enable_autoscaling = true
}

# Production CI/CD
build_timeout = 30  # Longer timeout for production builds

# Enhanced monitoring for production
enable_business_metrics = true

# Production security
enable_waf = true
enable_vpc_flow_logs = true

# Production compliance
compliance_required = "true"
audit_log_retention_days = 2555  # 7 years FDA compliance