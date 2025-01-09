# Infrastructure Management Guide

This guide explains how infrastructure is managed using Terraform in our application.

## Overview

Our infrastructure is defined as code using Terraform and includes:
- VPC and networking components
- ECS clusters and services
- Application Load Balancers
- Route53 DNS records
- S3 buckets for frontend assets
- AWS Secrets Manager for sensitive data

## Directory Structure

```
infra/
├── terraform/
│   ├── main.tf              # Main Terraform configuration
│   ├── variables.tf         # Variable definitions
│   ├── modules/
│   │   ├── vpc/            # VPC and networking
│   │   ├── ecs/            # ECS cluster and services
│   │   ├── dns/            # Route53 configuration
│   │   ├── s3/             # S3 buckets
│   │   └── secrets/        # Secrets management
│   └── environments/
│       ├── staging.tfvars  # Staging environment variables
│       └── production.tfvars # Production environment variables
```

## Local Development

### Prerequisites
- Terraform 1.5.0 or higher
- AWS CLI configured with appropriate credentials
- Python 3.10 or higher

### Setting Up Local Environment

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Initialize Terraform:
   ```bash
   python scripts/manage_infra.py init --env staging
   ```

3. Validate configuration:
   ```bash
   python scripts/manage_infra.py validate --env staging
   ```

4. Plan changes:
   ```bash
   python scripts/manage_infra.py plan \
     --env staging \
     --vars-file infra/terraform/environments/staging.tfvars
   ```

### Making Infrastructure Changes

1. Create a new branch:
   ```bash
   git checkout -b feature/infra-change
   ```

2. Make changes to Terraform files
3. Test locally:
   ```bash
   # Validate changes
   python scripts/manage_infra.py validate --env staging
   
   # Review plan
   python scripts/manage_infra.py plan \
     --env staging \
     --vars-file infra/terraform/environments/staging.tfvars
   ```

4. Create pull request
   - CI will automatically validate changes
   - Plan output will be added as PR comment
   - Required reviewers must approve

## CI/CD Integration

### Pull Request Validation
- Triggered on changes to `infra/` directory
- Validates Terraform configuration
- Generates plans for staging and production
- Posts plan output as PR comment

### Deployment Process
1. Changes merged to main branch
2. CI/CD pipeline:
   - Validates infrastructure
   - Applies changes to staging
   - Requires approval for production
   - Applies changes to production

## Blue-Green Deployments

Our infrastructure supports blue-green deployments:

1. **Load Balancer Configuration**
   - Two target groups (blue/green)
   - Weighted routing between environments
   - Health checks for both environments

2. **DNS Management**
   - Separate DNS records for blue/green
   - Main record for current active environment
   - Quick rollback via DNS

3. **Deployment Process**
   - Deploy to green environment
   - Verify health checks
   - Gradually shift traffic
   - Cleanup old blue environment

## Secrets Management

We use AWS Secrets Manager for sensitive data:

1. **Storing Secrets**
   - Environment-specific secret stores
   - Encrypted at rest
   - Version control for secrets

2. **Accessing Secrets**
   - ECS tasks use IAM roles
   - Application retrieves secrets at runtime
   - Automatic secret rotation support

3. **Local Development**
   - Use local `.env` files
   - Never commit secrets to repo
   - Documentation in `SECRETS.md`

## Best Practices

1. **Change Management**
   - Always create PR for changes
   - Include context and reasoning
   - Tag relevant team members
   - Consider maintenance windows

2. **Security**
   - Follow least privilege principle
   - Regular security audits
   - Monitor AWS Config rules
   - Enable CloudTrail logging

3. **Cost Management**
   - Review cost implications
   - Use cost estimation tools
   - Tag resources properly
   - Clean up unused resources

## Troubleshooting

### Common Issues

1. **Terraform State Lock**
   ```bash
   # Force unlock if needed
   terraform force-unlock LOCK_ID
   ```

2. **Failed Apply**
   - Check CloudWatch logs
   - Verify AWS credentials
   - Review error messages
   - Consider manual cleanup

3. **Resource Dependencies**
   - Review dependency graph
   - Check for circular dependencies
   - Verify destroy order

### Getting Help

1. Check AWS documentation
2. Review Terraform documentation
3. Contact DevOps team in #devops
4. Create GitHub issue with details
