"""Script to clean up alembic state."""

import asyncio
import asyncpg
from core.config.settings import settings


async def cleanup_alembic():
    """Clean up alembic state in the database."""
    try:
        conn = await asyncpg.connect(
            host=settings.database.DB_HOST,
            port=settings.database.DB_PORT,
            user=settings.database.DB_USER,
            password=settings.database.DB_PASSWORD,
            database=settings.database.DB_NAME,
        )

        # Drop alembic_version table if it exists
        await conn.execute("DROP TABLE IF EXISTS alembic_version")
        print("Successfully dropped alembic_version table")

        await conn.close()
    except Exception as e:
        print(f"Error cleaning up alembic state: {e}")


if __name__ == "__main__":
    asyncio.run(cleanup_alembic())
