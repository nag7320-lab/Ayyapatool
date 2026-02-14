#!/bin/bash
# =============================================================================
# Aypa TaxAI - EC2 Setup Script
# Runs on first boot to install Docker and deploy the app
# Optimized for t2.micro (1 GB RAM) with 2 GB swap
# =============================================================================

set -euo pipefail
exec > /var/log/aypa-setup.log 2>&1
echo "=== Aypa TaxAI Setup Started at $(date) ==="

# Create 2 GB swap file (critical for t2.micro with 1 GB RAM)
echo "Creating 2 GB swap..."
dd if=/dev/zero of=/swapfile bs=1M count=2048
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile swap swap defaults 0 0' >> /etc/fstab
echo "Swap enabled: $(swapon --show)"

# Update system
dnf update -y

# Install Docker
dnf install -y docker git
systemctl enable docker
systemctl start docker

# Install Docker Compose v2
DOCKER_COMPOSE_VERSION="v2.27.0"
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL "https://github.com/docker/compose/releases/download/$${DOCKER_COMPOSE_VERSION}/docker-compose-linux-x86_64" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Add ec2-user to docker group
usermod -aG docker ec2-user

# Create app directory
mkdir -p /opt/aypa
cd /opt/aypa

# Clone the repository
git clone https://github.com/nag7320-lab/Ayyapatool.git .

# Create .env file with secrets
cat > .env << ENVEOF
# Flask
FLASK_APP=app
FLASK_ENV=production
SECRET_KEY=${secret_key}
JWT_SECRET_KEY=${jwt_secret_key}

# Database
POSTGRES_DB=aypa_taxai
POSTGRES_USER=aypa
POSTGRES_PASSWORD=${postgres_password}
DATABASE_URL=postgresql://aypa:${postgres_password}@postgres:5432/aypa_taxai
REDIS_URL=redis://redis:6379/0

# AI
GOOGLE_API_KEY=${google_api_key}

# CORS - allow all for testing
CORS_ORIGINS=*
ENVEOF

# Get instance public IP for frontend env
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 || echo "localhost")
APP_HOST="${app_domain != "" ? app_domain : ""}"
if [ -z "$APP_HOST" ]; then
  APP_HOST="$PUBLIC_IP"
fi

# Create frontend env
cat > frontend/.env.local << FRONTEOF
NEXT_PUBLIC_API_URL=http://$APP_HOST/api
NEXT_PUBLIC_WS_URL=http://$APP_HOST
FRONTEOF

# Reduce gunicorn workers for t2.micro (1 vCPU)
sed -i 's/--workers", "4"/--workers", "1"/' infrastructure/docker/Dockerfile.backend
sed -i 's/--workers", "2"/--workers", "1"/' infrastructure/docker/Dockerfile.backend

# Set permissions
chown -R ec2-user:ec2-user /opt/aypa

# Build and start with Docker Compose (one service at a time to save RAM during build)
echo "Building and starting PostgreSQL and Redis..."
docker compose up -d postgres redis
sleep 10

echo "Building backend (this takes a few minutes)..."
docker compose up -d --build backend
sleep 30

echo "Building frontend (this takes a few minutes)..."
docker compose up -d --build frontend
sleep 20

echo "Starting nginx..."
docker compose up -d nginx

# Run database migrations
echo "Running database migrations..."
sleep 10
docker compose exec -T backend flask db upgrade 2>/dev/null || echo "Migration will run on next restart"

echo ""
echo "=== Aypa TaxAI Setup Complete at $(date) ==="
echo "Access the app at: http://$PUBLIC_IP"
echo ""
echo "Services status:"
docker compose ps
