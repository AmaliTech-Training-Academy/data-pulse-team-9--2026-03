variable "env"              { type = string }
variable "aws_region"       { type = string }
variable "public_subnet_id" { type = string }
variable "ec2_sg_id"        { type = string }
variable "instance_type" {
  type    = string
  default = "t3.small"
}
variable "ebs_volume_size" {
  type    = number
  default = 30
}
variable "ssm_prefix"       { type = string }
variable "key_pair_name"    { type = string }
variable "github_repo"      { type = string }
variable "git_branch" {
  type        = string
  description = "Git branch to checkout"
  default     = "develop"
}
variable "github_token" {
  type        = string
  description = "GitHub personal access token for private repos"
  default     = ""
  sensitive   = true
}

# -----------------------------------------------------------
# IAM Role — allows SSM Session Manager + reads dev SSM params
# -----------------------------------------------------------
resource "aws_iam_role" "ec2" {
  name = "datapulse-${var.env}-ec2"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "ec2_ssm_params" {
  name = "datapulse-${var.env}-ssm-read"
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ssm:GetParameter", "ssm:GetParameters", "ssm:GetParametersByPath"]
      Resource = "arn:aws:ssm:${var.aws_region}:*:parameter${var.ssm_prefix}/*"
    }]
  })
}

resource "aws_iam_instance_profile" "ec2" {
  name = "datapulse-${var.env}-ec2"
  role = aws_iam_role.ec2.name
}

# -----------------------------------------------------------
# EC2 Instance — t3.small, 30GB gp3
# -----------------------------------------------------------
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
  filter {
    name   = "state"
    values = ["available"]
  }
  filter {
    name   = "description"
    values = ["Amazon Linux 2023 AMI*"]
  }
}

resource "aws_instance" "dev" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = var.public_subnet_id
  vpc_security_group_ids = [var.ec2_sg_id]
  iam_instance_profile   = aws_iam_instance_profile.ec2.name
  key_name               = var.key_pair_name  # Use the provided key pair name

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.ebs_volume_size
    encrypted             = true
    delete_on_termination = false   # preserve data across stop/starts
  }

  user_data = templatefile("${path.module}/userdata.sh.tpl", {
    ssm_prefix   = var.ssm_prefix
    aws_region   = var.aws_region
    github_repo  = var.github_repo
    git_branch   = var.git_branch
    github_token = var.github_token
  })

  tags = {
    Name        = "datapulse-${var.env}"
    Environment = var.env
    Project     = "datapulse"
    ScheduleStop = "true"
  }

  # Avoid replacing the instance when a newer AMI is returned by the data source
  lifecycle {
    ignore_changes = [ami]
  }
}

# -----------------------------------------------------------
# Elastic IP — stable address across scheduler stop/starts
# -----------------------------------------------------------
resource "aws_eip" "dev" {
  instance = aws_instance.dev.id
  domain   = "vpc"
  tags     = { Name = "datapulse-${var.env}-eip" }
}

# -----------------------------------------------------------
# SSM param — scheduler Lambda reads this to find the instance
# -----------------------------------------------------------
resource "aws_ssm_parameter" "instance_id" {
  name  = "${var.ssm_prefix}/scheduler/instance_id"
  type  = "String"
  value = aws_instance.dev.id
}

# -----------------------------------------------------------
# Outputs
# -----------------------------------------------------------
output "instance_id"  { value = aws_instance.dev.id }
output "public_ip"    { value = aws_eip.dev.public_ip }
