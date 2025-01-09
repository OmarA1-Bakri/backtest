terraform {
  required_version = ">= 1.0.0"
  
  # Comment out S3 backend for now
  # backend "s3" {
  #   bucket = "backtest-ai-terraform-state"
  #   key    = "staging/terraform.tfstate"
  #   region = "us-east-1"
  #   
  #   dynamodb_table = "backtest-ai-terraform-locks"
  #   encrypt        = true
  # }
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  # Use dummy credentials for testing
  skip_credentials_validation = true
  skip_requesting_account_id = true
  skip_metadata_api_check    = true
  s3_use_path_style         = true
  
  endpoints {
    apigateway     = "http://localhost:4566"
    cloudformation = "http://localhost:4566"
    cloudwatch     = "http://localhost:4566"
    dynamodb       = "http://localhost:4566"
    ec2            = "http://localhost:4566"
    ecs            = "http://localhost:4566"
    elasticache    = "http://localhost:4566"
    iam            = "http://localhost:4566"
    rds            = "http://localhost:4566"
    route53        = "http://localhost:4566"
    s3             = "http://localhost:4566"
    secretsmanager = "http://localhost:4566"
    ses            = "http://localhost:4566"
    sns            = "http://localhost:4566"
    sqs            = "http://localhost:4566"
  }
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "BackTest AI"
      ManagedBy   = "Terraform"
    }
  }
}

# VPC
module "vpc" {
  source = "./modules/vpc"
  
  environment         = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
}

# Application Load Balancer
module "alb" {
  source = "./modules/alb"
  
  environment     = var.environment
  vpc_id         = module.vpc.vpc_id
  public_subnets = module.vpc.public_subnet_ids
  
  app_name        = var.app_name
  container_port  = var.container_port
  certificate_arn = var.certificate_arn
  
  health_check_path = var.health_check_path
}

# ECS Cluster
module "ecs" {
  source = "./modules/ecs"
  
  environment      = var.environment
  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnet_ids
  
  app_name        = var.app_name
  container_image = var.container_image
  container_port  = var.container_port
  
  desired_count     = var.desired_count
  task_cpu         = var.task_cpu
  task_memory      = var.task_memory
  
  health_check_path = var.health_check_path
  alb_security_group_id = module.alb.security_group_id
  target_group_arn      = module.alb.target_group_blue_arn
}

# RDS Database
module "rds" {
  source = "./modules/rds"
  
  environment      = var.environment
  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnet_ids
  
  db_name     = var.db_name
  db_username = var.db_username
  db_password = var.db_password
  
  instance_class    = var.db_instance_class
  allocated_storage = var.db_allocated_storage
  
  app_security_group_id = module.ecs.security_group_id
  alarm_actions        = []  # We'll configure this later with SNS topics
}

# Redis Cache
module "redis" {
  source = "./modules/redis"
  
  environment      = var.environment
  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnet_ids
  
  node_type       = var.redis_node_type
  num_cache_nodes = var.redis_num_nodes
  
  app_security_group_id = module.ecs.security_group_id
  alarm_actions        = []  # We'll configure this later with SNS topics
}
