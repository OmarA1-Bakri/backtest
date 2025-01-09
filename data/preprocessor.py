from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ResampleFrequency(str, Enum):
    """Supported resampling frequencies."""

    MIN_1 = "1min"
    MIN_5 = "5min"
    MIN_15 = "15min"
    MIN_30 = "30min"
    HOUR_1 = "1H"
    HOUR_4 = "4H"
    DAY_1 = "1D"
    WEEK_1 = "1W"


class DataPreprocessor:
    """Data preprocessing and validation for market data."""

    def __init__(
        self,
        remove_outliers: bool = True,
        fill_gaps: bool = True,
        outlier_std_threshold: float = 3.0,
        min_volume_percentile: float = 1.0,
    ):
        """Initialize the preprocessor.

        Args:
            remove_outliers: Whether to remove price and volume outliers
            fill_gaps: Whether to fill missing data points
            outlier_std_threshold: Number of std devs for outlier detection
            min_volume_percentile: Minimum volume percentile to keep
        """
        self.remove_outliers = remove_outliers
        self.fill_gaps = fill_gaps
        self.outlier_std_threshold = outlier_std_threshold
        self.min_volume_percentile = min_volume_percentile

    def process_dataframe(
        self, df: pd.DataFrame, target_frequency: Optional[str] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """Process market data with validation and optional resampling.

        Args:
            df: Input DataFrame with OHLCV data
            target_frequency: Optional target frequency for resampling

        Returns:
            Tuple of (processed DataFrame, processing statistics)
        """
        stats = {
            "original_rows": len(df),
            "gaps_filled": 0,
            "outliers_removed": 0,
            "invalid_rows": 0,
        }

        # Validate data
        df, invalid_rows = self._validate_data(df)
        stats["invalid_rows"] = invalid_rows

        if self.remove_outliers:
            df, outliers = self._remove_outliers(df)
            stats["outliers_removed"] = outliers

        if self.fill_gaps:
            df, gaps = self._fill_gaps(df)
            stats["gaps_filled"] = gaps

        # Resample if requested
        if target_frequency:
            df = self._resample_data(df, target_frequency)

        stats["final_rows"] = len(df)
        return df, stats

    def _validate_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """Validate market data for consistency and correctness."""
        invalid_rows = 0

        # Check for required columns
        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Ensure proper ordering
        df = df.sort_index()

        # Remove rows with NaN values
        original_len = len(df)
        df = df.dropna(subset=required_cols)
        invalid_rows += original_len - len(df)

        # Validate price relationships
        price_valid = (
            (df["High"] >= df["Low"])
            & (df["High"] >= df["Open"])
            & (df["High"] >= df["Close"])
            & (df["Low"] <= df["Open"])
            & (df["Low"] <= df["Close"])
            & (df["Low"] > 0)
        )

        # Validate volume
        volume_valid = df["Volume"] >= 0

        # Remove invalid rows
        valid_mask = price_valid & volume_valid
        invalid_rows += (~valid_mask).sum()
        df = df[valid_mask]

        return df, invalid_rows

    def _remove_outliers(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """Remove price and volume outliers."""
        original_len = len(df)

        # Calculate rolling statistics for outlier detection
        price_cols = ["Open", "High", "Low", "Close"]

        for col in price_cols:
            rolling_mean = df[col].rolling(window=20, min_periods=1).mean()
            rolling_std = df[col].rolling(window=20, min_periods=1).std()

            lower_bound = rolling_mean - self.outlier_std_threshold * rolling_std
            upper_bound = rolling_mean + self.outlier_std_threshold * rolling_std

            df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]

        # Remove low volume outliers
        min_volume = np.percentile(df["Volume"], self.min_volume_percentile)
        df = df[df["Volume"] >= min_volume]

        outliers_removed = original_len - len(df)
        return df, outliers_removed

    def _fill_gaps(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """Fill missing data points in time series."""
        original_index = df.index

        # Determine frequency
        freq = pd.infer_freq(df.index)
        if not freq:
            # Try to infer from most common time delta
            deltas = df.index[1:] - df.index[:-1]
            freq = pd.Timedelta(deltas.mode()[0])

        # Create continuous index
        full_index = pd.date_range(start=df.index.min(), end=df.index.max(), freq=freq)

        # Reindex and forward fill
        df = df.reindex(full_index)
        df = df.fillna(method="ffill")

        gaps_filled = len(full_index) - len(original_index)
        return df, gaps_filled

    def _resample_data(self, df: pd.DataFrame, target_frequency: str) -> pd.DataFrame:
        """Resample OHLCV data to target frequency."""
        if target_frequency not in ResampleFrequency.__members__.values():
            raise ValueError(
                f"Unsupported frequency: {target_frequency}. "
                f"Supported frequencies: {list(ResampleFrequency.__members__.values())}"
            )

        resampler = df.resample(target_frequency)

        return pd.DataFrame(
            {
                "Open": resampler["Open"].first(),
                "High": resampler["High"].max(),
                "Low": resampler["Low"].min(),
                "Close": resampler["Close"].last(),
                "Volume": resampler["Volume"].sum(),
            }
        )

    @staticmethod
    def calculate_returns(df: pd.DataFrame, method: str = "log") -> pd.Series:
        """Calculate returns from price data.

        Args:
            df: DataFrame with OHLCV data
            method: Return calculation method ('log' or 'simple')

        Returns:
            Series of returns
        """
        if method == "log":
            return np.log(df["Close"] / df["Close"].shift(1))
        elif method == "simple":
            return df["Close"].pct_change()
        else:
            raise ValueError("Method must be 'log' or 'simple'")

    @staticmethod
    def calculate_volatility(
        df: pd.DataFrame, window: int = 20, annualize: bool = True
    ) -> pd.Series:
        """Calculate rolling volatility.

        Args:
            df: DataFrame with OHLCV data
            window: Rolling window size
            annualize: Whether to annualize the volatility

        Returns:
            Series of volatility values
        """
        returns = DataPreprocessor.calculate_returns(df)
        vol = returns.rolling(window=window).std()

        if annualize:
            # Assuming daily data, adjust as needed
            minutes_per_day = 1440  # For minute data
            vol = vol * np.sqrt(minutes_per_day)

        return vol
