# .project_control Directory Index
[Version: 2025.01.17.1]
Last Updated: 2025-01-17T19:45:17Z

## Overview
The `.project_control` directory serves as the central hub for project management, documentation, and development tracking. This directory contains all project-related artifacts, including development history, code reviews, session management, and project state tracking.

## Directory Structure

### 📂 backups/
Automated backups of project state and reorganization operations.
- `context_backup_[timestamp]/` - Backups of project context
- `code_reviews_backup_[timestamp]/` - Backups of code reviews

### 📂 guidelines/
Project standards and development guidelines.
- `documentation_standards.md` - Standards for project documentation
- `cross_reference_guide.md` - Guide for cross-referencing system
- `metrics_documentation.md` - Documentation for project metrics

### 📂 history/
Historical records of development sessions and progress.
```
history/
├── chats/           # Development chat histories
│   └── chat_[date].md
└── checkpoints/     # Development checkpoints
    └── checkpoint_[number].md
```

### 📂 reviews/
Code review documentation and feedback.
- `YYYY_MM_DD_review.md` - Dated code review files

### 📂 scripts/
Utility scripts for project management.
- `cleanup.py` - Project structure maintenance
- `session_manager.py` - Development session management
- `checklist_manager.py` - Project checklist management

### 📂 state/
Current project state and tracking.
```
state/
└── checklists/     # Project checklists
    ├── development_checklist.md
    ├── copy_development_checklist.md
    └── SessionChecklist.md
```

### 📂 templates/
Templates for project documentation.
- `document_template.md` - Standard document template
- `checklist_template.yaml` - Checklist template
- `session_report_template.md` - Session report template

## Usage Guidelines

### 1. Session Management
- Start a new session: `python scripts/session_manager.py start`
- End session: `python scripts/session_manager.py end`
- Check status: `python scripts/session_manager.py status`

### 2. Documentation
- Follow `documentation_standards.md` for all new documents
- Use appropriate templates from `templates/`
- Store session chat histories in `history/chats/`
- Record checkpoints in `history/checkpoints/`

### 3. Code Reviews
- Store code reviews in `reviews/` using the format: `YYYY_MM_DD_review.md`
- Include both feedback and action items
- Reference related files using `@[filename]` syntax

### 4. Project State
- Track development progress in `state/checklists/`
- Use `checklist_manager.py` for checklist updates
- Regular backups are stored in `backups/`

## File Organization Rules

1. **Naming Conventions**
   - Dates: `YYYY_MM_DD` format
   - Chat files: `chat_[date].md`
   - Reviews: `YYYY_MM_DD_review.md`
   - Checkpoints: `checkpoint_[number].md`

2. **Cross-References**
   - Use `@[filename]` for file references
   - Use `#[section-name]` for section references
   - Use `$[metric-name]` for metric references

3. **Version Control**
   - Include version number in format: `YYYY.MM.DD.N`
   - Update timestamp in ISO format
   - Document changes in change log section

## Maintenance

The `.project_control` directory is maintained through several automated scripts:
1. `cleanup.py` - Organizes and validates directory structure
2. `session_manager.py` - Manages development sessions
3. `checklist_manager.py` - Handles project checklists

Regular maintenance tasks:
- Review and archive old chat histories
- Update checklists and progress tracking
- Validate cross-references
- Clean up outdated backups

## Related Files
- @[README.md] - Main project documentation
- @[DEVELOPMENT_GUIDELINES.md] - Development standards
- @[.system_prompts/] - System prompt files
