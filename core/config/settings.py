"""Application settings."""

import os
import pathlib
from typing import Any, Dict, List, Optional, Union
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import (
    AnyHttpUrl,
    EmailStr,
    PostgresDsn,
    RedisDsn,
    SecretStr,
    Field,
    field_validator,
)


def parse_bool(v: Any) -> bool:
    """Parse boolean values from environment variables."""
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.lower() in ("true", "1", "t", "y", "yes", "on")
    return bool(v)


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",  # Allow extra fields from .env
    )

    # Project
    PROJECT_NAME: str = "BackTestai"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DESCRIPTION: str = (
        "BackTestai - A powerful backtesting platform for trading strategies"
    )

    # Security
    SECRET_KEY: SecretStr = SecretStr("test-secret-key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    JWT_ALGORITHM: str = "HS256"
    JWT_SECRET_KEY: str = "your_secret_key_here"
    CORS_ORIGINS: List[AnyHttpUrl] = []
    CORS_ORIGIN_REGEX: Optional[str] = None

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: SecretStr = SecretStr("123456")
    DB_NAME: str = "backtest"
    TEST_DB_NAME: str = "backtest_test"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600  # Recycle connections after 1 hour

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Get database URI."""
        db_name = self.TEST_DB_NAME if self.TESTING else self.DB_NAME
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD.get_secret_value()}@{self.DB_HOST}:{self.DB_PORT}/{db_name}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[SecretStr] = None

    # Redis Cluster Configuration
    REDIS_CLUSTER_MODE: bool = Field(
        default=False, description="Enable Redis cluster mode"
    )
    REDIS_CLUSTER_NODES: str = Field(
        default="localhost", description="Comma-separated list of Redis cluster nodes"
    )

    # Redis Sentinel Configuration
    REDIS_SENTINEL_MODE: bool = Field(
        default=False, description="Enable Redis sentinel mode"
    )
    REDIS_SENTINEL_NODES: str = Field(
        default="localhost", description="Comma-separated list of Redis sentinel nodes"
    )
    REDIS_SENTINEL_PORT: int = Field(default=26379, description="Redis sentinel port")
    REDIS_SENTINEL_PASSWORD: Optional[SecretStr] = Field(
        default=None, description="Redis sentinel password"
    )
    REDIS_MASTER_GROUP: str = Field(
        default="mymaster", description="Redis sentinel master group name"
    )

    # Testing
    TESTING: bool = False
    DEBUG: bool = False

    # Data
    DATA_FILE: str = "data.csv"
    BACKTESTS: int = 3

    @field_validator("DEBUG", "TESTING", "DB_ECHO", mode="before")
    @classmethod
    def parse_bool_values(cls, v: Any) -> bool:
        """Parse boolean values from environment variables."""
        return parse_bool(v)


@lru_cache
def get_settings() -> "Settings":
    """Get application settings."""
    return Settings()


# Create settings instance
settings = get_settings()
