"""Script to set up test environment."""

import os
import sys
from pathlib import Path
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.config.settings import settings


def setup_test_environment():
    """Set up test environment."""
    # Set environment variables
    os.environ["ENV"] = "test"
    os.environ["PYTHONPATH"] = str(project_root)

    # Ensure PostgreSQL is running
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database="postgres",
        )
        conn.close()
        print("✓ PostgreSQL is running")
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        sys.exit(1)

    # Create test database
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database="postgres",
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Terminate existing connections
        cur.execute(
            """
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = %s
            AND pid <> pg_backend_pid()
        """,
            [settings.TEST_DB_NAME],
        )

        # Drop and recreate test database
        cur.execute(f"DROP DATABASE IF EXISTS {settings.TEST_DB_NAME}")
        cur.execute(f"CREATE DATABASE {settings.TEST_DB_NAME}")

        cur.close()
        conn.close()
        print(f"✓ Created test database: {settings.TEST_DB_NAME}")
    except Exception as e:
        print(f"✗ Failed to create test database: {e}")
        sys.exit(1)

    # Run migrations
    try:
        subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=str(project_root / "database" / "migrations"),
            check=True,
        )
        print("✓ Applied database migrations")
    except subprocess.CalledProcessError as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)

    print("\nTest environment setup complete! ✨")


if __name__ == "__main__":
    setup_test_environment()
