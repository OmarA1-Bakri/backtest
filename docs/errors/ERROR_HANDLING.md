# Error Handling Guide

## Overview

This document outlines the error handling strategy implemented in the BackTest AI application, covering exception hierarchy, error handling middleware, and the alerting system.

## Exception Hierarchy

### Base Exception
- `BacktestError`: Base exception class for all application errors
  - Contains: message, error_code, details, status_code

### Specific Exceptions
1. **Validation Errors**
   - `ValidationError`: Input validation failures
   - Status Code: 400

2. **Authentication Errors**
   - `AuthenticationError`: Authentication failures
   - Status Code: 401

3. **Authorization Errors**
   - `AuthorizationError`: Authorization failures
   - Status Code: 403

4. **Resource Errors**
   - `NotFoundError`: Resource not found
   - Status Code: 404

5. **Infrastructure Errors**
   - `DatabaseError`: Database operation failures
   - `CacheError`: Cache operation failures
   - Status Code: 500

6. **Business Logic Errors**
   - `BacktestExecutionError`: Backtest execution failures
   - `StrategyError`: Strategy operation failures
   - `DataError`: Data operation failures
   - Status Code: 500

## Error Handling Strategy

### 1. Exception Handling

```python
from core.errors.exceptions import ValidationError

def process_data(data: Dict):
    if not validate_data(data):
        raise ValidationError(
            message="Invalid data format",
            details={"errors": validation_errors}
        )
```

### 2. Error Middleware

The error handling middleware:
1. Catches all exceptions
2. Formats error response
3. Logs error details
4. Tracks error metrics
5. Returns consistent JSON response

Example Response:
```json
{
    "status_code": 400,
    "error_code": "VALIDATION_ERROR",
    "message": "Invalid data format",
    "details": {
        "errors": [
            "field 'price' must be positive"
        ]
    }
}
```

### 3. Error Logging

Errors are logged with context:
- Request details (method, URL, headers)
- Error details (code, message, stack trace)
- System context (resource usage, etc.)

Example:
```python
logger.error(
    "Error processing request",
    extra={
        "error_details": error_dict,
        "request_context": context,
        "traceback": exc.__traceback__
    }
)
```

## Alert System

### Alert Thresholds

1. **Critical Alerts**
   - CPU usage > 90%
   - Memory usage > 90%
   - Disk usage > 90%
   - Redis connection failure
   - Database connection failure

2. **Warning Alerts**
   - CPU usage > 70%
   - Memory usage > 80%
   - High error rate (>5%)
   - Slow database response (>1000ms)

### Alert Configuration

```python
AlertThreshold(
    name="high_cpu_usage",
    condition="system['cpu']['usage_percent'] > 90",
    severity="critical",
    cooldown_minutes=5,
    description="CPU usage exceeds 90%"
)
```

### Alert Lifecycle

1. **Detection**
   - Regular threshold checks
   - System metrics monitoring
   - Error rate calculation

2. **Processing**
   - Alert creation
   - Cooldown period enforcement
   - Context gathering

3. **Storage**
   - Redis-based storage
   - 24-hour retention
   - Queryable history

4. **Notification**
   - Severity-based routing
   - Multiple channels (logs, email, etc.)
   - Rate limiting

## Best Practices

### 1. Exception Handling

```python
try:
    # Operation that might fail
    result = await process_data(data)
except ValidationError as e:
    # Handle validation errors
    logger.warning(f"Validation failed: {e.message}")
    raise
except DatabaseError as e:
    # Handle database errors
    logger.error(f"Database error: {e.message}")
    raise
except Exception as e:
    # Handle unexpected errors
    logger.error(f"Unexpected error: {str(e)}")
    raise BacktestError(
        message="An unexpected error occurred",
        error_code="INTERNAL_ERROR",
        details={"original_error": str(e)}
    )
```

### 2. Error Response Format

Always return consistent error responses:
```python
{
    "status_code": int,
    "error_code": str,
    "message": str,
    "details": Dict[str, Any]
}
```

### 3. Error Tracking

Track errors for analysis:
```python
await performance_monitor._store_execution_metrics(
    operation="error",
    duration_ms=0,
    error=exc,
    metrics={
        "error_code": error_code,
        "endpoint": endpoint,
        "method": method
    }
)
```

## Testing Error Handling

### 1. Unit Tests

Test individual error cases:
```python
def test_validation_error():
    with pytest.raises(ValidationError) as exc:
        process_invalid_data()
    assert exc.value.error_code == "VALIDATION_ERROR"
    assert exc.value.status_code == 400
```

### 2. Integration Tests

Test error middleware:
```python
async def test_error_middleware():
    response = await client.get("/invalid")
    assert response.status_code == 404
    assert response.json()["error_code"] == "NOT_FOUND"
```

### 3. Alert Tests

Test alert system:
```python
async def test_alert_threshold():
    alerts = await alert_manager.check_thresholds()
    assert any(
        alert.name == "high_cpu_usage"
        for alert in alerts
    )
```

## Monitoring and Maintenance

### 1. Error Metrics

Monitor:
- Error rates by type
- Response times
- Resource usage
- Alert frequency

### 2. Alert Tuning

Regular review of:
- Threshold values
- Cooldown periods
- Alert patterns
- False positives

### 3. Error Analysis

Regular analysis of:
- Common error patterns
- System bottlenecks
- Performance issues
- Security incidents

## Security Considerations

1. **Error Messages**
   - Never expose sensitive data
   - Use generic messages for public
   - Log detailed info securely

2. **Rate Limiting**
   - Limit error responses
   - Prevent DoS attacks
   - Track suspicious patterns

3. **Access Control**
   - Restrict error details
   - Secure error logs
   - Control alert access
