"""Redis cluster configuration and replication management."""

from typing import List, Dict, Optional
import redis
from redis.cluster import RedisCluster
from redis.sentinel import Sentinel
from redis.exceptions import RedisError

from core.config.settings import settings
from logger import logger


class RedisClusterManager:
    """Manages Redis cluster configuration and replication."""

    def __init__(self):
        """Initialize cluster manager."""
        self.sentinel = None
        self.cluster = None
        self._initialize_cluster()

    def _initialize_cluster(self):
        """Initialize Redis cluster based on configuration."""
        if settings.REDIS_CLUSTER_MODE:
            # Initialize Redis Cluster
            startup_nodes = [
                {"host": host.strip(), "port": settings.REDIS_PORT}
                for host in settings.REDIS_CLUSTER_NODES.split(",")
            ]
            self.cluster = RedisCluster(
                startup_nodes=startup_nodes,
                decode_responses=True,
                password=(
                    settings.REDIS_PASSWORD.get_secret_value()
                    if settings.REDIS_PASSWORD
                    else None
                ),
                skip_full_coverage_check=True,
                socket_timeout=5.0,
                socket_connect_timeout=2.0,
                retry_on_timeout=True,
            )
        elif settings.REDIS_SENTINEL_MODE:
            # Initialize Redis Sentinel
            sentinel_nodes = [
                (host.strip(), settings.REDIS_SENTINEL_PORT)
                for host in settings.REDIS_SENTINEL_NODES.split(",")
            ]
            self.sentinel = Sentinel(
                sentinel_nodes,
                socket_timeout=5.0,
                password=(
                    settings.REDIS_PASSWORD.get_secret_value()
                    if settings.REDIS_PASSWORD
                    else None
                ),
                sentinel_kwargs={
                    "password": (
                        settings.REDIS_SENTINEL_PASSWORD.get_secret_value()
                        if settings.REDIS_SENTINEL_PASSWORD
                        else None
                    )
                },
            )

    def get_master_for_write(self) -> redis.Redis:
        """Get Redis master instance for write operations."""
        if self.cluster:
            return self.cluster
        elif self.sentinel:
            return self.sentinel.master_for(
                settings.REDIS_MASTER_GROUP,
                socket_timeout=5.0,
                password=(
                    settings.REDIS_PASSWORD.get_secret_value()
                    if settings.REDIS_PASSWORD
                    else None
                ),
            )
        raise RedisError("No cluster or sentinel configuration available")

    def get_slave_for_read(self) -> redis.Redis:
        """Get Redis slave instance for read operations."""
        if self.cluster:
            return self.cluster
        elif self.sentinel:
            return self.sentinel.slave_for(
                settings.REDIS_MASTER_GROUP,
                socket_timeout=5.0,
                password=(
                    settings.REDIS_PASSWORD.get_secret_value()
                    if settings.REDIS_PASSWORD
                    else None
                ),
            )
        raise RedisError("No cluster or sentinel configuration available")

    def check_cluster_health(self) -> Dict[str, bool]:
        """Check health of cluster nodes."""
        health = {"status": True, "details": {}}
        try:
            if self.cluster:
                nodes = self.cluster.cluster_nodes()
                for node in nodes:
                    health["details"][f"{node['host']}:{node['port']}"] = node[
                        "connected"
                    ]
            elif self.sentinel:
                master = self.sentinel.discover_master(settings.REDIS_MASTER_GROUP)
                slaves = self.sentinel.discover_slaves(settings.REDIS_MASTER_GROUP)
                health["details"]["master"] = bool(master)
                health["details"]["slaves"] = len(slaves)
        except RedisError as e:
            logger.error(f"Error checking cluster health: {e}")
            health["status"] = False
        return health


# Global instance
redis_cluster = RedisClusterManager()
