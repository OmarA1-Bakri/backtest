## Prompt for New AI Coding Agent
[Version: 2025.01.17.1]
Last Updated: 2025-01-17T19:01:08Z

You are tasked with reviewing the BackTest project—an advanced algorithmic trading strategy backtesting platform. The project emphasizes a sleek user interface, accurate market predictions, and cutting-edge AI algorithms.

### Objectives
1. **Evaluate the project’s current state** against development goals and **production readiness**.  
2. Provide **actionable recommendations** to advance toward deployment.  
3. **Update the roadmap** with **high-impact** next steps.

### Project Structure and Management Commands

### Project Organization
The project uses `.project_control` as the central hub for project management:
```
.project_control/
├── backups/       # Automated backups
├── guidelines/    # Project standards
├── history/      # Development history
│   ├── chats/    # Chat histories
│   └── checkpoints/ # Development checkpoints
├── reviews/      # Code reviews
├── scripts/      # Management scripts
├── state/        # Project state
└── templates/    # Document templates
```

### Session Management
Use the following commands to manage development sessions:
```bash
# Start a new session
python .project_control/scripts/session_manager.py start

# Check session status
python .project_control/scripts/session_manager.py status

# End session and generate report
python .project_control/scripts/session_manager.py end
```

### Project State
Track development progress using:
```bash
# View current checklist
python .project_control/scripts/checklist_manager.py view

# Update checklist item
python .project_control/scripts/checklist_manager.py update [category] [item] [status]

# Generate checklist report
python .project_control/scripts/checklist_manager.py report
```

### Documentation
- All documentation follows standards in @[.project_control/guidelines/documentation_standards.md]
- Use templates from @[.project_control/templates/] for new documents
- Store chat histories in @[.project_control/history/chats/]
- Record checkpoints in @[.project_control/history/checkpoints/]
- Code reviews go in @[.project_control/reviews/]

### Cross-References
- Use `@[filename]` for file references
- Use `#[section-name]` for section references
- Use `$[metric-name]` for metric references

For more details, refer to @[.project_control/INDEX.md]

### Development Process
1. Start each session with:
   ```bash
   python .project_control/scripts/session_manager.py start
   ```

2. Check progress during development:
   ```bash
   python .project_control/scripts/session_manager.py status
   ```

3. End session and generate report:
   ```bash
   python .project_control/scripts/session_manager.py end
   ```

### References & Constraints
- **@project_context**: Overview of the application’s architecture, objectives, and current state.  
- **@checkpoint_33.md**: Insights from the last review session.  
- **DEVELOPMENT_GUIDELINES.md**: Coding, testing, security, and AI collaboration standards. Consult these guidelines for **best practices** and **minimal, non-intrusive** changes.  
- Propose **new dependencies** only if they demonstrably improve **production readiness** and **adhere** to best practices.  
- Maintain **security and privacy**: No sensitive information should be exposed or committed.

### Steps for Review & Development Update

1. **Contextual Evaluation**  
   - Examine the `@project_context` folder to confirm the platform’s purpose, architecture, and key features.  
   - Identify documentation/implementation gaps and summarize **objectives**, **inconsistencies**, and **missing components**.

2. **Documentation Review**  
   - Focus on **README.md** and **DEVELOPMENT_GUIDELINES.md** for clarity, setup instructions, and roadmap alignment.  
   - Provide **specific, actionable** enhancements (e.g., clarifying instructions, addressing missing dependencies).

3. **Codebase Quality Check**  
   - Analyze core files to gauge **code quality**, **error handling**, and **infrastructure completeness**.  
   - Identify **incomplete or missing features** essential for production and verify best-practice alignment.

4. **Checklist Review and Update**  
   - Review `@development_checklist` and `@sessionchecklist.md` to validate completed items.  
   - Prioritize impactful, production-focused tasks.

### Deliverables (Limit ~300 Words Each)
1. **Project Context Summary**  
   - Main findings, suggested refinements, and rationale.
2. **Documentation Insights**  
   - Key gaps, clarity improvements, or missing content.
3. **Codebase Analysis**  
   - Strengths, weaknesses, optimization opportunities, and any recommended refactoring.
4. **Updated Roadmap**  
   - Concrete next steps with priorities and brief justifications.
5. **Additional Recommendations**  
   - Ideas to enhance **workflows**, **efficiency**, or **market readiness**.

### Style & Validation
- Present findings in **bulleted lists** or concise paragraphs for clarity.  
- Refer to **DEVELOPMENT_GUIDELINES.md** for any proposed code or config changes.  
- If broader modifications are needed, **request user confirmation** before proceeding.  
- Ensure all outputs maintain **security** (no secrets exposed) and comply with your established guidelines.