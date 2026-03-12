#!/bin/bash
# Simple script to restart dev EC2 instance

echo "Restarting Dev EC2 Instance..."
cd "C:\Users\HP\Desktop\DatapulseMain\terraform\environments\dev"
terraform apply -replace="module.ec2.aws_instance.dev" -auto-approve
echo "Done!"
