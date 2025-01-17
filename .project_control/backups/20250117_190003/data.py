from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from logger import logger


class Data:
    """Class for handling market data."""

    def __init__(self, data: pd.DataFrame = None):
        """Initialize Data object.

        Args:
            data: Optional DataFrame with market data
        """
        self.data = data if data is not None else pd.DataFrame()

    def load_csv(self, filepath: str) -> None:
        """Load data from CSV file.

        Args:
            filepath: Path to CSV file
        """
        try:
            self.data = pd.read_csv(filepath)
            self.data.index = (
                pd.to_datetime(self.data["Date"])
                if "Date" in self.data.columns
                else self.data.index
            )
        except Exception as e:
            logger.error(f"Error loading CSV file: {str(e)}")
            raise

    def add_technical_indicators(self) -> None:
        """Add technical indicators to the data."""
        try:
            # Simple Moving Averages
            self.data["SMA_20"] = self.data["Close"].rolling(window=20).mean()
            self.data["SMA_50"] = self.data["Close"].rolling(window=50).mean()

            # Exponential Moving Averages
            self.data["EMA_12"] = self.data["Close"].ewm(span=12).mean()
            self.data["EMA_26"] = self.data["Close"].ewm(span=26).mean()

            # MACD
            self.data["MACD"] = self.data["EMA_12"] - self.data["EMA_26"]
            self.data["Signal_Line"] = self.data["MACD"].ewm(span=9).mean()

            # RSI
            delta = self.data["Close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            self.data["RSI"] = 100 - (100 / (1 + rs))

            # Bollinger Bands
            self.data["BB_middle"] = self.data["Close"].rolling(window=20).mean()
            std = self.data["Close"].rolling(window=20).std()
            self.data["BB_upper"] = self.data["BB_middle"] + (std * 2)
            self.data["BB_lower"] = self.data["BB_middle"] - (std * 2)

        except Exception as e:
            logger.error(f"Error adding technical indicators: {str(e)}")
            raise

    def get_returns(self) -> pd.Series:
        """Calculate returns from price data.

        Returns:
            Series of returns
        """
        try:
            return self.data["Close"].pct_change()
        except Exception as e:
            logger.error(f"Error calculating returns: {str(e)}")
            return pd.Series()

    def get_volatility(self, window: int = 252) -> pd.Series:
        """Calculate rolling volatility.

        Args:
            window: Rolling window size

        Returns:
            Series of volatility values
        """
        try:
            returns = self.get_returns()
            return returns.rolling(window=window).std() * np.sqrt(window)
        except Exception as e:
            logger.error(f"Error calculating volatility: {str(e)}")
            return pd.Series()

    def get_sharpe_ratio(self, risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio.

        Args:
            risk_free_rate: Risk-free rate

        Returns:
            Sharpe ratio
        """
        try:
            returns = self.get_returns()
            excess_returns = returns - risk_free_rate
            if len(excess_returns) < 2:
                return 0.0
            return excess_returns.mean() / excess_returns.std() * np.sqrt(252)
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {str(e)}")
            return 0.0
