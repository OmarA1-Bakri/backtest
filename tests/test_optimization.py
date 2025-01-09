"""Test optimization functionality."""

import pytest
from unittest.mock import MagicMock
import pandas as pd
import json
from datetime import datetime, timedelta

from core.cache import RedisCache
from strategies.base.base_strategy import BaseStrategy


class MockStrategy(BaseStrategy):
    """Mock strategy for testing."""

    # Define parameters as class variables
    param1 = 5
    param2 = 5

    def __init__(self, broker, data, params, initial_cash=10000.0):
        """Initialize strategy."""
        super().__init__(broker=broker, data=data, params=params)
        self.cash = initial_cash
        self._position = 0  # Use a private variable for position

    @property
    def position(self):
        """Get current position."""
        return self._position

    @position.setter
    def position(self, value):
        """Set current position."""
        self._position = value

    def generate_signals(self):
        """Mock signal calculation."""
        return {
            "signal": 0,
            "price": self.data.Close.iloc[-1] if len(self.data) > 0 else 0,
        }

    def execute_trades(self, signals, timestamp=None):
        """Mock trade execution."""
        # Simple mock implementation
        signal = signals.get("signal", 0)
        price = signals.get("price", 0)

        if signal == 1 and self.position <= 0:  # Buy
            self.position = 1
        elif signal == -1 and self.position >= 0:  # Sell
            self.position = -1

    def next(self):
        """Process next data point."""
        signals = self.generate_signals()
        self.execute_trades(signals)


@pytest.fixture
def redis_cache():
    """Create Redis cache instance."""
    cache = RedisCache()
    # Clear any existing data
    cache.redis.flushdb()
    yield cache
    # Cleanup after tests
    cache.redis.flushdb()


def test_optimization_task():
    """Test optimization task execution."""
    # Create test data
    dates = pd.date_range(start="2020-01-01", end="2020-01-31", freq="D")
    data = pd.DataFrame(
        {
            "Close": range(len(dates)),
            "Open": range(len(dates)),
            "High": range(len(dates)),
            "Low": range(len(dates)),
            "Volume": [1000] * len(dates),
        },
        index=dates,
    )

    broker = MagicMock()

    # Create strategy instance
    strategy = MockStrategy(
        broker=broker,
        data=data,
        params={"param1": 5, "param2": 5},
        initial_cash=10000.0,
    )

    # Test strategy execution
    strategy.next()
    assert hasattr(strategy, "position")


def test_cache_integration(redis_cache):
    """Test cache integration for optimization results."""
    # Test data
    optimization_key = "opt_MockStrategy_2020-01-01_2020-01-31"
    optimization_result = {
        "params": {"param1": 5, "param2": 5},
        "train_sharpe": 1.5,
        "test_sharpe": 1.2,
    }

    # Store result
    assert redis_cache.set(optimization_key, optimization_result)

    # Retrieve result
    cached_result = redis_cache.get(optimization_key)
    assert cached_result == optimization_result

    # Test expiration
    assert redis_cache.get("nonexistent_key") is None
