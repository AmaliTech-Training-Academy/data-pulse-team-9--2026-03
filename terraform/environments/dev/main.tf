terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
    tls = { source = "hashicorp/tls", version = "~> 4.0" }
  }
  backend "s3" {
    bucket       = "datapulse-team9-terraform-state"
    key          = "dev/terraform.tfstate"
    region       = "eu-west-1"
    use_lockfile = true
    encrypt      = true
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "datapulse"
      Environment = "dev"
      ManagedBy   = "terraform"
    }
  }
}

locals {
  env        = "dev"
  ssm_prefix = "/datapulse/dev"
}

# -----------------------------------------------------------
# VPC — 10.1.0.0/16 (separate from prod 10.0.0.0/16)
# Dev EC2 sits in public subnet — no VPC endpoints needed
# -----------------------------------------------------------
# Add keypair module
module "keypair" {
  source = "../../modules/keypair"

  env = var.env
}

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
  source           = "../../modules/security"
  env              = local.env
  vpc_id           = module.vpc.vpc_id
  vpc_cidr         = module.vpc.vpc_cidr
  allowed_ssh_cidr = var.allowed_cidr
}

# -----------------------------------------------------------
# SSM Parameter Store — all dev secrets
# Stored as SecureString (KMS encrypted) for passwords
# -----------------------------------------------------------
resource "aws_ssm_parameter" "dev_config" {
  for_each = {
    postgres_user          = var.postgres_user
    postgres_db            = var.postgres_db
    analytics_user         = var.analytics_user
    analytics_db           = var.analytics_db
    django_settings_module = "datapulse.settings.dev"
    grafana_user           = var.grafana_user
  }
  name  = "${local.ssm_prefix}/${each.key}"
  type  = "String"
  value = each.value
}

resource "aws_ssm_parameter" "dev_secrets" {
  for_each = {
    postgres_password  = var.postgres_password
    analytics_password = var.analytics_password
    secret_key         = var.secret_key
    grafana_password   = var.grafana_password
  }
  name  = "${local.ssm_prefix}/${each.key}"
  type  = "SecureString"
  value = each.value
}

# -----------------------------------------------------------
# EC2 — t3.small, 30GB gp3
# -----------------------------------------------------------
module "ec2" {
  source           = "../../modules/ec2"
  env              = local.env
  aws_region       = var.aws_region
  public_subnet_id = module.vpc.public_subnet_ids[0]
  ec2_sg_id        = module.security.ec2_sg_id
  instance_type    = var.instance_type
  ebs_volume_size  = var.ebs_volume_size
  ssm_prefix       = local.ssm_prefix
  key_pair_name    = module.keypair.key_pair_name
  github_repo      = var.github_repo
  git_branch       = "develop"
  github_token     = var.github_token

  depends_on = [
    aws_ssm_parameter.dev_config,
    aws_ssm_parameter.dev_secrets,
  ]
}

# -----------------------------------------------------------
# Scheduler — stops EC2 at 8pm, starts at 7am weekdays
# -----------------------------------------------------------
module "scheduler" {
  source     = "../../modules/scheduler"
  env        = local.env
  aws_region = var.aws_region
  ssm_prefix = local.ssm_prefix
  mode       = "ec2"
  depends_on = [module.ec2]
}
