import pytest
import shutil
from pathlib import Path


@pytest.fixture
def workflow_dir(tmp_path):
    """Create a temporary workflow directory for testing."""
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    return workflows


@pytest.fixture
def mock_workflow(workflow_dir):
    """Copy mock workflow file to temporary directory."""
    mock_file = Path(__file__).parent / "fixtures" / "mock_workflow.yml"
    dest = workflow_dir / "mock_workflow.yml"
    shutil.copy(mock_file, dest)
    return dest
