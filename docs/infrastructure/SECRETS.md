# Secrets Management Guide

This guide explains how secrets are managed in our application using AWS Secrets Manager.

## Overview

We use AWS Secrets Manager to securely store and manage sensitive information such as:
- Database credentials
- API keys
- Service account credentials
- Encryption keys

## Architecture

### Secret Storage
- Environment-specific secret stores
- JSON format for multiple key-value pairs
- Automatic encryption at rest
- Version history maintained

### Access Control
- IAM roles for service access
- Least privilege principle
- Audit logging via CloudTrail
- Regular access reviews

## Local Development

### Setting Up Local Environment

1. Create `.env.local`:
   ```bash
   # Development environment variables
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=backtest_dev
   DB_USER=dev_user
   DB_PASSWORD=local_password_only
   ```

2. Use environment loader:
   ```python
   from dotenv import load_dotenv
   
   # Load local environment variables
   load_dotenv('.env.local')
   ```

### Security Guidelines
- Never commit `.env` files
- Use dummy values for local development
- Keep production secrets in AWS Secrets Manager
- Regularly rotate development credentials

## Production Environment

### Accessing Secrets

1. **ECS Tasks**
   ```json
   {
     "containerDefinitions": [{
       "secrets": [
         {
           "name": "DB_PASSWORD",
           "valueFrom": "arn:aws:secretsmanager:region:account:secret:path"
         }
       ]
     }]
   }
   ```

2. **Application Code**
   ```python
   import boto3
   
   def get_secret(secret_name):
       client = boto3.client('secretsmanager')
       response = client.get_secret_value(SecretId=secret_name)
       return response['SecretString']
   ```

### Secret Rotation

1. **Automatic Rotation**
   - Enabled for supported secret types
   - Configurable rotation schedule
   - Lambda function handles rotation

2. **Manual Rotation**
   ```bash
   # Using AWS CLI
   aws secretsmanager rotate-secret \
     --secret-id MySecret \
     --rotation-lambda-arn arn:aws:lambda:region:account:function:name
   ```

## CI/CD Integration

### Pipeline Configuration
- Secrets accessed via AWS credentials
- Environment-specific secret access
- Temporary credentials for builds
- No secret values in logs

### Deployment Process
1. CI/CD pipeline authenticates to AWS
2. Retrieves necessary secrets
3. Injects secrets into deployment
4. Verifies secret access

## Best Practices

### Secret Management
1. **Naming Convention**
   ```
   /<environment>/<service>/<secret-name>
   ```
   Example: `/production/backtest/database-credentials`

2. **Secret Values**
   - Use strong random values
   - Store related secrets together
   - Include metadata when useful

3. **Access Patterns**
   - Cache secret values appropriately
   - Handle retrieval failures gracefully
   - Log access attempts (not values)

### Security Guidelines
1. **Access Control**
   - Restrict by environment
   - Use separate roles per service
   - Regular permission reviews

2. **Monitoring**
   - Enable CloudTrail logging
   - Set up alerts for:
     - Failed access attempts
     - Secret rotation failures
     - Configuration changes

3. **Rotation Policy**
   - Database credentials: 90 days
   - API keys: 180 days
   - Certificates: Before expiration
   - Service accounts: Annually

## Troubleshooting

### Common Issues

1. **Access Denied**
   - Check IAM roles/policies
   - Verify AWS credentials
   - Review CloudTrail logs

2. **Rotation Failures**
   - Check rotation Lambda logs
   - Verify network access
   - Review secret configuration

3. **Application Errors**
   - Check secret name/path
   - Verify environment variables
   - Review application logs

### Getting Help

1. Check AWS Secrets Manager documentation
2. Review CloudWatch logs
3. Contact security team in #security
4. Create high-priority ticket for production issues

## Security Incident Response

If you suspect a secret has been compromised:

1. **Immediate Actions**
   - Rotate compromised secrets
   - Review access logs
   - Notify security team

2. **Investigation**
   - Review CloudTrail logs
   - Check application logs
   - Document findings

3. **Recovery**
   - Deploy new secrets
   - Update applications
   - Verify system operation

4. **Prevention**
   - Update access policies
   - Enhance monitoring
   - Document lessons learned
