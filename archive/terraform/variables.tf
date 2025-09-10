variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "zero-downtime-pipeline"
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be one of: dev, staging, production."
  }
}

variable "cost_center" {
  description = "Cost center for billing allocation"
  type        = string
  default     = "engineering"
}

variable "business_unit" {
  description = "Business unit for resource organization"
  type        = string
  default     = "platform-engineering"
}

variable "backup_policy" {
  description = "Backup policy tag for automated backups"
  type        = string
  default     = "standard"
}

variable "compliance_required" {
  description = "Whether compliance features are required (FDA, SOX, etc.)"
  type        = string
  default     = "true"
}

# ECS Configuration
variable "enable_spot_instances" {
  description = "Enable Spot instances for cost optimization"
  type        = bool
  default     = true
}

variable "ecs_desired_capacity" {
  description = "Desired capacity for ECS Auto Scaling Group"
  type        = number
  default     = 2
}

variable "ecs_min_capacity" {
  description = "Minimum capacity for ECS Auto Scaling Group"
  type        = number
  default     = 1
}

variable "ecs_max_capacity" {
  description = "Maximum capacity for ECS Auto Scaling Group"
  type        = number
  default     = 6
}

variable "ecs_instance_types" {
  description = "Instance types for ECS cluster (cost-optimized mix)"
  type        = list(string)
  default     = ["t3.medium", "t3.large", "m5.large"]
}

# Application Configuration
variable "finance_app_config" {
  description = "Configuration for finance trading application"
  type = object({
    cpu                = number
    memory             = number
    desired_count      = number
    min_capacity       = number
    max_capacity       = number
    health_check_path  = string
    container_port     = number
    enable_autoscaling = bool
  })
  default = {
    cpu                = 1024
    memory             = 2048
    desired_count      = 3
    min_capacity       = 2
    max_capacity       = 10
    health_check_path  = "/health/ready"
    container_port     = 8080
    enable_autoscaling = true
  }
}

variable "pharma_app_config" {
  description = "Configuration for pharma manufacturing application"
  type = object({
    cpu                = number
    memory             = number
    desired_count      = number
    min_capacity       = number
    max_capacity       = number
    health_check_path  = string
    container_port     = number
    enable_autoscaling = bool
  })
  default = {
    cpu                = 2048
    memory             = 4096
    desired_count      = 2
    min_capacity       = 1
    max_capacity       = 6
    health_check_path  = "/health/ready"
    container_port     = 8080
    enable_autoscaling = true
  }
}

# CI/CD Configuration
variable "github_repo" {
  description = "GitHub repository for source code"
  type        = string
  default     = "your-org/zero-downtime-pipeline"
}

variable "github_branch" {
  description = "GitHub branch for deployments"
  type        = string
  default     = "main"
}

variable "github_token_secret" {
  description = "AWS Secrets Manager secret name for GitHub token"
  type        = string
  default     = "github-token"
}

variable "build_timeout" {
  description = "Build timeout in minutes"
  type        = number
  default     = 15
}

# Monitoring Configuration
variable "enable_business_metrics" {
  description = "Enable business impact metrics and dashboards"
  type        = bool
  default     = true
}

variable "notification_endpoints" {
  description = "SNS topic ARNs for notifications"
  type        = list(string)
  default     = []
}

# Cost Optimization Variables
variable "enable_cost_optimization" {
  description = "Enable aggressive cost optimization features"
  type        = bool
  default     = true
}

variable "schedule_based_scaling" {
  description = "Enable schedule-based scaling for predictable workloads"
  type        = bool
  default     = true
}

variable "trading_hours_schedule" {
  description = "Trading hours for finance application scaling"
  type = object({
    scale_up_cron   = string
    scale_down_cron = string
    timezone        = string
  })
  default = {
    scale_up_cron   = "0 13 * * 1-5"  # 9:30 AM ET (13:30 UTC) Mon-Fri
    scale_down_cron = "0 21 * * 1-5"  # 4:00 PM ET (21:00 UTC) Mon-Fri
    timezone        = "UTC"
  }
}

variable "manufacturing_hours_schedule" {
  description = "Manufacturing hours for pharma application scaling"
  type = object({
    scale_up_cron   = string
    scale_down_cron = string
    timezone        = string
  })
  default = {
    scale_up_cron   = "0 6 * * *"   # 6:00 AM UTC daily
    scale_down_cron = "0 18 * * *"  # 6:00 PM UTC daily
    timezone        = "UTC"
  }
}

# Security Configuration
variable "enable_waf" {
  description = "Enable AWS WAF for additional security"
  type        = bool
  default     = true
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the application"
  type        = list(string)
  default     = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
}

variable "enable_vpc_flow_logs" {
  description = "Enable VPC Flow Logs for security monitoring"
  type        = bool
  default     = true
}

# Database Configuration (for future expansion)
variable "database_config" {
  description = "Database configuration for applications"
  type = object({
    engine         = string
    instance_class = string
    multi_az       = bool
    storage_type   = string
    storage_size   = number
  })
  default = {
    engine         = "postgres"
    instance_class = "db.t3.micro"
    multi_az       = false
    storage_type   = "gp3"
    storage_size   = 20
  }
}

# Compliance and Audit Configuration
variable "audit_log_retention_days" {
  description = "Retention period for audit logs (FDA compliance: 7 years = 2555 days)"
  type        = number
  default     = 2555
}

variable "enable_encryption_at_rest" {
  description = "Enable encryption at rest for all storage"
  type        = bool
  default     = true
}

variable "enable_encryption_in_transit" {
  description = "Enable encryption in transit for all communications"
  type        = bool
  default     = true
}