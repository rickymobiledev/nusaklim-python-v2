@echo off
where uv >nul 2>nul
if errorlevel 1 (
    echo uv belum terpasang atau tidak ada di PATH.
    exit /b 1
)
cd /d "%~dp0.."
echo Running full pipeline for Solar SUM update...

echo [1/8] Running process_nusaklim.py...
uv run python process_nusaklim.py

echo [2/8] Running benchmark_algo_allvars_h1_h7.py...
uv run python benchmark_algo_allvars_h1_h7.py

echo [3/8] Running retrain_pipeline.py...
uv run python retrain_pipeline.py

echo [4/8] Running run_benchmark_all_eligible.py...
uv run python run_benchmark_all_eligible.py

echo [5/8] Generating figures...
uv run python gen_figures_model.py
uv run python gen_figures_merged.py
uv run python generate_local_benchmark_figures.py

echo [6/8] Generating PDFs...
uv run python generate_model_pdf.py
uv run python generate_per_station_pdf.py
uv run python generate_master_documentation_pdf.py

echo Done!
