# Development Environment Setup

This directory contains setup scripts to quickly configure your development environment for DataPulse.

## Quick Start

### Windows
```cmd
scripts\setup.bat
```

### Linux/macOS
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

## What the scripts do

1. **Install pre-commit** - Automatically runs code checks before commits
2. **Install pre-commit hooks** - Sets up the actual hooks in your git repository
3. **Install development dependencies** - Python packages needed for development
4. **Install code formatters** - Black, isort, and flake8 for code quality
5. **Install security scanners** - Bandit and Safety for security checks
6. **Run initial check** - Formats any existing code to match project standards

## Manual Setup (if scripts don't work)

### Prerequisites
- Python 3.11+ installed
- pip package manager

### Steps
```bash
# Install pre-commit
pip install pre-commit

# Install pre-commit hooks
pre-commit install

# Install development dependencies
pip install -r backend/requirements.txt

# Install code formatters
pip install black isort flake8

# Install security scanners
pip install bandit[toml] safety

# Run initial formatting
pre-commit run --all-files
```

## Troubleshooting

### Permission denied (Linux/macOS)
```bash
chmod +x scripts/setup.sh
```

### Python not found
- Windows: Install from https://python.org
- macOS: `brew install python3`
- Ubuntu/Debian: `sudo apt install python3 python3-pip`

### Pre-commit fails on first run
This is normal - pre-commit will format files on first run. Just commit the formatted files.

## What happens after setup

- **Every commit** will automatically run code checks
- **Failed checks** will prevent the commit and show what needs fixing
- **Code formatting** will be applied automatically where possible

## Manual commands

```bash
# Check all files
pre-commit run --all-files

# Format Python code
black backend/

# Check code style
flake8 backend/

# Sort imports
isort backend/

# Security scans
bandit -r backend/
safety check -r backend/requirements.txt
```
