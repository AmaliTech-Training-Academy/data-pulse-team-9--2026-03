# Pull Request Guide

## Overview

This project enforces strict PR and commit standards through automated CI/CD workflows and pre-commit hooks.

---

## PR Title Format

All PR titles must follow Conventional Commits format:

```
type(scope): description
```

**Valid types:** `feat`, `fix`, `docs`, `test`, `devops`, `chore`, `refactor`, `ci`

**Examples:**

- `feat(auth): add JWT login`
- `fix(validation): handle empty CSV`
- `devops(ci): add security scan`

---

## Branch Naming

Branch names must follow this format:

```
type/description
```

**Valid types:** `feature`, `bugfix`, `hotfix`, `devops`, `docs`, `test`, `chore`

**Examples:**

- `feature/auth-system`
- `bugfix/null-check`
- `devops/ci-pipeline`

---

## PR Requirements

### 1. Link to Issue

PR description must reference an issue using:

- `Closes #123`
- `Fixes #123`
- `Resolves #123`
- `Task: #123`

### 2. Automated Checks

All PRs must pass:

- **PR title format validation** (`.github/workflows/pre-validation.yml`)
- **Branch name validation** (`.github/workflows/pre-validation.yml`)
- **Issue reference check** (`.github/workflows/pre-validation.yml`)
- **Auto-reviewer assignment** (`.github/workflows/auto-assign-reviewer.yml`)

### 3. Code Review

Reviewers are automatically assigned based on PR author:

- lubandi → JoeBright1619
- IshimweDiane → lubandi
- JoeBright1619 → IshimweDiane
- Kalisha1234 → tob-amalitech
- Zaina-M → Damas200
- Asheryram → Benjamin-yankey
- Others → Asheryram (default)

---

## Commit Message Format

All commits must follow Conventional Commits:

```
type(scope): description
```

**Examples:**

```bash
git commit -m "feat(auth): add login endpoint"
git commit -m "fix(upload): handle empty files"
git commit -m "devops(ci): add deployment workflow"
```

---

## Pre-Commit Hooks

Configured in `.pre-commit-config.yaml`:

### Code Quality

- **trailing-whitespace**: Removes trailing spaces
- **end-of-file-fixer**: Ensures files end with newline
- **check-yaml**: Validates YAML syntax
- **check-json**: Validates JSON syntax
- **check-merge-conflict**: Detects merge conflict markers

### Security

- **detect-private-key**: Prevents committing private keys
- **check-added-large-files**: Blocks files >500KB

### Python Code Formatting (backend/)

- **isort**: Sorts imports
- **black**: Code formatter
- **flake8**: Linting

### Python Code Formatting (data-engineering/, qa/)

- **black**: Code formatter

### Commit Message Validation

- **conventional-pre-commit**: Enforces conventional commit format

---

## Setup

See `SETUP.md` for pre-commit installation instructions.

---

## Workflow Files

1. **`.github/workflows/pre-validation.yml`**

   - Validates PR title format
   - Validates branch name format
   - Checks for issue references
2. **`.github/workflows/auto-assign-reviewer.yml`**

   - Auto-assigns reviewers based on PR author
   - Runs on PR open or ready_for_review
3. **`.pre-commit-config.yaml`**

   - Local pre-commit hooks for code quality
   - Runs before every commit

## Branch Protection Rules

### Merge to `develop`

Only these branch types can merge to `develop`:

- `feature/*`
- `bugfix/*`
- `hotfix/*`

### Merge to `main`

Only these branches can merge to `main`:

- `develop` (for releases)
- `hotfix/*` (for emergency fixes)

### Workflow File

**`.github/workflows/branch-protection.yml`**

- Validates branch merge rules
- Blocks unauthorized merges
- Enforces git flow strategy

## CI Pipeline

**`.github/workflows/ci.yml`**

Runs automatically on push/PR to main/develop:

1. **Pre-commit Checks**

   - Runs all pre-commit hooks
   - Must pass before lint job runs
2. **Lint Job**

   - black: Code formatting check (backend/, data-engineering/, qa/)
   - isort: Import sorting check (backend/)
   - flake8: Linting (backend/)
3. **Concurrency Control**

   - Cancels duplicate workflow runs
   - Saves CI resources
