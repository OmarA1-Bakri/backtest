"""Audit model.

This module defines the AuditLog model for tracking system events and user actions.

References:
    - SQLAlchemy 2.0 ORM: https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html
    - JSON Types: https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.JSON
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import String, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from core.database.base import Base


class AuditEventType(str, PyEnum):
    """Audit event types."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    ERROR = "error"


class AuditStatus(str, PyEnum):
    """Audit status types."""

    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"


class AuditLog(Base):
    """Audit log model for tracking system events and user actions."""

    __tablename__ = "audit_logs"

    # Override id from Base to use UUID
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=UUID
    )

    # Event information
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    event_type: Mapped[AuditEventType] = mapped_column(
        Enum(AuditEventType), nullable=False
    )
    status: Mapped[AuditStatus] = mapped_column(
        Enum(AuditStatus), nullable=False, default=AuditStatus.SUCCESS
    )

    # User information
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    user: Mapped[Optional["User"]] = relationship("User", lazy="joined")

    # Event details
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Request information
    request_method: Mapped[str] = mapped_column(String, nullable=False)
    request_url: Mapped[str] = mapped_column(String, nullable=False)
    request_headers: Mapped[Optional[Dict[str, str]]] = mapped_column(
        JSON, nullable=True
    )
    request_ip: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    request_user_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def __repr__(self) -> str:
        """String representation of AuditLog."""
        return (
            f"AuditLog(id={self.id}, event_type={self.event_type}, "
            f"status={self.status}, user_id={self.user_id})"
        )
