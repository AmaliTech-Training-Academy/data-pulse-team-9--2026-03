variable "env"                    { type = string }
variable "aws_region"             { type = string }
variable "private_subnet_ids"     { type = list(string) }
variable "ecs_sg_id"              { type = string }
variable "backend_tg_arn"         { type = string }
variable "streamlit_tg_arn"       { type = string }
variable "backend_image"          { type = string }
variable "etl_image"              { type = string }
variable "streamlit_image"        { type = string }
variable "backend_cpu"            {
  type = number
 default = 256
  }
variable "backend_memory"         {
   type = number
 default = 512
 }
variable "backend_task_count"     {
   type = number
 default = 1
 }
variable "celery_worker_count"    {
   type = number
 default = 1
 }
variable "ssm_prefix"             { type = string }
variable "secrets_manager_prefix" { type = string }

# -----------------------------------------------------------
# ECS Cluster + Capacity Providers (Fargate + Fargate Spot)
# -----------------------------------------------------------
resource "aws_ecs_cluster" "main" {
  name = "datapulse-${var.env}"
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  tags = { Name = "datapulse-${var.env}", Environment = var.env, Project = "datapulse" }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name       = aws_ecs_cluster.main.name
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
    base              = 1
  }
}

# -----------------------------------------------------------
# CloudWatch Log Groups — 14 day retention
# -----------------------------------------------------------
locals {
  services = ["backend", "celery-worker", "celery-beat", "etl", "streamlit"]
}

resource "aws_cloudwatch_log_group" "services" {
  for_each          = toset(local.services)
  name              = "/datapulse/${var.env}/${each.key}"
  retention_in_days = 14
}

# -----------------------------------------------------------
# IAM — Execution Role (pulls images, injects secrets)
# -----------------------------------------------------------
resource "aws_iam_role" "execution" {
  name = "datapulse-${var.env}-ecs-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "execution_basic" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "execution_secrets" {
  name = "datapulse-${var.env}-secrets"
  role = aws_iam_role.execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = "arn:aws:secretsmanager:${var.aws_region}:*:secret:${var.secrets_manager_prefix}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["ssm:GetParameter", "ssm:GetParameters", "ssm:GetParametersByPath"]
        Resource = "arn:aws:ssm:${var.aws_region}:*:parameter${var.ssm_prefix}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["kms:Decrypt"]
        Resource = "*"
      }
    ]
  })
}

# -----------------------------------------------------------
# IAM — Task Role (runtime permissions for app code)
# -----------------------------------------------------------
resource "aws_iam_role" "task" {
  name = "datapulse-${var.env}-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "task" {
  name = "datapulse-${var.env}-task"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:${var.aws_region}:*:log-group:/datapulse/${var.env}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["ssm:GetParameter"]
        Resource = "arn:aws:ssm:${var.aws_region}:*:parameter${var.ssm_prefix}/*"
      }
    ]
  })
}

# -----------------------------------------------------------
# Shared secret references (used across task definitions)
# -----------------------------------------------------------
locals {
  secret_ref = {
    database_url = {
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.secrets_manager_prefix}/database_url"
    }
    target_db_url = {
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.secrets_manager_prefix}/target_db_url"
    }
    secret_key = {
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.secrets_manager_prefix}/secret_key"
    }
    redis_url = {
      valueFrom = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.secrets_manager_prefix}/redis_url"
    }
  }

  ssm_ref = {
    django_settings = {
      valueFrom = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${var.ssm_prefix}/django_settings_module"
    }
  }
}

data "aws_caller_identity" "current" {}

# -----------------------------------------------------------
# Task Definition — Backend
# -----------------------------------------------------------
resource "aws_ecs_task_definition" "backend" {
  family                   = "datapulse-${var.env}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.backend_cpu
  memory                   = var.backend_memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name      = "backend"
    image     = var.backend_image
    essential = true

    portMappings = [{ containerPort = 8000, protocol = "tcp" }]

    secrets = [
      { name = "DATABASE_URL",   valueFrom = local.secret_ref.database_url.valueFrom },
      { name = "SECRET_KEY",     valueFrom = local.secret_ref.secret_key.valueFrom },
      { name = "CELERY_BROKER_URL", valueFrom = local.secret_ref.redis_url.valueFrom },
      { name = "CELERY_RESULT_BACKEND", valueFrom = local.secret_ref.redis_url.valueFrom },
      { name = "DJANGO_SETTINGS_MODULE", valueFrom = local.ssm_ref.django_settings.valueFrom },
    ]

    environment = [
      { name = "DEBUG",             value = "False" },
      { name = "GUNICORN_WORKERS",  value = "2" },
      { name = "GUNICORN_THREADS",  value = "2" },
      { name = "GUNICORN_LOG_LEVEL", value = "info" },
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/datapulse/${var.env}/backend"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }

    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8000/health/ || exit 1"]
      interval    = 30
      timeout     = 10
      retries     = 3
      startPeriod = 60
    }
  }])
}

# -----------------------------------------------------------
# Task Definition — Celery Worker
# -----------------------------------------------------------
resource "aws_ecs_task_definition" "celery_worker" {
  family                   = "datapulse-${var.env}-celery-worker"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name      = "celery-worker"
    image     = var.backend_image
    essential = true
    command   = ["celery", "-A", "datapulse", "worker", "--loglevel=info"]

    secrets = [
      { name = "DATABASE_URL",         valueFrom = local.secret_ref.database_url.valueFrom },
      { name = "SECRET_KEY",           valueFrom = local.secret_ref.secret_key.valueFrom },
      { name = "CELERY_BROKER_URL",    valueFrom = local.secret_ref.redis_url.valueFrom },
      { name = "CELERY_RESULT_BACKEND", valueFrom = local.secret_ref.redis_url.valueFrom },
      { name = "DJANGO_SETTINGS_MODULE", valueFrom = local.ssm_ref.django_settings.valueFrom },
    ]

    environment = [{ name = "DEBUG", value = "False" }]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/datapulse/${var.env}/celery-worker"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# -----------------------------------------------------------
# Task Definition — Celery Beat
# -----------------------------------------------------------
resource "aws_ecs_task_definition" "celery_beat" {
  family                   = "datapulse-${var.env}-celery-beat"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512  # Changed from 256 to 512 (valid Fargate combination)
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name      = "celery-beat"
    image     = var.backend_image
    essential = true
    command   = ["celery", "-A", "datapulse", "beat", "-l", "info",
                 "--scheduler", "django_celery_beat.schedulers:DatabaseScheduler"]

    secrets = [
      { name = "DATABASE_URL",         valueFrom = local.secret_ref.database_url.valueFrom },
      { name = "SECRET_KEY",           valueFrom = local.secret_ref.secret_key.valueFrom },
      { name = "CELERY_BROKER_URL",    valueFrom = local.secret_ref.redis_url.valueFrom },
      { name = "CELERY_RESULT_BACKEND", valueFrom = local.secret_ref.redis_url.valueFrom },
      { name = "DJANGO_SETTINGS_MODULE", valueFrom = local.ssm_ref.django_settings.valueFrom },
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/datapulse/${var.env}/celery-beat"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# -----------------------------------------------------------
# Task Definition — Streamlit
# -----------------------------------------------------------
resource "aws_ecs_task_definition" "streamlit" {
  family                   = "datapulse-${var.env}-streamlit"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name      = "streamlit"
    image     = var.streamlit_image
    essential = true

    portMappings = [{ containerPort = 8501, protocol = "tcp" }]

    secrets = [
      { name = "TARGET_DB_URL", valueFrom = local.secret_ref.target_db_url.valueFrom },
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/datapulse/${var.env}/streamlit"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }

    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8501/_stcore/health || exit 1"]
      interval    = 30
      timeout     = 10
      retries     = 3
      startPeriod = 60
    }
  }])
}

# -----------------------------------------------------------
# Task Definition — ETL (scheduled, runs then exits)
# -----------------------------------------------------------
resource "aws_ecs_task_definition" "etl" {
  family                   = "datapulse-${var.env}-etl"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name      = "etl"
    image     = var.etl_image
    essential = true

    secrets = [
      { name = "SOURCE_DB_URL", valueFrom = local.secret_ref.database_url.valueFrom },
      { name = "TARGET_DB_URL", valueFrom = local.secret_ref.target_db_url.valueFrom },
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/datapulse/${var.env}/etl"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# -----------------------------------------------------------
# ECS Services
# -----------------------------------------------------------

# Backend — 50% On-Demand / 50% Spot (blue/green via CodeDeploy)
resource "aws_ecs_service" "backend" {
  name            = "datapulse-${var.env}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.backend_task_count

  # Deployment controller MUST be CODE_DEPLOY for blue/green
  deployment_controller { type = "CODE_DEPLOY" }

  capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
    base              = 1
  }
  capacity_provider_strategy {
    capacity_provider = "FARGATE_SPOT"
    weight            = 1
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_sg_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.backend_tg_arn
    container_name   = "backend"
    container_port   = 8000
  }

  # Ignore task_definition + load_balancer changes — CodeDeploy manages these
  lifecycle {
    ignore_changes = [task_definition, load_balancer]
  }

  tags = { Environment = var.env, Project = "datapulse" }
}

# Celery Worker — 100% Spot (tasks are retryable)
resource "aws_ecs_service" "celery_worker" {
  name            = "datapulse-${var.env}-celery-worker"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.celery_worker.arn
  desired_count   = var.celery_worker_count

  deployment_controller { type = "ECS" }

  capacity_provider_strategy {
    capacity_provider = "FARGATE_SPOT"
    weight            = 1
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_sg_id]
    assign_public_ip = false
  }

  lifecycle { ignore_changes = [task_definition] }

  tags = { Environment = var.env, Project = "datapulse" }
}

# Celery Beat — 100% Spot, always exactly 1 task
resource "aws_ecs_service" "celery_beat" {
  name            = "datapulse-${var.env}-celery-beat"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.celery_beat.arn
  desired_count   = 1

  deployment_controller { type = "ECS" }

  capacity_provider_strategy {
    capacity_provider = "FARGATE_SPOT"
    weight            = 1
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_sg_id]
    assign_public_ip = false
  }

  lifecycle { ignore_changes = [task_definition] }

  tags = { Environment = var.env, Project = "datapulse" }
}

# Streamlit — 100% Spot, blue/green via CodeDeploy
resource "aws_ecs_service" "streamlit" {
  name            = "datapulse-${var.env}-streamlit"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.streamlit.arn
  desired_count   = 1

  deployment_controller { type = "CODE_DEPLOY" }

  capacity_provider_strategy {
    capacity_provider = "FARGATE_SPOT"
    weight            = 1
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_sg_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.streamlit_tg_arn
    container_name   = "streamlit"
    container_port   = 8501
  }

  lifecycle {
    ignore_changes = [task_definition, load_balancer]
  }

  tags = { Environment = var.env, Project = "datapulse" }
}

# -----------------------------------------------------------
# ETL Scheduled Task — EventBridge runs it at 2am UTC daily
# -----------------------------------------------------------
resource "aws_iam_role" "etl_events" {
  name = "datapulse-${var.env}-etl-events"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "etl_events" {
  name = "datapulse-${var.env}-etl-run"
  role = aws_iam_role.etl_events.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "ecs:RunTask"
      Resource = aws_ecs_task_definition.etl.arn
      Condition = {
        ArnLike = { "ecs:cluster" = aws_ecs_cluster.main.arn }
      }
    }, {
      Effect   = "Allow"
      Action   = "iam:PassRole"
      Resource = [aws_iam_role.execution.arn, aws_iam_role.task.arn]
    }]
  })
}

resource "aws_cloudwatch_event_rule" "etl" {
  name                = "datapulse-${var.env}-etl"
  schedule_expression = "cron(0 2 * * ? *)"
  description         = "Run ETL pipeline daily at 2am UTC"
}

resource "aws_cloudwatch_event_target" "etl" {
  rule     = aws_cloudwatch_event_rule.etl.name
  arn      = aws_ecs_cluster.main.arn
  role_arn = aws_iam_role.etl_events.arn

  ecs_target {
    task_definition_arn = aws_ecs_task_definition.etl.arn
    task_count          = 1
    launch_type         = "FARGATE"

    network_configuration {
      subnets          = var.private_subnet_ids
      security_groups  = [var.ecs_sg_id]
      assign_public_ip = false
    }
  }
}

# -----------------------------------------------------------
# Outputs
# -----------------------------------------------------------
output "cluster_name"           { value = aws_ecs_cluster.main.name }
output "cluster_arn"            { value = aws_ecs_cluster.main.arn }
output "backend_service_name"   { value = aws_ecs_service.backend.name }
output "streamlit_service_name" { value = aws_ecs_service.streamlit.name }
output "backend_td_family"      { value = aws_ecs_task_definition.backend.family }
output "streamlit_td_family"    { value = aws_ecs_task_definition.streamlit.family }
