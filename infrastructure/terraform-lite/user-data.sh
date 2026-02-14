#!/bin/bash
# =============================================================================
# Aypa TaxAI - EC2 Setup Script
# Runs on first boot to install Docker and deploy the app
# =============================================================================

set -euo pipefail
exec > /var/log/aypa-setup.log 2>&1
echo "=== Aypa TaxAI Setup Started at $(date) ==="

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
cat > .env << 'ENVEOF'
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

# Create frontend env
cat > frontend/.env.local << 'FRONTEOF'
NEXT_PUBLIC_API_URL=http://${app_domain != "" ? app_domain : "localhost"}/api
NEXT_PUBLIC_WS_URL=http://${app_domain != "" ? app_domain : "localhost"}
FRONTEOF

# Set permissions
chown -R ec2-user:ec2-user /opt/aypa

# Build and start with Docker Compose
docker compose up -d --build

# Wait for backend to be healthy and run migrations
echo "Waiting for database to be ready..."
sleep 15
docker compose exec -T backend flask db upgrade 2>/dev/null || echo "Migration will run on next restart"

echo "=== Aypa TaxAI Setup Complete at $(date) ==="
echo "Access the app at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
