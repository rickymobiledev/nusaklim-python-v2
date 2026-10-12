# ==============================================================================
# AUTOMATED TEST SUITE FOR FASTAPI BACKEND ENDPOINTS
# ==============================================================================

import sys
import os
import time
from fastapi.testclient import TestClient

# Ensure project root is on path (robust - tidak bergantung pada lokasi checkout/mesin)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.main import app
from api.config import settings

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": settings.weather_api_key}

print("=== RUNNING FASTAPI AUTOMATED ENDPOINT VERIFICATION ===")

def test_root_redirect():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in [302, 307], f"Expected redirect, got {response.status_code}"
    print("[PASS] GET / -> Redirects to /docs successfully.")

def test_health_endpoint():
    response = client.get("/api/v1/health", headers=AUTH_HEADERS)
    assert response.status_code == 200, f"Health check failed: {response.text}"
    data = response.json()
    assert data["status"] == "Healthy"
    assert data["total_active_stations"] >= 180
    assert data["model_loaded"] is True
    print(f"[PASS] GET /api/v1/health -> Status: {data['status']}, Latency: {data['inference_latency_ms']} ms, Stations: {data['total_active_stations']}")

def test_stations_list():
    response = client.get("/api/v1/stations", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["total_stations"] >= 180
    assert len(data["stations"]) >= 180
    first_stn = data["stations"][0]
    assert "station_id" in first_stn
    assert "lat" in first_stn and "lon" in first_stn
    print(f"[PASS] GET /api/v1/stations -> Successfully returned {data['total_stations']} AWS stations.")

def test_station_detail():
    response = client.get("/api/v1/stations/227", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["station_id"] == "227"
    assert "Sei Pancur" in data["estate_name"]
    print(f"[PASS] GET /api/v1/stations/227 -> {data['estate_name']} ({data['province']})")

def test_forecast_7_days():
    t0 = time.time()
    response = client.get("/api/v1/forecast/227", headers=AUTH_HEADERS)
    latency = (time.time() - t0) * 1000
    assert response.status_code == 200, f"Forecast failed: {response.text}"
    data = response.json()
    
    assert data["station"]["station_id"] == "227"
    assert len(data["forecast"]) == 7, f"Expected 7-day forecast items, got {len(data['forecast'])}"
    
    h1 = data["forecast"][0]
    assert h1["horizon"] == "H+1"
    assert "temp_avg" in h1
    assert "agronomic_advisory" in h1
    assert len(h1["agronomic_advisory"]) > 5
    
    print(f"[PASS] GET /api/v1/forecast/227 -> Latency: {latency:.2f} ms | 7 Horizons Returned:")
    for item in data["forecast"]:
        print(f"       - {item['horizon']} ({item['day_name']}, {item['date']}): {item['weather_condition']} | Temp: {item['temp_avg']} C | Rain: {item['rainfall_total_mm']} mm ({item['rain_probability_pct']}%) | Wind: {item['wind_direction']}")
        print(f"         Advisory: '{item['agronomic_advisory'][:60]}...'")

def test_compare_endpoint():
    response = client.get("/api/v1/compare/227", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "evaluation_summary" in data
    assert len(data["comparison_series"]) == 7
    print(f"[PASS] GET /api/v1/compare/227 -> Accuracy Advantage: {data['evaluation_summary']['accuracy_advantage']}")

def test_weather_requires_api_key():
    response = client.get("/api/v1/weather/227")
    assert response.status_code == 401, f"Expected 401 without API key, got {response.status_code}"
    print("[PASS] GET /api/v1/weather/227 (tanpa X-API-Key) -> 401 Unauthorized seperti diharapkan.")

def test_all_endpoints_require_api_key():
    for path in ("/api/v1/health", "/api/v1/stations", "/api/v1/forecast/227", "/api/v1/compare/227"):
        assert client.get(path).status_code == 401, f"{path} harus 401 tanpa X-API-Key"
        assert client.get(path, headers={"X-API-Key": "salah"}).status_code == 401, f"{path} harus 401 dengan key salah"
    assert client.post("/api/v1/retrain").status_code == 401
    print("[PASS] Semua endpoint -> 401 tanpa/dengan X-API-Key salah.")

def test_weather_physical_format():
    response = client.get("/api/v1/weather/227", headers=AUTH_HEADERS)
    assert response.status_code == 200, f"Weather (physical) failed: {response.text}"
    data = response.json()["data"]

    assert data["stationId"] == "227"
    assert len(data["forecast"]) == 7, f"Expected 7-day forecast items, got {len(data['forecast'])}"
    assert data["dataSource"] in ("model", "fallback_statistik")
    assert "generatedAt" in data

    d1 = data["forecast"][0]
    for field in ("temperature", "humidity", "radiation", "rainfall", "airPressure", "windSpeed", "windDirectionDeg"):
        assert field in d1, f"Field '{field}' hilang dari response /weather"
    print(f"[PASS] GET /api/v1/weather/227 -> dataSource: {data['dataSource']}, H+1 temperature: {d1['temperature']}°C")

def test_weather_bulk():
    response = client.get("/api/v1/weather", params={"stationIds": "227,210,2207"}, headers=AUTH_HEADERS)
    assert response.status_code == 200, f"Weather bulk failed: {response.text}"
    data = response.json()
    assert len(data["data"]) == 3, f"Expected 3 stations, got {len(data['data'])}"
    assert data["errors"] == []
    print(f"[PASS] GET /api/v1/weather?stationIds=227,210,2207 -> {len(data['data'])} stasiun berhasil, 0 error.")

def test_weather_bulk_exceeds_limit():
    ids = ",".join(str(i) for i in range(settings.max_bulk_stations + 10))
    response = client.get("/api/v1/weather", params={"stationIds": ids}, headers=AUTH_HEADERS)
    assert response.status_code == 400, f"Expected 400 for bulk limit, got {response.status_code}"
    print(f"[PASS] GET /api/v1/weather (>{settings.max_bulk_stations} station_id) -> 400 Bad Request seperti diharapkan.")

def test_retrain_trigger():
    response = client.post("/api/v1/retrain", headers=AUTH_HEADERS)
    # 409 valid kalau ada job retrain/ingest lain yang kebetulan masih berjalan (test lock konkurensi)
    assert response.status_code in (200, 409), f"Unexpected status: {response.status_code} - {response.text}"
    data = response.json()
    if response.status_code == 200:
        assert data["status"] == "Accepted"
        assert "task_id" in data
    print(f"[PASS] POST /api/v1/retrain -> HTTP {response.status_code} ({data.get('status') or data.get('detail')})")

def test_ingest_requires_api_key():
    response = client.post("/api/v1/ingest")
    assert response.status_code == 401, f"Expected 401 without API key, got {response.status_code}"
    print("[PASS] POST /api/v1/ingest (tanpa X-API-Key) -> 401 Unauthorized seperti diharapkan.")

def test_ingest_trigger():
    response = client.post("/api/v1/ingest", headers=AUTH_HEADERS)
    # 409 valid kalau test_retrain_trigger masih memegang training lock
    assert response.status_code in (200, 409), f"Unexpected status: {response.status_code} - {response.text}"
    data = response.json()
    print(f"[PASS] POST /api/v1/ingest -> HTTP {response.status_code} ({data.get('status') or data.get('detail')})")

def test_ingest_upload_requires_api_key():
    response = client.post("/api/v1/ingest/upload", files={"file": ("x.csv", b"a,b\n1,2\n", "text/csv")})
    assert response.status_code == 401, f"Expected 401 without API key, got {response.status_code}"
    print("[PASS] POST /api/v1/ingest/upload (tanpa X-API-Key) -> 401 Unauthorized seperti diharapkan.")

def test_ingest_upload_rejects_invalid_csv():
    response = client.post("/api/v1/ingest/upload", headers=AUTH_HEADERS,
                           files={"file": ("bad.csv", b"a,b\n1,2\n", "text/csv")})
    # 409 valid kalau test lain masih memegang training lock
    assert response.status_code in (400, 409), f"Unexpected status: {response.status_code} - {response.text}"
    print(f"[PASS] POST /api/v1/ingest/upload (CSV kolom salah) -> HTTP {response.status_code} seperti diharapkan.")

def test_ingest_json_requires_api_key():
    response = client.post("/api/v1/ingest/json", json={"records": [{"stnname": "227", "utctime": 1787136600}]})
    assert response.status_code == 401, f"Expected 401 without API key, got {response.status_code}"
    print("[PASS] POST /api/v1/ingest/json (tanpa X-API-Key) -> 401 Unauthorized seperti diharapkan.")

def test_ingest_json_rejects_invalid_payload():
    # Sengaja payload tidak valid agar pipeline 24 menit TIDAK terpicu
    for body in ({"records": []}, {"records": [{"stnname": "227"}]}, {"mode": "x", "records": [{"stnname": "227", "utctime": 1}]}):
        response = client.post("/api/v1/ingest/json", headers=AUTH_HEADERS, json=body)
        assert response.status_code == 422, f"Expected 422 for {body}, got {response.status_code}"
def test_ingest_json_no_retrain():
    body = {
        "mode": "append",
        "trigger_retrain": False,
        "records": [{"stnname": "227", "utctime": 1787136600, "tempout": 78.5}]
    }
    response = client.post("/api/v1/ingest/json", headers=AUTH_HEADERS, json=body)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["status"] == "Accepted"
    assert "batch-ingest-" in data["task_id"]
    assert "tanpa retrain" in data["message"]
    print(f"[PASS] POST /api/v1/ingest/json (trigger_retrain=False) -> {data['message']}")

def test_ingest_upload_no_retrain():
    csv_bytes = b"stnname,utctime,tempout,humout,windspd,winddir,bar,solar,rain15\n227,1787136600,78.5,85.0,2.0,180.0,29.9,500.0,0.0\n"
    response = client.post(
        "/api/v1/ingest/upload",
        headers=AUTH_HEADERS,
        data={"mode": "append", "trigger_retrain": "false"},
        files={"file": ("test.csv", csv_bytes, "text/csv")}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["status"] == "Accepted"
    assert "batch-upload-" in data["task_id"]
    assert "tanpa retrain" in data["message"]
    print(f"[PASS] POST /api/v1/ingest/upload (trigger_retrain=False) -> {data['message']}")

TEST_FUNCS = [
    test_root_redirect,
    test_health_endpoint,
    test_stations_list,
    test_station_detail,
    test_forecast_7_days,
    test_compare_endpoint,
    test_weather_requires_api_key,
    test_all_endpoints_require_api_key,
    test_weather_physical_format,
    test_weather_bulk,
    test_weather_bulk_exceeds_limit,
    test_retrain_trigger,
    test_ingest_requires_api_key,
    test_ingest_upload_requires_api_key,
    test_ingest_upload_rejects_invalid_csv,
    test_ingest_json_requires_api_key,
    test_ingest_json_rejects_invalid_payload,
    test_ingest_json_no_retrain,
    test_ingest_upload_no_retrain,
    test_ingest_trigger,
]

if __name__ == "__main__":
    for fn in TEST_FUNCS:
        fn()
    print("\n=======================================================")
    print(f"ALL {len(TEST_FUNCS)} FASTAPI BACKEND TEST CASES PASSED WITH 100% SUCCESS!")
    print("=======================================================")
