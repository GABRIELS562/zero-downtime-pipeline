variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for ALB"
  type        = list(string)
}

variable "security_group_ids" {
  description = "Security group IDs for ALB"
  type        = list(string)
}

variable "finance_target_group_arn" {
  description = "ARN of the finance trading target group"
  type        = string
}

variable "pharma_target_group_arn" {
  description = "ARN of the pharma manufacturing target group"
  type        = string
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for ALB"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Domain name for the ALB"
  type        = string
  default     = ""
}

variable "create_route53_zone" {
  description = "Create a Route53 hosted zone"
  type        = bool
  default     = true
}

variable "enable_waf" {
  description = "Enable AWS WAF for the ALB"
  type        = bool
  default     = true
}

variable "tags" {
  description = "A map of tags to assign to the resource"
  type        = map(string)
  default     = {}
}