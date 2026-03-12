# Project Changelog

All notable changes to this project are documented here.

---

## [2026-03-09] - CI/CD Pipeline Setup

### Added

#### GitHub Actions Workflows
- **PR Validation** (`.github/workflows/pre-validation.yml`)
  - Validates PR title follows conventional commits format
  - Validates branch name follows type/description pattern
  - Checks PR description references an issue
  - Runs on: PR opened, synchronize, reopened to main/develop

- **Auto-Assign Reviewer** (`.github/workflows/auto-assign-reviewer.yml`)
  - Automatically assigns reviewers based on PR author
  - Reviewer mapping:
    - lubandi → JoeBright1619
    - IshimweDiane → lubandi
    - JoeBright1619 → IshimweDiane
    - Kalisha1234 → tob-amalitech
    - Zaina-M → Damas200
    - Asheryram → Benjamin-yankey
    - Others → Asheryram (default)
  - Runs on: PR opened, ready_for_review

#### Pre-Commit Hooks
- **Configuration** (`.pre-commit-config.yaml`)
  - Code quality hooks:
    - trailing-whitespace
    - end-of-file-fixer
    - check-yaml, check-json
    - check-merge-conflict
  - Security hooks:
    - detect-private-key
    - check-added-large-files (max 500KB)
  - Python formatting (backend/):
    - isort (import sorting)
    - black (code formatting)
    - flake8 (linting)
  - Python formatting (data-engineering/, qa/):
    - black (code formatting)
  - Commit message validation:
    - conventional-pre-commit (enforces conventional commits)

#### Configuration Files
- `.env.example` - Environment variables template
- `.gitattributes` - Git attributes configuration
- `.gitignore` - Updated ignore patterns

#### Documentation
- `SETUP.md` - Pre-commit setup guide
- `docs/PR_GUIDE.md` - Pull request guidelines and workflow documentation
- `docs/CHANGELOG.md` - This file

### Changed
- Renamed `gitignore` to `.gitignore`

### Impact
- All team members must install pre-commit hooks locally
- All PRs must follow naming conventions or will fail validation
- All commits must follow conventional commit format
- Code is automatically formatted before commit

---

## Template for Future Entries

```markdown
##  Feature/Change Name

### Added
- New features or files

### Changed
- Modifications to existing functionality

### Fixed
- Bug fixes

### Removed
- Deleted features or files

### Impact
- Who/what is affected

### Related
- Issue #XX, PR #XX
```


---

## [2025-01-09] - Branch Protection Workflow

### Added
- **Branch Protection** (`.github/workflows/branch-protection.yml`)
  - Enforces branch merge rules:
    - Only `feature/`, `bugfix/`, `hotfix/` branches can merge to `develop`
    - Only `develop` or `hotfix/` branches can merge to `main`
  - Runs on: PR opened, synchronize, reopened to main/develop
  - Prevents unauthorized merges and maintains git flow

### Impact
- Enforces proper git branching strategy
- Prevents direct merges from feature branches to main
- Ensures code flows through develop before reaching main


---

## [2025-01-09] - CI Workflow

### Added
- **CI Pipeline** (`.github/workflows/ci.yml`)
  - Pre-commit checks job:
    - Runs all pre-commit hooks in CI
  - Lint job:
    - black (code formatting check) for backend/, data-engineering/, qa/
    - isort (import sorting check) for backend/
    - flake8 (linting) for backend/
  - Concurrency control: Cancels duplicate runs
  - Runs on: Push/PR to main/develop

### Impact
- All code changes are automatically validated
- Ensures code quality before merge
- Prevents broken code from reaching main/develop

---

## [2026-03-10] - Environment Configuration and Security Enhancement

### Added
- **Enhanced CI Pipeline** (`.github/workflows/ci.yml`)
  - Frontend build pipeline with ESLint, Prettier, and Jest testing
  - Comprehensive security scanning: Trivy, Bandit, Safety, Gitleaks, CodeQL
  - Updated CodeQL to v4, fixed Trivy installation with direct APT installation
  - Added frontend test coverage requirements (75%)
  - Integration tests with Docker health checks

- **Development Environment Setup**
  - Cross-platform setup scripts: `scripts/setup.sh` (Linux/macOS), `scripts/setup.bat` (Windows)
  - Auto-installation of pre-commit, formatters, and security scanners
  - Comprehensive documentation in `scripts/README.md` with troubleshooting
  - Manual security scan commands for local development

- **Frontend Testing Infrastructure**
  - Jest testing framework with Next.js integration
  - Prettier configuration for consistent code formatting
  - Basic test suite with coverage requirements
  - Testing library dependencies for component testing

- **Security Enhancements**
  - detect-secrets baseline configuration (`.secrets.baseline`)
  - Pre-commit hooks for secret detection
  - Bandit security scanning with HIGH severity blocking
  - Safety dependency vulnerability checking
  - Pragma comments for false positive handling

### Fixed
- Docker entrypoint permission issues with explicit shell execution
- Django STORAGES configuration for modern Django versions
- TypeScript linting errors (removed 'any' types, unused variables)
- Prettier formatting issues across frontend codebase
- Static file collection errors in containerized environment

### Changed
- Replaced deprecated STATICFILES_STORAGE with modern STORAGES setting
- Updated frontend package.json with testing and formatting dependencies
- Modified Docker CMD to ENTRYPOINT for better container execution
- Enhanced SETUP.md with security scanning information

### Impact
- Comprehensive security scanning in CI/CD pipeline
- Automated development environment setup for team members
- Frontend code quality enforcement with testing requirements
- Local security scanning capabilities for developers

---

## [2026-03-10] - Monitoring and Analytics Infrastructure

### Added
- **Analytics Database**
  - Separate PostgreSQL instance for analytics data isolation (port 5433)
  - Dedicated analytics user and database configuration
  - Health checks and proper service dependencies

- **Grafana Integration**
  - Grafana service with custom dashboards for data quality monitoring
  - Dashboard provisioning for automated deployment
  - Admin credentials via environment variables
  - Persistent data storage with dedicated volume
  - Accessible at http://localhost:3000

- **ETL Pipeline Service**
  - Data transformation service for operational to analytics data flow
  - Configurable scheduling (default: every 6 hours)
  - Proper service dependencies and health checks
  - Connection between operational and analytics databases

- **Docker Orchestration**
  - Extended docker-compose.yml with monitoring services
  - Added persistent volumes: analytics_pgdata, grafana_data
  - Environment variable configuration for all monitoring services
  - Service dependency management with health checks

### Changed
- Removed obsolete docker-compose version attribute
- Updated .env with analytics and monitoring variables

### Impact
- Complete monitoring and analytics infrastructure
- Data quality insights through Grafana dashboards
- Automated data pipeline for analytics warehouse
- Scalable monitoring architecture for production deployment
