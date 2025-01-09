"""Script to create test database tables."""

import asyncio
import sys
import os

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models.base import Base
from database.models.user import User
from database.models.strategy import Strategy
from database.models.backtest import Backtest
from database.models.metrics import Metrics
from sqlalchemy.ext.asyncio import create_async_engine
from tests.conftest import test_settings
from sqlalchemy import text


async def create_test_tables():
    """Create test database tables."""
    try:
        # Create engine
        engine = create_async_engine(test_settings.get_database_url())

        # Create tables
        async with engine.begin() as conn:
            # Create uuid-ossp extension
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))

            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        print("Created test database tables")
        await engine.dispose()

    except Exception as e:
        print(f"Error creating tables: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(create_test_tables())
