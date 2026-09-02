# ==============================================================================
# NUSAKLIM AWS - PUSAT PENELITIAN KELAPA SAWIT (PPKS)
# PRODUCTION DATA PREPROCESSING & EXPLORATORY DATA ANALYSIS (EDA) PIPELINE
# Berdasarkan Notulen Rapat Pembahasan Data Cuaca (20 Agustus 2026)
# ==============================================================================

import os
import sys
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def run_nusaklim_pipeline(
    input_csv=r"d:\Downloads\nusaklim\nusaklim-aws-reduce.csv",
    output_daily_csv=r"d:\Downloads\nusaklim\nusaklim_daily_aggregated.csv",
    figures_output_dir=r"d:\Downloads\nusaklim\figures",
    chunk_size=500000
):
    print("=" * 75)
    print("STARTING NUSAKLIM DATA PREPROCESSING & EDA PIPELINE (PPKS)")
    print("=" * 75)
    start_time = time.time()
    os.makedirs(figures_output_dir, exist_ok=True)

    total_raw_rows = 0
    dropped_non_station = 0
    dropped_invalid_timestamp = 0
    dropped_epoch_setup = 0
    retained_valid_rows = 0

    daily_data = {}
    interval_sample = []

    qc_flags = {
        'temp_qc_dropped': 0,
        'hum_qc_dropped': 0,
        'bar_qc_dropped': 0,
        'rain_qc_dropped': 0,
        'solar_qc_dropped': 0,
        'windspd_qc_dropped': 0,
        'winddir_qc_dropped': 0
    }

    chunk_count = 0
    print(f"Reading raw file: {input_csv}")
    print(f"Chunk processing size: {chunk_size:,} rows per batch")

    for chunk in pd.read_csv(input_csv, chunksize=chunk_size, low_memory=False):
        chunk_count += 1
        total_raw_rows += len(chunk)
        
        # 1. Bersihkan ID Stasiun
        chunk['stnname'] = chunk['stnname'].astype(str).str.strip()
        dummy_mask = chunk['stnname'].isin(['WiFiLogger', '9991', '9992', '9993', '9994', '9995', 'nan', '---', ''])
        dropped_non_station += dummy_mask.sum()
        chunk = chunk[~dummy_mask]
        if chunk.empty:
            continue
            
        # 2. Parsing Timestamp & Filter Setup Awal (< 2022-01-01)
        chunk['utctime_num'] = pd.to_numeric(chunk['utctime'], errors='coerce')
        nan_utc = chunk['utctime_num'].isna()
        dropped_invalid_timestamp += nan_utc.sum()
        chunk = chunk[~nan_utc]
        if chunk.empty:
            continue
            
        setup_mask = chunk['utctime_num'] < 1640995200  # Unix 2022-01-01
        dropped_epoch_setup += setup_mask.sum()
        chunk = chunk[~setup_mask]
        if chunk.empty:
            continue
            
        retained_valid_rows += len(chunk)
        
        # 3. Quality Control (QC) & Konversi Satuan (Sesuai Notulen Rapat)
        # Suhu (?F -> ?C, ambang batas tropis 12?C - 45?C, filter kode 3276.7?F & 0?F)
        temp_raw = pd.to_numeric(chunk['tempout'].replace('---', np.nan), errors='coerce')
        temp_c = (temp_raw - 32.0) * (5.0 / 9.0)
        temp_invalid = (temp_c < 12.0) | (temp_c > 45.0) | (temp_raw == 3276.7) | (temp_raw == 0)
        qc_flags['temp_qc_dropped'] += temp_invalid.sum()
        temp_c = temp_c.mask(temp_invalid)
        
        # Barometer (inHg -> hPa, ambang batas 920 - 1040 hPa)
        bar_raw = pd.to_numeric(chunk['bar'].replace('---', np.nan), errors='coerce')
        bar_hpa = bar_raw * 33.864
        bar_invalid = (bar_hpa < 920.0) | (bar_hpa > 1040.0)
        qc_flags['bar_qc_dropped'] += bar_invalid.sum()
        bar_hpa = bar_hpa.mask(bar_invalid)
        
        # Curah Hujan (rain15 * 12.70 -> mm, filter lonjakan rollover > 60 mm/15-min)
        rain_raw = pd.to_numeric(chunk['rain15'].replace('---', np.nan), errors='coerce')
        rain_invalid = (rain_raw < 0) | (rain_raw > 4.72)
        qc_flags['rain_qc_dropped'] += rain_invalid.sum()
        rain_raw = rain_raw.mask(rain_invalid)
        rain_mm = rain_raw * 12.70
        
        # Radiasi Solar (0 - 1500 W/m2, filter kode 32767)
        solar_raw = pd.to_numeric(chunk['solar'].replace('---', np.nan), errors='coerce')
        solar_invalid = (solar_raw < 0) | (solar_raw > 1500) | (solar_raw == 32767)
        qc_flags['solar_qc_dropped'] += solar_invalid.sum()
        solar_raw = solar_raw.mask(solar_invalid)
        
        # Kelembapan Relatif (15% - 100%, filter kode -1 dan 255)
        hum_raw = pd.to_numeric(chunk['humout'].replace('---', np.nan), errors='coerce')
        hum_invalid = (hum_raw < 15.0) | (hum_raw > 100.0) | (hum_raw == 255) | (hum_raw == -1)
        qc_flags['hum_qc_dropped'] += hum_invalid.sum()
        hum_raw = hum_raw.mask(hum_invalid)
        
        # Kecepatan Angin (0 - 80 km/h, filter kode 255)
        windspd_raw = pd.to_numeric(chunk['windspd'].replace('---', np.nan), errors='coerce')
        windspd_invalid = (windspd_raw < 0) | (windspd_raw > 80.0) | (windspd_raw == 255)
        qc_flags['windspd_qc_dropped'] += windspd_invalid.sum()
        windspd_raw = windspd_raw.mask(windspd_invalid)
        
        # Arah Angin Derajat (0? - 360?, filter kode 32767)
        winddir_raw = pd.to_numeric(chunk['winddir'].replace('---', np.nan), errors='coerce')
        winddir_invalid = (winddir_raw < 0) | (winddir_raw > 360.0) | (winddir_raw == 32767)
        qc_flags['winddir_qc_dropped'] += winddir_invalid.sum()
        winddir_raw = winddir_raw.mask(winddir_invalid)
        
        # Konversi Waktu Lokal Indonesia (WIB = UTC+7)
        dt_wib = pd.to_datetime(chunk['utctime_num'], unit='s') + pd.Timedelta(hours=7)
        date_str = dt_wib.dt.strftime('%Y-%m-%d')
        hour_val = dt_wib.dt.hour
        
        clean_chunk = pd.DataFrame({
            'stnname': chunk['stnname'],
            'date': date_str,
            'hour': hour_val,
            'temp_c': temp_c,
            'bar_hpa': bar_hpa,
            'rain_mm': rain_mm,
            'solar': solar_raw,
            'hum': hum_raw,
            'windspd': windspd_raw,
            'winddir': winddir_raw
        })
        
        # Subsampling interval untuk analisis EDA
        interval_sample.append(clean_chunk.iloc[::100])
        
        # 4. Agregasi Harian per Stasiun (SUM vs MEAN)
        grp = clean_chunk.groupby(['stnname', 'date'])
        agg_chunk = grp.agg(
            temp_sum=('temp_c', 'sum'), temp_count=('temp_c', 'count'), temp_min=('temp_c', 'min'), temp_max=('temp_c', 'max'),
            bar_sum=('bar_hpa', 'sum'), bar_count=('bar_hpa', 'count'),
            rain_sum=('rain_mm', 'sum'), rain_count=('rain_mm', 'count'),
            solar_sum=('solar', 'sum'), solar_count=('solar', 'count'),
            hum_sum=('hum', 'sum'), hum_count=('hum', 'count'), hum_min=('hum', 'min'), hum_max=('hum', 'max'),
            windspd_sum=('windspd', 'sum'), windspd_count=('windspd', 'count'), windspd_max=('windspd', 'max'),
            winddir_sum=('winddir', 'sum'), winddir_count=('winddir', 'count'),
            total_records=('temp_c', 'size')
        ).reset_index()
        
        for row in agg_chunk.itertuples(index=False):
            key = (row.stnname, row.date)
            if key not in daily_data:
                daily_data[key] = {
                    'stnname': row.stnname, 'date': row.date,
                    'temp_sum': row.temp_sum, 'temp_cnt': row.temp_count, 'temp_min': row.temp_min, 'temp_max': row.temp_max,
                    'bar_sum': row.bar_sum, 'bar_cnt': row.bar_count,
                    'rain_sum': row.rain_sum, 'rain_cnt': row.rain_count,
                    'solar_sum': row.solar_sum, 'solar_cnt': row.solar_count,
                    'hum_sum': row.hum_sum, 'hum_cnt': row.hum_count, 'hum_min': row.hum_min, 'hum_max': row.hum_max,
                    'windspd_sum': row.windspd_sum, 'windspd_cnt': row.windspd_count, 'windspd_max': row.windspd_max,
                    'winddir_sum': row.winddir_sum, 'winddir_cnt': row.winddir_count,
                    'total_records': row.total_records
                }
            else:
                d = daily_data[key]
                d['temp_sum'] += row.temp_sum
                d['temp_cnt'] += row.temp_count
                if not np.isnan(row.temp_min):
                    d['temp_min'] = min(d['temp_min'], row.temp_min) if not np.isnan(d['temp_min']) else row.temp_min
                if not np.isnan(row.temp_max):
                    d['temp_max'] = max(d['temp_max'], row.temp_max) if not np.isnan(d['temp_max']) else row.temp_max
                d['bar_sum'] += row.bar_sum
                d['bar_cnt'] += row.bar_count
                d['rain_sum'] += row.rain_sum
                d['rain_cnt'] += row.rain_count
                d['solar_sum'] += row.solar_sum
                d['solar_cnt'] += row.solar_count
                d['hum_sum'] += row.hum_sum
                d['hum_cnt'] += row.hum_count
                if not np.isnan(row.hum_min):
                    d['hum_min'] = min(d['hum_min'], row.hum_min) if not np.isnan(d['hum_min']) else row.hum_min
                if not np.isnan(row.hum_max):
                    d['hum_max'] = max(d['hum_max'], row.hum_max) if not np.isnan(d['hum_max']) else row.hum_max
                d['windspd_sum'] += row.windspd_sum
                d['windspd_cnt'] += row.windspd_count
                if not np.isnan(row.windspd_max):
                    d['windspd_max'] = max(d['windspd_max'], row.windspd_max) if not np.isnan(d['windspd_max']) else row.windspd_max
                d['winddir_sum'] += row.winddir_sum
                d['winddir_cnt'] += row.winddir_count
                d['total_records'] += row.total_records

        if chunk_count % 5 == 0:
            print(f"  Progress: {total_raw_rows:,} raw rows processed ({time.time() - start_time:.1f}s)...")

    # 5. Konstruksi Output DataFrame Harian
    print("Compiling final daily dataframe with Cardinal Wind Directions...")
    daily_list = []
    for (stn, dt_str), d in daily_data.items():
        temp_mean = d['temp_sum'] / d['temp_cnt'] if d['temp_cnt'] > 0 else np.nan
        bar_mean = d['bar_sum'] / d['bar_cnt'] if d['bar_cnt'] > 0 else np.nan
        hum_mean = d['hum_sum'] / d['hum_cnt'] if d['hum_cnt'] > 0 else np.nan
        windspd_mean = d['windspd_sum'] / d['windspd_cnt'] if d['windspd_cnt'] > 0 else np.nan
        winddir_mean = d['winddir_sum'] / d['winddir_cnt'] if d['winddir_cnt'] > 0 else np.nan
        
        rain_tot = min(300.0, d['rain_sum']) if d['rain_cnt'] > 0 and d['rain_sum'] <= 350.0 else (np.nan if d['rain_cnt'] == 0 else min(300.0, d['rain_sum']))
        solar_tot = d['solar_sum'] if d['solar_cnt'] > 0 else np.nan
        
        # Kategorisasi Arah Angin (Notulen Poin 4)
        if np.isnan(winddir_mean):
            wind_dir_name = '---'
        elif winddir_mean > 315:
            wind_dir_name = 'Utara'
        elif winddir_mean > 225:
            wind_dir_name = 'Barat'
        elif winddir_mean > 135:
            wind_dir_name = 'Selatan'
        elif winddir_mean > 45:
            wind_dir_name = 'Timur'
        elif winddir_mean >= 0:
            wind_dir_name = 'Utara'
        else:
            wind_dir_name = '---'
            
        daily_list.append({
            'stnname': stn,
            'date': dt_str,
            'temp_avg': round(temp_mean, 2) if not np.isnan(temp_mean) else np.nan,
            'temp_min': round(d['temp_min'], 2) if not np.isnan(d['temp_min']) else np.nan,
            'temp_max': round(d['temp_max'], 2) if not np.isnan(d['temp_max']) else np.nan,
            'humidity_avg': round(hum_mean, 2) if not np.isnan(hum_mean) else np.nan,
            'humidity_min': round(d['hum_min'], 2) if not np.isnan(d['hum_min']) else np.nan,
            'humidity_max': round(d['hum_max'], 2) if not np.isnan(d['hum_max']) else np.nan,
            'pressure_avg_hpa': round(bar_mean, 2) if not np.isnan(bar_mean) else np.nan,
            'rainfall_total_mm': round(min(300.0, rain_tot), 2) if (not np.isnan(rain_tot) and rain_tot <= 500) else np.nan,
            'solar_radiation_total': round(solar_tot, 2) if not np.isnan(solar_tot) else np.nan,
            'wind_speed_avg': round(windspd_mean, 2) if not np.isnan(windspd_mean) else np.nan,
            'wind_speed_max': round(d['windspd_max'], 2) if not np.isnan(d['windspd_max']) else np.nan,
            'wind_direction_deg': round(winddir_mean, 1) if not np.isnan(winddir_mean) else np.nan,
            'wind_direction_name': wind_dir_name,
            'records_count': d['total_records']
        })

    df_daily = pd.DataFrame(daily_list).sort_values(['stnname', 'date']).reset_index(drop=True)
    df_daily.to_csv(output_daily_csv, index=False)
    print(f"SUCCESS: Saved {len(df_daily):,} station-days to {output_daily_csv} ({os.path.getsize(output_daily_csv):,} bytes)")
    print(f"Pipeline completed in {time.time() - start_time:.2f} seconds.")
    return df_daily

if __name__ == '__main__':
    run_nusaklim_pipeline()
