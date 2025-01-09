"""Monitoring metrics module."""

import time
from functools import wraps
from prometheus_client import Counter, Gauge, Histogram, REGISTRY


def create_metrics():
    """Create and register metrics."""
    global REQUEST_LATENCY, RETURNS, SHARPE_RATIO, MAX_DRAWDOWN, TRADES, VOLUME, ERROR_COUNTER

    # Execution time metrics
    REQUEST_LATENCY = Histogram(
        "backtest_execution_time_seconds",
        "Time spent processing request",
        ["function", "status"],
    )

    # Returns metrics
    RETURNS = Gauge("backtest_returns", "Strategy returns", ["strategy"])

    # Sharpe ratio metrics
    SHARPE_RATIO = Gauge("backtest_sharpe_ratio", "Strategy Sharpe ratio", ["strategy"])

    # Max drawdown metrics
    MAX_DRAWDOWN = Gauge(
        "backtest_max_drawdown", "Strategy maximum drawdown", ["strategy"]
    )

    # Trade metrics
    TRADES = Counter(
        "backtest_trades_total", "Number of trades executed", ["strategy", "type"]
    )

    # Volume metrics
    VOLUME = Gauge("backtest_trading_volume", "Trading volume", ["strategy"])

    # Error metrics
    ERROR_COUNTER = Counter(
        "backtest_errors_total", "Number of errors by type", ["type", "function"]
    )


def record_execution_time(function: str, duration: float, status: str = "success"):
    """Record function execution time.

    Args:
        function: Name of the function
        duration: Execution time in seconds
        status: Execution status (success/error)
    """
    REQUEST_LATENCY.labels(function=function, status=status).observe(duration)


def record_returns(strategy: str, returns: float):
    """Record strategy returns.

    Args:
        strategy: Strategy name
        returns: Return value
    """
    RETURNS.labels(strategy=strategy).set(returns)


def update_sharpe_ratio(strategy: str, ratio: float):
    """Update Sharpe ratio.

    Args:
        strategy: Strategy name
        ratio: Sharpe ratio value
    """
    SHARPE_RATIO.labels(strategy=strategy).set(ratio)


def update_max_drawdown(strategy: str, drawdown: float):
    """Update maximum drawdown.

    Args:
        strategy: Strategy name
        drawdown: Maximum drawdown value
    """
    MAX_DRAWDOWN.labels(strategy=strategy).set(drawdown)


def record_trade(strategy: str, trade_type: str, amount: float):
    """Record trade execution.

    Args:
        strategy: Strategy name
        trade_type: Type of trade (buy/sell)
        amount: Trade amount
    """
    TRADES.labels(strategy=strategy, type=trade_type).inc()


def record_volume(strategy: str, volume: float):
    """Record trading volume.

    Args:
        strategy: Strategy name
        volume: Trading volume
    """
    VOLUME.labels(strategy=strategy).set(volume)


def record_error(error_type: str, function: str):
    """Record error occurrence.

    Args:
        error_type: Type of error
        function: Function where error occurred
    """
    ERROR_COUNTER.labels(type=error_type, function=function).inc()


def execution_time_decorator(name: str):
    """Decorator to record function execution time.

    Args:
        name: Name to use for the metric
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                record_execution_time(name, duration, "success")
                return result
            except Exception as e:
                duration = time.time() - start_time
                record_execution_time(name, duration, "error")
                record_error(type(e).__name__, name)
                raise

        return wrapper

    return decorator


# Initialize metrics
create_metrics()
