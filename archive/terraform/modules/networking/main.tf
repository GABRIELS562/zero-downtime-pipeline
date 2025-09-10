# Cost optimization: Use existing default VPC and create minimal subnets
data "aws_vpc" "selected" {
  id = var.vpc_id
}

data "aws_internet_gateway" "default" {
  filter {
    name   = "attachment.vpc-id"
    values = [var.vpc_id]
  }
}

# Get existing subnets in the VPC
data "aws_subnets" "existing" {
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }
}

data "aws_subnet" "existing" {
  for_each = toset(data.aws_subnets.existing.ids)
  id       = each.value
}

# Create private subnets only if needed (cost optimization)
resource "aws_subnet" "private" {
  count = length(var.availability_zones)
  
  vpc_id            = var.vpc_id
  cidr_block        = cidrsubnet(data.aws_vpc.selected.cidr_block, 4, count.index + 10)
  availability_zone = var.availability_zones[count.index]
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-private-subnet-${count.index + 1}"
    Type = "private"
    Tier = "application"
  })
}

# NAT Gateway for private subnets (cost optimization: single NAT for non-prod)
resource "aws_eip" "nat" {
  count = var.environment == "production" ? length(var.availability_zones) : 1
  
  domain = "vpc"
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-nat-eip-${count.index + 1}"
  })
  
  depends_on = [data.aws_internet_gateway.default]
}

# Use existing public subnets where possible
locals {
  public_subnets = [
    for subnet in data.aws_subnet.existing : subnet
    if subnet.map_public_ip_on_launch == true
  ]
  
  # Create public subnets only if we don't have enough existing ones
  need_public_subnets = length(local.public_subnets) < length(var.availability_zones)
}

resource "aws_subnet" "public" {
  count = local.need_public_subnets ? length(var.availability_zones) - length(local.public_subnets) : 0
  
  vpc_id                  = var.vpc_id
  cidr_block              = cidrsubnet(data.aws_vpc.selected.cidr_block, 4, count.index + 20)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-public-subnet-${count.index + 1}"
    Type = "public"
    Tier = "web"
  })
}

resource "aws_nat_gateway" "main" {
  count = var.environment == "production" ? length(var.availability_zones) : 1
  
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = length(local.public_subnets) > count.index ? local.public_subnets[count.index].id : aws_subnet.public[count.index].id
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-nat-gateway-${count.index + 1}"
  })
  
  depends_on = [data.aws_internet_gateway.default]
}

# Route tables for private subnets
resource "aws_route_table" "private" {
  count = length(aws_subnet.private)
  
  vpc_id = var.vpc_id
  
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = var.environment == "production" ? aws_nat_gateway.main[count.index].id : aws_nat_gateway.main[0].id
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-private-rt-${count.index + 1}"
    Type = "private"
  })
}

resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)
  
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# VPC Endpoints for cost optimization (reduce NAT Gateway usage)
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = var.vpc_id
  service_name = "com.amazonaws.${data.aws_region.current.name}.s3"
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-s3-endpoint"
  })
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  
  policy = jsonencode({
    Statement = [
      {
        Effect = "Allow"
        Principal = "*"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      }
    ]
  })
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-ecr-dkr-endpoint"
  })
}

resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  
  policy = jsonencode({
    Statement = [
      {
        Effect = "Allow"
        Principal = "*"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      }
    ]
  })
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-ecr-api-endpoint"
  })
}

resource "aws_vpc_endpoint" "logs" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.logs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-logs-endpoint"
  })
}

# Security group for VPC endpoints
resource "aws_security_group" "vpc_endpoints" {
  name_prefix = "${var.project_name}-${var.environment}-vpc-endpoints"
  vpc_id      = var.vpc_id
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.selected.cidr_block]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-vpc-endpoints-sg"
  })
}

# VPC Flow Logs for security monitoring
resource "aws_flow_log" "vpc" {
  count = var.enable_flow_logs ? 1 : 0
  
  iam_role_arn    = aws_iam_role.flow_log[0].arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_log[0].arn
  traffic_type    = "ALL"
  vpc_id          = var.vpc_id
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-vpc-flow-logs"
  })
}

resource "aws_cloudwatch_log_group" "vpc_flow_log" {
  count = var.enable_flow_logs ? 1 : 0
  
  name              = "/aws/vpc/flowlogs/${var.project_name}-${var.environment}"
  retention_in_days = var.environment == "production" ? 30 : 7
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-vpc-flow-logs"
  })
}

resource "aws_iam_role" "flow_log" {
  count = var.enable_flow_logs ? 1 : 0
  
  name_prefix = "${var.project_name}-${var.environment}-flow-log"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })
  
  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-flow-log-role"
  })
}

resource "aws_iam_role_policy" "flow_log" {
  count = var.enable_flow_logs ? 1 : 0
  
  name_prefix = "${var.project_name}-${var.environment}-flow-log"
  role        = aws_iam_role.flow_log[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

data "aws_region" "current" {}