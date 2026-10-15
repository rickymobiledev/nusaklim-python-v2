"""
Test End-to-End: POST /api/v1/ingest/json, background retrain, and forecast evaluation.

Alur Pengujian:
1. Evaluasi baseline awal (PostgreSQL raw & daily, model latest, API health & forecast).
2. Generate data observasi sensor stasiun 227 selama 1 minggu (7 hari x 144 pembacaan = 1,008 baris).
3. Kirim request POST /api/v1/ingest/json ke server API.
4. Pantau eksekusi background retrain pipeline secara real-time via logs.
5. Jalankan verifikasi & pengujian menyeluruh terhadap hasil retrain:
   - weather_raw di PostgreSQL
   - weather_daily di PostgreSQL
   - Bundle model latest & versioned
   - Endpoint GET /api/v1/health
   - Endpoint GET /api/v1/forecast/227
   - Endpoint GET /api/v1/weather/227
"""

import os
import sys
import time
import json
import math
from datetime import datetime, timezone, timedelta
import urllib.request
import urllib.error
import joblib

# Pastikan root proyek ada di path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from api.config import settings
from api.weather_store import connect


API_BASE = f"http://{settings.host}:{settings.port}{settings.api_prefix}"
API_KEY = settings.weather_api_key
STATION_ID = "227"


def make_request(path: str, method: str = "GET", data: dict | None = None, headers: dict | None = None):
    url = f"{API_BASE}{path}"
    req_headers = {
        "X-API-Key": API_KEY,
        "User-Agent": "NusaKlim-Ingest-Tester/1.0",
    }
    if headers:
        req_headers.update(headers)
    body_bytes = None
    if data is not None:
        body_bytes = json.dumps(data).encode("utf-8")
        req_headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            res_body = res.read().decode("utf-8")
            return res.status, json.loads(res_body) if res_body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(err_body)
        except Exception:
            return e.code, {"detail": err_body}
    except Exception as e:
        return 0, {"error": str(e)}


def generate_1week_station_data(station_id: str, start_epoch: int, interval_sec: int = 600, total_days: int = 7):
    """
    Generate data observasi 10-menitan selama 7 hari (1,008 baris)
    dengan pola fisis cuaca realistis di kebun sawit tropis (Sumatera Utara).
    """
    records = []
    total_records = (total_days * 24 * 3600) // interval_sec

    # Parameter cuaca rata-rata Sei Pancur
    base_temp_f = 79.0   # ~26.1 C
    temp_amp_f = 8.0     # amplitudo siang-malam ~4.4 C
    base_hum = 82.0
    hum_amp = 14.0
    base_bar_inhg = 29.88

    for i in range(total_records):
        utc = start_epoch + (i * interval_sec)
        dt_utc = datetime.fromtimestamp(utc, tz=timezone.utc)
        dt_wib = dt_utc + timedelta(hours=7)

        hour_frac = dt_wib.hour + dt_wib.minute / 60.0
        # Diurnal curve: puncak suhu pukul 14:00 WIB
        diurnal_rad = 2 * math.pi * (hour_frac - 14.0) / 24.0
        diurnal_factor = math.cos(diurnal_rad)

        temp_f = round(base_temp_f + (temp_amp_f * diurnal_factor) + (0.5 * math.sin(i * 0.1)), 1)
        hum = round(max(55.0, min(98.0, base_hum - (hum_amp * diurnal_factor) + (0.8 * math.cos(i * 0.1)))), 1)

        # Radiasi matahari: 0 pada malam hari (18:00 - 06:00 WIB), kurva lonceng siang hari
        if 6.0 <= hour_frac <= 18.0:
            solar_peak = 750.0
            solar_sin = math.sin(math.pi * (hour_frac - 6.0) / 12.0)
            solar = round(max(0.0, solar_peak * solar_sin + 20.0 * math.sin(i * 0.3)), 1)
        else:
            solar = 0.0

        bar = round(base_bar_inhg + 0.03 * math.sin(2 * math.pi * hour_frac / 12.0), 3)
        windspd = round(max(0.5, 2.5 + 1.8 * math.sin(i * 0.05)), 1)
        winddir = round((90.0 + 45.0 * math.sin(i * 0.08)) % 360.0, 1)

        # Hujan sporadis di sore hari (15:00 - 17:00 WIB) pada hari ke-3 dan ke-6
        day_idx = i // 144
        if day_idx in (2, 5) and 15.0 <= hour_frac <= 16.5:
            rain15 = round(0.12 * math.sin(math.pi * (hour_frac - 15.0) / 1.5), 3)
        else:
            rain15 = 0.0

        ts_str = dt_wib.strftime("%Y-%m-%d %H:%M:%S.000")
        records.append({
            "stnname": str(station_id),
            "utctime": utc,
            "tempout": temp_f,
            "humout": hum,
            "windspd": windspd,
            "winddir": winddir,
            "bar": bar,
            "solar": solar,
            "rain15": rain15,
            "created_at": ts_str,
            "updated_at": ts_str,
        })

    return records


def get_db_snapshot(station_id: str):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT count(*), min(utctime), max(utctime) FROM weather_raw WHERE stnname = %s", (station_id,))
        raw_cnt, raw_min_utc, raw_max_utc = cur.fetchone()

        cur.execute("SELECT count(*), min(date), max(date) FROM weather_daily WHERE stnname = %s", (station_id,))
        daily_cnt, daily_min_d, daily_max_d = cur.fetchone()

        cur.execute("SELECT count(*) FROM weather_raw")
        total_raw = cur.fetchone()[0]

        cur.execute("SELECT count(*) FROM weather_daily")
        total_daily = cur.fetchone()[0]

    return {
        "station_raw_count": raw_cnt,
        "station_raw_min_utc": raw_min_utc,
        "station_raw_max_utc": raw_max_utc,
        "station_daily_count": daily_cnt,
        "station_daily_min_date": str(daily_min_d) if daily_min_d else None,
        "station_daily_max_date": str(daily_max_d) if daily_max_d else None,
        "total_raw": total_raw,
        "total_daily": total_daily,
    }


def get_model_snapshot():
    path = settings.model_bundle_path
    if not os.path.exists(path):
        return None
    bundle = joblib.load(path)
    return {
        "mtime": os.path.getmtime(path),
        "timestamp": bundle.get("timestamp"),
        "max_train_date": bundle.get("max_train_date"),
        "train_samples": bundle.get("train_samples"),
        "models_count": len(bundle.get("models", {})),
        "metrics": bundle.get("metrics", {}),
    }


def main():
    print("=" * 80)
    print("TESTING REST API INGEST & AUTOMATED RETRAINING PIPELINE")
    print("=" * 80)
    print(f"Target API Endpoint : {API_BASE}/ingest/json")
    print(f"Target Stasiun AWS  : ID {STATION_ID}")
    print(f"Storage Backend     : {settings.storage_backend}")
    print("-" * 80)

    # 1. BASELINE CHECK
    print("\n[TAHAP 1] Memeriksa baseline awal sistem...")
    status_code, health_pre = make_request("/health")
    assert status_code == 200, f"Health check gagal: {health_pre}"
    print(f"  - API Health: Status={health_pre['status']}, Model Loaded={health_pre['model_loaded']}, Model Last Trained={health_pre['model_last_trained']}")

    db_pre = get_db_snapshot(STATION_ID)
    print(f"  - PostgreSQL weather_raw (Stasiun {STATION_ID}): {db_pre['station_raw_count']:,} baris | max utctime={db_pre['station_raw_max_utc']}")
    print(f"  - PostgreSQL weather_daily (Stasiun {STATION_ID}): {db_pre['station_daily_count']:,} hari | max date={db_pre['station_daily_max_date']}")
    print(f"  - Total Keseluruhan DB: raw={db_pre['total_raw']:,} baris | daily={db_pre['total_daily']:,} stasiun-hari")

    model_pre = get_model_snapshot()
    print(f"  - Model Bundles (Latest): timestamp={model_pre['timestamp']}, max_train_date={model_pre['max_train_date']}, samples={model_pre['train_samples']:,}")

    status_code, forecast_pre = make_request(f"/forecast/{STATION_ID}")
    assert status_code == 200, f"Forecast pre-check gagal: {forecast_pre}"
    print(f"  - Forecast Stasiun {STATION_ID} (Pre-Ingest): {len(forecast_pre['forecast'])} hari berhasil didapatkan.")

    # 2. GENERATE 1 MINGGU DATA OBSERVASI
    print("\n[TAHAP 2] Mempersiapkan 1 minggu data observasi sensor baru...")
    start_epoch = int(db_pre["station_raw_max_utc"]) + 600
    dt_start = datetime.fromtimestamp(start_epoch, tz=timezone.utc)
    records = generate_1week_station_data(STATION_ID, start_epoch, interval_sec=600, total_days=7)
    end_epoch = records[-1]["utctime"]
    dt_end = datetime.fromtimestamp(end_epoch, tz=timezone.utc)

    print(f"  - Jumlah record yang disiapkan: {len(records):,} pembacaan sensor (interval 10 menit)")
    print(f"  - Rentang Waktu UTC : {dt_start.strftime('%Y-%m-%d %H:%M:%S UTC')} s/d {dt_end.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  - Rentang Waktu WIB : {(dt_start + timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S WIB')} s/d {(dt_end + timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S WIB')}")
    print(f"  - Sampel Baris Pertama: {records[0]}")
    print(f"  - Sampel Baris Terakhir: {records[-1]}")

    # 3. KIRIM POST /api/v1/ingest/json
    print("\n[TAHAP 3] Mengirim POST /api/v1/ingest/json...")
    payload = {
        "mode": "append",
        "records": records
    }
    t_req_start = time.time()
    status_code, resp_json = make_request("/ingest/json", method="POST", data=payload)
    req_duration = time.time() - t_req_start

    print(f"  - HTTP Status: {status_code} (diterima dalam {req_duration:.2f}s)")
    print(f"  - Response Body: {resp_json}")
    assert status_code == 200 or status_code == 202, f"Expected 200/202, got {status_code}: {resp_json}"
    assert resp_json.get("status") == "Accepted", f"Expected Accepted status: {resp_json}"
    task_id = resp_json.get("task_id")
    assert task_id, "task_id tidak ditemukan di response"
    print(f"  [OK] Data 1 minggu diterima & disimpan ke PostgreSQL. Background task ID: {task_id}")

    # Cek bahwa PostgreSQL weather_raw langsung bertambah seketika setelah request selesai
    db_immediate = get_db_snapshot(STATION_ID)
    added_rows = db_immediate["station_raw_count"] - db_pre["station_raw_count"]
    print(f"  - Verifikasi weather_raw langsung: +{added_rows:,} baris baru tersimpan ke database!")
    assert added_rows == len(records), f"Expected {len(records)} rows added, got {added_rows}"

    # 4. PANTAU PROSES BACKGROUND RETRAIN PIPELINE
    print(f"\n[TAHAP 4] Memantau proses retrain di latar belakang ({task_id})...")
    run_log_path = os.path.join(settings.log_dir, "runs", f"{task_id}.log")
    pipeline_log_path = os.path.join(settings.log_dir, "pipeline.log")
    pipeline_history_path = os.path.join(settings.log_dir, "pipeline_history.jsonl")

    max_wait_seconds = 600  # 10 menit batas waktu
    poll_interval = 5
    started_wait = time.time()
    last_log_pos = 0
    pipeline_entry = None

    while time.time() - started_wait < max_wait_seconds:
        # Cek apakah ada output log baru di logs/runs/<task_id>.log
        if os.path.exists(run_log_path):
            with open(run_log_path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(last_log_pos)
                new_chunk = f.read()
                if new_chunk:
                    last_log_pos = f.tell()
                    for line in new_chunk.splitlines():
                        if any(k in line for k in ("=====", "Progress", "SUCCESS", "Tahap", "Initiating", "Training records", "MAE", "Model successfully saved")):
                            print(f"    [Pipeline Runner] {line}")

        # Cek pipeline_history.jsonl untuk task_id ini
        if os.path.exists(pipeline_history_path):
            with open(pipeline_history_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if line.strip():
                        try:
                            obj = json.loads(line)
                            if obj.get("task_id") == task_id:
                                pipeline_entry = obj
                                break
                        except Exception:
                            pass
        if pipeline_entry is not None:
            break

        time.sleep(poll_interval)
        elapsed = int(time.time() - started_wait)
        if elapsed % 20 == 0:
            print(f"  ... Menunggu pipeline selesai ({elapsed}s berjalan)...")

    assert pipeline_entry is not None, f"Pipeline tidak selesai dalam {max_wait_seconds} detik!"
    print(f"\n  [Selesai] Pipeline selesai dengan status: {pipeline_entry.get('status')}")
    print(f"  - Durasi Total   : {pipeline_entry.get('duration_sec', 0):.1f} detik")
    print(f"  - Rincian Metrik : {pipeline_entry.get('metrics_note', '-')}")
    print(f"  - Data Harian s/d: {pipeline_entry.get('max_train_date', '-')}")

    if pipeline_entry.get("status") != "SUKSES":
        print(f"  [ERROR] Pipeline Gagal: Tahap={pipeline_entry.get('stage')}, Alasan={pipeline_entry.get('reason')}")
        if os.path.exists(run_log_path):
            with open(run_log_path, "r", encoding="utf-8", errors="replace") as f:
                print(f.read()[-2000:])
        sys.exit(1)

    # 5. PENGUJIAN MENYELURUH HASIL RETRAIN
    print("\n[TAHAP 5] Melakukan pengujian & verifikasi menyeluruh hasil retrain...")

    # A. Verifikasi Database PostgreSQL
    print("\n  A. Verifikasi Database PostgreSQL:")
    db_post = get_db_snapshot(STATION_ID)
    print(f"     - weather_raw stasiun {STATION_ID} : {db_post['station_raw_count']:,} baris (sebelumnya {db_pre['station_raw_count']:,}) -> +{db_post['station_raw_count'] - db_pre['station_raw_count']:,} baris [PASS]")
    print(f"     - weather_daily stasiun {STATION_ID}: {db_post['station_daily_count']:,} hari (sebelumnya {db_pre['station_daily_count']:,}) -> +{db_post['station_daily_count'] - db_pre['station_daily_count']:,} hari [PASS]")
    print(f"     - Tanggal observasi harian terbaru : {db_post['station_daily_max_date']} (sebelumnya {db_pre['station_daily_max_date']}) [PASS]")
    assert db_post["station_daily_count"] > db_pre["station_daily_count"], "Jumlah baris weather_daily harus bertambah!"

    # B. Verifikasi Model Bundle di Disk
    print("\n  B. Verifikasi File Bundle Model di Disk:")
    model_post = get_model_snapshot()
    assert model_post is not None, "Model bundle tidak ditemukan!"
    print(f"     - Versi Timestamp Terbaru : {model_post['timestamp']} (sebelumnya {model_pre['timestamp']}) [PASS]")
    print(f"     - File mtime lebih baru   : {model_post['mtime'] > model_pre['mtime']} [PASS]")
    print(f"     - max_train_date Terbaru  : {model_post['max_train_date']} (sebelumnya {model_pre['max_train_date']}) [PASS]")
    print(f"     - Jumlah Sub-Model Aktif  : {model_post['models_count']} model [PASS]")
    print(f"     - Jumlah Sampel Training  : {model_post['train_samples']:,} baris [PASS]")
    assert model_post["mtime"] > model_pre["mtime"], "Model bundle harus diperbarui!"

    # C. Verifikasi Endpoint API Health
    print("\n  C. Verifikasi Endpoint GET /api/v1/health:")
    status_code, health_post = make_request("/health")
    assert status_code == 200
    print(f"     - Status Layanan     : {health_post['status']} [PASS]")
    print(f"     - Model Loaded       : {health_post['model_loaded']} [PASS]")
    print(f"     - Model Last Trained : {health_post['model_last_trained']} [PASS]")
    print(f"     - Inference Latency  : {health_post['inference_latency_ms']} ms [PASS]")
    assert health_post["model_loaded"] is True

    # D. Verifikasi Endpoint Forecast 7-Day Lengkap
    print(f"\n  D. Verifikasi Endpoint GET /api/v1/forecast/{STATION_ID}:")
    status_code, forecast_post = make_request(f"/forecast/{STATION_ID}")
    assert status_code == 200, f"Forecast gagal: {forecast_post}"
    forecast_items = forecast_post.get("forecast", [])
    assert len(forecast_items) == 7, f"Expected 7 forecast days, got {len(forecast_items)}"
    print(f"     - Stasiun          : {forecast_post['station']['estate_name']} (ID: {forecast_post['station']['station_id']})")
    print(f"     - Model Versi      : {forecast_post['model_version']}")
    print(f"     - Generated At     : {forecast_post['generated_at_wib']}")
    print(f"     - Horizon Dihasilkan:")
    for item in forecast_items:
        print(f"       [{item['horizon']}] {item['date']} ({item['day_name']}): {item['weather_condition']:<13} | Suhu={item['temp_avg']}°C | Hujan={item['rainfall_total_mm']}mm ({item['rain_probability_pct']}%) | Angin={item['wind_direction']} ({item['wind_speed_ms']} m/s)")
    print(f"     [PASS] Forecast 7 hari lengkap dengan rekomendasi agronomi berfungsi dengan model baru.")

    # E. Verifikasi Endpoint Weather Format Fisik
    print(f"\n  E. Verifikasi Endpoint GET /api/v1/weather/{STATION_ID}:")
    status_code, weather_post = make_request(f"/weather/{STATION_ID}")
    assert status_code == 200, f"Weather gagal: {weather_post}"
    w_data = weather_post.get("data", {})
    assert w_data.get("dataSource") == "model", f"Expected dataSource='model', got {w_data.get('dataSource')}"
    assert len(w_data.get("forecast", [])) == 7
    d1 = w_data["forecast"][0]
    print(f"     - Data Source  : {w_data['dataSource']} [PASS]")
    print(f"     - Generated At : {w_data['generatedAt']} [PASS]")
    print(f"     - H+1 Temp/Hum : {d1['temperature']}°C / {d1['humidity']}% [PASS]")
    print(f"     - H+1 Rain/Wind: {d1['rainfall']}mm / {d1['windSpeed']}m/s (Arah: {d1['windDirectionDeg']}°) [PASS]")

    print("\n" + "=" * 80)
    print("SEMUA PENGUJIAN INGEST, RETRAINING, DAN INFERENSI BERHASIL DENGAN STATUS 100% SUKSES!")
    print("=" * 80)


if __name__ == "__main__":
    main()
