# VPC Configuration
vpc_cidr = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
private_subnet_cidrs = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]

# ECS Configuration
app_name = "backtest-ai"
container_port = 80
desired_count = 2
task_cpu = 256
task_memory = 512

# RDS Configuration
db_instance_class = "db.t3.micro"
db_allocated_storage = 20

# Redis Configuration
redis_node_type = "cache.t3.micro"
redis_num_nodes = 1

# Health Check Configuration
health_check_path = "/health"
