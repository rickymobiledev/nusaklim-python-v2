import os
from pydantic import BaseModel

API_KEY = "nusaklim-secret-key-2026"

class Settings(BaseModel):
    app_name: str = "NusaKlim Weather AI REST API"
    app_version: str = "1.0.0"
    app_description: str = """
Layanan REST API Sistem Prediksi Cuaca 7 Hari Berbasis Machine Learning & Agroklimat untuk 183 Stasiun AWS PPKS.

### Kelompok Endpoint
- **Weather Forecast (7-Day)** - ramalan H+1 s/d H+7 per stasiun. Ada 2 format:
  - `/forecast/{station_id}` - format lengkap + rekomendasi agronomi, dipakai frontend/dashboard internal NusaKlim.
  - `/weather/{station_id}` & `/weather` (bulk) - format nilai fisik ringkas (stationId/temperature/humidity/radiation/.../units),
    untuk **ditarik server eksternal lain**.
- **MLOps & Automation** - `/retrain` (latih ulang model dari data harian yang sudah ada) vs `/ingest` (proses data mentah baru
  `nusaklim-aws-reduce.csv` dari awal, lalu retrain).
- **AWS Stations Metadata**, **Open-Meteo Benchmarking**, **System Health & Diagnostics** - pendukung.

### Autentikasi
Semua endpoint API butuh header `X-API-Key` (klik **Authorize** di Swagger). `/docs` & `/redoc` tetap terbuka.

### Alur Data Baru -> Forecast Baru
1. Taruh file data mentah baru di folder `data_raw/incoming/` dengan nama `nusaklim-aws-reduce_YYYYMMDD-YYYYMMDD.csv`
   (tanggal data pertama-terakhir), atau kirim lewat `POST /ingest/upload`. Master gabungan: `data_raw/nusaklim-aws-reduce.csv`.
   Hasil tiap proses (SUKSES/GAGAL + penyebab) dicatat di `logs/pipeline.log`.
2. Panggil `POST /ingest` (~24 menit: cleaning+agregasi ~3 menit, retrain ~21 menit).
3. Model otomatis reload di memori - panggilan `/forecast` atau `/weather` berikutnya sudah pakai model & baseline tanggal terbaru.
"""
    
    # Paths
    base_dir: str = r"D:\Projects\Kodepanda\Nusaklim\nusaklim"
    daily_csv_path: str = r"D:\Projects\Kodepanda\Nusaklim\nusaklim\nusaklim_daily_aggregated.csv"
    raw_data_dir: str = r"D:\Projects\Kodepanda\Nusaklim\nusaklim\data_raw"
    raw_csv_path: str = r"D:\Projects\Kodepanda\Nusaklim\nusaklim\data_raw\nusaklim-aws-reduce.csv"
    incoming_dir: str = r"D:\Projects\Kodepanda\Nusaklim\nusaklim\data_raw\incoming"
    archive_dir: str = r"D:\Projects\Kodepanda\Nusaklim\nusaklim\data_raw\archive"
    rejected_dir: str = r"D:\Projects\Kodepanda\Nusaklim\nusaklim\data_raw\rejected"
    log_dir: str = r"D:\Projects\Kodepanda\Nusaklim\nusaklim\logs"
    upload_staging_dir: str = r"D:\Projects\Kodepanda\Nusaklim\nusaklim\data_raw\staging"
    model_bundle_path: str = r"D:\Projects\Kodepanda\Nusaklim\nusaklim\models\weather_model_latest.joblib"
    openmeteo_summary_path: str = r"D:\Projects\Kodepanda\Nusaklim\nusaklim\openmeteo_benchmark_summary.json"
    
    # API Settings
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["*"]

    # API Key tunggal untuk SEMUA endpoint (header X-API-Key).
    weather_api_key: str = API_KEY
    max_bulk_stations: int = 50
    max_ingest_records: int = 100_000

settings = Settings()
