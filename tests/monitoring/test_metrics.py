"""Test module for monitoring metrics."""

import pytest
import asyncio
from prometheus_client import REGISTRY
from core.monitoring.metrics import (
    execution_time_decorator,
    record_returns,
    update_sharpe_ratio,
    update_max_drawdown,
    record_trade,
    record_volume,
    ERROR_COUNTER,
    REQUEST_LATENCY,
    create_metrics,
)


@pytest.fixture(autouse=True)
def clear_metrics():
    """Clear all metrics before each test."""
    for metric in list(REGISTRY._collector_to_names.keys()):
        REGISTRY.unregister(metric)

    # Re-register our metrics
    create_metrics()
    yield


@pytest.mark.asyncio
async def test_record_execution_time():
    """Test execution time recording."""

    @execution_time_decorator("test_function")
    async def test_function():
        await asyncio.sleep(0.1)
        return True

    # Execute function
    await test_function()

    # Check metrics
    value = REGISTRY.get_sample_value(
        "backtest_execution_time_seconds_count",
        {"function": "test_function", "status": "success"},
    )
    assert value == 1.0


def test_record_returns():
    """Test returns recording."""
    strategy = "test_strategy"
    returns = 0.15

    record_returns(strategy, returns)

    value = REGISTRY.get_sample_value("backtest_returns", {"strategy": strategy})
    assert value == returns


def test_update_sharpe_ratio():
    """Test Sharpe ratio update."""
    strategy = "test_strategy"
    ratio = 1.5

    update_sharpe_ratio(strategy, ratio)

    value = REGISTRY.get_sample_value("backtest_sharpe_ratio", {"strategy": strategy})
    assert value == ratio


def test_update_max_drawdown():
    """Test max drawdown update."""
    strategy = "test_strategy"
    drawdown = -0.25

    update_max_drawdown(strategy, drawdown)

    value = REGISTRY.get_sample_value("backtest_max_drawdown", {"strategy": strategy})
    assert value == drawdown


def test_record_trade():
    """Test trade recording."""
    strategy = "test_strategy"
    trade_type = "buy"
    amount = 1000.0

    record_trade(strategy, trade_type, amount)

    value = REGISTRY.get_sample_value(
        "backtest_trades_total", {"strategy": strategy, "type": trade_type}
    )
    assert value == 1.0


def test_record_volume():
    """Test volume recording."""
    strategy = "test_strategy"
    volume = 5000.0

    record_volume(strategy, volume)

    value = REGISTRY.get_sample_value("backtest_trading_volume", {"strategy": strategy})
    assert value == volume


@pytest.mark.asyncio
async def test_execution_time_decorator():
    """Test execution time decorator with success."""

    @execution_time_decorator("test_success")
    async def success_function():
        await asyncio.sleep(0.1)
        return True

    result = await success_function()
    assert result is True

    # Check success metrics
    count = REGISTRY.get_sample_value(
        "backtest_execution_time_seconds_count",
        {"function": "test_success", "status": "success"},
    )
    assert count == 1.0


@pytest.mark.asyncio
async def test_execution_time_decorator_error():
    """Test execution time decorator with error."""

    @execution_time_decorator("test_error")
    async def error_function():
        await asyncio.sleep(0.1)
        raise ValueError("Test error")

    with pytest.raises(ValueError):
        await error_function()

    # Check error metrics
    error_count = REGISTRY.get_sample_value(
        "backtest_errors_total", {"type": "ValueError", "function": "test_error"}
    )
    assert error_count == 1.0

    exec_count = REGISTRY.get_sample_value(
        "backtest_execution_time_seconds_count",
        {"function": "test_error", "status": "error"},
    )
    assert exec_count == 1.0
