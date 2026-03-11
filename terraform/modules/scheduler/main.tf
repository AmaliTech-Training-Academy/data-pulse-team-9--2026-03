variable "env"         { type = string }
variable "aws_region"  { type = string }
variable "ssm_prefix"  { type = string }

# Optional — only used for prod ECS scheduler
variable "ecs_cluster_name" {
  type = string
 default = ""
 }
variable "ecs_services"     {
  type = list(string)
  default = []
  }
variable "rds_instance_ids" {
  type = list(string)
  default = []
  }

# Determines which scheduler to create
variable "mode" {
  type        = string
  description = "ec2 (dev) or ecs (prod)"
  default     = "ec2"
  validation {
    condition     = contains(["ec2", "ecs"], var.mode)
    error_message = "mode must be ec2 or ecs"
  }
}

# -----------------------------------------------------------
# Shared IAM role
# -----------------------------------------------------------
resource "aws_iam_role" "scheduler" {
  name = "datapulse-${var.env}-scheduler"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "scheduler" {
  name = "datapulse-${var.env}-scheduler"
  role = aws_iam_role.scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      # Logs — always needed
      [{
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      }],
      # SSM — read instance ID (ec2 mode)
      var.mode == "ec2" ? [{
        Effect   = "Allow"
        Action   = ["ssm:GetParameter"]
        Resource = "arn:aws:ssm:${var.aws_region}:*:parameter${var.ssm_prefix}/scheduler/instance_id"
      }] : [],
      # EC2 start/stop (ec2 mode) — scoped by tags
      var.mode == "ec2" ? [{
        Effect   = "Allow"
        Action   = ["ec2:StartInstances", "ec2:StopInstances", "ec2:DescribeInstances"]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:ResourceTag/Environment" = var.env
            "aws:ResourceTag/Project"     = "datapulse"
          }
        }
      }] : [],
      # ECS update service (ecs mode)
      var.mode == "ecs" && length(var.ecs_services) > 0 ? [{
        Effect   = "Allow"
        Action   = ["ecs:UpdateService", "ecs:DescribeServices"]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:ResourceTag/Environment" = var.env
            "aws:ResourceTag/Project"     = "datapulse"
          }
        }
      }] : [],
      # RDS start/stop (ecs mode)
      var.mode == "ecs" && length(var.rds_instance_ids) > 0 ? [{
        Effect   = "Allow"
        Action   = ["rds:StartDBInstance", "rds:StopDBInstance", "rds:DescribeDBInstances"]
        Resource = [for id in var.rds_instance_ids : "arn:aws:rds:${var.aws_region}:*:db:${id}"]
      }] : [],
    )
  })
}

# -----------------------------------------------------------
# Python source — stored in locals to avoid heredoc-in-ternary
# HCL cannot parse <<-HEREDOC inside a ternary expression
# -----------------------------------------------------------
locals {
  stop_ec2_code = <<-PYTHON
import boto3, os

ec2 = boto3.client("ec2")
ssm = boto3.client("ssm")

def handler(event, context):
    instance_id = ssm.get_parameter(
        Name=os.environ["INSTANCE_ID_PARAM"]
    )["Parameter"]["Value"]
    print(f"Stopping EC2 {instance_id}...")
    ec2.stop_instances(InstanceIds=[instance_id])
    print("Stop initiated")
PYTHON

  stop_ecs_code = <<-PYTHON
import boto3, os

ecs = boto3.client("ecs")
rds = boto3.client("rds")

def handler(event, context):
    cluster  = os.environ["ECS_CLUSTER"]
    services = os.environ["ECS_SERVICES"].split(",")
    rds_ids  = os.environ["RDS_INSTANCES"].split(",")
    for svc in services:
        print(f"Scaling {svc} to 0...")
        ecs.update_service(cluster=cluster, service=svc, desiredCount=0)
    for db_id in rds_ids:
        print(f"Stopping RDS {db_id}...")
        try:
            rds.stop_db_instance(DBInstanceIdentifier=db_id)
        except Exception as e:
            print(f"Warning: {e}")
    print("Prod scaled to zero")
PYTHON

  start_ec2_code = <<-PYTHON
import boto3, os

ec2 = boto3.client("ec2")
ssm = boto3.client("ssm")

def handler(event, context):
    instance_id = ssm.get_parameter(
        Name=os.environ["INSTANCE_ID_PARAM"]
    )["Parameter"]["Value"]
    print(f"Starting EC2 {instance_id}...")
    ec2.start_instances(InstanceIds=[instance_id])
    waiter = ec2.get_waiter("instance_running")
    waiter.wait(InstanceIds=[instance_id])
    print("Instance running")
PYTHON

  start_ecs_code = <<-PYTHON
import boto3, os

ecs = boto3.client("ecs")
rds = boto3.client("rds")

DESIRED = {
    "datapulse-prod-backend":       1,
    "datapulse-prod-celery-worker": 1,
    "datapulse-prod-celery-beat":   1,
    "datapulse-prod-streamlit":     1,
}

def handler(event, context):
    cluster = os.environ["ECS_CLUSTER"]
    rds_ids = os.environ["RDS_INSTANCES"].split(",")
    for db_id in rds_ids:
        print(f"Starting RDS {db_id}...")
        try:
            rds.start_db_instance(DBInstanceIdentifier=db_id)
        except Exception as e:
            print(f"Warning: {e}")
    print("Waiting for RDS to be available...")
    waiter = rds.get_waiter("db_instance_available")
    for db_id in rds_ids:
        waiter.wait(
            DBInstanceIdentifier=db_id,
            WaiterConfig={"Delay": 15, "MaxAttempts": 40}
        )
        print(f"  {db_id} available")
    for svc, count in DESIRED.items():
        print(f"Scaling {svc} to {count}...")
        ecs.update_service(cluster=cluster, service=svc, desiredCount=count)
    print("Prod started")
PYTHON
}

# -----------------------------------------------------------
# Lambda — STOP
# -----------------------------------------------------------
data "archive_file" "stop" {
  type        = "zip"
  output_path = "${path.module}/stop_${var.env}.zip"

  source {
    filename = "handler.py"
    content  = var.mode == "ec2" ? local.stop_ec2_code : local.stop_ecs_code
  }
}

resource "aws_lambda_function" "stop" {
  function_name    = "datapulse-${var.env}-stop"
  role             = aws_iam_role.scheduler.arn
  filename         = data.archive_file.stop.output_path
  source_code_hash = data.archive_file.stop.output_base64sha256
  handler          = "handler.handler"
  runtime          = "python3.12"
  timeout          = 60

  environment {
    variables = var.mode == "ec2" ? {
      INSTANCE_ID_PARAM = "${var.ssm_prefix}/scheduler/instance_id"
    } : {
      ECS_CLUSTER   = var.ecs_cluster_name
      ECS_SERVICES  = join(",", var.ecs_services)
      RDS_INSTANCES = join(",", var.rds_instance_ids)
    }
  }
}

# -----------------------------------------------------------
# Lambda — START
# -----------------------------------------------------------
data "archive_file" "start" {
  type        = "zip"
  output_path = "${path.module}/start_${var.env}.zip"

  source {
    filename = "handler.py"
    content  = var.mode == "ec2" ? local.start_ec2_code : local.start_ecs_code
  }
}

resource "aws_lambda_function" "start" {
  function_name    = "datapulse-${var.env}-start"
  role             = aws_iam_role.scheduler.arn
  filename         = data.archive_file.start.output_path
  source_code_hash = data.archive_file.start.output_base64sha256
  handler          = "handler.handler"
  runtime          = "python3.12"
  timeout          = 720   # RDS can take up to 10 min to start

  environment {
    variables = var.mode == "ec2" ? {
      INSTANCE_ID_PARAM = "${var.ssm_prefix}/scheduler/instance_id"
    } : {
      ECS_CLUSTER   = var.ecs_cluster_name
      RDS_INSTANCES = join(",", var.rds_instance_ids)
    }
  }
}

# -----------------------------------------------------------
# EventBridge rules — weekdays 7am start / 8pm stop (UTC)
# -----------------------------------------------------------
resource "aws_cloudwatch_event_rule" "stop" {
  name                = "datapulse-${var.env}-stop"
  schedule_expression = "cron(0 20 ? * MON-FRI *)"
  description         = "Stop datapulse-${var.env} at 8pm UTC weekdays"
}

resource "aws_cloudwatch_event_rule" "start" {
  name                = "datapulse-${var.env}-start"
  schedule_expression = "cron(0 7 ? * MON-FRI *)"
  description         = "Start datapulse-${var.env} at 7am UTC weekdays"
}

resource "aws_cloudwatch_event_target" "stop" {
  rule      = aws_cloudwatch_event_rule.stop.name
  target_id = "StopLambda"
  arn       = aws_lambda_function.stop.arn
}

resource "aws_cloudwatch_event_target" "start" {
  rule      = aws_cloudwatch_event_rule.start.name
  target_id = "StartLambda"
  arn       = aws_lambda_function.start.arn
}

resource "aws_lambda_permission" "stop" {
  statement_id  = "AllowEventBridgeStop"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.stop.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.stop.arn
}

resource "aws_lambda_permission" "start" {
  statement_id  = "AllowEventBridgeStart"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.start.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.start.arn
}

# -----------------------------------------------------------
# Outputs
# -----------------------------------------------------------
output "stop_lambda_arn"  { value = aws_lambda_function.stop.arn }
output "start_lambda_arn" { value = aws_lambda_function.start.arn }
