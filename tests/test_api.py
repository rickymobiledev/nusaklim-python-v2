# ==============================================================================
# AUTOMATED TEST SUITE FOR FASTAPI BACKEND ENDPOINTS
# ==============================================================================

import sys
import os
import time
from fastapi.testclient import TestClient

# Ensure root directory is on path
sys.path.insert(0, "d:/Downloads/nusaklim")

from api.main import app

client = TestClient(app)

print("=== RUNNING FASTAPI AUTOMATED ENDPOINT VERIFICATION ===")

def test_root_redirect():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in [302, 307], f"Expected redirect, got {response.status_code}"
    print("[PASS] GET / -> Redirects to /docs successfully.")

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200, f"Health check failed: {response.text}"
    data = response.json()
    assert data["status"] == "Healthy"
    assert data["total_active_stations"] >= 180
    assert data["model_loaded"] is True
    print(f"[PASS] GET /api/v1/health -> Status: {data['status']}, Latency: {data['inference_latency_ms']} ms, Stations: {data['total_active_stations']}")

def test_stations_list():
    response = client.get("/api/v1/stations")
    assert response.status_code == 200
    data = response.json()
    assert data["total_stations"] >= 180
    assert len(data["stations"]) >= 180
    first_stn = data["stations"][0]
    assert "station_id" in first_stn
    assert "lat" in first_stn and "lon" in first_stn
    print(f"[PASS] GET /api/v1/stations -> Successfully returned {data['total_stations']} AWS stations.")

def test_station_detail():
    response = client.get("/api/v1/stations/227")
    assert response.status_code == 200
    data = response.json()
    assert data["station_id"] == "227"
    assert "Sei Pancur" in data["estate_name"]
    print(f"[PASS] GET /api/v1/stations/227 -> {data['estate_name']} ({data['province']})")

def test_forecast_7_days():
    t0 = time.time()
    response = client.get("/api/v1/forecast/227")
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
    response = client.get("/api/v1/compare/227")
    assert response.status_code == 200
    data = response.json()
    assert "evaluation_summary" in data
    assert len(data["comparison_series"]) == 7
    print(f"[PASS] GET /api/v1/compare/227 -> Accuracy Advantage: {data['evaluation_summary']['accuracy_advantage']}")

def test_retrain_trigger():
    response = client.post("/api/v1/retrain")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Accepted"
    assert "task_id" in data
    print(f"[PASS] POST /api/v1/retrain -> Status: {data['status']}, Task ID: {data['task_id']}")

if __name__ == "__main__":
    test_root_redirect()
    test_health_endpoint()
    test_stations_list()
    test_station_detail()
    test_forecast_7_days()
    test_compare_endpoint()
    test_retrain_trigger()
    print("\n=======================================================")
    print("ALL 7 FASTAPI BACKEND TEST CASES PASSED WITH 100% SUCCESS!")
    print("=======================================================")
