# ==============================================================================
# FIGURES FOR THE MERGED LAPORAN 3+4 (ML vs DL comparison + H+1->H+7 trajectory
# showcase). Reads benchmark_merged_5algo_h1_h7.json (3 ML dari Laporan 3 + 2 DL
# baru dari run_dl_benchmark_h1_h7.py) and the production model bundle.
# ==============================================================================
import os
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'DejaVu Sans'

BASE_DIR = r"D:\Projects\Kodepanda\Nusaklim\nusaklim"
FIG_DIR = os.path.join(BASE_DIR, "figures_benchmark")
os.makedirs(FIG_DIR, exist_ok=True)

from retrain_pipeline import (build_features_and_targets, DATA_PATH, CLASSIFICATION_TARGET,
                               REGRESSION_TARGETS, multi_metric_rank)

REG_TARGETS = list(REGRESSION_TARGETS.keys())
LABELS = {**REGRESSION_TARGETS, CLASSIFICATION_TARGET: 'Arah Mata Angin (kategori)'}
COLORS = {
    'temp_avg': '#DC2626', 'humidity_avg': '#059669', 'rainfall_total_mm': '#2563EB',
    'solar_radiation_avg': '#F59E0B', 'pressure_avg_hpa': '#0D9488', 'wind_speed_avg': '#7C3AED',
}
ALGO_SHORT = {
    'LightGBM (Gradient Boosting)': 'LightGBM', 'Ridge Regression (Linear Baseline)': 'Ridge',
    'Random Forest (Ensemble Bagging)': 'Random Forest', 'Logistic Regression (Linear Baseline)': 'Logistic Reg.',
    'LSTM (Recurrent Neural Network)': 'LSTM', 'GRU (Recurrent Neural Network)': 'GRU',
}
DEPLOYABLE = ['LightGBM (Gradient Boosting)', 'Ridge Regression (Linear Baseline)',
              'Random Forest (Ensemble Bagging)', 'Logistic Regression (Linear Baseline)']
ALGO_COLOR = {
    'LightGBM': '#2563EB', 'Ridge': '#059669', 'Random Forest': '#D97706',
    'Logistic Reg.': '#0D9488', 'LSTM': '#DC2626', 'GRU': '#7C3AED',
}

with open(os.path.join(BASE_DIR, 'benchmark_merged_5algo_h1_h7.json'), encoding='utf-8') as f:
    records = json.load(f)
df_bench = pd.DataFrame(records)
df_bench['AlgoShort'] = df_bench['Algoritma'].map(ALGO_SHORT)
df_reg = df_bench[df_bench['Variabel'] != CLASSIFICATION_TARGET]
df_clf = df_bench[df_bench['Variabel'] == CLASSIFICATION_TARGET]

# ------------------------------------------------------------------------------
# FIG M1: MAE grid, 5 algoritma, 6 indikator regresi, H+1
# ------------------------------------------------------------------------------
fig, axes = plt.subplots(2, 3, figsize=(16, 9))
axes = axes.flatten()
for ax, var in zip(axes, REG_TARGETS):
    sub = df_reg[(df_reg['Variabel'] == var) & (df_reg['Horizon'] == 'H+1')].sort_values('MAE')
    colors = [ALGO_COLOR[a] for a in sub['AlgoShort']]
    bars = ax.bar(sub['AlgoShort'], sub['MAE'], color=colors)
    best_idx = sub['MAE'].values.argmin()
    bars[best_idx].set_edgecolor('black')
    bars[best_idx].set_linewidth(2)
    ax.set_title(LABELS[var], fontsize=10.5, fontweight='bold')
    ax.set_ylabel('MAE')
    ax.tick_params(axis='x', labelrotation=30, labelsize=8)
fig.suptitle('Perbandingan MAE 5 Algoritma (3 ML + 2 DL) per Indikator Regresi, H+1', fontsize=13, fontweight='bold', color='#1E3A8A')
fig.tight_layout(rect=[0, 0, 1, 0.95])
p1 = os.path.join(FIG_DIR, 'fig_merged1_5algo_mae_grid.png')
fig.savefig(p1, dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('saved', p1)

# ------------------------------------------------------------------------------
# FIG M2: Wind direction classification, 5 algoritma, Accuracy & F1-Macro, H+1 & H+7
# ------------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
for ax, h in zip(axes, ['H+1', 'H+7']):
    sub = df_clf[df_clf['Horizon'] == h].sort_values('F1_Macro', ascending=False)
    x = np.arange(len(sub))
    width = 0.38
    ax.bar(x - width/2, sub['Accuracy'], width, label='Accuracy', color='#7C3AED')
    ax.bar(x + width/2, sub['F1_Macro'], width, label='F1-Macro', color='#DB2777')
    ax.axhline(0.568, color='#64748B', linestyle=':', linewidth=1.3, label='Baseline Mayoritas (56.8%)')
    ax.set_xticks(x)
    ax.set_xticklabels(sub['AlgoShort'], rotation=30, fontsize=8)
    ax.set_title(f'Klasifikasi Arah Angin ({h})', fontsize=10.5, fontweight='bold')
    ax.set_ylim(0, 1)
    ax.legend(fontsize=7.5)
fig.suptitle('Accuracy & F1-Macro Klasifikasi Arah Mata Angin, 5 Algoritma', fontsize=12.5, fontweight='bold', color='#1E3A8A')
fig.tight_layout(rect=[0, 0, 1, 0.94])
p2 = os.path.join(FIG_DIR, 'fig_merged2_wind_classification.png')
fig.savefig(p2, dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('saved', p2)

# ------------------------------------------------------------------------------
# FIG M3: Waktu latih vs MAE (pareto), Curah Hujan H+1, 5 algoritma
# ------------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 6))
sub = df_reg[(df_reg['Variabel'] == 'rainfall_total_mm') & (df_reg['Horizon'] == 'H+1')]
for _, r in sub.iterrows():
    ax.scatter(r['Training_s'], r['MAE'], s=110, color=ALGO_COLOR[ALGO_SHORT[r['Algoritma']]], zorder=3)
    ax.annotate(ALGO_SHORT[r['Algoritma']], (r['Training_s'], r['MAE']), textcoords='offset points',
                xytext=(6, 6), fontsize=9)
ax.set_xscale('log')
ax.set_xlabel('Waktu Latih (detik, skala log)')
ax.set_ylabel('MAE')
ax.set_title('Waktu Latih vs MAE - Curah Hujan (H+1), 5 Algoritma', fontsize=11.5, fontweight='bold')
ax.grid(True, alpha=0.3, linestyle='--')
fig.tight_layout()
p3 = os.path.join(FIG_DIR, 'fig_merged3_pareto_rain.png')
fig.savefig(p3, dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('saved', p3)

# ------------------------------------------------------------------------------
# FIG M4: Trajektori ramalan H+1->H+7 (1x forecast rollout) vs realisasi aktual,
# 5 stasiun, memakai model PRODUKSI (deployable ML) dari bundle terlatih.
# Issue date dipilih di dalam jendela uji (max_date - 7 hari) supaya realisasi
# aktual H+1..H+7 masih tersedia di dataset untuk dibandingkan.
# ------------------------------------------------------------------------------
bundle = joblib.load(os.path.join(BASE_DIR, "models", "weather_model_latest.joblib"))
feature_cols = bundle['feature_cols']
target_cols = bundle['target_cols']
models = bundle['models']
algo_used = bundle['algo_used']

df_daily = pd.read_csv(DATA_PATH)
df_featured, _, _, _ = build_features_and_targets(df_daily)
max_date = df_featured['date_dt'].max()
issue_date = max_date - pd.Timedelta(days=7)
print(f'\nFIG M4: issue_date={issue_date.date()}, realisasi aktual s/d {max_date.date()}')

with open(os.path.join(FIG_DIR, '..', 'figures_model', 'fig_model3_stations.json'), encoding='utf-8') as f:
    station_meta = json.load(f)
stations_5 = station_meta['station_ids'][:5]
print(f'5 stasiun showcase: {stations_5}')

traj_files = []
for stn in stations_5:
    stn_data = df_featured[df_featured['stnname'].astype(str) == stn].sort_values('date_dt')
    issue_row = stn_data[stn_data['date_dt'] == issue_date]
    if issue_row.empty:
        print(f'  [{stn}] tidak ada baris pada issue_date, dilewati.')
        continue
    X_issue = issue_row[feature_cols]

    fig, axes = plt.subplots(2, 3, figsize=(16, 8.5))
    axes = axes.flatten()
    for ax, var in zip(axes, REG_TARGETS):
        h_range = list(range(1, 8))
        dates = [issue_date + pd.Timedelta(days=h) for h in h_range]
        preds = [models[f'{var}_h{h}'].predict(X_issue)[0] for h in h_range]
        actuals = []
        for d in dates:
            row = stn_data[stn_data['date_dt'] == d]
            actuals.append(row[var].values[0] if not row.empty and not pd.isna(row[var].values[0]) else np.nan)

        ax.plot(dates, actuals, marker='o', color='#0F172A', linewidth=1.8, label='Aktual')
        ax.plot(dates, preds, marker='x', color='#DC2626', linewidth=1.5, linestyle='--',
                label=f'Prediksi ({algo_used[f"{var}_h1"]})')
        ax.set_title(LABELS[var], fontsize=10, fontweight='bold')
        ax.set_xticks(dates)
        ax.set_xticklabels([f'H+{h}' for h in h_range], fontsize=7.5)
        ax.tick_params(axis='y', labelsize=7.5)
        ax.legend(fontsize=6.5)
        ax.grid(True, alpha=0.3, linestyle='--')

    fig.suptitle(f'Trajektori Ramalan H+1 s/d H+7 vs Realisasi Aktual - Stasiun AWS {stn} '
                 f'(Titik Ramal: {issue_date.date()})', fontsize=12.5, fontweight='bold', color='#1E3A8A')
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    p4 = os.path.join(FIG_DIR, f'fig_merged4_trajectory_{stn}.png')
    fig.savefig(p4, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    traj_files.append(os.path.basename(p4))
    print('  saved', p4)

with open(os.path.join(FIG_DIR, 'fig_merged4_stations.json'), 'w', encoding='utf-8') as f:
    json.dump({'issue_date': str(issue_date.date()), 'station_ids': stations_5, 'files': traj_files}, f, indent=2)

print("\nAll merged figures generated successfully.")
