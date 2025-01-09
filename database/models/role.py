"""Role and permission models for RBAC implementation."""

import uuid
from datetime import datetime
from typing import List

from sqlalchemy import Column, String, Table, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func

from database.models.base import Base

# Association tables
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE")),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE")),
    Column(
        "permission_id",
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
    ),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)


class Role(Base):
    """Role model for RBAC."""

    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = Column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str] = Column(String(255))
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship(
        "Permission", secondary=role_permissions, back_populates="roles"
    )

    def __str__(self) -> str:
        """String representation of role."""
        return f"Role(name={self.name})"


class Permission(Base):
    """Permission model for RBAC."""

    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = Column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str] = Column(String(255))
    resource: Mapped[str] = Column(
        String(50), nullable=False
    )  # e.g., "strategy", "backtest"
    action: Mapped[str] = Column(
        String(50), nullable=False
    )  # e.g., "create", "read", "update"
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    roles = relationship(
        "Role", secondary=role_permissions, back_populates="permissions"
    )

    def __str__(self) -> str:
        """String representation of permission."""
        return f"Permission(name={self.name}, resource={self.resource}, action={self.action})"
