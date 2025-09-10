output "dashboard_url" {
  description = "URL of the CloudWatch dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${aws_cloudwatch_dashboard.executive_overview.dashboard_name}"
}

output "finance_cpu_alarm_arn" {
  description = "ARN of the finance CPU alarm"
  value       = aws_cloudwatch_metric_alarm.finance_cpu_high.arn
}

output "pharma_cpu_alarm_arn" {
  description = "ARN of the pharma CPU alarm"
  value       = aws_cloudwatch_metric_alarm.pharma_cpu_high.arn
}

output "alb_response_time_alarm_arn" {
  description = "ARN of the ALB response time alarm"
  value       = aws_cloudwatch_metric_alarm.alb_response_time.arn
}

output "alb_5xx_errors_alarm_arn" {
  description = "ARN of the ALB 5XX errors alarm"
  value       = aws_cloudwatch_metric_alarm.alb_5xx_errors.arn
}

output "finance_error_rate_alarm_arn" {
  description = "ARN of the finance error rate alarm"
  value       = var.enable_business_metrics ? aws_cloudwatch_metric_alarm.finance_error_rate[0].arn : null
}

output "pharma_error_rate_alarm_arn" {
  description = "ARN of the pharma error rate alarm"
  value       = var.enable_business_metrics ? aws_cloudwatch_metric_alarm.pharma_error_rate[0].arn : null
}

output "synthetics_canary_arn" {
  description = "ARN of the CloudWatch Synthetics canary"
  value       = var.environment == "production" ? aws_synthetics_canary.finance_trading_health[0].arn : null
}

output "log_insights_queries" {
  description = "CloudWatch Insights query definitions"
  value = {
    deployment_performance = aws_cloudwatch_query_definition.deployment_performance.name
    error_analysis        = aws_cloudwatch_query_definition.error_analysis.name
    business_impact       = var.enable_business_metrics ? aws_cloudwatch_query_definition.business_impact_analysis[0].name : null
  }
}