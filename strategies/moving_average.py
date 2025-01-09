"""Simple Moving Average Strategy."""

import pandas as pd
from typing import Dict, Any, List

from strategies.base import BaseStrategy
from logger import logger


class SimpleMAStrategy(BaseStrategy):
    """Simple Moving Average Strategy implementation."""

    # Define parameters as class variables
    short_window = 20
    long_window = 50
    trade_size = 1.0  # Default trade size

    def __init__(self, broker=None, data=None, params: Dict[str, Any] = None):
        """Initialize strategy with parameters."""
        super().__init__(broker, data, params)

    def generate_signals(self) -> Dict[str, Any]:
        """Generate trading signals based on moving averages.

        Returns:
            Dictionary containing signal information
        """
        try:
            # Get the last N prices where N is max window size
            lookback = max(self.short_window, self.long_window)
            logger.info(f"Lookback: {lookback}, Data length: {len(self.data.Close)}")

            if len(self.data.Close) < lookback:
                logger.warning(
                    f"Not enough data for moving averages. Need {lookback}, have {len(self.data.Close)}"
                )
                return {
                    "signal": 0,
                    "sma_short": None,
                    "sma_long": None,
                    "current_price": (
                        self.data.Close.iloc[-1] if len(self.data.Close) > 0 else None
                    ),
                }

            prices = self.data.Close.iloc[-lookback:]
            logger.info(f"Using {len(prices)} prices for calculation")

            # Calculate moving averages
            sma_short = prices.iloc[-self.short_window :].mean()
            sma_long = prices.iloc[-self.long_window :].mean()
            logger.info(f"SMA Short: {sma_short}, SMA Long: {sma_long}")

            # Generate signal
            signal = 0
            if sma_short > sma_long:
                signal = 1  # Buy signal
            elif sma_short < sma_long:
                signal = -1  # Sell signal

            result = {
                "signal": signal,
                "sma_short": sma_short,
                "sma_long": sma_long,
                "current_price": self.data.Close.iloc[-1],
            }
            logger.info(f"Generated signals: {result}")
            return result

        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            return {
                "signal": 0,
                "sma_short": None,
                "sma_long": None,
                "current_price": (
                    self.data.Close.iloc[-1] if len(self.data.Close) > 0 else None
                ),
            }

    def execute_trades(self, signals: Dict[str, Any]) -> None:
        """Execute trades based on signals.

        Args:
            signals: Dictionary containing signal information
        """
        try:
            signal = signals["signal"]
            current_price = signals["current_price"]

            # Execute trades based on signals and current position
            if signal == 1 and self.position <= 0:  # Buy signal
                self.buy(self.trade_size)
                self.log_trade("BUY", current_price, self.trade_size)

            elif signal == -1 and self.position >= 0:  # Sell signal
                self.sell(self.trade_size)
                self.log_trade("SELL", current_price, self.trade_size)

        except Exception as e:
            logger.error(f"Error executing trades: {e}")

    def calculate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate trading signals for backtesting.

        This method is used for testing and analysis, not live trading.

        Args:
            data: DataFrame with OHLCV data

        Returns:
            DataFrame with signals and indicators
        """
        df = data.copy()

        # Calculate moving averages
        df["SMA_short"] = df["CLOSE"].rolling(window=self.short_window).mean()
        df["SMA_long"] = df["CLOSE"].rolling(window=self.long_window).mean()

        # Generate signals
        df["signal"] = 0
        df.loc[df["SMA_short"] > df["SMA_long"], "signal"] = 1  # Buy signal
        df.loc[df["SMA_short"] < df["SMA_long"], "signal"] = -1  # Sell signal

        return df
