# Production Terraform Changes - Domain Optional

## Summary

Modified production Terraform configuration to work **without requiring a custom domain**. The infrastructure now uses AWS-provided DNS names (ALB DNS and Amplify default domains) instead of requiring custom domain setup.

## Files Modified

### 1. `terraform/modules/alb/main.tf`
**Changes:**
- Made `domain_name` variable optional (default: empty string)
- ACM certificate creation conditional (only if domain provided)
- HTTP listener behavior:
  - **With domain**: Redirects HTTP → HTTPS
  - **Without domain**: Serves traffic directly on HTTP
- HTTPS listener conditional (only created if domain provided)
- Separate Streamlit routing rules for HTTP and HTTPS listeners
- Updated outputs to handle both scenarios

**Result:** ALB works on HTTP (port 80) without SSL certificate when no domain is provided.

### 2. `terraform/modules/amplify/main.tf`
**Changes:**
- Made `domain_name` variable optional (default: empty string)
- WWW redirect rule conditional (only if domain provided)
- Domain association conditional (only if domain provided)
- Updated outputs to use Amplify default domain when custom domain not provided

**Result:** Amplify uses default domain (e.g., `main.d1a2b3c4.amplifyapp.com`) when no custom domain is provided.

### 3. `terraform/environments/prod/variables.tf`
**Changes:**
- Made `domain_name` variable optional with default empty string
- Added description explaining it's optional

**Result:** No error if domain_name is not provided or left empty.

### 4. `terraform/environments/prod/main.tf`
**Changes:**
- Updated ALB module call to pass optional domain_name
- Updated Amplify module call to conditionally set prod_api_url:
  - **With domain**: `https://yourdomain.com`
  - **Without domain**: `http://alb-dns-name.elb.amazonaws.com`
- Added comments explaining domain is optional

**Result:** Production environment works seamlessly with or without custom domain.

## Files Created

### 5. `terraform/environments/prod/terraform.tfvars`
**New file with:**
- Empty domain_name by default
- Placeholder values for all required variables
- Comments explaining how to get each value
- GitHub repo already filled in
- Secure password placeholders

### 6. `scripts/generate-prod-config.ps1`
**PowerShell helper script that generates:**
- Django secret key (50 characters)
- Strong passwords (25 characters each)
- Retrieves dev EC2 IP from Terraform output
- Provides next steps instructions

### 7. `scripts/generate-prod-config.sh`
**Bash version of the helper script** for Linux/Mac users.

### 8. `docs/PRODUCTION_DEPLOYMENT.md`
**Comprehensive deployment guide covering:**
- Architecture overview
- Prerequisites
- Step-by-step deployment instructions
- Configuration generation
- GitHub OIDC setup
- Container image building and pushing
- Database migrations
- Monitoring and troubleshooting
- Cost optimization details
- Cleanup instructions
- How to add custom domain later

## How It Works

### Without Custom Domain (Default)
```
User Request → ALB (HTTP:80) → ECS Tasks
                ↓
            Backend/Streamlit
```

**Access URLs:**
- Backend: `http://datapulse-prod-abc123.eu-west-1.elb.amazonaws.com`
- Streamlit: `http://datapulse-prod-abc123.eu-west-1.elb.amazonaws.com/streamlit`
- Frontend: `https://main.d1a2b3c4d5e6f7.amplifyapp.com`

### With Custom Domain (Optional)
```
User Request → Route53 → ALB (HTTPS:443 with ACM cert) → ECS Tasks
                          ↓
                      Backend/Streamlit
```

**Access URLs:**
- Backend: `https://yourdomain.com`
- Streamlit: `https://yourdomain.com/streamlit`
- Frontend: `https://yourdomain.com`

## Migration Path

To add a custom domain later:

1. Update `terraform.tfvars`:
   ```hcl
   domain_name = "yourdomain.com"
   ```

2. Set up DNS validation for ACM certificate

3. Run `terraform apply`

The infrastructure automatically:
- Creates ACM certificate
- Adds HTTPS listener to ALB
- Configures HTTP → HTTPS redirect
- Associates custom domain with Amplify
- Updates all service URLs

## Benefits

✅ **Faster setup** - No domain registration/DNS configuration needed
✅ **Lower cost** - No Route53 hosted zone charges ($0.50/month)
✅ **Simpler testing** - Use AWS-provided URLs immediately
✅ **Flexible** - Easy to add custom domain later without infrastructure changes
✅ **Production-ready** - All security and scaling features still work

## Testing Checklist

- [ ] Terraform plan shows no errors
- [ ] ALB created with HTTP listener
- [ ] ECS services can register with target groups
- [ ] Backend health checks pass on `/health/`
- [ ] Streamlit accessible via `/streamlit` path
- [ ] Amplify builds and deploys frontend
- [ ] Scheduler stops/starts services correctly
- [ ] Secrets Manager contains all credentials
- [ ] CloudWatch logs capture application logs
- [ ] Prometheus scrapes metrics successfully

## Security Considerations

**Without HTTPS:**
- Traffic between ALB and internet is unencrypted
- Suitable for testing/development
- **Not recommended for production with sensitive data**

**Recommendation:**
- Use domain-less setup for initial testing
- Add custom domain + HTTPS before handling real user data
- Consider using AWS Certificate Manager for free SSL certificates

## Cost Estimate (Without Domain)

**Monthly costs (eu-west-1, with scheduler):**
- ECS Fargate (Spot): ~$15-20
- RDS (2x db.t4g.micro): ~$25-30
- ElastiCache (cache.t4g.micro): ~$12-15
- ALB: ~$16-20
- Data transfer: ~$5-10
- Secrets Manager: ~$2
- CloudWatch Logs: ~$5

**Total: ~$80-100/month** (with 60% savings from scheduler)

**Without scheduler: ~$200-250/month**
