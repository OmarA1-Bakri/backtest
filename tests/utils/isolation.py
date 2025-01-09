"""Database test isolation utilities."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any, Optional, Dict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class TestState:
    """Test state management."""

    _snapshots: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def save_snapshot(cls, name: str, data: Dict[str, Any]) -> None:
        """Save a database state snapshot.

        Args:
            name: Name of the snapshot
            data: Data to save
        """
        cls._snapshots[name] = data

    @classmethod
    def get_snapshot(cls, name: str) -> Optional[Dict[str, Any]]:
        """Get a database state snapshot.

        Args:
            name: Name of the snapshot

        Returns:
            Optional[Dict[str, Any]]: Snapshot data if found
        """
        return cls._snapshots.get(name)

    @classmethod
    def clear_snapshots(cls) -> None:
        """Clear all snapshots."""
        cls._snapshots.clear()


@asynccontextmanager
async def isolated_db_session(
    session: AsyncSession,
) -> AsyncGenerator[AsyncSession, None]:
    """Create an isolated database session with automatic rollback.

    Args:
        session: Database session to isolate

    Yields:
        AsyncSession: Isolated database session
    """
    # Start a nested transaction
    transaction = await session.begin_nested()

    try:
        yield session
    finally:
        # Always rollback the nested transaction
        await transaction.rollback()


async def create_db_snapshot(
    session: AsyncSession, name: str, tables: list[str]
) -> None:
    """Create a snapshot of specified database tables.

    Args:
        session: Database session
        name: Name of the snapshot
        tables: List of table names to snapshot
    """
    snapshot_data = {}

    try:
        for table in tables:
            # Get table data
            result = await session.execute(text(f"SELECT * FROM {table}"))
            snapshot_data[table] = result.fetchall()

        # Save snapshot
        TestState.save_snapshot(name, snapshot_data)

    except Exception as e:
        logger.error(f"Error creating database snapshot: {e}")
        raise


async def restore_db_snapshot(session: AsyncSession, name: str) -> None:
    """Restore database state from a snapshot.

    Args:
        session: Database session
        name: Name of the snapshot to restore
    """
    snapshot = TestState.get_snapshot(name)
    if not snapshot:
        raise ValueError(f"Snapshot '{name}' not found")

    try:
        # Start a transaction
        async with session.begin():
            for table, data in snapshot.items():
                # Clear table
                await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))

                if data:
                    # Get column names
                    result = await session.execute(
                        text(
                            f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"
                        )
                    )
                    columns = [row[0] for row in result.fetchall()]

                    # Insert data
                    for row in data:
                        values = ", ".join(
                            [
                                f"'{value}'" if value is not None else "NULL"
                                for value in row
                            ]
                        )
                        await session.execute(
                            text(
                                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({values})"
                            )
                        )

    except Exception as e:
        logger.error(f"Error restoring database snapshot: {e}")
        raise


async def cleanup_tables(session: AsyncSession, tables: list[str]) -> None:
    """Clean up specified database tables.

    Args:
        session: Database session
        tables: List of table names to clean
    """
    try:
        async with session.begin():
            for table in tables:
                await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
    except Exception as e:
        logger.error(f"Error cleaning up tables: {e}")
        raise
