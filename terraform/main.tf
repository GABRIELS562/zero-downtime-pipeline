terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }

  backend "s3" {
    bucket         = "zero-downtime-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
    
    # Cost optimization: Use reduced redundancy for state files
    # This is acceptable for non-critical infrastructure
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project              = var.project_name
      Environment          = var.environment
      ManagedBy           = "terraform"
      CostCenter          = var.cost_center
      BusinessUnit        = var.business_unit
      BackupPolicy        = var.backup_policy
      MonitoringEnabled   = "true"
      ComplianceRequired  = var.compliance_required
    }
  }
}

# Data sources for existing VPC and subnets (cost optimization)
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Random suffix for unique resource naming
resource "random_id" "suffix" {
  byte_length = 4
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    CreatedBy   = "terraform"
    Repository  = "zero-downtime-pipeline"
  }
  
  # Cost optimization: Use single AZ for dev, multi-AZ for prod
  availability_zones = var.environment == "production" ? slice(data.aws_availability_zones.available.names, 0, 2) : slice(data.aws_availability_zones.available.names, 0, 1)
}

# Networking Module (using default VPC for cost optimization)
module "networking" {
  source = "./modules/networking"
  
  project_name       = var.project_name
  environment        = var.environment
  vpc_id            = data.aws_vpc.default.id
  availability_zones = local.availability_zones
  
  tags = local.common_tags
}

# Security Module
module "security" {
  source = "./modules/security"
  
  project_name = var.project_name
  environment  = var.environment
  vpc_id       = data.aws_vpc.default.id
  
  tags = local.common_tags
}

# ECS Cluster Module
module "ecs" {
  source = "./modules/ecs"
  
  project_name           = var.project_name
  environment            = var.environment
  vpc_id                = data.aws_vpc.default.id
  private_subnet_ids    = module.networking.private_subnet_ids
  public_subnet_ids     = module.networking.public_subnet_ids
  security_group_ids    = [module.security.ecs_security_group_id]
  
  # Cost optimization settings
  enable_spot_instances     = var.enable_spot_instances
  desired_capacity         = var.ecs_desired_capacity
  min_capacity            = var.ecs_min_capacity
  max_capacity            = var.ecs_max_capacity
  instance_types          = var.ecs_instance_types
  
  # Application configurations
  finance_app_config      = var.finance_app_config
  pharma_app_config       = var.pharma_app_config
  
  tags = local.common_tags
  
  depends_on = [module.networking, module.security]
}

# Application Load Balancer Module
module "alb" {
  source = "./modules/alb"
  
  project_name       = var.project_name
  environment        = var.environment
  vpc_id            = data.aws_vpc.default.id
  public_subnet_ids = module.networking.public_subnet_ids
  security_group_ids = [module.security.alb_security_group_id]
  
  # Target groups for applications
  finance_target_group_arn = module.ecs.finance_target_group_arn
  pharma_target_group_arn  = module.ecs.pharma_target_group_arn
  
  enable_deletion_protection = var.environment == "production"
  
  tags = local.common_tags
  
  depends_on = [module.networking, module.security, module.ecs]
}

# CloudWatch Monitoring Module
module "monitoring" {
  source = "./modules/monitoring"
  
  project_name     = var.project_name
  environment      = var.environment
  ecs_cluster_name = module.ecs.cluster_name
  alb_arn_suffix   = module.alb.alb_arn_suffix
  
  # Cost optimization: Reduced retention for non-prod
  log_retention_days = var.environment == "production" ? 90 : 14
  
  # Business impact monitoring
  enable_business_metrics = var.enable_business_metrics
  notification_endpoints  = var.notification_endpoints
  
  tags = local.common_tags
  
  depends_on = [module.ecs, module.alb]
}

# CI/CD Pipeline Module
module "codepipeline" {
  source = "./modules/codepipeline"
  
  project_name           = var.project_name
  environment            = var.environment
  ecs_cluster_name       = module.ecs.cluster_name
  ecs_service_names      = {
    finance = module.ecs.finance_service_name
    pharma  = module.ecs.pharma_service_name
  }
  
  # Repository configuration
  github_repo           = var.github_repo
  github_branch         = var.github_branch
  github_token_secret   = var.github_token_secret
  
  # Build configuration
  build_timeout         = var.build_timeout
  build_compute_type    = var.environment == "production" ? "BUILD_GENERAL1_MEDIUM" : "BUILD_GENERAL1_SMALL"
  
  # Cost optimization: Use smaller build instances for non-prod
  enable_build_caching  = true
  
  tags = local.common_tags
  
  depends_on = [module.ecs]
}