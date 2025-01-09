@echo off
setlocal

:: Set PostgreSQL path (adjust this path according to your installation)
set PGBIN=C:\Program Files\PostgreSQL\16\bin
set PATH="%PGBIN%";%PATH%

:: Set PostgreSQL password
set PGPASSWORD=456852

:: Drop test database if it exists
"%PGBIN%\psql" -U postgres -d postgres -c "DROP DATABASE IF EXISTS backtest_test;"
if %errorlevel% neq 0 (
    echo Failed to drop test database
    exit /b 1
)

:: Create test database
"%PGBIN%\psql" -U postgres -d postgres -c "CREATE DATABASE backtest_test;"
if %errorlevel% neq 0 (
    echo Failed to create test database
    exit /b 1
)

:: Run the setup script on the test database
"%PGBIN%\psql" -U postgres -d backtest_test -f scripts\setup_db.sql
if %errorlevel% neq 0 (
    echo Failed to run setup script
    exit /b 1
)

echo PostgreSQL setup completed successfully
exit /b 0
