# Simple script to restart dev EC2 instance

Write-Host "Restarting Dev EC2 Instance..."
Set-Location "C:\Users\HP\Desktop\DatapulseMain\terraform\environments\dev"
terraform apply -replace="module.ec2.aws_instance.dev" -auto-approve
Write-Host "Done!"
