#!/bin/bash

# Set environment variables for testing
export ENV=test
export PYTHONPATH=.

# Create logs directory if it doesn't exist
mkdir -p logs

# Run database setup
python scripts/manage_db.py setup-test

# Run tests with coverage
pytest --verbose \
    --cov=./ \
    --cov-report=xml \
    --cov-report=term-missing \
    --cov-config=.coveragerc \
    "$@"

# Store the exit code
exit_code=$?

# Clean up test database
python scripts/manage_db.py setup-test --cleanup

exit $exit_code
