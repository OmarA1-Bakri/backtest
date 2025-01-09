"""Test database migrations."""

import sys
from pathlib import Path
import pytest
import asyncpg
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncConnection
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from core.config.settings import settings
from core.database.testing import (
    create_test_database,
    drop_test_database,
    get_test_engine,
)


@pytest.fixture(scope="session")
async def async_engine():
    """Create test database engine."""
    # Create test database
    await create_test_database()

    # Create engine
    engine = get_test_engine()

    yield engine

    # Cleanup
    await engine.dispose()
    await drop_test_database()


@pytest.fixture(scope="session")
def alembic_config(async_engine):
    """Returns an Alembic config object pointing to the test DB."""
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", str(async_engine.url))
    config.attributes["testing"] = True  # Mark as testing environment
    return config


async def clean_database(engine):
    """Drop all tables in test database."""
    async with engine.begin() as conn:
        # Drop all tables in public schema
        await conn.execute(
            text(
                """
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """
            )
        )


def get_all_revisions():
    """Get all migration revisions."""
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    revisions = []

    for rev in script.walk_revisions():
        revisions.append(rev.revision)

    return list(reversed(revisions))


async def get_current_revision(engine) -> str:
    """Get current migration revision."""
    async with engine.connect() as conn:
        context = MigrationContext.configure(conn, opts={"as_sql": True})
        return context.get_current_revision()


@pytest.mark.asyncio
async def test_migration_upgrade_downgrade(async_engine, alembic_config):
    """Test migration upgrade and downgrade for each revision."""
    # Clean database
    await clean_database(async_engine)

    # Get all revisions
    revisions = get_all_revisions()
    assert len(revisions) > 0, "No migrations found"

    # Test upgrade to each revision
    for rev in revisions:
        # Upgrade to specific revision
        command.upgrade(alembic_config, rev)
        current_rev = await get_current_revision(async_engine)
        assert current_rev == rev, f"Failed to upgrade to revision {rev}"

        # Verify core tables exist and have correct structure
        async with async_engine.connect() as conn:
            inspector = inspect(async_engine)
            tables = await inspector.get_table_names()

            # Check core tables
            assert "users" in tables, "Users table not created"
            assert "audit_logs" in tables, "Audit logs table not created"

            # Check table columns
            user_columns = {col["name"] for col in await inspector.get_columns("users")}
            audit_columns = {
                col["name"] for col in await inspector.get_columns("audit_logs")
            }

            # Verify user table structure
            assert "id" in user_columns
            assert "email" in user_columns
            assert "hashed_password" in user_columns
            assert "created_at" in user_columns
            assert "updated_at" in user_columns

            # Verify audit log table structure
            assert "id" in audit_columns
            assert "user_id" in audit_columns
            assert "event_type" in audit_columns
            assert "event_data" in audit_columns
            assert "created_at" in audit_columns

        # Downgrade one revision
        command.downgrade(alembic_config, "-1")
        current_rev = await get_current_revision(async_engine)
        assert current_rev != rev, f"Failed to downgrade from revision {rev}"
