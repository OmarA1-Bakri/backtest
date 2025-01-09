"""Backtest request and response schemas."""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class BacktestRequest(BaseModel):
    """Backtest request model."""

    strategy_name: str = Field(..., description="Name of the strategy to backtest")
    start_date: datetime = Field(..., description="Start date for backtest")
    end_date: datetime = Field(..., description="End date for backtest")
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(..., description="Timeframe for data")
    initial_capital: float = Field(10000.0, description="Initial capital")
    position_size: float = Field(
        1.0, description="Position size as fraction of capital"
    )
    commission: float = Field(0.001, description="Trading commission")
    slippage: float = Field(0.001, description="Trading slippage")
    strategy_params: Optional[Dict[str, Any]] = Field(
        default=None, description="Strategy specific parameters"
    )


class BacktestResponse(BaseModel):
    """Backtest response model."""

    strategy_name: str = Field(..., description="Name of the strategy")
    start_date: datetime = Field(..., description="Start date of backtest")
    end_date: datetime = Field(..., description="End date of backtest")
    total_trades: int = Field(..., description="Total number of trades")
    winning_trades: int = Field(..., description="Number of winning trades")
    losing_trades: int = Field(..., description="Number of losing trades")
    win_rate: float = Field(..., description="Win rate")
    profit_factor: float = Field(..., description="Profit factor")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    total_return: float = Field(..., description="Total return")
    annual_return: float = Field(..., description="Annualized return")
    trades: List[Dict[str, Any]] = Field(..., description="List of trades")
