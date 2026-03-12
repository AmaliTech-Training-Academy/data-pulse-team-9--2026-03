# =============================================================
# Restart Dev EC2 Instance Script (PowerShell)
# =============================================================

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Restarting Dev EC2 Instance" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Change to dev environment directory
$DevPath = "C:\Users\HP\Desktop\DatapulseMain\terraform\environments\dev"
Set-Location $DevPath

Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
Write-Host ""

# Show current instance status
Write-Host "Current instance info:" -ForegroundColor Yellow
try {
    $InstanceId = terraform output -raw instance_id 2>$null
    $PublicIp = terraform output -raw public_ip 2>$null
    if ($InstanceId) {
        Write-Host "Instance ID: $InstanceId" -ForegroundColor Green
        Write-Host "Public IP: $PublicIp" -ForegroundColor Green
    } else {
        Write-Host "No instance found or terraform not initialized" -ForegroundColor Red
    }
} catch {
    Write-Host "Error getting instance info" -ForegroundColor Red
}
Write-Host ""

# Confirm action
Write-Host "⚠️  This will DESTROY and RECREATE the dev EC2 instance" -ForegroundColor Yellow
Write-Host "⚠️  Downtime: ~10-15 minutes" -ForegroundColor Yellow
Write-Host "✅ EBS data will be preserved" -ForegroundColor Green
Write-Host ""

$Confirmation = Read-Host "Continue? (y/N)"
if ($Confirmation -ne 'y' -and $Confirmation -ne 'Y') {
    Write-Host "❌ Operation cancelled" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔄 Starting instance replacement..." -ForegroundColor Cyan
Write-Host ""

# Run terraform replace
$TerraformResult = terraform apply -replace="module.ec2.aws_instance.dev" -auto-approve

# Check if successful
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Instance replacement completed successfully!" -ForegroundColor Green
    Write-Host ""

    Write-Host "New instance details:" -ForegroundColor Yellow
    $NewInstanceId = terraform output -raw instance_id
    $NewPublicIp = terraform output -raw public_ip
    Write-Host "Instance ID: $NewInstanceId" -ForegroundColor Green
    Write-Host "Public IP: $NewPublicIp" -ForegroundColor Green
    Write-Host ""

    Write-Host "🔍 Checking if services are starting..." -ForegroundColor Cyan
    Start-Sleep 30  # Wait for services to start

    Write-Host "Testing health endpoint: http://$NewPublicIp:8000/health/" -ForegroundColor Yellow

    # Try health check (may take a few minutes for services to start)
    for ($i = 1; $i -le 10; $i++) {
        try {
            $Response = Invoke-WebRequest -Uri "http://$NewPublicIp:8000/health/" -TimeoutSec 10 -ErrorAction Stop
            if ($Response.StatusCode -eq 200) {
                Write-Host "✅ Services are running!" -ForegroundColor Green
                Write-Host "🌐 Access your application at: http://$NewPublicIp:8000" -ForegroundColor Cyan
                break
            }
        } catch {
            Write-Host "⏳ Waiting for services to start... (attempt $i/10)" -ForegroundColor Yellow
            Start-Sleep 30
        }
    }

} else {
    Write-Host ""
    Write-Host "❌ Instance replacement failed!" -ForegroundColor Red
    Write-Host "Check the error messages above" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Dev EC2 Instance Restart Complete" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
