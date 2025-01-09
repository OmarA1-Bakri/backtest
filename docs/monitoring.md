# Monitoring and Logging Guide

## Overview
This document describes the monitoring and logging infrastructure for the Backtest application. The system uses structured logging, Prometheus metrics, and Grafana dashboards to provide comprehensive observability.

## Structured Logging

### Log Format
All logs are in JSON format and include the following fields:
- `timestamp`: ISO 8601 timestamp
- `level`: Log level (INFO, WARNING, ERROR, etc.)
- `logger`: Logger name
- `message`: Log message
- `request_id`: Unique identifier for HTTP requests
- `method`: HTTP method (for API requests)
- `path`: Request path (for API requests)
- `duration`: Request/task duration in seconds
- `environment`: Application environment
- `service`: Service name

### Accessing Logs
- Development: Logs are written to `logs/backtest.log` and stdout
- Production: Logs are forwarded to a centralized logging system
- View logs using:
  ```bash
  tail -f logs/backtest.log | jq
  ```

## Error Tracking (Sentry)

### Configuration
- Environment variables:
  - `SENTRY_DSN`: Sentry project DSN
  - `ENVIRONMENT`: Application environment

### Accessing Sentry
1. Log in to Sentry dashboard: https://sentry.io
2. Navigate to the Backtest project
3. View:
   - Recent errors
   - Error trends
   - Performance metrics
   - User impact

## Metrics (Prometheus)

### Available Metrics
1. HTTP Metrics:
   - `http_requests_total`: Request count by method, endpoint, and status
   - `http_request_duration_seconds`: Request latency histograms
   - `http_errors_total`: Error count by type

2. Task Metrics:
   - `celery_tasks_total`: Task count by name and status
   - `celery_task_duration_seconds`: Task duration histograms
   - `celery_queue_size`: Queue size by queue name

3. Cache Metrics:
   - `cache_hits_total`: Cache hit count
   - `cache_misses_total`: Cache miss count

4. System Metrics:
   - `system_cpu_usage`: CPU usage percentage
   - `system_memory_usage_bytes`: Memory usage

### Accessing Metrics
- Endpoint: `/metrics`
- Format: Prometheus text format
- Example:
  ```bash
  curl http://localhost:5000/metrics
  ```

## Distributed Tracing

### OpenTelemetry Setup
The application uses OpenTelemetry for distributed tracing with Jaeger as the backend:

1. **Configuration:**
   ```python
   from monitoring.tracing import TracingConfig
   
   tracer = TracingConfig(
       service_name="backtest-service",
       jaeger_host="localhost",
       jaeger_port=6831
   )
   tracer.setup_tracing()
   ```

2. **Component Instrumentation:**
   - Flask application:
     ```python
     tracer.instrument_flask(app)
     ```
   - Celery tasks:
     ```python
     tracer.instrument_celery(celery_app)
     ```
   - Database:
     ```python
     tracer.instrument_sqlalchemy(engine)
     ```

3. **Viewing Traces:**
   - Access Jaeger UI at: http://localhost:16686
   - Filter by service name: "backtest-service"
   - View end-to-end request flows and component interactions

## Strategy Performance Metrics

### Available Metrics
1. **Execution Metrics:**
   - `strategy_execution_seconds`: Execution time histogram
   - `strategy_errors_total`: Error count by type

2. **Performance Metrics:**
   - `strategy_returns_percent`: Returns distribution
   - `strategy_sharpe_ratio`: Current Sharpe ratio
   - `strategy_max_drawdown_percent`: Maximum drawdown

3. **Trading Metrics:**
   - `strategy_trades_total`: Trade count by position type
   - `strategy_trade_volume_total`: Trading volume by asset

### Recording Metrics
```python
from monitoring.metrics import MetricsRecorder

recorder = MetricsRecorder(strategy_name="my_strategy", timeframe="1h")
recorder.record_returns(15.5)
recorder.update_sharpe_ratio(2.1)
recorder.record_trade("long")
```

## Alerting

### Alert Rules
The following alert conditions are configured:

1. **Critical Alerts:**
   - High error rate (>10% in 5min)
   - Execution time >5min (95th percentile)

2. **Warning Alerts:**
   - Returns below -10% (15min window)
   - Drawdown exceeding 20%
   - Sharpe ratio below 0.5 (1h window)

### Alert Response Guide

1. **High Error Rate:**
   - Check error logs in Sentry
   - Verify external service health
   - Review recent code deployments

2. **Poor Performance:**
   - Analyze market conditions
   - Check strategy parameters
   - Review recent trades

3. **Slow Execution:**
   - Monitor system resources
   - Check database performance
   - Review task queue backlog

## Grafana Dashboards

### Main Dashboard
Located at: `monitoring/grafana/dashboards/backtest_dashboard.json`

Panels:
1. Request Rate
2. CPU Usage
3. Average Response Time
4. Task Success/Failure Rate

### Accessing Dashboards
1. Log in to Grafana: http://localhost:3000
2. Navigate to Dashboards > Backtest
3. Default time range: Last 1 hour
4. Refresh rate: 5 seconds

## Incident Response

### Steps
1. Receive alert notification
2. Access relevant dashboards and logs
3. Identify the issue:
   - Check error logs in Sentry
   - Review metrics in Grafana
   - Analyze request patterns
4. Take corrective action:
   - Restart services if needed
   - Scale resources if required
   - Roll back recent deployments if necessary

### Contact Information
- Primary on-call: [Contact Details]
- Secondary on-call: [Contact Details]
- Engineering manager: [Contact Details]

## Development Guidelines

### Adding New Metrics
1. Define metric in `core/metrics.py`
2. Register with Prometheus registry
3. Update Grafana dashboard
4. Document metric in this guide

### Adding New Logs
1. Use structured logging format
2. Include relevant context
3. Use appropriate log level
4. Add request_id for request-related logs

### Testing Monitoring
1. Run test script: `scripts/test_monitoring.py`
2. Verify metrics appear in Prometheus
3. Check Grafana dashboard updates
4. Trigger test alerts
