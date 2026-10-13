from pathlib import Path
from typing import Literal
from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Locate .env independently of the configurable project/data root.
CHECKOUT_ROOT = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NUSAKLIM_",
        env_file=CHECKOUT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
        hide_input_in_errors=True,
    )
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
    project_root: str = Field(default=str(CHECKOUT_ROOT), min_length=1,
                              validation_alias=AliasChoices("NUSAKLIM_PROJECT_ROOT", "PROJECT_ROOT"))
    base_dir: str = ""
    daily_csv_path: str = "nusaklim_daily_aggregated.csv"
    raw_data_dir: str = "data_raw"
    raw_csv_path: str = "nusaklim-aws-reduce.csv"
    incoming_dir: str = "incoming"
    archive_dir: str = "archive"
    rejected_dir: str = "rejected"
    log_dir: str = "logs"
    upload_staging_dir: str = "staging"
    model_bundle_path: str = "models/weather_model_latest.joblib"
    openmeteo_summary_path: str = "openmeteo_benchmark_summary.json"
    device_csv_path: str = "data/device_nusaklim.csv"
    
    # API Settings
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["*"]
    host: str = Field(default="127.0.0.1", min_length=1)
    port: int = Field(default=8000, ge=1, le=65535,
                      validation_alias=AliasChoices("NUSAKLIM_PORT", "PORT"))
    reload: bool = True

    # API Key tunggal untuk SEMUA endpoint (header X-API-Key).
    weather_api_key: str = Field(min_length=1, repr=False)
    max_bulk_stations: int = Field(default=50, gt=0)
    max_ingest_records: int = Field(default=100_000, gt=0)
    max_model_bundles: int = Field(default=10, gt=0, description="Maksimum bundle model berstempel waktu yang dipertahankan di models/.")
    max_run_logs: int = Field(default=30, gt=0, description="Maksimum file log eksekusi pipeline yang dipertahankan di logs/runs/.")
    storage_backend: Literal["csv", "postgres"] = "csv"
    database_url: str = Field(default="", repr=False)

    @model_validator(mode="after")
    def resolve_paths(self):
        if self.storage_backend == "postgres" and not self.database_url:
            raise ValueError("NUSAKLIM_DATABASE_URL wajib diisi untuk storage_backend=postgres")
        def absolute(value: str, parent: str | Path) -> str:
            path = Path(value).expanduser()
            return str((path if path.is_absolute() else Path(parent) / path).resolve())

        self.project_root = absolute(self.project_root, CHECKOUT_ROOT)
        self.base_dir = absolute(self.base_dir or self.project_root, self.project_root)
        for name in ("daily_csv_path", "raw_data_dir", "log_dir",
                     "model_bundle_path", "openmeteo_summary_path", "device_csv_path"):
            setattr(self, name, absolute(getattr(self, name), self.base_dir))
        for name in ("raw_csv_path", "incoming_dir", "archive_dir",
                     "rejected_dir", "upload_staging_dir"):
            setattr(self, name, absolute(getattr(self, name), self.raw_data_dir))
        return self

settings = Settings()
PROJECT_ROOT = Path(settings.project_root)
