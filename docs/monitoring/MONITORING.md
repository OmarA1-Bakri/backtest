# System Monitoring Guide

## Overview

This document outlines the monitoring system implemented in the BackTest AI application, covering health checks, performance monitoring, and alerting.

## Health Checks

### System Health (`/health/system`)

Monitors system-level resources:
- CPU usage (overall and per core)
- Memory usage
- Disk usage
- Process-specific metrics

Example response:
```json
{
    "status": "healthy",
    "details": {
        "cpu": {
            "cores": 8,
            "usage_percent": 45.2,
            "per_cpu_percent": [40.1, 48.3, ...]
        },
        "memory": {
            "total": 16000000000,
            "available": 8000000000,
            "used": 8000000000,
            "percent": 50.0
        },
        "disk": {
            "total": 500000000000,
            "used": 250000000000,
            "free": 250000000000,
            "percent": 50.0
        },
        "process": {
            "pid": 1234,
            "memory_percent": 2.5,
            "cpu_percent": 1.2
        }
    }
}
```

### Database Health (`/health/database`)

Monitors database connectivity and performance:
- Connection status
- Query response time
- Connection pool stats
- Database size and row counts

Example response:
```json
{
    "status": "healthy",
    "details": {
        "response_time_ms": 5.2,
        "stats": {
            "row_count": 10000,
            "db_size": "1.2 GB",
            "connections": 5
        },
        "connection_pool": {
            "size": 5,
            "overflow": 0,
            "timeout": 30
        }
    }
}
```

### Redis Health (`/health/redis`)

Monitors Redis cache health:
- Connection status
- Memory usage
- Client connections
- Pool statistics

Example response:
```json
{
    "status": "healthy",
    "details": {
        "ping": true,
        "used_memory": "1.5M",
        "connected_clients": 3,
        "uptime_seconds": 3600,
        "pool_stats": {
            "max_connections": 10,
            "current_connections": 2
        }
    }
}
```

## Performance Monitoring

### Operation Metrics (`/performance/{operation}`)

Track execution time and errors for specific operations:
- Response time
- Error rate
- Operation frequency

Example response:
```json
{
    "operation": "process_backtest",
    "metrics": [
        {
            "timestamp": "2024-12-29T12:00:00Z",
            "duration_ms": 1500.2,
            "error": null
        }
    ],
    "summary": {
        "count": 100,
        "avg_duration_ms": 1200.5,
        "error_count": 2
    }
}
```

### Slow Operations (`/performance/slow`)

Identify operations exceeding performance thresholds:
- Configurable threshold
- Average duration
- Occurrence count
- Recent examples

Example response:
```json
{
    "threshold_ms": 1000,
    "operations": [
        {
            "operation": "complex_calculation",
            "avg_duration_ms": 2500.3,
            "count": 50,
            "recent_metrics": [...]
        }
    ]
}
```

## Usage Patterns

### Tracking Operation Performance

Use the performance decorator:
```python
from core.monitoring.performance import performance_monitor

@performance_monitor.track_execution_time()
async def my_function():
    # Function implementation
    pass
```

### Health Check Integration

Add to your FastAPI application:
```python
from api.endpoints import health

app.include_router(health.router, tags=["health"])
```

## Best Practices

1. **Regular Monitoring**
   - Check health endpoints periodically
   - Monitor slow operations
   - Track system resource usage

2. **Performance Thresholds**
   - Set appropriate thresholds for your environment
   - Adjust based on observed patterns
   - Consider different thresholds for different operations

3. **Error Handling**
   - Monitor error rates
   - Investigate recurring errors
   - Set up alerts for critical errors

4. **Resource Management**
   - Monitor memory usage trends
   - Track connection pool utilization
   - Watch for resource leaks

## Alert Rules

### Critical Alerts

1. **System Health**
   - CPU usage > 90% for 5 minutes
   - Memory usage > 90%
   - Disk usage > 90%

2. **Database Health**
   - Response time > 1000ms
   - Connection pool exhaustion
   - High error rate (>5%)

3. **Redis Health**
   - Connection failures
   - Memory usage > 90%
   - High latency (>100ms)

### Warning Alerts

1. **System Performance**
   - CPU usage > 70% for 10 minutes
   - Memory usage > 80%
   - Disk usage > 80%

2. **Operation Performance**
   - Response time > threshold
   - Increasing error rate
   - Unusual patterns

## Monitoring Dashboard

Recommended metrics to display:
1. System resource usage over time
2. Database connection and query stats
3. Redis performance metrics
4. Slow operation trends
5. Error rate patterns

## Maintenance

1. **Log Rotation**
   - Implement log rotation
   - Archive old metrics
   - Clean up performance data

2. **Alert Tuning**
   - Review and adjust thresholds
   - Update alert rules
   - Monitor false positives

3. **Performance Optimization**
   - Analyze slow operations
   - Optimize resource usage
   - Tune connection pools

## Security Considerations

1. **Access Control**
   - Restrict access to monitoring endpoints
   - Implement authentication
   - Use secure connections

2. **Data Protection**
   - Sanitize sensitive data in logs
   - Secure metric storage
   - Protect monitoring endpoints

3. **Compliance**
   - Follow data retention policies
   - Implement audit logging
   - Maintain security standards
