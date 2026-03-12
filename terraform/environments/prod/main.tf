terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
  backend "s3" {
    bucket         = "datapulse-team9-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "eu-west-1"
    use_lockfile = true
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "datapulse"
      Environment = "prod"
      ManagedBy   = "terraform"
    }
  }
}

locals {
  env                    = "prod"
  ssm_prefix             = "/datapulse/prod"
  secrets_manager_prefix = "datapulse/prod"  # pragma: allowlist secret
}

# -----------------------------------------------------------
# VPC — 10.0.0.0/16 · 4 VPC endpoints (no NAT gateway)
# -----------------------------------------------------------
module "vpc" {
  source     = "../../modules/vpc"
  env        = local.env
  vpc_cidr   = var.vpc_cidr
  azs        = var.availability_zones
  aws_region = var.aws_region
}

# -----------------------------------------------------------
# Security Groups
# -----------------------------------------------------------
module "security" {
  source   = "../../modules/security"
  env      = local.env
  vpc_id   = module.vpc.vpc_id
  vpc_cidr = module.vpc.vpc_cidr
}

# -----------------------------------------------------------
# SSM Parameter Store — non-sensitive config (free tier)
# -----------------------------------------------------------
resource "aws_ssm_parameter" "config" {
  for_each = {
    postgres_user          = var.postgres_user
    postgres_db            = var.postgres_db
    analytics_user         = var.analytics_user
    analytics_db           = var.analytics_db
    django_settings_module = "datapulse.settings.prod"
    grafana_user           = var.grafana_user
  }
  name  = "${local.ssm_prefix}/${each.key}"
  type  = "String"
  value = each.value
}

# -----------------------------------------------------------
# Secrets Manager — passwords + connection URLs
# 7-day recovery window on deletion
# -----------------------------------------------------------
locals {
  secrets = {
    postgres_password  = var.postgres_password
    analytics_password = var.analytics_password
    secret_key         = var.secret_key
    grafana_password   = var.grafana_password
    database_url       = "postgresql://${var.postgres_user}:${var.postgres_password}@${module.rds.operational_endpoint}/${var.postgres_db}"
    target_db_url      = "postgresql://${var.analytics_user}:${var.analytics_password}@${module.rds.analytics_endpoint}/${var.analytics_db}"
    redis_url          = "redis://${module.elasticache.endpoint}:6379/0"
  }
}

resource "aws_secretsmanager_secret" "main" {
  for_each                = local.secrets
  name                    = "${local.secrets_manager_prefix}/${each.key}"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "main" {
  for_each      = local.secrets
  secret_id     = aws_secretsmanager_secret.main[each.key].id
  secret_string = each.value
}

# -----------------------------------------------------------
# ECR — 3 repositories, scan on push, keep last 5 images
# -----------------------------------------------------------
resource "aws_ecr_repository" "repos" {
  for_each             = toset(["backend", "etl", "streamlit"])
  name                 = "datapulse-${each.key}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration { scan_on_push = true }
  encryption_configuration { encryption_type = "AES256" }
}

resource "aws_ecr_lifecycle_policy" "repos" {
  for_each   = aws_ecr_repository.repos
  repository = each.value.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 5 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = { type = "expire" }
    }]
  })
}

# -----------------------------------------------------------
# RDS — 2x db.t4g.micro (Graviton) with schedule stop/start
# -----------------------------------------------------------
module "rds" {
  source               = "../../modules/rds"
  env                  = local.env
  private_subnet_ids   = module.vpc.private_subnet_ids
  rds_sg_id            = module.security.rds_sg_id
  instance_class       = "db.t4g.micro"
  operational_username = var.postgres_user
  operational_password = var.postgres_password
  operational_db_name  = var.postgres_db
  analytics_username   = var.analytics_user
  analytics_password   = var.analytics_password
  analytics_db_name    = var.analytics_db
}

# -----------------------------------------------------------
# ElastiCache Redis — cache.t4g.micro (Graviton)
# -----------------------------------------------------------
module "elasticache" {
  source             = "../../modules/elasticache"
  env                = local.env
  private_subnet_ids = module.vpc.private_subnet_ids
  redis_sg_id        = module.security.redis_sg_id
  node_type          = "cache.t4g.micro"
}

# -----------------------------------------------------------
# ALB — HTTP (or HTTPS if domain provided), blue + green target groups per service
# -----------------------------------------------------------
module "alb" {
  source            = "../../modules/alb"
  env               = local.env
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  alb_sg_id         = module.security.alb_sg_id
  domain_name       = var.domain_name  # Empty string = HTTP only, no ACM cert
}

# -----------------------------------------------------------
# ECS — Fargate Spot + rightsized tasks + scale-to-zero
# First apply: use placeholder images, then real images after
# ECR is populated by the first CD run
# -----------------------------------------------------------
module "ecs" {
  source                  = "../../modules/ecs"
  env                     = local.env
  aws_region              = var.aws_region
  private_subnet_ids      = module.vpc.private_subnet_ids
  ecs_sg_id               = module.security.ecs_sg_id
  backend_tg_arn          = module.alb.backend_tg_arn
  streamlit_tg_arn        = module.alb.streamlit_tg_arn
  backend_image           = var.backend_image
  etl_image               = var.etl_image
  streamlit_image         = var.streamlit_image
  backend_cpu             = 256
  backend_memory          = 512
  backend_task_count      = 1
  celery_worker_count     = 1
  ssm_prefix              = local.ssm_prefix
  secrets_manager_prefix  = local.secrets_manager_prefix

  depends_on = [
    aws_secretsmanager_secret_version.main,
    aws_ssm_parameter.config,
  ]
}

# -----------------------------------------------------------
# CodeDeploy — blue/green canary with Lambda hooks
# -----------------------------------------------------------
module "codedeploy" {
  source                   = "../../modules/codedeploy"
  env                      = local.env
  aws_region               = var.aws_region
  cluster_name             = module.ecs.cluster_name
  backend_service_name     = module.ecs.backend_service_name
  streamlit_service_name   = module.ecs.streamlit_service_name
  https_listener_arn       = module.alb.https_listener_arn
  test_listener_arn        = module.alb.test_listener_arn
  backend_blue_tg_name     = module.alb.backend_tg_name
  backend_green_tg_name    = module.alb.backend_green_tg_name
  streamlit_blue_tg_name   = module.alb.streamlit_tg_name
  streamlit_green_tg_name  = module.alb.streamlit_green_tg_name
  backend_blue_tg_arn      = module.alb.backend_tg_arn
  backend_green_tg_arn     = module.alb.backend_green_tg_arn
  alb_arn_suffix           = module.alb.alb_arn_suffix
  backend_tg_arn_suffix    = module.alb.backend_tg_arn_suffix
  alb_dns                  = module.alb.alb_dns
  ssm_prefix               = local.ssm_prefix

  depends_on = [module.ecs, module.alb]
}

# -----------------------------------------------------------
# Scheduler — stops ECS + RDS at 8pm, starts at 7am weekdays
# -----------------------------------------------------------
module "scheduler" {
  source           = "../../modules/scheduler"
  env              = local.env
  aws_region       = var.aws_region
  ssm_prefix       = local.ssm_prefix
  mode             = "ecs"
  ecs_cluster_name = module.ecs.cluster_name
  ecs_services = [
    "datapulse-prod-backend",
    "datapulse-prod-celery-worker",
    "datapulse-prod-celery-beat",
    "datapulse-prod-streamlit",
  ]
  rds_instance_ids = [
    module.rds.operational_id,
    module.rds.analytics_id,
  ]

  depends_on = [module.ecs, module.rds]
}

# -----------------------------------------------------------
# Amplify — Next.js frontend (optional, only if you have frontend code)
# -----------------------------------------------------------
module "amplify" {
  source              = "../../modules/amplify"
  app_name            = "datapulse-frontend"
  github_repo         = var.github_repo
  github_access_token = var.github_access_token
  domain_name         = var.domain_name  # Empty string = use Amplify default domain
  dev_api_url         = "http://placeholder-not-used"  # Dev branch preview not needed
  prod_api_url        = var.domain_name != "" ? "https://${var.domain_name}" : "http://${module.alb.alb_dns}"
}

# -----------------------------------------------------------
# GitHub Actions OIDC — no static keys stored in GitHub
# Run once: aws iam create-open-id-connect-provider before apply
# -----------------------------------------------------------
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

resource "aws_iam_role" "github_actions" {
  name = "datapulse-prod-github-actions"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = data.aws_iam_openid_connect_provider.github.arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:${var.github_repo}:ref:refs/heads/main"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "github_actions" {
  name = "datapulse-prod-ci"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability", "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage", "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart", "ecr:CompleteLayerUpload", "ecr:PutImage"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:UpdateService", "ecs:DescribeServices",
          "ecs:RegisterTaskDefinition", "ecs:DescribeTaskDefinition",
          "iam:PassRole"
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["codedeploy:CreateDeployment", "codedeploy:GetDeployment",
                    "codedeploy:StopDeployment", "codedeploy:GetDeploymentConfig",
                    "codedeploy:RegisterApplicationRevision"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["ssm:GetParameter"]
        Resource = "arn:aws:ssm:${var.aws_region}:*:parameter${local.ssm_prefix}/*"
      }
    ]
  })
}

# -----------------------------------------------------------
# Managed Prometheus + Grafana
# -----------------------------------------------------------
resource "aws_prometheus_workspace" "main" {
  alias = "datapulse-prod"
}

# IAM role for Grafana workspace
resource "aws_iam_role" "grafana" {
  name = "datapulse-${local.env}-grafana"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "grafana.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "grafana_cloudwatch" {
  role       = aws_iam_role.grafana.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonGrafanaCloudWatchAccess"
}

resource "aws_grafana_workspace" "main" {
  name                     = "datapulse-prod"
  account_access_type      = "CURRENT_ACCOUNT"
  authentication_providers = ["AWS_SSO"]
  permission_type          = "SERVICE_MANAGED"
  data_sources             = ["PROMETHEUS", "CLOUDWATCH", "XRAY"]
  role_arn                 = aws_iam_role.grafana.arn
}
