#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
/usr/bin/python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo "SETUP_OK: .venv ready"
