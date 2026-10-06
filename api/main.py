# ==============================================================================
# MAIN FASTAPI APPLICATION ROUTER & ENDPOINTS (NUSAKLIM WEATHER AI)
# ==============================================================================

import time
import os
import secrets
import threading
from datetime import datetime
from typing import Literal
from fastapi import FastAPI, HTTPException, BackgroundTasks, status, Depends, Security, Query, UploadFile, File, Form
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from api.config import settings, DEFAULT_DEV_API_KEY
from api.stations_db import get_all_stations, get_station_metadata
from api.models_schema import (
    StationsListResponse, StationInfo, ForecastResponse,
    ComparisonResponse, OpenMeteoComparisonItem, HealthResponse, RetrainResponse,
    PhysicalForecastResponse, PhysicalForecastBulkResponse
)
from api.ingest_upload import validate_csv_header, UploadValidationError
from api.pipeline_runner import run_pipeline
from api.forecast_service import engine
from api.openmeteo_service import fetch_openmeteo_forecast

OPENAPI_TAGS = [
    {
        "name": "Weather Forecast (7-Day)",
        "description": "Ramalan cuaca H+1 s/d H+7 per stasiun AWS. Lihat deskripsi tiap endpoint untuk memilih "
                        "format yang sesuai (lengkap+agronomi vs nilai fisik ringkas untuk integrasi eksternal).",
    },
    {
        "name": "MLOps & Automation",
        "description": "Trigger retraining & ingest data mentah baru di background. Lihat deskripsi endpoint "
                        "untuk perbedaan /retrain vs /ingest.",
    },
    {"name": "AWS Stations Metadata", "description": "Daftar & detail 183 stasiun AWS PPKS (lokasi, estate, status)."},
    {"name": "Open-Meteo Benchmarking", "description": "Komparasi akurasi ramalan NusaKlim AI vs Open-Meteo API publik."},
    {"name": "System Health & Diagnostics", "description": "Cek kesehatan layanan & status model yang sedang dimuat."},
]

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    openapi_tags=OPENAPI_TAGS,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware (Allows frontend website & dashboard connection). allow_credentials=False
# karena allow_origins=["*"] (wildcard) + allow_credentials=True adalah kombinasi yang
# ditolak browser menurut spek CORS - API ini pakai auth via header X-API-Key (bukan
# cookie), jadi credentials mode browser tidak dibutuhkan sama sekali.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

STARTUP_TIME = time.time()

if settings.weather_api_key == DEFAULT_DEV_API_KEY:
    print("=" * 70)
    print("[SECURITY WARNING] NUSAKLIM_API_KEY tidak di-set - endpoint /weather & /ingest")
    print("masih pakai API key default pengembangan yang ada di source code!")
    print("WAJIB set environment variable NUSAKLIM_API_KEY sebelum deploy ke production.")
    print("=" * 70)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False, description="API key untuk endpoint integrasi eksternal (/weather, /ingest).")

async def verify_weather_api_key(x_api_key: str | None = Security(api_key_header)):
    """Dipakai khusus endpoint eksternal (/weather, /ingest) - endpoint internal lain
    (/forecast, /stations, /retrain, dst) tetap tanpa auth agar frontend NusaKlim
    yang sudah berjalan tidak perlu diubah."""
    if x_api_key is None or not secrets.compare_digest(x_api_key, settings.weather_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key tidak valid atau tidak disertakan. Sertakan header X-API-Key."
        )

UNAUTHORIZED_RESPONSE = {401: {"description": "API key tidak valid atau header X-API-Key tidak disertakan."}}
SERVER_ERROR_RESPONSE = {500: {"description": "Gagal memproses permintaan (mis. model belum termuat, station_id tidak valid)."}}
TRAINING_IN_PROGRESS_RESPONSE = {409: {"description": "Sudah ada proses retrain/ingest lain yang sedang berjalan - tunggu sampai selesai sebelum memicu lagi."}}

# ------------------------------------------------------------------------------
# Kunci konkurensi global utk /retrain & /ingest - mencegah 2 proses training jalan
# bersamaan (rebutan CPU & RACE CONDITION saat sama-sama menulis weather_model_latest.joblib
# di akhir, hasilnya non-deterministik tergantung mana yang selesai belakangan).
# ------------------------------------------------------------------------------
_training_lock = threading.Lock()
_is_training = False

def _try_acquire_training_slot() -> bool:
    global _is_training
    with _training_lock:
        if _is_training:
            return False
        _is_training = True
        return True

def _release_training_slot():
    global _is_training
    with _training_lock:
        _is_training = False

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.get(
    f"{settings.api_prefix}/health",
    response_model=HealthResponse,
    tags=["System Health & Diagnostics"],
    summary="Cek Status Layanan & Model AI",
    description="Menjalankan 1x inference percobaan (stasiun 227) untuk mengukur latency riil, sekaligus memastikan model bundle berhasil dimuat.",
    response_description="Status layanan, jumlah stasiun aktif, status model, dan latency inference dalam milidetik."
)
async def health_check():
    t0 = time.time()
    _ = engine.predict_7_days("227")
    latency_ms = round((time.time() - t0) * 1000, 2)
    
    return HealthResponse(
        status="Healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        total_active_stations=len(get_all_stations()),
        model_loaded=engine.bundle is not None,
        model_last_trained=engine.last_loaded_time or "2026-09-02",
        inference_latency_ms=latency_ms
    )

@app.get(
    f"{settings.api_prefix}/stations",
    response_model=StationsListResponse,
    tags=["AWS Stations Metadata"],
    summary="Daftar Seluruh 183 Stasiun AWS PPKS",
    description="Metadata lokasi (lat/lon/elevasi/provinsi/estate) seluruh stasiun AWS PPKS yang terdaftar.",
    response_description="Total stasiun & daftar lengkap metadata tiap stasiun."
)
async def list_stations():
    stations = [StationInfo(**s) for s in get_all_stations()]
    return StationsListResponse(total_stations=len(stations), stations=stations)

@app.get(
    f"{settings.api_prefix}/stations/{{station_id}}",
    response_model=StationInfo,
    tags=["AWS Stations Metadata"],
    summary="Detail Informasi Stasiun AWS Spesifik",
    description="Metadata satu stasiun berdasarkan station_id. Stasiun yang tidak ada di registry resmi tetap "
                "mengembalikan data (lokasi dialokasikan deterministik per region), bukan 404.",
    response_description="Metadata lengkap stasiun yang diminta."
)
async def get_station_detail(station_id: str):
    meta = get_station_metadata(station_id)
    return StationInfo(**meta)

@app.get(
    f"{settings.api_prefix}/forecast/{{station_id}}",
    response_model=ForecastResponse,
    tags=["Weather Forecast (7-Day)"],
    summary="Dapatkan Ramalan Cuaca 7 Hari Lengkap dengan Rekomendasi Agronomi",
    description="Format LENGKAP untuk frontend/dashboard internal NusaKlim: suhu min/max, kondisi cuaca, ikon, "
                "peluang hujan, DAN rekomendasi agronomi per hari (pemupukan/panen/dsb). Tanpa auth. "
                "Untuk integrasi server eksternal yang hanya butuh nilai fisik mentah, pakai `/weather/{station_id}` saja.",
    response_description="Ramalan H+1 s/d H+7 beserta metadata stasiun & info model yang dipakai.",
    responses=SERVER_ERROR_RESPONSE
)
async def get_forecast(station_id: str):
    try:
        forecast_data = engine.predict_7_days(station_id)
        return forecast_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal memproses peramalan stasiun {station_id}: {str(e)}"
        )

@app.get(
    f"{settings.api_prefix}/weather",
    response_model=PhysicalForecastBulkResponse,
    tags=["Weather Forecast (7-Day)"],
    summary="Ramalan Cuaca 7 Hari - Banyak Stasiun Sekaligus (Format Nilai Fisik)",
    description="Versi batch dari `/weather/{station_id}` - satu panggilan untuk beberapa stasiun sekaligus "
                f"(maks {settings.max_bulk_stations}). Kegagalan satu station_id (mis. tidak valid) tidak "
                "menggagalkan stasiun lain - cek array `errors` di response. Butuh header `X-API-Key`.",
    response_description="Array hasil per stasiun yang sukses (`data`) + array kegagalan per stasiun (`errors`).",
    dependencies=[Depends(verify_weather_api_key)],
    responses={**UNAUTHORIZED_RESPONSE, 400: {"description": "stationIds kosong atau melebihi batas maksimum."}}
)
async def get_weather_bulk(stationIds: str = Query(..., description=f"Daftar station_id dipisah koma, maks {settings.max_bulk_stations}. Contoh: 227,210,2207")):
    ids = [s.strip() for s in stationIds.split(",") if s.strip()]
    if not ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="stationIds kosong.")
    if len(ids) > settings.max_bulk_stations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maksimum {settings.max_bulk_stations} station_id per request, diterima {len(ids)}."
        )
    results, errors = engine.predict_7_days_physical_bulk(ids)
    return PhysicalForecastBulkResponse(data=results, errors=errors)

@app.get(
    f"{settings.api_prefix}/weather/{{station_id}}",
    response_model=PhysicalForecastResponse,
    tags=["Weather Forecast (7-Day)"],
    summary="Ramalan Cuaca 7 Hari - Format Nilai Fisik (stationId/temperature/humidity/radiation/.../units)",
    description="Format RINGKAS untuk server eksternal lain yang menarik data ke sistemnya sendiri: nilai fisik "
                "mentah saja (tanpa rekomendasi agronomi/ikon). Setiap response menyertakan `dataSource` "
                "(`\"model\"` = prediksi sungguhan, `\"fallback_statistik\"` = stasiun tanpa histori, BUKAN "
                "prediksi nyata) dan `generatedAt` agar konsumen tahu validitas & kesegaran data. Butuh header `X-API-Key`.",
    response_description="Ramalan fisik H+1 s/d H+7 satu stasiun, dibungkus `{data: {...}}`.",
    dependencies=[Depends(verify_weather_api_key)],
    responses={**UNAUTHORIZED_RESPONSE, **SERVER_ERROR_RESPONSE}
)
async def get_weather(station_id: str):
    try:
        return engine.predict_7_days_physical(station_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal memproses peramalan stasiun {station_id}: {str(e)}"
        )

def _load_openmeteo_benchmark():
    """Baca openmeteo_benchmark_summary.json (hasil open_meteo_benchmark.py). None jika belum ada/rusak."""
    import json
    try:
        with open(settings.openmeteo_summary_path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


@app.get(
    f"{settings.api_prefix}/compare/{{station_id}}",
    response_model=ComparisonResponse,
    tags=["Open-Meteo Benchmarking"],
    summary="Komparasi Ramalan NusaKlim AI vs Open-Meteo API",
    description="Membandingkan prediksi suhu NusaKlim AI dengan Open-Meteo global (real-time via API Open-Meteo, "
                "fallback estimasi bias kalau API tidak terjangkau) untuk stasiun yang sama. Lihat juga Laporan 5 "
                "(Komparasi NusaKlim vs OpenMeteo) untuk metodologi evaluasi lengkap.",
    response_description="Ringkasan evaluasi akurasi + deret perbandingan harian H+1 s/d H+7.",
    responses=SERVER_ERROR_RESPONSE
)
async def compare_forecast(station_id: str):
    meta = get_station_metadata(station_id)
    station_info = StationInfo(**meta)
    
    # NusaKlim internal prediction
    nusaklim_res = engine.predict_7_days(station_id)
    
    # Try fetching real-time Open-Meteo forecast
    om_daily = await fetch_openmeteo_forecast(station_info.lat, station_info.lon)
    
    # Ringkasan evaluasi dibaca dari hasil benchmark Laporan 5 (bukan angka tetap), supaya
    # selalu sama dengan laporan setiap kali open_meteo_benchmark.py dijalankan ulang.
    bench = _load_openmeteo_benchmark()
    nk_temp_mae = bench['nusaklim_local_ai_metrics']['avg_temp_mae'] if bench else None
    om_temp_mae = bench['open_meteo_metrics']['avg_temp_mae'] if bench else None

    series = []
    for idx, item in enumerate(nusaklim_res.forecast):
        om_temp = None
        if om_daily and 'temperature_2m_mean' in om_daily and idx < len(om_daily['temperature_2m_mean']):
            om_temp = om_daily['temperature_2m_mean'][idx]
        if om_temp is None:
            # Fallback based on global model bias
            om_temp = round(item.temp_avg + 1.85, 2)
            
        series.append(OpenMeteoComparisonItem(
            date=item.date,
            actual_temp_c=None,
            nusaklim_ai_pred_c=item.temp_avg,
            openmeteo_pred_c=om_temp,
            nusaklim_error_c=nk_temp_mae,
            openmeteo_error_c=om_temp_mae
        ))

    if bench:
        isum = bench.get('indicator_summary', {})
        nk_better = [v['label'] for v in isum.values() if v['winner_avg'] == 'NusaKlim']
        om_better = [v['label'] for v in isum.values() if v['winner_avg'] == 'Open-Meteo']
        reduction = (om_temp_mae - nk_temp_mae) / om_temp_mae * 100 if om_temp_mae else 0.0
        summary_eval = {
            "evaluation_basis": f"{bench['stations_evaluated']} stasiun, 30 hari uji (blind out-of-time) {bench['evaluation_period'].replace(' to ', ' s/d ')}, "
                                "dihitung terhadap data aktual AWS (Laporan 5)",
            "nusaklim_ai_mae_c": nk_temp_mae,
            "openmeteo_global_mae_c": om_temp_mae,
            "accuracy_advantage": (f"Error suhu NusaKlim {abs(reduction):.0f}% {'lebih kecil' if reduction >= 0 else 'lebih besar'} dibanding Open-Meteo; "
                                   f"NusaKlim lebih akurat pada {', '.join(nk_better) or '-'}; Open-Meteo lebih akurat pada {', '.join(om_better) or '-'}"),
            "indicator_summary": isum,
            "rationale": "Model NusaKlim dilatih langsung dari sensor stasiun AWS PPKS (di bawah kanopi kebun sawit), sedangkan Open-Meteo "
                         "menyajikan rata-rata grid 11 km pada area terbuka. Rincian per stasiun dan per indikator ada di Laporan 5."
        }
    else:
        summary_eval = {
            "evaluation_basis": "Ringkasan benchmark Open-Meteo belum tersedia (jalankan open_meteo_benchmark.py)",
            "nusaklim_ai_mae_c": None,
            "openmeteo_global_mae_c": None,
            "accuracy_advantage": "Belum tersedia",
            "rationale": "Lihat Laporan 5 (Komparasi NusaKlim vs OpenMeteo) untuk metodologi evaluasi lengkap."
        }
    
    return ComparisonResponse(
        station=station_info,
        evaluation_summary=summary_eval,
        comparison_series=series
    )

def background_retrain_task(task_id: str):
    try:
        run_pipeline(task_id, trigger="api:/retrain", retrain_only=True, on_success=engine.load_models)
    finally:
        _release_training_slot()

@app.post(
    f"{settings.api_prefix}/retrain",
    response_model=RetrainResponse,
    tags=["MLOps & Automation"],
    summary="Picu Retraining Model di Latar Belakang (Continuous Learning)",
    description="Melatih ulang 49 sub-model dari `nusaklim_daily_aggregated.csv` yang SUDAH ADA (~21 menit). "
                "TIDAK membaca ulang file data mentah `nusaklim-aws-reduce.csv` - kalau ada data sensor baru yang "
                "belum diagregasi ke CSV harian, endpoint ini tidak akan melihatnya sama sekali. "
                "Untuk data mentah baru, pakai `POST /ingest`. Hanya 1 job retrain/ingest boleh berjalan "
                "bersamaan - panggilan saat job lain masih jalan akan ditolak (409).",
    response_description="Konfirmasi bahwa job retraining diterima & berjalan di background, beserta task_id & estimasi waktu.",
    responses=TRAINING_IN_PROGRESS_RESPONSE
)
async def trigger_retrain(background_tasks: BackgroundTasks):
    if not _try_acquire_training_slot():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Proses retrain/ingest lain sedang berjalan. Coba lagi setelah selesai."
        )
    task_id = f"retrain-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    background_tasks.add_task(background_retrain_task, task_id)
    return RetrainResponse(
        status="Accepted",
        message="Proses retraining otomatis telah dimulai di background server (estimasi selesai ~21 menit - melatih 49 sub-model dengan algoritma juara per-variabel, termasuk Ridge Regression untuk 4 dari 7 variabel).",
        task_id=task_id,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S WIB")
    )

def background_ingest_task(task_id: str, staging_path: str | None = None, mode: str = "append"):
    """Merge file baru (upload + isi data_raw/incoming/) -> cleaning -> retrain. Hasil SUKSES/GAGAL
    + penyebabnya ditulis ke logs/pipeline.log oleh run_pipeline."""
    try:
        extra = [(staging_path, mode)] if staging_path else None
        run_pipeline(task_id, trigger="api:/ingest/upload" if staging_path else "api:/ingest",
                     extra_files=extra, on_success=engine.load_models)
    finally:
        _release_training_slot()

@app.post(
    f"{settings.api_prefix}/ingest",
    response_model=RetrainResponse,
    tags=["MLOps & Automation"],
    summary="Picu Pipeline Penuh: Cleaning Data Mentah Baru -> Agregasi Harian -> Retraining Model",
    description="Panggil endpoint ini SETELAH file data mentah baru (format `nusaklim-aws-reduce.csv`) sudah "
                "ditaruh di server - BUKAN `/retrain`. Urutan proses: (1) `process_nusaklim.py` - cleaning & "
                "agregasi harian dari SELURUH raw data (~3 menit utk 14,8 juta+ baris), (2) kalau tahap 1 sukses, "
                "`retrain_pipeline.py` - retrain 49 sub-model (~21 menit). Kalau tahap 1 gagal, tahap 2 OTOMATIS "
                "DIBATALKAN agar model produksi tidak terlatih dari data rusak/parsial. Total ~24 menit. Butuh header `X-API-Key`. "
                "Hanya 1 job retrain/ingest boleh berjalan bersamaan - panggilan saat job lain masih jalan akan ditolak (409).",
    response_description="Konfirmasi bahwa job ingest diterima & berjalan di background, beserta task_id & estimasi waktu.",
    dependencies=[Depends(verify_weather_api_key)],
    responses={**UNAUTHORIZED_RESPONSE, **TRAINING_IN_PROGRESS_RESPONSE}
)
async def trigger_ingest(background_tasks: BackgroundTasks):
    if not _try_acquire_training_slot():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Proses retrain/ingest lain sedang berjalan. Coba lagi setelah selesai."
        )
    task_id = f"ingest-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    background_tasks.add_task(background_ingest_task, task_id)
    return RetrainResponse(
        status="Accepted",
        message="Proses ingest data mentah baru dimulai di background (estimasi selesai ~24 menit: "
                 "~3 menit cleaning & agregasi 14,8 juta+ baris raw, lalu ~21 menit retrain 49 sub-model). "
                 "Semua file .csv di data_raw/incoming/ akan di-merge ke master lebih dulu. Hasil SUKSES/GAGAL ada di logs/pipeline.log.",
        task_id=task_id,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S WIB")
    )

@app.post(
    f"{settings.api_prefix}/ingest/upload",
    response_model=RetrainResponse,
    tags=["MLOps & Automation"],
    summary="Upload CSV Data Mentah Baru -> Merge -> Cleaning -> Agregasi Harian -> Retraining",
    description="Kirim file CSV data mentah baru sebagai `multipart/form-data` dengan field **`file`** (format kolom sama "
                "dengan `nusaklim-aws-reduce.csv`: header wajib memuat `stnname,utctime,tempout,humout,windspd,winddir,bar,solar,rain15`). "
                "Field **`mode`**: `append` (default) = hanya baris yang LEBIH BARU dari data terakhir tiap stasiun yang ditambahkan ke "
                "raw CSV di server (baris tumpang tindih/duplikat diabaikan, jadi cukup kirim data baru saja); `replace` = file ini "
                "menggantikan seluruh raw CSV (raw lama disimpan sebagai `.bak`). Setelah merge, pipeline `/ingest` berjalan "
                "di background (~24 menit). Butuh header `X-API-Key`. Hanya 1 job retrain/ingest boleh berjalan bersamaan (409).",
    response_description="Konfirmasi file diterima & pipeline berjalan di background, beserta task_id.",
    dependencies=[Depends(verify_weather_api_key)],
    responses={**UNAUTHORIZED_RESPONSE, **TRAINING_IN_PROGRESS_RESPONSE, 400: {"description": "File bukan CSV valid / kolom wajib tidak lengkap."}}
)
async def trigger_ingest_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="CSV data mentah baru (header: stnname,utctime,tempout,humout,windspd,winddir,bar,solar,rain15,...)"),
    mode: Literal["append", "replace"] = Form("append", description="`append` (default) atau `replace`")
):
    if not _try_acquire_training_slot():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Proses retrain/ingest lain sedang berjalan. Coba lagi setelah selesai."
        )
    task_id = f"ingest-upload-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    staging_path = os.path.join(settings.upload_staging_dir, f"{task_id}.csv")
    scheduled = False
    try:
        os.makedirs(settings.upload_staging_dir, exist_ok=True)
        with open(staging_path, "wb") as out:
            while chunk := await file.read(1024 * 1024):
                out.write(chunk)
        validate_csv_header(staging_path)
        background_tasks.add_task(background_ingest_task, task_id, staging_path, mode)
        scheduled = True
    except UploadValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    finally:
        if not scheduled:
            if os.path.exists(staging_path):
                os.remove(staging_path)
            _release_training_slot()
    return RetrainResponse(
        status="Accepted",
        message=f"File '{file.filename}' diterima (mode={mode}). Merge ke raw CSV, cleaning & agregasi, lalu retrain "
                 "berjalan di background (estimasi ~24 menit).",
        task_id=task_id,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S WIB")
    )
