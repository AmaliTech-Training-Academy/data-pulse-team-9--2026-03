# Production Readiness Checklist

Use this checklist to ensure your production environment is properly configured before going live.

## ✅ Pre-Deployment

### Configuration
- [ ] Generated strong passwords using `generate-prod-config.ps1`
- [ ] Updated `terraform.tfvars` with all required values
- [ ] GitHub Personal Access Token created with correct scopes
- [ ] Dev EC2 IP retrieved from dev environment
- [ ] Reviewed all configuration values for correctness
- [ ] Ensured no placeholder values remain (CHANGE_ME)

### AWS Setup
- [ ] AWS CLI configured with correct credentials
- [ ] Correct AWS region selected (eu-west-1)
- [ ] GitHub OIDC provider created in IAM
- [ ] Sufficient AWS service limits for resources
- [ ] S3 bucket for Terraform state exists

### Code Preparation
- [ ] All code committed to GitHub
- [ ] `main` branch is stable and tested
- [ ] `develop` branch is stable and tested
- [ ] Database migrations are up to date
- [ ] Environment variables documented

## ✅ Infrastructure Deployment

### Terraform
- [ ] `terraform init` completed successfully
- [ ] `terraform plan` reviewed (no errors)
- [ ] `terraform apply` completed (~70 resources created)
- [ ] All outputs saved (ALB DNS, ECR URLs, etc.)
- [ ] No Terraform errors or warnings

### AWS Resources Created
- [ ] VPC with public/private subnets
- [ ] Security groups configured
- [ ] RDS instances (operational + analytics)
- [ ] ElastiCache Redis cluster
- [ ] Application Load Balancer
- [ ] ECS Cluster and services
- [ ] ECR repositories (backend, etl, streamlit)
- [ ] Lambda functions (scheduler)
- [ ] Secrets Manager secrets
- [ ] SSM parameters
- [ ] IAM roles and policies
- [ ] CloudWatch log groups
- [ ] Amplify app

## ✅ Application Deployment

### Container Images
- [ ] Backend Docker image built
- [ ] Streamlit Docker image built
- [ ] ETL Docker image built
- [ ] All images pushed to ECR
- [ ] Image tags documented
- [ ] `terraform.tfvars` updated with real image URLs
- [ ] `terraform apply` run again with real images

### Database Setup
- [ ] Database migrations executed successfully
- [ ] Initial data loaded (if needed)
- [ ] Database backups configured
- [ ] Connection strings tested
- [ ] Analytics database initialized

### Application Health
- [ ] Backend health check returns 200 OK
- [ ] Streamlit dashboard loads correctly
- [ ] Frontend connects to backend API
- [ ] Celery workers processing tasks
- [ ] Celery beat scheduler running
- [ ] Redis connection working

## ✅ Security

### Credentials
- [ ] All passwords are strong (25+ characters)
- [ ] No credentials in code or version control
- [ ] Secrets stored in AWS Secrets Manager
- [ ] GitHub token has minimal required scopes
- [ ] Database passwords rotated from defaults

### Network Security
- [ ] Security groups follow least privilege
- [ ] RDS not publicly accessible
- [ ] Redis not publicly accessible
- [ ] VPC endpoints configured for AWS services
- [ ] ALB security group allows only HTTP/HTTPS

### Access Control
- [ ] IAM roles follow least privilege
- [ ] GitHub Actions role has minimal permissions
- [ ] ECS task roles have minimal permissions
- [ ] No root access to containers
- [ ] Session Manager enabled for debugging

## ✅ Monitoring & Logging

### CloudWatch
- [ ] Log groups created for all services
- [ ] Logs flowing from ECS tasks
- [ ] Log retention configured
- [ ] CloudWatch alarms set up (optional)

### Prometheus & Grafana
- [ ] Prometheus workspace created
- [ ] Grafana workspace created
- [ ] Data sources configured
- [ ] Dashboards imported (optional)

### Application Monitoring
- [ ] Health check endpoints working
- [ ] Error tracking configured
- [ ] Performance metrics collected
- [ ] Database query monitoring enabled

## ✅ Cost Optimization

### Scheduler
- [ ] Stop Lambda function tested
- [ ] Start Lambda function tested
- [ ] EventBridge rules configured (7am start, 8pm stop)
- [ ] Scheduler working on weekdays
- [ ] Services stopped on weekends

### Resource Sizing
- [ ] ECS task sizes appropriate (CPU/memory)
- [ ] RDS instance class appropriate (db.t4g.micro)
- [ ] ElastiCache node type appropriate (cache.t4g.micro)
- [ ] Fargate Spot enabled for cost savings
- [ ] ECR lifecycle policies configured (keep last 5 images)

## ✅ CI/CD Pipeline

### GitHub Actions
- [ ] GitHub secrets configured (AWS_REGION, AWS_ROLE_ARN)
- [ ] Workflow file created for main branch
- [ ] Test deployment to prod successful
- [ ] Blue/green deployment working
- [ ] Rollback tested
- [ ] Build notifications configured (optional)

### CodeDeploy
- [ ] Blue/green deployment configured
- [ ] Health checks configured
- [ ] Deployment hooks working
- [ ] Automatic rollback enabled
- [ ] Deployment notifications configured (optional)

## ✅ Backup & Recovery

### Database Backups
- [ ] RDS automated backups enabled (7 days)
- [ ] Backup retention period configured
- [ ] Point-in-time recovery tested
- [ ] Backup restoration procedure documented

### Disaster Recovery
- [ ] Recovery Time Objective (RTO) defined
- [ ] Recovery Point Objective (RPO) defined
- [ ] Disaster recovery plan documented
- [ ] Backup restoration tested

## ✅ Documentation

### Technical Documentation
- [ ] Architecture diagram created
- [ ] Deployment process documented
- [ ] Troubleshooting guide created
- [ ] Runbook for common operations
- [ ] API documentation updated

### Operational Documentation
- [ ] Access credentials documented (securely)
- [ ] On-call procedures defined
- [ ] Escalation paths documented
- [ ] Monitoring dashboard URLs documented
- [ ] Cost tracking setup

## ✅ Testing

### Functional Testing
- [ ] All API endpoints tested
- [ ] Frontend functionality verified
- [ ] Data pipeline tested end-to-end
- [ ] Scheduled tasks working
- [ ] File uploads working

### Performance Testing
- [ ] Load testing completed
- [ ] Response times acceptable
- [ ] Database query performance verified
- [ ] Caching working correctly
- [ ] Auto-scaling tested (if configured)

### Security Testing
- [ ] Vulnerability scan completed
- [ ] Penetration testing done (optional)
- [ ] Security headers configured
- [ ] CORS configured correctly
- [ ] Rate limiting tested

## ✅ Go-Live

### Pre-Launch
- [ ] All checklist items above completed
- [ ] Stakeholders notified of launch
- [ ] Support team briefed
- [ ] Monitoring dashboards ready
- [ ] Incident response plan ready

### Launch
- [ ] DNS updated (if using custom domain)
- [ ] SSL certificate validated (if using custom domain)
- [ ] Traffic routing verified
- [ ] All services healthy
- [ ] Monitoring active

### Post-Launch
- [ ] Monitor for 24 hours
- [ ] Check error rates
- [ ] Verify cost tracking
- [ ] Collect user feedback
- [ ] Document lessons learned

## 🚨 Emergency Contacts

- **AWS Support**: [Your support plan]
- **On-Call Engineer**: [Contact info]
- **Team Lead**: [Contact info]
- **DevOps Team**: [Contact info]

## 📊 Key Metrics to Monitor

- [ ] HTTP 5xx error rate < 1%
- [ ] HTTP 4xx error rate < 5%
- [ ] Average response time < 500ms
- [ ] Database CPU < 70%
- [ ] Database connections < 80% of max
- [ ] ECS task health check success rate > 99%
- [ ] Daily active users tracked
- [ ] Cost per day within budget

## 🎯 Success Criteria

- [ ] Application accessible via ALB DNS
- [ ] All services running and healthy
- [ ] No critical errors in logs
- [ ] Monitoring and alerting working
- [ ] Cost within expected range
- [ ] Team trained on operations
- [ ] Documentation complete

---

**Sign-off:**
- [ ] Technical Lead: _________________ Date: _______
- [ ] DevOps Lead: _________________ Date: _______
- [ ] Security Lead: _________________ Date: _______
- [ ] Product Owner: _________________ Date: _______
