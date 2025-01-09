#!/usr/bin/env python3
"""Database management script for migrations and verification."""
import argparse
import sys
import os
from pathlib import Path
import alembic.config
import alembic.command
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.config.settings import Settings

settings = Settings()


def create_database():
    """Create database and schema if they don't exist."""
    # Connect to postgres database to create new database
    conn = psycopg2.connect(
        host=settings.database.DB_HOST,
        port=settings.database.DB_PORT,
        user=settings.database.DB_USER,
        password=settings.database.DB_PASSWORD,
        database="postgres",
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Create database if it doesn't exist
    cursor.execute(
        "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
        (settings.database.DB_NAME,),
    )
    if not cursor.fetchone():
        cursor.execute(f"CREATE DATABASE {settings.database.DB_NAME}")
        print(f"Created database {settings.database.DB_NAME}")

    cursor.close()
    conn.close()

    # Connect to the new database to create schema and extensions
    engine = create_engine(settings.database.get_sync_database_url())
    with engine.connect() as conn:
        # Create extensions
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pg_trgm"'))
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "btree_gin"'))
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "btree_gist"'))

        # Create schema
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS backtest"))

        # Set search path
        conn.execute(text("SET search_path TO backtest, public"))

        conn.commit()

    print("Database setup complete")


def get_current_revision(engine):
    """Get current database revision."""
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        return context.get_current_revision()


def get_head_revision():
    """Get latest available revision."""
    config = alembic.config.Config("database/migrations/alembic.ini")
    script = ScriptDirectory.from_config(config)
    return script.get_current_head()


def verify_schema(engine):
    """Verify database schema matches the expected version."""
    current = get_current_revision(engine)
    head = get_head_revision()

    if current != head:
        print(f"Schema mismatch! Current: {current}, Expected: {head}")
        return False

    print("Database schema is up-to-date")
    return True


def setup_test_database():
    """Set up test database."""
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            host=settings.database.DB_HOST,
            port=settings.database.DB_PORT,
            user=settings.database.DB_USER,
            password=settings.database.DB_PASSWORD,
            database="postgres",
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        with conn.cursor() as cur:
            # Drop test database if it exists
            cur.execute(f"DROP DATABASE IF EXISTS {settings.database.TEST_DB_NAME}")
            print(f"Dropped existing test database: {settings.database.TEST_DB_NAME}")

            # Create new test database
            cur.execute(f"CREATE DATABASE {settings.database.TEST_DB_NAME}")
            print(f"Created new test database: {settings.database.TEST_DB_NAME}")

        conn.close()

        # Connect to test database to create extensions
        test_conn = psycopg2.connect(
            host=settings.database.DB_HOST,
            port=settings.database.DB_PORT,
            user=settings.database.DB_USER,
            password=settings.database.DB_PASSWORD,
            database=settings.database.TEST_DB_NAME,
        )
        test_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        with test_conn.cursor() as cur:
            # Create extensions
            cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            cur.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
            cur.execute('CREATE EXTENSION IF NOT EXISTS "btree_gin"')
            cur.execute('CREATE EXTENSION IF NOT EXISTS "btree_gist"')

            # Create schema
            cur.execute("CREATE SCHEMA IF NOT EXISTS backtest")

        test_conn.close()

        # Run migrations on test database
        test_engine = create_engine(settings.database.get_sync_test_database_url())
        config = alembic.config.Config("database/migrations/alembic.ini")
        alembic.command.upgrade(config, "head")

        print("Test database setup completed successfully")
        return True

    except Exception as e:
        print(f"Error setting up test database: {e}")
        return False


def run_migrations(engine, tag=None):
    """Run database migrations."""
    config = alembic.config.Config("database/migrations/alembic.ini")
    alembic.command.upgrade(config, "head", tag=tag)
    print("Migrations completed successfully")


def create_migration(message):
    """Create a new migration."""
    config = alembic.config.Config("database/migrations/alembic.ini")
    alembic.command.revision(config, message=message, autogenerate=True)
    print("Migration created successfully")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Database management script")
    parser.add_argument(
        "action",
        choices=["verify", "migrate", "create-migration", "setup-test", "setup"],
        help="Action to perform",
    )
    parser.add_argument(
        "--message", help="Migration message (required for create-migration)"
    )
    args = parser.parse_args()

    if args.action == "setup-test":
        if not setup_test_database():
            sys.exit(1)
    elif args.action == "setup":
        create_database()
    else:
        engine = create_engine(settings.database.get_sync_database_url())

        if args.action == "verify":
            if not verify_schema(engine):
                sys.exit(1)
        elif args.action == "migrate":
            run_migrations(engine)
        elif args.action == "create-migration":
            if not args.message:
                print("Error: --message is required for create-migration")
                sys.exit(1)
            create_migration(args.message)


if __name__ == "__main__":
    main()
