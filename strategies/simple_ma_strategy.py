"""Simple Moving Average Strategy."""

from typing import Dict, Any
import pandas as pd
import numpy as np
from strategies.base.base_strategy import BaseStrategy


class SimpleMAStrategy(BaseStrategy):
    """Simple Moving Average Strategy."""

    def __init__(
        self, broker, data: pd.DataFrame, params: Dict[str, Any], initial_cash: float
    ):
        """Initialize strategy."""
        super().__init__(broker, data, params)
        self.short_window = params.get("short_window", 5)
        self.long_window = params.get("long_window", 20)
        self.cash = initial_cash
        self.position = 0
        self.symbol = "default"  # Can be updated based on your needs

    def generate_signals(self) -> Dict[str, Any]:
        """Generate trading signals based on moving average crossovers."""
        # Calculate moving averages
        short_ma = self.data["Close"].rolling(window=self.short_window).mean()
        long_ma = self.data["Close"].rolling(window=self.long_window).mean()

        # Get latest values
        latest_short_ma = short_ma.iloc[-1]
        latest_long_ma = long_ma.iloc[-1]
        prev_short_ma = short_ma.iloc[-2]
        prev_long_ma = long_ma.iloc[-2]

        # Determine action based on crossover
        if latest_short_ma > latest_long_ma and prev_short_ma <= prev_long_ma:
            action = "buy"
            confidence = min(1.0, (latest_short_ma - latest_long_ma) / latest_long_ma)
        elif latest_short_ma < latest_long_ma and prev_short_ma >= prev_long_ma:
            action = "sell"
            confidence = min(1.0, (latest_long_ma - latest_short_ma) / latest_long_ma)
        else:
            action = "hold"
            confidence = 0.5

        return {
            "action": action,
            "confidence": confidence,
            "short_ma": latest_short_ma,
            "long_ma": latest_long_ma,
        }

    def execute_trades(self, signals: Dict[str, Any]) -> None:
        """Execute trades based on signals."""
        action = signals.get("action", "hold")
        price = self.data["Close"].iloc[-1]

        if action == "buy" and self.position <= 0:  # Buy signal
            position_size = self.cash / price if price > 0 else 0
            if position_size > 0:
                self.broker.place_buy_order(
                    symbol=self.symbol,
                    quantity=position_size,
                    price=price,
                )
                self.position = position_size
                self.cash -= position_size * price

        elif action == "sell" and self.position > 0:  # Sell signal
            self.broker.place_sell_order(
                symbol=self.symbol,
                quantity=self.position,
                price=price,
            )
            self.cash += self.position * price
            self.position = 0

    def next(self) -> None:
        """Execute strategy for the next time step."""
        try:
            signals = self.generate_signals()
            self.execute_trades(signals)
        except Exception as e:
            self.logger.error(f"Error in strategy execution: {e}")

    def init(self) -> None:
        """Initialize strategy."""
        super().init()
        self.logger.info(
            f"Initialized SimpleMAStrategy with short_window={self.short_window}, "
            f"long_window={self.long_window}, initial_cash={self.cash}"
        )
