import os
from pathlib import Path
import shutil
from datetime import datetime

def create_directory_structure():
    base_path = Path("c:/backtestai/backtest/project_control")
    
    # Create new directories
    directories = [
        "history/chats",
        "history/checkpoints",
        "state/checklists"
    ]
    
    for dir_path in directories:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

def move_files():
    source_dir = Path("c:/backtestai/backtest/project_context")
    target_dir = Path("c:/backtestai/backtest/project_control")
    
    # Create backup
    backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = target_dir / "backups" / f"context_backup_{backup_time}"
    shutil.copytree(source_dir, backup_dir)
    print(f"Created backup at: {backup_dir}")
    
    # Move files to appropriate directories
    for file_path in source_dir.glob("*"):
        if file_path.name.lower().startswith(("chat", "Chat")):
            target = target_dir / "history/chats" / file_path.name
            shutil.move(str(file_path), str(target))
            print(f"Moved chat file: {file_path.name}")
            
        elif file_path.name.lower().startswith("checkpoint"):
            target = target_dir / "history/checkpoints" / file_path.name
            shutil.move(str(file_path), str(target))
            print(f"Moved checkpoint file: {file_path.name}")
            
        elif file_path.name.lower().endswith(("checklist.md", "checklist")):
            target = target_dir / "state/checklists" / file_path.name
            shutil.move(str(file_path), str(target))
            print(f"Moved checklist file: {file_path.name}")

def remove_empty_directory():
    dir_path = Path("c:/backtestai/backtest/project_context")
    if dir_path.exists():
        if not any(dir_path.iterdir()):
            dir_path.rmdir()
            print(f"Removed empty directory: {dir_path}")
        else:
            print(f"Warning: Directory not empty: {dir_path}")
            print("Remaining files:")
            for file in dir_path.iterdir():
                print(f"- {file.name}")

def main():
    print("Starting reorganization...")
    create_directory_structure()
    move_files()
    remove_empty_directory()
    print("Reorganization complete!")

if __name__ == "__main__":
    main()
