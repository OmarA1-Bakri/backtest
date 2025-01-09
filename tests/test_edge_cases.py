"""Test edge cases and boundary conditions."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal

from models.model_facade import ModelFacade
from strategies.moving_average import SimpleMAStrategy
from risk.manager import RiskManager
from database.models.backtest import Backtest
from database.models.backtest_result import BacktestResult
from database.models.strategy import Strategy
from core.config.settings import Settings


def create_edge_case_data():
    """Create various edge case price data scenarios."""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    scenarios = {}

    # Flat prices
    scenarios["flat"] = pd.DataFrame(
        {
            "open": [100] * 100,
            "high": [100] * 100,
            "low": [100] * 100,
            "close": [100] * 100,
            "volume": [1000] * 100,
        },
        index=dates,
    )

    # Extreme volatility
    close_prices = [100]
    for _ in range(99):
        change = np.random.choice([-0.1, 0.1])  # 10% moves
        close_prices.append(close_prices[-1] * (1 + change))

    scenarios["volatile"] = pd.DataFrame(
        {
            "open": close_prices,
            "high": [p * 1.05 for p in close_prices],
            "low": [p * 0.95 for p in close_prices],
            "close": close_prices,
            "volume": [1000] * 100,
        },
        index=dates,
    )

    # Missing data
    scenarios["missing"] = pd.DataFrame(
        {
            "open": [100] * 100,
            "high": [100] * 100,
            "low": [100] * 100,
            "close": [100 if i % 10 != 0 else np.nan for i in range(100)],
            "volume": [1000] * 100,
        },
        index=dates,
    )

    # Zero volume
    scenarios["zero_volume"] = pd.DataFrame(
        {
            "open": [100] * 100,
            "high": [100] * 100,
            "low": [100] * 100,
            "close": [100] * 100,
            "volume": [0] * 100,
        },
        index=dates,
    )

    return scenarios


def test_edge_case_data_handling(db_session):
    """Test handling of edge case data scenarios."""
    scenarios = create_edge_case_data()
    features = ["open", "high", "low", "close", "volume"]
    model_settings = {
        "model_type": "lstm",
        "input_size": 10,
        "hidden_size": 32,
        "num_layers": 2,
        "output_size": 1,
    }

    for scenario_name, data in scenarios.items():
        # Initialize components
        model_facade = ModelFacade(model_settings=model_settings, features=features)
        risk_manager = RiskManager(model_facade=model_facade, initial_cash=10000.0)
        strategy = SimpleMAStrategy(
            data=data,
            params={"short_window": 5, "long_window": 20},
            initial_cash=10000.0,
        )
        strategy.risk_manager = risk_manager

        # Run strategy
        signals = strategy.generate_signals()

        if scenario_name == "flat":
            # Flat prices should generate minimal signals
            assert signals["action"] == "hold"
            assert signals["confidence"] < 0.1

        elif scenario_name == "volatile":
            # Volatile prices should have risk limits
            position_size = strategy.calculate_position_size(signals)
            assert position_size <= strategy.initial_cash * 0.2

        elif scenario_name == "missing":
            # Should handle missing data gracefully
            assert not pd.isna(signals["confidence"])

        elif scenario_name == "zero_volume":
            # Should consider volume in position sizing
            position_size = strategy.calculate_position_size(signals)
            assert position_size == 0


def test_numerical_edge_cases(db_session):
    """Test handling of numerical edge cases."""
    # Test very large numbers
    large_capital = Decimal("1000000000.00")  # 1 billion
    risk_manager = RiskManager(model_facade=MagicMock(), initial_cash=large_capital)
    assert risk_manager.current_cash == large_capital

    # Test very small numbers
    small_capital = Decimal("0.01")
    risk_manager = RiskManager(model_facade=MagicMock(), initial_cash=small_capital)
    assert risk_manager.current_cash == small_capital

    # Test position sizing with extreme values
    signal = {"action": "buy", "confidence": 1.0}

    large_position = risk_manager.calculate_position_size(signal)
    assert large_position <= large_capital * Decimal("0.2")

    small_position = risk_manager.calculate_position_size(signal)
    assert small_position <= small_capital * Decimal("0.2")


def test_time_edge_cases(db_session):
    """Test handling of time-related edge cases."""
    # Test data with gaps
    dates = pd.date_range(start="2024-01-01", periods=50, freq="D").tolist()
    dates.extend(pd.date_range(start="2024-03-01", periods=50, freq="D"))

    data = pd.DataFrame(
        {
            "open": [100] * 100,
            "high": [100] * 100,
            "low": [100] * 100,
            "close": [100] * 100,
            "volume": [1000] * 100,
        },
        index=dates,
    )

    strategy = SimpleMAStrategy(
        data=data, params={"short_window": 5, "long_window": 20}, initial_cash=10000.0
    )

    # Should handle the gap properly
    signals = strategy.generate_signals()
    assert isinstance(signals, dict)
    assert "action" in signals
    assert "confidence" in signals


def test_concurrent_risk_management(db_session):
    """Test concurrent risk management scenarios."""
    import asyncio

    risk_manager = RiskManager(
        model_facade=MagicMock(), initial_cash=10000.0, max_position_size=0.2
    )

    async def update_position(amount):
        await asyncio.sleep(0.1)  # Simulate processing time
        risk_manager.update_cash(amount)
        return risk_manager.current_cash

    async def run_concurrent_updates():
        tasks = [
            update_position(-1000),  # Buy
            update_position(500),  # Sell
            update_position(-750),  # Buy
            update_position(1250),  # Sell
        ]
        results = await asyncio.gather(*tasks)
        return results

    # Run concurrent updates
    final_positions = asyncio.run(run_concurrent_updates())

    # Verify final state
    assert len(final_positions) == 4
    assert risk_manager.current_cash == 10000.0  # Should be back to initial
