variable "env"               { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "redis_sg_id"        { type = string }
variable "node_type"          {
  type = string
 default = "cache.t4g.micro"
 }

resource "aws_elasticache_subnet_group" "main" {
  name       = "datapulse-${var.env}"
  subnet_ids = var.private_subnet_ids
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "datapulse-${var.env}"
  engine               = "redis"
  engine_version       = "7.1"
  node_type            = var.node_type
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [var.redis_sg_id]

  tags = {
    Name        = "datapulse-${var.env}-redis"
    Environment = var.env
    Project     = "datapulse"
  }
}

output "endpoint" { value = aws_elasticache_cluster.redis.cache_nodes[0].address }
