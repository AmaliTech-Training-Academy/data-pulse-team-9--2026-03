# Fetch dev config from SSM, then Secrets Manager if not found. Output terraform.tfvars format.
# Requires: AWS CLI (aws configure) with access to SSM and Secrets Manager.
#
# Usage:
#   .\scripts\get-dev-ssm-to-tfvars.ps1
#   .\scripts\get-dev-ssm-to-tfvars.ps1 | Out-File -Encoding utf8 terraform\environments\dev\terraform.tfvars.new

param(
    [string] $Region = "eu-west-1",
    [string] $SsmPrefix = "/datapulse/dev",
    [string] $SmPrefix = "datapulse/dev"
)

$vars = @(
    "postgres_user", "postgres_db", "postgres_password",
    "analytics_user", "analytics_db", "analytics_password",
    "secret_key", "grafana_user", "grafana_password"
)

function Get-SsmParam {
    param([string]$Key)
    $name = "$SsmPrefix/$Key"
    $result = & aws ssm get-parameter --name $name --with-decryption --region $Region --query "Parameter.Value" --output text 2>$null
    if ($LASTEXITCODE -eq 0 -and $result) { $result } else { $null }
}

function Get-SmSecretByKey {
    param([string]$Key)
    $id = "$SmPrefix/$Key"
    $result = & aws secretsmanager get-secret-value --secret-id $id --region $Region --query "SecretString" --output text 2>$null
    if ($LASTEXITCODE -eq 0 -and $result) { $result } else { $null }
}

function Get-SmSecretJson {
    param([string]$Key)
    try {
        $result = & aws secretsmanager get-secret-value --secret-id $SmPrefix --region $Region --query "SecretString" --output text 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $result) { return $null }
        $obj = $result | ConvertFrom-Json
        $obj.$Key
    } catch { $null }
}

function Get-Param {
    param([string]$Key)
    $v = Get-SsmParam -Key $Key
    if ($v) { return $v }
    $v = Get-SmSecretByKey -Key $Key
    if ($v) { return $v }
    Get-SmSecretJson -Key $Key
}

@"
# Terraform Variables for DataPulse Dev
# From SSM $SsmPrefix and/or Secrets Manager $SmPrefix — set allowed_cidr, github_repo, github_token.

# Set these yourself (not in SSM/SM):
allowed_cidr     = "0.0.0.0/0"
github_repo      = "your-org/your-repo"
github_token     = ""

# From SSM / Secrets Manager:
"@

foreach ($key in $vars) {
    $val = Get-Param -Key $key
    if ($val) {
        $valEscaped = $val -replace '\\', '\\' -replace '"', '\"'
        "${key} = `"$valEscaped`""
    } else {
        "# ${key} = `"<not found in SSM or Secrets Manager>`""
    }
}
