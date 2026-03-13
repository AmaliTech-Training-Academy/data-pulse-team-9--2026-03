#!/bin/bash
# Fetch dev config from SSM Parameter Store, then Secrets Manager if not found.
# Outputs terraform.tfvars format.
# Requires: AWS CLI configured with access to SSM and Secrets Manager.
#
# Usage:
#   ./scripts/get-dev-ssm-to-tfvars.sh
#   ./scripts/get-dev-ssm-to-tfvars.sh > terraform/environments/dev/terraform.tfvars.new

set -e
SSM_PREFIX="${SSM_PREFIX:-/datapulse/dev}"
SM_PREFIX="${SM_PREFIX:-datapulse/dev}"
AWS_REGION="${AWS_REGION:-eu-west-1}"

while [ $# -gt 0 ]; do
  case "$1" in
    --region)   AWS_REGION="$2"; shift 2 ;;
    --ssm)      SSM_PREFIX="$2";  shift 2 ;;
    --secrets)  SM_PREFIX="$2";   shift 2 ;;
    *) echo "Usage: $0 [--region REGION] [--ssm PREFIX] [--secrets PREFIX]" >&2; exit 1 ;;
  esac
done

# Try SSM first
get_ssm() {
  aws ssm get-parameter --name "$SSM_PREFIX/$1" --with-decryption --region "$AWS_REGION" --query "Parameter.Value" --output text 2>/dev/null || echo ""
}

# Try Secrets Manager: secret id "<prefix>/<key>" (e.g. datapulse/dev/postgres_user)
get_sm_key() {
  aws secretsmanager get-secret-value --secret-id "$SM_PREFIX/$1" --region "$AWS_REGION" --query "SecretString" --output text 2>/dev/null || echo ""
}

# Try Secrets Manager: single secret "<prefix>" with JSON body
get_sm_json() {
  local json key="$1"
  json=$(aws secretsmanager get-secret-value --secret-id "$SM_PREFIX" --region "$AWS_REGION" --query "SecretString" --output text 2>/dev/null) || return 1
  [ -z "$json" ] && return 1
  if command -v python3 >/dev/null 2>&1; then
    echo "$json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('$key', ''))" 2>/dev/null || echo ""
  elif command -v jq >/dev/null 2>&1; then
    echo "$json" | jq -r --arg k "$key" '.[$k] // empty' 2>/dev/null || echo ""
  else
    echo ""
  fi
}

get_param() {
  local key="$1" val
  val=$(get_ssm "$key")
  if [ -n "$val" ]; then
    echo "$val"
    return
  fi
  val=$(get_sm_key "$key")
  if [ -n "$val" ]; then
    echo "$val"
    return
  fi
  val=$(get_sm_json "$key")
  if [ -n "$val" ]; then
    echo "$val"
  fi
}

echo "# Terraform Variables for DataPulse Dev"
echo "# From SSM $SSM_PREFIX and/or Secrets Manager $SM_PREFIX — set allowed_cidr, github_repo, github_token."
echo ""
echo "# Set these yourself (not in SSM/SM):"
echo 'allowed_cidr     = "0.0.0.0/0"'
echo 'github_repo      = "your-org/your-repo"'
echo 'github_token     = ""'
echo ""
echo "# From SSM / Secrets Manager:"

for key in postgres_user postgres_db postgres_password analytics_user analytics_db analytics_password secret_key grafana_user grafana_password; do
  val=$(get_param "$key")
  if [ -n "$val" ]; then
    val_escaped=$(echo "$val" | sed 's/\\/\\\\/g; s/"/\\"/g')
    echo "${key} = \"${val_escaped}\""
  else
    echo "# ${key} = \"<not found in SSM or Secrets Manager>\""
  fi
done
