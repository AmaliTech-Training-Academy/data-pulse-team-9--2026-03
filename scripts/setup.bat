@echo off
REM Setup script for DataPulse development environment (Windows)

echo Setting up DataPulse development environment...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is required but not installed
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if pip is installed
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is required but not installed
    pause
    exit /b 1
)

echo Installing pre-commit...
pip install pre-commit
if errorlevel 1 (
    echo ERROR: Failed to install pre-commit
    pause
    exit /b 1
)

echo Installing pre-commit hooks...
pre-commit install
if errorlevel 1 (
    echo ERROR: Failed to install pre-commit hooks
    pause
    exit /b 1
)

echo Installing development dependencies...
if exist "backend\requirements.txt" (
    pip install -r backend\requirements.txt
) else (
    echo WARNING: backend\requirements.txt not found, skipping backend dependencies
)

echo Installing code formatters...
pip install black isort flake8
if errorlevel 1 (
    echo ERROR: Failed to install code formatters
    pause
    exit /b 1
)

echo Installing security scanners...
pip install bandit[toml] safety
if errorlevel 1 (
    echo ERROR: Failed to install security scanners
    pause
    exit /b 1
)

echo Running initial pre-commit check...
pre-commit run --all-files
if errorlevel 1 (
    echo WARNING: Some files need formatting - this is normal on first run
)

echo.
echo Setup complete! You can now:
echo    - Make commits (pre-commit will run automatically)
echo    - Run 'pre-commit run --all-files' to check all files
echo    - Run 'black backend/' to format Python code
echo    - Run 'flake8 backend/' to check code style
echo    - Run 'bandit -r backend/' to scan for security issues
echo    - Run 'safety check -r backend/requirements.txt' to check dependencies
echo.
pause
