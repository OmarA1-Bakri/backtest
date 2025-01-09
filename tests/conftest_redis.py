"""Redis test configuration."""

import pytest
from unittest.mock import patch
from core.cache import RedisCache, RedisConnectionManager


@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings for Redis tests."""
    with patch("core.config.settings.settings") as mock_settings:
        mock_settings.redis.host = "localhost"
        mock_settings.redis.port = 6379
        mock_settings.redis.db = 0
        mock_settings.redis.password = None
        yield mock_settings


@pytest.fixture(autouse=True)
def clear_redis_pool():
    """Clear Redis connection pool after each test."""
    yield
    RedisConnectionManager.clear_pool()


@pytest.fixture
def redis_cache():
    """Provide a Redis cache instance for tests."""
    cache = RedisCache()
    yield cache
    cache.close()
