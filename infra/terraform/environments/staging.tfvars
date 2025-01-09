aws_region = "us-west-2"
vpc_cidr    = "10.1.0.0/16"

availability_zones = [
  "us-west-2a",
  "us-west-2b"
]

app_name        = "backtest"
container_port  = 8000
desired_count   = 1
domain_name     = "staging.backtest.example.com"

# Blue-green deployment weights
blue_weight  = 100
green_weight = 0

# Task configuration
task_cpu    = 256
task_memory = 512

frontend_bucket_name = "backtest-frontend-staging"
