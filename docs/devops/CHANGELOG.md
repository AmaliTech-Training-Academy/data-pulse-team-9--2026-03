# Project Changelog

All notable changes to this project are documented here.

---

##  CI/CD Pipeline Setup

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

## [2025-01-XX] - Branch Protection Workflow

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

## [2025-01-XX] - CI Workflow

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
