# Arsitektur dan Daftar File Python NusaKlim

Dokumen ini merangkum fungsionalitas dari semua file Python (`*.py`) yang digunakan dalam proyek NusaKlim Weather AI. File dikelompokkan berdasarkan peran utamanya agar mudah dipahami.

## 1. Direktori API (`/api`)
Kumpulan file untuk menjalankan layanan REST API (FastAPI) publik.
- **`api/main.py`**: Entry point utama server FastAPI, mendefinisikan rute (endpoints), autentikasi, dan konfigurasi server.
- **`api/config.py`**: Pengaturan aplikasi dan environment variable (seperti `NUSAKLIM_API_KEY`).
- **`api/models_schema.py`**: Definisi skema data (Pydantic) untuk validasi *request* dan *response* API.
- **`api/stations_db.py`**: Mengelola data/metadata dari 183 stasiun cuaca AWS (lokasi, status).
- **`api/forecast_service.py`**: Logika bisnis utama untuk memuat model ML dan menghasilkan prediksi cuaca (H+1 sd H+7) serta rekomendasi agronomi.
- **`api/openmeteo_service.py`**: Modul integrasi ke API pihak ketiga (Open-Meteo) untuk perbandingan data (komparasi).
- **`api/ingest_upload.py`**: Menangani endpoint untuk upload data cuaca terbaru (ingestion).
- **`api/pipeline_runner.py`**: Menjalankan proses berat (*background task*) seperti *retraining* model secara asinkron agar tidak memblokir API.
- **`tests/test_api.py`**: Unit test dan integration test untuk menguji endpoints API secara otomatis.

## 2. Pemrosesan Data & Pipeline Model ML
Script inti untuk memproses data mentah menjadi data siap latih dan membuat model Machine Learning.
- **`process_nusaklim.py`**: Script utama pemrosesan, pembersihan data (EDA), dan *feature engineering*.
- **`clean_interval_data.py`**: Modul khusus untuk membersihkan dan menangani data time-series (interval waktu).
- **`station_sampling.py`**: Menentukan stasiun mana saja yang memenuhi syarat (*eligible*) untuk dijadikan data latih dan validasi.
- **`retrain_pipeline.py`**: Pipeline end-to-end untuk melatih ulang (retrain) dan menyimpan model prediksi berdasarkan data terbaru.

## 3. Benchmarking & Evaluasi Model
Script untuk mengukur performa model, membandingkan algoritma, dan validasi lokal vs global.
- **`benchmark_algo_h1_h7.py`** & **`benchmark_algo_allvars_h1_h7.py`**: Menguji dan membandingkan performa berbagai algoritma ML untuk prediksi 1 hingga 7 hari ke depan.
- **`run_benchmark_all_eligible.py`**: Melakukan pengujian model secara menyeluruh ke seluruh 94 stasiun yang memiliki data lengkap.
- **`run_local_benchmark_v2.py`**: Validasi performa untuk model khusus lokal tiap stasiun.
- **`run_dl_benchmark_h1_h7.py`**: Pengujian khusus untuk algoritma berbasis Deep Learning.
- **`local_vs_global_stats.py`**: Menghitung statistik komparatif antara model lokal NusaKlim dengan model global (seperti Open-Meteo).
- **`open_meteo_benchmark.py`**: Script untuk mengambil dan menguji akurasi data Open-Meteo historis.
- **`demo_performa_model.py`**: Script demo cepat untuk menampilkan visualisasi/performa model (sering digunakan untuk presentasi).

## 4. Generator Laporan (PDF) & Visualisasi
Script otomatis untuk membuat grafik dan me-render dokumen PDF untuk Laporan 1 hingga 6.
- **`generate_master_documentation_pdf.py`**: Mengenerate Laporan 6 (Dokumentasi lengkap merangkum laporan 1-5).
- **`generate_model_pdf.py`**: Mengenerate Laporan 3 (Hasil pemodelan prediksi cuaca).
- **`generate_per_station_pdf.py`**: Mengenerate Laporan 3b (Analisis detail performa per stasiun vs global).
- **`generate_openmeteo_pdf.py`**: Mengenerate Laporan komparasi khusus terhadap Open-Meteo.
- **`generate_pdf.py`, `generate_gap_pdf.py`, `generate_interval_pdf.py`**: Script dasar/utilitas dan generator laporan untuk analisis data (Laporan 1 & 2).
- **`gen_figures_model.py`, `gen_figures_merged.py`, `generate_local_benchmark_figures.py`**: Script spesifik untuk menghasilkan grafik/plot (PNG) performa model yang akan disisipkan ke dalam PDF.
- **`generate_distributions_with_boxplots.py`, `generate_timeseries_decomposition.py`, `generate_rainfall_classification_named.py`**: Membuat grafik distribusi data, dekomposisi time-series, dan visualisasi klasifikasi hujan untuk Laporan EDA.
- **`fix_eda_figures.py`, `fix_flowchart.py`**: Script utilitas untuk memperbaiki atau merender ulang diagram/flowchart tertentu.
- **`create_presentation.py`, `create_attractive_presentation.py`, `create_data_cleaning_eda_presentation.py`**: Generator untuk membuat slide presentasi otomatis berdasarkan hasil analisis.

## 5. Lain-lain
- **`scratch/check_ranges.py`**: Script *scratch* (sementara) yang dipakai untuk mengecek range/rentang nilai data saat proses debugging.

