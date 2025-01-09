from typing import Dict, List, Union
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class MarketDataService:
    """Service for loading and managing market data from CSV files."""

    def __init__(
        self,
        data_dir: Union[str, Path],
        cache_size: int = 100,
        datetime_format: str = "%Y-%m-%d %H:%M:%S",
    ):
        """Initialize the market data service.

        Args:
            data_dir: Directory containing CSV data files
            cache_size: Number of symbols to cache
            datetime_format: Format of datetime strings in CSV
        """
        self.data_dir = Path(data_dir)
        self.cache_size = cache_size
        self.datetime_format = datetime_format
        self._validate_data_directory()

    def _validate_data_directory(self) -> None:
        """Ensure data directory exists and contains CSV files."""
        if not self.data_dir.exists():
            raise ValueError(f"Data directory does not exist: {self.data_dir}")
        if not self.data_dir.is_dir():
            raise ValueError(f"Data path is not a directory: {self.data_dir}")
        if not list(self.data_dir.glob("*.csv")):
            raise ValueError(f"No CSV files found in directory: {self.data_dir}")

    @lru_cache(maxsize=100)
    def get_historical_data(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str = "1min",
    ) -> pd.DataFrame:
        """Load historical market data for a symbol from CSV.

        Args:
            symbol: Trading symbol (e.g., 'AAPL')
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Data interval ('1min', '5min', etc.)

        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Convert dates if needed
            if isinstance(start_date, str):
                start_date = pd.to_datetime(start_date)
            if isinstance(end_date, str):
                end_date = pd.to_datetime(end_date)

            # Find matching CSV file
            csv_path = self._find_data_file(symbol, interval)

            # Load and process data
            df = self._load_csv_data(csv_path, start_date, end_date)

            # Calculate additional features
            self._add_technical_indicators(df)

            return df

        except Exception as e:
            logger.error(f"Error loading data for {symbol}: {str(e)}")
            raise

    def _find_data_file(self, symbol: str, interval: str) -> Path:
        """Find the appropriate CSV file for the symbol and interval."""
        # Try different possible filename patterns
        patterns = [
            f"{symbol}_{interval}.csv",
            f"{symbol}.csv",
            f"{symbol.lower()}_{interval}.csv",
            f"{symbol.lower()}.csv",
            f"{symbol.upper()}_{interval}.csv",
            f"{symbol.upper()}.csv",
        ]

        for pattern in patterns:
            file_path = self.data_dir / pattern
            if file_path.exists():
                return file_path

        raise FileNotFoundError(
            f"No data file found for symbol {symbol} with interval {interval}"
        )

    def _load_csv_data(
        self, file_path: Path, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Load and process CSV data."""
        try:
            # Read CSV with automatic format detection
            df = pd.read_csv(file_path)

            # Try to identify datetime column
            datetime_cols = [
                col
                for col in df.columns
                if any(
                    time_kw in col.lower() for time_kw in ["time", "date", "timestamp"]
                )
            ]

            if not datetime_cols:
                raise ValueError(f"No datetime column found in {file_path.name}")

            # Set index to datetime
            df["timestamp"] = pd.to_datetime(
                df[datetime_cols[0]], format=self.datetime_format, errors="coerce"
            )
            df.set_index("timestamp", inplace=True)

            # Ensure required columns exist
            required_cols = ["Open", "High", "Low", "Close", "Volume"]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(
                    f"Missing required columns in {file_path.name}: {missing_cols}"
                )

            # Filter date range
            df = df[(df.index >= start_date) & (df.index <= end_date)]

            # Sort by timestamp
            df.sort_index(inplace=True)

            return df

        except Exception as e:
            logger.error(f"Error reading {file_path}: {str(e)}")
            raise

    def _add_technical_indicators(self, df: pd.DataFrame) -> None:
        """Add technical indicators to the dataframe.

        Args:
            df: DataFrame with OHLCV data
        """
        # Moving averages
        df["SMA_20"] = df["Close"].rolling(window=20).mean()
        df["SMA_50"] = df["Close"].rolling(window=50).mean()
        df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()

        # Volatility
        df["ATR"] = self._calculate_atr(df)
        df["Volatility"] = df["Close"].rolling(window=20).std()

        # Volume indicators
        df["Volume_SMA_20"] = df["Volume"].rolling(window=20).mean()
        df["Volume_Ratio"] = df["Volume"] / df["Volume_SMA_20"]

        # Momentum indicators
        df["RSI"] = self._calculate_rsi(df["Close"])
        df["MACD"], df["MACD_Signal"] = self._calculate_macd(df["Close"])

        # Trend indicators
        df["ADX"] = self._calculate_adx(df)

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high = df["High"]
        low = df["Low"]
        close = df["Close"]

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_macd(
        self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> tuple[pd.Series, pd.Series]:
        """Calculate MACD and Signal line."""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        return macd, signal_line

    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average Directional Index."""
        plus_dm = df["High"].diff()
        minus_dm = df["Low"].diff()

        plus_dm = plus_dm.where((plus_dm > 0) & (plus_dm > minus_dm.abs()), 0)
        minus_dm = minus_dm.abs().where((minus_dm > 0) & (minus_dm > plus_dm), 0)

        tr = self._calculate_atr(df, period)
        plus_di = 100 * (plus_dm.rolling(period).mean() / tr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / tr)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        return adx

    def get_latest_data(self, symbol: str, lookback_periods: int = 100) -> pd.DataFrame:
        """Get the most recent market data."""
        df = self.get_historical_data(
            symbol,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
        )
        return df.tail(lookback_periods)

    def get_multiple_symbols(
        self,
        symbols: List[str],
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
    ) -> Dict[str, pd.DataFrame]:
        """Load data for multiple symbols."""
        return {
            symbol: self.get_historical_data(symbol, start_date, end_date)
            for symbol in symbols
        }
