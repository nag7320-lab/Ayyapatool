# =============================================================================
# Aypa TaxAI - Minimal Cost AWS Setup (Testing/Dev)
# Single EC2 instance running docker-compose (~$5-15/month)
# =============================================================================
#
# This is the CHEAPEST way to run Aypa TaxAI on AWS for testing.
# Everything runs on one EC2 instance via docker-compose:
#   - Backend (Flask)
#   - Frontend (Next.js)
#   - PostgreSQL
#   - Redis
#   - Nginx (reverse proxy)
#
# Usage:
#   cd infrastructure/terraform-lite
#   cp terraform.tfvars.example terraform.tfvars  # fill in your values
#   terraform init
#   terraform plan
#   terraform apply
#
# After deploy:
#   ssh -i aypa-key.pem ec2-user@<public-ip>
#   cd /opt/aypa && sudo docker-compose up -d
#
# Estimated cost: ~$5-15/month (t3.small in ap-south-1)
# =============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "aypa-taxai"
      Environment = "testing"
      ManagedBy   = "terraform"
    }
  }
}

# =============================================================================
# SSH Key Pair
# =============================================================================

resource "tls_private_key" "ssh" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "main" {
  key_name   = "aypa-taxai-key"
  public_key = tls_private_key.ssh.public_key_openssh
}

resource "local_file" "ssh_private_key" {
  content         = tls_private_key.ssh.private_key_pem
  filename        = "${path.module}/aypa-key.pem"
  file_permission = "0400"
}

# =============================================================================
# VPC (Default VPC - no cost)
# =============================================================================

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# =============================================================================
# Security Group
# =============================================================================

resource "aws_security_group" "aypa" {
  name_prefix = "aypa-taxai-"
  description = "Aypa TaxAI - HTTP, HTTPS, SSH access"
  vpc_id      = data.aws_vpc.default.id

  # SSH
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_allowed_cidrs
  }

  # HTTP
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # All outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    create_before_destroy = true
  }
}

# =============================================================================
# EC2 Instance
# =============================================================================

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "aypa" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.main.key_name
  vpc_security_group_ids = [aws_security_group.aypa.id]
  subnet_id              = tolist(data.aws_subnets.default.ids)[0]

  associate_public_ip_address = true

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.volume_size
    encrypted             = true
    delete_on_termination = true
  }

  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    postgres_password = var.postgres_password
    secret_key        = var.secret_key
    jwt_secret_key    = var.jwt_secret_key
    google_api_key    = var.google_api_key
    app_domain        = var.app_domain
  }))

  tags = {
    Name = "aypa-taxai-server"
  }

  lifecycle {
    ignore_changes = [ami]
  }
}

# =============================================================================
# Elastic IP (static IP - free when attached to running instance)
# =============================================================================

resource "aws_eip" "aypa" {
  instance = aws_instance.aypa.id
  domain   = "vpc"

  tags = {
    Name = "aypa-taxai-eip"
  }
}
