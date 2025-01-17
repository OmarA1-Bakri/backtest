import os
from pathlib import Path
import git
import json
from datetime import datetime
import pandas as pd
from typing import Dict, List
import radon.complexity as radon
from radon.raw import analyze
from coverage import Coverage
import psutil
import time


class MetricsCollector:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.metrics_path = repo_path / "project_control" / "metrics"
        self.metrics_path.mkdir(parents=True, exist_ok=True)
        self.repo = git.Repo(repo_path)

    def collect_code_metrics(self) -> Dict:
        """Collect code-related metrics."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "files": {},
            "total": {"lines": 0, "functions": 0, "classes": 0, "complexity": 0},
        }

        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    with open(file_path, "r") as f:
                        content = f.read()

                    # Basic metrics
                    analysis = analyze(content)
                    metrics["files"][str(file_path)] = {
                        "lines": analysis.loc,
                        "blank_lines": analysis.blank,
                        "comments": analysis.comments,
                        "complexity": radon.cc_visit(content),
                    }

                    # Update totals
                    metrics["total"]["lines"] += analysis.loc

        return metrics

    def collect_git_metrics(self) -> Dict:
        """Collect git-related metrics."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "commits": {
                "total": len(list(self.repo.iter_commits())),
                "last_24h": len(list(self.repo.iter_commits(since="24.hours.ago"))),
                "last_week": len(list(self.repo.iter_commits(since="1.week.ago"))),
            },
            "branches": len(list(self.repo.heads)),
            "tags": len(list(self.repo.tags)),
            "contributors": len(set(c.author.email for c in self.repo.iter_commits())),
        }
        return metrics

    def collect_test_coverage(self) -> Dict:
        """Collect test coverage metrics."""
        cov = Coverage()
        cov.start()

        # Run tests here
        import pytest

        pytest.main(["--quiet"])

        cov.stop()
        cov.save()

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "total_coverage": cov.report(),
            "by_file": {},
        }

        for file in cov.get_data().measured_files():
            file_coverage = cov.report(file)
            metrics["by_file"][file] = file_coverage

        return metrics

    def collect_performance_metrics(self) -> Dict:
        """Collect system performance metrics."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent,
            },
        }
        return metrics

    def collect_backtesting_metrics(self, strategy_name: str) -> Dict:
        """Collect backtesting performance metrics."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy_name,
            "execution_time": 0,
            "memory_usage": 0,
            "results": {},
        }

        # Time the strategy execution
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss

        # Run backtest here
        # strategy.run()

        metrics["execution_time"] = time.time() - start_time
        metrics["memory_usage"] = psutil.Process().memory_info().rss - start_memory

        return metrics

    def save_metrics(self, metric_type: str, metrics: Dict) -> None:
        """Save metrics to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = self.metrics_path / f"{metric_type}_{timestamp}.json"

        with open(file_path, "w") as f:
            json.dump(metrics, f, indent=2)

    def generate_report(self, days: int = 7) -> pd.DataFrame:
        """Generate a metrics report for the specified time period."""
        metrics_data = []

        # Collect all metric files
        for file in self.metrics_path.glob("*.json"):
            with open(file, "r") as f:
                data = json.load(f)
                metrics_data.append(data)

        # Convert to DataFrame
        df = pd.DataFrame(metrics_data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Filter by date range
        df = df[df["timestamp"] > pd.Timestamp.now() - pd.Timedelta(days=days)]

        return df


def main():
    """CLI interface for metrics collection."""
    import click

    @click.group()
    def cli():
        """BackTest AI Project Metrics Collector"""
        pass

    @cli.command()
    def collect_all():
        """Collect all metrics"""
        collector = MetricsCollector(Path.cwd())

        # Collect all metrics
        code_metrics = collector.collect_code_metrics()
        git_metrics = collector.collect_git_metrics()
        coverage_metrics = collector.collect_test_coverage()
        performance_metrics = collector.collect_performance_metrics()

        # Save metrics
        collector.save_metrics("code", code_metrics)
        collector.save_metrics("git", git_metrics)
        collector.save_metrics("coverage", coverage_metrics)
        collector.save_metrics("performance", performance_metrics)

        click.echo("All metrics collected and saved.")

    @cli.command()
    @click.option("--days", default=7, help="Number of days to include in report")
    def report(days):
        """Generate metrics report"""
        collector = MetricsCollector(Path.cwd())
        df = collector.generate_report(days)

        # Display summary
        click.echo(df.describe())

        # Save report
        report_path = (
            Path.cwd()
            / "project_control"
            / "reports"
            / f"metrics_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )
        df.to_excel(report_path)
        click.echo(f"Report saved to {report_path}")

    cli()


if __name__ == "__main__":
    main()
