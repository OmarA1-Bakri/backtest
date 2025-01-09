output "alb_dns_name" {
  description = "DNS name of ALB"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of ALB"
  value       = aws_lb.main.zone_id
}

output "target_group_blue_arn" {
  description = "ARN of blue target group"
  value       = aws_lb_target_group.blue.arn
}

output "target_group_green_arn" {
  description = "ARN of green target group"
  value       = aws_lb_target_group.green.arn
}

output "https_listener_arn" {
  description = "ARN of HTTPS listener"
  value       = aws_lb_listener.https.arn
}

output "security_group_id" {
  description = "Security group ID of ALB"
  value       = aws_security_group.alb.id
}
