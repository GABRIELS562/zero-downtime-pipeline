# Infrastructure Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = data.aws_vpc.default.id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.networking.private_subnet_ids
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.networking.public_subnet_ids
}

# ECS Outputs
output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = module.ecs.cluster_arn
}

output "finance_service_name" {
  description = "Name of the finance trading ECS service"
  value       = module.ecs.finance_service_name
}

output "pharma_service_name" {
  description = "Name of the pharma manufacturing ECS service"
  value       = module.ecs.pharma_service_name
}

# ECR Outputs
output "finance_ecr_repository_url" {
  description = "URL of the finance trading ECR repository"
  value       = module.ecs.finance_ecr_repository_url
}

output "pharma_ecr_repository_url" {
  description = "URL of the pharma manufacturing ECR repository"
  value       = module.ecs.pharma_ecr_repository_url
}

output "latency_monitor_ecr_repository_url" {
  description = "URL of the latency monitor ECR repository"
  value       = module.ecs.latency_monitor_ecr_repository_url
}

# Load Balancer Outputs
output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.alb.alb_dns_name
}

output "trading_domain" {
  description = "Domain name for trading application"
  value       = module.alb.trading_domain
}

output "manufacturing_domain" {
  description = "Domain name for manufacturing application"
  value       = module.alb.manufacturing_domain
}

output "ssl_certificate_arn" {
  description = "ARN of the SSL certificate"
  value       = module.alb.certificate_arn
}

# CI/CD Outputs
output "finance_pipeline_name" {
  description = "Name of the finance trading CodePipeline"
  value       = module.codepipeline.finance_pipeline_name
}

output "pharma_pipeline_name" {
  description = "Name of the pharma manufacturing CodePipeline"
  value       = module.codepipeline.pharma_pipeline_name
}

output "codepipeline_artifacts_bucket" {
  description = "Name of the CodePipeline artifacts S3 bucket"
  value       = module.codepipeline.artifacts_bucket_name
}

# Monitoring Outputs
output "cloudwatch_dashboard_url" {
  description = "URL of the CloudWatch dashboard"
  value       = module.monitoring.dashboard_url
}

output "monitoring_alarms" {
  description = "ARNs of CloudWatch alarms"
  value = {
    finance_cpu_alarm      = module.monitoring.finance_cpu_alarm_arn
    pharma_cpu_alarm       = module.monitoring.pharma_cpu_alarm_arn
    alb_response_time      = module.monitoring.alb_response_time_alarm_arn
    alb_5xx_errors        = module.monitoring.alb_5xx_errors_alarm_arn
    finance_error_rate     = module.monitoring.finance_error_rate_alarm_arn
    pharma_error_rate      = module.monitoring.pharma_error_rate_alarm_arn
  }
}

# Security Outputs
output "security_groups" {
  description = "Security group IDs"
  value = {
    alb          = module.security.alb_security_group_id
    ecs_tasks    = module.security.ecs_security_group_id
    rds          = module.security.rds_security_group_id
    redis        = module.security.redis_security_group_id
    vpc_endpoints = module.security.vpc_endpoints_security_group_id
  }
}

output "security_services" {
  description = "Security service identifiers"
  value = {
    security_hub_account = module.security.security_hub_account_id
    guardduty_detector  = module.security.guardduty_detector_id
    config_recorder     = module.security.config_recorder_name
  }
}

# Storage Outputs
output "s3_buckets" {
  description = "S3 bucket names for data storage"
  value = {
    audit_logs            = module.ecs.audit_logs_bucket_name
    batch_data           = module.ecs.batch_data_bucket_name
    pipeline_artifacts   = module.codepipeline.artifacts_bucket_name
  }
}

# Cost Optimization Information
output "cost_optimization_features" {
  description = "Enabled cost optimization features"
  value = {
    spot_instances_enabled     = var.enable_spot_instances
    build_caching_enabled     = true
    vpc_endpoints_enabled     = true
    single_nat_gateway        = var.environment != "production"
    reduced_log_retention     = var.environment != "production"
    container_insights        = var.environment == "production"
    access_logs_enabled       = var.environment == "production"
    synthetics_enabled        = var.environment == "production"
  }
}

# Application URLs
output "application_urls" {
  description = "Application URLs for access"
  value = {
    trading_https      = "https://${module.alb.trading_domain}"
    manufacturing_https = "https://${module.alb.manufacturing_domain}"
    alb_dns           = "https://${module.alb.alb_dns_name}"
  }
}

# Environment Information
output "environment_info" {
  description = "Environment configuration details"
  value = {
    project_name     = var.project_name
    environment      = var.environment
    aws_region       = var.aws_region
    availability_zones = local.availability_zones
    deployment_timestamp = timestamp()
  }
}

# Compliance and Audit
output "compliance_features" {
  description = "Compliance and audit features"
  value = {
    audit_logs_retention_days = var.audit_log_retention_days
    encryption_at_rest       = var.enable_encryption_at_rest
    encryption_in_transit    = var.enable_encryption_in_transit
    vpc_flow_logs_enabled    = var.enable_vpc_flow_logs
    waf_enabled             = var.enable_waf
    security_hub_enabled    = true
    guardduty_enabled       = true
  }
}