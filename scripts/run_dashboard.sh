#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ]; then
  echo "Project venv not found. Running scripts/setup_env.sh first..."
  bash scripts/setup_env.sh
fi
. .venv/bin/activate
python -m streamlit run app.py --server.headless true --server.port "${PORT:-8502}" --server.baseUrlPath "nps-ops-dashboard"
