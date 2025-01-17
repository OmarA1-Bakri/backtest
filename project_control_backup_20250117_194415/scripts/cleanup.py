import os
import shutil
from pathlib import Path
import logging
from datetime import datetime
import git

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ProjectCleanup:
    def __init__(self, root_dir: str = None):
        self.root_dir = Path(root_dir or os.getcwd())
        self.backup_dir = (
            self.root_dir
            / "project_control"
            / "backups"
            / datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        self.repo = git.Repo(self.root_dir)

    def create_backup(self, file_path: Path) -> Path:
        """Create backup of a file before moving/deleting it."""
        if not file_path.exists():
            return None

        backup_path = self.backup_dir / file_path.relative_to(self.root_dir)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        return backup_path

    def create_directories(self):
        """Create new directory structure."""
        directories = [
            "core/broker",
            "core/data",
            "infrastructure/workers",
            "config/env",
            "project_control/guidelines",
            "project_control/backups",
            "project_control/state",
            "project_control/reports/sessions",
        ]

        for dir_path in directories:
            full_path = self.root_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")

    def move_files(self):
        """Move files to their new locations."""
        moves = {
            "broker.py": "core/broker/broker.py",
            "data.py": "core/data/market_data.py",
            "data_processing.py": "core/data/processing.py",
            "celery_worker.py": "infrastructure/workers/celery_worker.py",
            "dependencies.py": "infrastructure/dependencies.py",
            ".env": "config/env/.env",
            ".env.test": "config/env/.env.test",
            "DEVELOPMENT_GUIDELINES.md": "project_control/guidelines/development.md",
            "DEPLOYMENT.md": "project_control/guidelines/deployment.md",
        }

        for src, dst in moves.items():
            src_path = self.root_dir / src
            dst_path = self.root_dir / dst

            if src_path.exists():
                self.create_backup(src_path)
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(src_path, dst_path)
                logger.info(f"Moved {src} to {dst}")
            else:
                logger.warning(f"Source file not found: {src}")

    def remove_files(self):
        """Remove unnecessary files."""
        files_to_remove = [
            "all-files.txt",
            "sorted-files.txt",
            ".coverage",
            "coverage.xml",
        ]

        for file in files_to_remove:
            file_path = self.root_dir / file
            if file_path.exists():
                self.create_backup(file_path)
                file_path.unlink()
                logger.info(f"Removed file: {file}")
            else:
                logger.warning(f"File not found for removal: {file}")

    def commit_changes(self):
        """Commit the reorganization changes."""
        try:
            self.repo.git.add(A=True)
            self.repo.index.commit(
                "Project reorganization: Clean up root directory structure"
            )
            logger.info("Changes committed to git")
        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")

    def cleanup(self):
        """Execute the cleanup process."""
        logger.info("Starting project cleanup...")

        try:
            self.create_directories()
            self.move_files()
            self.remove_files()
            self.commit_changes()
            logger.info("Project cleanup completed successfully!")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise


def main():
    cleanup = ProjectCleanup()
    cleanup.cleanup()


if __name__ == "__main__":
    main()
