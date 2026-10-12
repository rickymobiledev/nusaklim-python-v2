#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

if ! command -v uv >/dev/null 2>&1; then
  echo "uv belum terpasang atau tidak ada di PATH." >&2
  exit 1
fi

echo "Running pipeline from retrain_pipeline.py..."

echo "[3/8] Running retrain_pipeline.py..."
uv run python retrain_pipeline.py

echo "[4/8] Running run_benchmark_all_eligible.py..."
uv run python run_benchmark_all_eligible.py

echo "[5/8] Generating figures..."
uv run python gen_figures_model.py
uv run python gen_figures_merged.py
uv run python generate_local_benchmark_figures.py

echo "[6/8] Generating PDFs..."
uv run python generate_model_pdf.py
uv run python generate_per_station_pdf.py
uv run python generate_master_documentation_pdf.py

echo "Done!"
