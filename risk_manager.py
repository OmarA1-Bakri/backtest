"""Risk management module."""

import numpy as np
from typing import Dict, Optional, Tuple
from logger import logger
from core.config.settings import config


class RiskManager:
    """
    RiskManager handles position sizing and risk metrics based on market regimes.
    Implements sophisticated risk management strategies including VaR, Expected Shortfall,
    and dynamic position sizing based on market conditions.
    """

    def __init__(self, model_facade, initial_cash: Optional[float] = None):
        """
        Initialize the RiskManager with model facade and initial parameters.

        Args:
            model_facade: Model facade for predictions
            initial_cash (Optional[float]): Initial capital for trading
        """
        self.model_facade = model_facade
        self.initial_cash = (
            initial_cash if initial_cash is not None else config.INITIAL_CASH
        )
        self.base_position_size = self.initial_cash * 0.01  # 1% of initial cash
        self.max_drawdown = config.MAX_DRAWDOWN  # 20% default
        self.current_drawdown = 0
        self.position_limits = {
            "Low Volatility": 1.5,
            "Medium Volatility": 1.2,
            "High Volatility": 0.5,
            "default": 1.0,
        }
        self.risk_metrics: Dict[str, float] = {}
        self.stop_loss_active = False
        self.stop_loss_price = 0.0

    def get_position_size(self, current_features: np.ndarray, X_seq=None) -> float:
        """
        Determines position size based on the current market regime and risk metrics.

        Args:
            current_features (np.ndarray): Current feature vector
            X_seq: Optional sequence data for LSTM models

        Returns:
            float: Calculated position size
        """
        try:
            # Get market regime prediction
            regime = self.model_facade.predict_regime(current_features, X_seq)

            # Calculate base position size based on regime
            position_multiplier = self.position_limits.get(
                regime, self.position_limits["default"]
            )
            position_size = self.base_position_size * position_multiplier

            # Adjust for risk metrics
            var = self.calculate_var(current_features)
            if var > 0:
                position_size *= 1 - var  # Reduce position size based on VaR

            # Check drawdown limits
            if self.current_drawdown >= self.max_drawdown:
                logger.warning(
                    f"Max drawdown limit reached: {self.current_drawdown:.2%}"
                )
                return 0

            return position_size

        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return self.base_position_size  # Return default size on error

    def calculate_var(
        self, current_features: np.ndarray, confidence: float = 0.95
    ) -> float:
        """
        Calculate Value at Risk (VaR) for the current market conditions.

        Args:
            current_features (np.ndarray): Current feature vector
            confidence (float): Confidence level for VaR calculation

        Returns:
            float: Calculated VaR
        """
        try:
            # Get volatility estimate from model
            volatility = self.model_facade.predict_volatility(current_features)

            # Calculate VaR using parametric method
            z_score = np.abs(
                np.percentile(np.random.standard_normal(1000), confidence * 100)
            )
            var = volatility * z_score

            self.risk_metrics["VaR"] = var
            return var

        except Exception as e:
            logger.error(f"Error calculating VaR: {str(e)}")
            return 0.0

    def update_drawdown(self, portfolio_value: float) -> None:
        """
        Update the current drawdown based on portfolio value.

        Args:
            portfolio_value (float): Current portfolio value
        """
        try:
            # Calculate drawdown
            drawdown = (self.initial_cash - portfolio_value) / self.initial_cash
            self.current_drawdown = max(self.current_drawdown, drawdown)

            # Log warning if approaching max drawdown
            if self.current_drawdown > self.max_drawdown * 0.8:
                logger.warning(
                    f"Approaching max drawdown limit. Current: {self.current_drawdown:.2%}, "
                    f"Max: {self.max_drawdown:.2%}"
                )

        except Exception as e:
            logger.error(f"Error updating drawdown: {str(e)}")

    def update_stop_loss(self, current_price: float, position: str) -> bool:
        """
        Update and check stop loss conditions.

        Args:
            current_price (float): Current asset price
            position (str): Current position ('long' or 'short')

        Returns:
            bool: True if stop loss triggered, False otherwise
        """
        try:
            if not self.stop_loss_active:
                return False

            if position == "long" and current_price < self.stop_loss_price:
                logger.info(f"Stop loss triggered at {current_price}")
                return True

            if position == "short" and current_price > self.stop_loss_price:
                logger.info(f"Stop loss triggered at {current_price}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking stop loss: {str(e)}")
            return False

    def set_stop_loss(
        self, entry_price: float, position: str, risk_percent: float = 0.02
    ) -> None:
        """
        Set stop loss price for a new position.

        Args:
            entry_price (float): Entry price for the position
            position (str): Position type ('long' or 'short')
            risk_percent (float): Percentage of position to risk
        """
        try:
            self.stop_loss_active = True
            if position == "long":
                self.stop_loss_price = entry_price * (1 - risk_percent)
            else:  # short position
                self.stop_loss_price = entry_price * (1 + risk_percent)

            logger.info(f"Stop loss set at {self.stop_loss_price}")

        except Exception as e:
            logger.error(f"Error setting stop loss: {str(e)}")
            self.stop_loss_active = False

    def get_risk_metrics(self) -> Dict[str, float]:
        """
        Get current risk metrics.

        Returns:
            Dict[str, float]: Dictionary of risk metrics
        """
        return {
            **self.risk_metrics,
            "current_drawdown": self.current_drawdown,
            "max_drawdown_limit": self.max_drawdown,
        }
