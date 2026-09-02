# ==============================================================================
# PYDANTIC SCHEMAS FOR API REQUEST & RESPONSE VALIDATION
# ==============================================================================

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class StationInfo(BaseModel):
    station_id: str = Field(..., example="227")
    estate_name: str = Field(..., example="Kebun Sei Pancur (Pusat Riset Agroklimat)")
    province: str = Field(..., example="Sumatera Utara")
    region: Optional[str] = Field(None, example="Medan & Marihat")
    lat: float = Field(..., example=3.487)
    lon: float = Field(..., example=98.712)
    elevation_m: int = Field(..., example=45)
    status: str = Field(..., example="Active")

class StationsListResponse(BaseModel):
    total_stations: int
    stations: List[StationInfo]

class DailyForecastItem(BaseModel):
    horizon: str = Field(..., example="H+1")
    date: str = Field(..., example="2026-08-20")
    day_name: str = Field(..., example="Kamis")
    temp_avg: float = Field(..., example=27.45, description="Suhu rata-rata (?C)")
    temp_min: float = Field(..., example=23.20, description="Suhu minimum malam (?C)")
    temp_max: float = Field(..., example=32.10, description="Suhu maksimum siang (?C)")
    humidity_avg: float = Field(..., example=84.5, description="Kelembapan rata-rata (%)")
    rainfall_total_mm: float = Field(..., example=3.20, description="Estimasi curah hujan (mm)")
    rain_probability_pct: int = Field(..., example=65, description="Peluang terjadinya hujan (%)")
    weather_condition: str = Field(..., example="Hujan Ringan")
    weather_icon: str = Field(..., example="rain-light")
    wind_direction: str = Field(..., example="Selatan")
    agronomic_advisory: str = Field(..., example="Aman untuk aktivitas panen TBS dan aplikasi herbisida.")

class ForecastResponse(BaseModel):
    station: StationInfo
    generated_at_wib: str
    model_version: str
    model_algorithm: str = "LightGBM Multi-Horizon Regressor & Classifier"
    evaluation_mae_temp: float = 0.801
    forecast: List[DailyForecastItem]

class OpenMeteoComparisonItem(BaseModel):
    date: str
    actual_temp_c: Optional[float]
    nusaklim_ai_pred_c: float
    openmeteo_pred_c: float
    nusaklim_error_c: Optional[float]
    openmeteo_error_c: Optional[float]

class ComparisonResponse(BaseModel):
    station: StationInfo
    evaluation_summary: Dict[str, Any]
    comparison_series: List[OpenMeteoComparisonItem]

class HealthResponse(BaseModel):
    status: str = "Healthy"
    app_name: str
    version: str
    total_active_stations: int
    model_loaded: bool
    model_last_trained: str
    inference_latency_ms: float

class RetrainResponse(BaseModel):
    status: str
    message: str
    task_id: str
    timestamp: str
