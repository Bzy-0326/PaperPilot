#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3.11}"

if [ ! -d ".venv" ]; then
  echo "[1/5] Creating virtual environment with ${PYTHON_BIN}..."
  "${PYTHON_BIN}" -m venv .venv
fi

echo "[2/5] Activating virtual environment..."
# shellcheck disable=SC1091
source .venv/bin/activate

echo "[3/5] Upgrading pip..."
python -m pip install --upgrade pip

echo "[4/5] Installing backend dependencies..."
pip install -r requirements.txt

echo "[5/5] Starting backend server..."
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
