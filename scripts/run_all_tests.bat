@echo off
echo Running all tests for BackTest AI project...
python scripts/run_all_tests.py
if errorlevel 1 (
    echo Tests failed!
    exit /b 1
) else (
    echo All tests passed successfully!
    exit /b 0
)
