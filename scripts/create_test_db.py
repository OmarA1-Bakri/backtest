"""Script to create test database."""

import asyncio
import asyncpg


async def create_test_database():
    """Create test database if it doesn't exist."""
    try:
        # Connect to default database first
        conn = await asyncpg.connect(
            user="postgres", password="456852", database="postgres", host="localhost"
        )

        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", "backtest_test"
        )

        if not exists:
            # Create database
            await conn.execute("CREATE DATABASE backtest_test")
            print("Created database 'backtest_test'")
        else:
            print("Database 'backtest_test' already exists")

        await conn.close()

    except Exception as e:
        print(f"Error creating database: {e}")


if __name__ == "__main__":
    asyncio.run(create_test_database())
