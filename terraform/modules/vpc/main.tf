variable "env"        { type = string }
variable "vpc_cidr"   { type = string }
variable "azs"        { type = list(string) }
variable "aws_region" { type = string }

# -----------------------------------------------------------
# VPC
# -----------------------------------------------------------
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = { Name = "datapulse-${var.env}" }
}

# -----------------------------------------------------------
# Public subnets (ALB in prod / EC2 in dev)
# -----------------------------------------------------------
resource "aws_subnet" "public" {
  count                   = length(var.azs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = var.azs[count.index]
  map_public_ip_on_launch = true
  tags = { Name = "datapulse-${var.env}-public-${count.index + 1}" }
}

# -----------------------------------------------------------
# Private subnets (ECS, RDS, ElastiCache — prod only)
# -----------------------------------------------------------
resource "aws_subnet" "private" {
  count             = length(var.azs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = var.azs[count.index]
  tags = { Name = "datapulse-${var.env}-private-${count.index + 1}" }
}

# -----------------------------------------------------------
# Internet Gateway + public route table
# -----------------------------------------------------------
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "datapulse-${var.env}-igw" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  tags = { Name = "datapulse-${var.env}-public-rt" }
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# -----------------------------------------------------------
# Private route table (no NAT — VPC endpoints used instead)
# -----------------------------------------------------------
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "datapulse-${var.env}-private-rt" }
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# -----------------------------------------------------------
# VPC Interface Endpoints — trimmed to 4 essential ones
# ssm/ssmmessages/xray removed to save ~$6/mo
# Only created for prod (dev EC2 has direct internet via IGW)
# -----------------------------------------------------------
resource "aws_security_group" "endpoints" {
  name        = "datapulse-${var.env}-endpoints"
  description = "Allow HTTPS from VPC to interface endpoints"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "datapulse-${var.env}-endpoints-sg" }
}

locals {
  # ecr.api + ecr.dkr: pull images
  # secretsmanager: ECS task secrets injection
  # logs: CloudWatch log delivery from Fargate
  interface_endpoints = ["ecr.api", "ecr.dkr", "secretsmanager", "logs"]
}

resource "aws_vpc_endpoint" "interfaces" {
  for_each            = toset(local.interface_endpoints)
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.${each.key}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.endpoints.id]
  private_dns_enabled = true
  tags = { Name = "datapulse-${var.env}-endpoint-${each.key}" }
}

# S3 gateway — free, needed by ECR to pull image layers
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private.id]
  tags = { Name = "datapulse-${var.env}-endpoint-s3" }
}

# -----------------------------------------------------------
# Outputs
# -----------------------------------------------------------
output "vpc_id"             { value = aws_vpc.main.id }
output "vpc_cidr"           { value = aws_vpc.main.cidr_block }
output "public_subnet_ids"  { value = aws_subnet.public[*].id }
output "private_subnet_ids" { value = aws_subnet.private[*].id }
