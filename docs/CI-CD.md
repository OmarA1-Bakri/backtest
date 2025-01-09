# CI/CD Pipeline Documentation

## Overview
This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the Backtest application. The pipeline uses GitHub Actions for automation and AWS services for deployment.

## Pipeline Structure

### 1. Continuous Integration (ci.yml)
Triggered on:
- Push to `main` and `develop` branches
- Pull requests to `main` and `develop` branches

Components:
- **Backend Tests**
  - Python 3.10 environment
  - Redis service container
  - Dependency installation
  - Linting (black, pylint, mypy)
  - Unit tests with coverage
  - Coverage report upload to Codecov

- **Frontend Tests**
  - Node.js 18 environment
  - NPM dependency caching
  - ESLint checks
  - Prettier formatting checks
  - TypeScript type checking
  - Unit tests with coverage
  - Coverage report upload to Codecov

- **Database Tests**
  - Migration tests
  - Schema verification
  - Rollback tests
  - Database connection tests

- **Build**
  - Builds both backend and frontend
  - Creates deployable artifacts
  - Uploads artifacts for deployment workflows

### 2. Staging Deployment (staging-deploy.yml)
Triggered on:
- Push to `develop` branch
- Successful CI workflow completion

Steps:
1. Downloads build artifacts
2. Configures AWS credentials
3. Runs database migrations
4. Deploys frontend to S3 bucket
5. Updates ECS service for backend
6. Runs health checks
7. Sends Slack notifications

### 3. Production Deployment (production-deploy.yml)
Triggered on:
- Release publication

Steps:
1. Downloads build artifacts
2. Creates deployment tag
3. Backs up current production version
4. Runs database migrations with rollback safety
5. Deploys to green environment
6. Runs health checks
7. Switches traffic if successful
8. Cleans up blue environment
9. Sends deployment notifications

## Environment Variables and Secrets

### Required Secrets
1. AWS Credentials:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`

2. Database Credentials:
   - `DB_HOST`
   - `DB_PORT`
   - `DB_NAME`
   - `DB_USER`
   - `DB_PASSWORD`

3. Staging Environment:
   - `STAGING_FRONTEND_BUCKET`
   - `STAGING_ECS_CLUSTER`
   - `STAGING_ECS_SERVICE`
   - `STAGING_API_URL`
   - `STAGING_FRONTEND_URL`

4. Production Environment:
   - `PROD_FRONTEND_BUCKET`
   - `PROD_ECS_CLUSTER`
   - `PROD_ECS_SERVICE`
   - `PROD_API_URL`
   - `PROD_FRONTEND_URL`
   - `ROUTE53_ZONE_ID`
   - `ALB_HOSTED_ZONE_ID`

5. Notifications:
   - `SLACK_WEBHOOK_URL`

## Development Workflow

### Local Development
1. Clone repository
2. Install dependencies:
   ```bash
   # Backend
   pip install -r requirements.txt
   
   # Frontend
   cd Frontend
   npm install
   ```

3. Set up database:
   ```bash
   # Set environment variables
   export DB_HOST=localhost
   export DB_PORT=5432
   export DB_NAME=backtest
   export DB_USER=your_username
   export DB_PASSWORD=your_password
   
   # Run migrations
   python scripts/manage_db.py migrate
   ```

4. Run tests:
   ```bash
   # Backend
   pytest
   
   # Frontend
   npm test
   
   # Database
   python scripts/manage_db.py verify
   ```

### Creating Pull Requests
1. Create feature branch from `develop`
2. Make changes and commit
3. If database changes:
   - Update models
   - Create migration: `python scripts/manage_db.py create --message "description"`
   - Test migration locally
   - Commit migration file separately
4. Push branch and create PR
5. CI pipeline will automatically run
6. Review and address any failures
7. Merge when approved and CI passes

### Releasing to Production
1. Merge `develop` into `main`
2. Create a new release in GitHub
3. Tag version following semver
4. Production deployment will trigger automatically

## Monitoring Deployments

### Viewing Pipeline Status
1. GitHub Actions tab in repository
2. Click on workflow run
3. View job details and logs

### Deployment Notifications
- Slack channel: #deployments
- Includes:
  - Deployment status
  - Environment
  - Version/commit
  - Migration status
  - Duration
  - Any failures

### Health Checks
- Backend: `/health` endpoint
- Frontend: Homepage load
- Database: Schema version verification
- Metrics in Grafana dashboards

## Rollback Procedures

### Automatic Rollback
Production deployments include automatic rollback if:
1. Database migrations fail:
   - Rolls back to previous migration version
   - Halts deployment

2. Health checks fail:
   - Frontend reverts to backup in S3
   - Backend reverts to previous task definition
   - Database remains at current version (migrations succeeded)

3. Traffic switch fails:
   - Route53 records revert to blue environment
   - Green environment is cleaned up
   - Database remains at current version

### Manual Rollback
If needed, manual rollback steps:
1. Database:
   ```bash
   # Roll back to specific version
   python scripts/manage_db.py rollback --tag <revision_id>
   
   # Verify schema
   python scripts/manage_db.py verify
   ```

2. Frontend:
   ```bash
   aws s3 sync s3://[bucket]-backup-[tag]/ s3://[bucket]/ --delete
   ```

3. Backend:
   ```bash
   aws ecs update-service --cluster [cluster] --service [service] --task-definition [previous-version]
   ```

## Troubleshooting

### Common Issues
1. Failed Tests
   - Check test logs in GitHub Actions
   - Run tests locally to reproduce
   - Review coverage reports

2. Migration Failures
   - Check migration logs
   - Verify database connectivity
   - Review migration files for errors
   - Test rollback procedures

3. Deployment Failures
   - Check health check logs
   - Verify AWS credentials
   - Check service logs in CloudWatch
   - Verify database schema version

4. Build Issues
   - Verify dependencies are up to date
   - Check build logs for errors
   - Confirm environment variables are set

### Getting Help
1. Check existing issues in GitHub
2. Contact DevOps team in #devops Slack channel
3. Review AWS and GitHub Actions documentation
4. For database issues, check `docs/database/MIGRATIONS.md`
