# Redis Cache System Documentation

## Overview

The Redis cache system provides a robust, efficient, and feature-rich caching solution for the BackTest AI platform. It includes:

- Comprehensive data type support (strings, lists, hashes)
- Automatic function result caching
- Cache warming and eviction strategies
- Real-time monitoring and metrics
- Pipeline support for batch operations

## Basic Usage

### Simple Key-Value Operations

```python
from core.cache import redis_cache

# Set a value
redis_cache.set("user:123", user_data, ex=3600)  # Expires in 1 hour

# Get a value
user = redis_cache.get("user:123", model_type=User)

# Check if key exists
if redis_cache.exists("user:123"):
    # Do something

# Delete a key
redis_cache.delete("user:123")
```

### List Operations

```python
# Push to list
redis_cache.lpush("recent_trades", trade)
redis_cache.rpush("recent_trades", trade)

# Pop from list
trade = redis_cache.lpop("recent_trades")
trade = redis_cache.rpop("recent_trades")

# Get range
trades = redis_cache.lrange("recent_trades", 0, -1)
```

### Hash Operations

```python
# Set hash field
redis_cache.hset("user:123:prefs", "theme", "dark")

# Get hash field
theme = redis_cache.hget("user:123:prefs", "theme")
```

### Pipeline Operations

```python
# Execute multiple commands atomically
with redis_cache.pipeline() as pipe:
    pipe.set("key1", "value1")
    pipe.get("key2")
    pipe.delete("key3")
    results = pipe.execute()
```

## Automatic Function Caching

Use the `@memoize` decorator to automatically cache function results:

```python
from core.cache_decorators import memoize

@memoize(ttl=3600)  # Cache for 1 hour
def get_user_preferences(user_id: int) -> dict:
    # Expensive database query
    return preferences

@memoize(prefix="strategy", model_type=Strategy)
def load_strategy(strategy_id: int) -> Strategy:
    # Load strategy from database
    return strategy
```

### Cache Invalidation

```python
from core.cache_decorators import invalidate_cache

# Invalidate specific function call
invalidate_cache(get_user_preferences, user_id=123)
```

## Cache Warming

The cache warmer helps maintain fresh cache data:

```python
from core.cache_warmer import cache_warmer

# Register function for warming
cache_warmer.register_warm_function(
    get_user_preferences,
    user_id=123
)

# Start background warming
cache_warmer.start(interval=300)  # Every 5 minutes

# Manual warm
results = cache_warmer.warm_now()
```

## Cache Monitoring

Monitor cache health and performance:

```python
from core.cache_monitor import cache_monitor

# Start monitoring
cache_monitor.start(interval=60)  # Every minute

# Watch specific keys
cache_monitor.watch_key("user:123:prefs")

# Get metrics
metrics = cache_monitor.get_metrics()
print(f"Memory used: {metrics['memory']['used_bytes']} bytes")
print(f"Hit rate: {metrics['operations']['hit_rate']}%")
```

## Eviction Policies

Configure cache eviction policies:

```python
from core.cache_warmer import eviction_policy

# Configure limits
eviction_policy.configure(
    max_memory_bytes=1024 * 1024 * 1024,  # 1GB
    max_keys=1000000,  # 1M keys
    min_ttl=60,        # 1 minute
    max_ttl=86400      # 1 day
)

# Enforce policy
stats = eviction_policy.enforce()
```

## Key Naming Conventions

Follow these conventions for cache keys:

- Use colon (:) as namespace separator
- Use descriptive prefixes
- Include ID or unique identifier

Examples:
- `user:{id}` - User data
- `session:{id}` - Session data
- `backtest:{id}:results` - Backtest results
- `strategy:{id}:params` - Strategy parameters

## Distributed Caching and Replication

The cache system supports both Redis Cluster and Sentinel modes for distributed caching and high availability.

### Redis Cluster Mode

Enable and configure Redis Cluster for horizontal scaling:

```python
# In settings
REDIS_CLUSTER_MODE = True
REDIS_CLUSTER_NODES = "node1:6379,node2:6379,node3:6379"

# The cache automatically handles:
# - Data sharding across nodes
# - Node failure detection
# - Automatic resharding
```

### Redis Sentinel Mode

Enable and configure Redis Sentinel for high availability:

```python
# In settings
REDIS_SENTINEL_MODE = True
REDIS_SENTINEL_NODES = "sentinel1:26379,sentinel2:26379"
REDIS_SENTINEL_PASSWORD = "secret"  # Optional
REDIS_MASTER_GROUP = "mymaster"

# The cache automatically handles:
# - Master/slave failover
# - Read from replicas
# - Write to master
```

### Health Monitoring

Monitor cluster and replication health:

```python
from core.cache import redis_cache

# Check overall health
health = redis_cache.check_health()
if not health["status"]:
    print("Cache system unhealthy")
    print(f"Connection status: {health['connection']}")
    print(f"Replication status: {health['replication']}")
    
# Get detailed node status
if "details" in health:
    for node, status in health["details"].items():
        print(f"Node {node}: {'healthy' if status else 'unhealthy'}")
```

### Best Practices for Distributed Setup

1. **Configuration**
   - Use consistent node configurations
   - Set appropriate timeouts
   - Configure memory limits

2. **Data Distribution**
   - Use consistent hashing for key distribution
   - Group related keys with hash tags
   - Monitor key distribution

3. **Failover Handling**
   - Implement retry logic
   - Handle temporary failures gracefully
   - Log failover events

4. **Monitoring**
   - Watch node health
   - Monitor replication lag
   - Track failover events

## Performance Benchmarks

The cache system has been benchmarked with the following results:

### Single Operations
- SET operations: ~0.22ms average
- GET operations: ~0.30ms average
- Maximum latency: <2ms for individual operations

### Pipeline Operations
- Batch size: 100 operations
- Average time per operation: ~0.07ms
- Total batch time: ~7ms

### Performance Guidelines
- Use pipeline operations for bulk data
- Keep data size under 1MB per key
- Monitor operation latency
- Use read replicas for heavy read loads

## Configuration Management

### Environment Variables
```bash
# Redis Connection
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=secret
REDIS_DB=0

# Distributed Setup
REDIS_CLUSTER_MODE=true
REDIS_CLUSTER_NODES=node1:6379,node2:6379
REDIS_SENTINEL_MODE=false
REDIS_SENTINEL_NODES=sentinel1:26379
REDIS_SENTINEL_PASSWORD=secret
REDIS_MASTER_GROUP=mymaster

# Performance
REDIS_POOL_SIZE=10
REDIS_SOCKET_TIMEOUT=2
REDIS_RETRY_ON_TIMEOUT=true
```

### Cache Settings
```python
# In settings.py
CACHE_DEFAULT_TTL = 3600  # 1 hour
CACHE_MAX_MEMORY = "1gb"
CACHE_EVICTION_POLICY = "allkeys-lru"
CACHE_MAX_CONNECTIONS = 10000
```

### Monitoring Settings
```python
# In settings.py
CACHE_MONITOR_INTERVAL = 60  # seconds
CACHE_ALERT_MEMORY_THRESHOLD = 0.8  # 80% memory usage
CACHE_ALERT_HIT_RATE_THRESHOLD = 0.5  # 50% hit rate
CACHE_ALERT_ERROR_THRESHOLD = 0.01  # 1% error rate
```

## Best Practices

1. **Set TTL for All Keys**
   - Always set an expiration time
   - Use reasonable TTL values based on data volatility

2. **Use Appropriate Data Types**
   - Strings for simple values
   - Lists for ordered data
   - Hashes for structured data

3. **Batch Operations**
   - Use pipelines for multiple operations
   - Reduce network roundtrips

4. **Error Handling**
   - Cache errors are non-fatal
   - Always have fallback logic

5. **Monitoring**
   - Watch memory usage
   - Monitor hit/miss rates
   - Set up alerts for issues

## Troubleshooting

Common issues and solutions:

1. **High Memory Usage**
   - Check eviction policy settings
   - Review key TTLs
   - Monitor key count

2. **Low Hit Rate**
   - Verify cache warming setup
   - Check key naming consistency
   - Review TTL values

3. **Slow Operations**
   - Use pipeline for batch operations
   - Check network latency
   - Monitor Redis server load

4. **Connection Issues**
   - Verify Redis server status
   - Check connection pool settings
   - Review network configuration
