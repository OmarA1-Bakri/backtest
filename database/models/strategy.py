"""Strategy model."""

from sqlalchemy import Column, String, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.models.base import Base


class Strategy(Base):
    """Strategy model."""

    __tablename__ = "strategies"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    name = Column(String, nullable=False)
    description = Column(String)
    code = Column(String)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    parameters = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="strategies")
    backtests = relationship("Backtest", back_populates="strategy")

    def __repr__(self):
        """String representation of the strategy."""
        return f"<Strategy {self.name}>"
