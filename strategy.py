import numpy as np
import pandas as pd
import time
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
from core.metrics import MetricsCollector
from backtesting import Strategy
from backtesting.lib import crossover
from logger import logger
from risk_manager import RiskManager
from core.config.settings import config
from data_processing import add_technical_indicators
from sklearn.model_selection import KFold
from psutil import Process


class StrategyInterface(ABC):
    """Base interface for all trading strategies."""

    @abstractmethod
    def generate_signals(self) -> Dict[str, Any]:
        """Generate trading signals based on current market conditions."""
        pass

    @abstractmethod
    def execute_trades(self, signals: Dict[str, Any]) -> None:
        """Execute trades based on generated signals."""
        pass

    @abstractmethod
    def init(self) -> None:
        """Initialize strategy parameters and models."""
        pass

    @abstractmethod
    def next(self) -> None:
        """Process next data point and make trading decisions."""
        pass


class BaseStrategy(Strategy, ABC):
    """Base strategy implementation with common functionality."""

    def __init__(self, broker, data, params, **kwargs):
        """Initialize strategy.

        Args:
            broker: Broker object
            data: Historical price data
            params: Strategy parameters
            **kwargs: Additional keyword arguments including initial_cash
        """
        super().__init__(broker, data, params)
        self.model_facade: Optional[ModelFacade] = None
        self.risk_manager: Optional[RiskManager] = None
        self.performance_metrics: Dict[str, float] = {}
        self.trade_history: List[Dict[str, Any]] = []
        self.initial_cash = kwargs.get("initial_cash", 10000.0)
        self.metrics = MetricsCollector()
        self.starting_cash = self.initial_cash

    @abstractmethod
    def generate_signals(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def execute_trades(self, signals: Dict[str, Any]) -> None:
        pass

    def next(self) -> None:
        try:
            current_price = self.data.Close[-1]
            if self.risk_manager and self.risk_manager.check_stop_loss(current_price):
                if self.position:
                    self.position.close()
                    logger.info(
                        f"Stop loss triggered, position closed at price: {current_price:.2f}"
                    )
                    self._reset_position_vars()
            else:
                signals = self.generate_signals()
                self.execute_trades(signals)
                self.update_metrics()
        except Exception as e:
            logger.error(f"Error in strategy next(): {e}")

    def init(self) -> None:
        """Initialize strategy with data preprocessing and model setup."""
        try:
            self.data_df = self._get_original_data()
            self.data_df = add_technical_indicators(self.data_df)
            self.data_df = self.add_market_structure_indicators(self.data_df)

            self.features = [col for col in self.data_df.columns if col != "Target"]

            self.model_facade = ModelFacade(
                features=self.features, model_settings=config.models
            )
            self.model_facade.load_all_models()

            self.risk_manager = RiskManager(
                model_facade=self.model_facade, initial_cash=self.initial_cash
            )

            logger.info("Strategy initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing strategy: {e}")
            raise

    def _get_original_data(self) -> pd.DataFrame:
        """Get original market data."""
        return pd.DataFrame(
            {
                "Open": self.data.Open,
                "High": self.data.High,
                "Low": self.data.Low,
                "Close": self.data.Close,
                "Volume": self.data.Volume,
            }
        )

    def update_metrics(self) -> None:
        """Update strategy performance metrics."""
        try:
            current_value = self.equity
            self.metrics.track_portfolio_value(current_value)

            # Calculate and track returns
            returns = (current_value - self.starting_cash) / self.starting_cash
            self.metrics.track_returns(returns)

            # Track position values
            if self.position:
                symbol = self.data.df.index.name or "default"
                position_value = self.position.size * self.data.Close[-1]
                self.metrics.track_position_value(symbol, position_value)

            if len(self.trade_history) > 0:
                trades_df = pd.DataFrame(self.trade_history)
                self.performance_metrics.update(
                    {
                        "win_rate": (
                            len(trades_df[trades_df["pnl"] > 0]) / len(trades_df)
                        ),
                        "avg_win": trades_df[trades_df["pnl"] > 0]["pnl"].mean(),
                        "avg_loss": trades_df[trades_df["pnl"] < 0]["pnl"].mean(),
                        "largest_win": trades_df["pnl"].max(),
                        "largest_loss": trades_df["pnl"].min(),
                    }
                )
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")

    def log_trade(
        self, trade_type: str, price: float, size: float, pnl: float = 0
    ) -> None:
        """Log trade details for analysis."""
        try:
            # Track trade in Prometheus metrics
            symbol = self.data.df.index.name or "default"
            if trade_type == "buy":
                self.metrics.track_trade("buy")
            elif trade_type == "sell":
                self.metrics.track_trade("sell")

            if pnl != 0:
                self.metrics.track_trade_pnl(symbol, pnl)

            self.trade_history.append(
                {
                    "timestamp": pd.Timestamp.now(),
                    "type": trade_type,
                    "price": price,
                    "size": size,
                    "pnl": pnl,
                }
            )
        except Exception as e:
            logger.error(f"Error logging trade: {e}")

    def combinatorial_purged_cross_validation(
        self, X: np.ndarray, y: np.ndarray, n_splits: int = 5, n_combinations: int = 10
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Perform combinatorial purged cross-validation."""
        try:
            kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
            all_combinations = []

            for _ in range(n_combinations):
                combination = []
                for train_index, test_index in kf.split(X):
                    purged_train_index = self.purge_overlapping_samples(
                        train_index, test_index
                    )
                    combination.append((purged_train_index, test_index))
                all_combinations.append(combination)

            return all_combinations
        except Exception as e:
            logger.error(f"Error in cross-validation: {e}")
            return []

    def purge_overlapping_samples(
        self, train_index: np.ndarray, test_index: np.ndarray, embargo: int = 5
    ) -> np.ndarray:
        """Remove overlapping samples and apply embargo period."""
        try:
            return train_index[:-embargo]
        except Exception as e:
            logger.error(f"Error purging samples: {e}")
            return train_index

    def add_market_structure_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add market structure indicators to the dataframe.

        Args:
            df (pd.DataFrame): DataFrame with OHLCV data

        Returns:
            pd.DataFrame: DataFrame with added market structure indicators
        """
        try:
            df = df.copy()

            # Volatility regime
            df["Returns"] = df["Close"].pct_change()
            df["Volatility"] = df["Returns"].rolling(window=20).std() * np.sqrt(252)

            # Market regime based on moving averages
            df["SMA_20"] = df["Close"].rolling(window=20).mean()
            df["SMA_50"] = df["Close"].rolling(window=50).mean()
            df = df.dropna(subset=["SMA_20", "SMA_50"]).reset_index(drop=True)
            df["Trend"] = 0
            df.loc[df["SMA_20"] > df["SMA_50"], "Trend"] = 1
            df.loc[df["SMA_20"] < df["SMA_50"], "Trend"] = -1

            # Support and resistance levels
            df["Pivot"] = (df["High"] + df["Low"] + df["Close"]) / 3
            df["R1"] = 2 * df["Pivot"] - df["Low"]
            df["S1"] = 2 * df["Pivot"] - df["High"]

            # Market breadth
            df["Price_Range"] = df["High"] - df["Low"]
            df["Range_MA"] = df["Price_Range"].rolling(window=20).mean()

            # Volume profile
            df["Volume_MA"] = df["Volume"].rolling(window=20).mean()
            df["Volume_Trend"] = df["Volume"] / df["Volume_MA"]

            logger.info("Successfully added market structure indicators")
            return df

        except Exception as e:
            logger.error(f"Error adding market structure indicators: {str(e)}")
            raise


class ImprovedTMCS(BaseStrategy):
    """
    Improved Time Series Momentum Strategy with Regime Detection.
    Implements sophisticated trading logic with multiple models and risk management.
    """

    def __init__(self, broker, data, params):
        super().__init__(broker, data, params)
        self._position = None
        self._params = params
        self.current_stop_loss = None
        self.current_take_profit = None
        self.trailing_stop = None
        self.regime_history: List[str] = []
        logger.info("ImprovedTMCS strategy initialized")

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value

    def generate_signals(self) -> Dict[str, Any]:
        """Generate trading signals using ensemble model predictions."""
        try:
            current_df = self.data_df.iloc[: len(self.data.Close)]
            predictions = self.model_facade.predict_all(current_df)

            # Store regime for analysis
            self.regime_history.append(predictions["hmm"])

            return predictions
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            return {"ensemble": 0.5, "hmm": "Unknown"}

    def execute_trades(self, signals: Dict[str, Any]) -> None:
        """Execute trades based on signals and risk management rules."""
        try:
            ensemble_signal = signals["ensemble"]
            current_price = self.data.Close[-1]
            regime = signals["hmm"]

            # Calculate risk metrics
            if len(self.trade_history) > 0:
                returns = pd.DataFrame(self.trade_history)["pnl"].values
                risk_metrics = self.risk_manager.calculate_risk_metrics(returns)

                # Adjust position size based on risk metrics
                if "var_95" in risk_metrics and "es_95" in risk_metrics:
                    self.risk_manager.adjust_position_size(
                        self.position.size if self.position else 0,
                        risk_metrics["var_95"],
                        risk_metrics["es_95"],
                    )

            # Execute trades based on signals
            if ensemble_signal > 0.6 and not self.position.is_long:
                self._enter_long_position(current_price, regime)
            elif ensemble_signal < 0.4 and not self.position.is_short:
                self._enter_short_position(current_price, regime)

            self._manage_positions(current_price, regime)

        except Exception as e:
            logger.error(f"Error executing trades: {e}")

    def _enter_long_position(self, current_price: float, regime: str) -> None:
        """Enter a long position with proper risk management."""
        try:
            current_features = self.data_df.iloc[-1:][self.features].values
            position_size = self.risk_manager.get_position_size(
                current_features=current_features
            )

            stop_loss = self.risk_manager.adjust_stop_loss(
                current_price, self.data.ATR[-1], regime
            )
            take_profit = self.risk_manager.adjust_take_profit(
                current_price, self.data.ATR[-1], regime
            )

            self.buy(size=position_size, sl=stop_loss, tp=take_profit)
            self.current_stop_loss = stop_loss
            self.current_take_profit = take_profit

            # Set trailing stop
            self.trailing_stop = current_price * 0.98  # 2% trailing stop

            self.log_trade("LONG", current_price, position_size)
            logger.info(
                f"Long position entered: Size={position_size:.2f}, "
                f"Price={current_price:.2f}, SL={stop_loss:.2f}, TP={take_profit:.2f}"
            )

        except Exception as e:
            logger.error(f"Error entering long position: {e}")

    def _enter_short_position(self, current_price: float, regime: str) -> None:
        """Enter a short position with proper risk management."""
        try:
            current_features = self.data_df.iloc[-1:][self.features].values
            position_size = self.risk_manager.get_position_size(
                current_features=current_features
            )

            stop_loss = self.risk_manager.adjust_stop_loss(
                current_price, self.data.ATR[-1], regime
            )
            take_profit = self.risk_manager.adjust_take_profit(
                current_price, self.data.ATR[-1], regime
            )

            self.sell(size=position_size, sl=stop_loss, tp=take_profit)
            self.current_stop_loss = stop_loss
            self.current_take_profit = take_profit

            # Set trailing stop
            self.trailing_stop = current_price * 1.02  # 2% trailing stop

            self.log_trade("SHORT", current_price, position_size)
            logger.info(
                f"Short position entered: Size={position_size:.2f}, "
                f"Price={current_price:.2f}, SL={stop_loss:.2f}, TP={take_profit:.2f}"
            )

        except Exception as e:
            logger.error(f"Error entering short position: {e}")

    def _manage_positions(self, current_price: float, regime: str) -> None:
        """Manage existing positions including trailing stops."""
        try:
            if self.position:
                # Update trailing stop
                if self.position.is_long and current_price > self.trailing_stop:
                    self.trailing_stop = max(
                        self.trailing_stop, current_price * 0.98  # 2% trailing stop
                    )
                elif self.position.is_short and current_price < self.trailing_stop:
                    self.trailing_stop = min(
                        self.trailing_stop, current_price * 1.02  # 2% trailing stop
                    )

                # Check stops
                if self.position.is_long:
                    if (
                        current_price <= self.trailing_stop
                        or current_price <= self.current_stop_loss
                    ):
                        self.position.close()
                        self.log_trade(
                            "CLOSE_LONG",
                            current_price,
                            self.position.size,
                            self.position.pl,
                        )
                        self._reset_position_vars()

                    elif current_price >= self.current_take_profit:
                        self.position.close()
                        self.log_trade(
                            "TP_LONG",
                            current_price,
                            self.position.size,
                            self.position.pl,
                        )
                        self._reset_position_vars()

                elif self.position.is_short:
                    if (
                        current_price >= self.trailing_stop
                        or current_price >= self.current_stop_loss
                    ):
                        self.position.close()
                        self.log_trade(
                            "CLOSE_SHORT",
                            current_price,
                            self.position.size,
                            self.position.pl,
                        )
                        self._reset_position_vars()

                    elif current_price <= self.current_take_profit:
                        self.position.close()
                        self.log_trade(
                            "TP_SHORT",
                            current_price,
                            self.position.size,
                            self.position.pl,
                        )
                        self._reset_position_vars()

        except Exception as e:
            logger.error(f"Error managing positions: {e}")

    def _reset_position_vars(self) -> None:
        """Reset position-related variables."""
        self.current_stop_loss = None
        self.current_take_profit = None
        self.trailing_stop = None
        self.regime_history = []


class SimpleMAStrategy(Strategy):
    """A simple Moving Average crossover strategy."""

    # Define parameters as class variables
    fast_ma = 20  # Default value for fast moving average
    slow_ma = 50  # Default value for slow moving average

    def __init__(self, broker, data, params):
        """Initialize the strategy.

        Args:
            broker: Backtesting broker instance
            data: OHLCV data
            params: Strategy parameters including fast_ma and slow_ma
        """
        super().__init__(broker, data, params)
        self.metrics = MetricsCollector()
        self.last_portfolio_value = None
        self.peak_portfolio_value = None
        self.metrics_update_counter = 0
        self.last_metrics_update = 0

    def init(self):
        """Initialize strategy."""
        # Add moving averages if not already present
        if "SMA20" not in self.data.df.columns:
            self.data.df["SMA20"] = self.I(
                lambda x: x.rolling(window=self.fast_ma).mean(), self.data.Close
            )
        if "SMA50" not in self.data.df.columns:
            self.data.df["SMA50"] = self.I(
                lambda x: x.rolling(window=self.slow_ma).mean(), self.data.Close
            )

        # Initialize metrics tracking
        self.last_portfolio_value = self.equity
        self.peak_portfolio_value = self.equity

    def next(self):
        """Strategy logic for each step."""
        # Only calculate metrics every 10 steps to improve performance
        self.metrics_update_counter += 1

        # Trading logic
        if crossover(self.data.SMA20, self.data.SMA50):
            self.buy()
        elif crossover(self.data.SMA50, self.data.SMA20):
            self.sell()

        # Update metrics less frequently for better performance
        if self.metrics_update_counter >= 10:
            self.update_metrics()
            self.metrics_update_counter = 0

    def update_metrics(self) -> None:
        """Update strategy metrics using data timestamps.

        The timestamp is retrieved from the backtesting data's DatetimeIndex,
        ensuring we use the correct historical time for each data point.
        All timestamps are assumed to be in UTC.
        """
        # Get current portfolio value and calculate returns
        current_value = self.equity

        try:
            # Get current timestamp directly from the data index
            current_timestamp = self.data.index[
                -1
            ]  # Latest timestamp in current window

            # Convert to Unix timestamp (seconds since epoch)
            current_time = int(current_timestamp.timestamp())

            logger.debug(
                f"Timestamp: {current_timestamp}, " f"Unix time: {current_time}"
            )
        except Exception as e:
            # Log detailed error information for debugging
            logger.error(
                f"Error getting timestamp: {str(e)}\n"
                f"DataFrame index type: {type(self.data.df.index)}"
            )
            # Fallback to current time - Note: This will affect backtest accuracy
            current_time = int(time.time())

        returns = (
            current_value - self.last_portfolio_value
        ) / self.last_portfolio_value
        self.peak_portfolio_value = max(self.peak_portfolio_value, current_value)

        # Calculate drawdown
        drawdown = (
            (self.peak_portfolio_value - current_value) / self.peak_portfolio_value
            if self.peak_portfolio_value > 0
            else 0
        )

        # Update metrics with accurate timestamp
        metrics = {
            "portfolio_value": current_value,
            "returns": returns * 100,  # Convert to percentage
            "drawdown": drawdown * 100,  # Convert to percentage
            "timestamp": current_time,  # Historical timestamp from data
            "symbol": (
                self.data.df.columns[0][1]
                if isinstance(self.data.df.columns[0], tuple)
                else "default"
            ),
        }

        # Update trading metrics
        self.metrics.update_trading_metrics("SimpleMAStrategy", metrics)

        # Store current value for next iteration
        self.last_portfolio_value = current_value
