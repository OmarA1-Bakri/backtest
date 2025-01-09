resource "aws_db_subnet_group" "main" {
  name       = "${var.environment}-${var.db_name}"
  subnet_ids = var.private_subnets
  
  tags = {
    Environment = var.environment
    Name        = "${var.environment}-${var.db_name}"
  }
}

resource "aws_security_group" "rds" {
  name        = "${var.environment}-${var.db_name}-rds"
  description = "Allow inbound database traffic"
  vpc_id      = var.vpc_id
  
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
  }
  
  tags = {
    Environment = var.environment
    Name        = "${var.environment}-${var.db_name}-rds"
  }
}

resource "aws_db_instance" "main" {
  identifier = "${var.environment}-${var.db_name}"
  
  engine         = "postgres"
  engine_version = "13.7"
  
  instance_class    = var.instance_class
  allocated_storage = var.allocated_storage
  
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"
  
  multi_az               = var.environment == "production"
  skip_final_snapshot    = var.environment != "production"
  deletion_protection    = var.environment == "production"
  
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  
  performance_insights_enabled = true
  
  tags = {
    Environment = var.environment
    Name        = "${var.environment}-${var.db_name}"
  }
}

resource "aws_cloudwatch_metric_alarm" "database_cpu" {
  alarm_name          = "${var.environment}-${var.db_name}-cpu-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS CPU utilization"
  alarm_actions       = var.alarm_actions
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
}

resource "aws_cloudwatch_metric_alarm" "database_memory" {
  alarm_name          = "${var.environment}-${var.db_name}-freeable-memory"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "FreeableMemory"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "100000000" # 100MB
  alarm_description   = "This metric monitors RDS freeable memory"
  alarm_actions       = var.alarm_actions
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
}

resource "aws_cloudwatch_metric_alarm" "database_disk" {
  alarm_name          = "${var.environment}-${var.db_name}-free-storage"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "1000000000" # 1GB
  alarm_description   = "This metric monitors RDS free storage space"
  alarm_actions       = var.alarm_actions
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
}
