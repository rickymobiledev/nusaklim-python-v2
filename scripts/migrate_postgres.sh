#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

if ! command -v uv >/dev/null 2>&1; then
  echo "uv belum terpasang atau tidak ada di PATH." >&2
  exit 1
fi

uv run python -m api.migrate_postgres "$@"