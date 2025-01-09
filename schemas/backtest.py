"""Backtest schemas."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class BacktestBase(BaseModel):
    """Base backtest schema."""

    name: str
    description: Optional[str] = None
    strategy_id: int
    initial_capital: float
    start_date: datetime
    end_date: datetime
    parameters: Optional[Dict[str, Any]] = None


class BacktestCreate(BacktestBase):
    """Create backtest schema."""

    pass


class BacktestResponse(BacktestBase):
    """Response backtest schema."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""

        from_attributes = True
