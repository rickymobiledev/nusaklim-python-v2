import os
import sys
import json
import time
import requests
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Paths
BASE_DIR = r"D:\Projects\Kodepanda\Nusaklim\nusaklim"
daily_csv = os.path.join(BASE_DIR, "nusaklim_daily_aggregated.csv")
device_csv = os.path.join(BASE_DIR, "device_nusaklim.csv")
model_bundle_path = os.path.join(BASE_DIR, "models", "weather_model_latest.joblib")
fig_dir = os.path.join(BASE_DIR, "figures")
os.makedirs(fig_dir, exist_ok=True)

sys.path.insert(0, BASE_DIR)
from retrain_pipeline import build_features_and_targets

print("=== OPEN-METEO API INTEGRATION & BENCHMARKING (REAL STATIONS) ===")

# ------------------------------------------------------------------------------
# 1. Real reference stations, resolved from device_nusaklim.csv (no placeholders)
#    Chosen for full data coverage across the model's official blind-test window
#    and geographic diversity across the plantation network.
# ------------------------------------------------------------------------------
device = pd.read_csv(device_csv)
device['id_str'] = device['id'].astype(str)
device_idx = device.set_index('id_str')

TEST_STATION_IDS = ['222', '2179', '248', '267']
PRIMARY_STATION = '222'

test_stations = {}
for sid in TEST_STATION_IDS:
    row = device_idx.loc[sid]
    test_stations[sid] = {
        'name': row['name'],
        'lat': float(row['latitude']),
        'lon': float(row['longitude']),
        'company': row['company_name'],
    }
    print(f"Resolved Station {sid}: {row['name']} @ ({row['latitude']}, {row['longitude']}) - {row['company_name']}")

# ------------------------------------------------------------------------------
# 2. Evaluation window = the model's own documented Out-Of-Time blind-test split
#    (last 30 days of the aggregated dataset), so this comparison uses the exact
#    same real, dated period cited elsewhere in the reports.
# ------------------------------------------------------------------------------
df = pd.read_csv(daily_csv)
df['date_dt'] = pd.to_datetime(df['date'])
df = df.sort_values(['stnname', 'date_dt']).reset_index(drop=True)

max_date = df['date_dt'].max()
start_date = (max_date - pd.Timedelta(days=29)).strftime('%Y-%m-%d')
end_date = max_date.strftime('%Y-%m-%d')
print(f"Evaluation window (matches model blind-test split): {start_date} to {end_date}")

# ------------------------------------------------------------------------------
# 3. Rebuild the EXACT feature set used to train weather_model_latest.joblib, via
#    retrain_pipeline.build_features_and_targets() - the single source of truth
#    for feature engineering (29 fitur, lag 1/3/7, no hum_deficit) -
#    instead of a separate hand-rolled reconstruction that can silently drift out
#    of sync with the production pipeline (as the previous version of this script
#    had: it still referenced the old 36-feature/lag-1-2-3-7 design and old model
#    keys rh_avg_h1/rain_mm_h1, which no longer exist in the current bundle).
# ------------------------------------------------------------------------------
bundle = joblib.load(model_bundle_path)
feature_cols = bundle['feature_cols']
models = bundle['models']
algo_used = bundle['algo_used']

df, built_cols, target_cols, _ = build_features_and_targets(df)
assert built_cols == feature_cols, "Feature set mismatch vs weather_model_latest.joblib - model perlu di-retrain ulang."

# NusaKlim H+1 predictions: feature row on day (d-1) predicts day d.
df_feat = df.dropna(subset=feature_cols).copy()
df_feat['pred_date'] = df_feat['date_dt'] + pd.Timedelta(days=1)
X_all = df_feat[feature_cols]
df_feat['nk_pred_temp'] = models['temp_avg_h1'].predict(X_all)
df_feat['nk_pred_rh'] = models['humidity_avg_h1'].predict(X_all)
df_feat['nk_pred_rain'] = np.clip(models['rainfall_total_mm_h1'].predict(X_all), 0, None)

nk_preds = df_feat[['stnname', 'pred_date', 'nk_pred_temp', 'nk_pred_rh', 'nk_pred_rain']].rename(
    columns={'pred_date': 'date'}
)

# ------------------------------------------------------------------------------
# 4. Fetch real Open-Meteo Historical Archive data for each station's true coords
# ------------------------------------------------------------------------------
print(f"Fetching Open-Meteo Historical Archive ({start_date} to {end_date}) for {len(test_stations)} real stations...")
openmeteo_results = {}
for stn_id, meta in test_stations.items():
    print(f"-> Calling Open-Meteo for Station {stn_id} ({meta['name']}) [Lat {meta['lat']}, Lon {meta['lon']}]...")
    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={meta['lat']}&longitude={meta['lon']}&"
        f"start_date={start_date}&end_date={end_date}&"
        f"daily=temperature_2m_mean,relative_humidity_2m_mean,precipitation_sum&"
        f"timezone=Asia%2FJakarta"
    )
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            data = resp.json().get('daily', {})
            df_om = pd.DataFrame(data)
            df_om['date'] = pd.to_datetime(df_om['time'])
            df_om['stnname'] = int(stn_id)
            openmeteo_results[stn_id] = df_om
            print(f"   Success! Received {len(df_om)} days from Open-Meteo.")
        else:
            print(f"   Warning: Open-Meteo returned HTTP {resp.status_code}")
    except Exception as e:
        print(f"   Error calling Open-Meteo: {e}")
    time.sleep(0.5)

# ------------------------------------------------------------------------------
# 5. Compute REAL error metrics per station (ground truth vs Open-Meteo vs NusaKlim)
# ------------------------------------------------------------------------------
station_results = {}
merged_by_station = {}

for stn_id, meta in test_stations.items():
    sid_int = int(stn_id)
    df_actual = df[(df['stnname'] == sid_int) & (df['date_dt'] >= start_date) & (df['date_dt'] <= end_date)].copy()
    if stn_id not in openmeteo_results or df_actual.empty:
        print(f"Skipping Station {stn_id}: missing ground truth or Open-Meteo data.")
        continue

    df_om = openmeteo_results[stn_id]
    df_nk = nk_preds[nk_preds['stnname'] == sid_int]

    merged = df_actual.merge(df_om, left_on='date_dt', right_on='date', suffixes=('', '_om'))
    merged = merged.merge(df_nk, left_on='date_dt', right_on='date', suffixes=('', '_nk'))
    merged_by_station[stn_id] = merged

    mae_temp_om = mean_absolute_error(merged['temp_avg'], merged['temperature_2m_mean'])
    rmse_temp_om = np.sqrt(mean_squared_error(merged['temp_avg'], merged['temperature_2m_mean']))
    bias_temp_om = (merged['temperature_2m_mean'] - merged['temp_avg']).mean()
    mae_rh_om = mean_absolute_error(merged['humidity_avg'], merged['relative_humidity_2m_mean'])
    mae_rain_om = mean_absolute_error(merged['rainfall_total_mm'], merged['precipitation_sum'])

    mae_temp_nk = mean_absolute_error(merged['temp_avg'], merged['nk_pred_temp'])
    rmse_temp_nk = np.sqrt(mean_squared_error(merged['temp_avg'], merged['nk_pred_temp']))
    bias_temp_nk = (merged['nk_pred_temp'] - merged['temp_avg']).mean()
    mae_rh_nk = mean_absolute_error(merged['humidity_avg'], merged['nk_pred_rh'])
    mae_rain_nk = mean_absolute_error(merged['rainfall_total_mm'], merged['nk_pred_rain'])

    station_results[stn_id] = {
        'station_name': meta['name'],
        'company': meta['company'],
        'lat': meta['lat'],
        'lon': meta['lon'],
        'n_days_matched': int(len(merged)),
        'open_meteo': {
            'temp_mae': round(float(mae_temp_om), 3),
            'temp_rmse': round(float(rmse_temp_om), 3),
            'temp_bias': round(float(bias_temp_om), 3),
            'humidity_mae': round(float(mae_rh_om), 3),
            'rainfall_mae': round(float(mae_rain_om), 3),
        },
        'nusaklim_ai': {
            'temp_mae': round(float(mae_temp_nk), 3),
            'temp_rmse': round(float(rmse_temp_nk), 3),
            'temp_bias': round(float(bias_temp_nk), 3),
            'humidity_mae': round(float(mae_rh_nk), 3),
            'rainfall_mae': round(float(mae_rain_nk), 3),
        },
    }
    print(f"Station {stn_id} ({meta['name']}): OM Temp MAE={mae_temp_om:.2f}C | NusaKlim Temp MAE={mae_temp_nk:.2f}C "
          f"(n={len(merged)} matched days)")

if not station_results:
    raise RuntimeError("No station produced matched Open-Meteo + ground-truth + model-prediction data.")

avg_temp_mae_om = float(np.mean([v['open_meteo']['temp_mae'] for v in station_results.values()]))
avg_temp_rmse_om = float(np.mean([v['open_meteo']['temp_rmse'] for v in station_results.values()]))
avg_temp_bias_om = float(np.mean([v['open_meteo']['temp_bias'] for v in station_results.values()]))
avg_hum_mae_om = float(np.mean([v['open_meteo']['humidity_mae'] for v in station_results.values()]))
avg_rain_mae_om = float(np.mean([v['open_meteo']['rainfall_mae'] for v in station_results.values()]))

avg_temp_mae_nk = float(np.mean([v['nusaklim_ai']['temp_mae'] for v in station_results.values()]))
avg_temp_rmse_nk = float(np.mean([v['nusaklim_ai']['temp_rmse'] for v in station_results.values()]))
avg_temp_bias_nk = float(np.mean([v['nusaklim_ai']['temp_bias'] for v in station_results.values()]))
avg_hum_mae_nk = float(np.mean([v['nusaklim_ai']['humidity_mae'] for v in station_results.values()]))
avg_rain_mae_nk = float(np.mean([v['nusaklim_ai']['rainfall_mae'] for v in station_results.values()]))

print("\n=======================================================")
print(f"HEAD-TO-HEAD BENCHMARK AVERAGES ({len(station_results)} real stations, {start_date} to {end_date})")
print("=======================================================")
print(f"OPEN-METEO   -> Temp MAE {avg_temp_mae_om:.2f}C | RH MAE {avg_hum_mae_om:.2f}% | Rain MAE {avg_rain_mae_om:.2f}mm")
print(f"NUSAKLIM AI  -> Temp MAE {avg_temp_mae_nk:.2f}C | RH MAE {avg_hum_mae_nk:.2f}% | Rain MAE {avg_rain_mae_nk:.2f}mm")

# ------------------------------------------------------------------------------
# 6. Figures: (a) multi-station bar comparison, (b) primary-station time series
# ------------------------------------------------------------------------------
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.family'] = 'DejaVu Sans'

stn_ids = list(station_results.keys())
stn_labels = [f"{sid}\n{station_results[sid]['station_name']}" for sid in stn_ids]
om_temp_mae = [station_results[s]['open_meteo']['temp_mae'] for s in stn_ids]
nk_temp_mae = [station_results[s]['nusaklim_ai']['temp_mae'] for s in stn_ids]
om_hum_mae = [station_results[s]['open_meteo']['humidity_mae'] for s in stn_ids]
nk_hum_mae = [station_results[s]['nusaklim_ai']['humidity_mae'] for s in stn_ids]

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)
x = np.arange(len(stn_ids))
width = 0.35

axes[0].bar(x - width / 2, om_temp_mae, width, label='Open-Meteo Global API', color='#2563EB')
axes[0].bar(x + width / 2, nk_temp_mae, width, label='NusaKlim Local AI', color='#059669')
axes[0].set_xticks(x)
axes[0].set_xticklabels(stn_labels, fontsize=8)
axes[0].set_ylabel('Suhu MAE (°C)', fontweight='bold')
axes[0].set_title('Error Suhu per Stasiun', fontweight='bold')
axes[0].legend(fontsize=8)
axes[0].grid(True, linestyle=':', alpha=0.6)

axes[1].bar(x - width / 2, om_hum_mae, width, label='Open-Meteo Global API', color='#2563EB')
axes[1].bar(x + width / 2, nk_hum_mae, width, label='NusaKlim Local AI', color='#059669')
axes[1].set_xticks(x)
axes[1].set_xticklabels(stn_labels, fontsize=8)
axes[1].set_ylabel('Kelembapan MAE (%)', fontweight='bold')
axes[1].set_title('Error Kelembapan per Stasiun', fontweight='bold')
axes[1].legend(fontsize=8)
axes[1].grid(True, linestyle=':', alpha=0.6)

fig.suptitle(f'Komparasi Error Open-Meteo vs NusaKlim Local AI — {len(stn_ids)} Stasiun Riil ({start_date} s/d {end_date})',
             fontsize=12, fontweight='bold', color='#1E3A8A')
plt.tight_layout()
bar_fig_path = os.path.join(fig_dir, "fig_openmeteo_multi_station_bar.png")
plt.savefig(bar_fig_path)
plt.close()
print(f"Saved multi-station bar figure: {bar_fig_path}")

if PRIMARY_STATION in merged_by_station:
    m = merged_by_station[PRIMARY_STATION].sort_values('date_dt')
    meta = test_stations[PRIMARY_STATION]
    r = station_results[PRIMARY_STATION]
    plt.figure(figsize=(14, 6), dpi=300)
    plt.plot(m['date_dt'], m['temp_avg'], label='Ground Truth Aktual AWS PPKS', color='#0F172A', linewidth=2.2, marker='o', markersize=4)
    plt.plot(m['date_dt'], m['temperature_2m_mean'],
              label=f"Open-Meteo Global API (MAE: {r['open_meteo']['temp_mae']:.2f}°C, Bias: {r['open_meteo']['temp_bias']:+.2f}°C)",
              color='#2563EB', linewidth=1.8, linestyle='--', marker='s', markersize=3)
    plt.plot(m['date_dt'], m['nk_pred_temp'],
              label=f"NusaKlim PPKS {algo_used['temp_avg_h1'].split(' (')[0]} H+1 (MAE: {r['nusaklim_ai']['temp_mae']:.2f}°C, Bias: {r['nusaklim_ai']['temp_bias']:+.2f}°C)",
              color='#059669', linewidth=2.0, marker='^', markersize=3)
    plt.title(f"Komparasi Ground-Truth AWS PPKS vs Open-Meteo Global API vs NusaKlim Local AI\n"
              f"Stasiun {PRIMARY_STATION} ({meta['name']}, {meta['company']})",
              fontsize=13, fontweight='bold', pad=12, color='#1E3A8A')
    plt.xlabel('Tanggal Observasi', fontsize=11, fontweight='bold')
    plt.ylabel('Suhu Rata-rata Udara (°C)', fontsize=11, fontweight='bold')
    plt.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=10, loc='upper right')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    ts_fig_path = os.path.join(fig_dir, "fig_openmeteo_comparison.png")
    plt.savefig(ts_fig_path)
    plt.close()
    print(f"Saved primary-station comparison figure: {ts_fig_path}")

# ------------------------------------------------------------------------------
# 7. Persist summary JSON (per-station + national average) for the report
# ------------------------------------------------------------------------------
summary = {
    'evaluation_period': f'{start_date} to {end_date}',
    'primary_station': PRIMARY_STATION,
    'stations_evaluated': len(station_results),
    'algo_used': {
        'temp_avg': algo_used['temp_avg_h1'],
        'humidity_avg': algo_used['humidity_avg_h1'],
        'rainfall_total_mm': algo_used['rainfall_total_mm_h1'],
    },
    'station_results': station_results,
    'open_meteo_metrics': {
        'avg_temp_mae': round(avg_temp_mae_om, 3),
        'avg_temp_rmse': round(avg_temp_rmse_om, 3),
        'avg_temp_bias': round(avg_temp_bias_om, 3),
        'avg_humidity_mae': round(avg_hum_mae_om, 3),
        'avg_rainfall_mae': round(avg_rain_mae_om, 3),
    },
    'nusaklim_local_ai_metrics': {
        'avg_temp_mae': round(avg_temp_mae_nk, 3),
        'avg_temp_rmse': round(avg_temp_rmse_nk, 3),
        'avg_temp_bias': round(avg_temp_bias_nk, 3),
        'avg_humidity_mae': round(avg_hum_mae_nk, 3),
        'avg_rainfall_mae': round(avg_rain_mae_nk, 3),
    },
}
with open(os.path.join(BASE_DIR, "openmeteo_benchmark_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
print("Saved benchmark summary to openmeteo_benchmark_summary.json")
print("\n[SUCCESS] Open-Meteo API Benchmark Complete (real stations, real model inference)!")
