"""Database base module.

This module provides the base configuration for SQLAlchemy models following
SQLAlchemy 2.0 best practices.

References:
    - SQLAlchemy ORM: https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html#declarative-mapping
    - Type Annotations: https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html#declarative-table-configuration
"""

from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Recommended naming convention for PostgreSQL
# https://docs.sqlalchemy.org/en/20/core/metadata.html#metadata-naming-conventions
NAMING_CONVENTION: Dict[str, str] = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}

# Create metadata with naming convention
metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """Base class for all database models.

    This class provides common functionality and configuration for all models:
    - Automatic table naming based on class name
    - Common columns (id, created_at, updated_at)
    - JSON serialization support
    - Type annotation support
    """

    metadata = metadata

    # Use class name lowercase as table name
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    # Common columns for all models
    id: Mapped[UUID] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary.

        This method is useful for JSON serialization and API responses.
        """
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }
