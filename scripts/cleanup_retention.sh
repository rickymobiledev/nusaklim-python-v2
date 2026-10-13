#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"
if ! command -v uv >/dev/null 2>&1; then
    echo "uv belum terpasang atau tidak ada di PATH." >&2
    exit 1
fi
uv run python scripts/cleanup_retention.py "$@"
