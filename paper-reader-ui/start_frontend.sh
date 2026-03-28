#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1/2] Installing frontend dependencies..."
npm install

echo "[2/2] Starting frontend server..."
npm run dev
