"""Database configuration module."""

from typing import Dict, Any
from pydantic import BaseSettings, PostgresDsn

from core.config.settings import settings


class DatabaseSettings(BaseSettings):
    """Database settings."""

    DB_HOST: str = settings.DB_HOST
    DB_PORT: int = settings.DB_PORT
    DB_NAME: str = settings.DB_NAME
    DB_USER: str = settings.DB_USER
    DB_PASSWORD: str = settings.DB_PASSWORD
    DB_POOL_SIZE: int = settings.DB_POOL_SIZE
    DB_POOL_TIMEOUT: int = settings.DB_POOL_TIMEOUT
    DB_MAX_OVERFLOW: int = settings.DB_MAX_OVERFLOW

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        """Get database URI."""
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=str(self.DB_PORT),
            path=f"/{self.DB_NAME}",
        )

    class Config:
        """Pydantic config."""

        case_sensitive = True
