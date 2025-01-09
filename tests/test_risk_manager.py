"""Test module for risk manager."""

import pytest
import pandas as pd
import numpy as np
from core.config.settings import config
from models.model_facade import ModelFacade
from risk.manager import RiskManager
from unittest.mock import MagicMock


def create_test_data(prices):
    """Create test DataFrame with price data."""
    df = pd.DataFrame(
        {
            "open": prices,
            "high": [p * 1.01 for p in prices],
            "low": [p * 0.99 for p in prices],
            "close": prices,
            "volume": [100] * len(prices),
        },
        index=pd.date_range(start="2024-01-01", periods=len(prices)),
    )
    return df


def test_risk_manager_initialization():
    """Test risk manager initialization."""
    model_facade = MagicMock()
    risk_manager = RiskManager(
        model_facade=model_facade,
        initial_cash=10000.0,
        max_position_size=0.2,
        stop_loss_pct=0.02,
    )

    assert risk_manager.initial_cash == 10000.0
    assert risk_manager.current_cash == 10000.0
    assert risk_manager.max_position_size == 0.2
    assert risk_manager.stop_loss_pct == 0.02


def test_position_size_calculation():
    """Test position sizing calculations."""
    model_facade = MagicMock()
    risk_manager = RiskManager(
        model_facade=model_facade, initial_cash=10000.0, max_position_size=0.2
    )

    # Test with different confidence levels
    signal_high = {"action": "buy", "confidence": 0.8}
    signal_low = {"action": "buy", "confidence": 0.3}

    size_high = risk_manager.calculate_position_size(signal_high)
    size_low = risk_manager.calculate_position_size(signal_low)

    assert size_high > size_low
    assert size_high <= 2000.0  # Max 20% of initial cash
    assert size_low > 0


def test_cash_updates():
    """Test cash position updates."""
    model_facade = MagicMock()
    risk_manager = RiskManager(model_facade=model_facade, initial_cash=10000.0)

    # Test buy
    risk_manager.update_cash(-1000.0)
    assert risk_manager.current_cash == 9000.0

    # Test sell
    risk_manager.update_cash(500.0)
    assert risk_manager.current_cash == 9500.0


def test_risk_limits():
    """Test risk limit checks."""
    model_facade = MagicMock()
    risk_manager = RiskManager(
        model_facade=model_facade, initial_cash=10000.0, max_position_size=0.2
    )

    # Test within limits
    assert risk_manager.check_risk_limits(price=100.0, position_size=1000.0)

    # Test exceeds cash
    assert not risk_manager.check_risk_limits(price=100.0, position_size=11000.0)

    # Test exceeds max position size
    assert not risk_manager.check_risk_limits(price=100.0, position_size=2500.0)


def test_risk_manager_position_sizing():
    """Test position sizing calculations."""
    # Create test data
    prices = [10, 12, 14, 13, 15, 16, 17, 18, 19, 20]
    df = create_test_data(prices)
    features = ["open", "high", "low", "close", "volume"]

    # Create a mock model facade
    model_facade = ModelFacade(features=features, model_settings=config.models)
    model_facade.predict_hmm_regime = MagicMock(return_value="Low Volatility")

    # Initialize the risk manager
    risk_manager = RiskManager(model_facade=model_facade, initial_cash=10000)

    # Get position size
    position_size = risk_manager.get_position_size(df.iloc[0][features].values)
    assert position_size > 0

    # Test with different regime
    model_facade.predict_hmm_regime = MagicMock(return_value="High Volatility")
    position_size = risk_manager.get_position_size(df.iloc[0][features].values)
    assert position_size > 0


def test_risk_manager_stop_loss():
    # Create test data
    prices = [10, 12, 14, 13, 15, 16, 17, 18, 19, 20]
    df = create_test_data(prices)
    features = ["open", "high", "low", "close", "volume"]

    # Create a mock model facade
    model_facade = ModelFacade(features=features, model_settings=config.models)
    model_facade.predict_hmm_regime = MagicMock(return_value="Low Volatility")

    # Initialize the risk manager
    risk_manager = RiskManager(model_facade=model_facade, initial_cash=10000)

    # Set stop loss
    atr = 1
    stop_loss = risk_manager.adjust_stop_loss(15, atr, "Low Volatility")
    assert stop_loss == 13

    # Check if stop loss is triggered
    assert risk_manager.check_stop_loss(12) is True
    assert risk_manager.check_stop_loss(14) is False

    # Check if stop loss is not triggered if not active
    risk_manager.stop_loss_active = False
    assert risk_manager.check_stop_loss(12) is False
