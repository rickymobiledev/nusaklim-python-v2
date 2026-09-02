# ==============================================================================
# ASYNC OPEN-METEO SERVICE CLIENT
# ==============================================================================

import httpx
import pandas as pd
from typing import Optional, Dict, Any

async def fetch_openmeteo_forecast(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
        f"precipitation_sum,precipitation_probability_max,relative_humidity_2m_mean,wind_direction_10m_dominant&"
        f"timezone=Asia%2FJakarta&forecast_days=7"
    )
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json().get('daily', {})
    except Exception as e:
        print(f"[Warning] Failed to fetch live Open-Meteo forecast: {e}")
    return None

async def fetch_openmeteo_archive(lat: float, lon: float, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}&"
        f"start_date={start_date}&end_date={end_date}&"
        f"daily=temperature_2m_mean,relative_humidity_2m_mean,precipitation_sum&"
        f"timezone=Asia%2FJakarta"
    )
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json().get('daily', {})
    except Exception as e:
        print(f"[Warning] Failed to fetch Open-Meteo archive: {e}")
    return None
