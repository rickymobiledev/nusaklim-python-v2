# ==============================================================================
# NUSAKLIM AWS - PUSAT PENELITIAN KELAPA SAWIT (PPKS)
# PEMBERSIHAN DATA TINGKAT INTERVAL (10-15 MENIT) -> nusaklim_cleaned_interval.csv
# Kriteria kewajaran fisik direvisi sesuai catatan tim peneliti (September 2026)
# ==============================================================================

import os
import time
import json
import numpy as np
import pandas as pd

BASE_DIR = r"D:\Projects\Kodepanda\Nusaklim\nusaklim"
INPUT_CSV = os.path.join(BASE_DIR, "data_raw", "nusaklim-aws-reduce.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "nusaklim_cleaned_interval.csv")
STATS_JSON = os.path.join(BASE_DIR, "interval_cleaning_stats.json")
CHUNK_SIZE = 500_000

RTC_EPOCH_CUTOFF = 1640995200  # 2022-01-01 00:00 UTC
DUMMY_STATIONS = ['WiFiLogger', '9991', '9992', '9993', '9994', '9995', 'nan', '---', '']


def run():
    start_time = time.time()
    total_raw_rows = 0
    dropped_non_station = 0
    dropped_invalid_timestamp = 0
    dropped_epoch_setup = 0
    retained_valid_rows = 0

    qc_dropped = {
        'temp': 0, 'humidity': 0, 'pressure': 0,
        'rain': 0, 'solar': 0, 'windspd': 0, 'winddir': 0,
    }

    first_write = True
    chunk_count = 0

    print(f"Reading raw file: {INPUT_CSV}")
    for chunk in pd.read_csv(INPUT_CSV, chunksize=CHUNK_SIZE, low_memory=False):
        chunk_count += 1
        total_raw_rows += len(chunk)

        # 1. Filter stasiun non-AWS (ID uji internal)
        chunk['stnname'] = chunk['stnname'].astype(str).str.strip()
        dummy_mask = chunk['stnname'].isin(DUMMY_STATIONS)
        dropped_non_station += dummy_mask.sum()
        chunk = chunk[~dummy_mask]
        if chunk.empty:
            continue

        # 2. Parsing timestamp & filter RTC reset (< 2022-01-01)
        utctime_num = pd.to_numeric(chunk['utctime'], errors='coerce')
        nan_utc = utctime_num.isna()
        dropped_invalid_timestamp += nan_utc.sum()
        chunk = chunk[~nan_utc]
        utctime_num = utctime_num[~nan_utc]
        if chunk.empty:
            continue

        setup_mask = utctime_num < RTC_EPOCH_CUTOFF
        dropped_epoch_setup += setup_mask.sum()
        chunk = chunk[~setup_mask]
        utctime_num = utctime_num[~setup_mask]
        if chunk.empty:
            continue

        retained_valid_rows += len(chunk)

        # 3. Konversi satuan & kriteria kewajaran fisik (batas baru per variabel)
        temp_raw = pd.to_numeric(chunk['tempout'].replace('---', np.nan), errors='coerce')
        temp_c = (temp_raw - 32.0) * (5.0 / 9.0)
        temp_invalid = (temp_c < 0.0) | (temp_c > 100.0) | (temp_raw == 3276.7) | (temp_raw == -90)
        qc_dropped['temp'] += temp_invalid.sum()
        temp_c = temp_c.mask(temp_invalid)

        hum_raw = pd.to_numeric(chunk['humout'].replace('---', np.nan), errors='coerce')
        hum_invalid = (hum_raw < 0.0) | (hum_raw > 100.0) | (hum_raw == -1) | (hum_raw == 255)
        qc_dropped['humidity'] += hum_invalid.sum()
        humidity_pct = hum_raw.mask(hum_invalid)

        bar_raw = pd.to_numeric(chunk['bar'].replace('---', np.nan), errors='coerce')
        pressure_hpa = bar_raw * 33.864
        pressure_invalid = (pressure_hpa < 500.0) | (pressure_hpa > 1200.0)
        qc_dropped['pressure'] += pressure_invalid.sum()
        pressure_hpa = pressure_hpa.mask(pressure_invalid)

        rain_raw = pd.to_numeric(chunk['rain15'].replace('---', np.nan), errors='coerce')
        rainfall_mm = rain_raw * 12.70
        rain_invalid = (rainfall_mm < 0) | (rainfall_mm > 1000.0)
        qc_dropped['rain'] += rain_invalid.sum()
        rainfall_mm = rainfall_mm.mask(rain_invalid)

        solar_raw = pd.to_numeric(chunk['solar'].replace('---', np.nan), errors='coerce')
        solar_invalid = (solar_raw < 0) | (solar_raw > 2000) | (solar_raw == 32767)
        qc_dropped['solar'] += solar_invalid.sum()
        solar_radiation_wm2 = solar_raw.mask(solar_invalid)

        windspd_raw = pd.to_numeric(chunk['windspd'].replace('---', np.nan), errors='coerce')
        windspd_invalid = (windspd_raw < 0) | (windspd_raw > 100.0) | (windspd_raw == 255)
        qc_dropped['windspd'] += windspd_invalid.sum()
        wind_speed_kmh = windspd_raw.mask(windspd_invalid)

        winddir_raw = pd.to_numeric(chunk['winddir'].replace('---', np.nan), errors='coerce')
        winddir_invalid = (winddir_raw < 0) | (winddir_raw > 360.0) | (winddir_raw == 32767)
        qc_dropped['winddir'] += winddir_invalid.sum()
        wind_direction_deg = winddir_raw.mask(winddir_invalid)

        # 4. Konversi waktu lokal WIB (UTC+7)
        datetime_wib = pd.to_datetime(utctime_num, unit='s') + pd.Timedelta(hours=7)

        clean_chunk = pd.DataFrame({
            'stnname': chunk['stnname'].values,
            'datetime_wib': datetime_wib.dt.strftime('%Y-%m-%d %H:%M:%S').values,
            'utctime': utctime_num.astype('int64').values,
            'temp_c': temp_c.round(2).values,
            'humidity_pct': humidity_pct.round(2).values,
            'pressure_hpa': pressure_hpa.round(2).values,
            'rainfall_mm': rainfall_mm.round(2).values,
            'solar_radiation_wm2': solar_radiation_wm2.round(1).values,
            'wind_speed_kmh': wind_speed_kmh.round(2).values,
            'wind_direction_deg': wind_direction_deg.round(1).values,
        })

        clean_chunk.to_csv(OUTPUT_CSV, mode='w' if first_write else 'a', header=first_write, index=False)
        first_write = False

        if chunk_count % 5 == 0:
            print(f"  Progress: {total_raw_rows:,} raw rows processed ({time.time() - start_time:.1f}s)...")

    elapsed = time.time() - start_time
    stats = {
        'total_raw_rows': int(total_raw_rows),
        'dropped_non_station': int(dropped_non_station),
        'dropped_invalid_timestamp': int(dropped_invalid_timestamp),
        'dropped_epoch_setup': int(dropped_epoch_setup),
        'retained_valid_rows': int(retained_valid_rows),
        'qc_masked_to_nan': {k: int(v) for k, v in qc_dropped.items()},
        'output_file_bytes': os.path.getsize(OUTPUT_CSV),
        'elapsed_seconds': round(elapsed, 1),
        'thresholds': {
            'temp_c': [0.0, 100.0],
            'humidity_pct': [0.0, 100.0],
            'pressure_hpa': [500.0, 1200.0],
            'rainfall_mm': [0.0, 1000.0],
            'solar_radiation_wm2': [0.0, 2000.0],
            'wind_speed_kmh': [0.0, 100.0],
            'wind_direction_deg': [0.0, 360.0],
        }
    }
    with open(STATS_JSON, 'w') as f:
        json.dump(stats, f, indent=2)

    print("=" * 75)
    print(f"SUCCESS: {retained_valid_rows:,} baris valid ditulis ke {OUTPUT_CSV}")
    print(f"Ukuran file: {os.path.getsize(OUTPUT_CSV):,} bytes")
    print(f"Waktu proses: {elapsed:.1f}s")
    print(f"Statistik disimpan di: {STATS_JSON}")
    print(json.dumps(stats, indent=2))


if __name__ == '__main__':
    run()
