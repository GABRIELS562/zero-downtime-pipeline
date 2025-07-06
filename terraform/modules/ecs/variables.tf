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

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "Public subnet IDs"
  type        = list(string)
}

variable "security_group_ids" {
  description = "Security group IDs for ECS tasks"
  type        = list(string)
}

variable "enable_spot_instances" {
  description = "Enable Spot instances for cost optimization"
  type        = bool
  default     = true
}

variable "desired_capacity" {
  description = "Desired capacity for ECS Auto Scaling Group"
  type        = number
  default     = 2
}

variable "min_capacity" {
  description = "Minimum capacity for ECS Auto Scaling Group"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum capacity for ECS Auto Scaling Group"
  type        = number
  default     = 6
}

variable "instance_types" {
  description = "Instance types for ECS cluster"
  type        = list(string)
  default     = ["t3.medium", "t3.large", "m5.large"]
}

variable "finance_app_config" {
  description = "Configuration for finance trading application"
  type = object({
    cpu                = number
    memory             = number
    desired_count      = number
    min_capacity       = number
    max_capacity       = number
    health_check_path  = string
    container_port     = number
    enable_autoscaling = bool
  })
}

variable "pharma_app_config" {
  description = "Configuration for pharma manufacturing application"
  type = object({
    cpu                = number
    memory             = number
    desired_count      = number
    min_capacity       = number
    max_capacity       = number
    health_check_path  = string
    container_port     = number
    enable_autoscaling = bool
  })
}

variable "tags" {
  description = "A map of tags to assign to the resource"
  type        = map(string)
  default     = {}
}