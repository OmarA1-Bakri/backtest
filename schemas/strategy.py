"""Strategy schemas."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class StrategyBase(BaseModel):
    """Base strategy schema."""

    name: str
    description: Optional[str] = None
    code: str
    parameters: Optional[Dict[str, Any]] = None


class StrategyCreate(StrategyBase):
    """Create strategy schema."""

    pass


class StrategyResponse(StrategyBase):
    """Response strategy schema."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""

        from_attributes = True
