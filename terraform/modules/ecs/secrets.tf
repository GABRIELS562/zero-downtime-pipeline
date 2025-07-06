# Secrets Manager for application secrets
resource "aws_secretsmanager_secret" "finance_secrets" {
  name_prefix = "${var.project_name}-${var.environment}-finance-secrets"
  description = "Secrets for finance trading application"
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-finance-secrets"
    Application = "finance-trading"
  })
}

resource "aws_secretsmanager_secret_version" "finance_secrets" {
  secret_id = aws_secretsmanager_secret.finance_secrets.id
  secret_string = jsonencode({
    MARKET_DATA_API_KEY = "your-market-data-api-key"
    DATABASE_URL        = "postgres://user:pass@finance-db.example.com:5432/trading"
    REDIS_URL          = "redis://finance-redis.example.com:6379"
    JWT_SECRET         = "your-jwt-secret-key"
  })
}

resource "aws_secretsmanager_secret" "pharma_secrets" {
  name_prefix = "${var.project_name}-${var.environment}-pharma-secrets"
  description = "Secrets for pharma manufacturing application"
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-pharma-secrets"
    Application = "pharma-manufacturing"
  })
}

resource "aws_secretsmanager_secret_version" "pharma_secrets" {
  secret_id = aws_secretsmanager_secret.pharma_secrets.id
  secret_string = jsonencode({
    BATCH_DATABASE_URL    = "postgres://user:pass@pharma-db.example.com:5432/manufacturing"
    AUDIT_DATABASE_URL    = "postgres://user:pass@audit-db.example.com:5432/audit"
    SENSOR_API_KEY        = "your-sensor-api-key"
    DIGITAL_SIGNATURE_KEY = "your-digital-signature-key"
  })
}