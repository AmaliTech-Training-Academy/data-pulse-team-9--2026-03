variable "env" {
  type        = string
  description = "Environment name (dev, prod)"
}

variable "key_name" {
  type        = string
  description = "Name for the key pair"
  default     = "datapulse"
}

# Generate RSA private key
resource "tls_private_key" "ssh_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Create AWS key pair using the generated public key
resource "aws_key_pair" "generated" {
  key_name   = "${var.key_name}-${var.env}"
  public_key = tls_private_key.ssh_key.public_key_openssh

  tags = {
    Name        = "${var.key_name}-${var.env}"
    Environment = var.env
    Project     = "datapulse"
    ManagedBy   = "terraform"
  }
}

# Store private key in AWS Secrets Manager
resource "aws_secretsmanager_secret" "ssh_private_key" {
  name        = "datapulse/${var.env}/ssh-private-key"
  description = "SSH private key for ${var.env} environment EC2 instances"

  tags = {
    Name        = "datapulse-${var.env}-ssh-key"
    Environment = var.env
    Project     = "datapulse"
    ManagedBy   = "terraform"
  }
}

resource "aws_secretsmanager_secret_version" "ssh_private_key" {
  secret_id = aws_secretsmanager_secret.ssh_private_key.id
  secret_string = jsonencode({
    private_key = tls_private_key.ssh_key.private_key_pem
    public_key  = tls_private_key.ssh_key.public_key_openssh
    key_name    = aws_key_pair.generated.key_name
  })
}

# Outputs
output "key_pair_name" {
  description = "Name of the created key pair"
  value       = aws_key_pair.generated.key_name
}

output "public_key" {
  description = "Public key content"
  value       = tls_private_key.ssh_key.public_key_openssh
}

output "private_key_secret_arn" {
  description = "ARN of the secret containing the private key"
  value       = aws_secretsmanager_secret.ssh_private_key.arn
}

output "private_key_secret_name" {
  description = "Name of the secret containing the private key"
  value       = aws_secretsmanager_secret.ssh_private_key.name
}

# Local output for debugging (sensitive)
output "private_key_pem" {
  description = "Private key in PEM format (sensitive)"
  value       = tls_private_key.ssh_key.private_key_pem
  sensitive   = true
}
