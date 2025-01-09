"""Test module for simple moving average strategy."""

import pytest
import pandas as pd
from typing import Dict, Any
from datetime import datetime

from strategies.moving_average import SimpleMAStrategy


@pytest.fixture
def test_data() -> pd.DataFrame:
    """Create test DataFrame with OHLCV data.

    Returns:
        DataFrame with OHLCV columns and DateTimeIndex
    """
    prices = [100, 101, 102, 103, 104]
    dates = pd.date_range(start="2024-01-01", periods=len(prices), freq="D")

    df = pd.DataFrame(
        {
            "OPEN": prices,
            "HIGH": [p * 1.01 for p in prices],
            "LOW": [p * 0.99 for p in prices],
            "CLOSE": prices,
            "VOLUME": [1000] * len(prices),
        },
        index=dates,
    )
    return df


class MockBroker:
    """Mock broker class for testing."""

    def __init__(self):
        self.orders = []
        self.equity = 10000.0
        self.position = 0

    def buy(self, size: float):
        self.orders.append(("BUY", size))
        self.position += size

    def sell(self, size: float):
        self.orders.append(("SELL", size))
        self.position -= size


class MockData:
    """Mock data class for testing."""

    def __init__(self, prices: list):
        self.Close = pd.Series(
            [100] * 50 + prices
        )  # Add enough history for moving averages
        self.Open = pd.Series([100] * 50 + prices)
        self.High = pd.Series([101] * 50 + [p * 1.01 for p in prices])
        self.Low = pd.Series([99] * 50 + [p * 0.99 for p in prices])
        self.Volume = pd.Series([1000] * (50 + len(prices)))


def test_strategy_initialization():
    """Test strategy initialization."""
    params = {"short_window": 5, "long_window": 10}

    mock_broker = MockBroker()
    mock_data = MockData([100] * 20)

    strategy = SimpleMAStrategy(broker=mock_broker, data=mock_data, params=params)

    assert strategy.short_window == 5
    assert strategy.long_window == 10


def test_calculate_signals(test_data: pd.DataFrame):
    """Test signal calculation for backtesting."""
    mock_broker = MockBroker()
    mock_data = MockData([100] * 20)

    strategy = SimpleMAStrategy(
        broker=mock_broker, data=mock_data, params={"short_window": 2, "long_window": 3}
    )

    signals = strategy.calculate_signals(test_data)

    # Check signal column exists
    assert "signal" in signals.columns

    # Check moving averages are calculated
    assert "SMA_short" in signals.columns
    assert "SMA_long" in signals.columns

    # Verify signal values are valid
    assert signals["signal"].isin([-1, 0, 1]).all()


def test_generate_signals():
    """Test live trading signal generation."""
    prices = [100, 101, 102, 103, 104]
    mock_data = MockData(prices)
    mock_broker = MockBroker()

    strategy = SimpleMAStrategy(
        broker=mock_broker, data=mock_data, params={"short_window": 2, "long_window": 3}
    )

    signals = strategy.generate_signals()

    # Check signal structure
    assert isinstance(signals, dict)
    assert all(
        k in signals for k in ["signal", "sma_short", "sma_long", "current_price"]
    )
    assert signals["signal"] in [-1, 0, 1]
    assert isinstance(signals["sma_short"], float)
    assert isinstance(signals["sma_long"], float)
    assert signals["current_price"] == prices[-1]


def test_execute_trades():
    """Test trade execution logic."""
    prices = [100, 101, 102, 103, 104]
    mock_data = MockData(prices)
    mock_broker = MockBroker()

    strategy = SimpleMAStrategy(
        broker=mock_broker, data=mock_data, params={"short_window": 2, "long_window": 3}
    )

    # Test buy signal
    buy_signals = {"signal": 1, "current_price": 104.0}
    strategy.execute_trades(buy_signals)

    # Test sell signal
    sell_signals = {"signal": -1, "current_price": 102.0}
    strategy.execute_trades(sell_signals)

    # Verify trade history
    assert len(strategy.trade_history) > 0
    for trade in strategy.trade_history:
        assert isinstance(trade, dict)
        assert all(k in trade for k in ["timestamp", "type", "price", "size"])
        assert trade["type"] in ["BUY", "SELL"]
        assert isinstance(trade["price"], float)
        assert isinstance(trade["size"], (int, float))
