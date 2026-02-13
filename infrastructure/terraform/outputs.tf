# =============================================================================
# Aypa TaxAI - Terraform Outputs
# =============================================================================

# -----------------------------------------------------------------------------
# Load Balancer
# -----------------------------------------------------------------------------

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Hosted zone ID of the ALB (for Route53 alias records)"
  value       = aws_lb.main.zone_id
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.main.arn
}

output "application_url" {
  description = "URL to access the application"
  value       = "http://${aws_lb.main.dns_name}"
}

# -----------------------------------------------------------------------------
# RDS PostgreSQL
# -----------------------------------------------------------------------------

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint (host:port)"
  value       = aws_db_instance.main.endpoint
}

output "rds_hostname" {
  description = "RDS PostgreSQL hostname"
  value       = aws_db_instance.main.address
}

output "rds_port" {
  description = "RDS PostgreSQL port"
  value       = aws_db_instance.main.port
}

output "rds_database_name" {
  description = "Name of the PostgreSQL database"
  value       = aws_db_instance.main.db_name
}

output "rds_connection_string" {
  description = "PostgreSQL connection string (without password)"
  value       = "postgresql://${var.db_username}:****@${aws_db_instance.main.endpoint}/${var.db_name}"
  sensitive   = false
}

# -----------------------------------------------------------------------------
# ElastiCache Redis
# -----------------------------------------------------------------------------

output "redis_endpoint" {
  description = "ElastiCache Redis primary endpoint"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "redis_port" {
  description = "ElastiCache Redis port"
  value       = 6379
}

output "redis_connection_string" {
  description = "Redis connection string"
  value       = "redis://${aws_elasticache_replication_group.main.primary_endpoint_address}:6379"
}

# -----------------------------------------------------------------------------
# S3 Bucket
# -----------------------------------------------------------------------------

output "s3_bucket_name" {
  description = "Name of the S3 bucket for document storage"
  value       = aws_s3_bucket.main.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.main.arn
}

output "s3_bucket_domain" {
  description = "Regional domain name of the S3 bucket"
  value       = aws_s3_bucket.main.bucket_regional_domain_name
}

# -----------------------------------------------------------------------------
# ECR Repositories
# -----------------------------------------------------------------------------

output "ecr_backend_repository_url" {
  description = "URL of the backend ECR repository"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_frontend_repository_url" {
  description = "URL of the frontend ECR repository"
  value       = aws_ecr_repository.frontend.repository_url
}

# -----------------------------------------------------------------------------
# ECS Cluster
# -----------------------------------------------------------------------------

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "ecs_backend_service_name" {
  description = "Name of the backend ECS service"
  value       = aws_ecs_service.backend.name
}

output "ecs_frontend_service_name" {
  description = "Name of the frontend ECS service"
  value       = aws_ecs_service.frontend.name
}

# -----------------------------------------------------------------------------
# Networking
# -----------------------------------------------------------------------------

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}
