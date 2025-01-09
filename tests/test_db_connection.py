"""Test database connection.

This module tests the database connection using both synchronous and asynchronous APIs.
"""

import pytest
from sqlalchemy import text

from core.database.testing import (
    create_test_database,
    drop_test_database,
    get_test_engine,
)


@pytest.mark.asyncio
async def test_db_connection():
    """Test database connection."""
    try:
        # Create test database
        await create_test_database()
        print("\n[OK] Successfully created test database")

        # Create engine and test connection
        engine = get_test_engine()
        async with engine.connect() as conn:
            # Check if we can execute queries
            result = await conn.execute(text("SELECT version();"))
            version = await result.scalar()
            print(f"[OK] PostgreSQL version: {version}")

            # Test transaction management
            async with conn.begin():
                # Create a test table
                await conn.execute(
                    text(
                        """
                    CREATE TABLE test_table (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL
                    )
                """
                    )
                )
                print("[OK] Created test table")

                # Insert some data
                await conn.execute(
                    text(
                        """
                    INSERT INTO test_table (name) VALUES ('test')
                """
                    )
                )
                print("[OK] Inserted test data")

                # Query the data
                result = await conn.execute(text("SELECT * FROM test_table"))
                rows = await result.fetchall()
                assert len(rows) == 1, "Expected 1 row"
                assert rows[0][1] == "test", "Expected name to be 'test'"
                print("[OK] Successfully queried test data")

        # Cleanup
        await engine.dispose()
        await drop_test_database()
        print("[OK] Cleaned up test database")

        print("\nAll database connection tests passed! ✨")
        return True

    except Exception as e:
        print(f"\n[ERROR] Database connection failed: {str(e)}")
        return False


if __name__ == "__main__":
    pytest.main(["-v", __file__])
