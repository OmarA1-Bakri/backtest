"""Test broker functionality."""

import pytest
import pandas as pd
import numpy as np
from broker import Broker


@pytest.fixture
def broker():
    """Create a broker instance with default settings."""
    return Broker()


@pytest.fixture
def broker_with_cash():
    """Create a broker instance with specific initial cash."""
    return Broker(initial_cash=10000.0)


def test_broker_initialization():
    """Test broker initialization with different cash amounts."""
    # Test default initialization
    broker = Broker()
    assert broker.initial_cash == 100000.0
    assert broker.cash == 100000.0
    assert broker.positions == {}
    assert broker.trades == []
    assert broker.commission_rate == 0.001

    # Test initialization with specific cash amount
    broker = Broker(initial_cash=50000.0)
    assert broker.initial_cash == 50000.0
    assert broker.cash == 50000.0


def test_place_buy_order(broker):
    """Test placing buy orders."""
    # Test successful buy order
    assert broker.place_order("AAPL", 10, 150.0)
    assert broker.positions["AAPL"] == 10
    assert len(broker.trades) == 1
    assert broker.trades[0]["type"] == "buy"
    assert broker.trades[0]["quantity"] == 10
    assert broker.trades[0]["price"] == 150.0

    # Calculate expected cash after trade with commission
    commission = 10 * 150.0 * 0.001
    expected_cash = 100000.0 - (10 * 150.0 + commission)
    assert pytest.approx(broker.cash) == expected_cash

    # Test insufficient cash
    assert not broker.place_order("AAPL", 10000, 150.0)
    assert broker.positions["AAPL"] == 10  # Position should remain unchanged


def test_place_sell_order(broker):
    """Test placing sell orders."""
    # First buy some shares
    broker.place_order("AAPL", 10, 150.0)
    initial_cash = broker.cash

    # Test successful sell order
    assert broker.place_order("AAPL", -5, 160.0)
    assert broker.positions["AAPL"] == 5
    assert len(broker.trades) == 2
    assert broker.trades[1]["type"] == "sell"
    assert broker.trades[1]["quantity"] == -5
    assert broker.trades[1]["price"] == 160.0

    # Calculate expected cash after trade with commission
    commission = 5 * 160.0 * 0.001
    expected_cash = initial_cash + (5 * 160.0 - commission)
    assert pytest.approx(broker.cash) == expected_cash

    # Test insufficient shares
    assert not broker.place_order("AAPL", -10, 160.0)
    assert broker.positions["AAPL"] == 5  # Position should remain unchanged


def test_get_position(broker):
    """Test getting positions."""
    # Test non-existent position
    assert broker.get_position("AAPL") == 0

    # Test after buying
    broker.place_order("AAPL", 10, 150.0)
    assert broker.get_position("AAPL") == 10

    # Test after selling
    broker.place_order("AAPL", -5, 160.0)
    assert broker.get_position("AAPL") == 5


def test_get_portfolio_value(broker):
    """Test portfolio value calculation."""
    # Buy multiple stocks
    broker.place_order("AAPL", 10, 150.0)
    broker.place_order("GOOGL", 5, 2500.0)

    # Test portfolio value calculation
    current_prices = {"AAPL": 160.0, "GOOGL": 2600.0}
    expected_value = broker.cash + (10 * 160.0) + (5 * 2600.0)
    assert pytest.approx(broker.get_portfolio_value(current_prices)) == expected_value

    # Test with missing price
    current_prices = {"AAPL": 160.0}  # GOOGL price missing
    expected_value = broker.cash + (10 * 160.0)  # Should only count AAPL
    assert pytest.approx(broker.get_portfolio_value(current_prices)) == expected_value


def test_get_performance_metrics(broker):
    """Test performance metrics calculation."""
    # Execute a series of trades
    broker.place_order("AAPL", 10, 150.0)  # Buy at 150
    broker.place_order("AAPL", -5, 160.0)  # Sell half at 160
    broker.place_order("AAPL", -5, 140.0)  # Sell rest at 140

    metrics = broker.get_performance_metrics()
    assert "total_return" in metrics
    assert "sharpe_ratio" in metrics
    assert "max_drawdown" in metrics
    assert "num_trades" in metrics
    assert metrics["num_trades"] == 3


def test_error_handling(broker):
    """Test error handling in broker operations."""
    # Test invalid order parameters
    assert not broker.place_order("AAPL", 0, 150.0)  # Zero quantity
    assert not broker.place_order("AAPL", 10, -150.0)  # Negative price

    # Test portfolio value with invalid prices
    assert broker.get_portfolio_value({}) == broker.cash  # Empty prices

    # Buy some shares then test with invalid prices
    broker.place_order("AAPL", 10, 150.0)
    assert broker.get_portfolio_value({"AAPL": -100.0}) == broker.cash  # Negative price
