# =============================================================================
# Aypa TaxAI - Terraform Variables
# =============================================================================

# -----------------------------------------------------------------------------
# General
# -----------------------------------------------------------------------------

variable "project_name" {
  description = "Name of the project, used as prefix for all resources"
  type        = string
  default     = "aypa-taxai"
}

variable "environment" {
  description = "Deployment environment (staging, production)"
  type        = string
  default     = "staging"

  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be either 'staging' or 'production'."
  }
}

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-south-1"
}

# -----------------------------------------------------------------------------
# Networking
# -----------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets (one per AZ)"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets (one per AZ)"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}

# -----------------------------------------------------------------------------
# ECS - Backend
# -----------------------------------------------------------------------------

variable "backend_cpu" {
  description = "CPU units for backend ECS task (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "backend_memory" {
  description = "Memory (MiB) for backend ECS task"
  type        = number
  default     = 1024
}

variable "backend_desired_count" {
  description = "Desired number of backend ECS tasks"
  type        = number
  default     = 2
}

variable "backend_max_count" {
  description = "Maximum number of backend ECS tasks for auto-scaling"
  type        = number
  default     = 6
}

# -----------------------------------------------------------------------------
# ECS - Frontend
# -----------------------------------------------------------------------------

variable "frontend_cpu" {
  description = "CPU units for frontend ECS task (1024 = 1 vCPU)"
  type        = number
  default     = 256
}

variable "frontend_memory" {
  description = "Memory (MiB) for frontend ECS task"
  type        = number
  default     = 512
}

variable "frontend_desired_count" {
  description = "Desired number of frontend ECS tasks"
  type        = number
  default     = 2
}

variable "frontend_max_count" {
  description = "Maximum number of frontend ECS tasks for auto-scaling"
  type        = number
  default     = 4
}

# -----------------------------------------------------------------------------
# RDS PostgreSQL
# -----------------------------------------------------------------------------

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "db_allocated_storage" {
  description = "Initial allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Maximum storage for autoscaling in GB"
  type        = number
  default     = 100
}

variable "db_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "aypa_taxai"
}

variable "db_username" {
  description = "Master username for the RDS instance"
  type        = string
  default     = "aypa_admin"
}

variable "db_password" {
  description = "Master password for the RDS instance"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.db_password) >= 16
    error_message = "Database password must be at least 16 characters long."
  }
}

# -----------------------------------------------------------------------------
# ElastiCache Redis
# -----------------------------------------------------------------------------

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.small"
}

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 30
}

# -----------------------------------------------------------------------------
# Application Secrets (passed via environment or tfvars)
# -----------------------------------------------------------------------------

variable "secret_key" {
  description = "Flask SECRET_KEY for session signing"
  type        = string
  sensitive   = true
  default     = ""
}

variable "jwt_secret_key" {
  description = "JWT signing secret key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "google_api_key" {
  description = "Google Gemini API key for AI features"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openai_api_key" {
  description = "OpenAI API key (fallback LLM)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "sentry_dsn" {
  description = "Sentry DSN for error monitoring"
  type        = string
  sensitive   = true
  default     = ""
}
