variable "app_name"            { type = string }
variable "github_repo"         { type = string }
variable "github_access_token" {
  type      = string
  sensitive = true
}
variable "domain_name"         {
  type        = string
  default     = ""
  description = "Optional custom domain"
}
variable "dev_api_url"         { type = string }
variable "prod_api_url"        { type = string }

resource "aws_amplify_app" "main" {
  name         = var.app_name
  repository   = "https://github.com/${var.github_repo}"
  access_token = var.github_access_token
  platform     = "WEB_COMPUTE"   # SSR support for Next.js

  build_spec = file("${path.module}/amplify.yml")

  custom_rule {
    source = "/<*>"
    status = "404-200"
    target = "/index.html"
  }

  dynamic "custom_rule" {
    for_each = var.domain_name != "" ? [1] : []
    content {
      source = "https://www.${var.domain_name}"
      status = "302"
      target = "https://${var.domain_name}"
    }
  }

  enable_branch_auto_build    = true
  enable_branch_auto_deletion = true

  environment_variables = {
    NEXT_PUBLIC_APP_NAME = "DataPulse"
    # Configure for monorepo - only build when frontend changes
    AMPLIFY_MONOREPO_APP_ROOT = "frontend"
    AMPLIFY_DIFF_DEPLOY = "true"
  }
}

resource "aws_amplify_branch" "dev" {
  app_id      = aws_amplify_app.main.id
  branch_name = "develop"
  stage       = "DEVELOPMENT"

  enable_auto_build             = true
  enable_pull_request_preview   = false  # Completely disable PR previews

  environment_variables = {
    NEXT_PUBLIC_API_URL     = var.dev_api_url
    NEXT_PUBLIC_ENVIRONMENT = "dev"
    NEXT_PUBLIC_API_TIMEOUT = "30000"
  }

  tags = { Environment = "dev", Project = "datapulse" }
}

resource "aws_amplify_branch" "prod" {
  app_id      = aws_amplify_app.main.id
  branch_name = "main"
  stage       = "PRODUCTION"

  enable_auto_build           = true
  enable_pull_request_preview = false  # Disable PR previews for main too

  environment_variables = {
    NEXT_PUBLIC_API_URL     = var.prod_api_url
    NEXT_PUBLIC_ENVIRONMENT = "production"
    NEXT_PUBLIC_API_TIMEOUT = "15000"
  }

  tags = { Environment = "prod", Project = "datapulse" }
}

resource "aws_amplify_domain_association" "main" {
  count       = var.domain_name != "" ? 1 : 0
  app_id      = aws_amplify_app.main.id
  domain_name = var.domain_name

  sub_domain {
    branch_name = aws_amplify_branch.prod.branch_name
    prefix      = ""
  }
  sub_domain {
    branch_name = aws_amplify_branch.prod.branch_name
    prefix      = "www"
  }
  sub_domain {
    branch_name = aws_amplify_branch.dev.branch_name
    prefix      = "dev"
  }
}

output "app_id"         { value = aws_amplify_app.main.id }
output "default_domain" { value = aws_amplify_app.main.default_domain }
output "prod_url"       { value = var.domain_name != "" ? "https://${var.domain_name}" : "https://main.${aws_amplify_app.main.default_domain}" }
output "dev_url"        { value = var.domain_name != "" ? "https://dev.${var.domain_name}" : "https://develop.${aws_amplify_app.main.default_domain}" }
