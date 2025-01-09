"""Test environment configuration module."""

import os
from pathlib import Path

# Set test environment
os.environ["ENV"] = "test"
os.environ["TESTING"] = "true"

# Load test environment variables
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env.test")

# Import settings after environment is configured
from core.config.settings import settings

# Test database configuration
TEST_DATABASE_URL = (
    f"postgresql://{settings.database.DB_USER}:{settings.database.DB_PASSWORD}"
    f"@{settings.database.DB_HOST}:{settings.database.DB_PORT}/{settings.database.TEST_DB_NAME}"
)
