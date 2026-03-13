# SSH Key Pair outputs
output "ssh_key_pair_name" {
  description = "Name of the SSH key pair"
  value       = module.keypair.key_pair_name
}

output "ssh_private_key_secret_name" {
  description = "Name of the secret containing the SSH private key"
  value       = module.keypair.private_key_secret_name
}

output "public_ip" {
  description = "EC2 Elastic IP — use for all dev service URLs"
  value       = module.ec2.public_ip
}

output "instance_id" {
  description = "EC2 instance ID"
  value       = module.ec2.instance_id
}

output "service_urls" {
  description = "Dev service URLs (direct to EC2, when not using ALB)"
  value = {
    backend    = "http://${module.ec2.public_ip}:8000"
    frontend   = "http://${module.ec2.public_ip}:3001"
    streamlit  = "http://${module.ec2.public_ip}:8501"
    grafana    = "http://${module.ec2.public_ip}:3000"
    prometheus = "http://${module.ec2.public_ip}:9090"
    loki       = "http://${module.ec2.public_ip}:3100"
    tempo      = "http://${module.ec2.public_ip}:3200"
  }
}

# ALB — single entry point; use these when load balancer is in front
output "alb_dns_name" {
  description = "ALB DNS name — use as base URL for all apps (path-based routing)"
  value       = aws_lb.dev.dns_name
}

output "alb_url" {
  description = "Base URL via ALB (HTTP). Set NEXT_PUBLIC_API_URL to this for frontend API calls."
  value       = "http://${aws_lb.dev.dns_name}"
}

output "alb_service_paths" {
  description = "Paths on the ALB for each service"
  value = {
    frontend  = "http://${aws_lb.dev.dns_name}/"
    backend   = "http://${aws_lb.dev.dns_name}/api/"
    streamlit = "http://${aws_lb.dev.dns_name}/streamlit/"
    grafana   = "http://${aws_lb.dev.dns_name}/grafana/"
  }
}
