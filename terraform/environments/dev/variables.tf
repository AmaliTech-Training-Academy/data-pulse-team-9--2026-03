variable "aws_region" {
  type    = string
  default = "eu-west-1"
}
variable "env" {
  type        = string
  description = "Environment name"
  default     = "dev"
}
variable "vpc_cidr" {
  type    = string
  default = "10.1.0.0/16"
}
variable "availability_zones" {
  type    = list(string)
  default = ["eu-west-1a", "eu-west-1b"]
}
variable "allowed_cidr" {
  type        = string
  description = "Team VPN/IP CIDR — only source allowed to hit EC2 ports"
}
variable "instance_type" {
  type    = string
  default = "t3.small"
}
variable "ebs_volume_size" {
  type    = number
  default = 30
}
variable "github_repo" {
  type        = string
  description = "GitHub repo in ORG/REPO format"
}
variable "github_token" {
  type        = string
  description = "GitHub personal access token for private repos"
  default     = ""
  sensitive   = true
}
# Remove the public_key variable since we'll generate it
# variable "public_key" {
#   type        = string
#   description = "SSH public key content for EC2 key pair"
# }

# Credentials — store in terraform.tfvars, never commit
variable "postgres_user" {
  type = string
}
variable "postgres_password" {
  type      = string
  sensitive = true
}
variable "postgres_db" {
  type = string
}
variable "analytics_user" {
  type = string
}
variable "analytics_password" {
  type      = string
  sensitive = true
}
variable "analytics_db" {
  type = string
}
variable "secret_key" {
  type      = string
  sensitive = true
}
variable "grafana_user" {
  type = string
}
variable "grafana_password" {
  type      = string
  sensitive = true
}
