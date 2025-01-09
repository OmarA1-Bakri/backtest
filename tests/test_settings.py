"""Test settings configuration."""

from pydantic_settings import BaseSettings
from pydantic import Field


class TestSettings(BaseSettings):
    """Test settings configuration."""

    # Environment
    env: str = Field(default="test")
    testing: bool = Field(default=True)

    # Database
    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432)
    db_user: str = Field(default="postgres")
    db_password: str = Field(default="456852")
    db_name: str = Field(default="backtest")
    test_db_name: str = Field(default="backtest_test")

    @property
    def DATABASE_URL(self) -> str:
        """Get database URL."""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def TEST_DATABASE_URL(self) -> str:
        """Get test database URL."""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.test_db_name}"

    # Redis
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: str | None = Field(default=None)

    # Security
    security_jwt_secret_key: str = Field(default="test_secret_key")
    security_jwt_algorithm: str = Field(default="HS256")
    security_access_token_expire_minutes: int = Field(default=30)
    security_refresh_token_expire_minutes: int = Field(default=10080)  # 7 days

    # API
    api_v1_str: str = Field(default="/api/v1")

    class Config:
        """Pydantic config."""

        env_file = ".env.test"
        case_sensitive = False


settings = TestSettings()
