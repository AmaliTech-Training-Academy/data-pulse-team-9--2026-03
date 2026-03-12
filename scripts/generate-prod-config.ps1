# =============================================================
# Helper script to generate production configuration values
# =============================================================

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "DataPulse Production Setup Helper" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Generate Django Secret Key
Write-Host "1. Django Secret Key:" -ForegroundColor Yellow
$chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
$secretKey = -join ((1..50) | ForEach-Object { $chars[(Get-Random -Maximum $chars.Length)] })
Write-Host $secretKey -ForegroundColor Green
Write-Host ""

# Generate strong passwords
Write-Host "2. PostgreSQL Password:" -ForegroundColor Yellow
$postgresPassword = -join ((1..25) | ForEach-Object { $chars[(Get-Random -Maximum $chars.Length)] })
Write-Host $postgresPassword -ForegroundColor Green
Write-Host ""

Write-Host "3. Analytics DB Password:" -ForegroundColor Yellow
$analyticsPassword = -join ((1..25) | ForEach-Object { $chars[(Get-Random -Maximum $chars.Length)] })
Write-Host $analyticsPassword -ForegroundColor Green
Write-Host ""

Write-Host "4. Grafana Password:" -ForegroundColor Yellow
$grafanaPassword = -join ((1..25) | ForEach-Object { $chars[(Get-Random -Maximum $chars.Length)] })
Write-Host $grafanaPassword -ForegroundColor Green
Write-Host ""

# Get Dev EC2 IP
Write-Host "5. Dev EC2 IP Address:" -ForegroundColor Yellow
if (Test-Path "terraform\environments\dev") {
    Push-Location terraform\environments\dev
    try {
        $devIp = terraform output -raw public_ip 2>$null
        if ($devIp) {
            Write-Host $devIp -ForegroundColor Green
        } else {
            Write-Host "Run: cd terraform\environments\dev && terraform output public_ip" -ForegroundColor Red
        }
    } catch {
        Write-Host "Run: cd terraform\environments\dev && terraform output public_ip" -ForegroundColor Red
    }
    Pop-Location
} else {
    Write-Host "Run: cd terraform\environments\dev && terraform output public_ip" -ForegroundColor Red
}
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "1. Copy the values above into terraform\environments\prod\terraform.tfvars"
Write-Host "2. Get GitHub PAT from: https://github.com/settings/tokens"
Write-Host "   Required scopes: repo, admin:repo_hook"
Write-Host "3. Review and update all CHANGE_ME values"
Write-Host "4. Deploy: cd terraform\environments\prod && terraform init && terraform apply"
Write-Host ""
