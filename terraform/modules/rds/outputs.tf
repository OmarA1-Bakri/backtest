output "endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
}

output "db_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}

output "username" {
  description = "Database username"
  value       = aws_db_instance.main.username
}

output "port" {
  description = "Database port"
  value       = 5432
}

output "security_group_id" {
  description = "Security group ID"
  value       = aws_security_group.rds.id
}
