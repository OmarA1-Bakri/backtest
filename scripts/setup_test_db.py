"""Script to set up test database with proper connection handling."""

import asyncio
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from core.config.settings import settings
from database.config import get_database_url, create_engine_instance
from database.models.base import Base


def terminate_database_connections():
    """Terminate all connections to the test database."""
    conn = psycopg2.connect(
        host=settings.database.DB_HOST,
        port=settings.database.DB_PORT,
        user=settings.database.DB_USER,
        password=settings.database.DB_PASSWORD,
        database="postgres",
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    cur = conn.cursor()
    try:
        # Terminate all connections to the test database
        cur.execute(
            """
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = %s
            AND pid <> pg_backend_pid()
            """,
            [settings.database.TEST_DB_NAME],
        )
    finally:
        cur.close()
        conn.close()


def create_test_database():
    """Create test database if it doesn't exist."""
    conn = psycopg2.connect(
        host=settings.database.DB_HOST,
        port=settings.database.DB_PORT,
        user=settings.database.DB_USER,
        password=settings.database.DB_PASSWORD,
        database="postgres",
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    cur = conn.cursor()
    try:
        # Drop test database if it exists
        cur.execute(f"DROP DATABASE IF EXISTS {settings.database.TEST_DB_NAME}")
        print(f"[OK] Dropped existing test database: {settings.database.TEST_DB_NAME}")

        # Create fresh test database
        cur.execute(f"CREATE DATABASE {settings.database.TEST_DB_NAME}")
        print(f"[OK] Created test database: {settings.database.TEST_DB_NAME}")

    finally:
        cur.close()
        conn.close()


def setup_database_schema():
    """Set up database schema and extensions."""
    # Connect to test database
    conn = psycopg2.connect(
        host=settings.database.DB_HOST,
        port=settings.database.DB_PORT,
        user=settings.database.DB_USER,
        password=settings.database.DB_PASSWORD,
        database=settings.database.TEST_DB_NAME,
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    cur = conn.cursor()
    try:
        # Create extensions
        cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        print("[OK] Created UUID extension")

        # Create schema
        cur.execute("CREATE SCHEMA IF NOT EXISTS backtest")
        print("[OK] Created backtest schema")

    finally:
        cur.close()
        conn.close()


async def create_tables():
    """Create database tables using SQLAlchemy."""
    engine = create_engine_instance(testing=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] Created database tables")
    await engine.dispose()


async def setup_test_database():
    """Set up test database for testing."""
    try:
        print("Setting up test database...")
        terminate_database_connections()
        create_test_database()
        setup_database_schema()
        await create_tables()
        print("Test database setup completed successfully!")
    except Exception as e:
        print(f"Error setting up test database: {e}")
        raise


async def cleanup_test_database():
    """Clean up test database after testing."""
    try:
        print("Cleaning up test database...")
        terminate_database_connections()
        conn = psycopg2.connect(
            host=settings.database.DB_HOST,
            port=settings.database.DB_PORT,
            user=settings.database.DB_USER,
            password=settings.database.DB_PASSWORD,
            database="postgres",
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        cur = conn.cursor()
        try:
            cur.execute(f"DROP DATABASE IF EXISTS {settings.database.TEST_DB_NAME}")
            print(f"[OK] Dropped test database: {settings.database.TEST_DB_NAME}")
        finally:
            cur.close()
            conn.close()
    except Exception as e:
        print(f"Error cleaning up test database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(setup_test_database())
