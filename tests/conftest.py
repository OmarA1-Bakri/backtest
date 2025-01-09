"""Test configuration module."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from redis.asyncio import Redis
from sqlalchemy import text

from api.deps import get_session
from core.config.settings import Settings, get_settings, SecretStr
from database.base import Base


def get_settings_override():
    """Get settings override for testing.

    Only override the minimum settings needed for testing.
    Keep the rest from the .env file.
    """
    settings = get_settings()  # Get settings from .env

    # Override only what's needed for tests
    settings.TESTING = True
    settings.DEBUG = True
    settings.DB_NAME = "backtest_test"
    settings.REDIS_DB = 1
    settings.SECRET_KEY = SecretStr("test-secret-key")
    settings.DB_PASSWORD = SecretStr("456852")

    return settings


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_app() -> FastAPI:
    """Create a test app with overridden settings."""
    from api.app import app

    app.dependency_overrides[get_settings] = get_settings_override
    return app


@pytest.fixture
async def test_db_engine():
    """Create a test database engine."""
    settings = get_settings_override()
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=settings.DB_ECHO,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
    )

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
def test_session_maker(test_db_engine):
    """Create a test session maker."""
    return sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture
async def test_session(test_session_maker) -> AsyncGenerator[AsyncSession, None]:
    """Create a test session."""
    async with test_session_maker() as session:
        try:
            await session.begin()  # Start a transaction
            yield session
            await session.rollback()  # Rollback any changes
        finally:
            await session.close()


@pytest.fixture(autouse=True)
async def clean_database(test_db_engine):
    """Clean database before each test."""
    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(autouse=True)
async def clean_redis():
    """Clean Redis database before each test."""
    settings = get_settings_override()
    redis = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD.get_secret_value(),
        decode_responses=True,
    )
    try:
        await redis.flushdb()
        yield redis
    finally:
        await redis.close()


@pytest.fixture
async def test_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client
