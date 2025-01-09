import os
import pytest
import yaml
from pathlib import Path

WORKFLOW_DIR = Path(__file__).parent.parent.parent / ".github" / "workflows"


def load_workflow(filename):
    """Load a workflow file and return its content as a dict."""
    with open(WORKFLOW_DIR / filename, "r", encoding="utf-8") as f:
        content = f.read()
        # Remove any potential BOM and ensure proper line endings
        content = content.encode("utf-8").decode("utf-8-sig").replace("\r\n", "\n")
        result = yaml.safe_load(content)
        # Fix the boolean key issue
        if True in result and "workflow_dispatch" in result[True]:
            result["on"] = result[True]
            del result[True]
        print(f"Loaded YAML from {filename}:")
        print(result)
        return result


def test_workflow_files_exist():
    """Test that all required workflow files exist."""
    required_files = [
        "build.yml",
        "ci.yml",
        "code-quality.yml",
        "coverage.yml",
        "rollback.yml",
        "container-security.yml",
    ]
    for file in required_files:
        assert (WORKFLOW_DIR / file).exists(), f"Workflow file {file} not found"


def test_workflow_syntax():
    """Test that all workflow files are valid YAML."""
    for file in WORKFLOW_DIR.glob("*.yml"):
        try:
            load_workflow(file.name)
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in {file.name}: {str(e)}")
        except UnicodeDecodeError as e:
            pytest.fail(f"Encoding error in {file.name}: {str(e)}")


def test_build_workflow():
    """Test build workflow configuration."""
    workflow = load_workflow("build.yml")

    # Check required jobs exist
    assert "build-backend" in workflow["jobs"]
    assert "build-frontend" in workflow["jobs"]
    assert "tag-release" in workflow["jobs"]

    # Check caching is configured
    backend_job = workflow["jobs"]["build-backend"]
    assert any(
        step.get("uses", "").startswith("actions/cache@")
        for step in backend_job["steps"]
    )


def test_code_quality_workflow():
    """Test code quality workflow configuration."""
    workflow = load_workflow("code-quality.yml")

    # Check both Python and frontend quality checks
    assert "code-quality" in workflow["jobs"]
    assert "frontend-quality" in workflow["jobs"]

    # Verify required tools are installed
    quality_job = workflow["jobs"]["code-quality"]
    install_step = next(
        step
        for step in quality_job["steps"]
        if step.get("name") == "Install dependencies"
    )
    assert "flake8" in install_step["run"]
    assert "pylint" in install_step["run"]
    assert "black" in install_step["run"]


def test_coverage_workflow():
    """Test coverage workflow configuration."""
    workflow = load_workflow("coverage.yml")

    # Check coverage job exists
    assert "coverage" in workflow["jobs"]

    # Verify coverage threshold
    coverage_job = workflow["jobs"]["coverage"]
    coverage_step = next(
        step
        for step in coverage_job["steps"]
        if step.get("name") == "Run tests with coverage"
    )
    assert "--cov-fail-under=80" in coverage_step["run"]


def test_container_security_workflow():
    """Test container security workflow configuration."""
    workflow = load_workflow("container-security.yml")

    # Check required jobs exist
    assert "scan-backend" in workflow["jobs"]
    assert "scan-frontend" in workflow["jobs"]
    assert "scan-base-images" in workflow["jobs"]

    # Verify Trivy configuration
    backend_job = workflow["jobs"]["scan-backend"]
    trivy_step = next(
        step
        for step in backend_job["steps"]
        if step.get("name") == "Run Trivy vulnerability scanner"
    )
    assert trivy_step["with"]["severity"] == "CRITICAL,HIGH"


def test_rollback_workflow():
    """Test rollback workflow configuration."""
    workflow = load_workflow("rollback.yml")

    # Check workflow is manually triggered
    assert "workflow_dispatch" in workflow.get(
        "on", {}
    ), "workflow_dispatch trigger not found"

    # Check environment input
    inputs = workflow.get("on", {}).get("workflow_dispatch", {}).get("inputs", {})
    assert "environment" in inputs, "environment input not found"
    assert "options" in inputs["environment"], "environment options not found"
    assert all(
        env in inputs["environment"]["options"] for env in ["staging", "production"]
    ), "missing environment options"

    # Verify required jobs
    assert all(
        job in workflow.get("jobs", {}) for job in ["validate", "rollback", "notify"]
    ), "missing required jobs"
