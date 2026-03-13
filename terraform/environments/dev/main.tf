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

# -----------------------------------------------------------
# ALB — single entry point for backend, frontend, Streamlit, Grafana
# Path-based routing; EC2 instance targets
# -----------------------------------------------------------
resource "aws_lb" "dev" {
  name               = "datapulse-${local.env}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [module.security.alb_sg_id]
  subnets            = module.vpc.public_subnet_ids

  enable_deletion_protection = false
  idle_timeout               = 60

  tags = { Name = "datapulse-${local.env}-alb" }
}

# Target groups — instance type (one EC2, different ports per service)
resource "aws_lb_target_group" "backend" {
  name        = "datapulse-${local.env}-backend"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = module.vpc.vpc_id
  target_type = "instance"

  health_check {
    path                = "/health/"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 10
    matcher             = "200"
  }
  tags = { Name = "datapulse-${local.env}-backend" }
}

resource "aws_lb_target_group" "frontend" {
  name        = "datapulse-${local.env}-frontend"
  port        = 3001
  protocol    = "HTTP"
  vpc_id      = module.vpc.vpc_id
  target_type = "instance"

  health_check {
    path                = "/"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 10
    matcher             = "200"
  }
  tags = { Name = "datapulse-${local.env}-frontend" }
}

resource "aws_lb_target_group" "streamlit" {
  name        = "datapulse-${local.env}-streamlit"
  port        = 8501
  protocol    = "HTTP"
  vpc_id      = module.vpc.vpc_id
  target_type = "instance"

  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400
    enabled         = true
  }
  health_check {
    path                = "/_stcore/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 10
    matcher             = "200"
  }
  tags = { Name = "datapulse-${local.env}-streamlit" }
}

resource "aws_lb_target_group" "grafana" {
  name        = "datapulse-${local.env}-grafana"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = module.vpc.vpc_id
  target_type = "instance"

  health_check {
    path                = "/api/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 10
    matcher             = "200"
  }
  tags = { Name = "datapulse-${local.env}-grafana" }
}

# Register EC2 instance with each target group
resource "aws_lb_target_group_attachment" "backend" {
  target_group_arn = aws_lb_target_group.backend.arn
  target_id        = module.ec2.instance_id
  port             = 8000
}

resource "aws_lb_target_group_attachment" "frontend" {
  target_group_arn = aws_lb_target_group.frontend.arn
  target_id        = module.ec2.instance_id
  port             = 3001
}

resource "aws_lb_target_group_attachment" "streamlit" {
  target_group_arn = aws_lb_target_group.streamlit.arn
  target_id        = module.ec2.instance_id
  port             = 8501
}

resource "aws_lb_target_group_attachment" "grafana" {
  target_group_arn = aws_lb_target_group.grafana.arn
  target_id        = module.ec2.instance_id
  port             = 3000
}

# Allow ALB to reach EC2 on app ports
resource "aws_security_group_rule" "alb_to_ec2_backend" {
  type                     = "ingress"
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  source_security_group_id = module.security.alb_sg_id
  security_group_id        = module.security.ec2_sg_id
  description              = "Backend from ALB"
}

resource "aws_security_group_rule" "alb_to_ec2_frontend" {
  type                     = "ingress"
  from_port                = 3001
  to_port                  = 3001
  protocol                 = "tcp"
  source_security_group_id = module.security.alb_sg_id
  security_group_id        = module.security.ec2_sg_id
  description              = "Frontend from ALB"
}

resource "aws_security_group_rule" "alb_to_ec2_streamlit" {
  type                     = "ingress"
  from_port                = 8501
  to_port                  = 8501
  protocol                 = "tcp"
  source_security_group_id = module.security.alb_sg_id
  security_group_id        = module.security.ec2_sg_id
  description              = "Streamlit from ALB"
}

resource "aws_security_group_rule" "alb_to_ec2_grafana" {
  type                     = "ingress"
  from_port                = 3000
  to_port                  = 3000
  protocol                 = "tcp"
  source_security_group_id = module.security.alb_sg_id
  security_group_id        = module.security.ec2_sg_id
  description              = "Grafana from ALB"
}

# HTTP listener — path-based routing
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.dev.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

# /api -> backend (Django)
resource "aws_lb_listener_rule" "backend" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  condition {
    path_pattern {
      values = ["/api", "/api/*", "/health/*", "/admin", "/admin/*"]
    }
  }
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

# /streamlit -> Streamlit
resource "aws_lb_listener_rule" "streamlit" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 20

  condition {
    path_pattern {
      values = ["/streamlit", "/streamlit/*"]
    }
  }
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.streamlit.arn
  }
}

# /grafana -> Grafana
resource "aws_lb_listener_rule" "grafana" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 30

  condition {
    path_pattern {
      values = ["/grafana", "/grafana/*"]
    }
  }
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.grafana.arn
  }
}
