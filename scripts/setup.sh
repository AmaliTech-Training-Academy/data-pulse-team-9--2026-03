#!/bin/bash
# Setup script for DataPulse development environment

set -e

echo "Setting up DataPulse development environment..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required but not installed"
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip is required but not installed"
    exit 1
fi

# Use pip3 if available, otherwise pip
PIP_CMD="pip"
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
fi

echo "Installing pre-commit..."
$PIP_CMD install pre-commit

echo "Installing pre-commit hooks..."
pre-commit install

echo "Installing development dependencies..."
if [ -f "backend/requirements.txt" ]; then
    $PIP_CMD install -r backend/requirements.txt
else
    echo "WARNING: backend/requirements.txt not found, skipping backend dependencies"
fi

echo "Installing code formatters..."
$PIP_CMD install black isort flake8

echo "Installing security scanners..."
$PIP_CMD install bandit[toml] safety

echo "Running initial pre-commit check..."
pre-commit run --all-files || echo "WARNING: Some files need formatting - this is normal on first run"

echo "Setup complete! You can now:"
echo "   - Make commits (pre-commit will run automatically)"
echo "   - Run 'pre-commit run --all-files' to check all files"
echo "   - Run 'black backend/' to format Python code"
echo "   - Run 'flake8 backend/' to check code style"
echo "   - Run 'bandit -r backend/' to scan for security issues"
echo "   - Run 'safety check -r backend/requirements.txt' to check dependencies"
