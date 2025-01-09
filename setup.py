"""Setup configuration."""

from setuptools import setup, find_packages

setup(
    name="backtest",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "alembic",
        "psycopg2-binary",
        "pytest",
        "pytest-asyncio",
        "httpx",
        "redis",
        "python-dotenv",
    ],
)
