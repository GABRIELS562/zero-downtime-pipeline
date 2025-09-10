# S3 bucket for CodePipeline artifacts
resource "aws_s3_bucket" "codepipeline_artifacts" {
  bucket_prefix = "${var.project_name}-${var.environment}-pipeline-artifacts"
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-pipeline-artifacts"
  })
}

resource "aws_s3_bucket_encryption" "codepipeline_artifacts" {
  bucket = aws_s3_bucket.codepipeline_artifacts.id
  
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "codepipeline_artifacts" {
  bucket = aws_s3_bucket.codepipeline_artifacts.id
  
  rule {
    id     = "artifacts_lifecycle"
    status = "Enabled"
    
    expiration {
      days = 30
    }
    
    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }
}

resource "aws_s3_bucket_public_access_block" "codepipeline_artifacts" {
  bucket = aws_s3_bucket.codepipeline_artifacts.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CodeBuild projects for each application
resource "aws_codebuild_project" "finance_trading" {
  name          = "${var.project_name}-${var.environment}-finance-trading-build"
  description   = "Build project for finance trading application"
  service_role  = aws_iam_role.codebuild.arn
  
  artifacts {
    type = "CODEPIPELINE"
  }
  
  cache {
    type  = var.enable_build_caching ? "S3" : "NO_CACHE"
    location = var.enable_build_caching ? "${aws_s3_bucket.codepipeline_artifacts.bucket}/cache/finance-trading" : null
  }
  
  environment {
    compute_type                = var.build_compute_type
    image                      = "aws/codebuild/amazonlinux2-x86_64-standard:4.0"
    type                       = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"
    privileged_mode            = true  # Required for Docker builds
    
    environment_variable {
      name  = "AWS_DEFAULT_REGION"
      value = data.aws_region.current.name
    }
    
    environment_variable {
      name  = "AWS_ACCOUNT_ID"
      value = data.aws_caller_identity.current.account_id
    }
    
    environment_variable {
      name  = "IMAGE_REPO_NAME"
      value = "${var.project_name}/finance-trading"
    }
    
    environment_variable {
      name  = "IMAGE_TAG"
      value = "latest"
    }
    
    environment_variable {
      name  = "ENVIRONMENT"
      value = var.environment
    }
  }
  
  source {
    type = "CODEPIPELINE"
    buildspec = "apps/finance-trading/buildspec.yml"
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-finance-trading-build"
    Application = "finance-trading"
  })
}

resource "aws_codebuild_project" "pharma_manufacturing" {
  name          = "${var.project_name}-${var.environment}-pharma-manufacturing-build"
  description   = "Build project for pharma manufacturing application"
  service_role  = aws_iam_role.codebuild.arn
  
  artifacts {
    type = "CODEPIPELINE"
  }
  
  cache {
    type  = var.enable_build_caching ? "S3" : "NO_CACHE"
    location = var.enable_build_caching ? "${aws_s3_bucket.codepipeline_artifacts.bucket}/cache/pharma-manufacturing" : null
  }
  
  environment {
    compute_type                = var.build_compute_type
    image                      = "aws/codebuild/amazonlinux2-x86_64-standard:4.0"
    type                       = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"
    privileged_mode            = true
    
    environment_variable {
      name  = "AWS_DEFAULT_REGION"
      value = data.aws_region.current.name
    }
    
    environment_variable {
      name  = "AWS_ACCOUNT_ID"
      value = data.aws_caller_identity.current.account_id
    }
    
    environment_variable {
      name  = "IMAGE_REPO_NAME"
      value = "${var.project_name}/pharma-manufacturing"
    }
    
    environment_variable {
      name  = "IMAGE_TAG"
      value = "latest"
    }
    
    environment_variable {
      name  = "ENVIRONMENT"
      value = var.environment
    }
  }
  
  source {
    type = "CODEPIPELINE"
    buildspec = "apps/pharma-manufacturing/buildspec.yml"
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-pharma-manufacturing-build"
    Application = "pharma-manufacturing"
  })
}

# CodePipeline for Finance Trading
resource "aws_codepipeline" "finance_trading" {
  name     = "${var.project_name}-${var.environment}-finance-trading-pipeline"
  role_arn = aws_iam_role.codepipeline.arn
  
  artifact_store {
    location = aws_s3_bucket.codepipeline_artifacts.bucket
    type     = "S3"
    
    encryption_key {
      id   = aws_kms_key.codepipeline.arn
      type = "KMS"
    }
  }
  
  stage {
    name = "Source"
    
    action {
      name             = "Source"
      category         = "Source"
      owner            = "ThirdParty"
      provider         = "GitHub"
      version          = "1"
      output_artifacts = ["source_output"]
      
      configuration = {
        Owner      = split("/", var.github_repo)[0]
        Repo       = split("/", var.github_repo)[1]
        Branch     = var.github_branch
        OAuthToken = data.aws_secretsmanager_secret_version.github_token.secret_string
      }
    }
  }
  
  stage {
    name = "Build"
    
    action {
      name             = "Build"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      input_artifacts  = ["source_output"]
      output_artifacts = ["build_output"]
      version          = "1"
      
      configuration = {
        ProjectName = aws_codebuild_project.finance_trading.name
      }
    }
  }
  
  stage {
    name = "Deploy"
    
    action {
      name            = "Deploy"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "ECS"
      input_artifacts = ["build_output"]
      version         = "1"
      
      configuration = {
        ClusterName = var.ecs_cluster_name
        ServiceName = var.ecs_service_names.finance
        FileName    = "imagedefinitions.json"
      }
    }
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-finance-trading-pipeline"
    Application = "finance-trading"
  })
}

# CodePipeline for Pharma Manufacturing
resource "aws_codepipeline" "pharma_manufacturing" {
  name     = "${var.project_name}-${var.environment}-pharma-manufacturing-pipeline"
  role_arn = aws_iam_role.codepipeline.arn
  
  artifact_store {
    location = aws_s3_bucket.codepipeline_artifacts.bucket
    type     = "S3"
    
    encryption_key {
      id   = aws_kms_key.codepipeline.arn
      type = "KMS"
    }
  }
  
  stage {
    name = "Source"
    
    action {
      name             = "Source"
      category         = "Source"
      owner            = "ThirdParty"
      provider         = "GitHub"
      version          = "1"
      output_artifacts = ["source_output"]
      
      configuration = {
        Owner      = split("/", var.github_repo)[0]
        Repo       = split("/", var.github_repo)[1]
        Branch     = var.github_branch
        OAuthToken = data.aws_secretsmanager_secret_version.github_token.secret_string
      }
    }
  }
  
  stage {
    name = "Build"
    
    action {
      name             = "Build"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      input_artifacts  = ["source_output"]
      output_artifacts = ["build_output"]
      version          = "1"
      
      configuration = {
        ProjectName = aws_codebuild_project.pharma_manufacturing.name
      }
    }
  }
  
  # Manual approval for production pharma deployments (FDA compliance)
  dynamic "stage" {
    for_each = var.environment == "production" ? [1] : []
    content {
      name = "Approval"
      
      action {
        name     = "ManualApproval"
        category = "Approval"
        owner    = "AWS"
        provider = "Manual"
        version  = "1"
        
        configuration = {
          NotificationArn = aws_sns_topic.deployment_notifications.arn
          CustomData      = "Please review and approve the pharma manufacturing deployment for FDA compliance."
        }
      }
    }
  }
  
  stage {
    name = "Deploy"
    
    action {
      name            = "Deploy"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "ECS"
      input_artifacts = ["build_output"]
      version         = "1"
      
      configuration = {
        ClusterName = var.ecs_cluster_name
        ServiceName = var.ecs_service_names.pharma
        FileName    = "imagedefinitions.json"
      }
    }
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-pharma-manufacturing-pipeline"
    Application = "pharma-manufacturing"
  })
}

# KMS key for pipeline encryption
resource "aws_kms_key" "codepipeline" {
  description             = "KMS key for CodePipeline encryption"
  deletion_window_in_days = 7
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-codepipeline-key"
  })
}

resource "aws_kms_alias" "codepipeline" {
  name          = "alias/${var.project_name}-${var.environment}-codepipeline"
  target_key_id = aws_kms_key.codepipeline.key_id
}

# SNS topic for deployment notifications
resource "aws_sns_topic" "deployment_notifications" {
  name = "${var.project_name}-${var.environment}-deployment-notifications"
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-deployment-notifications"
  })
}

# EventBridge rules for pipeline state changes
resource "aws_cloudwatch_event_rule" "codepipeline_state_change" {
  name        = "${var.project_name}-${var.environment}-pipeline-state-change"
  description = "Capture pipeline state changes"
  
  event_pattern = jsonencode({
    source      = ["aws.codepipeline"]
    detail-type = ["CodePipeline Pipeline Execution State Change"]
    detail = {
      pipeline = [
        aws_codepipeline.finance_trading.name,
        aws_codepipeline.pharma_manufacturing.name
      ]
    }
  })
  
  tags = var.tags
}

resource "aws_cloudwatch_event_target" "sns" {
  rule      = aws_cloudwatch_event_rule.codepipeline_state_change.name
  target_id = "SendToSNS"
  arn       = aws_sns_topic.deployment_notifications.arn
}

# Data sources
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

data "aws_secretsmanager_secret" "github_token" {
  name = var.github_token_secret
}

data "aws_secretsmanager_secret_version" "github_token" {
  secret_id = data.aws_secretsmanager_secret.github_token.id
}