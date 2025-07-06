# Security groups for ALB
resource "aws_security_group" "alb" {
  name_prefix = "${var.project_name}-${var.environment}-alb"
  vpc_id      = var.vpc_id
  description = "Security group for Application Load Balancer"
  
  # HTTP access from anywhere (will redirect to HTTPS)
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # HTTPS access from anywhere
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # Allow all outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-alb-sg"
    Type = "alb"
  })
}

# Security group for ECS tasks
resource "aws_security_group" "ecs_tasks" {
  name_prefix = "${var.project_name}-${var.environment}-ecs-tasks"
  vpc_id      = var.vpc_id
  description = "Security group for ECS tasks"
  
  # Allow traffic from ALB
  ingress {
    description     = "HTTP from ALB"
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  # Health check ports
  ingress {
    description     = "Health checks from ALB"
    from_port       = 8081
    to_port         = 8081
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  # Metrics port for monitoring
  ingress {
    description     = "Metrics from ALB"
    from_port       = 9090
    to_port         = 9090
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  # Allow communication between ECS tasks
  ingress {
    description = "Inter-service communication"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    self        = true
  }
  
  # Allow all outbound traffic (for external API calls, database connections, etc.)
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-ecs-tasks-sg"
    Type = "ecs-tasks"
  })
}

# Security group for RDS (if used in future)
resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-${var.environment}-rds"
  vpc_id      = var.vpc_id
  description = "Security group for RDS database"
  
  # PostgreSQL access from ECS tasks only
  ingress {
    description     = "PostgreSQL from ECS"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }
  
  # No outbound rules needed for RDS
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-rds-sg"
    Type = "rds"
  })
}

# Security group for Redis/ElastiCache (if used in future)
resource "aws_security_group" "redis" {
  name_prefix = "${var.project_name}-${var.environment}-redis"
  vpc_id      = var.vpc_id
  description = "Security group for Redis/ElastiCache"
  
  # Redis access from ECS tasks only
  ingress {
    description     = "Redis from ECS"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-redis-sg"
    Type = "redis"
  })
}

# Security group for VPC endpoints
resource "aws_security_group" "vpc_endpoints" {
  name_prefix = "${var.project_name}-${var.environment}-vpc-endpoints"
  vpc_id      = var.vpc_id
  description = "Security group for VPC endpoints"
  
  # HTTPS access from ECS tasks
  ingress {
    description     = "HTTPS from ECS"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }
  
  # HTTPS access from VPC CIDR (for other services)
  ingress {
    description = "HTTPS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.main.cidr_block]
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-vpc-endpoints-sg"
    Type = "vpc-endpoints"
  })
}

# Network ACLs for additional security layer
resource "aws_network_acl" "private" {
  vpc_id     = var.vpc_id
  subnet_ids = var.private_subnet_ids
  
  # Allow inbound HTTP/HTTPS from public subnets
  ingress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "allow"
    cidr_block = data.aws_vpc.main.cidr_block
    from_port  = 80
    to_port    = 80
  }
  
  ingress {
    protocol   = "tcp"
    rule_no    = 110
    action     = "allow"
    cidr_block = data.aws_vpc.main.cidr_block
    from_port  = 443
    to_port    = 443
  }
  
  # Allow inbound ephemeral ports for return traffic
  ingress {
    protocol   = "tcp"
    rule_no    = 120
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024
    to_port    = 65535
  }
  
  # Allow all outbound traffic
  egress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-private-nacl"
  })
}

# IAM roles for cross-service access (least privilege)
resource "aws_iam_role" "cross_service_access" {
  name_prefix = "${var.project_name}-${var.environment}-cross-service"
  description = "Role for cross-service communication with least privilege"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Condition = {
          StringEquals = {
            "aws:RequestedRegion" = data.aws_region.current.name
          }
        }
      }
    ]
  })
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-cross-service-role"
  })
}

# Least privilege policy for finance trading service
resource "aws_iam_role_policy" "finance_trading_policy" {
  name_prefix = "${var.project_name}-${var.environment}-finance-trading"
  role        = aws_iam_role.cross_service_access.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "cloudwatch:namespace" = "ZeroDowntime/Finance"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.project_name}-${var.environment}-finance-secrets*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/ecs/${var.project_name}-${var.environment}/finance-trading:*"
      }
    ]
  })
}

# Least privilege policy for pharma manufacturing service
resource "aws_iam_role_policy" "pharma_manufacturing_policy" {
  name_prefix = "${var.project_name}-${var.environment}-pharma-manufacturing"
  role        = aws_iam_role.cross_service_access.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "cloudwatch:namespace" = "ZeroDowntime/Pharma"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.project_name}-${var.environment}-pharma-secrets*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:PutObjectAcl"
        ]
        Resource = [
          "arn:aws:s3:::${var.project_name}-${var.environment}-audit-logs*/*",
          "arn:aws:s3:::${var.project_name}-${var.environment}-batch-data*/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/ecs/${var.project_name}-${var.environment}/pharma-manufacturing:*"
      }
    ]
  })
}

# Security hub findings and compliance
resource "aws_securityhub_account" "main" {
  count = var.enable_security_hub ? 1 : 0
  
  enable_default_standards = true
}

resource "aws_securityhub_standards_subscription" "aws_foundational" {
  count         = var.enable_security_hub ? 1 : 0
  standards_arn = "arn:aws:securityhub:::standard/aws-foundational-security/v/1.0.0"
  
  depends_on = [aws_securityhub_account.main]
}

resource "aws_securityhub_standards_subscription" "cis" {
  count         = var.enable_security_hub ? 1 : 0
  standards_arn = "arn:aws:securityhub:::standard/cis-aws-foundations-benchmark/v/1.2.0"
  
  depends_on = [aws_securityhub_account.main]
}

# GuardDuty for threat detection
resource "aws_guardduty_detector" "main" {
  count  = var.enable_guardduty ? 1 : 0
  enable = true
  
  datasources {
    s3_logs {
      enable = true
    }
    kubernetes {
      audit_logs {
        enable = false  # We're using ECS, not EKS
      }
    }
    malware_protection {
      scan_ec2_instance_with_findings {
        ebs_volumes {
          enable = true
        }
      }
    }
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-guardduty"
  })
}

# Config rules for compliance
resource "aws_config_configuration_recorder" "main" {
  count    = var.enable_config ? 1 : 0
  name     = "${var.project_name}-${var.environment}-config-recorder"
  role_arn = aws_iam_role.config[0].arn
  
  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
  
  depends_on = [aws_config_delivery_channel.main]
}

resource "aws_config_delivery_channel" "main" {
  count           = var.enable_config ? 1 : 0
  name            = "${var.project_name}-${var.environment}-config-delivery-channel"
  s3_bucket_name  = aws_s3_bucket.config[0].bucket
  s3_key_prefix   = "config"
  
  snapshot_delivery_properties {
    delivery_frequency = "Daily"
  }
}

resource "aws_s3_bucket" "config" {
  count         = var.enable_config ? 1 : 0
  bucket_prefix = "${var.project_name}-${var.environment}-aws-config"
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-config-bucket"
  })
}

resource "aws_iam_role" "config" {
  count = var.enable_config ? 1 : 0
  
  name_prefix = "${var.project_name}-${var.environment}-config"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-config-role"
  })
}

resource "aws_iam_role_policy_attachment" "config" {
  count = var.enable_config ? 1 : 0
  
  role       = aws_iam_role.config[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/ConfigRole"
}

# Data sources
data "aws_vpc" "main" {
  id = var.vpc_id
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}