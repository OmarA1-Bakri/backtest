resource "aws_secretsmanager_secret" "app_secrets" {
  name = "${var.environment}/${var.app_name}"
  
  tags = {
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    "db-password" = var.db_password
    "api-key"     = var.api_key
    # Add other secrets as needed
  })
}

# IAM role for ECS tasks to access secrets
resource "aws_iam_role" "secret_access" {
  name = "${var.environment}-${var.app_name}-secret-access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "secret_access" {
  name = "${var.environment}-${var.app_name}-secret-access"
  role = aws_iam_role.secret_access.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.app_secrets.arn
        ]
      }
    ]
  })
}
