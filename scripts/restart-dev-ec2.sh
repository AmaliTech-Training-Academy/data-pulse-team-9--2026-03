#!/bin/bash
# =============================================================
# Restart Dev EC2 Instance Script
# =============================================================

echo "=========================================="
echo "Restarting Dev EC2 Instance"
echo "=========================================="
echo ""

# Change to dev environment directory
cd "C:\Users\HP\Desktop\DatapulseMain\terraform\environments\dev"

echo "Current directory: $(pwd)"
echo ""

# Show current instance status
echo "Current instance info:"
terraform output instance_id 2>/dev/null || echo "No instance found or terraform not initialized"
terraform output public_ip 2>/dev/null || echo "No public IP found"
echo ""

# Confirm action
echo "⚠️  This will DESTROY and RECREATE the dev EC2 instance"
echo "⚠️  Downtime: ~10-15 minutes"
echo "✅ EBS data will be preserved"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Operation cancelled"
    exit 1
fi

echo ""
echo "🔄 Starting instance replacement..."
echo ""

# Run terraform replace
terraform apply -replace="module.ec2.aws_instance.dev" -auto-approve

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Instance replacement completed successfully!"
    echo ""
    echo "New instance details:"
    echo "Instance ID: $(terraform output -raw instance_id)"
    echo "Public IP: $(terraform output -raw public_ip)"
    echo ""
    echo "🔍 Checking if services are starting..."
    sleep 30  # Wait for services to start

    PUBLIC_IP=$(terraform output -raw public_ip)
    echo "Testing health endpoint: http://$PUBLIC_IP:8000/health/"

    # Try health check (may take a few minutes for services to start)
    for i in {1..10}; do
        if curl -f -s "http://$PUBLIC_IP:8000/health/" > /dev/null; then
            echo "✅ Services are running!"
            echo "🌐 Access your application at: http://$PUBLIC_IP:8000"
            break
        else
            echo "⏳ Waiting for services to start... (attempt $i/10)"
            sleep 30
        fi
    done

else
    echo ""
    echo "❌ Instance replacement failed!"
    echo "Check the error messages above"
    exit 1
fi

echo ""
echo "=========================================="
echo "Dev EC2 Instance Restart Complete"
echo "=========================================="
