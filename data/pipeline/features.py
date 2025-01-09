from typing import Dict, Any, Optional, List, Union, Callable
import pandas as pd
import numpy as np
import talib
import logging

logger = logging.getLogger(__name__)


def add_technical_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """Add technical indicators to data.

    Args:
        data: Input DataFrame

    Returns:
        DataFrame with technical indicators
    """
    df = data.copy()

    try:
        # Price-based indicators
        df["ema_9"] = talib.EMA(df["close"], timeperiod=9)
        df["ema_21"] = talib.EMA(df["close"], timeperiod=21)
        df["ema_50"] = talib.EMA(df["close"], timeperiod=50)
        df["ema_200"] = talib.EMA(df["close"], timeperiod=200)

        # Momentum indicators
        df["rsi"] = talib.RSI(df["close"], timeperiod=14)
        df["macd"], df["macd_signal"], df["macd_hist"] = talib.MACD(
            df["close"], fastperiod=12, slowperiod=26, signalperiod=9
        )

        # Volatility indicators
        df["atr"] = talib.ATR(df["high"], df["low"], df["close"], timeperiod=14)
        df["bollinger_upper"], df["bollinger_middle"], df["bollinger_lower"] = (
            talib.BBANDS(df["close"], timeperiod=20, nbdevup=2, nbdevdn=2)
        )

        # Volume indicators
        df["obv"] = talib.OBV(df["close"], df["volume"])
        df["adl"] = talib.AD(df["high"], df["low"], df["close"], df["volume"])

        # Trend indicators
        df["adx"] = talib.ADX(df["high"], df["low"], df["close"], timeperiod=14)
        df["cci"] = talib.CCI(df["high"], df["low"], df["close"], timeperiod=14)

    except Exception as e:
        logger.error(f"Error calculating technical indicators: {e}")
        raise

    return df


def add_price_patterns(data: pd.DataFrame) -> pd.DataFrame:
    """Add candlestick pattern indicators.

    Args:
        data: Input DataFrame

    Returns:
        DataFrame with pattern indicators
    """
    df = data.copy()

    try:
        # Reversal patterns
        df["doji"] = talib.CDLDOJI(df["open"], df["high"], df["low"], df["close"])
        df["hammer"] = talib.CDLHAMMER(df["open"], df["high"], df["low"], df["close"])
        df["shooting_star"] = talib.CDLSHOOTINGSTAR(
            df["open"], df["high"], df["low"], df["close"]
        )

        # Continuation patterns
        df["engulfing"] = talib.CDLENGULFING(
            df["open"], df["high"], df["low"], df["close"]
        )
        df["harami"] = talib.CDLHARAMI(df["open"], df["high"], df["low"], df["close"])

    except Exception as e:
        logger.error(f"Error calculating price patterns: {e}")
        raise

    return df


def add_regime_features(data: pd.DataFrame) -> pd.DataFrame:
    """Add market regime indicators.

    Args:
        data: Input DataFrame

    Returns:
        DataFrame with regime indicators
    """
    df = data.copy()

    try:
        # Trend strength
        df["trend_strength"] = abs(df["close"].pct_change(20)) / (
            df["close"].pct_change(20).rolling(window=20).std() + 1e-8
        )

        # Trend direction
        df["trend_direction"] = np.sign(df["close"].pct_change(20))

        # Combined trend indicator
        df["trend_indicator"] = df["trend_strength"] * df["trend_direction"]

        # Volatility regime
        df["volatility_regime"] = pd.qcut(
            df["close"].pct_change().rolling(window=20).std(),
            q=3,
            labels=["low", "medium", "high"],
        )

        # Volume regime
        df["volume_regime"] = pd.qcut(
            df["volume"].rolling(window=20).mean(),
            q=3,
            labels=["low", "medium", "high"],
        )

        # Momentum regime
        df["momentum_regime"] = pd.qcut(
            df["close"].pct_change(20), q=3, labels=["bearish", "neutral", "bullish"]
        )

    except Exception as e:
        logger.error(f"Error calculating regime features: {e}")
        raise

    return df


def add_derived_features(data: pd.DataFrame) -> pd.DataFrame:
    """Add derived technical features.

    Args:
        data: Input DataFrame

    Returns:
        DataFrame with derived features
    """
    df = data.copy()

    try:
        # Price ratios
        df["close_to_ema9"] = df["close"] / df["ema_9"] - 1
        df["close_to_ema21"] = df["close"] / df["ema_21"] - 1
        df["close_to_ema50"] = df["close"] / df["ema_50"] - 1
        df["close_to_ema200"] = df["close"] / df["ema_200"] - 1

        # Volatility ratios
        df["atr_to_close"] = df["atr"] / df["close"]
        df["bb_width"] = (df["bollinger_upper"] - df["bollinger_lower"]) / df[
            "bollinger_middle"
        ]

        # Volume ratios
        df["volume_to_ma20"] = df["volume"] / df["volume"].rolling(window=20).mean()

        # Momentum combinations
        df["macd_rsi_signal"] = (df["macd"] > df["macd_signal"]).astype(int) * (
            df["rsi"] > 50
        ).astype(int)

    except Exception as e:
        logger.error(f"Error calculating derived features: {e}")
        raise

    return df
