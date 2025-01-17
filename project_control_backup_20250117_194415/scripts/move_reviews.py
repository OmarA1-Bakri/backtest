import os
from pathlib import Path
import shutil
from datetime import datetime


def setup_reviews_directory():
    base_path = Path("c:/backtestai/backtest/project_control")
    reviews_path = base_path / "reviews"
    reviews_path.mkdir(exist_ok=True)
    return reviews_path


def backup_reviews():
    source_dir = Path("c:/backtestai/backtest/.code_reviews")
    backup_dir = (
        Path("c:/backtestai/backtest/project_control/backups")
        / f"code_reviews_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    if source_dir.exists():
        shutil.copytree(source_dir, backup_dir)
        print(f"Created backup at: {backup_dir}")


def move_reviews():
    source_dir = Path("c:/backtestai/backtest/.code_reviews")
    target_dir = Path("c:/backtestai/backtest/project_control/reviews")

    if source_dir.exists():
        for file_path in source_dir.glob("*"):
            # Convert filename to a more readable format
            # e.g., 9_1_25.md -> 2025_01_09_review.md
            if file_path.name.endswith(".md"):
                parts = file_path.stem.split("_")
                if len(parts) == 3:
                    day, month, year = parts
                    new_name = f"20{year}_{month.zfill(2)}_{day.zfill(2)}_review.md"
                    target = target_dir / new_name
                else:
                    target = target_dir / file_path.name

                shutil.move(str(file_path), str(target))
                print(f"Moved review file: {file_path.name} -> {target.name}")


def remove_old_directory():
    dir_path = Path("c:/backtestai/backtest/.code_reviews")
    if dir_path.exists():
        if not any(dir_path.iterdir()):
            shutil.rmtree(dir_path)
            print(f"Removed old directory: {dir_path}")
        else:
            print(f"Warning: Directory not empty: {dir_path}")
            for file in dir_path.iterdir():
                print(f"- {file.name}")


def main():
    print("Starting code reviews reorganization...")
    reviews_dir = setup_reviews_directory()
    backup_reviews()
    move_reviews()
    remove_old_directory()
    print("Reorganization complete!")


if __name__ == "__main__":
    main()
