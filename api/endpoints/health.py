"""Health check endpoints."""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.monitoring.health import SystemHealthCheck
from core.monitoring.performance import performance_monitor
from logger import logger

router = APIRouter()


class ServiceStatus(BaseModel):
    """Service status model."""

    status: str
    details: Dict[str, Any] | None = None


class HealthResponse(BaseModel):
    """Health check response model."""

    timestamp: str
    status: str
    services: Dict[str, ServiceStatus]


class PerformanceMetrics(BaseModel):
    """Performance metrics model."""

    operation: str
    metrics: List[Dict[str, Any]]
    summary: Dict[str, Any]


class SlowOperation(BaseModel):
    """Slow operation model."""

    operation: str
    avg_duration_ms: float
    count: int
    recent_metrics: List[Dict[str, Any]]


class SlowOperationsResponse(BaseModel):
    """Slow operations response model."""

    threshold_ms: float
    operations: List[SlowOperation]


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check comprehensive system health status."""
    try:
        health_status = await SystemHealthCheck.get_full_health_status()
        return HealthResponse(**health_status)
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            timestamp=datetime.utcnow().isoformat(),
            status="error",
            services={
                "error": ServiceStatus(status="error", details={"error": str(e)})
            },
        )


@router.get("/health/system", response_model=ServiceStatus)
async def system_health() -> ServiceStatus:
    """Check system health including CPU, memory, and disk usage."""
    try:
        system_status = SystemHealthCheck.check_system()
        return ServiceStatus(status=system_status["status"], details=system_status)
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        return ServiceStatus(status="error", details={"error": str(e)})


@router.get("/health/database", response_model=ServiceStatus)
async def database_health() -> ServiceStatus:
    """Check database health and performance."""
    try:
        db_status = await SystemHealthCheck.check_database()
        return ServiceStatus(status=db_status["status"], details=db_status)
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return ServiceStatus(status="error", details={"error": str(e)})


@router.get("/health/redis", response_model=ServiceStatus)
async def redis_health() -> ServiceStatus:
    """Check Redis health and performance."""
    try:
        redis_status = SystemHealthCheck.check_redis()
        return ServiceStatus(status=redis_status["status"], details=redis_status)
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return ServiceStatus(status="error", details={"error": str(e)})


@router.get("/performance/{operation}", response_model=PerformanceMetrics)
async def operation_performance(
    operation: str, limit: int = Query(default=100, ge=1, le=1000)
) -> PerformanceMetrics:
    """Get performance metrics for a specific operation."""
    try:
        metrics = await performance_monitor.get_operation_metrics(operation, limit)
        return PerformanceMetrics(**metrics)
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {str(e)}")
        return PerformanceMetrics(
            operation=operation, metrics=[], summary={"error": str(e)}
        )


@router.get("/performance/slow", response_model=SlowOperationsResponse)
async def slow_operations(
    threshold_ms: Optional[float] = Query(default=None, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
) -> SlowOperationsResponse:
    """Get list of slow operations exceeding threshold."""
    try:
        slow_ops = await performance_monitor.get_slow_operations(threshold_ms, limit)
        return SlowOperationsResponse(**slow_ops)
    except Exception as e:
        logger.error(f"Failed to get slow operations: {str(e)}")
        return SlowOperationsResponse(
            threshold_ms=threshold_ms or performance_monitor.slow_threshold_ms,
            operations=[],
        )
