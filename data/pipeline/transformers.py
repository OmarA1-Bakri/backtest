from typing import Dict, Any, Optional, List, Union, Callable
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def clean_data(data: pd.DataFrame) -> pd.DataFrame:
    """Clean market data.

    Args:
        data: Input DataFrame

    Returns:
        Cleaned DataFrame
    """
    df = data.copy()

    try:
        # Sort by date
        df = df.sort_values("date")

        # Remove duplicates
        df = df.drop_duplicates(subset=["date", "symbol"])

        # Forward fill missing values
        df = df.fillna(method="ffill")

        # Remove remaining missing values
        df = df.dropna()

        # Ensure numeric types
        numeric_cols = ["open", "high", "low", "close", "volume"]
        df[numeric_cols] = df[numeric_cols].astype(float)

        # Remove zero or negative prices
        df = df[df[["open", "high", "low", "close"]].gt(0).all(axis=1)]

        # Remove zero volume
        df = df[df["volume"] > 0]

    except Exception as e:
        logger.error(f"Error cleaning data: {e}")
        raise

    return df


def normalize_data(data: pd.DataFrame) -> pd.DataFrame:
    """Normalize market data.

    Args:
        data: Input DataFrame

    Returns:
        Normalized DataFrame
    """
    df = data.copy()

    try:
        # Calculate returns
        price_cols = ["open", "high", "low", "close"]
        for col in price_cols:
            df[f"{col}_return"] = df[col].pct_change()

        # Normalize volume
        df["volume_normalized"] = df["volume"] / df["volume"].rolling(window=20).mean()

        # Z-score normalization for technical indicators
        indicator_cols = [
            col for col in df.columns if col.startswith(("rsi", "macd", "adx", "cci"))
        ]
        for col in indicator_cols:
            df[f"{col}_zscore"] = (df[col] - df[col].rolling(window=20).mean()) / df[
                col
            ].rolling(window=20).std()

    except Exception as e:
        logger.error(f"Error normalizing data: {e}")
        raise

    return df


def resample_data(data: pd.DataFrame, freq: str = "1D") -> pd.DataFrame:
    """Resample market data to different frequency.

    Args:
        data: Input DataFrame
        freq: Resampling frequency

    Returns:
        Resampled DataFrame
    """
    df = data.copy()

    try:
        # Set date as index
        df = df.set_index("date")

        # Define aggregation functions
        agg_dict = {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }

        # Add custom aggregations for technical indicators
        indicator_cols = [col for col in df.columns if col not in agg_dict]
        for col in indicator_cols:
            agg_dict[col] = "last"

        # Resample data
        df = df.resample(freq).agg(agg_dict)

        # Reset index
        df = df.reset_index()

    except Exception as e:
        logger.error(f"Error resampling data: {e}")
        raise

    return df


def filter_data(
    data: pd.DataFrame,
    min_price: float = 1.0,
    min_volume: float = 1000,
    min_volatility: float = 0.001,
) -> pd.DataFrame:
    """Filter market data based on criteria.

    Args:
        data: Input DataFrame
        min_price: Minimum price threshold
        min_volume: Minimum volume threshold
        min_volatility: Minimum volatility threshold

    Returns:
        Filtered DataFrame
    """
    df = data.copy()

    try:
        # Price filter
        df = df[df["close"] >= min_price]

        # Volume filter
        df = df[df["volume"] >= min_volume]

        # Volatility filter
        volatility = df["close"].pct_change().rolling(window=20).std()
        df = df[volatility >= min_volatility]

        # Remove any remaining gaps
        df = df.reset_index(drop=True)

    except Exception as e:
        logger.error(f"Error filtering data: {e}")
        raise

    return df
