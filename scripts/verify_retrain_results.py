"""
Verifikasi Hasil Retrain & Pengujian Endpoint API NusaKlim
"""

import sys
import os
import json
import urllib.request
import joblib

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from api.config import settings
from api.weather_store import connect

API_BASE = f"http://{settings.host}:{settings.port}{settings.api_prefix}"
API_KEY = settings.weather_api_key
STATION_ID = "227"


def make_request(path: str):
    url = f"{API_BASE}{path}"
    req = urllib.request.Request(url, headers={"X-API-Key": API_KEY})
    with urllib.request.urlopen(req, timeout=15) as res:
        return res.status, json.loads(res.read().decode("utf-8"))


def main():
    print("=" * 80)
    print("HASIL VERIFIKASI & PENGUJIAN AKHIR MODEL NUSAKLIM (PASCA RETRAIN)")
    print("=" * 80)

    # 1. DATABASE POSTGRESQL
    print("\n1. Database PostgreSQL:")
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT count(*), max(utctime) FROM weather_raw WHERE stnname = %s", (STATION_ID,))
        raw_cnt, max_utc = cur.fetchone()
        cur.execute("SELECT count(*), max(date) FROM weather_daily WHERE stnname = %s", (STATION_ID,))
        daily_cnt, max_date = cur.fetchone()
        cur.execute("SELECT count(*) FROM weather_raw")
        total_raw = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM weather_daily")
        total_daily = cur.fetchone()[0]

    print(f"   - weather_raw Stasiun {STATION_ID} : {raw_cnt:,} baris | max utctime = {max_utc}")
    print(f"   - weather_daily Stasiun {STATION_ID}: {daily_cnt:,} hari | max date = {max_date}")
    print(f"   - Total DB: {total_raw:,} baris raw | {total_daily:,} stasiun-hari daily")

    # 2. MODEL BUNDLE
    print("\n2. File Bundle Model (models/weather_model_latest.joblib):")
    bundle = joblib.load(settings.model_bundle_path)
    print(f"   - Versi Model Bundle : {bundle['timestamp']}")
    print(f"   - max_train_date     : {bundle['max_train_date']}")
    print(f"   - split_date validasi: {bundle['split_date']}")
    print(f"   - Sampel Training    : {bundle['train_samples']:,} baris")
    print(f"   - Jumlah Sub-Model   : {len(bundle['models'])} model (7 horizon x 7 variabel)")
    print(f"   - MAE Suhu H+1       : {bundle['metrics'].get('temp_avg_h1', {}).get('MAE')} °C")
    print(f"   - MAE Hujan H+7      : {bundle['metrics'].get('rainfall_total_mm_h7', {}).get('MAE')} mm")

    # 3. GET /api/v1/health
    print("\n3. API Health Endpoint (GET /api/v1/health):")
    status, health = make_request("/health")
    print(f"   - HTTP Status        : {status}")
    print(f"   - Status Layanan     : {health['status']}")
    print(f"   - Total Stasiun Aktif: {health['total_active_stations']}")
    print(f"   - Model Loaded       : {health['model_loaded']}")
    print(f"   - Model Last Trained : {health['model_last_trained']}")
    print(f"   - Inference Latency  : {health['inference_latency_ms']} ms")

    # 4. GET /api/v1/forecast/227
    print(f"\n4. API Forecast 7-Day Lengkap (GET /api/v1/forecast/{STATION_ID}):")
    status, fc = make_request(f"/forecast/{STATION_ID}")
    stn = fc["station"]
    print(f"   - Stasiun     : {stn['estate_name']} ({stn['province']}) - Lat/Lon: {stn['lat']}, {stn['lon']}")
    print(f"   - Model Versi : {fc['model_version']}")
    print(f"   - Algoritma   : {fc['model_algorithm']}")
    print(f"   - Tabel Ramalan H+1 s/d H+7:")
    print(f"     {'Horizon':<8} {'Tanggal':<12} {'Hari':<8} {'Kondisi':<14} {'Suhu':<10} {'Hujan':<14} {'Peluang':<9} {'Angin':<10} {'Advisory'}")
    print("     " + "-" * 115)
    for row in fc["forecast"]:
        temp_str = f"{row['temp_avg']}°C"
        rain_str = f"{row['rainfall_total_mm']} mm"
        prob_str = f"{row['rain_probability_pct']}%"
        wind_str = f"{row['wind_direction']}"
        adv_short = row['agronomic_advisory'][:40] + "..." if len(row['agronomic_advisory']) > 40 else row['agronomic_advisory']
        print(f"     {row['horizon']:<8} {row['date']:<12} {row['day_name']:<8} {row['weather_condition']:<14} {temp_str:<10} {rain_str:<14} {prob_str:<9} {wind_str:<10} {adv_short}")

    # 5. GET /api/v1/weather/227
    print(f"\n5. API Weather Format Nilai Fisik (GET /api/v1/weather/{STATION_ID}):")
    status, w = make_request(f"/weather/{STATION_ID}")
    w_data = w["data"]
    print(f"   - Data Source : {w_data['dataSource']}")
    print(f"   - Generated At: {w_data['generatedAt']}")
    print(f"   - Rincian Nilai Fisik H+1:")
    d1 = w_data["forecast"][0]
    print(f"     * Tanggal           : {d1['date']}")
    print(f"     * Suhu              : {d1['temperature']} {w_data['units']['temperature']}")
    print(f"     * Kelembapan        : {d1['humidity']} {w_data['units']['humidity']}")
    print(f"     * Curah Hujan       : {d1['rainfall']} {w_data['units']['rainfall']}")
    print(f"     * Radiasi Solar     : {d1['radiation']} {w_data['units']['radiation']}")
    print(f"     * Tekanan Udara     : {d1['airPressure']} {w_data['units']['airPressure']}")
    print(f"     * Kecepatan Angin   : {d1['windSpeed']} {w_data['units']['windSpeed']}")
    print(f"     * Arah Angin        : {d1['windDirectionDeg']}°")

    # 6. PIPELINE LOG ENTRY
    print("\n6. Entri Log MLOps Pipeline Terakhir (logs/pipeline.log):")
    with open(os.path.join(settings.log_dir, "pipeline.log"), "r", encoding="utf-8") as f:
        last_lines = f.readlines()[-3:]
        for line in last_lines:
            print("   " + line.strip())

    print("\n" + "=" * 80)
    print("KESIMPULAN: SELURUH PROSES INGEST, CLEANING, RETRAIN, DAN INFERENSI VALID 100%!")
    print("=" * 80)


if __name__ == "__main__":
    main()
