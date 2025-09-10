output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = aws_security_group.alb.id
}

output "ecs_security_group_id" {
  description = "ID of the ECS tasks security group"
  value       = aws_security_group.ecs_tasks.id
}

output "rds_security_group_id" {
  description = "ID of the RDS security group"
  value       = aws_security_group.rds.id
}

output "redis_security_group_id" {
  description = "ID of the Redis security group"
  value       = aws_security_group.redis.id
}

output "vpc_endpoints_security_group_id" {
  description = "ID of the VPC endpoints security group"
  value       = aws_security_group.vpc_endpoints.id
}

output "cross_service_role_arn" {
  description = "ARN of the cross-service access role"
  value       = aws_iam_role.cross_service_access.arn
}

output "security_hub_account_id" {
  description = "AWS Security Hub account ID"
  value       = var.enable_security_hub ? aws_securityhub_account.main[0].id : null
}

output "guardduty_detector_id" {
  description = "AWS GuardDuty detector ID"
  value       = var.enable_guardduty ? aws_guardduty_detector.main[0].id : null
}

output "config_recorder_name" {
  description = "AWS Config recorder name"
  value       = var.enable_config ? aws_config_configuration_recorder.main[0].name : null
}

output "private_network_acl_id" {
  description = "ID of the private network ACL"
  value       = aws_network_acl.private.id
}