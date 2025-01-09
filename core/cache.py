"""Redis cache module with connection pooling and retry mechanism."""

import json
from typing import Any, Dict, Optional, Type, TypeVar, Union, List
import redis
from redis.connection import ConnectionPool
from redis.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, TimeoutError, RedisError

from core.config.settings import settings
from core.serialization import JsonSerializer
from logger import logger
from core.cache_cluster import redis_cluster

T = TypeVar("T")


class RedisConnectionManager:
    """Manages Redis connection pool and provides connection health checks."""

    _pool: Optional[ConnectionPool] = None

    @classmethod
    def get_pool(cls) -> ConnectionPool:
        """Get or create Redis connection pool."""
        if cls._pool is None:
            cls._pool = ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=(
                    settings.REDIS_PASSWORD.get_secret_value()
                    if settings.REDIS_PASSWORD
                    else None
                ),
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=2.0,
                retry_on_timeout=True,
            )
        return cls._pool

    @classmethod
    def clear_pool(cls):
        """Clear the connection pool."""
        if cls._pool is not None:
            cls._pool.disconnect()
            cls._pool = None


class RedisCache:
    """Redis cache implementation with connection pooling and retry mechanism.

    Usage patterns:
    1. Simple key-value storage:
        cache.set("key", value)
        value = cache.get("key")

    2. Caching with expiration:
        cache.set("key", value, ex=3600)  # Expires in 1 hour

    3. Caching complex objects:
        user = User(id=1, name="John")
        cache.set("user:1", user)
        user = cache.get("user:1", model_type=User)

    4. Atomic operations:
        cache.set("key", value, nx=True)  # Set only if key doesn't exist
        cache.set("key", value, xx=True)  # Set only if key exists

    5. Pattern-based operations:
        cache.delete_pattern("user:*")  # Delete all user-related keys

    Key naming conventions:
    - Use colon (:) as namespace separator
    - Use descriptive prefixes for different types of data
    - Examples:
        - user:{id} - User data
        - session:{id} - Session data
        - backtest:{id}:results - Backtest results
        - strategy:{id}:params - Strategy parameters
    """

    def __init__(self):
        """Initialize Redis cache with retry mechanism."""
        self.serializer = JsonSerializer()
        self.retry = Retry(ExponentialBackoff(), 3)
        self._redis = None
        self._read_redis = None

    @property
    def redis(self) -> "redis.Redis":
        """Get Redis client for write operations."""
        if settings.REDIS_CLUSTER_MODE or settings.REDIS_SENTINEL_MODE:
            return redis_cluster.get_master_for_write()
        if self._redis is None:
            self._redis = redis.Redis(
                connection_pool=RedisConnectionManager.get_pool(),
                retry=self.retry,
            )
        return self._redis

    @property
    def read_redis(self) -> "redis.Redis":
        """Get Redis client for read operations (may be replica in distributed setup)."""
        if settings.REDIS_CLUSTER_MODE or settings.REDIS_SENTINEL_MODE:
            return redis_cluster.get_slave_for_read()
        return self.redis  # In non-distributed mode, use same client for reads

    def pipeline(self) -> "RedisPipeline":
        """Create a new pipeline for atomic operations."""
        return RedisPipeline(self.redis.pipeline(), self.serializer)

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        try:
            value = self.read_redis.get(key)
            return self.serializer.deserialize(value) if value is not None else default
        except RedisError as e:
            logger.error(f"Error getting key {key} from cache: {e}")
            return default

    def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """Set value in cache."""
        try:
            serialized = self.serializer.serialize(value)
            return bool(self.redis.set(key, serialized, ex=ex, nx=nx, xx=xx))
        except RedisError as e:
            logger.error(f"Error setting key {key} in cache: {e}")
            return False

    def delete(self, keys: Union[str, List[str]]) -> int:
        """Delete key(s) from cache.

        Args:
            keys: Single key or list of keys to delete

        Returns:
            Number of keys deleted
        """
        try:
            if isinstance(keys, list):
                return self.redis.delete(*keys)
            return bool(self.redis.delete(keys))
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection error in delete(): {str(e)}")
            return 0
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return 0

    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern.

        Args:
            pattern: Pattern to match (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection error in delete_pattern(): {str(e)}")
            return 0
        except Exception as e:
            logger.error(f"Cache delete_pattern error: {str(e)}")
            return 0

    def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists
        """
        try:
            return bool(self.redis.exists(key))
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection error in exists(): {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Cache exists error: {str(e)}")
            return False

    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment value by amount.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value after increment or None on error
        """
        try:
            if amount == 1:
                return self.redis.incr(key)
            return self.redis.incrby(key, amount)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection error in incr(): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Cache incr error: {str(e)}")
            return None

    def decr(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement value by given amount.

        Args:
            key: Cache key
            amount: Amount to decrement by (default: 1)

        Returns:
            New value after decrement or None if operation failed
        """
        try:
            return self.redis.decr(key, amount)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection error in decr(): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Cache decr error: {str(e)}")
            return None

    def lpush(self, key: str, *values: Any) -> Optional[int]:
        """Push values to the head of a list.

        Args:
            key: List key
            values: One or more values to push

        Returns:
            Length of list after push or None if operation failed
        """
        try:
            serialized = [self.serializer.serialize(v) for v in values]
            return self.redis.lpush(key, *serialized)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection error in lpush(): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Cache lpush error: {str(e)}")
            return None

    def rpush(self, key: str, *values: Any) -> Optional[int]:
        """Push values to the tail of a list.

        Args:
            key: List key
            values: One or more values to push

        Returns:
            Length of list after push or None if operation failed
        """
        try:
            serialized = [self.serializer.serialize(v) for v in values]
            return self.redis.rpush(key, *serialized)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection error in rpush(): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Cache rpush error: {str(e)}")
            return None

    def lpop(
        self, key: str, model_type: Optional[Type[T]] = None
    ) -> Optional[Union[Any, T]]:
        """Pop value from the head of a list.

        Args:
            key: List key
            model_type: Optional model type for deserialization

        Returns:
            Popped value or None if list is empty or operation failed
        """
        try:
            value = self.redis.lpop(key)
            if value is not None:
                return self.serializer.deserialize(value, model_type)
            return None
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection error in lpop(): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Cache lpop error: {str(e)}")
            return None

    def rpop(
        self, key: str, model_type: Optional[Type[T]] = None
    ) -> Optional[Union[Any, T]]:
        """Pop value from the tail of a list.

        Args:
            key: List key
            model_type: Optional model type for deserialization

        Returns:
            Popped value or None if list is empty or operation failed
        """
        try:
            value = self.redis.rpop(key)
            if value is not None:
                return self.serializer.deserialize(value, model_type)
            return None
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection error in rpop(): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Cache rpop error: {str(e)}")
            return None

    def lrange(
        self, key: str, start: int, end: int, model_type: Optional[Type[T]] = None
    ) -> Optional[list[Union[Any, T]]]:
        """Get range of values from list.

        Args:
            key: List key
            start: Start index
            end: End index
            model_type: Optional model type for deserialization

        Returns:
            List of values or None if operation failed
        """
        try:
            values = self.redis.lrange(key, start, end)
            if values:
                return [self.serializer.deserialize(v, model_type) for v in values]
            return []
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection error in lrange(): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Cache lrange error: {str(e)}")
            return None

    def hset(self, key: str, field: str, value: Any) -> bool:
        """Set hash field to value.

        Args:
            key: Hash key
            field: Hash field
            value: Value to set

        Returns:
            True if field was new and set successfully
        """
        try:
            serialized = self.serializer.serialize(value)
            return bool(self.redis.hset(key, field, serialized))
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection error in hset(): {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Cache hset error: {str(e)}")
            return False

    def hget(
        self, key: str, field: str, model_type: Optional[Type[T]] = None
    ) -> Optional[Union[Any, T]]:
        """Get value of hash field.

        Args:
            key: Hash key
            field: Hash field
            model_type: Optional model type for deserialization

        Returns:
            Field value or None if field doesn't exist or operation failed
        """
        try:
            value = self.redis.hget(key, field)
            if value is not None:
                return self.serializer.deserialize(value, model_type)
            return None
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection error in hget(): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Cache hget error: {str(e)}")
            return None

    def check_health(self) -> Dict[str, bool]:
        """Check health of Redis connection and cluster if enabled."""
        health = {"status": True, "connection": True, "replication": True}
        try:
            # Check basic connection
            self.redis.ping()

            # Check cluster health if enabled
            if settings.REDIS_CLUSTER_MODE or settings.REDIS_SENTINEL_MODE:
                cluster_health = redis_cluster.check_cluster_health()
                health.update(cluster_health)
        except RedisError as e:
            logger.error(f"Redis health check failed: {e}")
            health["status"] = False
            health["connection"] = False
        return health

    def close(self):
        """Close Redis connection and clear pool."""
        try:
            self.redis.close()
            RedisConnectionManager.clear_pool()
        except Exception as e:
            logger.error(f"Error closing Redis connection: {str(e)}")


class RedisPipeline:
    """Pipeline for executing multiple Redis commands atomically."""

    def __init__(self, pipeline: redis.client.Pipeline, serializer: JsonSerializer):
        self.pipeline = pipeline
        self.serializer = serializer

    def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ):
        """Add set command to pipeline."""
        serialized = self.serializer.serialize(value)
        self.pipeline.set(key, serialized, ex=ex, nx=nx, xx=xx)
        return self

    def get(self, key: str):
        """Add get command to pipeline."""
        self.pipeline.get(key)
        return self

    def delete(self, key: str):
        """Add delete command to pipeline."""
        self.pipeline.delete(key)
        return self

    def execute(self) -> list[Any]:
        """Execute pipeline commands."""
        try:
            results = self.pipeline.execute()
            # Decode any string values
            decoded = []
            for result in results:
                if isinstance(result, bytes):
                    result = result.decode("utf-8")
                if (
                    isinstance(result, str)
                    and result.startswith('"')
                    and result.endswith('"')
                ):
                    result = result[1:-1]  # Remove quotes
                decoded.append(result)
            return decoded
        except Exception as e:
            logger.error(f"Pipeline execute error: {str(e)}")
            return []

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if exc_type is None:
            self.execute()
        return False  # Don't suppress exceptions


# Global instance
redis_cache = RedisCache()
