"""Database utilities for testing."""

import logging
from contextlib import contextmanager
from typing import Generator, Any, Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from core.database import Base, DatabaseManager
from core.config.settings import settings

logger = logging.getLogger(__name__)


class TestDatabaseManager:
    """Test database connection and session management."""

    _test_engine: Optional[Engine] = None
    _TestSessionLocal: Optional[sessionmaker] = None

    @classmethod
    def initialize_test_db(cls) -> None:
        """Initialize test database engine and session factory."""
        if cls._test_engine is not None:
            return

        # Use test database URL
        test_db_url = settings.database.get_test_database_url()

        # Create test engine with smaller pool size for tests
        cls._test_engine = create_engine(
            test_db_url,
            pool_size=2,
            max_overflow=0,
            pool_timeout=5,
            pool_pre_ping=True,
        )

        cls._TestSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=cls._test_engine
        )

        # Create all tables in test database
        Base.metadata.create_all(bind=cls._test_engine)

    @classmethod
    def get_test_session(cls) -> Session:
        """Get a test database session."""
        if cls._TestSessionLocal is None:
            cls.initialize_test_db()
        return cls._TestSessionLocal()

    @classmethod
    @contextmanager
    def test_session_scope(cls) -> Generator[Session, Any, None]:
        """Provide a transactional scope around test operations."""
        session = cls.get_test_session()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Test database error occurred: {str(e)}")
            session.rollback()
            raise
        finally:
            session.close()

    @classmethod
    def cleanup_test_db(cls) -> None:
        """Clean up test database resources."""
        if cls._test_engine is not None:
            # Drop all tables
            Base.metadata.drop_all(bind=cls._test_engine)
            # Dispose of the engine
            cls._test_engine.dispose()
            cls._test_engine = None
        cls._TestSessionLocal = None


@contextmanager
def temp_database_session() -> Generator[Session, Any, None]:
    """Create a temporary database session for tests with automatic rollback."""
    # Initialize test database if not already done
    TestDatabaseManager.initialize_test_db()

    # Get a new session
    session = TestDatabaseManager.get_test_session()

    # Start a nested transaction
    transaction = session.begin_nested()

    try:
        yield session
        # If no exception occurred, still rollback the nested transaction
        transaction.rollback()
    except Exception as e:
        # If an exception occurred, rollback the transaction and re-raise
        transaction.rollback()
        raise
    finally:
        # Always close the session
        session.close()


def setup_test_database() -> None:
    """Set up test database before running tests."""
    # Initialize test database
    TestDatabaseManager.initialize_test_db()

    # Create all tables
    Base.metadata.create_all(bind=TestDatabaseManager._test_engine)


def teardown_test_database() -> None:
    """Clean up test database after running tests."""
    TestDatabaseManager.cleanup_test_db()
