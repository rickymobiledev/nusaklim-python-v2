import os
from pydantic import BaseModel

class Settings(BaseModel):
    app_name: str = "NusaKlim Weather AI REST API"
    app_version: str = "1.0.0"
    app_description: str = "Layanan REST API Sistem Prediksi Cuaca 7 Hari Berbasis Machine Learning & Agroklimat PPKS"
    
    # Paths
    base_dir: str = r"d:\Downloads\nusaklim"
    daily_csv_path: str = r"d:\Downloads\nusaklim\nusaklim_daily_aggregated.csv"
    model_bundle_path: str = r"d:\Downloads\nusaklim\models\weather_model_latest.joblib"
    openmeteo_summary_path: str = r"d:\Downloads\nusaklim\openmeteo_benchmark_summary.json"
    
    # API Settings
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["*"]

settings = Settings()
