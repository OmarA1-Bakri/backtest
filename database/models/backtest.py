"""Backtest model."""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.models.base import Base


class Backtest(Base):
    """Backtest model."""

    __tablename__ = "backtests"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    strategy_id = Column(
        UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False
    )
    initial_capital = Column(Float, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)
    parameters = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="backtests")
    strategy = relationship("Strategy", back_populates="backtests")
    metrics = relationship("Metrics", back_populates="backtest")
    results = relationship("BacktestResult", back_populates="backtest")

    def __repr__(self):
        """String representation of the backtest."""
        return f"<Backtest {self.id}>"
