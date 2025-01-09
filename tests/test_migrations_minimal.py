"""Minimal test to verify database migrations work correctly."""

import pytest
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text, inspect

from core.config.settings import settings


@pytest.fixture(scope="session")
def minimal_test_db():
    """Creates and drops the test DB once per session, with no async code."""
    # 1. Connect to the admin DB (e.g., 'postgres')
    admin_url = f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/postgres"
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    # 2. Drop and recreate the test DB
    with admin_engine.connect() as conn:
        conn.execute(
            text(f"DROP DATABASE IF EXISTS {settings.TEST_DB_NAME} WITH (FORCE)")
        )
        conn.execute(text(f"CREATE DATABASE {settings.TEST_DB_NAME}"))

    # 3. Connect to test DB and drop schema if exists
    test_url = f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.TEST_DB_NAME}"
    test_engine = create_engine(test_url, isolation_level="AUTOCOMMIT")
    with test_engine.connect() as conn:
        # Drop schema and extension first
        conn.execute(text("DROP SCHEMA IF EXISTS backtest CASCADE"))
        conn.execute(text('DROP EXTENSION IF EXISTS "uuid-ossp" CASCADE'))
        # Create schema
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS backtest"))
        # Create extension in public schema
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))

    yield  # Tests run here

    # 4. Drop the test DB after tests
    with admin_engine.connect() as conn:
        conn.execute(
            text(f"DROP DATABASE IF EXISTS {settings.TEST_DB_NAME} WITH (FORCE)")
        )


@pytest.fixture(scope="session")
def minimal_sync_engine(minimal_test_db):
    """Creates a synchronous engine pointed at backtest_test."""
    sync_url = f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.TEST_DB_NAME}"
    engine = create_engine(sync_url)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def minimal_alembic_config(minimal_sync_engine):
    """Returns an Alembic config object pointing to the sync test DB URL."""
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.attributes["testing"] = True  # Set testing mode
    alembic_cfg.set_main_option("sqlalchemy.url", str(minimal_sync_engine.url))
    return alembic_cfg


def test_migrations(minimal_sync_engine, minimal_alembic_config):
    """
    Minimal single test:
    1. Runs upgrade head
    2. Verifies a known table or revision is present
    3. Runs downgrade base
    4. Verifies we returned to 'base' or the table got dropped
    """
    # 1. Upgrade to head
    command.upgrade(minimal_alembic_config, "head")

    # Verify we have all the expected tables
    inspector = inspect(minimal_sync_engine)
    tables = inspector.get_table_names(schema="backtest")
    expected_tables = {
        "users",
        "audit_logs",
        "strategies",
        "backtests",
        "backtest_results",
        "metrics",
    }
    assert expected_tables.issubset(set(tables)), f"Missing tables. Found: {tables}"

    # 2. Downgrade to base
    command.downgrade(minimal_alembic_config, "base")

    # Verify all tables are gone
    inspector = inspect(minimal_sync_engine)
    tables = inspector.get_table_names(schema="backtest")
    assert not tables, f"Expected no tables after downgrade, but found: {tables}"
