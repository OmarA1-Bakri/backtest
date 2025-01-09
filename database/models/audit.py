"""Audit log model."""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship

from database.models.base import Base


class AuditLog(Base):
    """Audit log model."""

    __tablename__ = "audit_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False,
    )
    # Make user_id nullable to support anonymous requests and system events
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User ID, can be null for anonymous requests or system events",
    )
    action = Column(String(50), nullable=True, comment="Type of action being logged")
    method = Column(String, nullable=True)
    path = Column(String, nullable=True)
    status_code = Column(Integer, nullable=True)
    request_body = Column(JSONB, nullable=True)
    error_detail = Column(String, nullable=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        """Get string representation."""
        return f"<AuditLog {self.id}>"
