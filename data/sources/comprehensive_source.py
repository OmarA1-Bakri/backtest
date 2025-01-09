from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .base import DataSource
import logging

logger = logging.getLogger(__name__)


class ComprehensiveDataSource(DataSource):
    """Comprehensive data source."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize comprehensive data source.

        Args:
            name: Source identifier
            config: Source configuration
        """
        super().__init__(name, config)

    def load(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Load data from comprehensive source.

        Args:
            symbol: Asset symbol
            start_date: Start date for data
            end_date: End date for data
            **kwargs: Additional parameters

        Returns:
            DataFrame with market data
        """
        # For now, return sample data
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (pd.to_datetime(end_date) - timedelta(days=365)).strftime(
                "%Y-%m-%d"
            )
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        dates = pd.date_range(start=start, end=end, freq="D")
        data = pd.DataFrame(
            {
                "open": np.random.normal(100, 10, len(dates)),
                "high": np.random.normal(105, 10, len(dates)),
                "low": np.random.normal(95, 10, len(dates)),
                "close": np.random.normal(100, 10, len(dates)),
                "volume": np.random.normal(1000000, 100000, len(dates)),
            },
            index=dates,
        )
        data.index.name = "date"
        data = data.reset_index()
        data["symbol"] = symbol
        return data

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
