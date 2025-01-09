terraform {
  required_version = ">= 1.0.0"

  backend "s3" {
    # Will be configured via backend-config during init
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "backtest"
      ManagedBy   = "terraform"
    }
  }
}

# VPC and Networking
module "vpc" {
  source = "./modules/vpc"

  environment         = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
}

# ECS Cluster and Services
module "ecs" {
  source = "./modules/ecs"

  environment      = var.environment
  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets
  public_subnets  = module.vpc.public_subnets

  app_name        = var.app_name
  container_image = var.container_image
  container_port  = var.container_port
  desired_count   = var.desired_count

  depends_on = [module.vpc]
}

# Route53 DNS Records
module "dns" {
  source = "./modules/dns"

  environment       = var.environment
  domain_name      = var.domain_name
  alb_dns_name     = module.ecs.alb_dns_name
  alb_zone_id      = module.ecs.alb_zone_id
  blue_weight      = var.blue_weight
  green_weight     = var.green_weight

  depends_on = [module.ecs]
}

# S3 Buckets for Frontend
module "s3" {
  source = "./modules/s3"

  environment  = var.environment
  bucket_name = var.frontend_bucket_name
}

# Secrets Manager
module "secrets" {
  source = "./modules/secrets"

  environment = var.environment
  app_name    = var.app_name
}
