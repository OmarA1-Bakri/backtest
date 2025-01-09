variable "environment" {
  description = "Environment name (e.g., staging, production)"
  type        = string
}

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-west-2"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "backtest"
}

variable "container_image" {
  description = "Docker image to deploy"
  type        = string
}

variable "container_port" {
  description = "Container port to expose"
  type        = number
  default     = 8000
}

variable "desired_count" {
  description = "Desired number of container instances"
  type        = number
  default     = 2
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
}

variable "blue_weight" {
  description = "Weight for blue environment traffic"
  type        = number
  default     = 100
}

variable "green_weight" {
  description = "Weight for green environment traffic"
  type        = number
  default     = 0
}

variable "frontend_bucket_name" {
  description = "Name of the S3 bucket for frontend assets"
  type        = string
}
