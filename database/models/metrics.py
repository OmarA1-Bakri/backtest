"""Metrics model."""

from sqlalchemy import Column, Float, DateTime, ForeignKey, text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.models.base import Base


class Metrics(Base):
    """Metrics model."""

    __tablename__ = "metrics"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        server_default=text("uuid_generate_v4()"),
    )
    backtest_id = Column(UUID(as_uuid=True), ForeignKey("backtests.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    total_return = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    profit_factor = Column(Float)
    trades_count = Column(Integer)
    additional_metrics = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    backtest = relationship("Backtest", back_populates="metrics")
    user = relationship("User", back_populates="metrics")

    def __repr__(self):
        """String representation of the metrics."""
        return f"<Metrics {self.id}>"
