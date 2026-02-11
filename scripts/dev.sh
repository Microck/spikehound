#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
. "$VENV_DIR/bin/activate"

pip install --upgrade pip
pip install -r "$ROOT_DIR/requirements.txt" -r "$ROOT_DIR/requirements-dev.txt"

exec uvicorn web.app:app --reload --app-dir "$ROOT_DIR/src"
