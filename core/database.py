"""Database module for SQLAlchemy configuration and session management."""

from contextlib import contextmanager
from typing import Generator, Any
import logging

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError

from core.config.settings import settings

logger = logging.getLogger(__name__)

# Create declarative base for models
Base = declarative_base()


class DatabaseManager:
    """Database connection and session management."""

    _engine: Engine = None
    _SessionLocal: sessionmaker = None

    @classmethod
    def initialize(cls, database_url: str = None) -> None:
        """Initialize database engine and session factory."""
        if cls._engine is not None:
            return

        if database_url is None:
            database_url = settings.database.get_database_url()

        cls._engine = create_engine(
            database_url,
            pool_size=settings.database.DB_POOL_SIZE,
            max_overflow=settings.database.DB_MAX_OVERFLOW,
            pool_timeout=settings.database.DB_POOL_TIMEOUT,
            pool_pre_ping=True,  # Enable connection health checks
        )

        cls._SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=cls._engine
        )

    @classmethod
    def get_engine(cls) -> Engine:
        """Get SQLAlchemy engine instance."""
        if cls._engine is None:
            cls.initialize()
        return cls._engine

    @classmethod
    def get_session(cls) -> Session:
        """Create a new database session."""
        if cls._SessionLocal is None:
            cls.initialize()
        return cls._SessionLocal()

    @classmethod
    @contextmanager
    def session_scope(cls) -> Generator[Session, Any, None]:
        """Provide a transactional scope around a series of operations."""
        session = cls.get_session()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Database error occurred: {str(e)}")
            session.rollback()
            raise
        finally:
            session.close()

    @classmethod
    def dispose(cls) -> None:
        """Dispose of the current engine and session factory."""
        if cls._engine is not None:
            cls._engine.dispose()
            cls._engine = None
        cls._SessionLocal = None


# Initialize database on module import
DatabaseManager.initialize()
