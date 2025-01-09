"""Integration tests for Redis cache system."""

import asyncio
import time
from datetime import datetime
from typing import Optional
import pytest
from pydantic import BaseModel

from core.cache import redis_cache
from core.cache_decorators import memoize, invalidate_cache
from core.cache_warmer import cache_warmer, eviction_policy
from core.cache_monitor import cache_monitor


class TestUser(BaseModel):
    """Test user model."""

    id: int
    name: str
    email: str
    created_at: datetime


@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for each test."""
    # Clear cache before each test
    redis_cache.redis.flushdb()
    yield
    # Clean up after each test
    redis_cache.redis.flushdb()


def test_basic_operations():
    """Test basic cache operations."""
    # Set and get
    assert redis_cache.set("test:key", "value")
    assert redis_cache.get("test:key") == "value"

    # Expiration
    assert redis_cache.set("test:ex", "value", ex=1)
    assert redis_cache.get("test:ex") == "value"
    time.sleep(1.1)
    assert redis_cache.get("test:ex") is None

    # Delete
    assert redis_cache.delete("test:key")
    assert redis_cache.get("test:key") is None

    # Exists
    assert redis_cache.exists("test:key") is False


def test_model_serialization():
    """Test model serialization and deserialization."""
    user = TestUser(
        id=1, name="Test User", email="test@example.com", created_at=datetime.utcnow()
    )

    # Set and get with model
    assert redis_cache.set("user:1", user)
    cached_user = redis_cache.get("user:1", model_type=TestUser)
    assert isinstance(cached_user, TestUser)
    assert cached_user.id == user.id
    assert cached_user.name == user.name
    assert cached_user.email == user.email
    assert cached_user.created_at == user.created_at


def test_list_operations():
    """Test Redis list operations."""
    # Push and pop
    assert redis_cache.lpush("test:list", 1, 2, 3) == 3
    assert redis_cache.rpush("test:list", 4, 5) == 5

    # Range
    values = redis_cache.lrange("test:list", 0, -1)
    assert values == [3, 2, 1, 4, 5]

    # Pop
    assert redis_cache.lpop("test:list") == 3
    assert redis_cache.rpop("test:list") == 5


def test_hash_operations():
    """Test Redis hash operations."""
    # Set hash fields
    assert redis_cache.hset("test:hash", "field1", "value1")
    assert redis_cache.hset("test:hash", "field2", "value2")

    # Get hash fields
    assert redis_cache.hget("test:hash", "field1") == "value1"
    assert redis_cache.hget("test:hash", "field2") == "value2"


def test_pipeline_operations():
    """Test Redis pipeline operations."""
    with redis_cache.pipeline() as pipe:
        pipe.set("key1", "value1")
        pipe.set("key2", "value2")
        pipe.get("key1")
        pipe.get("key2")
        results = pipe.execute()

    assert results == [True, True, "value1", "value2"]


@memoize(ttl=60)
def expensive_function(x: int) -> int:
    """Test function for cache decorator."""
    time.sleep(0.1)  # Simulate expensive operation
    return x * 2


def test_cache_decorator():
    """Test cache decorator functionality."""
    # First call should be slow
    start = time.time()
    result1 = expensive_function(5)
    duration1 = time.time() - start

    # Second call should be fast (cached)
    start = time.time()
    result2 = expensive_function(5)
    duration2 = time.time() - start

    assert result1 == result2 == 10
    assert duration1 > 0.1  # Original call takes time
    assert duration2 < 0.01  # Cached call is fast

    # Invalidate cache
    invalidate_cache(expensive_function, 5)

    # Third call should be slow again
    start = time.time()
    result3 = expensive_function(5)
    duration3 = time.time() - start

    assert result3 == 10
    assert duration3 > 0.1


def test_cache_warmer():
    """Test cache warming functionality."""
    # Register function for warming
    cache_warmer.register_warm_function(expensive_function, 5)

    # Initial warm
    results = cache_warmer.warm_now()
    assert len(results) == 1
    assert all(results.values())

    # Function should now be cached
    start = time.time()
    result = expensive_function(5)
    duration = time.time() - start
    assert duration < 0.01


def test_eviction_policy():
    """Test cache eviction policy."""
    # Configure strict limits
    eviction_policy.configure(
        max_memory_bytes=1024 * 1024, max_keys=10, min_ttl=1, max_ttl=5  # 1MB
    )

    # Add test data
    for i in range(15):  # Exceeds max_keys
        redis_cache.set(f"test:key:{i}", "x" * 1000)

    # Enforce policy
    stats = eviction_policy.enforce()
    assert stats["expired_keys"] > 0

    # Check remaining keys
    keys = redis_cache.redis.keys("test:key:*")
    assert len(keys) <= 10


def test_cache_monitor():
    """Test cache monitoring functionality."""
    # Start monitor
    cache_monitor.start(interval=1)

    # Add test data
    for i in range(10):
        redis_cache.set(f"test:key:{i}", f"value:{i}")

    # Get metrics
    time.sleep(1)  # Wait for monitor cycle
    metrics = cache_monitor.get_metrics()

    assert "memory" in metrics
    assert "operations" in metrics
    assert "keys" in metrics
    assert metrics["keys"]["total"] >= 10

    # Stop monitor
    cache_monitor.stop()


@pytest.mark.benchmark
def test_cache_performance(benchmark):
    """Benchmark cache performance."""

    def bench_operation():
        # Set operation
        redis_cache.set("bench:key", "value")
        # Get operation
        value = redis_cache.get("bench:key")
        # Delete operation
        redis_cache.delete("bench:key")
        return value

    # Run benchmark
    result = benchmark(bench_operation)
    assert result == "value"


@pytest.mark.benchmark
def test_pipeline_performance(benchmark):
    """Benchmark pipeline performance."""

    def bench_pipeline():
        with redis_cache.pipeline() as pipe:
            for i in range(100):
                pipe.set(f"bench:key:{i}", f"value:{i}")
            return pipe.execute()

    # Run benchmark
    results = benchmark(bench_pipeline)
    assert len(results) == 100
    assert all(results)
