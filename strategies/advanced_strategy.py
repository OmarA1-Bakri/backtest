from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class TradeSignal:
    """Represents a trading signal."""

    symbol: str
    direction: int  # 1 for long, -1 for short, 0 for no position
    confidence: float
    target_price: float
    stop_loss: float
    position_size: float
    timestamp: pd.Timestamp
    metadata: Dict


class StrategyBase(ABC):
    """Base class for trading strategies."""

    @abstractmethod
    def generate_signals(
        self, data: pd.DataFrame, model_predictions: np.ndarray, **kwargs
    ) -> List[TradeSignal]:
        """Generate trading signals."""
        pass


class AdaptiveMLStrategy(StrategyBase):
    """Advanced ML-based trading strategy with adaptive features."""

    def __init__(
        self,
        confidence_threshold: float = 0.6,
        position_sizing_method: str = "kelly",
        stop_loss_atr_multiplier: float = 2.0,
        take_profit_atr_multiplier: float = 3.0,
        max_positions: int = 5,
        trend_following: bool = True,
    ):
        """Initialize the strategy.

        Args:
            confidence_threshold: Minimum confidence for trade entry
            position_sizing_method: Method for position sizing ('kelly', 'fixed', 'volatility')
            stop_loss_atr_multiplier: ATR multiplier for stop loss
            take_profit_atr_multiplier: ATR multiplier for take profit
            max_positions: Maximum number of concurrent positions
            trend_following: Whether to consider trend direction
        """
        self.confidence_threshold = confidence_threshold
        self.position_sizing_method = position_sizing_method
        self.stop_loss_atr_multiplier = stop_loss_atr_multiplier
        self.take_profit_atr_multiplier = take_profit_atr_multiplier
        self.max_positions = max_positions
        self.trend_following = trend_following

    def generate_signals(
        self, data: pd.DataFrame, model_predictions: np.ndarray, **kwargs
    ) -> List[TradeSignal]:
        """Generate trading signals based on ML predictions and market data.

        Args:
            data: Market data with technical indicators
            model_predictions: ML model predictions
            **kwargs: Additional parameters

        Returns:
            List of trading signals
        """
        signals = []

        for i, timestamp in enumerate(data.index[-len(model_predictions) :]):
            row = data.loc[timestamp]
            prediction = model_predictions[i]

            # Calculate trade direction and confidence
            direction, confidence = self._get_trade_direction(
                prediction, row, self.confidence_threshold
            )

            if direction != 0:  # If we have a valid signal
                # Calculate position size
                position_size = self._calculate_position_size(
                    direction, confidence, row, kwargs.get("capital", 100000)
                )

                # Calculate entry, stop loss, and target prices
                entry_price = row["Close"]
                stop_loss, target = self._calculate_price_levels(
                    direction, entry_price, row["ATR"]
                )

                # Create trade signal
                signal = TradeSignal(
                    symbol=kwargs.get("symbol", "UNKNOWN"),
                    direction=direction,
                    confidence=confidence,
                    target_price=target,
                    stop_loss=stop_loss,
                    position_size=position_size,
                    timestamp=timestamp,
                    metadata={
                        "entry_price": entry_price,
                        "atr": row["ATR"],
                        "rsi": row["RSI"],
                        "adx": row["ADX"],
                        "volume_ratio": row["Volume_Ratio"],
                    },
                )

                signals.append(signal)

        return signals

    def _get_trade_direction(
        self, prediction: float, data: pd.Series, threshold: float
    ) -> Tuple[int, float]:
        """Determine trade direction and confidence."""
        # Base confidence on model prediction
        confidence = abs(prediction)

        if confidence < threshold:
            return 0, 0.0

        # Initial direction based on prediction
        direction = 1 if prediction > 0 else -1

        if self.trend_following:
            # Consider trend indicators
            trend_score = self._calculate_trend_score(data)

            # Adjust or filter signals based on trend
            if (direction > 0 and trend_score < 0) or (
                direction < 0 and trend_score > 0
            ):
                confidence *= 0.5  # Reduce confidence if against trend
                if confidence < threshold:
                    return 0, 0.0

        return direction, confidence

    def _calculate_trend_score(self, data: pd.Series) -> float:
        """Calculate overall trend score."""
        trend_signals = [
            1 if data["Close"] > data["SMA_20"] else -1,
            1 if data["SMA_20"] > data["SMA_50"] else -1,
            1 if data["MACD"] > data["MACD_Signal"] else -1,
            1 if data["ADX"] > 25 else 0,  # Strong trend if ADX > 25
        ]

        return np.mean(trend_signals)

    def _calculate_position_size(
        self, direction: int, confidence: float, data: pd.Series, capital: float
    ) -> float:
        """Calculate position size based on selected method."""
        if self.position_sizing_method == "kelly":
            # Kelly Criterion-based sizing
            win_rate = 0.5 + (confidence - self.confidence_threshold)
            risk_ratio = self.take_profit_atr_multiplier / self.stop_loss_atr_multiplier
            kelly_fraction = win_rate - ((1 - win_rate) / risk_ratio)
            position_size = max(
                0.0, kelly_fraction * capital * 0.02
            )  # Max 2% risk per trade

        elif self.position_sizing_method == "volatility":
            # Volatility-based sizing
            vol_factor = 0.1 / data["Volatility"]  # Target 10% annualized volatility
            position_size = capital * vol_factor * confidence

        else:  # 'fixed'
            # Fixed percentage of capital
            position_size = capital * 0.02 * confidence  # Base size 2% of capital

        return min(position_size, capital * 0.1)  # Cap at 10% of capital

    def _calculate_price_levels(
        self, direction: int, entry_price: float, atr: float
    ) -> Tuple[float, float]:
        """Calculate stop loss and target prices."""
        if direction > 0:
            stop_loss = entry_price - (atr * self.stop_loss_atr_multiplier)
            target = entry_price + (atr * self.take_profit_atr_multiplier)
        else:
            stop_loss = entry_price + (atr * self.stop_loss_atr_multiplier)
            target = entry_price - (atr * self.take_profit_atr_multiplier)

        return stop_loss, target
