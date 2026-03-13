variable "env"              { type = string }
variable "vpc_id"           { type = string }
variable "vpc_cidr"         { type = string }
variable "allowed_ssh_cidr" {
  type    = string
  default = "0.0.0.0/0"
}

# -----------------------------------------------------------
# ALB — public HTTPS/HTTP
# -----------------------------------------------------------
resource "aws_security_group" "alb" {
  name        = "datapulse-${var.env}-alb"
  description = "ALB: allow HTTP/HTTPS from internet"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  # Test listener for CodeDeploy green environment - VPC-internal only
  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "CodeDeploy test listener - internal only"
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "datapulse-${var.env}-alb-sg" }
}

# -----------------------------------------------------------
# ECS tasks — accept traffic from ALB only
# -----------------------------------------------------------
resource "aws_security_group" "ecs" {
  name        = "datapulse-${var.env}-ecs"
  description = "ECS tasks: accept from ALB on app ports"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "Django from ALB"
  }
  ingress {
    from_port       = 8501
    to_port         = 8501
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "Streamlit from ALB"
  }
  ingress {
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "Grafana from ALB"
  }
  # ECS tasks also need to talk to each other (Celery → Redis etc.)
  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
    description = "ECS inter-task"
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "datapulse-${var.env}-ecs-sg" }
}

# -----------------------------------------------------------
# RDS — accept from ECS only
# -----------------------------------------------------------
resource "aws_security_group" "rds" {
  name        = "datapulse-${var.env}-rds"
  description = "RDS: accept from ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
    description     = "Postgres from ECS"
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "datapulse-${var.env}-rds-sg" }
}

# -----------------------------------------------------------
# ElastiCache — accept from ECS only
# -----------------------------------------------------------
resource "aws_security_group" "redis" {
  name        = "datapulse-${var.env}-redis"
  description = "Redis: accept from ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
    description     = "Redis from ECS"
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "datapulse-${var.env}-redis-sg" }
}

# -----------------------------------------------------------
# Dev EC2 — SSH + app ports restricted to allowed_cidr
# -----------------------------------------------------------
resource "aws_security_group" "ec2" {
  name        = "datapulse-${var.env}-ec2"
  description = "Dev EC2: SSH + app ports from team VPN/IP"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
    description = "SSH from team"
  }
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
    description = "Django"
  }
  ingress {
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
    description = "Streamlit"
  }
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
    description = "Grafana"
  }
  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
    description = "Prometheus"
  }
  ingress {
    from_port   = 3100
    to_port     = 3100
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
    description = "Loki"
  }
  ingress {
    from_port   = 3200
    to_port     = 3200
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
    description = "Tempo"
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "datapulse-${var.env}-ec2-sg" }
}

# -----------------------------------------------------------
# Outputs
# -----------------------------------------------------------
output "alb_sg_id"   { value = aws_security_group.alb.id }
output "ecs_sg_id"   { value = aws_security_group.ecs.id }
output "rds_sg_id"   { value = aws_security_group.rds.id }
output "redis_sg_id" { value = aws_security_group.redis.id }
output "ec2_sg_id"   { value = aws_security_group.ec2.id }
