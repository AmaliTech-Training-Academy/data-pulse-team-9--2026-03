#  PRE-COMMIT SETUP (5 Minutes)

## One-Time Setup

```bash
# 1. Install pre-commit
pip install pre-commit

# 2. Windows users: If you get "command not found"
py -c "import sysconfig; print(sysconfig.get_path('scripts'))"
# Copy the path shown, then run:
echo 'export PATH="$PATH:/c/Users/YOUR_USERNAME/AppData/Local/Python/pythoncore-3.14-64/Scripts"' >> ~/.bashrc
source ~/.bashrc

# 3. Install hooks (in project root)
pre-commit install
pre-commit install --hook-type commit-msg

# Done! ✅
```

---

## What Happens Now?

Every time you commit, pre-commit automatically:
- ✅ Formats your Python code (black)
- ✅ Sorts imports (isort)
- ✅ Checks code style (flake8)
- ✅ Removes trailing spaces
- ✅ Checks for secrets/keys
- ✅ Validates commit message format

**You don't do anything - it's automatic!**

---

## Commit Message Format

```bash
# ✅ CORRECT
git commit -m "feat(auth): add login endpoint"
git commit -m "fix(upload): handle empty files"
git commit -m "devops(ci): add deployment workflow"

# ❌ WRONG
git commit -m "added stuff"
git commit -m "fixed bug"
```

**Format:** `type(scope): description`

**Types:** feat, fix, devops, test, docs, refactor, chore

---

## If Pre-Commit Fails

```bash
# Pre-commit already fixed your code
# Just add and commit again:
git add .
git commit -m "feat(auth): add login"
# Now it passes ✅
```

---

## Manual Formatting (Optional)

If you want to format code before committing:

```bash
# Windows
format.bat backend

# Linux/Mac/Git Bash
./format.sh backend
```

This runs:
1. isort (import sorting)
2. black (code formatting)
3. flake8 (linting)

---

## Troubleshooting

**"pre-commit: command not found" (Windows)**
```bash
# Find your Python Scripts path
py -c "import sysconfig; print(sysconfig.get_path('scripts'))"

# Add to PATH (replace with your actual path)
echo 'export PATH="$PATH:/c/Users/HP/AppData/Local/Python/pythoncore-3.14-64/Scripts"' >> ~/.bashrc
source ~/.bashrc

# Verify
pre-commit --version

# Now install hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

**"black not found"**
```bash
pip install black flake8 isort
```

**Commit message rejected**
```bash
# ❌ Wrong
git commit -m "added login"

# ✅ Correct
git commit -m "feat(auth): add login"
```

---

## Quick Reference

```bash
# Setup (once)
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg

# Normal workflow
git add .
git commit -m "feat(scope): description"
# Pre-commit runs automatically

# If it fails
git add .
git commit -m "feat(scope): description"
# Try again

# Skip (emergency only)
git commit -m "message" --no-verify
```

---

**Questions?** Ask @Asheryram (DevOps)
