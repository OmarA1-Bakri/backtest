"""Run tests with proper environment setup."""

import os
import sys
import pytest
import asyncio
from pathlib import Path


def setup_test_environment():
    """Set up test environment."""
    # Get project root
    project_root = Path(__file__).parent.absolute()

    # Add project root to Python path
    sys.path.insert(0, str(project_root))

    # Set environment variables
    os.environ["PYTHONPATH"] = str(project_root)
    os.environ["ENV"] = "test"
    os.environ["TESTING"] = "true"

    # Load test environment variables
    from dotenv import load_dotenv

    env_file = project_root / ".env.test"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        print(f"Warning: Test environment file not found at {env_file}")


async def setup_database():
    """Set up test database."""
    try:
        from scripts.setup_test_db import setup_test_database

        setup_test_database()
    except Exception as e:
        print(f"Error setting up test database: {str(e)}")
        sys.exit(1)


def run_tests():
    """Run the test suite."""
    try:
        # Set up environment
        setup_test_environment()

        # Set up test database
        asyncio.run(setup_database())

        # Run pytest
        project_root = Path(__file__).parent.absolute()
        test_path = project_root / "tests"

        # Run tests with coverage
        pytest_args = [
            "-v",
            "--import-mode=importlib",
            "--cov=.",
            "--cov-report=term-missing",
            str(test_path),
        ]

        return pytest.main(pytest_args)

    except Exception as e:
        print(f"Error running tests: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
