"""Base strategy module."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import pandas as pd

from logger import logger


class BaseStrategy(ABC):
    """Base class for all trading strategies."""

    def __init__(self, broker=None, data=None, params: Dict[str, Any] = None):
        """Initialize strategy.

        Args:
            broker: Broker instance for executing trades
            data: Data source for prices and indicators
            params: Strategy parameters
        """
        self._broker = broker
        self._data = data
        self.trade_history: List[Dict[str, Any]] = []

        # Set default values
        self.cash = 0.0
        self.position = 0

        # Update with broker values if available
        if broker is not None:
            self.cash = getattr(broker, "equity", 0.0)
            self.position = getattr(broker, "position", 0)

        # Update parameters if provided
        if params:
            for name, value in params.items():
                setattr(self, name, value)

    @property
    def broker(self):
        """Get broker instance."""
        return self._broker

    @property
    def data(self):
        """Get data source."""
        return self._data

    @abstractmethod
    def generate_signals(self) -> Dict[str, Any]:
        """Generate trading signals.

        Returns:
            Dictionary containing signal information
        """
        pass

    @abstractmethod
    def execute_trades(self, signals: Dict[str, Any]) -> None:
        """Execute trades based on signals.

        Args:
            signals: Dictionary containing signal information
        """
        pass

    def buy(self, size: float) -> None:
        """Execute buy order.

        Args:
            size: Size of the order
        """
        try:
            if self.broker:
                self.broker.buy(size)
                self.position += size
        except Exception as e:
            logger.error(f"Error executing buy order: {e}")

    def sell(self, size: float) -> None:
        """Execute sell order.

        Args:
            size: Size of the order
        """
        try:
            if self.broker:
                self.broker.sell(size)
                self.position -= size
        except Exception as e:
            logger.error(f"Error executing sell order: {e}")

    def log_trade(self, trade_type: str, price: float, size: float) -> None:
        """Log trade to history.

        Args:
            trade_type: Type of trade (BUY/SELL)
            price: Trade price
            size: Trade size
        """
        self.trade_history.append(
            {
                "timestamp": pd.Timestamp.now(),
                "type": trade_type,
                "price": price,
                "size": size,
            }
        )
