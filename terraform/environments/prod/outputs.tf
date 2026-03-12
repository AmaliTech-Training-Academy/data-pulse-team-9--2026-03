output "alb_dns" {
  description = "ALB DNS — add CNAME to your domain registrar before custom domain works"
  value       = module.alb.alb_dns
}

output "service_urls" {
  description = "Prod service URLs"
  value = {
    frontend   = "https://${var.domain_name}"
    frontend_dev = "https://dev.${var.domain_name}"
    backend    = "https://${var.domain_name}/"
    streamlit  = "https://${var.domain_name}/streamlit"
    grafana    = aws_grafana_workspace.main.endpoint
    prometheus = aws_prometheus_workspace.main.prometheus_endpoint
  }
}

output "ecr_urls" {
  description = "ECR repository URLs — use in CD workflow"
  value = {
    for k, v in aws_ecr_repository.repos : k => v.repository_url
  }
}

output "github_actions_role_arn" {
  description = "Add this as PROD_AWS_ROLE_ARN GitHub secret"
  value       = aws_iam_role.github_actions.arn
}

output "amplify_app_id" {
  value = module.amplify.app_id
}
