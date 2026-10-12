#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

UV_CMD="uv"
if ! command -v uv >/dev/null 2>&1; then
  if command -v uv.exe >/dev/null 2>&1; then
    UV_CMD="uv.exe"
  elif [ -x "/c/Python312/Scripts/uv.exe" ]; then
    UV_CMD="/c/Python312/Scripts/uv.exe"
  else
    echo "uv belum terpasang atau tidak ada di PATH." >&2
    exit 1
  fi
fi

"$UV_CMD" run python scripts/import_data.py "$@"
