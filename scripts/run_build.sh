#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ]; then
  echo "Project venv not found. Running scripts/setup_env.sh first..."
  bash scripts/setup_env.sh
fi
. .venv/bin/activate
python scripts/build_data.py
