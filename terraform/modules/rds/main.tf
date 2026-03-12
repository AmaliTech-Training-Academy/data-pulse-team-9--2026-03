variable "env"                { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "rds_sg_id"          { type = string }
variable "instance_class"     {
   type = string
 default = "db.t4g.micro"
 }

# Passwords injected from Secrets Manager — not stored in state
variable "operational_password" {
  type = string
 sensitive = true
}
variable "analytics_password"   {
  type = string
 sensitive = true
}
variable "operational_username" { type = string }
variable "analytics_username"   { type = string }
variable "operational_db_name"  { type = string }
variable "analytics_db_name"    { type = string }

# -----------------------------------------------------------
# Subnet Group (shared by both instances)
# -----------------------------------------------------------
resource "aws_db_subnet_group" "main" {
  name       = "datapulse-${var.env}"
  subnet_ids = var.private_subnet_ids
  tags       = { Name = "datapulse-${var.env}-rds-subnet-group" }
}

# -----------------------------------------------------------
# Parameter Group — Postgres 15
# -----------------------------------------------------------
resource "aws_db_parameter_group" "postgres15" {
  name   = "datapulse-${var.env}-postgres15"
  family = "postgres15"

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }
  parameter {
    name  = "log_min_duration_statement"
    value = "1000"   # log queries > 1s
  }
}

# -----------------------------------------------------------
# Operational DB
# -----------------------------------------------------------
resource "aws_db_instance" "operational" {
  identifier        = "datapulse-${var.env}-operational"
  engine            = "postgres"
  engine_version    = "15"
  instance_class    = var.instance_class
  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = var.operational_db_name
  username = var.operational_username
  password = var.operational_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.rds_sg_id]
  parameter_group_name   = aws_db_parameter_group.postgres15.name

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"
  deletion_protection     = true
  skip_final_snapshot     = false
  final_snapshot_identifier = "datapulse-${var.env}-operational-final"

  performance_insights_enabled = false   # saves ~$0/mo on t4g.micro (not supported)
  monitoring_interval          = 0       # enhanced monitoring off on micro

  tags = {
    Name         = "datapulse-${var.env}-operational"
    Environment  = var.env
    Project      = "datapulse"
    ScheduleStop = "true"
  }
}

# -----------------------------------------------------------
# Analytics DB
# -----------------------------------------------------------
resource "aws_db_instance" "analytics" {
  identifier        = "datapulse-${var.env}-analytics"
  engine            = "postgres"
  engine_version    = "15"
  instance_class    = var.instance_class
  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = var.analytics_db_name
  username = var.analytics_username
  password = var.analytics_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.rds_sg_id]
  parameter_group_name   = aws_db_parameter_group.postgres15.name

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"
  deletion_protection     = true
  skip_final_snapshot     = false
  final_snapshot_identifier = "datapulse-${var.env}-analytics-final"

  performance_insights_enabled = false
  monitoring_interval          = 0

  tags = {
    Name         = "datapulse-${var.env}-analytics"
    Environment  = var.env
    Project      = "datapulse"
    ScheduleStop = "true"
  }
}

# -----------------------------------------------------------
# Outputs
# -----------------------------------------------------------
output "operational_endpoint" { value = aws_db_instance.operational.endpoint }
output "analytics_endpoint"   { value = aws_db_instance.analytics.endpoint }
output "operational_id"       { value = aws_db_instance.operational.identifier }
output "analytics_id"         { value = aws_db_instance.analytics.identifier }
