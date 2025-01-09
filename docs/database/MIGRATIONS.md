# Database Migrations Guide

This guide explains how database migrations are handled in our application using Alembic.

## Overview

We use Alembic for managing database migrations. The migration process is fully automated in our CI/CD pipeline and includes:
- Automatic migration execution during deployments
- Schema version verification
- Rollback procedures for failed migrations
- Blue-green deployment integration

## Local Development

### Prerequisites
- Python 3.10 or higher
- PostgreSQL database
- Required Python packages (install via `pip install -r requirements.txt`)

### Environment Setup

Set the following environment variables:
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=backtest
export DB_USER=your_username
export DB_PASSWORD=your_password
```

### Creating New Migrations

1. Make your changes to the SQLAlchemy models in the codebase
2. Create a new migration:

   ```bash
   python scripts/manage_db.py create --message "description_of_changes"
   ```
3. Review the generated migration file in `database/migrations/versions/`
4. Test the migration locally:
   ```bash
   python scripts/manage_db.py migrate
   ```

### Verifying Database Schema

To verify your local database schema matches the latest migration:
```bash
python scripts/manage_db.py verify
```

### Rolling Back Migrations

To rollback to a specific revision:
```bash
python scripts/manage_db.py rollback --tag <revision_id>
```

## CI/CD Pipeline Integration

### Deployment Process

1. **Pre-deployment**
   - Current database state is verified
   - Migration history is backed up

2. **Migration Execution**
   - New migrations are automatically run
   - Schema version is verified
   - If migrations fail, deployment is halted

3. **Blue-Green Deployment**
   - Migrations run before green environment deployment
   - Traffic only switches if migrations succeed
   - Automatic rollback if any step fails

### Rollback Procedures

#### Automatic Rollback
The pipeline automatically handles rollbacks in case of:
- Failed migrations
- Failed health checks
- Failed deployment verification

#### Manual Rollback
If manual intervention is needed:

1. Access the production database:
   ```bash
   # Set production environment variables
   source .env.production
   
   # Rollback to specific version
   python scripts/manage_db.py rollback --tag <revision_id>
   ```

2. Verify the rollback:
   ```bash
   python scripts/manage_db.py verify
   ```

## Troubleshooting

### Common Issues

1. **Migration Conflicts**
   - Ensure your local branch is up to date
   - Check for conflicting migration versions
   - Review migration dependencies

2. **Schema Verification Failures**
   - Compare local and production schemas
   - Check for missing migrations
   - Verify environment variables

3. **Rollback Failures**
   - Check database connectivity
   - Review migration logs
   - Verify rollback dependencies

### Getting Help

1. Check the deployment logs in GitHub Actions
2. Review the application logs in CloudWatch
3. Contact the database administrator for production issues

## Best Practices

1. **Migration Safety**
   - Always include both `upgrade()` and `downgrade()` operations
   - Test migrations on staging before production
   - Use transactions for data migrations

2. **Version Control**
   - Commit migration files separately from model changes
   - Include clear descriptions in migration messages
   - Tag significant database versions

3. **Testing**
   - Test migrations with representative data
   - Verify rollback procedures
   - Include migration tests in CI pipeline
