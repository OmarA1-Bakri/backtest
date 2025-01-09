#!/usr/bin/env python3
"""Database setup script."""

import os
import sys
import time
from pathlib import Path

# Add the project root directory to the Python path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("psycopg2 is not installed. Please install it first.")
    sys.exit(1)

try:
    import alembic.config
except ImportError:
    print("alembic is not installed. Please install it first.")
    sys.exit(1)

from core.config.settings import get_settings

settings = get_settings()


def check_postgres_installed() -> bool:
    """Check if PostgreSQL is installed."""
    try:
        import psycopg2

        print("\nPostgreSQL is installed")
        return True
    except ImportError:
        print("\nPostgreSQL is not installed")
        return False


def check_postgres_running() -> bool:
    """Check if PostgreSQL server is running."""
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD.get_secret_value(),
            database="postgres",
            connect_timeout=5,
        )
        conn.close()
        print("\nPostgreSQL server is running")
        return True
    except psycopg2.Error as e:
        print(f"\nPostgreSQL server is not running: {e}")
        return False


def create_database() -> bool:
    """Create the database if it doesn't exist."""
    try:
        # Connect to default database
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD.get_secret_value(),
            database="postgres",
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Check if database exists
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{settings.DB_NAME}'")
        exists = cur.fetchone()

        if not exists:
            print(f"\nCreating database '{settings.DB_NAME}'...")
            cur.execute(f'CREATE DATABASE "{settings.DB_NAME}"')
            print(f"Database '{settings.DB_NAME}' created successfully")
        else:
            print(f"\nDatabase '{settings.DB_NAME}' already exists")

        cur.close()
        conn.close()
        return True

    except psycopg2.Error as e:
        print(f"\nError creating database: {e}")
        return False


def setup_database_schema() -> bool:
    """Set up the database schema."""
    try:
        # Connect to the application database
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD.get_secret_value(),
            database=settings.DB_NAME,
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Enable required extensions
        print("\nEnabling required extensions...")

        # List of extensions we want to enable
        desired_extensions = [
            "uuid-ossp",  # For UUID generation (already installed)
            "pgcrypto",  # For encryption functions
            "hstore",  # For key-value storage
            "btree_gist",  # For exclusion constraints
            "pg_trgm",  # For text search
        ]

        for ext in desired_extensions:
            try:
                cur.execute(f'CREATE EXTENSION IF NOT EXISTS "{ext}"')
                print(f"Extension '{ext}' enabled")
            except psycopg2.Error as e:
                print(f"Warning: Could not enable extension '{ext}': {e}")
                conn.rollback()

        cur.close()
        conn.close()

        print("\nDatabase schema setup completed")
        return True

    except psycopg2.Error as e:
        print(f"\nError setting up database schema: {e}")
        return False


def init_alembic() -> bool:
    """Initialize Alembic if not already initialized."""
    try:
        print("\nInitializing Alembic...")

        # Get the directory containing this script
        current_dir = Path(__file__).resolve().parent

        # The migrations directory should be in the project root
        migrations_dir = current_dir.parent / "migrations"

        if not migrations_dir.exists():
            print(f"Creating migrations directory at {migrations_dir}")
            migrations_dir.mkdir(parents=True, exist_ok=True)

            # Initialize Alembic
            alembic_cfg = alembic.config.Config()
            alembic_cfg.set_main_option("script_location", str(migrations_dir))
            alembic_cfg.set_main_option("sqlalchemy.url", str(settings.DATABASE_URI))

            # Create alembic.ini
            alembic_ini = current_dir.parent / "alembic.ini"
            if not alembic_ini.exists():
                with open(alembic_ini, "w") as f:
                    f.write(
                        """# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = migrations

# template used to generate migration files
# file_template = %%(rev)s_%%(slug)s

# timezone to use when rendering the date
# within the migration file as well as the filename.
# string value is passed to dateutil.tz.gettz()
# leave blank for localtime
# timezone =

# max length of characters to apply to the
# "slug" field
#truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version location specification; this defaults
# to migrations/versions.  When using multiple version
# directories, initial revisions must be specified with --version-path
# version_locations = %(here)s/bar %(here)s/bat migrations/versions

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = driver://user:pass@localhost/dbname


[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks=black
# black.type=console_scripts
# black.entrypoint=black
# black.options=-l 79

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
                    )

            # Create env.py
            env_py = migrations_dir / "env.py"
            if not env_py.exists():
                with open(env_py, "w") as f:
                    f.write(
                        """from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    \"\"\"Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    \"\"\"
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    \"\"\"Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    \"\"\"
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""
                    )

            # Create versions directory
            versions_dir = migrations_dir / "versions"
            if not versions_dir.exists():
                versions_dir.mkdir(parents=True, exist_ok=True)

            # Create script.py.mako
            script_mako = migrations_dir / "script.py.mako"
            if not script_mako.exists():
                with open(script_mako, "w") as f:
                    f.write(
                        """\"\"\"${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

\"\"\"
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
"""
                    )

            print("Alembic initialized successfully")
            return True

    except Exception as e:
        print(f"\nError initializing Alembic: {e}")
        return False


def run_migrations() -> bool:
    """Run database migrations using Alembic."""
    try:
        print("\nRunning database migrations...")

        # Get the directory containing this script
        current_dir = Path(__file__).resolve().parent

        # The alembic.ini file should be in the project root
        alembic_ini = current_dir.parent / "alembic.ini"

        if not alembic_ini.exists():
            print(f"\nAlembic configuration not found at {alembic_ini}")
            return False

        # Create Alembic configuration
        alembic_cfg = alembic.config.Config(str(alembic_ini))

        # Run the migrations
        alembic.command.upgrade(alembic_cfg, "head")

        print("Database migrations completed successfully")
        return True

    except Exception as e:
        print(f"\nError running migrations: {e}")
        return False


def verify_database() -> bool:
    """Verify the database setup."""
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD.get_secret_value(),
            database=settings.DB_NAME,
        )
        cur = conn.cursor()

        # Check if we can execute queries
        cur.execute("SELECT 1")
        result = cur.fetchone()

        if result and result[0] == 1:
            print("\nDatabase verification successful")
            success = True
        else:
            print("\nDatabase verification failed")
            success = False

        cur.close()
        conn.close()
        return success

    except psycopg2.Error as e:
        print(f"\nDatabase verification failed: {e}")
        return False


def main() -> bool:
    """Main function to set up the database."""
    print("\nBackTest AI Database Setup")

    # Step 1: Check if PostgreSQL is installed
    if not check_postgres_installed():
        return False

    # Step 2: Check if PostgreSQL server is running
    if not check_postgres_running():
        return False

    # Step 3: Create database if it doesn't exist
    if not create_database():
        return False

    # Step 4: Set up database schema
    if not setup_database_schema():
        return False

    # Step 5: Run migrations
    if not run_migrations():
        return False

    # Step 6: Verify database setup
    if not verify_database():
        return False

    print("\nDatabase setup completed successfully!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
