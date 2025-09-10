# ECR Repositories for container images
resource "aws_ecr_repository" "finance_trading" {
  name                 = "${var.project_name}/finance-trading"
  image_tag_mutability = "MUTABLE"
  
  encryption_configuration {
    encryption_type = "AES256"
  }
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-finance-trading-ecr"
    Application = "finance-trading"
  })
}

resource "aws_ecr_repository" "pharma_manufacturing" {
  name                 = "${var.project_name}/pharma-manufacturing"
  image_tag_mutability = "MUTABLE"
  
  encryption_configuration {
    encryption_type = "AES256"
  }
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-pharma-manufacturing-ecr"
    Application = "pharma-manufacturing"
  })
}

resource "aws_ecr_repository" "latency_monitor" {
  name                 = "${var.project_name}/latency-monitor"
  image_tag_mutability = "MUTABLE"
  
  encryption_configuration {
    encryption_type = "AES256"
  }
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-latency-monitor-ecr"
    Application = "latency-monitor"
  })
}

# ECR Lifecycle policies for cost optimization
resource "aws_ecr_lifecycle_policy" "finance_trading" {
  repository = aws_ecr_repository.finance_trading.name
  
  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 production images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["prod", "production", "release"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Keep last 5 staging images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["staging", "stage"]
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 3
        description  = "Delete untagged images older than 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

resource "aws_ecr_lifecycle_policy" "pharma_manufacturing" {
  repository = aws_ecr_repository.pharma_manufacturing.name
  
  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 15 production images (FDA compliance)"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["prod", "production", "release"]
          countType     = "imageCountMoreThan"
          countNumber   = 15
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Keep last 5 staging images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["staging", "stage"]
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 3
        description  = "Delete untagged images older than 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

resource "aws_ecr_lifecycle_policy" "latency_monitor" {
  repository = aws_ecr_repository.latency_monitor.name
  
  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}