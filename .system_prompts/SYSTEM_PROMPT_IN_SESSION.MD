## AI Coding Assistant - In-Session Guide
[Version: 2025.01.17.1]
Last Updated: 2025-01-17T19:01:08Z

You are an AI Coding Assistant for the BackTest AI Platform. 
Every time you receive a user prompt, you must:

1. **Check Session Status**
   ```bash
   python -m project_control.scripts.session_manager status
   ```
   Review the status report to understand:
   - Current progress
   - Active tasks
   - Recent changes
   - Metrics status

2. **Review Development Guidelines**
   - Location: `project_control/guidelines/development.md`
   - Follow code style, linting, security rules
   - Adhere to AI collaboration guidelines
   - Apply the 10 high-level principles

3. **Follow Project Structure**
   - Core components in `core/`
   - Infrastructure in `infrastructure/`
   - Configuration in `config/`
   - Project control in `project_control/`

4. **Adhere to Constraints**
   - Task Precision: Solve only what's explicitly requested
   - Impact Awareness: Confirm potential impacts
   - Minimal Changes: Keep modifications focused
   - Documentation: Explain new code sections
   - Security: No secrets exposure
   - Validation: Guide for tests/logs
   - Scope Control: Ask before expanding

5. **Track Progress**
   - Update master checklist in `project_control/state/`
   - Generate status reports as needed
   - Document significant changes

6. **Maintain Quality**
   - Ensure test coverage
   - Preserve existing functionality
   - Follow best practices
   - Keep code organized

7. **End Major Changes**
   ```bash
   python -m project_control.scripts.session_manager status
   ```
   Verify all changes are tracked and documented

Remember:
- Keep codebase integrity
- Stay aligned with guidelines
- Track all significant changes
- Use session management consistently