# Development Guidelines for the BackTest AI Platform

These guidelines consolidate best practices for configuration management, database handling, API development, testing, AI collaboration, security, and performance. Following them ensures consistent code quality, maintainability, and reliability across the BackTest AI Platform.

---

## 1. Pre-Development Checklist

Before making any changes to the codebase, ensure you complete this checklist:

### 1.1 System Architecture Review

- [ ] Review complete directory structure in `README.md`.
- [ ] Map data flow between components:
api/ → core/ → database/ strategies/ → indicators/ → data/ risk/ → monitoring/

markdown
Copy code
- [ ] Understand key subsystems:
- Trading Engine (`strategies/`, `indicators/`, `risk/`)
- Data Management (`data/`, `database/`)
- API Layer (`api/`, `schemas/`)
- Infrastructure (`terraform/`, `monitoring/`)

### 1.2 Code Organization

**Core Components**  
- `api/`: REST API implementation  
- `core/`: Application framework and business logic  
- `data/`: Market data management  
- `database/`: Data persistence layer  
- `strategies/`: Trading strategy implementations  
- `risk/`: Risk management system  
- `monitoring/`: System observability

**Support Components**  
- `scripts/`: Development and maintenance utilities  
- `tests/`: Test suites and utilities  
- `terraform/`: Infrastructure as Code  
- `project_context/`: Development history

---

## 2. Development Standards

### 2.1 Configuration Management

1. **Settings Structure**  
 - All configuration settings must be defined in `core/config/settings.py`.
 - Use **Pydantic** for settings validation.
 - Follow consistent naming conventions (no mixed prefixes).
 - Document all settings with clear descriptions.

2. **Environment Variables**  
 - Use `.env` for local development.
 - Use proper secret management in production.
 - **Never commit** sensitive values to version control.
 - Document all required environment variables.

3. **Testing Configuration**  
 - Keep test settings minimal and focused.
 - Only override settings needed for specific tests.
 - Use consistent naming with main settings.
 - Document test-specific settings.

4. **Configuration Changes Process**  
 1. **Analyze impact** before making changes:
    - Identify affected components  
    - Review usage across codebase  
    - Consider backward compatibility  
    - Evaluate testing implications  
 2. **Make targeted changes**:
    - Prefer updating test code over production code  
    - Keep changes focused and minimal  
    - Maintain consistency in naming  
    - Update documentation  
 3. **Validate changes**:
    - Run affected test suites  
    - Check for side effects  
    - Verify configuration loading  
    - Test environment handling  

### 2.2 Database Changes

1. Review existing migrations in `alembic/versions/`.
2. Check database utilities in `scripts/`.
3. Update both async and sync database access patterns.
4. Maintain test database isolation.
5. Follow naming conventions in `setup_db.sql`.
6. Always create proper indexes for foreign keys.
7. Use PostgreSQL-specific features when beneficial.
8. Implement proper audit logging for changes.

### 2.3 API Development

1. Use FastAPI dependency injection.
2. Implement proper error handling.
3. Follow REST principles.
4. Document with OpenAPI/Swagger.
5. Include proper validation schemas.

### 2.4 Authentication System

1. Use Redis for token management.
2. Implement proper session handling.
3. Follow security best practices.
4. Use unified error handling.
5. Maintain audit logs for security events.
6. Implement rate limiting.
7. Use secure password policies.
8. Support 2FA where needed.

### 2.5 Testing Requirements

1. Maintain test isolation.
2. Use proper fixtures from `conftest.py`.
3. Include both unit and integration tests.
4. Follow existing patterns in `tests/`.
5. Ensure proper error case coverage.
6. Use transaction rollback in database tests.
7. Mock external services appropriately.
8. Verify security implications.

---

## 3. Critical Subsystems

### 3.1 Authentication System

- Located in `core/security/`.
- Uses JWT tokens with Redis backend.
- Includes refresh token mechanism.
- Implements proper session management.
- Maintains comprehensive audit logs.
- Supports role-based access control.
- Uses rate limiting for security.
- Implements proper password policies.

### 3.2 Risk Management

- Real-time risk monitoring.
- Position management.
- Exposure tracking.
- Stop-loss implementation.

### 3.3 Data Pipeline

- Market data ingestion.
- Real-time processing.
- Historical data management.
- Cache optimization.

---

## 4. Best Practices for Changes

### 4.1 Configuration Changes

When making configuration-related changes, follow this process:

1. **Analysis Phase**  
 - Document current state and intended changes.  
 - Map all affected components.  
 - Identify potential risks.  
 - Consider backward compatibility.

2. **Impact Assessment**  
 - Review all file dependencies.  
 - Check for naming conventions.  
 - Evaluate test coverage.  
 - Consider deployment impact.

3. **Implementation Strategy**  
 - Choose the least disruptive approach.  
 - Prefer updating test code over production code.  
 - Maintain consistent naming conventions.  
 - Keep changes focused and minimal.

4. **Validation Process**  
 - Run targeted tests first.  
 - Verify no unintended side effects.  
 - Check configuration loading.  
 - Test in different environments.

**Example Decision Process (Markdown Format):**

1. **Problem Identification**  
 - Identify the specific issue (e.g., test failures).  
 - Gather error messages and stack traces.  
 - Document affected components.

2. **Root Cause Analysis**  
 - Trace error to source.  
 - Review related code.  
 - Check configuration dependencies.  
 - Identify naming inconsistencies.

3. **Solution Design**  
 - List possible approaches.  
 - Evaluate impact of each approach.  
 - Consider testing implications.  
 - Choose least disruptive solution.

4. **Implementation**  
 - Make focused changes.  
 - Update documentation.  
 - Add test coverage.  
 - Verify changes.

---

## 5. Before Making Changes

1. **Impact Analysis**  
 - Identify affected components.
 - Check dependent services.
 - Review test coverage.
 - Consider performance impact.

2. **Documentation**  
 - Update API documentation.
 - Maintain `README.md`.
 - Document configuration changes.
 - Update development notes.

3. **Testing Strategy**  
 - Plan test coverage.
 - Include edge cases.
 - Test error scenarios.
 - Verify performance impact.

---

## 6. Development Workflow

1. **Initial Review**  
 - Review relevant documentation.
 - Check existing implementations.
 - Understand test requirements.
 - Review security implications.

2. **Implementation**  
 - Follow existing patterns.
 - Maintain test coverage.
 - Update documentation.
 - Include proper logging.

3. **Validation**  
 - Run full test suite.
 - Check performance impact.
 - Verify security.
 - Review documentation.

---

## 7. Key Files to Review

1. **Configuration**  
 - `.env` and `.env.test`: Environment configuration  
 - `alembic.ini`: Database migration settings  
 - `pytest.ini`: Test configuration  
 - `docker-compose.yml`: Service configuration

2. **Core Implementation**  
 - `main.py`: Application entry point  
 - `core/config/settings.py`: Application settings  
 - `database/session.py`: Database configuration  
 - `api/app.py`: API setup

3. **Testing**  
 - `tests/conftest.py`: Test configuration  
 - `tests/api/`: API test patterns  
 - `tests/core/`: Core functionality tests  
 - `tests/database/`: Database tests

---

## 8. Monitoring and Observability

1. **Logging**  
 - Use structured logging.
 - Include context information.
 - Follow severity levels.
 - Maintain proper categories.

2. **Metrics**  
 - System metrics.
 - Business metrics.
 - Performance metrics.
 - Error tracking.

---

## 9. Deployment Considerations

1. **Infrastructure**  
 - Review Terraform modules.
 - Check environment configs.
 - Verify security groups.
 - Review monitoring setup.

2. **Database**  
 - Check migration status.
 - Verify indices.
 - Review performance.
 - Check connections.

---

## 10. AI Collaboration, Code Style, and CI/CD

### 10.1 Code Style and Linting
- Adopt a consistent style guide (e.g., PEP 8 for Python).
- Use linters and formatters (e.g., Black, Flake8, Ruff) to ensure consistency.
- Automate style checks in your CI pipeline to catch issues early.

### 10.2 Static Analysis
- Run static analysis (e.g., MyPy) to catch type errors and enforce type hints.
- Integrate static analysis into local development workflows and CI.

### 10.3 Quality Gates
- Enforce coverage thresholds (e.g., >80% test coverage).
- Set up a CI workflow that fails on coverage or linting issues.
- Implement a review process for code maintainability (e.g., cyclomatic complexity).

### 10.4 Collaboration With the AI Coding Agent
1. **Verification of AI-Generated Code**  
 - Manually review AI-generated code for correctness, security, and maintainability.  
 - Ensure AI-suggested code passes existing test suites before merging.  
 - Use clear commit messages to indicate which parts are AI-generated vs. human-edited.

2. **Security and Privacy**  
 - Avoid exposing secrets or credentials in prompts or code examples.  
 - Check for accidental commits of sensitive data (e.g., `.env` files).

3. **Prompt Management**  
 - Provide the AI with targeted prompts for incremental code changes.  
 - Update context incrementally and avoid overloading with entire repositories.

4. **Iterative Development**  
 - Encourage small, incremental changes from the AI.  
 - Validate each incremental change with tests and code reviews.

### 10.5 Code Reviews and Approvals
- Use detailed Pull Request (PR) descriptions, automated checklists, and assign reviewers.
- Require passing CI on main branches.
- Ensure at least one human reviewer for AI-generated changes.

### 10.6 CI/CD Pipeline
- **Pipeline Stages**: Build, test, security scans, deploy.
- **AI-Specific Checks**: Consider scanning AI-generated code with Semgrep or SonarQube.
- **Artifacts and Logs**: Store build artifacts securely and sanitize logs for secrets.

### 10.7 Security and Compliance
- **OWASP Top 10**: Watch for common vulnerabilities (injection, XSS, CSRF, etc.).
- **Threat Modeling**: Reassess if AI changes critical security components.
- **Regulatory Requirements**: (e.g., GDPR, PCI-DSS, FINRA) Ensure compliance.

### 10.8 Performance and Load Testing
- **Benchmark** critical paths (e.g., data ingestion, trading execution).
- **Regression Testing**: Run performance tests after AI-generated changes.
- **Load and Stress Tests**: Use tools like Locust or JMeter to confirm scalability.

### 10.9 Governance and Ethics (Optional)
- **Human-in-the-Loop**: Final responsibility lies with the human developer.
- **Code Ownership**: Clarify licensing for AI-generated code.
- **Bias & Fairness**: In finance, consider ethical/regulatory implications of AI-driven logic.

---

## 11. Conclusion

Following these **Development Guidelines** ensures:

1. **Consistent code quality**  
2. **Proper system integration**  
3. **Maintainable codebase**  
4. **Reliable performance**  
5. **Secure implementation**  
6. **Responsible AI collaboration**

**Always** confirm that any changes:

- Align with existing implementations  
- Maintain adequate test coverage  
- Address security implications  
- Update relevant documentation  
- Comply with performance requirements  

---

## Additional Resources

- **Project documentation**: `docs/`
- **Development history**: `project_context/`
- **Infrastructure**: `terraform/README.md`
- **API documentation**: Access via `/api/docs` in the running environment
