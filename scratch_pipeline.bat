@echo off
echo Running full pipeline for Solar SUM update...

echo [1/8] Running process_nusaklim.py...
.venv\Scripts\python.exe process_nusaklim.py

echo [2/8] Running benchmark_algo_allvars_h1_h7.py...
.venv\Scripts\python.exe benchmark_algo_allvars_h1_h7.py

echo [3/8] Running retrain_pipeline.py...
.venv\Scripts\python.exe retrain_pipeline.py

echo [4/8] Running run_benchmark_all_eligible.py...
.venv\Scripts\python.exe run_benchmark_all_eligible.py

echo [5/8] Generating figures...
.venv\Scripts\python.exe gen_figures_model.py
.venv\Scripts\python.exe gen_figures_merged.py
.venv\Scripts\python.exe generate_local_benchmark_figures.py

echo [6/8] Generating PDFs...
.venv\Scripts\python.exe generate_model_pdf.py
.venv\Scripts\python.exe generate_per_station_pdf.py
.venv\Scripts\python.exe generate_master_documentation_pdf.py

echo Done!

