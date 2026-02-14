# =============================================================================
# Aypa TaxAI - Minimal Setup Variables
# =============================================================================

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "instance_type" {
  description = "EC2 instance type (t2.micro = FREE TIER)"
  type        = string
  default     = "t2.micro"
}

variable "volume_size" {
  description = "Root EBS volume size in GB (free tier: up to 30 GB gp2/gp3)"
  type        = number
  default     = 30
}

variable "ssh_allowed_cidrs" {
  description = "CIDR blocks allowed to SSH (set to your IP for security)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "app_domain" {
  description = "Domain name for the app (leave empty to use IP address)"
  type        = string
  default     = ""
}

# -----------------------------------------------------------------------------
# Secrets
# -----------------------------------------------------------------------------

variable "postgres_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.postgres_password) >= 12
    error_message = "Password must be at least 12 characters."
  }
}

variable "secret_key" {
  description = "Flask SECRET_KEY"
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "JWT signing secret"
  type        = string
  sensitive   = true
}

variable "google_api_key" {
  description = "Google Gemini API key"
  type        = string
  sensitive   = true
  default     = ""
}
