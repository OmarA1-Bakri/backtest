# Redis Usage Guide

## Overview

This document outlines the Redis caching strategy and usage patterns for the BackTest AI application.

## Key Features

- Connection pooling with automatic retry mechanism
- JSON serialization with support for complex Python types
- Health monitoring and metrics
- Pattern-based key operations
- Type-safe deserialization with Pydantic models

## Key Naming Conventions

We use a hierarchical naming structure with colons (:) as namespace separators:

```
<namespace>:<entity>:<id>:<attribute>
```

Common namespaces:
- `user`: User-related data
- `session`: Session data
- `backtest`: Backtest data
- `strategy`: Strategy data
- `metrics`: Performance metrics

Examples:
```
user:123:profile
session:abc:token
backtest:456:results
strategy:789:parameters
metrics:backtest:456:daily
```

## Usage Patterns

### 1. Simple Key-Value Storage

```python
from core.cache import redis_cache

# Set value
redis_cache.set("key", "value")

# Get value
value = redis_cache.get("key")
```

### 2. Caching with Expiration

```python
# Cache for 1 hour
redis_cache.set("session:123", session_data, ex=3600)
```

### 3. Caching Complex Objects

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str

# Store user
user = User(id=1, name="John", email="john@example.com")
redis_cache.set(f"user:{user.id}", user)

# Retrieve user with type safety
user = redis_cache.get(f"user:1", model_type=User)
```

### 4. Atomic Operations

```python
# Set only if key doesn't exist
success = redis_cache.set("lock:resource", "locked", nx=True)

# Set only if key exists
success = redis_cache.set("counter", 0, xx=True)
```

### 5. Pattern-Based Operations

```python
# Delete all user session data
redis_cache.delete_pattern("session:user:123:*")
```

## Best Practices

1. **Key Expiration**
   - Always set expiration for session data
   - Consider expiration for cache data that becomes stale
   - Use reasonable expiration times based on data volatility

2. **Error Handling**
   - Cache operations are designed to fail gracefully
   - Check return values for success/failure
   - Log errors are automatically handled

3. **Memory Management**
   - Monitor memory usage via health checks
   - Use pattern-based deletion for cleanup
   - Implement periodic cleanup for stale data

4. **Type Safety**
   - Use Pydantic models for complex data structures
   - Specify model_type when retrieving complex objects
   - Validate data before caching

## Common Use Cases

### Session Management

```python
# Store session
session_data = {"user_id": 123, "permissions": ["read", "write"]}
redis_cache.set(f"session:{session_id}", session_data, ex=3600)

# Retrieve session
session = redis_cache.get(f"session:{session_id}")
```

### Caching Backtest Results

```python
# Store results
results = {"metrics": {...}, "trades": [...]}
redis_cache.set(f"backtest:{backtest_id}:results", results)

# Retrieve results
results = redis_cache.get(f"backtest:{backtest_id}:results")
```

### Rate Limiting

```python
# Increment counter
key = f"ratelimit:user:{user_id}:{timestamp}"
redis_cache.set(key, 1, ex=60, nx=True)  # Expire in 60 seconds
```

## Health Monitoring

The Redis cache includes built-in health monitoring accessible via the `/health/redis` endpoint:

```python
# Get detailed health metrics
health = redis_cache._health_check()
```

Health metrics include:
- Connection status
- Memory usage
- Connected clients
- Uptime
- Connection pool statistics

## Performance Considerations

1. **Serialization**
   - Complex objects are automatically serialized to JSON
   - Consider data size when caching large objects
   - Use compression for large datasets if needed

2. **Connection Pool**
   - Connections are automatically managed
   - Pool size is configurable via settings
   - Monitor pool usage via health checks

3. **Retry Mechanism**
   - Automatic retry with exponential backoff
   - Configurable retry attempts
   - Graceful failure handling

## Security

1. **Authentication**
   - Redis password is configured via environment variables
   - TLS support available if needed
   - Connection timeout limits

2. **Data Protection**
   - Sensitive data should be encrypted before caching
   - Use appropriate expiration times
   - Implement access controls at application level

## Monitoring and Maintenance

1. **Health Checks**
   - Regular connection health monitoring
   - Memory usage tracking
   - Client connection monitoring

2. **Cleanup**
   - Implement periodic cleanup jobs
   - Use pattern-based deletion
   - Monitor key space usage

3. **Logging**
   - All errors are automatically logged
   - Monitor for connection issues
   - Track cache hit/miss rates
