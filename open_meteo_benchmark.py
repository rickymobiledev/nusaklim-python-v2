import os
import sys
import json
import time
import requests
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Paths
BASE_DIR = r"D:\Projects\Kodepanda\Nusaklim\nusaklim"
daily_csv = os.path.join(BASE_DIR, "nusaklim_daily_aggregated.csv")
device_csv = os.path.join(BASE_DIR, "device_nusaklim.csv")
model_bundle_path = os.path.join(BASE_DIR, "models", "weather_model_latest.joblib")
fig_dir = os.path.join(BASE_DIR, "figures")
os.makedirs(fig_dir, exist_ok=True)

sys.path.insert(0, BASE_DIR)
from retrain_pipeline import build_features_and_targets

print("=== OPEN-METEO API INTEGRATION & BENCHMARKING (REAL STATIONS, 7 INDIKATOR) ===")

# ------------------------------------------------------------------------------
# 1. Real reference stations, resolved from device_nusaklim.csv (no placeholders)
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
#    (last 30 days of the aggregated dataset).
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
#    retrain_pipeline.build_features_and_targets() (single source of truth).
# ------------------------------------------------------------------------------
bundle = joblib.load(model_bundle_path)
feature_cols = bundle['feature_cols']
models = bundle['models']
algo_used = bundle['algo_used']

df, built_cols, target_cols, _ = build_features_and_targets(df)
assert built_cols == feature_cols, "Feature set mismatch vs weather_model_latest.joblib - model perlu di-retrain ulang."

# ------------------------------------------------------------------------------
# 3b. Definisi 7 indikator: kolom data aktual AWS, kunci model NusaKlim (H+1), dan
#     padanan Open-Meteo (agregasi harian dari data per jam, zona waktu WIB).
# ------------------------------------------------------------------------------
INDICATORS = [
    # (kunci, label, satuan, kolom aktual AWS, kolom Open-Meteo harian)
    ('temp_avg', 'Suhu Rata-rata', '°C', 'temp_avg', 'om_temp'),
    ('humidity_avg', 'Kelembapan', '%', 'humidity_avg', 'om_rh'),
    ('rainfall_total_mm', 'Curah Hujan', 'mm', 'rainfall_total_mm', 'om_rain'),
    ('solar_radiation_avg', 'Radiasi Matahari', 'W/m²', 'solar_radiation_avg', 'om_solar'),
    ('pressure_avg_hpa', 'Tekanan Udara', 'hPa', 'pressure_avg_hpa', 'om_pressure'),
    ('wind_speed_avg', 'Kecepatan Angin', 'km/h', 'wind_speed_avg', 'om_wind'),
    ('wind_direction_name', 'Arah Mata Angin', 'kategori', 'wind_direction_name', 'om_winddir_cat'),
]
CLF_KEY = 'wind_direction_name'

# NusaKlim H+1: baris fitur pada hari (d-1) memprediksi hari d, untuk SEMUA 7 indikator.
df_feat = df.dropna(subset=feature_cols).copy()
df_feat['pred_date'] = df_feat['date_dt'] + pd.Timedelta(days=1)
X_all = df_feat[feature_cols]
for key, *_ in INDICATORS:
    pred = models[f'{key}_h1'].predict(X_all)
    if key == CLF_KEY:
        df_feat[f'nk_{key}'] = pd.Series(pred, index=df_feat.index).astype(str)
    else:
        pred = np.asarray(pred, dtype=float)
        if key in ('rainfall_total_mm', 'solar_radiation_avg', 'wind_speed_avg'):
            pred = np.clip(pred, 0, None)
        if key == 'humidity_avg':
            pred = np.clip(pred, 0, 100)
        df_feat[f'nk_{key}'] = pred

nk_cols = [f'nk_{k}' for k, *_ in INDICATORS]
nk_preds = df_feat[['stnname', 'pred_date'] + nk_cols].rename(columns={'pred_date': 'date_dt'})


def deg_to_cardinal(deg):
    """Kategorisasi identik dengan process_nusaklim.py (data aktual AWS)."""
    if deg is None or np.isnan(deg):
        return np.nan
    if deg > 315:
        return 'Utara'
    if deg > 225:
        return 'Barat'
    if deg > 135:
        return 'Selatan'
    if deg > 45:
        return 'Timur'
    return 'Utara'


# ------------------------------------------------------------------------------
# 4. Ambil data peramalan Open-Meteo (Historical Forecast API) per jam, agregasi harian
# ------------------------------------------------------------------------------
HOURLY = ('temperature_2m,relative_humidity_2m,precipitation,shortwave_radiation,'
          'surface_pressure,wind_speed_10m,wind_direction_10m')


def fetch_open_meteo(lat, lon):
    last_err = None
    for base in ('https://historical-forecast-api.open-meteo.com/v1/forecast',
                 'https://archive-api.open-meteo.com/v1/archive'):
        try:
            resp = requests.get(base, params=dict(latitude=lat, longitude=lon, start_date=start_date,
                                                  end_date=end_date, hourly=HOURLY, timezone='Asia/Jakarta'),
                                timeout=40)
            if resp.status_code == 200:
                h = pd.DataFrame(resp.json()['hourly'])
                h['time'] = pd.to_datetime(h['time'])
                h['date_dt'] = h['time'].dt.normalize()
                rad = np.deg2rad(h['wind_direction_10m'])
                h['u'] = -h['wind_speed_10m'] * np.sin(rad)
                h['v'] = -h['wind_speed_10m'] * np.cos(rad)
                g = h.groupby('date_dt')
                out = pd.DataFrame({
                    'om_temp': g['temperature_2m'].mean(),
                    'om_rh': g['relative_humidity_2m'].mean(),
                    'om_rain': g['precipitation'].sum(min_count=1),
                    'om_solar': g['shortwave_radiation'].mean(),
                    'om_pressure': g['surface_pressure'].mean(),
                    'om_wind': g['wind_speed_10m'].mean(),
                })
                mean_deg = (np.rad2deg(np.arctan2(-g['u'].mean(), -g['v'].mean())) + 360) % 360
                out['om_winddir_deg'] = mean_deg
                out['om_winddir_cat'] = mean_deg.map(deg_to_cardinal)
                return out.reset_index(), base
            last_err = f'HTTP {resp.status_code}'
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
    raise RuntimeError(f'Open-Meteo gagal untuk koordinat ({lat}, {lon}): {last_err}')


print(f"Fetching Open-Meteo ({start_date} to {end_date}) for {len(test_stations)} real stations...")
openmeteo_results = {}
om_source = None
for stn_id, meta in test_stations.items():
    print(f"-> Calling Open-Meteo for Station {stn_id} ({meta['name']}) [Lat {meta['lat']}, Lon {meta['lon']}]...")
    om_df, om_source = fetch_open_meteo(meta['lat'], meta['lon'])
    openmeteo_results[stn_id] = om_df
    print(f"   Success! {len(om_df)} days from {om_source}")
    time.sleep(0.5)

# ------------------------------------------------------------------------------
# 5. Hitung MAE (regresi) / Accuracy (arah angin) tiap indikator: Open-Meteo vs NusaKlim
#    terhadap data aktual AWS, per stasiun.
# ------------------------------------------------------------------------------
station_results = {}
merged_by_station = {}

for stn_id, meta in test_stations.items():
    sid_int = int(stn_id)
    df_actual = df[(df['stnname'] == sid_int) & (df['date_dt'] >= start_date) & (df['date_dt'] <= end_date)].copy()
    df_nk = nk_preds[nk_preds['stnname'] == sid_int].drop(columns='stnname')
    merged = df_actual.merge(openmeteo_results[stn_id], on='date_dt', how='inner').merge(df_nk, on='date_dt', how='inner')
    merged = merged.sort_values('date_dt')
    merged_by_station[stn_id] = merged

    ind_res = {}
    for key, label, unit, act_col, om_col in INDICATORS:
        nk_col = f'nk_{key}'
        sub = merged.dropna(subset=[act_col, om_col, nk_col])
        if key == CLF_KEY:
            acc_om = float((sub[om_col] == sub[act_col]).mean())
            acc_nk = float((sub[nk_col] == sub[act_col]).mean())
            ind_res[key] = {'label': label, 'unit': unit, 'metric': 'Accuracy', 'n': int(len(sub)),
                            'om': {'value': round(acc_om, 4)}, 'nk': {'value': round(acc_nk, 4)},
                            'winner': 'NusaKlim' if acc_nk > acc_om else ('Open-Meteo' if acc_om > acc_nk else 'Seri')}
        else:
            mae_om = float(mean_absolute_error(sub[act_col], sub[om_col]))
            mae_nk = float(mean_absolute_error(sub[act_col], sub[nk_col]))
            bias_om = float((sub[om_col] - sub[act_col]).mean())
            bias_nk = float((sub[nk_col] - sub[act_col]).mean())
            ind_res[key] = {'label': label, 'unit': unit, 'metric': 'MAE', 'n': int(len(sub)),
                            'om': {'value': round(mae_om, 3), 'bias': round(bias_om, 3)},
                            'nk': {'value': round(mae_nk, 3), 'bias': round(bias_nk, 3)},
                            'winner': 'NusaKlim' if mae_nk < mae_om else ('Open-Meteo' if mae_om < mae_nk else 'Seri')}

    t, h, r = ind_res['temp_avg'], ind_res['humidity_avg'], ind_res['rainfall_total_mm']
    station_results[stn_id] = {
        'station_name': meta['name'], 'company': meta['company'], 'lat': meta['lat'], 'lon': meta['lon'],
        'n_days_matched': int(len(merged)),
        'indicators': ind_res,
        # kunci lama (kompatibilitas API / laporan lain)
        'open_meteo': {'temp_mae': t['om']['value'],
                       'temp_rmse': round(float(np.sqrt(mean_squared_error(merged['temp_avg'], merged['om_temp']))), 3),
                       'temp_bias': t['om']['bias'], 'humidity_mae': h['om']['value'], 'rainfall_mae': r['om']['value']},
        'nusaklim_ai': {'temp_mae': t['nk']['value'],
                        'temp_rmse': round(float(np.sqrt(mean_squared_error(merged['temp_avg'], merged['nk_temp_avg']))), 3),
                        'temp_bias': t['nk']['bias'], 'humidity_mae': h['nk']['value'], 'rainfall_mae': r['nk']['value']},
    }
    print(f"\nStasiun {stn_id} ({meta['name']}), n={len(merged)} hari:")
    for key, label, unit, *_ in INDICATORS:
        x = ind_res[key]
        if x['metric'] == 'Accuracy':
            om_s, nk_s = f"{x['om']['value'] * 100:.1f}%", f"{x['nk']['value'] * 100:.1f}%"
        else:
            om_s, nk_s = f"{x['om']['value']:.3f}", f"{x['nk']['value']:.3f}"
        print(f"  {label:18s} {x['metric']:8s} OM={om_s}  NK={nk_s}  -> {x['winner']}")

if not station_results:
    raise RuntimeError("No station produced matched data.")

# Ringkasan lintas stasiun per indikator
indicator_summary = {}
for key, label, unit, *_ in INDICATORS:
    om_vals = [station_results[s]['indicators'][key]['om']['value'] for s in station_results]
    nk_vals = [station_results[s]['indicators'][key]['nk']['value'] for s in station_results]
    wins = [station_results[s]['indicators'][key]['winner'] for s in station_results]
    nk_better_avg = (np.mean(nk_vals) > np.mean(om_vals)) if key == CLF_KEY else (np.mean(nk_vals) < np.mean(om_vals))
    indicator_summary[key] = {
        'label': label, 'unit': unit, 'metric': 'Accuracy' if key == CLF_KEY else 'MAE',
        'om_avg': round(float(np.mean(om_vals)), 4), 'nk_avg': round(float(np.mean(nk_vals)), 4),
        'nk_wins': int(sum(w == 'NusaKlim' for w in wins)), 'om_wins': int(sum(w == 'Open-Meteo' for w in wins)),
        'ties': int(sum(w == 'Seri' for w in wins)), 'n_stations': len(wins),
        'winner_avg': 'NusaKlim' if nk_better_avg else 'Open-Meteo',
    }


def _avg(fn):
    return float(np.mean([fn(v) for v in station_results.values()]))


avg_temp_mae_om = _avg(lambda v: v['open_meteo']['temp_mae'])
avg_temp_mae_nk = _avg(lambda v: v['nusaklim_ai']['temp_mae'])
avg_temp_rmse_om = _avg(lambda v: v['open_meteo']['temp_rmse'])
avg_temp_rmse_nk = _avg(lambda v: v['nusaklim_ai']['temp_rmse'])
avg_temp_bias_om = _avg(lambda v: v['open_meteo']['temp_bias'])
avg_temp_bias_nk = _avg(lambda v: v['nusaklim_ai']['temp_bias'])
avg_hum_mae_om = _avg(lambda v: v['open_meteo']['humidity_mae'])
avg_hum_mae_nk = _avg(lambda v: v['nusaklim_ai']['humidity_mae'])
avg_rain_mae_om = _avg(lambda v: v['open_meteo']['rainfall_mae'])
avg_rain_mae_nk = _avg(lambda v: v['nusaklim_ai']['rainfall_mae'])

print("\n=== RINGKASAN LINTAS STASIUN ===")
for key, x in indicator_summary.items():
    print(f"{x['label']:18s} {x['metric']:8s} OM={x['om_avg']:.3f} NK={x['nk_avg']:.3f} | NK menang {x['nk_wins']}/{x['n_stations']} stasiun")

# ------------------------------------------------------------------------------
# 6. Gambar: (a) heatmap rasio error, (b) kurva deret waktu 7 indikator per stasiun
# ------------------------------------------------------------------------------
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.family'] = 'DejaVu Sans'

COL_ACT, COL_OM, COL_NK = '#0F172A', '#2563EB', '#059669'
stn_ids = list(station_results.keys())

# (a) Rasio error NusaKlim / Open-Meteo (MAE; untuk arah angin: laju salah = 1 - Accuracy)
ratio = np.zeros((len(INDICATORS), len(stn_ids)))
annot = [[''] * len(stn_ids) for _ in INDICATORS]
for j, sid in enumerate(stn_ids):
    for i, (key, label, unit, *_) in enumerate(INDICATORS):
        x = station_results[sid]['indicators'][key]
        if key == CLF_KEY:
            e_om, e_nk = 1 - x['om']['value'], 1 - x['nk']['value']
            annot[i][j] = f"OM {x['om']['value'] * 100:.0f}% | NK {x['nk']['value'] * 100:.0f}%"
        else:
            e_om, e_nk = x['om']['value'], x['nk']['value']
            annot[i][j] = f"OM {e_om:.2f} | NK {e_nk:.2f}"
        ratio[i, j] = e_nk / e_om if e_om > 0 else np.nan

fig, ax = plt.subplots(figsize=(11, 5.6), dpi=300)
im = ax.imshow(np.log2(np.clip(ratio, 0.25, 4)), cmap='RdYlGn_r', vmin=-2, vmax=2, aspect='auto')
ax.grid(False)
ax.set_xticks(range(len(stn_ids)))
ax.set_xticklabels([f"{s}\n{station_results[s]['station_name']}" for s in stn_ids], fontsize=8.5)
ax.set_yticks(range(len(INDICATORS)))
ax.set_yticklabels([f"{lbl} ({'Accuracy' if k == CLF_KEY else 'MAE'}, {u})" for k, lbl, u, *_ in INDICATORS], fontsize=8.5)
for i in range(len(INDICATORS)):
    for j in range(len(stn_ids)):
        ratio_txt = '×0 (tanpa salah)' if ratio[i, j] == 0 else f'×{ratio[i, j]:.2f}'
        ax.text(j, i, annot[i][j] + '\n' + ratio_txt, ha='center', va='center', fontsize=7.2, color='black')
cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
cb.set_ticks([-2, -1, 0, 1, 2])
cb.set_ticklabels(['0.25×', '0.5×', '1×', '2×', '4×'])
cb.set_label('Error NusaKlim ÷ Error Open-Meteo (hijau = NusaKlim lebih akurat)', fontsize=8)
ax.set_title(f'Error Prediksi 7 Indikator per Stasiun: NusaKlim (NK) vs Open-Meteo (OM) terhadap Data Aktual AWS\n{start_date} s/d {end_date}',
             fontsize=10.5, fontweight='bold', color='#1E3A8A')
plt.tight_layout()
heat_path = os.path.join(fig_dir, 'fig_openmeteo_ratio_heatmap.png')
plt.savefig(heat_path)
plt.close()
print(f'Saved heatmap: {heat_path}')

# (b) Kurva deret waktu: aktual vs Open-Meteo vs NusaKlim, 7 indikator, satu gambar per stasiun
CARD = ['Utara', 'Timur', 'Selatan', 'Barat']
for sid in stn_ids:
    m = merged_by_station[sid]
    meta = test_stations[sid]
    res = station_results[sid]['indicators']
    fig, axes = plt.subplots(4, 2, figsize=(13, 15), dpi=200)
    axes = axes.flatten()
    for ax, (key, label, unit, act_col, om_col) in zip(axes, INDICATORS):
        x = res[key]
        if key == CLF_KEY:
            ymap = {c: i for i, c in enumerate(CARD)}
            ax.plot(m['date_dt'], m[act_col].map(ymap), 'o', color=COL_ACT, markersize=7, label='Aktual AWS')
            ax.plot(m['date_dt'], m[om_col].map(ymap) + 0.12, 's', color=COL_OM, markersize=4.5,
                    label=f"Open-Meteo (Accuracy {x['om']['value'] * 100:.0f}%)")
            ax.plot(m['date_dt'], m[f'nk_{key}'].map(ymap) - 0.12, '^', color=COL_NK, markersize=4.5,
                    label=f"NusaKlim (Accuracy {x['nk']['value'] * 100:.0f}%)")
            ax.set_yticks(range(len(CARD)))
            ax.set_yticklabels(CARD)
            ax.set_ylim(-0.6, len(CARD) - 0.4)
        else:
            ax.plot(m['date_dt'], m[act_col], color=COL_ACT, linewidth=2.0, marker='o', markersize=3, label='Aktual AWS')
            ax.plot(m['date_dt'], m[om_col], color=COL_OM, linewidth=1.5, linestyle='--', marker='s', markersize=2.5,
                    label=f"Open-Meteo (MAE {x['om']['value']:.2f})")
            ax.plot(m['date_dt'], m[f'nk_{key}'], color=COL_NK, linewidth=1.6, marker='^', markersize=2.5,
                    label=f"NusaKlim (MAE {x['nk']['value']:.2f})")
            ax.set_ylabel(f'{label} ({unit})', fontsize=8.5)
        ax.set_title(f"{label} — lebih akurat: {x['winner']}", fontsize=9.5, fontweight='bold')
        ax.legend(fontsize=7, loc='best', frameon=True)
        ax.tick_params(axis='x', labelrotation=30, labelsize=7)
        ax.tick_params(axis='y', labelsize=7.5)
        ax.grid(True, linestyle=':', alpha=0.6)
    axes[-1].axis('off')
    axes[-1].text(0.02, 0.95,
                  f"Stasiun {sid} — {meta['name']}\n{meta['company']}\nPeriode {start_date} s/d {end_date}\n"
                  f"{station_results[sid]['n_days_matched']} hari data aktual\n\n"
                  "Hitam: data aktual AWS\nBiru putus-putus: Open-Meteo\nHijau: prediksi H+1 NusaKlim",
                  va='top', fontsize=9, color='#1E3A8A')
    fig.suptitle(f"Kurva Perbandingan Data Aktual AWS vs Open-Meteo vs Prediksi H+1 NusaKlim — Stasiun {sid} {meta['name']}",
                 fontsize=12, fontweight='bold', color='#1E3A8A', y=0.995)
    plt.tight_layout(rect=[0, 0, 1, 0.985])
    ts_path = os.path.join(fig_dir, f'fig_openmeteo_ts_{sid}.png')
    plt.savefig(ts_path)
    plt.close()
    print(f'Saved time-series figure: {ts_path}')

# ------------------------------------------------------------------------------
# 7. Simpan ringkasan JSON
# ------------------------------------------------------------------------------
summary = {
    'evaluation_period': f'{start_date} to {end_date}',
    'primary_station': PRIMARY_STATION,
    'stations_evaluated': len(station_results),
    'open_meteo_source': om_source,
    'algo_used': {k: algo_used[f'{k}_h1'] for k, *_ in INDICATORS},
    'indicator_summary': indicator_summary,
    'station_results': station_results,
    'open_meteo_metrics': {'avg_temp_mae': round(avg_temp_mae_om, 3), 'avg_temp_rmse': round(avg_temp_rmse_om, 3),
                           'avg_temp_bias': round(avg_temp_bias_om, 3), 'avg_humidity_mae': round(avg_hum_mae_om, 3),
                           'avg_rainfall_mae': round(avg_rain_mae_om, 3)},
    'nusaklim_local_ai_metrics': {'avg_temp_mae': round(avg_temp_mae_nk, 3), 'avg_temp_rmse': round(avg_temp_rmse_nk, 3),
                                  'avg_temp_bias': round(avg_temp_bias_nk, 3), 'avg_humidity_mae': round(avg_hum_mae_nk, 3),
                                  'avg_rainfall_mae': round(avg_rain_mae_nk, 3)},
}
with open(os.path.join(BASE_DIR, "openmeteo_benchmark_summary.json"), "w", encoding='utf-8') as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print("Saved benchmark summary to openmeteo_benchmark_summary.json")
print("\n[SUCCESS] Open-Meteo API Benchmark Complete (real stations, real model inference)!")
