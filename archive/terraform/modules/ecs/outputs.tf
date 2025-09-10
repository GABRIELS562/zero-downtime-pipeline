output "cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "cluster_id" {
  description = "ID of the ECS cluster"
  value       = aws_ecs_cluster.main.id
}

output "cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "finance_service_name" {
  description = "Name of the finance trading ECS service"
  value       = aws_ecs_service.finance_trading.name
}

output "pharma_service_name" {
  description = "Name of the pharma manufacturing ECS service"
  value       = aws_ecs_service.pharma_manufacturing.name
}

output "finance_target_group_arn" {
  description = "ARN of the finance trading target group"
  value       = aws_lb_target_group.finance_trading.arn
}

output "pharma_target_group_arn" {
  description = "ARN of the pharma manufacturing target group"
  value       = aws_lb_target_group.pharma_manufacturing.arn
}

output "finance_ecr_repository_url" {
  description = "URL of the finance trading ECR repository"
  value       = aws_ecr_repository.finance_trading.repository_url
}

output "pharma_ecr_repository_url" {
  description = "URL of the pharma manufacturing ECR repository"
  value       = aws_ecr_repository.pharma_manufacturing.repository_url
}

output "latency_monitor_ecr_repository_url" {
  description = "URL of the latency monitor ECR repository"
  value       = aws_ecr_repository.latency_monitor.repository_url
}

output "task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  value       = aws_iam_role.ecs_execution.arn
}

output "task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task.arn
}

output "finance_log_group_name" {
  description = "Name of the finance trading CloudWatch log group"
  value       = aws_cloudwatch_log_group.finance_trading.name
}

output "pharma_log_group_name" {
  description = "Name of the pharma manufacturing CloudWatch log group"
  value       = aws_cloudwatch_log_group.pharma_manufacturing.name
}

output "audit_logs_bucket_name" {
  description = "Name of the audit logs S3 bucket"
  value       = aws_s3_bucket.audit_logs.bucket
}

output "batch_data_bucket_name" {
  description = "Name of the batch data S3 bucket"
  value       = aws_s3_bucket.batch_data.bucket
}