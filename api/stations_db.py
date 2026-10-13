# ==============================================================================
# STATIONS REGISTRY & METADATA (sumber: device_nusaklim.csv / weather_stations)
# ==============================================================================

import pandas as pd

_stations_cache = None

def _get_device_df():
    global _stations_cache
    if _stations_cache is not None:
        return _stations_cache
    try:
        from api.weather_store import load_stations
        df = load_stations()
        if not df.empty:
            _stations_cache = df.set_index("id", drop=False)
            return _stations_cache
    except Exception:
        pass
    return None

def _clean(value):
    if value is None or pd.isna(value):
        return None
    value = str(value).strip()
    return value or None

def _to_float(value):
    try:
        return float(value) if pd.notna(value) else None
    except (ValueError, TypeError):
        return None

def get_station_metadata(station_id: str) -> dict:
    """Metadata stasiun dari device_nusaklim.csv / tabel weather_stations.

    Field yang tidak ada di sumber (province, elevation_m) dikembalikan None,
    bukan diisi nilai tebakan.
    """
    stn_str = str(station_id).strip()
    dev_df = _get_device_df()
    if dev_df is not None and stn_str in dev_df.index:
        row = dev_df.loc[stn_str]
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]
        return {
            'station_id': stn_str,
            'estate_name': _clean(row.get('name')) or f"Stasiun AWS #{stn_str}",
            'province': None,
            'region': _clean(row.get('company_name')),
            'lat': _to_float(row.get('latitude')),
            'lon': _to_float(row.get('longitude')),
            'elevation_m': None,
            'status': 'Active'
        }

    return {
        'station_id': stn_str,
        'estate_name': f"Stasiun AWS #{stn_str}",
        'province': None,
        'region': None,
        'lat': None,
        'lon': None,
        'elevation_m': None,
        'status': 'Unknown'
    }

def get_all_stations() -> list[dict]:
    dev_df = _get_device_df()
    if dev_df is None or dev_df.empty:
        return []
    ids = dict.fromkeys(str(i).strip() for i in dev_df.index)
    return [get_station_metadata(sid) for sid in ids if sid]
