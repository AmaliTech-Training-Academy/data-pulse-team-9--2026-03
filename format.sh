#!/bin/bash
# Format and lint Python code
# Usage: ./format.sh <path>

set -e

if [ -z "$1" ]; then
    echo "Usage: ./format.sh <path>"
    echo "Example: ./format.sh backend"
    exit 1
fi

PATH_TO_FORMAT="$1"

echo "🔧 Formatting Python code in: $PATH_TO_FORMAT"
echo ""

echo "1️⃣  Running isort..."
python -m isort "$PATH_TO_FORMAT"
echo "✅ isort complete"
echo ""

echo "2️⃣  Running black..."
python -m black "$PATH_TO_FORMAT"
echo "✅ black complete"
echo ""

echo "3️⃣  Running flake8..."
python -m flake8 "$PATH_TO_FORMAT"
echo "✅ flake8 complete"
echo ""

echo "🎉 All checks passed!"
