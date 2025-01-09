"""Metrics schemas."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class MetricsBase(BaseModel):
    """Base metrics schema."""

    backtest_id: int
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    trades_count: int
    details: Optional[Dict[str, Any]] = None


class MetricsCreate(MetricsBase):
    """Create metrics schema."""

    pass


class MetricsResponse(MetricsBase):
    """Response metrics schema."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""

        from_attributes = True
