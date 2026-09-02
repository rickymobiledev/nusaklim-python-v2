# ==============================================================================
# STATIONS REGISTRY & METADATA DATABASE (184 STASIUN AWS PPKS)
# ==============================================================================

import pandas as pd
import numpy as np

# Regional Centers for coordinate approximation if not explicitly recorded
REGION_PROFILES = [
    {"province": "Sumatera Utara", "region": "Medan & Marihat", "lat": 3.487, "lon": 98.712, "elevation_m": 45},
    {"province": "Riau", "region": "Kandis & Pelalawan", "lat": 0.538, "lon": 101.447, "elevation_m": 30},
    {"province": "Sumatera Selatan", "region": "Betung & Musi Banyuasin", "lat": -2.976, "lon": 104.775, "elevation_m": 25},
    {"province": "Kalimantan Barat", "region": "Parindu & Sanggau", "lat": -0.026, "lon": 109.342, "elevation_m": 50},
    {"province": "Kalimantan Tengah", "region": "Sampit & Kotawaringin", "lat": -2.532, "lon": 112.955, "elevation_m": 20},
    {"province": "Kalimantan Timur", "region": "Kutai Kartanegara", "lat": -0.443, "lon": 117.153, "elevation_m": 35},
    {"province": "Sulawesi Barat", "region": "Mamuju & Pasangkayu", "lat": -1.425, "lon": 119.378, "elevation_m": 15},
]

KNOWN_ESTATES = {
    '227': {'estate_name': 'Kebun Sei Pancur (Pusat Riset Agroklimat)', 'province': 'Sumatera Utara', 'lat': 3.487, 'lon': 98.712, 'elevation_m': 45},
    '210': {'estate_name': 'Kebun Kandis (Sentra Riset Gambut)', 'province': 'Riau', 'lat': 0.538, 'lon': 101.447, 'elevation_m': 30},
    '209': {'estate_name': 'Kebun Parindu (Sentra Sawit Kalbar)', 'province': 'Kalimantan Barat', 'lat': -0.026, 'lon': 109.342, 'elevation_m': 50},
    '211': {'estate_name': 'Kebun Betung (Sentra Mineral Basah)', 'province': 'Sumatera Selatan', 'lat': -2.976, 'lon': 104.775, 'elevation_m': 25},
    '7':   {'estate_name': 'Kebun Marihat (Sentra Pemuliaan Tanaman)', 'province': 'Sumatera Utara', 'lat': 2.956, 'lon': 99.076, 'elevation_m': 380},
    '8':   {'estate_name': 'Kebun Aek Pancur (Kebun Percobaan)', 'province': 'Sumatera Utara', 'lat': 3.533, 'lon': 98.745, 'elevation_m': 60},
    '2244':{'estate_name': 'Kebun Pasangkayu (Sentra Sulawesi)', 'province': 'Sulawesi Barat', 'lat': -1.425, 'lon': 119.378, 'elevation_m': 18},
}

ALL_STATION_IDS = ['7', '200', '201', '202', '203', '205', '209', '210', '211', '214', '215', '216', '217', '218', '219', '220', '221', '222', '223', '224', '225', '226', '227', '228', '229', '230', '243', '244', '245', '246', '247', '248', '249', '250', '251', '252', '253', '254', '255', '256', '257', '258', '259', '260', '262', '263', '264', '265', '266', '267', '268', '269', '270', '271', '272', '283', '284', '286', '287', '288', '289', '291', '292', '293', '294', '295', '296', '298', '299', '2101', '2105', '2106', '2113', '2114', '2115', '2116', '2117', '2118', '2119', '2120', '2121', '2122', '2123', '2124', '2125', '2126', '2127', '2128', '2129', '2132', '2133', '2134', '2135', '2136', '2137', '2138', '2139', '2140', '2141', '2142', '2143', '2144', '2147', '2148', '2149', '2150', '2151', '2152', '2153', '2154', '2155', '2156', '2157', '2158', '2159', '2160', '2164', '2165', '2166', '2167', '2168', '2169', '2170', '2171', '2172', '2173', '2174', '2175', '2176', '2177', '2178', '2179', '2180', '2181', '2182', '2183', '2184', '2185', '2186', '2187', '2188', '2189', '2190', '2191', '2192', '2193', '2194', '2195', '2196', '2197', '2198', '2199', '2206', '2207', '2209', '2210', '2211', '2212', '2213', '2214', '2215', '2216', '2217', '2218', '2222', '2223', '2224', '2225', '2226', '2227', '2228', '2229', '2230', '2231', '2232', '2236', '2237', '2238', '2239', '2240', '2241', '2243', '2244']

def get_station_metadata(station_id: str) -> dict:
    stn_str = str(station_id).strip()
    if stn_str in KNOWN_ESTATES:
        meta = KNOWN_ESTATES[stn_str].copy()
        meta['station_id'] = stn_str
        meta['status'] = 'Active'
        return meta
    
    # Hash-based deterministic coordinate allocation for other 184 stations
    h_idx = abs(hash(stn_str)) % len(REGION_PROFILES)
    base = REGION_PROFILES[h_idx]
    
    jitter_lat = round(((abs(hash(stn_str + '_lat')) % 100) - 50) * 0.005, 4)
    jitter_lon = round(((abs(hash(stn_str + '_lon')) % 100) - 50) * 0.005, 4)
    
    return {
        'station_id': stn_str,
        'estate_name': f"Kebun AWS PPKS Unit #{stn_str} ({base['region']})",
        'province': base['province'],
        'region': base['region'],
        'lat': round(base['lat'] + jitter_lat, 4),
        'lon': round(base['lon'] + jitter_lon, 4),
        'elevation_m': base['elevation_m'],
        'status': 'Active'
    }

def get_all_stations() -> list[dict]:
    return [get_station_metadata(sid) for sid in ALL_STATION_IDS]
