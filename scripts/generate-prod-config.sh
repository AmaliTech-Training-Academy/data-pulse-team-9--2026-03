#!/bin/bash
# =============================================================
# Helper script to generate production configuration values
# =============================================================

echo "=========================================="
echo "DataPulse Production Setup Helper"
echo "=========================================="
echo ""

# Generate Django Secret Key
echo "1. Django Secret Key:"
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || \
python -c "import secrets; print(''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)))"
echo ""

# Generate strong passwords
echo "2. PostgreSQL Password:"
openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
echo ""

echo "3. Analytics DB Password:"
openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
echo ""

echo "4. Grafana Password:"
openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
echo ""

# Get Dev EC2 IP
echo "5. Dev EC2 IP Address:"
if [ -d "terraform/environments/dev" ]; then
    cd terraform/environments/dev
    terraform output -raw public_ip 2>/dev/null || echo "Run: cd terraform/environments/dev && terraform output public_ip"
    cd ../../..
else
    echo "Run: cd terraform/environments/dev && terraform output public_ip"
fi
echo ""

echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo "1. Copy the values above into terraform/environments/prod/terraform.tfvars"
echo "2. Get GitHub PAT from: https://github.com/settings/tokens"
echo "   Required scopes: repo, admin:repo_hook"
echo "3. Review and update all CHANGE_ME values"
echo "4. Deploy: cd terraform/environments/prod && terraform init && terraform apply"
echo ""
