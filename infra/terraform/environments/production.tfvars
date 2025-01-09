aws_region = "us-west-2"
vpc_cidr    = "10.0.0.0/16"

availability_zones = [
  "us-west-2a",
  "us-west-2b",
  "us-west-2c"
]

app_name        = "backtest"
container_port  = 8000
desired_count   = 3
domain_name     = "backtest.example.com"

# Blue-green deployment weights
blue_weight  = 100
green_weight = 0

# Task configuration
task_cpu    = 512
task_memory = 1024

frontend_bucket_name = "backtest-frontend-production"
