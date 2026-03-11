variable "env"                    { type = string }
variable "aws_region"             { type = string }
variable "cluster_name"           { type = string }
variable "backend_service_name"   { type = string }
variable "streamlit_service_name" { type = string }
variable "https_listener_arn"     { type = string }
variable "test_listener_arn"      { type = string }
variable "backend_blue_tg_name"   { type = string }
variable "backend_green_tg_name"  { type = string }
variable "streamlit_blue_tg_name" { type = string }
variable "streamlit_green_tg_name"{ type = string }
variable "backend_blue_tg_arn"    { type = string }
variable "backend_green_tg_arn"   { type = string }
variable "alb_arn_suffix"         { type = string }
variable "backend_tg_arn_suffix"  { type = string }
variable "alb_dns"                { type = string }
variable "ssm_prefix"             { type = string }

# -----------------------------------------------------------
# IAM Role for CodeDeploy
# -----------------------------------------------------------
resource "aws_iam_role" "codedeploy" {
  name = "datapulse-${var.env}-codedeploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "codedeploy.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "codedeploy" {
  role       = aws_iam_role.codedeploy.name
  policy_arn = "arn:aws:iam::aws:policy/AWSCodeDeployRoleForECS"
}

# -----------------------------------------------------------
# IAM Role for hook Lambdas
# -----------------------------------------------------------
resource "aws_iam_role" "hooks" {
  name = "datapulse-${var.env}-deploy-hooks"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "hooks" {
  name = "datapulse-${var.env}-deploy-hooks"
  role = aws_iam_role.hooks.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["codedeploy:PutLifecycleEventHookExecutionStatus"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["elasticloadbalancing:ModifyRule", "elasticloadbalancing:DescribeRules",
                    "elasticloadbalancing:DescribeTargetGroups", "elasticloadbalancing:ModifyListener"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# -----------------------------------------------------------
# Hook Lambda: AfterAllowTestTraffic
# Smoke tests green on test listener (:8080) before any
# production traffic shifts to it
# -----------------------------------------------------------
data "archive_file" "hook_smoke_test" {
  type        = "zip"
  output_path = "${path.module}/hook_smoke_test.zip"

  source {
    filename = "handler.py"
    content  = <<-PYTHON
      import boto3, urllib.request, os

      codedeploy = boto3.client("codedeploy")

      def handler(event, context):
          deployment_id   = event["DeploymentId"]
          lifecycle_event = event["LifecycleEventHookExecutionId"]
          test_host       = os.environ["ALB_DNS"]

          try:
              url = f"http://{test_host}:8080/health/"
              print(f"→ Smoke testing green at {url}")
              with urllib.request.urlopen(url, timeout=10) as r:
                  status = "Succeeded" if r.status == 200 else "Failed"
                  print(f"  HTTP {r.status} → {status}")
          except Exception as e:
              print(f"✗ Smoke test failed: {e}")
              status = "Failed"

          codedeploy.put_lifecycle_event_hook_execution_status(
              deploymentId=deployment_id,
              lifecycleEventHookExecutionId=lifecycle_event,
              status=status
          )
    PYTHON
  }
}

resource "aws_lambda_function" "hook_smoke_test" {
  function_name    = "datapulse-${var.env}-hook-smoke-test"
  role             = aws_iam_role.hooks.arn
  filename         = data.archive_file.hook_smoke_test.output_path
  source_code_hash = data.archive_file.hook_smoke_test.output_base64sha256
  handler          = "handler.handler"
  runtime          = "python3.12"
  timeout          = 60

  environment {
    variables = { ALB_DNS = var.alb_dns }
  }
}

# -----------------------------------------------------------
# Hook Lambda: BeforeAllowTraffic
# Shifts ALB to 50/50, bakes for 10 minutes, then signals
# CodeDeploy to complete the final 100% shift to green
# -----------------------------------------------------------
data "archive_file" "hook_canary_50" {
  type        = "zip"
  output_path = "${path.module}/hook_canary_50.zip"

  source {
    filename = "handler.py"
    content  = <<-PYTHON
      import boto3, os, time

      codedeploy = boto3.client("codedeploy")
      elbv2      = boto3.client("elbv2")

      def handler(event, context):
          deployment_id   = event["DeploymentId"]
          lifecycle_event = event["LifecycleEventHookExecutionId"]

          blue_tg_arn  = os.environ["BLUE_TG_ARN"]
          green_tg_arn = os.environ["GREEN_TG_ARN"]
          listener_arn = os.environ["LISTENER_ARN"]
          bake_seconds = int(os.environ.get("BAKE_SECONDS", "600"))

          try:
              rules = elbv2.describe_rules(ListenerArn=listener_arn)["Rules"]
              default_rule = next(r for r in rules if r["IsDefault"])

              print(f"→ Shifting to 50/50 for {bake_seconds}s bake...")
              elbv2.modify_rule(
                  RuleArn=default_rule["RuleArn"],
                  Actions=[{
                      "Type": "forward",
                      "ForwardConfig": {
                          "TargetGroups": [
                              {"TargetGroupArn": blue_tg_arn,  "Weight": 50},
                              {"TargetGroupArn": green_tg_arn, "Weight": 50},
                          ],
                          "TargetGroupStickinessConfig": {"Enabled": False}
                      }
                  }]
              )

              time.sleep(bake_seconds)
              print("✓ Bake complete — signalling success for final 100% shift")
              status = "Succeeded"

          except Exception as e:
              print(f"✗ Canary 50% hook failed: {e}")
              status = "Failed"

          codedeploy.put_lifecycle_event_hook_execution_status(
              deploymentId=deployment_id,
              lifecycleEventHookExecutionId=lifecycle_event,
              status=status
          )
    PYTHON
  }
}

resource "aws_lambda_function" "hook_canary_50" {
  function_name    = "datapulse-${var.env}-hook-canary-50"
  role             = aws_iam_role.hooks.arn
  filename         = data.archive_file.hook_canary_50.output_path
  source_code_hash = data.archive_file.hook_canary_50.output_base64sha256
  handler          = "handler.handler"
  runtime          = "python3.12"
  timeout          = 720

  environment {
    variables = {
      BLUE_TG_ARN  = var.backend_blue_tg_arn
      GREEN_TG_ARN = var.backend_green_tg_arn
      LISTENER_ARN = var.https_listener_arn
      BAKE_SECONDS = "600"
    }
  }
}

# -----------------------------------------------------------
# Store hook ARNs in SSM so CD workflow can read them
# -----------------------------------------------------------
resource "aws_ssm_parameter" "hook_smoke_test_arn" {
  name  = "${var.ssm_prefix}/hook_smoke_test_arn"
  type  = "String"
  value = aws_lambda_function.hook_smoke_test.arn
}

resource "aws_ssm_parameter" "hook_canary_50_arn" {
  name  = "${var.ssm_prefix}/hook_canary_50_arn"
  type  = "String"
  value = aws_lambda_function.hook_canary_50.arn
}

# -----------------------------------------------------------
# CloudWatch Alarms — trigger CodeDeploy auto-rollback
# -----------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "backend_5xx" {
  alarm_name          = "datapulse-${var.env}-backend-5xx"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Sum"
  threshold           = 10
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
    TargetGroup  = var.backend_tg_arn_suffix
  }
}

resource "aws_cloudwatch_metric_alarm" "backend_latency" {
  alarm_name          = "datapulse-${var.env}-backend-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  extended_statistic  = "p99"
  threshold           = 5
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
    TargetGroup  = var.backend_tg_arn_suffix
  }
}

# -----------------------------------------------------------
# CodeDeploy App
# -----------------------------------------------------------
resource "aws_codedeploy_app" "main" {
  name             = "datapulse-${var.env}"
  compute_platform = "ECS"
}

# Custom canary config: 10% for 5 minutes, then 50% hook, then 100%
resource "aws_codedeploy_deployment_config" "canary" {
  deployment_config_name = "datapulse-${var.env}-canary"
  compute_platform       = "ECS"

  traffic_routing_config {
    type = "TimeBasedCanary"
    time_based_canary {
      interval   = 5
      percentage = 10
    }
  }
}

# -----------------------------------------------------------
# Deployment Group — Backend
# -----------------------------------------------------------
resource "aws_codedeploy_deployment_group" "backend" {
  app_name              = aws_codedeploy_app.main.name
  deployment_group_name = "datapulse-${var.env}-backend"
  service_role_arn      = aws_iam_role.codedeploy.arn
  deployment_config_name = aws_codedeploy_deployment_config.canary.id

  auto_rollback_configuration {
    enabled = true
    events  = ["DEPLOYMENT_FAILURE", "DEPLOYMENT_STOP_ON_ALARM"]
  }

  alarm_configuration {
    alarms  = [
      aws_cloudwatch_metric_alarm.backend_5xx.alarm_name,
      aws_cloudwatch_metric_alarm.backend_latency.alarm_name,
    ]
    enabled = true
  }

  blue_green_deployment_config {
    deployment_ready_option {
      action_on_timeout = "CONTINUE_DEPLOYMENT"
    }
    terminate_blue_instances_on_deployment_success {
      action                           = "TERMINATE"
      termination_wait_time_in_minutes = 10
    }
  }

  deployment_style {
    deployment_option = "WITH_TRAFFIC_CONTROL"
    deployment_type   = "BLUE_GREEN"
  }

  ecs_service {
    cluster_name = var.cluster_name
    service_name = var.backend_service_name
  }

  load_balancer_info {
    target_group_pair_info {
      prod_traffic_route { listener_arns = [var.https_listener_arn] }
      test_traffic_route { listener_arns = [var.test_listener_arn] }
      target_group { name = var.backend_blue_tg_name }
      target_group { name = var.backend_green_tg_name }
    }
  }
}

# -----------------------------------------------------------
# Deployment Group — Streamlit
# -----------------------------------------------------------
resource "aws_codedeploy_deployment_group" "streamlit" {
  app_name              = aws_codedeploy_app.main.name
  deployment_group_name = "datapulse-${var.env}-streamlit"
  service_role_arn      = aws_iam_role.codedeploy.arn
  deployment_config_name = aws_codedeploy_deployment_config.canary.id

  auto_rollback_configuration {
    enabled = true
    events  = ["DEPLOYMENT_FAILURE", "DEPLOYMENT_STOP_ON_ALARM"]
  }

  alarm_configuration {
    alarms  = [aws_cloudwatch_metric_alarm.backend_5xx.alarm_name]
    enabled = true
  }

  blue_green_deployment_config {
    deployment_ready_option {
      action_on_timeout = "CONTINUE_DEPLOYMENT"
    }
    terminate_blue_instances_on_deployment_success {
      action                           = "TERMINATE"
      termination_wait_time_in_minutes = 10
    }
  }

  deployment_style {
    deployment_option = "WITH_TRAFFIC_CONTROL"
    deployment_type   = "BLUE_GREEN"
  }

  ecs_service {
    cluster_name = var.cluster_name
    service_name = var.streamlit_service_name
  }

  load_balancer_info {
    target_group_pair_info {
      prod_traffic_route { listener_arns = [var.https_listener_arn] }
      test_traffic_route { listener_arns = [var.test_listener_arn] }
      target_group { name = var.streamlit_blue_tg_name }
      target_group { name = var.streamlit_green_tg_name }
    }
  }
}

# -----------------------------------------------------------
# Outputs
# -----------------------------------------------------------
output "app_name"                  { value = aws_codedeploy_app.main.name }
output "backend_deployment_group"  { value = aws_codedeploy_deployment_group.backend.deployment_group_name }
output "streamlit_deployment_group"{ value = aws_codedeploy_deployment_group.streamlit.deployment_group_name }
