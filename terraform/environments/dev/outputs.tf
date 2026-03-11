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
  description = "Dev service URLs"
  value = {
    backend    = "http://${module.ec2.public_ip}:8000"
    streamlit  = "http://${module.ec2.public_ip}:8501"
    grafana    = "http://${module.ec2.public_ip}:3000"
    prometheus = "http://${module.ec2.public_ip}:9090"
    loki       = "http://${module.ec2.public_ip}:3100"
    tempo      = "http://${module.ec2.public_ip}:3200"
  }
}
