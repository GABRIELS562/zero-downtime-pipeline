variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "ecs_service_names" {
  description = "Names of the ECS services"
  type = object({
    finance = string
    pharma  = string
  })
}

variable "github_repo" {
  description = "GitHub repository in format owner/repo"
  type        = string
}

variable "github_branch" {
  description = "GitHub branch to deploy from"
  type        = string
  default     = "main"
}

variable "github_token_secret" {
  description = "AWS Secrets Manager secret name containing GitHub token"
  type        = string
}

variable "build_timeout" {
  description = "Build timeout in minutes"
  type        = number
  default     = 15
}

variable "build_compute_type" {
  description = "CodeBuild compute type"
  type        = string
  default     = "BUILD_GENERAL1_SMALL"
  
  validation {
    condition = contains([
      "BUILD_GENERAL1_SMALL",
      "BUILD_GENERAL1_MEDIUM",
      "BUILD_GENERAL1_LARGE",
      "BUILD_GENERAL1_2XLARGE"
    ], var.build_compute_type)
    error_message = "Build compute type must be one of: BUILD_GENERAL1_SMALL, BUILD_GENERAL1_MEDIUM, BUILD_GENERAL1_LARGE, BUILD_GENERAL1_2XLARGE."
  }
}

variable "enable_build_caching" {
  description = "Enable build caching for faster builds"
  type        = bool
  default     = true
}

variable "tags" {
  description = "A map of tags to assign to the resource"
  type        = map(string)
  default     = {}
}