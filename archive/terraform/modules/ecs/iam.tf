# ECS Task Execution Role
resource "aws_iam_role" "ecs_execution" {
  name_prefix = "${var.project_name}-${var.environment}-ecs-execution"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-ecs-execution-role"
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Additional permissions for ECS execution role
resource "aws_iam_role_policy" "ecs_execution_additional" {
  name_prefix = "${var.project_name}-${var.environment}-ecs-execution-additional"
  role        = aws_iam_role.ecs_execution.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "kms:Decrypt"
        ]
        Resource = [
          aws_secretsmanager_secret.finance_secrets.arn,
          aws_secretsmanager_secret.pharma_secrets.arn,
          "arn:aws:kms:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:key/*"
        ]
      }
    ]
  })
}

# ECS Task Role (least privilege principle)
resource "aws_iam_role" "ecs_task" {
  name_prefix = "${var.project_name}-${var.environment}-ecs-task"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-ecs-task-role"
  })
}

# Task role policy for CloudWatch metrics and logging
resource "aws_iam_role_policy" "ecs_task_cloudwatch" {
  name_prefix = "${var.project_name}-${var.environment}-ecs-task-cloudwatch"
  role        = aws_iam_role.ecs_task.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:ListMetrics"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "cloudwatch:namespace" = [
              "ZeroDowntime/Finance",
              "ZeroDowntime/Pharma",
              "ECS/ContainerInsights"
            ]
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.finance_trading.arn}:*",
          "${aws_cloudwatch_log_group.pharma_manufacturing.arn}:*"
        ]
      }
    ]
  })
}

# EC2 Instance Role for ECS cluster
resource "aws_iam_role" "ecs_instance" {
  name_prefix = "${var.project_name}-${var.environment}-ecs-instance"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-ecs-instance-role"
  })
}

resource "aws_iam_role_policy_attachment" "ecs_instance" {
  role       = aws_iam_role.ecs_instance.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

resource "aws_iam_role_policy_attachment" "ecs_instance_ssm" {
  role       = aws_iam_role.ecs_instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ecs" {
  name_prefix = "${var.project_name}-${var.environment}-ecs"
  role        = aws_iam_role.ecs_instance.name
  
  tags = var.tags
}

# Application-specific IAM policies
resource "aws_iam_role_policy" "finance_trading_specific" {
  name_prefix = "${var.project_name}-${var.environment}-finance-trading"
  role        = aws_iam_role.ecs_task.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.finance_secrets.arn
      },
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
      }
    ]
  })
}

resource "aws_iam_role_policy" "pharma_manufacturing_specific" {
  name_prefix = "${var.project_name}-${var.environment}-pharma-manufacturing"
  role        = aws_iam_role.ecs_task.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.pharma_secrets.arn
      },
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
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = [
          "${aws_s3_bucket.audit_logs.arn}/*",
          "${aws_s3_bucket.batch_data.arn}/*"
        ]
      }
    ]
  })
}

# Data sources
data "aws_caller_identity" "current" {}