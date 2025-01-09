# Production Incident Runbook

## Quick Reference
- **Production URL:** https://[your-domain]
- **Staging URL:** https://staging.[your-domain]
- **Monitoring Dashboard:** https://grafana.[your-domain]
- **Error Tracking:** https://sentry.io/organizations/backtest/
- **Slack Channel:** #prod-incidents

## Incident Severity Levels

### Severity 1 (Critical)
- System is completely down
- Data loss or corruption
- Security breach
- **Response Time:** Immediate (< 15 minutes)

### Severity 2 (High)
- Major feature unavailable
- Significant performance degradation
- **Response Time:** < 30 minutes

### Severity 3 (Medium)
- Minor feature issues
- Non-critical performance issues
- **Response Time:** < 2 hours

## Emergency Contacts
1. Primary On-Call Engineer
2. Backend Team Lead
3. Frontend Team Lead
4. DevOps Lead
5. Engineering Manager

## Common Incidents and Resolution Steps

### 1. Production Deployment Failure

#### Symptoms
- Failed health checks
- 5xx errors in production
- Deployment pipeline errors

#### Resolution Steps
1. **Immediate Actions:**
   ```bash
   # Check deployment status
   aws ecs describe-services --cluster prod-cluster --services backtest-service
   
   # View recent logs
   aws logs get-log-events --log-group-name /ecs/backtest-prod
   ```

2. **Rollback Procedure:**
   ```bash
   # Rollback frontend
   aws s3 sync s3://backtest-prod-backup-[tag]/ s3://backtest-prod/ --delete
   
   # Rollback backend
   aws ecs update-service --cluster prod-cluster --service backtest-service \
     --task-definition backtest-prod:[previous-version]
   ```

3. **Verify Recovery:**
   - Check health endpoints
   - Verify critical user flows
   - Monitor error rates

### 2. Performance Degradation

#### Symptoms
- High latency alerts
- Increased error rates
- CPU/Memory alerts

#### Resolution Steps
1. **Check System Metrics:**
   - Review Grafana dashboards
   - Check Redis cache hit rates
   - Monitor database connections

2. **Quick Fixes:**
   ```bash
   # Scale up ECS service
   aws ecs update-service --cluster prod-cluster --service backtest-service \
     --desired-count [increased-count]
   
   # Clear Redis cache if needed
   redis-cli FLUSHALL
   ```

3. **If Persists:**
   - Review recent code changes
   - Check for database bottlenecks
   - Analyze slow queries

### 3. Data Pipeline Issues

#### Symptoms
- Failed backtest jobs
- Stale data alerts
- Queue backlog alerts

#### Resolution Steps
1. **Check Pipeline Status:**
   ```bash
   # View Celery queue
   celery -A backtest.celery inspect active
   
   # Check task status
   celery -A backtest.celery inspect reserved
   ```

2. **Recovery Actions:**
   - Restart failed tasks
   - Clear stuck queues
   - Verify data consistency

## Post-Incident Procedures

### 1. Incident Report
Create a detailed incident report including:
- Timeline of events
- Root cause analysis
- Resolution steps taken
- Prevention measures

### 2. Update Documentation
- Update runbook if needed
- Document new failure modes
- Update monitoring thresholds

### 3. Follow-up Tasks
- Create JIRA tickets for improvements
- Schedule post-mortem meeting
- Update alert thresholds if needed

## Preventive Measures

### 1. Pre-Release Checklist
- [ ] All tests passing
- [ ] Security scan clear
- [ ] Performance benchmarks reviewed
- [ ] Database migrations tested
- [ ] Rollback procedure verified
- [ ] Environment variables checked
- [ ] Dependencies reviewed
- [ ] API compatibility verified

### 2. Regular Maintenance
- Weekly dependency updates
- Monthly security audits
- Quarterly load testing
- Regular backup verification

## Useful Commands

### Health Checks
```bash
# Backend health
curl -v https://api.backtest.com/health

# Check ECS service health
aws ecs describe-services --cluster prod-cluster --services backtest-service
```

### Logs
```bash
# View ECS logs
aws logs get-log-events --log-group-name /ecs/backtest-prod

# View application logs
tail -f /var/log/backtest/application.log
```

### Deployment
```bash
# View deployment status
aws deploy get-deployment --deployment-id [deployment-id]

# List recent deployments
aws deploy list-deployments --application-name backtest
```

### Database
```bash
# Check connections
SELECT count(*) FROM pg_stat_activity;

# Kill long queries
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE state = 'active' AND state_change < now() - interval '5 minutes';
```

## Additional Resources
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Redis Commands](https://redis.io/commands)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
