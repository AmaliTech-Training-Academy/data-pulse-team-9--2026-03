variable "env"               { type = string }
variable "vpc_id"            { type = string }
variable "public_subnet_ids" { type = list(string) }
variable "alb_sg_id"         { type = string }
variable "domain_name"       { type = string }

# -----------------------------------------------------------
# ALB
# -----------------------------------------------------------
resource "aws_lb" "main" {
  name               = "datapulse-${var.env}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_sg_id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = true

  tags = { Name = "datapulse-${var.env}-alb" }
}

# -----------------------------------------------------------
# ACM Certificate
# -----------------------------------------------------------
resource "aws_acm_certificate" "main" {
  domain_name               = var.domain_name
  subject_alternative_names = ["*.${var.domain_name}"]
  validation_method         = "DNS"
  lifecycle { create_before_destroy = true }
}

resource "aws_acm_certificate_validation" "main" {
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for r in aws_acm_certificate.main.domain_validation_options : r.resource_record_name]
}

# -----------------------------------------------------------
# Target Groups — BLUE (live)
# -----------------------------------------------------------
resource "aws_lb_target_group" "backend_blue" {
  name        = "datapulse-${var.env}-backend-blue"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/health/"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 10
    matcher             = "200"
  }

  tags = { Name = "datapulse-${var.env}-backend-blue" }
}

resource "aws_lb_target_group" "streamlit_blue" {
  name        = "datapulse-${var.env}-streamlit-blue"
  port        = 8501
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

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

  tags = { Name = "datapulse-${var.env}-streamlit-blue" }
}

# -----------------------------------------------------------
# Target Groups — GREEN (new version during deployment)
# -----------------------------------------------------------
resource "aws_lb_target_group" "backend_green" {
  name        = "datapulse-${var.env}-backend-green"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/health/"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 10
    matcher             = "200"
  }

  tags = { Name = "datapulse-${var.env}-backend-green" }
}

resource "aws_lb_target_group" "streamlit_green" {
  name        = "datapulse-${var.env}-streamlit-green"
  port        = 8501
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

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

  tags = { Name = "datapulse-${var.env}-streamlit-green" }
}

# -----------------------------------------------------------
# Listeners
# -----------------------------------------------------------

# HTTP → HTTPS redirect
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# HTTPS — main production listener
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate_validation.main.certificate_arn

  # Default → backend (blue)
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend_blue.arn
  }
}

# Streamlit path rule — /streamlit and /streamlit/*
resource "aws_lb_listener_rule" "streamlit" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 10

  condition {
    path_pattern {
      values = ["/streamlit", "/streamlit/*"]
    }
  }

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.streamlit_blue.arn
  }
}

# Test listener on :8080 — CodeDeploy hits green here before shifting prod traffic
resource "aws_lb_listener" "test" {
  load_balancer_arn = aws_lb.main.arn
  port              = 8080
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend_green.arn
  }
}

# -----------------------------------------------------------
# Outputs
# -----------------------------------------------------------
output "alb_arn"                  { value = aws_lb.main.arn }
output "alb_arn_suffix"           { value = aws_lb.main.arn_suffix }
output "alb_dns"                  { value = aws_lb.main.dns_name }
output "https_listener_arn"       { value = aws_lb_listener.https.arn }
output "backend_tg_arn"           { value = aws_lb_target_group.backend_blue.arn }
output "backend_tg_name"          { value = aws_lb_target_group.backend_blue.name }
output "backend_tg_arn_suffix"    { value = aws_lb_target_group.backend_blue.arn_suffix }
output "backend_green_tg_arn"     { value = aws_lb_target_group.backend_green.arn }
output "backend_green_tg_name"    { value = aws_lb_target_group.backend_green.name }
output "streamlit_tg_arn"         { value = aws_lb_target_group.streamlit_blue.arn }
output "streamlit_tg_name"        { value = aws_lb_target_group.streamlit_blue.name }
output "streamlit_green_tg_name"  { value = aws_lb_target_group.streamlit_green.name }
