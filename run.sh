#!/usr/bin/env bash
set -e

echo "============================================================"
echo "  ReimburseAI - Expense & Reimbursement Assistant (Linux/macOS)"
echo "============================================================"

# Resolve script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for Python 3
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 is not found in PATH!"
    echo "Please install Python 3.10+ (e.g. brew install python3 or sudo apt install python3 python3-venv)"
    exit 1
fi

# Create virtual environment if not present
if [ ! -d ".venv" ]; then
    echo "[*] Creating virtual environment in .venv..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies if needed
if ! python -c "import fastapi, uvicorn" &>/dev/null; then
    echo "[*] Installing required dependencies from requirements.txt..."
    pip install -r requirements.txt
fi

# Execute dynamic runner
python run.py "$@"
