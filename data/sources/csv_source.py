from typing import Dict, Any, Optional, List
import pandas as pd
from pathlib import Path
import logging
from data.sources.base import DataSource

logger = logging.getLogger(__name__)


class CSVDataSource(DataSource):
    """Data source for CSV files."""

    def __init__(
        self, name: str, data_dir: str, config: Optional[Dict[str, Any]] = None
    ):
        """Initialize CSV data source.

        Args:
            name: Source identifier
            data_dir: Directory containing CSV files
            config: Source configuration
        """
        super().__init__(name, config)
        self.data_dir = Path(data_dir)

        # Default configuration
        self.date_column = self.config.get("date_column", "date")
        self.symbol_column = self.config.get("symbol_column", "symbol")
        self.required_columns = self.config.get(
            "required_columns", ["open", "high", "low", "close", "volume"]
        )
        self.date_format = self.config.get("date_format", "%Y-%m-%d")
        self.file_pattern = self.config.get("file_pattern", "{symbol}.csv")

    def load(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Load data from CSV file.

        Args:
            symbol: Asset symbol
            start_date: Start date for data
            end_date: End date for data
            **kwargs: Additional parameters

        Returns:
            DataFrame with market data
        """
        # Construct file path
        file_path = self.data_dir / self.file_pattern.format(symbol=symbol)

        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")

        # Load data
        try:
            data = pd.read_csv(file_path)

            # Convert date column
            data[self.date_column] = pd.to_datetime(
                data[self.date_column], format=self.date_format
            )

            # Add symbol if not present
            if self.symbol_column not in data.columns:
                data[self.symbol_column] = symbol

            # Filter by date range
            if start_date:
                data = data[data[self.date_column] >= pd.to_datetime(start_date)]
            if end_date:
                data = data[data[self.date_column] <= pd.to_datetime(end_date)]

            # Sort by date
            data = data.sort_values(self.date_column)

            # Update metadata
            self.update_metadata(
                symbol=symbol,
                start_date=data[self.date_column].min(),
                end_date=data[self.date_column].max(),
                rows=len(data),
                columns=list(data.columns),
            )

            return data

        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {e}")
            raise

    def validate(self, data: pd.DataFrame) -> bool:
        """Validate loaded data.

        Args:
            data: DataFrame to validate

        Returns:
            True if data is valid
        """
        # Check required columns
        missing_cols = set(self.required_columns) - set(data.columns)
        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            return False

        # Check date column
        if self.date_column not in data.columns:
            logger.error(f"Missing date column: {self.date_column}")
            return False

        # Check for missing values
        if data[self.required_columns].isnull().any().any():
            logger.error("Found missing values in required columns")
            return False

        # Check date sorting
        if not data[self.date_column].is_monotonic_increasing:
            logger.error("Dates are not monotonically increasing")
            return False

        return True

    def list_symbols(self) -> List[str]:
        """List available symbols.

        Returns:
            List of available symbols
        """
        symbols = []
        for file_path in self.data_dir.glob("*.csv"):
            try:
                # Extract symbol from filename
                symbol = file_path.stem
                symbols.append(symbol)
            except Exception as e:
                logger.warning(f"Error parsing symbol from {file_path}: {e}")

        return symbols

    def get_date_range(self, symbol: str) -> tuple[pd.Timestamp, pd.Timestamp]:
        """Get available date range for a symbol.

        Args:
            symbol: Asset symbol

        Returns:
            Tuple of (start_date, end_date)
        """
        data = self.load(symbol)
        return data[self.date_column].min(), data[self.date_column].max()
