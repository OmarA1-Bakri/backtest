"""Alembic environment configuration.

This module configures Alembic for database migrations with SQLAlchemy 2.0
and async support.

References:
    - Alembic Async: https://alembic.sqlalchemy.org/en/latest/cookbook.html#async-migrations
    - SQLAlchemy 2.0: https://docs.sqlalchemy.org/en/20/changelog/migration_20.html
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from core.config.settings import settings
from database.models.base import Base
from database.models import *  # noqa: F403, F401

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get database URL from settings
db_url = f"postgresql://{settings.BACKTEST_DB_USER}:{settings.BACKTEST_DB_PASSWORD}@{settings.BACKTEST_DB_HOST}:{settings.BACKTEST_DB_PORT}/{settings.BACKTEST_DB_NAME}"
config.set_main_option("sqlalchemy.url", db_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = db_url
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
