#!/bin/bash
# =============================================================================
# Aypa TaxAI - One-Command AWS Deploy Script
# Deploys the entire app on a single EC2 instance (~$10-15/month)
#
# Prerequisites:
#   1. AWS CLI configured: aws configure
#   2. Terraform installed: https://developer.hashicorp.com/terraform/install
#   3. Google Gemini API key (optional): https://aistudio.google.com/apikey
#
# Usage:
#   chmod +x deploy.sh
#   ./deploy.sh
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════╗"
echo "║        Aypa TaxAI - AWS Deploy           ║"
echo "║     Single EC2 (FREE TIER eligible)      ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI not found. Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html${NC}"
    exit 1
fi

if ! command -v terraform &> /dev/null; then
    echo -e "${RED}ERROR: Terraform not found. Install: https://developer.hashicorp.com/terraform/install${NC}"
    exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}ERROR: AWS not configured. Run: aws configure${NC}"
    exit 1
fi

echo -e "${GREEN}All prerequisites met!${NC}"

# Navigate to terraform-lite directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="$SCRIPT_DIR/infrastructure/terraform-lite"
cd "$TF_DIR"

# Check if terraform.tfvars exists
if [ ! -f terraform.tfvars ]; then
    echo ""
    echo -e "${YELLOW}Creating terraform.tfvars with secure defaults...${NC}"

    POSTGRES_PASS=$(openssl rand -hex 16)
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)

    echo ""
    read -p "Enter your Google Gemini API key (press Enter to skip): " GEMINI_KEY
    echo ""
    read -p "AWS region [ap-south-1]: " AWS_REGION
    AWS_REGION=${AWS_REGION:-ap-south-1}
    echo ""
    read -p "Instance type [t2.micro=FREE tier (default), t3.small=\$15/mo]: " INSTANCE
    INSTANCE=${INSTANCE:-t2.micro}
    echo ""
    read -p "Domain name (press Enter to use IP address): " DOMAIN

    cat > terraform.tfvars << EOF
aws_region        = "$AWS_REGION"
instance_type     = "$INSTANCE"
volume_size       = 30
ssh_allowed_cidrs = ["0.0.0.0/0"]
app_domain        = "$DOMAIN"

postgres_password = "$POSTGRES_PASS"
secret_key        = "$SECRET_KEY"
jwt_secret_key    = "$JWT_SECRET"
google_api_key    = "$GEMINI_KEY"
EOF

    echo -e "${GREEN}terraform.tfvars created with secure random passwords!${NC}"
fi

# Terraform init and apply
echo ""
echo -e "${YELLOW}Initializing Terraform...${NC}"
terraform init

echo ""
echo -e "${YELLOW}Planning infrastructure...${NC}"
terraform plan -out=tfplan

echo ""
echo -e "${YELLOW}Review the plan above. Cost: FREE with t2.micro (if eligible), ~\$15/mo otherwise${NC}"
read -p "Deploy now? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo -e "${YELLOW}Deploying to AWS...${NC}"
terraform apply tfplan

# Get outputs
PUBLIC_IP=$(terraform output -raw public_ip)
SSH_CMD=$(terraform output -raw ssh_command)
APP_URL=$(terraform output -raw app_url)

echo ""
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║              DEPLOYMENT SUCCESSFUL!                  ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║                                                      ║"
echo "  App URL:  $APP_URL"
echo "  Server:   $PUBLIC_IP"
echo "  SSH:      $SSH_CMD"
echo "║                                                      ║"
echo "║  NOTE: The server is installing Docker & building    ║"
echo "║  the app. This takes ~5-10 minutes on first boot.   ║"
echo "║                                                      ║"
echo "║  Monitor progress:                                   ║"
echo "║  $SSH_CMD"
echo "║  tail -f /var/log/aypa-setup.log                    ║"
echo "║                                                      ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "SSH key saved to: $TF_DIR/aypa-key.pem"
echo ""
echo -e "${YELLOW}To destroy (stop billing): cd $TF_DIR && terraform destroy${NC}"
