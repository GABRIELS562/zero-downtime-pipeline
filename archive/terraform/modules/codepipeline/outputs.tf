output "finance_pipeline_name" {
  description = "Name of the finance trading pipeline"
  value       = aws_codepipeline.finance_trading.name
}

output "pharma_pipeline_name" {
  description = "Name of the pharma manufacturing pipeline"
  value       = aws_codepipeline.pharma_manufacturing.name
}

output "finance_build_project_name" {
  description = "Name of the finance trading build project"
  value       = aws_codebuild_project.finance_trading.name
}

output "pharma_build_project_name" {
  description = "Name of the pharma manufacturing build project"
  value       = aws_codebuild_project.pharma_manufacturing.name
}

output "artifacts_bucket_name" {
  description = "Name of the CodePipeline artifacts bucket"
  value       = aws_s3_bucket.codepipeline_artifacts.bucket
}

output "kms_key_arn" {
  description = "ARN of the KMS key used for encryption"
  value       = aws_kms_key.codepipeline.arn
}

output "notification_topic_arn" {
  description = "ARN of the SNS topic for deployment notifications"
  value       = aws_sns_topic.deployment_notifications.arn
}

output "codebuild_role_arn" {
  description = "ARN of the CodeBuild IAM role"
  value       = aws_iam_role.codebuild.arn
}

output "codepipeline_role_arn" {
  description = "ARN of the CodePipeline IAM role"
  value       = aws_iam_role.codepipeline.arn
}