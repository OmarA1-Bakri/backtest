"""Backtest result model."""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.models.base import Base


class BacktestResult(Base):
    """Backtest result model."""

    __tablename__ = "backtest_results"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    backtest_id = Column(UUID(as_uuid=True), ForeignKey("backtests.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    action = Column(String, nullable=False)  # "BUY" or "SELL"
    symbol = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    position_value = Column(Float, nullable=False)
    portfolio_value = Column(Float, nullable=False)
    signal_data = Column(JSONB)  # Additional signal data
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    backtest = relationship("Backtest", back_populates="results")

    def __repr__(self):
        """String representation of the backtest result."""
        return f"<BacktestResult {self.id}>"
