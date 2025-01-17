"""
Data processing utilities for the backtesting system.
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path
from functools import lru_cache

from data.market_data import MarketDataService
from logger import logger
from core import config
from numpy.lib.stride_tricks import sliding_window_view


def load_data(file_path: str) -> pd.DataFrame:
    """Load data from a CSV file."""
    try:
        df = pd.read_csv(file_path)
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        return df
    except Exception as e:
        logger.error(f"Error loading data from {file_path}: {str(e)}")
        raise


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add technical indicators to the dataframe."""
    try:
        df = df.copy()
        close = df["Close"] if "Close" in df.columns else df["CLOSE"]
        volume = df["Volume"] if "Volume" in df.columns else df["VOLUME"]

        # Add SMA
        df["SMA20"] = close.rolling(window=20).mean()
        df["SMA50"] = close.rolling(window=50).mean()

        # Add EMA
        df["EMA20"] = close.ewm(span=20, adjust=False).mean()

        # Add RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        # Add Bollinger Bands
        bb_middle = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        df["BB_middle"] = bb_middle
        df["BB_upper"] = bb_middle + 2 * bb_std
        df["BB_lower"] = bb_middle - 2 * bb_std

        # Add Volume indicators
        df["Volume_SMA"] = volume.rolling(window=20).mean()

        return df
    except Exception as e:
        logger.error(f"Error adding technical indicators: {str(e)}")
        raise


def add_technical_indicators_original(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add technical indicators to the dataframe.

    Args:
        df (pd.DataFrame): DataFrame with OHLCV data

    Returns:
        pd.DataFrame: DataFrame with added technical indicators
    """
    try:
        # Make a copy to avoid modifying the original
        df = df.copy()

        # Initialize MarketDataService
        market_data_service = MarketDataService(data_dir=config.data_dir)

        # Add technical indicators using MarketDataService
        market_data_service._add_technical_indicators(df)

        logger.info("Successfully added technical indicators")
        return df

    except Exception as e:
        logger.error(f"Error adding technical indicators: {e}")
        raise


def preprocess_data(
    df: pd.DataFrame,
    features: List[str],
    target: Optional[str] = None,
    lookback: int = 20,
) -> dict[str, np.ndarray]:
    """
    Preprocess data for model training or prediction.

    Args:
        df (pd.DataFrame): Input DataFrame
        features (List[str]): List of feature columns
        target (Optional[str]): Target column name
        lookback (int): Number of lookback periods

    Returns:
        Dict[str, np.ndarray]: Dictionary with preprocessed X and y arrays
    """
    try:
        # Check for NaN values in feature columns
        if df[features].isna().any().any():
            raise ValueError("NaN values found in feature columns")

        # Create feature matrix
        X = df[features].values

        # Create sequences for time series models
        if len(X) > lookback:
            X_seq = sliding_window_view(X, (lookback, X.shape[1]))
        else:
            X_seq = np.array([])

        result = {"X": X, "X_seq": X_seq}

        # Add target if provided and exists in columns
        if target is not None and target in df.columns:
            y = df[target].values[lookback:]
            if np.isnan(y).any():
                raise ValueError("NaN values found in target column")
            result["y"] = y

        logger.info(
            f"Successfully preprocessed data with shape: X={X.shape}, X_seq={X_seq.shape}"
        )
        return result

    except Exception as e:
        logger.error(f"Error preprocessing data: {e}")
        raise
