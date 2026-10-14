# ==============================================================================
# FIGURES ARAH MATA ANGIN UNTUK LAPORAN 3 (Aktual vs Prediksi NusaKlim saja):
#   (a) deret waktu harian H+1 pada 30 hari data uji, 10 stasiun
#   (b) trajektori ramalan H+1 s/d H+7 vs realisasi, 5 stasiun
# Memakai model produksi (weather_model_latest.joblib) dan daftar stasiun yang sama
# dengan Gambar 7 dan Gambar 8 (fig_model3_stations.json, fig_merged4_stations.json).
# ==============================================================================
import os
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker

plt.rcParams['font.family'] = 'DejaVu Sans'

BASE_DIR = r"D:\Projects\Kodepanda\Nusaklim\nusaklim"
FIG_MODEL = os.path.join(BASE_DIR, "figures_model")
FIG_BENCH = os.path.join(BASE_DIR, "figures_benchmark")

from retrain_pipeline import build_features_and_targets, DATA_PATH

KEY = 'wind_direction_name'
CARD = ['Utara', 'Timur', 'Selatan', 'Barat']  # sumbu y: Barat di atas, Utara di bawah
YMAP = {c: i for i, c in enumerate(CARD)}
COL_ACT, COL_NK = '#0F172A', '#059669'

bundle = joblib.load(os.path.join(BASE_DIR, "models", "weather_model_latest.joblib"))
feature_cols, target_cols = bundle['feature_cols'], bundle['target_cols']
models, algo_used = bundle['models'], bundle['algo_used']

df_featured, _, _, _ = build_features_and_targets(pd.read_csv(DATA_PATH))
max_date = df_featured['date_dt'].max()
split_date = max_date - pd.Timedelta(days=30)
test_df = df_featured[df_featured['date_dt'] > split_date]
period = f"{(split_date + pd.Timedelta(days=1)).date()} s/d {max_date.date()}"


def style_axis(ax):
    ax.set_yticks(range(len(CARD)))
    ax.set_yticklabels(CARD, fontsize=8)
    ax.set_ylim(-0.6, len(CARD) - 0.4)
    ax.grid(True, linestyle=':', alpha=0.6)


# ------------------------------------------------------------------------------
# (a) Deret waktu 30 hari uji, H+1
# ------------------------------------------------------------------------------
with open(os.path.join(FIG_MODEL, 'fig_model3_stations.json'), encoding='utf-8') as f:
    stations = json.load(f)['station_ids']

fig, axes = plt.subplots(5, 2, figsize=(14, 17))
axes = axes.flatten()
target_col = target_cols[f'{KEY}_h1']
for ax, stn in zip(axes, stations):
    d = test_df[test_df['stnname'].astype(str) == stn].sort_values('date_dt')
    d = d.dropna(subset=feature_cols + [target_col])
    pred = pd.Series(models[f'{KEY}_h1'].predict(d[feature_cols]), index=d.index).astype(str)
    act = d[target_col].astype(str)
    acc = float((pred == act).mean()) if len(d) else float('nan')
    t_dates = d['date_dt'] + pd.Timedelta(days=1)  # tanggal yang diramal (target H+1), bukan tanggal baris fitur
    ax.plot(t_dates, act.map(YMAP), 'o', color=COL_ACT, markersize=8, label='Aktual AWS')
    ax.plot(t_dates, pred.map(YMAP), '^', color=COL_NK, markersize=5.5,
            label=f'NusaKlim (Accuracy {acc * 100:.0f}%)')
    style_axis(ax)
    ax.set_title(f'Stasiun AWS {stn} ({len(d)} hari uji)', fontsize=10, fontweight='bold')
    ax.xaxis.set_major_locator(mticker.FixedLocator(mdates.date2num(list(pd.date_range(end=max_date, periods=8, freq='4D')))))  # tick terakhir = max_date
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    ax.tick_params(axis='x', labelsize=8)
    ax.legend(fontsize=7.5, loc='lower left')
    print(f'  [{stn}] n={len(d)} acc={acc:.3f}')
fig.suptitle(f'Deret Waktu Harian Arah Mata Angin: Aktual vs Prediksi NusaKlim (H+1), 10 Stasiun, {period}',
             fontsize=12.5, fontweight='bold', color='#1E3A8A')
fig.tight_layout(rect=[0, 0, 1, 0.975])
p_a = os.path.join(FIG_MODEL, 'fig_model3b_winddir_timeseries.png')
fig.savefig(p_a, dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('saved', p_a)

# ------------------------------------------------------------------------------
# (b) Trajektori H+1 s/d H+7 dari satu titik ramal
# ------------------------------------------------------------------------------
with open(os.path.join(FIG_BENCH, 'fig_merged4_stations.json'), encoding='utf-8') as f:
    meta = json.load(f)
issue_date = pd.Timestamp(meta['issue_date'])
stations_t = meta['station_ids']

fig, axes = plt.subplots(3, 2, figsize=(14, 11))
axes = axes.flatten()
hs = list(range(1, 8))
for ax, stn in zip(axes, stations_t):
    d = df_featured[df_featured['stnname'].astype(str) == stn].sort_values('date_dt')
    row = d[d['date_dt'] == issue_date]
    if row.empty:
        ax.set_visible(False)
        continue
    X = row[feature_cols]
    preds = [str(models[f'{KEY}_h{h}'].predict(X)[0]) for h in hs]
    acts = []
    for h in hs:
        r = d[d['date_dt'] == issue_date + pd.Timedelta(days=h)]
        acts.append(r[KEY].values[0] if not r.empty and isinstance(r[KEY].values[0], str) else None)
    valid = [(a, p) for a, p in zip(acts, preds) if a is not None]
    acc = np.mean([a == p for a, p in valid]) if valid else float('nan')
    ax.plot(hs, [YMAP.get(a, np.nan) for a in acts], 'o', color=COL_ACT, markersize=9, label='Aktual AWS')
    ax.plot(hs, [YMAP[p] for p in preds], '^', color=COL_NK, markersize=6,
            label=f'NusaKlim (benar {sum(a == p for a, p in valid)}/{len(valid)} hari)')
    style_axis(ax)
    ax.set_xticks(hs)
    ax.set_xticklabels([f'H+{h}\n{(issue_date + pd.Timedelta(days=h)):%d-%m}' for h in hs], fontsize=8)
    ax.set_title(f'Stasiun AWS {stn}', fontsize=10, fontweight='bold')
    ax.legend(fontsize=7.5, loc='lower left')
    print(f'  [{stn}] traj acc={acc:.3f}')
for ax in axes[len(stations_t):]:
    ax.set_visible(False)
fig.suptitle(f'Trajektori Ramalan Arah Mata Angin H+1 s/d H+7 vs Realisasi Aktual (Titik Ramal: {issue_date.date()})',
             fontsize=12.5, fontweight='bold', color='#1E3A8A')
fig.tight_layout(rect=[0, 0, 1, 0.97])
p_b = os.path.join(FIG_BENCH, 'fig_merged4b_winddir_trajectory.png')
fig.savefig(p_b, dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('saved', p_b)
