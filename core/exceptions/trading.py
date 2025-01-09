"""Trading-specific exceptions for the BackTest AI application."""

from typing import Any, Dict, Optional
from decimal import Decimal

from core.exceptions.base import BackTestError


class TradingError(BackTestError):
    """Base exception for trading-related errors."""

    def __init__(
        self,
        message: str,
        symbol: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize TradingError.

        Args:
            message: Error message
            symbol: Optional trading symbol
            details: Optional dictionary containing additional error details
        """
        error_details = details or {}
        if symbol:
            error_details["symbol"] = symbol

        super().__init__(
            message=message,
            error_code="TRADING_ERROR",
            details=error_details,
        )


class InsufficientFundsError(TradingError):
    """Exception raised when there are insufficient funds for a trade."""

    def __init__(
        self,
        message: str,
        required_amount: float,
        available_amount: float,
        symbol: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize InsufficientFundsError.

        Args:
            message: Error message
            required_amount: Required amount for the trade
            available_amount: Available amount in the account
            symbol: Optional trading symbol
            details: Optional dictionary containing additional error details
        """
        error_details = details or {}
        error_details.update(
            {
                "required_amount": required_amount,
                "available_amount": available_amount,
            }
        )

        super().__init__(
            message=message,
            symbol=symbol,
            details=error_details,
        )
        self.error_code = "INSUFFICIENT_FUNDS_ERROR"


class InvalidOrderError(TradingError):
    """Exception raised when an order is invalid."""

    def __init__(
        self,
        message: str,
        order_id: str,
        symbol: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize InvalidOrderError.

        Args:
            message: Error message
            order_id: ID of the invalid order
            symbol: Optional trading symbol
            details: Optional dictionary containing additional error details
        """
        error_details = details or {}
        error_details["order_id"] = order_id

        super().__init__(
            message=message,
            symbol=symbol,
            details=error_details,
        )
        self.error_code = "INVALID_ORDER_ERROR"


class PositionLimitError(TradingError):
    """Exception raised when position limits are exceeded."""

    def __init__(
        self,
        message: str,
        current_position: Decimal,
        position_limit: Decimal,
        strategy_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize PositionLimitError.

        Args:
            message: Error message
            current_position: Current position size
            position_limit: Maximum allowed position size
            strategy_name: Optional name of the trading strategy
            details: Optional dictionary containing additional error details
        """
        error_details = details or {}
        error_details.update(
            {
                "current_position": str(current_position),
                "position_limit": str(position_limit),
            }
        )

        super().__init__(
            message=message,
            strategy_name=strategy_name,
            details=error_details,
        )
        self.error_code = "POSITION_LIMIT_ERROR"


class MarketDataError(TradingError):
    """Exception raised when there are issues with market data."""

    def __init__(
        self,
        message: str,
        symbol: str,
        data_type: str,
        strategy_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize MarketDataError.

        Args:
            message: Error message
            symbol: Trading symbol
            data_type: Type of market data
            strategy_name: Optional name of the trading strategy
            details: Optional dictionary containing additional error details
        """
        error_details = details or {}
        error_details.update(
            {
                "symbol": symbol,
                "data_type": data_type,
            }
        )

        super().__init__(
            message=message,
            strategy_name=strategy_name,
            details=error_details,
        )
        self.error_code = "MARKET_DATA_ERROR"


class RiskLimitError(TradingError):
    """Exception raised when risk limits are exceeded."""

    def __init__(
        self,
        message: str,
        risk_metric: str,
        current_value: float,
        limit_value: float,
        strategy_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize RiskLimitError.

        Args:
            message: Error message
            risk_metric: Name of the risk metric
            current_value: Current value of the risk metric
            limit_value: Limit value for the risk metric
            strategy_name: Optional name of the trading strategy
            details: Optional dictionary containing additional error details
        """
        error_details = details or {}
        error_details.update(
            {
                "risk_metric": risk_metric,
                "current_value": current_value,
                "limit_value": limit_value,
            }
        )

        super().__init__(
            message=message,
            strategy_name=strategy_name,
            details=error_details,
        )
        self.error_code = "RISK_LIMIT_ERROR"


class ExecutionError(TradingError):
    """Exception raised when trade execution fails."""

    def __init__(
        self,
        message: str,
        order_id: str,
        execution_details: Dict[str, Any],
        strategy_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize ExecutionError.

        Args:
            message: Error message
            order_id: ID of the failed order
            execution_details: Details of the execution attempt
            strategy_name: Optional name of the trading strategy
            details: Optional dictionary containing additional error details
        """
        error_details = details or {}
        error_details.update(
            {
                "order_id": order_id,
                "execution_details": execution_details,
            }
        )

        super().__init__(
            message=message,
            strategy_name=strategy_name,
            details=error_details,
        )
        self.error_code = "EXECUTION_ERROR"
