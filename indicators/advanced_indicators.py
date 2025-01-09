from typing import Optional, List, Dict
import pandas as pd
import numpy as np
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import talib
from enum import Enum


class IndicatorCategory(str, Enum):
    """Categories of technical indicators."""

    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    PATTERN = "pattern"
    CUSTOM = "custom"


@dataclass
class IndicatorConfig:
    """Configuration for technical indicators."""

    name: str
    category: IndicatorCategory
    params: Dict
    columns: List[str]


class AdvancedIndicators:
    """Advanced technical indicator calculations with parallel processing."""

    def __init__(self, max_workers: int = 4, chunk_size: int = 10000):
        """Initialize indicator calculator.

        Args:
            max_workers: Maximum number of parallel workers
            chunk_size: Size of data chunks for parallel processing
        """
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self._register_indicators()

    def _register_indicators(self):
        """Register available indicators with their configurations."""
        self.indicators = {
            # Trend Indicators
            "SUPERTREND": IndicatorConfig(
                name="SUPERTREND",
                category=IndicatorCategory.TREND,
                params={"period": 10, "multiplier": 3},
                columns=["supertrend", "supertrend_direction"],
            ),
            "ICHIMOKU": IndicatorConfig(
                name="ICHIMOKU",
                category=IndicatorCategory.TREND,
                params={"tenkan": 9, "kijun": 26, "senkou": 52},
                columns=["tenkan", "kijun", "senkou_a", "senkou_b", "chikou"],
            ),
            # Momentum Indicators
            "TSI": IndicatorConfig(
                name="TSI",
                category=IndicatorCategory.MOMENTUM,
                params={"fast": 13, "slow": 25},
                columns=["tsi", "tsi_signal"],
            ),
            "SQUEEZE_MOMENTUM": IndicatorConfig(
                name="SQUEEZE_MOMENTUM",
                category=IndicatorCategory.MOMENTUM,
                params={"bb_length": 20, "kc_length": 20, "kc_mult": 2},
                columns=["squeeze_on", "momentum"],
            ),
            # Volatility Indicators
            "KELTNER": IndicatorConfig(
                name="KELTNER",
                category=IndicatorCategory.VOLATILITY,
                params={"period": 20, "atr_period": 10, "multiplier": 2},
                columns=["kc_middle", "kc_upper", "kc_lower"],
            ),
            "VIX_FIX": IndicatorConfig(
                name="VIX_FIX",
                category=IndicatorCategory.VOLATILITY,
                params={"period": 22},
                columns=["vix_fix"],
            ),
            # Volume Indicators
            "ACCUMULATION_DISTRIBUTION": IndicatorConfig(
                name="ACCUMULATION_DISTRIBUTION",
                category=IndicatorCategory.VOLUME,
                params={"period": 21},
                columns=["ad_line", "ad_signal"],
            ),
            "VOLUME_PROFILE": IndicatorConfig(
                name="VOLUME_PROFILE",
                category=IndicatorCategory.VOLUME,
                params={"bins": 24},
                columns=["value_area_high", "value_area_low", "poc"],
            ),
        }

    def calculate_all(
        self,
        df: pd.DataFrame,
        indicators: Optional[List[str]] = None,
        parallel: bool = True,
    ) -> pd.DataFrame:
        """Calculate multiple indicators in parallel.

        Args:
            df: OHLCV DataFrame
            indicators: List of indicator names to calculate
            parallel: Whether to use parallel processing

        Returns:
            DataFrame with added indicator columns
        """
        if indicators is None:
            indicators = list(self.indicators.keys())

        if parallel and len(df) >= self.chunk_size:
            return self._parallel_calculate(df, indicators)
        else:
            return self._sequential_calculate(df, indicators)

    def _parallel_calculate(
        self, df: pd.DataFrame, indicators: List[str]
    ) -> pd.DataFrame:
        """Calculate indicators in parallel using chunks."""
        # Split data into chunks
        chunks = np.array_split(df, max(1, len(df) // self.chunk_size))
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self._sequential_calculate, chunk, indicators)
                for chunk in chunks
            ]

            for future in as_completed(futures):
                results.append(future.result())

        return pd.concat(results)

    def _sequential_calculate(
        self, df: pd.DataFrame, indicators: List[str]
    ) -> pd.DataFrame:
        """Calculate indicators sequentially."""
        result = df.copy()

        for ind_name in indicators:
            if ind_name not in self.indicators:
                continue

            config = self.indicators[ind_name]
            method = getattr(self, f"_calculate_{ind_name.lower()}")
            ind_df = method(result, **config.params)

            for col in config.columns:
                result[f"{ind_name}_{col}"] = ind_df[col]

        return result

    def _calculate_supertrend(
        self, df: pd.DataFrame, period: int = 10, multiplier: float = 3.0
    ) -> pd.DataFrame:
        """Calculate SuperTrend indicator."""
        atr = talib.ATR(df["High"], df["Low"], df["Close"], timeperiod=period)

        # Calculate basic upper and lower bands
        basic_upper = (df["High"] + df["Low"]) / 2 + multiplier * atr
        basic_lower = (df["High"] + df["Low"]) / 2 - multiplier * atr

        # Initialize SuperTrend
        supertrend = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=int)

        # Calculate SuperTrend values
        for i in range(1, len(df)):
            if df["Close"].iloc[i] > supertrend.iloc[i - 1]:
                supertrend.iloc[i] = max(basic_lower.iloc[i], supertrend.iloc[i - 1])
                direction.iloc[i] = 1
            else:
                supertrend.iloc[i] = min(basic_upper.iloc[i], supertrend.iloc[i - 1])
                direction.iloc[i] = -1

        return pd.DataFrame(
            {"supertrend": supertrend, "supertrend_direction": direction}
        )

    def _calculate_ichimoku(
        self, df: pd.DataFrame, tenkan: int = 9, kijun: int = 26, senkou: int = 52
    ) -> pd.DataFrame:
        """Calculate Ichimoku Cloud indicator."""
        # Calculate conversion line (Tenkan-sen)
        high_tenkan = df["High"].rolling(window=tenkan).max()
        low_tenkan = df["Low"].rolling(window=tenkan).min()
        tenkan_sen = (high_tenkan + low_tenkan) / 2

        # Calculate base line (Kijun-sen)
        high_kijun = df["High"].rolling(window=kijun).max()
        low_kijun = df["Low"].rolling(window=kijun).min()
        kijun_sen = (high_kijun + low_kijun) / 2

        # Calculate leading span A (Senkou span A)
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun)

        # Calculate leading span B (Senkou span B)
        high_senkou = df["High"].rolling(window=senkou).max()
        low_senkou = df["Low"].rolling(window=senkou).min()
        senkou_span_b = ((high_senkou + low_senkou) / 2).shift(kijun)

        # Calculate lagging span (Chikou span)
        chikou_span = df["Close"].shift(-kijun)

        return pd.DataFrame(
            {
                "tenkan": tenkan_sen,
                "kijun": kijun_sen,
                "senkou_a": senkou_span_a,
                "senkou_b": senkou_span_b,
                "chikou": chikou_span,
            }
        )

    def _calculate_tsi(
        self, df: pd.DataFrame, fast: int = 13, slow: int = 25
    ) -> pd.DataFrame:
        """Calculate True Strength Index."""
        diff = df["Close"].diff()

        # First smoothing
        diff_smooth1 = diff.ewm(span=slow, adjust=False).mean()
        abs_diff_smooth1 = abs(diff).ewm(span=slow, adjust=False).mean()

        # Second smoothing
        diff_smooth2 = diff_smooth1.ewm(span=fast, adjust=False).mean()
        abs_diff_smooth2 = abs_diff_smooth1.ewm(span=fast, adjust=False).mean()

        # Calculate TSI
        tsi = 100 * (diff_smooth2 / abs_diff_smooth2)
        tsi_signal = tsi.ewm(span=13, adjust=False).mean()

        return pd.DataFrame({"tsi": tsi, "tsi_signal": tsi_signal})

    def _calculate_squeeze_momentum(
        self,
        df: pd.DataFrame,
        bb_length: int = 20,
        kc_length: int = 20,
        kc_mult: float = 2.0,
    ) -> pd.DataFrame:
        """Calculate Squeeze Momentum indicator."""
        # Calculate Bollinger Bands
        bb_mid = df["Close"].rolling(window=bb_length).mean()
        bb_std = df["Close"].rolling(window=bb_length).std()
        bb_upper = bb_mid + 2 * bb_std
        bb_lower = bb_mid - 2 * bb_std

        # Calculate Keltner Channels
        tr = pd.DataFrame(
            {
                "tr1": df["High"] - df["Low"],
                "tr2": abs(df["High"] - df["Close"].shift()),
                "tr3": abs(df["Low"] - df["Close"].shift()),
            }
        ).max(axis=1)

        atr = tr.rolling(window=kc_length).mean()
        kc_mid = df["Close"].rolling(window=kc_length).mean()
        kc_upper = kc_mid + kc_mult * atr
        kc_lower = kc_mid - kc_mult * atr

        # Calculate squeeze
        squeeze_on = (bb_upper <= kc_upper) & (bb_lower >= kc_lower)

        # Calculate momentum
        highest = df["High"].rolling(window=kc_length).max()
        lowest = df["Low"].rolling(window=kc_length).min()
        momentum = df["Close"] - (highest + lowest) / 2

        return pd.DataFrame({"squeeze_on": squeeze_on, "momentum": momentum})

    def _calculate_vix_fix(self, df: pd.DataFrame, period: int = 22) -> pd.DataFrame:
        """Calculate VIX Fix indicator."""
        close = df["Close"]
        high = df["High"].rolling(window=period).max()
        low = df["Low"].rolling(window=period).min()

        vix_fix = 100 * (close - low) / (high - low)

        return pd.DataFrame({"vix_fix": vix_fix})

    def _calculate_volume_profile(
        self, df: pd.DataFrame, bins: int = 24
    ) -> pd.DataFrame:
        """Calculate Volume Profile."""
        price_range = df["High"].max() - df["Low"].min()
        bin_size = price_range / bins

        # Create price bins
        price_bins = np.linspace(df["Low"].min(), df["High"].max(), bins + 1)

        # Calculate volume for each price level
        volume_profile = np.zeros(bins)
        for i in range(len(df)):
            price = df["Close"].iloc[i]
            volume = df["Volume"].iloc[i]
            bin_idx = int((price - df["Low"].min()) / bin_size)
            if 0 <= bin_idx < bins:
                volume_profile[bin_idx] += volume

        # Find POC (Point of Control)
        poc_idx = np.argmax(volume_profile)
        poc = price_bins[poc_idx]

        # Calculate Value Area (70% of volume)
        total_volume = np.sum(volume_profile)
        target_volume = 0.7 * total_volume
        current_volume = volume_profile[poc_idx]

        upper_idx = lower_idx = poc_idx
        while current_volume < target_volume and (
            upper_idx < bins - 1 or lower_idx > 0
        ):
            if upper_idx < bins - 1:
                upper_idx += 1
                current_volume += volume_profile[upper_idx]
            if lower_idx > 0 and current_volume < target_volume:
                lower_idx -= 1
                current_volume += volume_profile[lower_idx]

        value_area_high = price_bins[upper_idx]
        value_area_low = price_bins[lower_idx]

        return pd.DataFrame(
            {
                "value_area_high": pd.Series(value_area_high, index=df.index),
                "value_area_low": pd.Series(value_area_low, index=df.index),
                "poc": pd.Series(poc, index=df.index),
            }
        )
