"""Base classes and utilities for database testing."""

from datetime import datetime
from typing import Callable, Optional
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.testing.session import TestSessionLocal

logger = logging.getLogger(__name__)


class RollbackTestException(Exception):
    """Custom exception for triggering and identifying intentional rollbacks in tests."""

    pass


class DatabaseStateVerifier:
    """Utility class for database state verification."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.verification_log = []

    async def verify_row_count(self, table: str, expected: int) -> None:
        """Verify row count with detailed logging."""
        result = await self.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
        actual = result.scalar()

        verification = {
            "table": table,
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.utcnow(),
            "success": actual == expected,
        }
        self.verification_log.append(verification)

        assert actual == expected, (
            f"Row count mismatch in {table}:\n"
            f"Expected: {expected}\n"
            f"Actual: {actual}\n"
            f"Verification history: {self._format_verification_history()}"
        )

    def _format_verification_history(self) -> str:
        """Format verification history for debugging."""
        return "\n".join(
            f"[{v['timestamp']}] {v['table']}: "
            f"expected={v['expected']}, actual={v['actual']}, "
            f"{'✓' if v['success'] else '✗'}"
            for v in self.verification_log
        )


class TransactionTestCase:
    """Base class for transaction-based test cases."""

    def __init__(self, session_factory: TestSessionLocal):
        self.session_factory = session_factory
        self.verifier: Optional[DatabaseStateVerifier] = None

    async def setup(self, session: AsyncSession):
        """Setup test environment with proper transaction isolation."""
        self.verifier = DatabaseStateVerifier(session)
        async with session.begin():
            await self._perform_setup(session)

    async def run_test(self, session: AsyncSession):
        """Execute test with transaction control."""
        try:
            async with session.begin():
                await self._setup_initial_state(session)
                await self.verifier.verify_row_count("test_rollback", 2)
                await self._perform_test_operations(session)
                await self.verifier.verify_row_count("test_rollback", 4)
        except RollbackTestException as e:
            await handle_transaction_error(session, e)

    async def verify(self, session: AsyncSession):
        """Verify final state in isolated session."""
        self.verifier = DatabaseStateVerifier(session)
        async with session.begin():
            await self._verify_final_state(session)

    async def cleanup(self):
        """Ensure proper resource cleanup."""
        async with self.session_factory.get_session() as session:
            async with session.begin():
                await self._perform_cleanup(session)
        await self.session_factory.cleanup()

    # Methods to be implemented by subclasses
    async def _perform_setup(self, session: AsyncSession):
        """Setup operations to be implemented by subclasses."""
        raise NotImplementedError()

    async def _setup_initial_state(self, session: AsyncSession):
        """Setup initial state to be implemented by subclasses."""
        raise NotImplementedError()

    async def _perform_test_operations(self, session: AsyncSession):
        """Test operations to be implemented by subclasses."""
        raise NotImplementedError()

    async def _verify_final_state(self, session: AsyncSession):
        """Final state verification to be implemented by subclasses."""
        raise NotImplementedError()

    async def _verify_rollback_state(self, session: AsyncSession):
        """Rollback state verification to be implemented by subclasses."""
        raise NotImplementedError()

    async def _perform_cleanup(self, session: AsyncSession):
        """Cleanup operations to be implemented by subclasses."""
        raise NotImplementedError()


async def handle_transaction_error(trans, error: Exception) -> None:
    """Handle transaction errors with proper logging and cleanup."""
    logger.error(f"Transaction error: {error}")
    try:
        await trans.rollback()
        logger.info("Transaction rolled back successfully")
    except Exception as rollback_error:
        logger.error(f"Rollback failed: {rollback_error}")
        raise RuntimeError("Failed to rollback transaction") from rollback_error


async def manage_test_session(
    session_factory: TestSessionLocal, operation: Callable
) -> None:
    """Manage test session lifecycle with proper cleanup."""
    async with session_factory.get_session() as session:
        await operation(session)
