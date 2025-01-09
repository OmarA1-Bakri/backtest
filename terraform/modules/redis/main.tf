resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.environment}-redis-subnet-group"
  subnet_ids = var.private_subnets
}

resource "aws_security_group" "redis" {
  name        = "${var.environment}-redis"
  description = "Allow inbound Redis traffic"
  vpc_id      = var.vpc_id
  
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
  }
  
  tags = {
    Environment = var.environment
    Name        = "${var.environment}-redis"
  }
}

resource "aws_elasticache_parameter_group" "main" {
  family = "redis6.x"
  name   = "${var.environment}-redis-params"
  
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id = "${var.environment}-redis"
  description         = "Redis cluster for ${var.environment}"
  
  node_type            = var.node_type
  port                 = 6379
  parameter_group_name = aws_elasticache_parameter_group.main.name
  
  snapshot_retention_limit = 7
  snapshot_window         = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"
  
  automatic_failover_enabled = true
  multi_az_enabled          = var.environment == "production"
  
  num_cache_clusters = var.num_cache_nodes
  
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  tags = {
    Environment = var.environment
    Name        = "${var.environment}-redis"
  }
}

resource "aws_cloudwatch_metric_alarm" "cache_cpu" {
  alarm_name          = "${var.environment}-redis-cpu-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors Redis CPU utilization"
  alarm_actions       = var.alarm_actions
  
  dimensions = {
    CacheClusterId = aws_elasticache_replication_group.main.id
  }
}

resource "aws_cloudwatch_metric_alarm" "cache_memory" {
  alarm_name          = "${var.environment}-redis-memory"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "FreeableMemory"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "100000000" # 100MB
  alarm_description   = "This metric monitors Redis freeable memory"
  alarm_actions       = var.alarm_actions
  
  dimensions = {
    CacheClusterId = aws_elasticache_replication_group.main.id
  }
}

resource "aws_cloudwatch_metric_alarm" "cache_hit_rate" {
  alarm_name          = "${var.environment}-redis-hit-rate"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CacheHitRate"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors Redis cache hit rate"
  alarm_actions       = var.alarm_actions
  
  dimensions = {
    CacheClusterId = aws_elasticache_replication_group.main.id
  }
}
