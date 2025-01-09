#!/bin/bash

# Exit on error
set -e

echo "Verifying CI/CD pipeline..."

# Check if required secrets are set
check_secrets() {
    local missing_secrets=()
    
    # List of required secrets
    declare -a secrets=(
        "AWS_ACCESS_KEY_ID"
        "AWS_SECRET_ACCESS_KEY"
        "SNYK_TOKEN"
        "SLACK_WEBHOOK_URL"
        "STAGING_FRONTEND_BUCKET"
        "STAGING_ECS_CLUSTER"
        "ROUTE53_ZONE_ID"
        "PROD_TASK_DEFINITION"
        "PROD_ECS_CLUSTER"
        "PROD_ECS_SERVICE"
        "PROD_FRONTEND_BUCKET"
        "PROD_API_URL"
        "PROD_FRONTEND_URL"
        "ALB_HOSTED_ZONE_ID"
        "DOMAIN_NAME"
    )
    
    for secret in "${secrets[@]}"; do
        if [ -z "${!secret}" ]; then
            missing_secrets+=("$secret")
        fi
    done
    
    if [ ${#missing_secrets[@]} -ne 0 ]; then
        echo "Error: Missing required secrets:"
        printf '%s\n' "${missing_secrets[@]}"
        exit 1
    fi
}

# Run backend tests
run_backend_tests() {
    echo "Running backend tests..."
    pytest --cov=./ --cov-report=xml
    
    # Check coverage threshold
    coverage_score=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')
    if (( $(echo "$coverage_score < 80" | bc -l) )); then
        echo "Error: Coverage ($coverage_score%) is below threshold (80%)"
        exit 1
    fi
}

# Run frontend tests
run_frontend_tests() {
    echo "Running frontend tests..."
    cd Frontend
    npm run test:coverage
    
    # Check coverage threshold
    if ! npm run test:coverage | grep -q "All files.*|.*80.*|.*80.*|.*80.*|.*80"; then
        echo "Error: Frontend coverage is below threshold (80%)"
        exit 1
    fi
    cd ..
}

# Run security checks
run_security_checks() {
    echo "Running security checks..."
    
    # Run Snyk security scan
    snyk test
    
    # Run npm audit
    cd Frontend
    npm audit
    cd ..
}

# Verify deployment configurations
verify_deployments() {
    echo "Verifying deployment configurations..."
    
    # Check AWS configuration
    aws configure list
    
    # Verify ECS clusters
    echo "Verifying ECS clusters..."
    aws ecs describe-clusters --clusters $STAGING_ECS_CLUSTER
    aws ecs describe-clusters --clusters $PROD_ECS_CLUSTER
    
    # Verify S3 buckets
    echo "Verifying S3 buckets..."
    aws s3 ls s3://$STAGING_FRONTEND_BUCKET
    aws s3 ls s3://$PROD_FRONTEND_BUCKET
    aws s3 ls s3://$PROD_FRONTEND_BUCKET-green
    
    # Verify Route53 configuration
    echo "Verifying Route53 configuration..."
    aws route53 get-hosted-zone --id $ROUTE53_ZONE_ID
    
    # Verify task definitions
    echo "Verifying task definitions..."
    aws ecs describe-task-definition --task-definition $PROD_TASK_DEFINITION
    aws ecs describe-task-definition --task-definition $PROD_TASK_DEFINITION-green
}

# Verify blue-green deployment configuration
verify_blue_green() {
    echo "Verifying blue-green deployment configuration..."
    
    # Check Route53 JSON files
    if [ ! -f "infrastructure/deployment/route53-update.json" ] || [ ! -f "infrastructure/deployment/route53-rollback.json" ]; then
        echo "Error: Missing Route53 configuration files"
        exit 1
    fi
    
    # Verify health check endpoints
    echo "Verifying health check endpoints..."
    curl -f https://$PROD_API_URL/health || {
        echo "Error: Blue environment health check failed"
        exit 1
    }
    
    curl -f https://$PROD_API_URL-green/health || {
        echo "Warning: Green environment not currently deployed (this is normal if no deployment is in progress)"
    }
    
    # Verify ALB configuration
    echo "Verifying ALB configuration..."
    aws elbv2 describe-load-balancers --names $PROD_ECS_SERVICE
    aws elbv2 describe-load-balancers --names $PROD_ECS_SERVICE-green
}

# Main execution
echo "Starting pipeline verification..."

# Check environment
check_secrets

# Run tests
run_backend_tests
run_frontend_tests

# Security checks
run_security_checks

# Verify deployments
verify_deployments

# Verify blue-green deployment
verify_blue_green

echo "Pipeline verification completed successfully!"
