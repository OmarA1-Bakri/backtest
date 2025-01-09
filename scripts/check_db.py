"""Script to check database structure."""

import asyncio
from sqlalchemy import text
from database.config import get_db_session


async def check_db_structure():
    """Check database structure."""
    async with get_db_session(testing=True) as session:
        # Get table columns
        result = await session.execute(
            text(
                """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users'
            """
            )
        )
        columns = result.fetchall()
        print("\nTable structure:")
        for column in columns:
            print(f"Column: {column[0]}, Type: {column[1]}")


if __name__ == "__main__":
    asyncio.run(check_db_structure())
