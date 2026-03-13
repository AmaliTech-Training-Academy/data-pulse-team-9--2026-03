variable "aws_region"           {
    type = string
 default = "eu-west-1"
 }
variable "vpc_cidr"             {
    type = string
 default = "10.0.0.0/16"
}
variable "availability_zones"   {
    type = list(string)
 default = ["eu-west-1a", "eu-west-1b"]
}
variable "domain_name"          {
    type        = string
    default     = ""
    description = "Optional custom domain (e.g. datapulse.io). Leave empty to use AWS-provided DNS names"
}
variable "github_repo"          {
    type = string
 description = "GitHub repo in ORG/REPO format"
}
variable "github_access_token"  {
    type = string
 sensitive = true
  description = "GitHub PAT for Amplify"
}
variable "dev_ec2_ip"           {
    type = string
 description = "Dev EC2 Elastic IP — from dev terraform output"
}

# Image URIs — placeholder on first apply, real after first CD run
variable "backend_image"        {
    type = string
 default = "public.ecr.aws/nginx/nginx:latest"
 }
variable "etl_image"            {
    type = string
 default = "public.ecr.aws/nginx/nginx:latest"
 }
variable "streamlit_image"      {
    type = string
 default = "public.ecr.aws/nginx/nginx:latest"
 }
variable "grafana_image"        {
    type = string
 default = "public.ecr.aws/nginx/nginx:latest"
 }

# RDS sizing
variable "rds_instance_class"   {
    type = string
 default = "db.t4g.micro"
 }

# Credentials — store in terraform.tfvars, never commit
variable "postgres_user"        { type = string }
variable "postgres_password"    {
     type = string
 sensitive = true
 }
variable "postgres_db"          { type = string }
variable "analytics_user"       { type = string }
variable "analytics_password"   {
    type = string
 sensitive = true
 }
variable "analytics_db"         { type = string }
variable "secret_key"           {
    type = string
 sensitive = true
 }
variable "grafana_user"         { type = string }
variable "grafana_password"     {
    type = string
 sensitive = true
 }
