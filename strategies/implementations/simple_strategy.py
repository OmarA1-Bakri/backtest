from typing import List, Dict, Any
from base.base_strategy import BaseStrategy
from backtesting.lib import crossover
from logger import logger


class SimpleMAStrategy(BaseStrategy):
    """
    Simple Moving Average Crossover Strategy.
    Implements a basic trading strategy based on the crossover of two SMAs.
    """

    def __init__(self, broker, data, params):
        super().__init__(broker, data, params)
        self.fast_ma = params.get("fast_ma", 20)
        self.slow_ma = params.get("slow_ma", 50)
        self.current_stop_loss = None
        self.current_take_profit = None
        self.trailing_stop = None
        self.regime_history: List[str] = []
        logger.info("SimpleMAStrategy initialized")

    def generate_signals(self) -> Dict[str, Any]:
        """Generate trading signals based on SMA crossover."""
        try:
            current_df = self.data_df.iloc[: len(self.data.Close)]
            fast_ma = current_df["Close"].rolling(window=self.fast_ma).mean()
            slow_ma = current_df["Close"].rolling(window=self.slow_ma).mean()

            if crossover(fast_ma, slow_ma):
                return {"signal": 1}  # Buy signal
            elif crossover(slow_ma, fast_ma):
                return {"signal": -1}  # Sell signal
            else:
                return {"signal": 0}  # No signal
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            return {"signal": 0}

    def execute_trades(self, signals: Dict[str, Any]) -> None:
        """Execute trades based on signals and risk management rules."""
        try:
            signal = signals["signal"]
            current_price = self.data.Close[-1]

            if signal > 0 and not self.position.is_long:
                self._enter_long_position(current_price)
            elif signal < 0 and not self.position.is_short:
                self._enter_short_position(current_price)

            self._manage_positions(current_price)

        except Exception as e:
            logger.error(f"Error executing trades: {e}")

    def _enter_long_position(self, current_price: float) -> None:
        """Enter a long position with proper risk management."""
        try:
            current_features = self.data_df.iloc[-1:][self.features].values
            position_size = self.risk_manager.get_position_size(
                current_features=current_features
            )

            stop_loss = self.risk_manager.adjust_stop_loss(
                current_price, self.data.ATR[-1], "default"
            )
            take_profit = self.risk_manager.adjust_take_profit(
                current_price, self.data.ATR[-1], "default"
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

    def _enter_short_position(self, current_price: float) -> None:
        """Enter a short position with proper risk management."""
        try:
            current_features = self.data_df.iloc[-1:][self.features].values
            position_size = self.risk_manager.get_position_size(
                current_features=current_features
            )

            stop_loss = self.risk_manager.adjust_stop_loss(
                current_price, self.data.ATR[-1], "default"
            )
            take_profit = self.risk_manager.adjust_take_profit(
                current_price, self.data.ATR[-1], "default"
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

    def _manage_positions(self, current_price: float) -> None:
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
