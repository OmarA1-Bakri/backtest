from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from logger import logger


class Broker:
    """Simulated broker for backtesting."""

    def __init__(self, initial_cash: float = None):
        """Initialize broker with initial cash.

        Args:
            initial_cash: Starting cash for trading
        """
        self.initial_cash = initial_cash or 100000.0
        self.cash = self.initial_cash
        self.positions: Dict[str, float] = {}  # symbol -> quantity
        self.trades: List[Dict] = []
        self.commission_rate = 0.001  # 0.1% commission per trade

    def place_order(
        self, symbol: str, quantity: float, price: float, order_type: str = "market"
    ) -> bool:
        """Place a trading order.

        Args:
            symbol: Trading symbol
            quantity: Order quantity (positive for buy, negative for sell)
            price: Order price
            order_type: Type of order (market, limit, etc.)

        Returns:
            True if order executed successfully, False otherwise
        """
        try:
            # Validate input parameters
            if quantity == 0:
                logger.warning("Invalid order: quantity cannot be zero")
                return False
            if price <= 0:
                logger.warning("Invalid order: price must be positive")
                return False

            commission = abs(quantity * price * self.commission_rate)
            total_cost = quantity * price + commission

            # Check if we have enough cash for buy orders
            if quantity > 0 and total_cost > self.cash:
                logger.warning(
                    f"Insufficient cash for order: {total_cost} > {self.cash}"
                )
                return False

            # Check if we have enough shares for sell orders
            current_position = self.positions.get(symbol, 0)
            if quantity < 0 and abs(quantity) > current_position:
                logger.warning(
                    f"Insufficient shares for order: {abs(quantity)} > {current_position}"
                )
                return False

            # Execute order
            self.cash -= total_cost
            self.positions[symbol] = current_position + quantity

            # Record trade
            self.trades.append(
                {
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": price,
                    "commission": commission,
                    "type": "buy" if quantity > 0 else "sell",
                }
            )

            return True
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return False

    def get_position(self, symbol: str) -> float:
        """Get current position for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Current position quantity
        """
        return self.positions.get(symbol, 0)

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate current portfolio value.

        Args:
            current_prices: Dictionary of current prices for each symbol

        Returns:
            Total portfolio value
        """
        try:
            portfolio_value = self.cash
            for symbol, quantity in self.positions.items():
                if symbol in current_prices and current_prices[symbol] > 0:
                    portfolio_value += quantity * current_prices[symbol]
            return portfolio_value
        except Exception as e:
            logger.error(f"Error calculating portfolio value: {str(e)}")
            return self.cash

    def get_performance_metrics(self) -> Dict[str, float]:
        """Calculate performance metrics for the portfolio.

        Returns:
            Dictionary of performance metrics
        """
        try:
            # Calculate returns
            returns = []
            cash = self.initial_cash
            for trade in self.trades:
                cash -= trade["quantity"] * trade["price"] + trade["commission"]
                returns.append((cash - self.initial_cash) / self.initial_cash)

            returns = pd.Series(returns)

            # Calculate metrics
            total_return = (cash - self.initial_cash) / self.initial_cash
            sharpe_ratio = (
                returns.mean() / returns.std() * np.sqrt(252) if len(returns) > 1 else 0
            )
            max_drawdown = (returns.cummax() - returns).max()

            return {
                "total_return": total_return,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "num_trades": len(self.trades),
            }
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {str(e)}")
            return {}
