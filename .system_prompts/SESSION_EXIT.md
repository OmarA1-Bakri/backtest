## Session Exit Prompt
[Version: 2025.01.17.1]
Last Updated: 2025-01-17T19:01:08Z

**Objective**  
Perform a detailed review of this session and update project documentation accordingly.

### 1. End Session and Generate Report
```bash
python -m project_control.scripts.session_manager end
```
Review the generated report for:
- Completed tasks
- Modified files
- Metrics changes
- Session duration

### 2. Review Session Artifacts

1. **Session Report**
   - Location: `project_control/reports/sessions/`
   - Review auto-generated end-of-session report
   - Verify metrics and progress

2. **Master Checklist**
   - Location: `project_control/state/master_checklist.yaml`
   - Verify task status updates
   - Ensure new tasks are added if created

3. **Documentation Updates**
   - Guidelines: `project_control/guidelines/`
   - API docs: `docs/api/`
   - Examples: `docs/examples/`

### 3. Verify File Organization

1. **Core Components**
   - Check changes in `core/`
   - Verify broker/data processing updates
   - Review strategy modifications

2. **Infrastructure**
   - Review `infrastructure/` changes
   - Check worker configurations
   - Verify monitoring setup

3. **Configuration**
   - Verify `config/env/` files
   - Check for sensitive data exposure
   - Validate environment settings

### 4. Final Checks

1. **Code Quality**
   - All tests passing
   - Documentation updated
   - No sensitive data exposed

2. **Git Status**
   - Clean working directory
   - Meaningful commit messages
   - No untracked files

3. **Project State**
   - Clear next steps documented
   - All TODOs captured in checklist
   - Dependencies up to date

**Reminder**:  
- The session manager handles auto-commits and report generation
- Follow the project structure for all updates
- Keep documentation in sync with changes
- Use `python -m project_control.scripts.session_manager status` for final verification