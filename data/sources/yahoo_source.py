from typing import Dict, Any, Optional
import pandas as pd
import yfinance as yf
import logging
from datetime import datetime, timedelta
from .base import DataSource

logger = logging.getLogger(__name__)


class YahooDataSource(DataSource):
    """Data source for Yahoo Finance."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize Yahoo Finance data source.

        Args:
            name: Source identifier
            config: Source configuration
        """
        super().__init__(name, config)

        # Default configuration
        self.interval = self.config.get("interval", "1d")
        self.prepost = self.config.get("prepost", False)
        self.auto_adjust = self.config.get("auto_adjust", True)
        self.cache_data = self.config.get("cache_data", True)
        self.cache = {}

    def load(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Load data from Yahoo Finance.

        Args:
            symbol: Asset symbol
            start_date: Start date for data
            end_date: End date for data
            **kwargs: Additional parameters

        Returns:
            DataFrame with market data
        """
        # Check cache
        cache_key = f"{symbol}_{start_date}_{end_date}"
        if self.cache_data and cache_key in self.cache:
            return self.cache[cache_key].copy()

        try:
            # Create ticker object
            ticker = yf.Ticker(symbol)

            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if not start_date:
                start_date = (pd.to_datetime(end_date) - timedelta(days=365)).strftime(
                    "%Y-%m-%d"
                )

            # Download data
            data = ticker.history(
                start=start_date,
                end=end_date,
                interval=self.interval,
                prepost=self.prepost,
                auto_adjust=self.auto_adjust,
            )

            # Reset index to make date a column
            data = data.reset_index()

            # Rename columns to match standard format
            data = data.rename(
                columns={
                    "Date": "date",
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Volume": "volume",
                }
            )

            # Add symbol column
            data["symbol"] = symbol

            # Update metadata
            self.update_metadata(
                symbol=symbol,
                start_date=data["date"].min(),
                end_date=data["date"].max(),
                rows=len(data),
                columns=list(data.columns),
                info=ticker.info,
            )

            # Cache data if enabled
            if self.cache_data:
                self.cache[cache_key] = data.copy()

            return data

        except Exception as e:
            logger.error(f"Error loading data for {symbol}: {e}")
            raise

    def validate(self, data: pd.DataFrame) -> bool:
        """Validate loaded data.

        Args:
            data: DataFrame to validate

        Returns:
            True if data is valid
        """
        required_columns = ["date", "open", "high", "low", "close", "volume"]

        # Check required columns
        missing_cols = set(required_columns) - set(data.columns)
        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            return False

        # Check for missing values
        if data[required_columns].isnull().any().any():
            logger.error("Found missing values in required columns")
            return False

        # Check date sorting
        if not data["date"].is_monotonic_increasing:
            logger.error("Dates are not monotonically increasing")
            return False

        return True

    def get_info(self, symbol: str) -> Dict[str, Any]:
        """Get additional information about a symbol.

        Args:
            symbol: Asset symbol

        Returns:
            Dictionary of symbol information
        """
        try:
            ticker = yf.Ticker(symbol)
            return ticker.info
        except Exception as e:
            logger.error(f"Error getting info for {symbol}: {e}")
            return {}

    def clear_cache(self) -> None:
        """Clear the data cache."""
        self.cache.clear()
        logger.info("Cache cleared")
