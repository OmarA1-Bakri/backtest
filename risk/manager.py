from typing import Dict, Any, Optional
import logging
from models.model_facade import ModelFacade

logger = logging.getLogger(__name__)


class RiskManager:
    """Manages trading risk and position sizing."""

    def __init__(
        self,
        model_facade: ModelFacade,
        initial_cash: float = 10000.0,
        max_position_size: float = 0.2,
        stop_loss_pct: float = 0.02,
        take_profit_pct: float = 0.05,
    ):
        """Initialize risk manager.

        Args:
            model_facade: Model facade for predictions
            initial_cash: Initial capital
            max_position_size: Maximum position size as fraction of portfolio
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
        """
        self.model_facade = model_facade
        self.initial_cash = initial_cash
        self.current_cash = initial_cash
        self.max_position_size = max_position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.stop_loss_price = None
        self.stop_loss_active = False

    def calculate_position_size(self, signal: Dict[str, Any]) -> float:
        """Calculate position size based on risk parameters.

        Args:
            signal: Trading signal with prediction confidence

        Returns:
            Position size in base currency
        """
        confidence = signal.get("confidence", 0.5)

        # Scale position size by confidence and max size
        position_size = self.current_cash * self.max_position_size * confidence

        return min(position_size, self.current_cash)

    def update_cash(self, trade_amount: float):
        """Update available cash after trade.

        Args:
            trade_amount: Amount of cash used in trade (negative for buys)
        """
        self.current_cash += trade_amount

    def get_position_size(self, features: Any) -> float:
        """Get position size based on current market conditions.

        Args:
            features: Market features for prediction

        Returns:
            Recommended position size
        """
        # Get regime prediction
        regime = self.model_facade.predict_hmm_regime(features)

        # Adjust max position size based on regime
        if regime == "High Volatility":
            max_size = self.max_position_size * 0.5
        else:
            max_size = self.max_position_size

        return self.current_cash * max_size

    def adjust_stop_loss(self, price: float, atr: float, regime: str) -> float:
        """Adjust stop loss based on volatility.

        Args:
            price: Current price
            atr: Average True Range
            regime: Market regime

        Returns:
            Stop loss price
        """
        # Use wider stops in high volatility
        if regime == "High Volatility":
            stop_distance = atr * 3  # 3 ATR for high volatility
        else:
            stop_distance = atr * 2  # 2 ATR for normal volatility

        # Apply minimum stop based on percentage
        min_stop = price * self.stop_loss_pct
        stop_distance = max(stop_distance, min_stop)

        self.stop_loss_price = price - stop_distance
        self.stop_loss_active = True

        return self.stop_loss_price

    def check_stop_loss(self, price: float) -> bool:
        """Check if stop loss is triggered.

        Args:
            price: Current price

        Returns:
            True if stop loss is triggered
        """
        if not hasattr(self, "stop_loss_price") or not hasattr(
            self, "stop_loss_active"
        ):
            return False

        if not self.stop_loss_active:
            return False

        return price <= self.stop_loss_price

    def check_risk_limits(self, price: float, position_size: float) -> bool:
        """Check if trade meets risk limits.

        Args:
            price: Current price
            position_size: Proposed position size

        Returns:
            True if trade meets risk limits
        """
        # Check if we have enough cash
        if position_size > self.current_cash:
            logger.warning("Position size exceeds available cash")
            return False

        # Check if position size is too large
        if position_size > self.initial_cash * self.max_position_size:
            logger.warning("Position size exceeds maximum allowed")
            return False

        return True
