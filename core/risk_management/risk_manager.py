"""
Risk management module for handling position sizing and stop losses.
"""

import numpy as np
from typing import Optional
from ..models.model_facade import ModelFacade
from ..config.settings import Settings


class RiskManager:
    """
    Risk manager class for handling position sizing and risk management.
    """

    def __init__(self, model_facade: ModelFacade, initial_cash: float = 10000.0):
        """
        Initialize the risk manager.

        Args:
            model_facade: Model facade instance for market predictions
            initial_cash: Initial cash amount for trading
        """
        self.model_facade = model_facade
        self.initial_cash = initial_cash
        self.current_cash = initial_cash
        self.settings = Settings()

        # Risk parameters
        self.max_position_size = 0.2  # Maximum position size as percentage of portfolio
        self.risk_per_trade = 0.02  # Maximum risk per trade (2% of portfolio)
        self.atr_multiplier = {
            "Low Volatility": 2.0,
            "Medium Volatility": 2.5,
            "High Volatility": 3.0,
        }

    def get_position_size(self, market_data):
        """Calculate position size based on market conditions and risk parameters.

        Args:
            market_data: Array of market data features

        Returns:
            float: Position size in units
        """
        regime = self.model_facade.predict_hmm_regime(market_data)

        # Base position size as percentage of capital
        base_size = 0.02  # 2% of capital

        # Adjust based on volatility regime
        if regime == "High Volatility":
            base_size *= 0.5  # Reduce position size in high volatility
        elif regime == "Low Volatility":
            base_size *= 1.5  # Increase position size in low volatility

        position_size = self.initial_cash * base_size
        return position_size

    def adjust_stop_loss(self, entry_price, atr, regime):
        """Calculate and adjust stop loss based on market conditions.

        Args:
            entry_price: Entry price of the position
            atr: Average True Range value
            regime: Current market regime

        Returns:
            float: Stop loss price
        """
        # Base stop loss multiplier
        multiplier = 2.0

        # Adjust multiplier based on regime
        if regime == "High Volatility":
            multiplier = 3.0  # Wider stop in high volatility
        elif regime == "Low Volatility":
            multiplier = 1.5  # Tighter stop in low volatility

        stop_distance = atr * multiplier
        stop_loss = entry_price - stop_distance

        return stop_loss

    def update_portfolio_value(self, new_value: float) -> None:
        """
        Update the current portfolio value.

        Args:
            new_value: New portfolio value
        """
        self.current_cash = new_value

    def calculate_risk_adjusted_position(self, price: float, stop_loss: float) -> float:
        """
        Calculate position size based on risk per trade.

        Args:
            price: Current price
            stop_loss: Stop loss price

        Returns:
            Risk-adjusted position size
        """
        if price <= stop_loss:
            return 0.0

        risk_amount = self.current_cash * self.risk_per_trade
        price_risk = abs(price - stop_loss)
        return risk_amount / price_risk if price_risk > 0 else 0.0
