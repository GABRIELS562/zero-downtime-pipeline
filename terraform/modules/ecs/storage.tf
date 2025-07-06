# S3 buckets for application data and compliance
resource "aws_s3_bucket" "audit_logs" {
  bucket_prefix = "${var.project_name}-${var.environment}-audit-logs"
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-audit-logs"
    Purpose = "FDA compliance audit logs"
    Retention = "7-years"
  })
}

resource "aws_s3_bucket_versioning" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_encryption" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id
  
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id
  
  rule {
    id     = "audit_log_lifecycle"
    status = "Enabled"
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    
    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }
    
    # FDA compliance: 7 years retention
    expiration {
      days = 2555
    }
    
    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

resource "aws_s3_bucket_public_access_block" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Batch data storage for pharma manufacturing
resource "aws_s3_bucket" "batch_data" {
  bucket_prefix = "${var.project_name}-${var.environment}-batch-data"
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-batch-data"
    Purpose = "Manufacturing batch data"
    Retention = "7-years"
  })
}

resource "aws_s3_bucket_versioning" "batch_data" {
  bucket = aws_s3_bucket.batch_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_encryption" "batch_data" {
  bucket = aws_s3_bucket.batch_data.id
  
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "batch_data" {
  bucket = aws_s3_bucket.batch_data.id
  
  rule {
    id     = "batch_data_lifecycle"
    status = "Enabled"
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    
    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }
    
    expiration {
      days = 2555
    }
  }
}

resource "aws_s3_bucket_public_access_block" "batch_data" {
  bucket = aws_s3_bucket.batch_data.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "finance_trading" {
  name              = "/ecs/${var.project_name}-${var.environment}/finance-trading"
  retention_in_days = var.environment == "production" ? 90 : 14
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-finance-trading-logs"
    Application = "finance-trading"
  })
}

resource "aws_cloudwatch_log_group" "pharma_manufacturing" {
  name              = "/ecs/${var.project_name}-${var.environment}/pharma-manufacturing"
  retention_in_days = var.environment == "production" ? 2555 : 30  # FDA compliance for production
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-pharma-manufacturing-logs"
    Application = "pharma-manufacturing"
  })
}