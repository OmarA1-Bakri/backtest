import os
from pathlib import Path
import yaml
from datetime import datetime
from typing import Dict, List, Optional
import json
from rich.console import Console
from rich.table import Table
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

class ChecklistManager:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.checklist_path = repo_path / "project_control" / "state"
        self.template_path = repo_path / "project_control" / "templates"
        self.console = Console()
        self.current_checklist = None

    def create_checklist(self, name: str, template: str = "checklist_template.yaml") -> None:
        """Create a new checklist from template."""
        template_file = self.template_path / template
        target_file = self.checklist_path / f"{name}.yaml"

        if not template_file.exists():
            raise FileNotFoundError(f"Template {template} not found")

        if target_file.exists():
            raise FileExistsError(f"Checklist {name} already exists")

        # Load and customize template
        with open(template_file, 'r') as f:
            checklist = yaml.safe_load(f)

        # Update metadata
        checklist['version'] = datetime.now().strftime("%Y.%m.%d.1")
        checklist['last_updated'] = datetime.now().isoformat()

        # Save new checklist
        with open(target_file, 'w') as f:
            yaml.dump(checklist, f, sort_keys=False)

        self.console.print(f"[green]Created new checklist: {name}[/green]")

    def load_checklist(self, name: str) -> Dict:
        """Load a checklist."""
        file_path = self.checklist_path / f"{name}.yaml"
        if not file_path.exists():
            raise FileNotFoundError(f"Checklist {name} not found")

        with open(file_path, 'r') as f:
            self.current_checklist = yaml.safe_load(f)
        return self.current_checklist

    def save_checklist(self, name: str = None) -> None:
        """Save current checklist."""
        if not self.current_checklist:
            raise ValueError("No checklist loaded")

        name = name or self.current_checklist.get('title', 'checklist')
        file_path = self.checklist_path / f"{name}.yaml"

        # Update metadata
        self.current_checklist['last_updated'] = datetime.now().isoformat()

        with open(file_path, 'w') as f:
            yaml.dump(self.current_checklist, f, sort_keys=False)

        self.console.print(f"[green]Saved checklist: {name}[/green]")

    def update_item_status(self, category: str, item: str, status: str) -> None:
        """Update status of a checklist item."""
        if not self.current_checklist:
            raise ValueError("No checklist loaded")

        try:
            self.current_checklist['categories'][category]['items'][item]['status'] = status
            self._update_metrics()
            self.console.print(f"[green]Updated status of {category}.{item} to {status}[/green]")
        except KeyError:
            raise KeyError(f"Item {category}.{item} not found in checklist")

    def _update_metrics(self) -> None:
        """Update checklist metrics."""
        if not self.current_checklist:
            return

        metrics = {
            'completed': 0,
            'in_progress': 0,
            'blocked': 0,
            'pending': 0
        }

        for category in self.current_checklist['categories'].values():
            for item in category['items'].values():
                metrics[item['status']] += 1

        self.current_checklist['metrics']['completion'].update({
            'total_items': sum(metrics.values()),
            **metrics
        })

    def generate_report(self, format: str = 'console') -> None:
        """Generate a report of the checklist status."""
        if not self.current_checklist:
            raise ValueError("No checklist loaded")

        if format == 'console':
            self._generate_console_report()
        elif format == 'markdown':
            return self._generate_markdown_report()
        elif format == 'json':
            return self._generate_json_report()
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_console_report(self) -> None:
        """Generate a console report using rich."""
        table = Table(title=f"Checklist Report: {self.current_checklist.get('title', 'Untitled')}")
        
        table.add_column("Category")
        table.add_column("Item")
        table.add_column("Status")
        table.add_column("Priority")
        table.add_column("Assignee")
        
        for cat_name, category in self.current_checklist['categories'].items():
            for item_name, item in category['items'].items():
                table.add_row(
                    cat_name,
                    item_name,
                    item['status'],
                    item['priority'],
                    item.get('assignee', 'Unassigned')
                )
        
        self.console.print(table)

    def analyze_dependencies(self) -> None:
        """Analyze and visualize checklist dependencies."""
        if not self.current_checklist:
            raise ValueError("No checklist loaded")

        # Create dependency graph
        G = nx.DiGraph()
        
        for cat_name, category in self.current_checklist['categories'].items():
            for item_name, item in category['items'].items():
                node_id = f"{cat_name}.{item_name}"
                G.add_node(node_id, **item)
                
                for dep in item.get('dependencies', []):
                    G.add_edge(dep, node_id)

        # Find cycles
        cycles = list(nx.simple_cycles(G))
        if cycles:
            self.console.print("[red]Warning: Dependency cycles detected![/red]")
            for cycle in cycles:
                self.console.print(f"Cycle: {' -> '.join(cycle)}")

        # Critical path
        try:
            critical_path = nx.dag_longest_path(G)
            self.console.print("\n[green]Critical Path:[/green]")
            self.console.print(" -> ".join(critical_path))
        except nx.NetworkXUnfeasible:
            self.console.print("[yellow]Cannot determine critical path due to cycles[/yellow]")

        # Visualize
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_color='lightblue', 
                node_size=1500, font_size=8, font_weight='bold')
        plt.title("Dependency Graph")
        plt.savefig(self.repo_path / "project_control" / "reports" / "dependency_graph.png")
        plt.close()

    def export_excel(self, output_path: str) -> None:
        """Export checklist to Excel format."""
        if not self.current_checklist:
            raise ValueError("No checklist loaded")

        # Flatten checklist data
        data = []
        for cat_name, category in self.current_checklist['categories'].items():
            for item_name, item in category['items'].items():
                data.append({
                    'Category': cat_name,
                    'Item': item_name,
                    'Description': item['description'],
                    'Status': item['status'],
                    'Priority': item['priority'],
                    'Assignee': item.get('assignee', ''),
                    'Deadline': item.get('deadline', ''),
                    'Dependencies': ', '.join(item.get('dependencies', [])),
                    'Notes': item.get('notes', '')
                })

        df = pd.DataFrame(data)
        df.to_excel(output_path, index=False)
        self.console.print(f"[green]Exported checklist to {output_path}[/green]")

def main():
    """CLI interface for checklist management."""
    import click

    @click.group()
    def cli():
        """BackTest AI Project Checklist Manager"""
        pass

    @cli.command()
    @click.argument('name')
    def create(name):
        """Create a new checklist"""
        manager = ChecklistManager(Path.cwd())
        manager.create_checklist(name)

    @cli.command()
    @click.argument('name')
    def load(name):
        """Load and display a checklist"""
        manager = ChecklistManager(Path.cwd())
        manager.load_checklist(name)
        manager.generate_report()

    @cli.command()
    @click.argument('name')
    @click.argument('category')
    @click.argument('item')
    @click.argument('status')
    def update(name, category, item, status):
        """Update item status"""
        manager = ChecklistManager(Path.cwd())
        manager.load_checklist(name)
        manager.update_item_status(category, item, status)
        manager.save_checklist()

    @cli.command()
    @click.argument('name')
    def analyze(name):
        """Analyze checklist dependencies"""
        manager = ChecklistManager(Path.cwd())
        manager.load_checklist(name)
        manager.analyze_dependencies()

    @cli.command()
    @click.argument('name')
    @click.argument('output')
    def export(name, output):
        """Export checklist to Excel"""
        manager = ChecklistManager(Path.cwd())
        manager.load_checklist(name)
        manager.export_excel(output)

    cli()
