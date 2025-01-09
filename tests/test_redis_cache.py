"""Test suite for Redis cache implementation."""

import pytest
import json
import time
from unittest.mock import patch, MagicMock
from redis.exceptions import ConnectionError, TimeoutError
from core.cache import RedisCache, RedisConnectionManager, redis_cache
from core.config.settings import settings


@pytest.fixture
def mock_redis():
    """Fixture for mocked Redis instance."""
    with patch("redis.Redis") as mock:
        mock.return_value.ping.return_value = True
        yield mock


@pytest.fixture
def test_redis_cache(mock_redis):
    """Fixture for test Redis cache instance."""
    cache = RedisCache()
    yield cache
    cache.close()


class TestRedisConnectionManager:
    """Test Redis connection pool management."""

    def test_get_pool_singleton(self):
        """Test that get_pool returns the same pool instance."""
        pool1 = RedisConnectionManager.get_pool()
        pool2 = RedisConnectionManager.get_pool()
        assert pool1 is pool2

    def test_pool_configuration(self):
        """Test pool configuration parameters."""
        pool = RedisConnectionManager.get_pool()
        assert pool.connection_kwargs["host"] == settings.redis.REDIS_HOST
        assert pool.connection_kwargs["port"] == settings.redis.REDIS_PORT
        assert pool.connection_kwargs["db"] == settings.redis.REDIS_DB
        assert pool.connection_kwargs["retry_on_timeout"] is True

    def test_clear_pool(self):
        """Test pool clearing functionality."""
        pool = RedisConnectionManager.get_pool()
        RedisConnectionManager.clear_pool()
        assert RedisConnectionManager._pool is None
        new_pool = RedisConnectionManager.get_pool()
        assert pool is not new_pool


class TestRedisCache:
    """Test Redis cache functionality."""

    def test_health_check_success(self, test_redis_cache, mock_redis):
        """Test successful health check."""
        assert test_redis_cache._health_check() is True

    def test_health_check_failure(self, test_redis_cache, mock_redis):
        """Test health check failure."""
        mock_redis.return_value.ping.side_effect = ConnectionError("Connection failed")
        with pytest.raises(ConnectionError):
            test_redis_cache._health_check()

    @pytest.mark.parametrize(
        "test_data",
        [
            {"key": "test_str", "value": "test_value"},
            {"key": "test_int", "value": 42},
            {"key": "test_dict", "value": {"nested": "value"}},
            {"key": "test_list", "value": [1, 2, 3]},
        ],
    )
    def test_set_get_operations(self, test_redis_cache, mock_redis, test_data):
        """Test set and get operations with different data types."""
        key, value = test_data["key"], test_data["value"]

        # Mock successful set operation
        mock_redis.return_value.set.return_value = True
        mock_redis.return_value.get.return_value = json.dumps(value)

        # Test set operation
        assert test_redis_cache.set(key, value) is True
        mock_redis.return_value.set.assert_called_with(
            key, json.dumps(value), ex=None, nx=False, xx=False
        )

        # Test get operation
        assert test_redis_cache.get(key) == value
        mock_redis.return_value.get.assert_called_with(key)

    def test_set_with_expiry(self, test_redis_cache, mock_redis):
        """Test set operation with expiration."""
        mock_redis.return_value.set.return_value = True
        assert test_redis_cache.set("test_key", "test_value", ex=60) is True
        mock_redis.return_value.set.assert_called_with(
            "test_key", '"test_value"', ex=60, nx=False, xx=False
        )

    def test_delete_single(self, test_redis_cache, mock_redis):
        """Test delete operation for single key."""
        mock_redis.return_value.delete.return_value = 1
        assert test_redis_cache.delete("test_key") == 1
        mock_redis.return_value.delete.assert_called_with("test_key")

    def test_delete_multiple(self, test_redis_cache, mock_redis):
        """Test delete operation for multiple keys."""
        mock_redis.return_value.delete.return_value = 2
        assert test_redis_cache.delete(["key1", "key2"]) == 2
        mock_redis.return_value.delete.assert_called_with("key1", "key2")

    def test_exists(self, test_redis_cache, mock_redis):
        """Test exists operation."""
        mock_redis.return_value.exists.return_value = 1
        assert test_redis_cache.exists("test_key") == 1
        mock_redis.return_value.exists.assert_called_with("test_key")

    def test_incr(self, test_redis_cache, mock_redis):
        """Test increment operation."""
        mock_redis.return_value.incr.return_value = 1
        mock_redis.return_value.incrby.return_value = 5

        assert test_redis_cache.incr("test_key") == 1
        assert test_redis_cache.incr("test_key", 5) == 5

    @pytest.mark.parametrize(
        "exception,expected",
        [
            (ConnectionError("Connection failed"), None),
            (TimeoutError("Timeout"), None),
            (Exception("Unknown error"), None),
        ],
    )
    def test_error_handling(self, test_redis_cache, mock_redis, exception, expected):
        """Test error handling for various exceptions."""
        mock_redis.return_value.get.side_effect = exception
        assert test_redis_cache.get("test_key") == expected


@pytest.mark.integration
class TestRedisIntegration:
    """Integration tests for Redis cache."""

    @pytest.fixture
    def live_redis_cache(self):
        """Fixture for live Redis cache instance."""
        cache = RedisCache()
        yield cache
        # Cleanup
        cache.delete("test_key")
        cache.close()

    def test_live_connection(self, live_redis_cache):
        """Test live Redis connection."""
        assert live_redis_cache._health_check() is True

    def test_live_operations(self, live_redis_cache):
        """Test live Redis operations."""
        # Test set and get
        assert live_redis_cache.set("test_key", "test_value") is True
        assert live_redis_cache.get("test_key") == "test_value"

        # Test exists
        assert live_redis_cache.exists("test_key") == 1

        # Test delete
        assert live_redis_cache.delete("test_key") == 1
        assert live_redis_cache.get("test_key") is None

    def test_live_connection_pool(self, live_redis_cache):
        """Test connection pool behavior."""
        pool = live_redis_cache.redis.connection_pool

        # Create multiple operations to test pool
        for i in range(5):
            live_redis_cache.set(f"test_key_{i}", f"value_{i}")

        # Clean up
        live_redis_cache.delete([f"test_key_{i}" for i in range(5)])


class TestRedisResilience:
    """Test Redis resilience and recovery capabilities."""

    def test_retry_mechanism(self, test_redis_cache, mock_redis):
        """Test retry mechanism for failed operations."""
        # Configure mock to fail first, then succeed
        mock_redis.return_value.get.side_effect = [
            TimeoutError("Operation timed out"),
            "null",  # Redis returns "null" for None in JSON
        ]

        result = test_redis_cache.get("test_key")
        assert result is None
        assert mock_redis.return_value.get.call_count == 2

    def test_circuit_breaker(self, test_redis_cache, mock_redis):
        """Test circuit breaker behavior."""
        # Mock consecutive failures
        mock_redis.return_value.ping.side_effect = ConnectionError("Connection failed")

        with pytest.raises(ConnectionError):
            test_redis_cache._health_check()

        # Verify pool was cleared
        assert RedisConnectionManager._pool is None

    @pytest.mark.parametrize("operation", ["get", "set", "delete", "exists", "incr"])
    def test_operation_timeout(self, test_redis_cache, mock_redis, operation):
        """Test timeout handling for different operations."""
        mock_method = getattr(mock_redis.return_value, operation)
        mock_method.side_effect = TimeoutError("Operation timed out")

        if operation == "set":
            result = test_redis_cache.set("key", "value")
            assert result is False
        elif operation == "incr":
            result = test_redis_cache.incr("key")
            assert result is None
        elif operation in ["delete", "exists"]:
            result = getattr(test_redis_cache, operation)("key")
            assert result == 0
        else:
            result = getattr(test_redis_cache, operation)("key")
            assert result is None
