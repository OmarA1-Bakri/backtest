from typing import Dict, Any


class StopLossManager:
    """Manages stop-loss orders based on risk parameters."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize stop-loss manager."""
        self.config = config
        self.stop_loss_multiplier = self.config.get("stop_loss_multiplier", 2.0)
        self.take_profit_multiplier = self.config.get("take_profit_multiplier", 3.0)

    def calculate_stop_loss(
        self, current_price: float, atr: float, direction: int
    ) -> float:
        """Calculate stop-loss price.

        Args:
            current_price: Current asset price
            atr: Average True Range
            direction: Trade direction (1 for long, -1 for short)

        Returns:
            Calculated stop-loss price
        """
        if direction > 0:
            stop_loss = current_price - (atr * self.stop_loss_multiplier)
        else:
            stop_loss = current_price + (atr * self.stop_loss_multiplier)
        return stop_loss

    def calculate_take_profit(
        self, current_price: float, atr: float, direction: int
    ) -> float:
        """Calculate take-profit price.

        Args:
            current_price: Current asset price
            atr: Average True Range
            direction: Trade direction (1 for long, -1 for short)

        Returns:
            Calculated take-profit price
        """
        if direction > 0:
            take_profit = current_price + (atr * self.take_profit_multiplier)
        else:
            take_profit = current_price - (atr * self.take_profit_multiplier)
        return take_profit
