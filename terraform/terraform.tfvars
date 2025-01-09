# Environment
environment = "staging"
aws_region  = "us-east-1"

# Application
app_name        = "backtest-ai"
container_image = "backtest-ai:latest"
container_port  = 8000
desired_count   = 2
task_cpu        = 256
task_memory     = 512

# VPC
vpc_cidr = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
private_subnet_cidrs = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]

# Database
db_name             = "backtest"
db_username         = "admin"
db_password         = "dummy-password"  # Change this in production
db_instance_class   = "db.t3.micro"
db_allocated_storage = 20

# Redis
redis_node_type  = "cache.t3.micro"
redis_num_nodes  = 1

# Load Balancer
certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/dummy-cert"  # Replace with actual cert ARN
health_check_path = "/health"
