"""
Comprehensive test runner for the BackTest AI project.
Runs all backend and frontend tests with coverage reporting.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, cwd=None):
    """Run a command and return its success status."""
    try:
        subprocess.run(command, check=True, cwd=cwd, shell=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return False


def setup_test_environment():
    """Setup test environment including dependencies."""
    print("\n=== Setting up test environment ===")

    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Add project root to Python path
    sys.path.insert(0, str(project_root))

    # Set up environment variables for testing
    os.environ["TESTING"] = "true"
    os.environ["DB_NAME"] = "test_db"
    os.environ["PYTHONPATH"] = str(project_root)

    print("Test environment setup complete")
    return True


def run_backend_tests():
    """Run all backend tests with coverage."""
    print("\n=== Running Backend Tests ===")

    # Run pytest with coverage
    success = run_command(
        "python -m pytest --cov=./ --cov-report=xml --cov-report=html --verbose"
    )

    if not success:
        print("Backend tests failed")
        return False

    print("Backend tests completed successfully")
    return True


def run_frontend_tests():
    """Run frontend tests including unit tests."""
    print("\n=== Running Frontend Tests ===")

    frontend_dir = "Frontend"

    # Install frontend dependencies if needed
    if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
        if not run_command("npm ci", cwd=frontend_dir):
            print("Failed to install frontend dependencies")
            return False

    # Run ESLint
    if not run_command(
        "npm run lint -- --no-error-on-unmatched-pattern", cwd=frontend_dir
    ):
        print("ESLint checks failed")
        return False

    # Run TypeScript checks
    if not run_command("npm run type-check", cwd=frontend_dir):
        print("TypeScript checks failed")
        return False

    # Run unit tests
    if not run_command("npm run test", cwd=frontend_dir):
        print("Frontend unit tests failed")
        return False

    print("Frontend tests completed successfully")
    return True


def main():
    """Main test runner function."""
    # Setup
    if not setup_test_environment():
        sys.exit(1)

    # Run tests
    backend_success = run_backend_tests()
    frontend_success = run_frontend_tests()

    # Print summary
    print("\n=== Test Summary ===")
    print("Backend Tests:", "PASSED" if backend_success else "FAILED")
    print("Frontend Tests:", "PASSED" if frontend_success else "FAILED")

    # Exit with appropriate status
    if not (backend_success and frontend_success):
        sys.exit(1)


if __name__ == "__main__":
    main()
