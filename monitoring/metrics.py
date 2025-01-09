"""Metrics module for monitoring."""

import time
import functools
import asyncio
from typing import Any, Callable
from prometheus_client import Counter, Gauge, Histogram, Summary

# Define metrics
EXECUTION_TIME = Histogram(
    "backtest_execution_time_seconds",
    "Time spent executing backtests",
    ["function", "status"],
)

RETURNS = Gauge(
    "backtest_returns",
    "Strategy returns",
    ["strategy"],
)

SHARPE_RATIO = Gauge(
    "backtest_sharpe_ratio",
    "Strategy Sharpe ratio",
    ["strategy"],
)

MAX_DRAWDOWN = Gauge(
    "backtest_max_drawdown",
    "Strategy maximum drawdown",
    ["strategy"],
)

TRADES = Counter(
    "backtest_trades_total",
    "Number of trades executed",
    ["strategy", "direction"],
)

VOLUME = Counter(
    "backtest_volume_total",
    "Total trading volume",
    ["strategy"],
)

ERROR_COUNTER = Counter(
    "backtest_errors_total",
    "Number of errors encountered",
    ["function", "error_type"],
)

# Request metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

ACTIVE_REQUESTS = Gauge(
    "http_requests_active",
    "Number of active HTTP requests",
    ["method", "endpoint"],
)

# Database metrics
DB_QUERY_COUNT = Counter(
    "db_queries_total",
    "Total number of database queries",
    ["operation", "table"],
)

DB_QUERY_LATENCY = Histogram(
    "db_query_duration_seconds",
    "Database query latency in seconds",
    ["operation", "table"],
)

DB_CONNECTION_COUNT = Gauge(
    "db_connections_active",
    "Number of active database connections",
)

# Cache metrics
CACHE_HIT_COUNT = Counter(
    "cache_hits_total",
    "Total number of cache hits",
    ["cache_type"],
)

CACHE_MISS_COUNT = Counter(
    "cache_misses_total",
    "Total number of cache misses",
    ["cache_type"],
)

CACHE_SIZE = Gauge(
    "cache_size_bytes",
    "Total size of cache in bytes",
    ["cache_type"],
)

CACHE_EVICTIONS = Counter(
    "cache_evictions_total",
    "Total number of cache evictions",
    ["cache_type"],
)

# Memory metrics
MEMORY_USAGE = Gauge(
    "memory_usage_bytes",
    "Memory usage in bytes",
    ["type"],
)

# System metrics
CPU_USAGE = Gauge(
    "cpu_usage_percent",
    "CPU usage percentage",
    ["type"],
)

DISK_USAGE = Gauge(
    "disk_usage_bytes",
    "Disk usage in bytes",
    ["path", "type"],
)

# Network metrics
NETWORK_IO = Counter(
    "network_io_bytes",
    "Network IO in bytes",
    ["direction"],
)

NETWORK_ERRORS = Counter(
    "network_errors_total",
    "Network errors",
    ["type"],
)


def record_returns(strategy: str, returns: float) -> None:
    """Record strategy returns."""
    RETURNS.labels(strategy=strategy).set(returns)


def update_sharpe_ratio(strategy: str, sharpe: float) -> None:
    """Update Sharpe ratio."""
    SHARPE_RATIO.labels(strategy=strategy).set(sharpe)


def update_max_drawdown(strategy: str, drawdown: float) -> None:
    """Update maximum drawdown."""
    MAX_DRAWDOWN.labels(strategy=strategy).set(drawdown)


def record_trade(strategy: str, direction: str, size: float = 1.0) -> None:
    """Record a trade."""
    TRADES.labels(strategy=strategy, direction=direction).inc(size)


def record_volume(strategy: str, volume: float) -> None:
    """Record trading volume."""
    VOLUME.labels(strategy=strategy).inc(volume)


def execution_time_decorator(name: str):
    """Decorator to record function execution time.

    Args:
        name: Name of the function being monitored
    """

    def decorator(func: Callable[..., Any]):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                EXECUTION_TIME.labels(function=name, status="success").observe(
                    time.time() - start_time
                )
                return result
            except Exception as e:
                EXECUTION_TIME.labels(function=name, status="error").observe(
                    time.time() - start_time
                )
                ERROR_COUNTER.labels(function=name, error_type=type(e).__name__).inc()
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                EXECUTION_TIME.labels(function=name, status="success").observe(
                    time.time() - start_time
                )
                return result
            except Exception as e:
                EXECUTION_TIME.labels(function=name, status="error").observe(
                    time.time() - start_time
                )
                ERROR_COUNTER.labels(function=name, error_type=type(e).__name__).inc()
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
