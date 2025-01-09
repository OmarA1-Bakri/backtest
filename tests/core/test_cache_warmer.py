"""Tests for cache warmer and eviction policy."""

import time
from unittest.mock import MagicMock, patch

import pytest
from core.cache import redis_cache
from core.cache_decorators import memoize
from core.cache_warmer import cache_warmer, eviction_policy


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    with patch.object(redis_cache, "redis") as mock:
        mock.info.return_value = {
            "used_memory": 1024 * 1024,  # 1MB
            "db0": {"keys": 100},
        }
        mock.keys.return_value = ["key1", "key2", "key3"]
        mock.ttl.return_value = 300
        yield mock


# Sample function for cache warming tests
@memoize(ttl=60)
def cached_function(value: int) -> int:
    """Sample function for testing cache warming."""
    return value * 2


def test_cache_warmer_registration():
    """Test registering functions for cache warming."""
    cache_warmer.register_warm_function(cached_function, 42)
    assert len(cache_warmer._warm_functions) == 1

    # Test registering non-memoized function
    def regular_function():
        pass

    with pytest.raises(ValueError):
        cache_warmer.register_warm_function(regular_function)


def test_cache_warmer_configuration():
    """Test cache warmer configuration."""
    cache_warmer.configure(refresh_interval=600, refresh_threshold=0.3)
    assert cache_warmer._refresh_interval == 600
    assert cache_warmer._refresh_threshold == 0.3


def test_cache_warmer_stats():
    """Test cache warmer statistics."""
    cache_warmer.register_warm_function(cached_function, 42)
    stats_before = cache_warmer.get_stats()
    cache_warmer.warm_now()
    stats_after = cache_warmer.get_stats()

    assert stats_after["total_refreshes"] == stats_before["total_refreshes"] + 1
    assert stats_after["successful_refreshes"] >= stats_before["successful_refreshes"]
    assert stats_after["last_refresh_time"] is not None


def test_eviction_policy_configuration():
    """Test eviction policy configuration."""
    eviction_policy.configure(
        max_memory_bytes=2 * 1024 * 1024,  # 2MB
        max_keys=500,
        min_ttl=120,
        max_ttl=43200,
    )
    assert eviction_policy.max_memory_bytes == 2 * 1024 * 1024
    assert eviction_policy.max_keys == 500
    assert eviction_policy.min_ttl == 120
    assert eviction_policy.max_ttl == 43200


def test_eviction_policy_enforcement(mock_redis):
    """Test eviction policy enforcement."""
    # Configure policy with low limits to trigger evictions
    eviction_policy.configure(
        max_memory_bytes=512 * 1024,  # 512KB
        max_keys=2,
        max_ttl=3600,
    )

    # Test enforcement
    stats = eviction_policy.enforce()
    assert "memory_evictions" in stats  # Should trigger memory eviction
    assert "key_limit_evictions" in stats  # Should trigger key limit eviction

    # Check stats
    policy_stats = eviction_policy.get_stats()
    assert policy_stats["total_evictions"] > 0
    assert policy_stats["memory_evictions"] > 0
    assert policy_stats["key_limit_evictions"] > 0


def test_cache_warmer_background_thread():
    """Test cache warmer background thread."""
    cache_warmer.configure(refresh_interval=1)  # 1 second interval for testing
    cache_warmer.register_warm_function(cached_function, 42)

    # Start warmer
    cache_warmer.start()
    time.sleep(2)  # Wait for at least one refresh

    # Check stats
    stats = cache_warmer.get_stats()
    assert stats["total_refreshes"] > 0
    assert stats["last_refresh_time"] is not None

    # Stop warmer
    cache_warmer.stop()
