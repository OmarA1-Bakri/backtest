"""User model.

This module defines the User model for authentication and authorization.

References:
    - SQLAlchemy 2.0 ORM: https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html
    - Type Annotations: https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from core.database.base import Base


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    # Override id from Base to use UUID
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=UUID
    )

    # Authentication fields
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    # Authorization fields
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamp fields
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        """String representation of User."""
        return f"User(id={self.id}, email={self.email}, is_active={self.is_active})"
