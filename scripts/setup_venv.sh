#!/usr/bin/env bash
#
# OPTIONAL: only powers your editor (Cursor/VS Code) autocomplete, lint, and lets you run
# `pytest` on your machine. The app itself runs in Docker; you do NOT need this.
#
# Needs Python 3.12 locally. Zero-install alternative: "Dev Containers: Reopen in Container".
#
#   ./scripts/setup_venv.sh
#   # then in Cursor/VS Code: "Python: Select Interpreter" -> ./.venv/bin/python

set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3.12}"
command -v "$PYTHON" >/dev/null || PYTHON=python3

echo "Creating .venv with $PYTHON ..."
"$PYTHON" -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements-dev.txt

echo
echo "Done. Run tests with ./.venv/bin/pytest, or pick ./.venv/bin/python as your interpreter."
