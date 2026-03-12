# Production Deployment Guide

This guide walks you through deploying the DataPulse application to AWS production environment **without a custom domain**.

## 🏗️ Production Architecture

- **ECS Fargate** - Scalable container orchestration
- **RDS PostgreSQL** - 2 managed databases (operational + analytics)
- **ElastiCache Redis** - Managed Redis cluster
- **Application Load Balancer** - HTTP load balancing (HTTPS if domain added later)
- **ECR** - Container image registry
- **CodeDeploy** - Blue/green deployments
- **AWS Amplify** - Next.js frontend hosting
- **Managed Prometheus + Grafana** - AWS-managed monitoring
- **Cost Scheduler** - Auto stop/start (7am-8pm weekdays)

## 📋 Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.5.0 installed
3. **GitHub Personal Access Token** with `repo` and `admin:repo_hook` scopes
4. **Dev environment** already deployed (to get EC2 IP)

## 🚀 Deployment Steps

### Step 1: Generate Configuration Values

**On Windows:**
```powershell
cd c:\Users\HP\Desktop\DatapulseMain
.\scripts\generate-prod-config.ps1
```

**On Linux/Mac:**
```bash
cd /path/to/DatapulseMain
bash scripts/generate-prod-config.sh
```

This will generate:
- Django secret key
- Strong passwords for databases and Grafana
- Dev EC2 IP address

### Step 2: Get GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `admin:repo_hook`
4. Copy the token (starts with `ghp_`)

### Step 3: Update terraform.tfvars

Edit `terraform/environments/prod/terraform.tfvars`:

```hcl
# Update these values:
github_access_token = "ghp_YOUR_TOKEN_HERE"
dev_ec2_ip          = "YOUR_DEV_IP_HERE"

# Paste generated passwords:
postgres_password   = "GENERATED_PASSWORD_1"
analytics_password  = "GENERATED_PASSWORD_2"
secret_key          = "GENERATED_SECRET_KEY"
grafana_password    = "GENERATED_PASSWORD_3"
```

### Step 4: Set Up GitHub OIDC Provider (One-Time)

This allows GitHub Actions to deploy without storing AWS credentials:

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
  --region eu-west-1
```

### Step 5: Deploy Infrastructure

```bash
cd terraform/environments/prod
terraform init
terraform plan
terraform apply
```

This will create ~70 AWS resources. Review the plan carefully before applying.

**Expected duration:** 15-20 minutes

### Step 6: Note Important Outputs

After deployment, save these outputs:

```bash
terraform output
```

Key outputs:
- `alb_dns_name` - Your application URL (e.g., `datapulse-prod-123.eu-west-1.elb.amazonaws.com`)
- `ecr_repositories` - Container registry URLs
- `amplify_default_domain` - Frontend URL
- `rds_endpoints` - Database connection strings

### Step 7: Build and Push Container Images

```bash
# Get ECR login
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.eu-west-1.amazonaws.com

# Build and push backend
cd backend
docker build -t datapulse-backend .
docker tag datapulse-backend:latest YOUR_ACCOUNT_ID.dkr.ecr.eu-west-1.amazonaws.com/datapulse-backend:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.eu-west-1.amazonaws.com/datapulse-backend:latest

# Build and push streamlit
cd ../data-engineering
docker build -t datapulse-streamlit .
docker tag datapulse-streamlit:latest YOUR_ACCOUNT_ID.dkr.ecr.eu-west-1.amazonaws.com/datapulse-streamlit:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.eu-west-1.amazonaws.com/datapulse-streamlit:latest

# Build and push ETL
cd ..
docker build -f devops/Dockerfile.pipeline -t datapulse-etl .
docker tag datapulse-etl:latest YOUR_ACCOUNT_ID.dkr.ecr.eu-west-1.amazonaws.com/datapulse-etl:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.eu-west-1.amazonaws.com/datapulse-etl:latest
```

### Step 8: Update ECS Services with Real Images

Update `terraform.tfvars` with real ECR image URLs:

```hcl
backend_image   = "YOUR_ACCOUNT_ID.dkr.ecr.eu-west-1.amazonaws.com/datapulse-backend:latest"
etl_image       = "YOUR_ACCOUNT_ID.dkr.ecr.eu-west-1.amazonaws.com/datapulse-etl:latest"
streamlit_image = "YOUR_ACCOUNT_ID.dkr.ecr.eu-west-1.amazonaws.com/datapulse-streamlit:latest"
```

Then apply:
```bash
terraform apply
```

### Step 9: Run Database Migrations

```bash
# Get ECS task ARN
TASK_ARN=$(aws ecs list-tasks --cluster datapulse-prod --service-name datapulse-prod-backend --region eu-west-1 --query 'taskArns[0]' --output text)

# Run migrations
aws ecs execute-command \
  --cluster datapulse-prod \
  --task $TASK_ARN \
  --container backend \
  --command "python manage.py migrate" \
  --interactive \
  --region eu-west-1
```

### Step 10: Access Your Application

- **Backend API**: `http://YOUR_ALB_DNS_NAME`
- **Streamlit Dashboard**: `http://YOUR_ALB_DNS_NAME/streamlit`
- **Frontend**: `https://main.YOUR_AMPLIFY_DOMAIN.amplifyapp.com`
- **Grafana**: Access via AWS Console → Amazon Managed Grafana

## 🔒 Security Notes

- All secrets stored in AWS Secrets Manager
- Database credentials encrypted at rest
- VPC endpoints for private AWS service access
- Security groups restrict traffic to necessary ports only
- No hardcoded credentials in code

## 💰 Cost Optimization

**Automatic Scheduler:**
- Stops ECS services and RDS at 8pm UTC weekdays
- Starts everything at 7am UTC weekdays
- Completely stopped on weekends
- **Estimated savings: ~60% on compute costs**

**Manual Control:**
```bash
# Stop everything now
aws lambda invoke --function-name datapulse-prod-stop /dev/stdout

# Start everything now
aws lambda invoke --function-name datapulse-prod-start /dev/stdout
```

## 📊 Monitoring

**CloudWatch Logs:**
```bash
aws logs tail /ecs/datapulse-prod-backend --follow
```

**Prometheus Metrics:**
- Access via AWS Console → Amazon Managed Service for Prometheus

**Grafana Dashboards:**
- Access via AWS Console → Amazon Managed Grafana

## 🔄 CI/CD Pipeline

After infrastructure is deployed, set up GitHub Actions for automated deployments:

1. Add GitHub secrets (Settings → Secrets → Actions):
   - `AWS_REGION`: `eu-west-1`
   - `AWS_ROLE_ARN`: Get from `terraform output github_actions_role_arn`

2. Push to `main` branch triggers automatic deployment

## 🆘 Troubleshooting

**ECS tasks not starting:**
```bash
aws ecs describe-services --cluster datapulse-prod --services datapulse-prod-backend --region eu-west-1
```

**Database connection issues:**
- Check security groups allow ECS → RDS traffic
- Verify connection strings in Secrets Manager

**ALB health checks failing:**
- Ensure `/health/` endpoint returns 200
- Check ECS task logs for errors

## 🧹 Cleanup

To destroy all production resources:

```bash
cd terraform/environments/prod
terraform destroy
```

**Warning:** This will delete all data. Ensure you have backups!

## 📝 Adding Custom Domain Later

If you want to add a custom domain later:

1. Update `terraform.tfvars`:
   ```hcl
   domain_name = "yourdomain.com"
   ```

2. Create Route53 hosted zone or use external DNS

3. Add DNS validation records for ACM certificate

4. Apply changes:
   ```bash
   terraform apply
   ```

The infrastructure will automatically switch from HTTP to HTTPS with your custom domain.

## 🎯 Next Steps

- Set up CloudWatch alarms for critical metrics
- Configure backup retention policies
- Implement WAF rules for additional security
- Set up cross-region replication for disaster recovery
- Configure custom Grafana dashboards
