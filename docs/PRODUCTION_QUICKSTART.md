# Production Quick Start Guide

Deploy DataPulse to AWS production in 10 minutes (without custom domain).

## Prerequisites
- AWS CLI configured
- Terraform installed
- Dev environment deployed

## Quick Deploy

### 1. Generate Config (Windows)
```powershell
cd c:\Users\HP\Desktop\DatapulseMain
.\scripts\generate-prod-config.ps1
```

### 2. Get GitHub Token
https://github.com/settings/tokens → Generate new token → Select `repo` + `admin:repo_hook`

### 3. Update Config
Edit `terraform/environments/prod/terraform.tfvars`:
- Paste GitHub token
- Paste generated passwords
- Add dev EC2 IP

### 4. Setup GitHub OIDC (One-Time)
```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### 5. Deploy
```bash
cd terraform\environments\prod
terraform init
terraform apply
```

### 6. Save Outputs
```bash
terraform output
```

## Access Your App

- **Backend**: `http://YOUR_ALB_DNS`
- **Streamlit**: `http://YOUR_ALB_DNS/streamlit`
- **Frontend**: `https://main.YOUR_AMPLIFY_DOMAIN.amplifyapp.com`

## Next Steps

1. Push images to ECR (see full guide)
2. Update terraform.tfvars with real image URLs
3. Run `terraform apply` again
4. Run database migrations
5. Set up CI/CD pipeline

## Full Documentation

See `docs/PRODUCTION_DEPLOYMENT.md` for complete guide.

## Cost

~$80-100/month with auto scheduler (stops 8pm-7am weekdays + weekends)

## Cleanup

```bash
terraform destroy
```
