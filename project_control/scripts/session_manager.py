import click
import git
from datetime import datetime
from pathlib import Path
from typing import Optional
import yaml
from rich.console import Console
from rich.table import Table
import json

class SessionManager:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.console = Console()
        self.repo = git.Repo(repo_path)
        self.session_file = repo_path / "project_control" / "state" / "current_session.json"
        self.checklist_file = repo_path / "project_control" / "state" / "master_checklist.yaml"

    def start_session(self):
        """Start a new development session."""
        # Ensure clean git state
        if self.repo.is_dirty():
            self._auto_commit("Auto-commit before session start")

        # Record session start
        session_data = {
            "start_time": datetime.now().isoformat(),
            "completed_items": [],
            "modified_files": [],
            "metrics_snapshot": self._get_metrics_snapshot()
        }
        
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.session_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        self._generate_status_report("start")
        
    def end_session(self):
        """End the current session and generate report."""
        if not self.session_file.exists():
            self.console.print("[red]No active session found!")
            return

        # Auto-commit changes
        if self.repo.is_dirty():
            self._auto_commit("Auto-commit at session end")

        # Update session data
        with open(self.session_file, 'r') as f:
            session_data = json.load(f)
        
        session_data["end_time"] = datetime.now().isoformat()
        session_data["final_metrics"] = self._get_metrics_snapshot()
        
        # Generate end report
        self._generate_status_report("end", session_data)
        
        # Archive session data
        archive_path = self.repo_path / "project_control" / "reports" / "sessions"
        archive_path.mkdir(parents=True, exist_ok=True)
        archive_file = archive_path / f"session_{session_data['start_time'][:10]}.json"
        with open(archive_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        # Clean up current session
        self.session_file.unlink()

    def status_update(self):
        """Generate current status report."""
        if not self.session_file.exists():
            self.console.print("[red]No active session found!")
            return

        self._generate_status_report("update")

    def _auto_commit(self, message: str):
        """Automatically commit changes with given message."""
        self.repo.git.add(A=True)
        self.repo.index.commit(message)

    def _get_metrics_snapshot(self):
        """Collect current project metrics."""
        return {
            "completed_tasks": self._count_completed_tasks(),
            "test_coverage": self._get_test_coverage(),
            "performance_metrics": self._get_performance_metrics()
        }

    def _generate_status_report(self, report_type: str, session_data: Optional[dict] = None):
        """Generate status report based on type."""
        if session_data is None and self.session_file.exists():
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)

        table = Table(title=f"Project Status Report ({report_type})")
        
        if report_type == "start":
            self._generate_start_report(table)
        elif report_type == "end":
            self._generate_end_report(table, session_data)
        else:
            self._generate_update_report(table, session_data)

        self.console.print(table)

    def _count_completed_tasks(self):
        """Count completed tasks from checklist."""
        if not self.checklist_file.exists():
            return 0
        
        with open(self.checklist_file, 'r') as f:
            checklist = yaml.safe_load(f)
        
        return sum(1 for task in self._flatten_tasks(checklist) if task.get('status') == 'completed')

    def _get_test_coverage(self):
        """Get current test coverage metrics."""
        # TODO: Implement test coverage collection
        return {}

    def _get_performance_metrics(self):
        """Get current performance metrics."""
        # TODO: Implement performance metrics collection
        return {}

    def _generate_start_report(self, table):
        """Generate start of session report."""
        table.add_column("Metric")
        table.add_column("Value")
        
        metrics = self._get_metrics_snapshot()
        table.add_row("Tasks Completed", str(metrics["completed_tasks"]))
        table.add_row("Git Status", "Clean" if not self.repo.is_dirty() else "Uncommitted changes")

    def _generate_end_report(self, table, session_data):
        """Generate end of session report."""
        table.add_column("Metric")
        table.add_column("Start")
        table.add_column("End")
        
        start_metrics = session_data["metrics_snapshot"]
        end_metrics = session_data["final_metrics"]
        
        table.add_row(
            "Tasks Completed",
            str(start_metrics["completed_tasks"]),
            str(end_metrics["completed_tasks"])
        )

    def _generate_update_report(self, table, session_data):
        """Generate update report."""
        table.add_column("Metric")
        table.add_column("Value")
        
        current_metrics = self._get_metrics_snapshot()
        table.add_row("Tasks Completed", str(current_metrics["completed_tasks"]))
        table.add_row("Git Status", "Clean" if not self.repo.is_dirty() else "Uncommitted changes")

    def _flatten_tasks(self, checklist, parent_key=''):
        """Flatten nested checklist structure."""
        tasks = []
        for key, value in checklist.items():
            new_key = f"{parent_key}.{key}" if parent_key else key
            if isinstance(value, dict):
                if 'status' in value:
                    tasks.append(value)
                else:
                    tasks.extend(self._flatten_tasks(value, new_key))
        return tasks

@click.group()
def cli():
    """BackTest AI Project Session Manager"""
    pass

@cli.command()
def start():
    """Start a new development session"""
    manager = SessionManager(Path.cwd())
    manager.start_session()

@cli.command()
def end():
    """End current development session"""
    manager = SessionManager(Path.cwd())
    manager.end_session()

@cli.command()
def status():
    """Show current session status"""
    manager = SessionManager(Path.cwd())
    manager.status_update()

if __name__ == '__main__':
    cli()
