# ECS Cluster with cost optimization
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}-cluster"
  
  # Cost optimization: Enable container insights only for production
  setting {
    name  = "containerInsights"
    value = var.environment == "production" ? "enabled" : "disabled"
  }
  
  # Capacity providers for cost optimization
  capacity_providers = ["FARGATE", "FARGATE_SPOT", "EC2"]
  
  default_capacity_provider_strategy {
    capacity_provider = var.enable_spot_instances ? "FARGATE_SPOT" : "FARGATE"
    weight           = 80
    base             = var.environment == "production" ? 2 : 1
  }
  
  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight           = 20
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-cluster"
  })
}

# Auto Scaling Group for EC2 capacity provider (additional cost optimization)
resource "aws_launch_template" "ecs" {
  name_prefix   = "${var.project_name}-${var.environment}-ecs-"
  image_id      = data.aws_ami.ecs_optimized.id
  instance_type = var.instance_types[0]
  
  vpc_security_group_ids = var.security_group_ids
  
  # Cost optimization: Mixed instance policy with Spot instances
  instance_market_options {
    market_type = var.enable_spot_instances ? "spot" : null
    dynamic "spot_options" {
      for_each = var.enable_spot_instances ? [1] : []
      content {
        spot_instance_type             = "one-time"
        instance_interruption_behavior = "terminate"
      }
    }
  }
  
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    cluster_name = aws_ecs_cluster.main.name
  }))
  
  iam_instance_profile {
    name = aws_iam_instance_profile.ecs.name
  }
  
  tag_specifications {
    resource_type = "instance"
    tags = merge(var.tags, {
      Name = "${var.project_name}-${var.environment}-ecs-instance"
    })
  }
  
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_group" "ecs" {
  name                = "${var.project_name}-${var.environment}-ecs-asg"
  vpc_zone_identifier = var.private_subnet_ids
  target_group_arns   = []
  health_check_type   = "EC2"
  health_check_grace_period = 300
  
  desired_capacity = var.desired_capacity
  max_size         = var.max_capacity
  min_size         = var.min_capacity
  
  # Mixed instances policy for cost optimization
  mixed_instances_policy {
    launch_template {
      launch_template_specification {
        launch_template_id = aws_launch_template.ecs.id
        version           = "$Latest"
      }
      
      dynamic "override" {
        for_each = var.instance_types
        content {
          instance_type = override.value
        }
      }
    }
    
    instances_distribution {
      on_demand_base_capacity                  = var.environment == "production" ? 1 : 0
      on_demand_percentage_above_base_capacity = var.enable_spot_instances ? 20 : 100
      spot_allocation_strategy                 = "diversified"
    }
  }
  
  # Scheduled scaling for cost optimization
  dynamic "tag" {
    for_each = var.tags
    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true
    }
  }
  
  tag {
    key                 = "AmazonECSManaged"
    value               = true
    propagate_at_launch = true
  }
}

# EC2 Capacity Provider
resource "aws_ecs_capacity_provider" "ec2" {
  name = "${var.project_name}-${var.environment}-ec2"
  
  auto_scaling_group_provider {
    auto_scaling_group_arn         = aws_autoscaling_group.ecs.arn
    managed_termination_protection = "ENABLED"
    
    managed_scaling {
      status                    = "ENABLED"
      target_capacity          = 80
      minimum_scaling_step_size = 1
      maximum_scaling_step_size = 1000
    }
  }
  
  tags = var.tags
}

# Task definitions for applications
resource "aws_ecs_task_definition" "finance_trading" {
  family                   = "${var.project_name}-finance-trading"
  requires_compatibilities = ["FARGATE", "EC2"]
  network_mode            = "awsvpc"
  cpu                     = var.finance_app_config.cpu
  memory                  = var.finance_app_config.memory
  execution_role_arn      = aws_iam_role.ecs_execution.arn
  task_role_arn          = aws_iam_role.ecs_task.arn
  
  container_definitions = jsonencode([
    {
      name         = "finance-trading"
      image        = "${aws_ecr_repository.finance_trading.repository_url}:latest"
      essential    = true
      
      portMappings = [
        {
          containerPort = var.finance_app_config.container_port
          protocol      = "tcp"
        }
      ]
      
      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "LOG_LEVEL"
          value = var.environment == "production" ? "INFO" : "DEBUG"
        },
        {
          name  = "MAX_LATENCY_MS"
          value = "50"
        },
        {
          name  = "SUCCESS_RATE_THRESHOLD"
          value = "99.99"
        }
      ]
      
      secrets = [
        {
          name      = "MARKET_DATA_API_KEY"
          valueFrom = aws_secretsmanager_secret.finance_secrets.arn
        }
      ]
      
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.finance_app_config.container_port}${var.finance_app_config.health_check_path} || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.finance_trading.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "ecs"
        }
      }
      
      # Cost optimization: CPU and memory reservations
      memoryReservation = var.finance_app_config.memory * 0.8
    },
    {
      name         = "latency-monitor"
      image        = "${aws_ecr_repository.latency_monitor.repository_url}:latest"
      essential    = false
      
      portMappings = [
        {
          containerPort = 8082
          protocol      = "tcp"
        }
      ]
      
      environment = [
        {
          name  = "TARGET_ENDPOINT"
          value = "http://localhost:${var.finance_app_config.container_port}/health/fast"
        },
        {
          name  = "MAX_LATENCY_MS"
          value = "50"
        }
      ]
      
      # Minimal resources for sidecar
      cpu    = 128
      memory = 256
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.finance_trading.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "latency-monitor"
        }
      }
    }
  ])
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-finance-trading-task"
    Application = "finance-trading"
  })
}

resource "aws_ecs_task_definition" "pharma_manufacturing" {
  family                   = "${var.project_name}-pharma-manufacturing"
  requires_compatibilities = ["FARGATE", "EC2"]
  network_mode            = "awsvpc"
  cpu                     = var.pharma_app_config.cpu
  memory                  = var.pharma_app_config.memory
  execution_role_arn      = aws_iam_role.ecs_execution.arn
  task_role_arn          = aws_iam_role.ecs_task.arn
  
  container_definitions = jsonencode([
    {
      name         = "pharma-manufacturing"
      image        = "${aws_ecr_repository.pharma_manufacturing.repository_url}:latest"
      essential    = true
      
      portMappings = [
        {
          containerPort = var.pharma_app_config.container_port
          protocol      = "tcp"
        }
      ]
      
      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "LOG_LEVEL"
          value = var.environment == "production" ? "INFO" : "DEBUG"
        },
        {
          name  = "EFFICIENCY_THRESHOLD"
          value = "98.0"
        },
        {
          name  = "FDA_AUDIT_ENABLED"
          value = "true"
        },
        {
          name  = "GMP_VALIDATION_ENABLED"
          value = "true"
        }
      ]
      
      secrets = [
        {
          name      = "BATCH_DATABASE_URL"
          valueFrom = aws_secretsmanager_secret.pharma_secrets.arn
        }
      ]
      
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.pharma_app_config.container_port}${var.pharma_app_config.health_check_path} || exit 1"]
        interval    = 60
        timeout     = 10
        retries     = 3
        startPeriod = 120
      }
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.pharma_manufacturing.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "ecs"
        }
      }
      
      memoryReservation = var.pharma_app_config.memory * 0.8
    }
  ])
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-pharma-manufacturing-task"
    Application = "pharma-manufacturing"
  })
}

# ECS Services
resource "aws_ecs_service" "finance_trading" {
  name            = "finance-trading"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.finance_trading.arn
  desired_count   = var.finance_app_config.desired_count
  
  capacity_provider_strategy {
    capacity_provider = var.enable_spot_instances ? "FARGATE_SPOT" : "FARGATE"
    weight           = 80
    base             = var.environment == "production" ? 1 : 0
  }
  
  capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight           = 20
  }
  
  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = var.security_group_ids
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.finance_trading.arn
    container_name   = "finance-trading"
    container_port   = var.finance_app_config.container_port
  }
  
  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
    
    deployment_circuit_breaker {
      enable   = true
      rollback = true
    }
  }
  
  # Market hours-based scaling
  lifecycle {
    ignore_changes = [desired_count]
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-finance-trading-service"
    Application = "finance-trading"
  })
  
  depends_on = [aws_lb_target_group.finance_trading]
}

resource "aws_ecs_service" "pharma_manufacturing" {
  name            = "pharma-manufacturing"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.pharma_manufacturing.arn
  desired_count   = var.pharma_app_config.desired_count
  
  capacity_provider_strategy {
    capacity_provider = var.enable_spot_instances ? "FARGATE_SPOT" : "FARGATE"
    weight           = 60
    base             = 1
  }
  
  capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight           = 40
  }
  
  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = var.security_group_ids
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.pharma_manufacturing.arn
    container_name   = "pharma-manufacturing"
    container_port   = var.pharma_app_config.container_port
  }
  
  deployment_configuration {
    maximum_percent         = 150
    minimum_healthy_percent = 100
    
    deployment_circuit_breaker {
      enable   = true
      rollback = true
    }
  }
  
  lifecycle {
    ignore_changes = [desired_count]
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-pharma-manufacturing-service"
    Application = "pharma-manufacturing"
  })
  
  depends_on = [aws_lb_target_group.pharma_manufacturing]
}

# Auto Scaling for ECS Services
resource "aws_appautoscaling_target" "finance_trading" {
  count = var.finance_app_config.enable_autoscaling ? 1 : 0
  
  max_capacity       = var.finance_app_config.max_capacity
  min_capacity       = var.finance_app_config.min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.finance_trading.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
  
  tags = var.tags
}

resource "aws_appautoscaling_policy" "finance_trading_cpu" {
  count = var.finance_app_config.enable_autoscaling ? 1 : 0
  
  name               = "${var.project_name}-finance-trading-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.finance_trading[0].resource_id
  scalable_dimension = aws_appautoscaling_target.finance_trading[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.finance_trading[0].service_namespace
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 300
  }
}

resource "aws_appautoscaling_target" "pharma_manufacturing" {
  count = var.pharma_app_config.enable_autoscaling ? 1 : 0
  
  max_capacity       = var.pharma_app_config.max_capacity
  min_capacity       = var.pharma_app_config.min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.pharma_manufacturing.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
  
  tags = var.tags
}

resource "aws_appautoscaling_policy" "pharma_manufacturing_cpu" {
  count = var.pharma_app_config.enable_autoscaling ? 1 : 0
  
  name               = "${var.project_name}-pharma-manufacturing-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.pharma_manufacturing[0].resource_id
  scalable_dimension = aws_appautoscaling_target.pharma_manufacturing[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.pharma_manufacturing[0].service_namespace
  
  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 80.0
    scale_in_cooldown  = 600
    scale_out_cooldown = 300
  }
}

# Data sources
data "aws_region" "current" {}

data "aws_ami" "ecs_optimized" {
  most_recent = true
  owners      = ["amazon"]
  
  filter {
    name   = "name"
    values = ["amzn2-ami-ecs-hvm-*-x86_64-ebs"]
  }
}