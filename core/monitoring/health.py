"""System health monitoring module."""

import os
import psutil
import time
from typing import Dict, Any, List
from datetime import datetime

from core.cache import redis_cache
from core.database.session import async_session_maker
from sqlalchemy import text
from logger import logger


class SystemHealthCheck:
    """System health monitoring implementation."""

    @staticmethod
    async def check_database() -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            async with async_session_maker() as session:
                # Check connection and basic query performance
                result = await session.execute(text("SELECT 1"))
                await result.scalar()

                # Get database stats
                result = await session.execute(
                    text(
                        """
                        SELECT 
                            sum(n_live_tup) as row_count,
                            pg_size_pretty(pg_database_size(current_database())) as db_size,
                            (SELECT count(*) FROM pg_stat_activity) as connections
                        FROM pg_stat_user_tables;
                    """
                    )
                )
                stats = result.mappings().first()

            response_time = (time.time() - start_time) * 1000  # Convert to ms

            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "stats": dict(stats) if stats else {},
                "connection_pool": {
                    "size": async_session_maker.pool.size(),
                    "overflow": async_session_maker.pool.overflow(),
                    "timeout": async_session_maker.pool.timeout(),
                },
            }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}

    @staticmethod
    def check_system() -> Dict[str, Any]:
        """Check system resources and performance."""
        try:
            cpu_count = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "status": "healthy",
                "cpu": {
                    "cores": cpu_count,
                    "usage_percent": cpu_percent,
                    "per_cpu_percent": psutil.cpu_percent(interval=1, percpu=True),
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent,
                },
                "process": {
                    "pid": os.getpid(),
                    "memory_percent": psutil.Process().memory_percent(),
                    "cpu_percent": psutil.Process().cpu_percent(),
                },
            }
        except Exception as e:
            logger.error(f"System health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}

    @staticmethod
    def check_redis() -> Dict[str, Any]:
        """Check Redis health and performance."""
        return redis_cache._health_check()

    @classmethod
    async def get_full_health_status(cls) -> Dict[str, Any]:
        """Get comprehensive health status of all systems."""
        db_health = await cls.check_database()
        redis_health = cls.check_redis()
        system_health = cls.check_system()

        # Determine overall status
        services_status = {
            "database": db_health["status"],
            "redis": redis_health["status"],
            "system": system_health["status"],
        }

        if all(status == "healthy" for status in services_status.values()):
            overall_status = "healthy"
        elif any(status == "unhealthy" for status in services_status.values()):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": overall_status,
            "services": {
                "database": db_health,
                "redis": redis_health,
                "system": system_health,
            },
        }

    @classmethod
    def get_system_metrics(cls) -> Dict[str, float]:
        """Get key system metrics for monitoring."""
        try:
            system = cls.check_system()

            return {
                "cpu_usage": system["cpu"]["usage_percent"],
                "memory_usage": system["memory"]["percent"],
                "disk_usage": system["disk"]["percent"],
                "process_cpu": system["process"]["cpu_percent"],
                "process_memory": system["process"]["memory_percent"],
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {str(e)}")
            return {}
