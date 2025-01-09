@echo off
setlocal

:: Set environment variables for testing
set ENV=test
set PYTHONPATH=.

:: Create logs directory if it doesn't exist
if not exist logs mkdir logs

:: Run database setup
python scripts/manage_db.py setup-test
if errorlevel 1 exit /b 1

:: Run tests with coverage
pytest --verbose ^
    --cov=./ ^
    --cov-report=xml ^
    --cov-report=term-missing ^
    --cov-config=.coveragerc ^
    %*

:: Store the exit code
set exit_code=%errorlevel%

:: Clean up test database
python scripts/manage_db.py setup-test --cleanup

exit /b %exit_code%
