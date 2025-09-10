# CloudWatch Dashboard for Executive Overview
resource "aws_cloudwatch_dashboard" "executive_overview" {
  dashboard_name = "${var.project_name}-${var.environment}-executive-overview"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", "finance-trading", "ClusterName", var.ecs_cluster_name],
            [".", "MemoryUtilization", ".", ".", ".", "."],
            [".", "CPUUtilization", "ServiceName", "pharma-manufacturing", "ClusterName", var.ecs_cluster_name],
            [".", "MemoryUtilization", ".", ".", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "ECS Service Resource Utilization"
          period  = 300
        }
      },
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", var.alb_arn_suffix],
            [".", "RequestCount", ".", "."],
            [".", "HTTPCode_Target_2XX_Count", ".", "."],
            [".", "HTTPCode_Target_4XX_Count", ".", "."],
            [".", "HTTPCode_Target_5XX_Count", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "Application Load Balancer Metrics"
          period  = 300
        }
      },
      {
        type   = "log"
        width  = 24
        height = 6
        properties = {
          query   = "SOURCE '/ecs/${var.project_name}-${var.environment}/finance-trading' | fields @timestamp, @message | sort @timestamp desc | limit 100"
          region  = data.aws_region.current.name
          title   = "Recent Finance Trading Logs"
        }
      }
    ]
  })
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-executive-dashboard"
  })
}

# CloudWatch Alarms for critical metrics
resource "aws_cloudwatch_metric_alarm" "finance_cpu_high" {
  alarm_name          = "${var.project_name}-${var.environment}-finance-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ECS CPU utilization for finance trading"
  alarm_actions       = var.notification_endpoints
  
  dimensions = {
    ServiceName = "finance-trading"
    ClusterName = var.ecs_cluster_name
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-finance-cpu-alarm"
    Application = "finance-trading"
    Severity = "warning"
  })
}

resource "aws_cloudwatch_metric_alarm" "pharma_cpu_high" {
  alarm_name          = "${var.project_name}-${var.environment}-pharma-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "85"
  alarm_description   = "This metric monitors ECS CPU utilization for pharma manufacturing"
  alarm_actions       = var.notification_endpoints
  
  dimensions = {
    ServiceName = "pharma-manufacturing"
    ClusterName = var.ecs_cluster_name
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-pharma-cpu-alarm"
    Application = "pharma-manufacturing"
    Severity = "warning"
  })
}

resource "aws_cloudwatch_metric_alarm" "alb_response_time" {
  alarm_name          = "${var.project_name}-${var.environment}-alb-response-time"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Average"
  threshold           = "2"
  alarm_description   = "This metric monitors ALB response time"
  alarm_actions       = var.notification_endpoints
  
  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-alb-response-time-alarm"
    Severity = "warning"
  })
}

resource "aws_cloudwatch_metric_alarm" "alb_5xx_errors" {
  alarm_name          = "${var.project_name}-${var.environment}-alb-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors ALB 5XX errors"
  alarm_actions       = var.notification_endpoints
  
  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-alb-5xx-errors-alarm"
    Severity = "critical"
  })
}

# Custom CloudWatch metrics for business impact
resource "aws_cloudwatch_log_metric_filter" "finance_trading_errors" {
  name           = "${var.project_name}-${var.environment}-finance-trading-errors"
  log_group_name = "/ecs/${var.project_name}-${var.environment}/finance-trading"
  pattern        = "[timestamp, requestid, level=\"ERROR\", ...]"
  
  metric_transformation {
    name      = "FinanceTradingErrors"
    namespace = "ZeroDowntime/Finance"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "pharma_manufacturing_errors" {
  name           = "${var.project_name}-${var.environment}-pharma-manufacturing-errors"
  log_group_name = "/ecs/${var.project_name}-${var.environment}/pharma-manufacturing"
  pattern        = "[timestamp, requestid, level=\"ERROR\", ...]"
  
  metric_transformation {
    name      = "PharmaManufacturingErrors"
    namespace = "ZeroDowntime/Pharma"
    value     = "1"
  }
}

# Business metrics alarms
resource "aws_cloudwatch_metric_alarm" "finance_error_rate" {
  count = var.enable_business_metrics ? 1 : 0
  
  alarm_name          = "${var.project_name}-${var.environment}-finance-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "FinanceTradingErrors"
  namespace           = "ZeroDowntime/Finance"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "High error rate in finance trading application"
  alarm_actions       = var.notification_endpoints
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-finance-error-rate-alarm"
    Application = "finance-trading"
    Severity = "critical"
    BusinessImpact = "high"
  })
}

resource "aws_cloudwatch_metric_alarm" "pharma_error_rate" {
  count = var.enable_business_metrics ? 1 : 0
  
  alarm_name          = "${var.project_name}-${var.environment}-pharma-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "PharmaManufacturingErrors"
  namespace           = "ZeroDowntime/Pharma"
  period              = "300"
  statistic           = "Sum"
  threshold           = "3"
  alarm_description   = "High error rate in pharma manufacturing application"
  alarm_actions       = var.notification_endpoints
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-pharma-error-rate-alarm"
    Application = "pharma-manufacturing"
    Severity = "critical"
    BusinessImpact = "high"
  })
}

# CloudWatch Insights queries for operational intelligence
resource "aws_cloudwatch_query_definition" "deployment_performance" {
  name = "${var.project_name}-${var.environment}-deployment-performance"
  
  log_group_names = [
    "/ecs/${var.project_name}-${var.environment}/finance-trading",
    "/ecs/${var.project_name}-${var.environment}/pharma-manufacturing"
  ]
  
  query_string = <<-EOT
fields @timestamp, @message
| filter @message like /deployment/
| stats count() by bin(5m)
| sort @timestamp desc
EOT
}

resource "aws_cloudwatch_query_definition" "error_analysis" {
  name = "${var.project_name}-${var.environment}-error-analysis"
  
  log_group_names = [
    "/ecs/${var.project_name}-${var.environment}/finance-trading",
    "/ecs/${var.project_name}-${var.environment}/pharma-manufacturing"
  ]
  
  query_string = <<-EOT
fields @timestamp, @message, @logStream
| filter @message like /ERROR/
| stats count() by @logStream
| sort count desc
| limit 20
EOT
}

resource "aws_cloudwatch_query_definition" "business_impact_analysis" {
  count = var.enable_business_metrics ? 1 : 0
  
  name = "${var.project_name}-${var.environment}-business-impact-analysis"
  
  log_group_names = [
    "/ecs/${var.project_name}-${var.environment}/finance-trading",
    "/ecs/${var.project_name}-${var.environment}/pharma-manufacturing"
  ]
  
  query_string = <<-EOT
fields @timestamp, @message
| filter @message like /revenue/ or @message like /efficiency/ or @message like /trading_volume/
| stats count() by bin(1h)
| sort @timestamp desc
EOT
}

# CloudWatch Synthetics for endpoint monitoring
resource "aws_synthetics_canary" "finance_trading_health" {
  count = var.environment == "production" ? 1 : 0
  
  name                 = "${var.project_name}-${var.environment}-finance-health"
  artifact_s3_location = "s3://${aws_s3_bucket.synthetics_artifacts[0].bucket}/"
  execution_role_arn   = aws_iam_role.synthetics[0].arn
  handler              = "apiCanaryBlueprint.handler"
  zip_file            = "apicanary.zip"
  runtime_version     = "syn-nodejs-puppeteer-6.2"
  
  schedule {
    expression = "rate(5 minutes)"
  }
  
  run_config {
    timeout_in_seconds = 60
    memory_in_mb      = 960
  }
  
  success_retention_period = 2
  failure_retention_period = 14
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-finance-canary"
    Application = "finance-trading"
  })
}

# S3 bucket for Synthetics artifacts (production only)
resource "aws_s3_bucket" "synthetics_artifacts" {
  count         = var.environment == "production" ? 1 : 0
  bucket_prefix = "${var.project_name}-${var.environment}-synthetics"
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-synthetics-artifacts"
  })
}

resource "aws_s3_bucket_lifecycle_configuration" "synthetics_artifacts" {
  count  = var.environment == "production" ? 1 : 0
  bucket = aws_s3_bucket.synthetics_artifacts[0].id
  
  rule {
    id     = "synthetics_lifecycle"
    status = "Enabled"
    
    expiration {
      days = 30
    }
  }
}

# IAM role for Synthetics
resource "aws_iam_role" "synthetics" {
  count = var.environment == "production" ? 1 : 0
  
  name_prefix = "${var.project_name}-${var.environment}-synthetics"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-synthetics-role"
  })
}

resource "aws_iam_role_policy_attachment" "synthetics" {
  count = var.environment == "production" ? 1 : 0
  
  role       = aws_iam_role.synthetics[0].name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchSyntheticsExecutionRolePolicy"
}

# Cost optimization: CloudWatch logs retention
resource "aws_cloudwatch_log_group" "ecs_cluster" {
  name              = "/aws/ecs/cluster/${var.ecs_cluster_name}"
  retention_in_days = var.log_retention_days
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-ecs-cluster-logs"
  })
}

# Data sources
data "aws_region" "current" {}