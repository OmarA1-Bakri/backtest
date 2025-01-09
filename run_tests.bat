@echo off
setlocal

REM Set environment variables
set PYTHONPATH=%~dp0
set ENV=test

REM Run the tests
python -m pytest tests/database/test_migrations.py -v -s --log-cli-level=INFO
