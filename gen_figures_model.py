# ==============================================================================
# REGENERATE figures_model/*.png FROM THE REAL RETRAINED MODEL BUNDLE
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
FIG_DIR = os.path.join(BASE_DIR, "figures_model")
os.makedirs(FIG_DIR, exist_ok=True)

from retrain_pipeline import build_features_and_targets, DATA_PATH, extract_feature_importance, compute_permutation_importance, CLASSIFICATION_TARGET

bundle = joblib.load(os.path.join(BASE_DIR, "models", "weather_model_latest.joblib"))
metrics = bundle['metrics']
feature_cols = bundle['feature_cols']
target_cols = bundle['target_cols']
models = bundle['models']
algo_used = bundle['algo_used']

df_daily = pd.read_csv(DATA_PATH)
df_featured, _, _, _ = build_features_and_targets(df_daily)

from datetime import timedelta
max_date = df_featured['date_dt'].max()
split_date = max_date - timedelta(days=30)
test_df = df_featured[df_featured['date_dt'] > split_date]

REG_TARGETS = ['temp_avg', 'humidity_avg', 'rainfall_total_mm', 'solar_radiation_avg', 'pressure_avg_hpa', 'wind_speed_avg']
LABELS = {
    'temp_avg': 'Suhu Rata-rata (°C)', 'humidity_avg': 'Kelembapan (%)',
    'rainfall_total_mm': 'Curah Hujan (mm)', 'solar_radiation_avg': 'Radiasi Matahari (W/m²)',
    'pressure_avg_hpa': 'Tekanan Udara (hPa)', 'wind_speed_avg': 'Kecepatan Angin (km/h)',
    'wind_direction_name': 'Arah Mata Angin (kategori)',
}
COLORS = {
    'temp_avg': '#DC2626', 'humidity_avg': '#059669', 'rainfall_total_mm': '#2563EB',
    'solar_radiation_avg': '#F59E0B', 'pressure_avg_hpa': '#0D9488', 'wind_speed_avg': '#7C3AED',
    'wind_direction_name': '#DB2777',
}

# ------------------------------------------------------------------------------
# FIG 1: Error decay curve (MAE per horizon) for all 6 regression targets, normalized
# ------------------------------------------------------------------------------
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
axes = axes.flatten()
for ax, var in zip(axes, REG_TARGETS):
    horizons = list(range(1, 8))
    maes = [metrics[f'{var}_h{h}']['MAE'] for h in horizons]
    ax.plot(horizons, maes, marker='o', color=COLORS[var], linewidth=2)
    ax.set_title(LABELS[var], fontsize=10.5, fontweight='bold')
    ax.set_xlabel('Horizon (H+n)', fontsize=8.5)
    ax.set_ylabel('MAE', fontsize=8.5)
    ax.set_xticks(horizons)
    ax.grid(True, alpha=0.3, linestyle='--')
fig.suptitle('Kurva Peluruhan Error Prediksi (MAE) per Horizon H+1 s/d H+7 - 6 Target Regresi', fontsize=13, fontweight='bold', color='#1E3A8A')
fig.tight_layout(rect=[0, 0, 1, 0.95])
p1 = os.path.join(FIG_DIR, 'fig_model1_horizon_performance.png')
fig.savefig(p1, dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('saved', p1)

# ------------------------------------------------------------------------------
# FIG 1b: Wind direction classifier accuracy per horizon
# ------------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 4.5))
horizons = list(range(1, 8))
acc = [metrics[f'wind_direction_name_h{h}']['Accuracy'] for h in horizons]
f1m = [metrics[f'wind_direction_name_h{h}']['F1_Macro'] for h in horizons]
ax.plot(horizons, acc, marker='o', color='#7C3AED', linewidth=2, label='Accuracy')
ax.plot(horizons, f1m, marker='s', color='#DB2777', linewidth=2, linestyle='--', label='F1-Macro')
ax.axhline(0.568, color='#64748B', linestyle=':', linewidth=1.5, label='Baseline Kelas Mayoritas (Selatan, 56.8%)')
ax.set_title('Performa Klasifikasi Arah Mata Angin per Horizon', fontsize=11, fontweight='bold')
ax.set_xlabel('Horizon (H+n)')
ax.set_ylabel('Skor')
ax.set_xticks(horizons)
ax.set_ylim(0, 1)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3, linestyle='--')
fig.tight_layout()
p1b = os.path.join(FIG_DIR, 'fig_model1b_wind_direction_performance.png')
fig.savefig(p1b, dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('saved', p1b)

# ------------------------------------------------------------------------------
# FIG 2: Feature importance (H+1) - seluruh 7 variabel target, masing-masing
# memakai algoritma juaranya sendiri (extract_feature_importance menyeragamkan
# ekstraksi importance lintas LightGBM/Ridge/Logistic Regression/Random Forest).
# ------------------------------------------------------------------------------
ALL_TARGETS_FOR_IMPORTANCE = REG_TARGETS + [CLASSIFICATION_TARGET]

perm_imp = {}
for var in ALL_TARGETS_FOR_IMPORTANCE:
    key = f'{var}_h1'
    col = target_cols[key]
    vt = test_df.dropna(subset=feature_cols + [col])
    ttype = 'classification' if var == CLASSIFICATION_TARGET else 'regression'
    perm_imp[key] = compute_permutation_importance(models[key], vt[feature_cols], vt[col], ttype)

with open(os.path.join(FIG_DIR, 'permutation_importance_h1.json'), 'w', encoding='utf-8') as f:
    json.dump({k: v.to_dict() for k, v in perm_imp.items()}, f, indent=2)

fig, axes = plt.subplots(2, 4, figsize=(22, 10))
axes = axes.flatten()
for ax, var in zip(axes, ALL_TARGETS_FOR_IMPORTANCE):
    imp = perm_imp[f'{var}_h1'].sort_values(ascending=True).tail(10)
    ax.barh(imp.index, imp.values, color=COLORS[var])
    unit = 'penurunan F1-Macro' if var == CLASSIFICATION_TARGET else 'kenaikan MAE'
    ax.set_title(f'{LABELS[var]}\n({algo_used[f"{var}_h1"]})', fontsize=9.5, fontweight='bold')
    ax.set_xlabel(f'Permutation importance ({unit} saat fitur diacak)', fontsize=7.5)
    ax.tick_params(axis='y', labelsize=7.5)
    ax.tick_params(axis='x', labelsize=7)
for ax in axes[len(ALL_TARGETS_FOR_IMPORTANCE):]:
    ax.axis('off')

fig.suptitle('Top 10 Fitur Paling Berpengaruh per Variabel Target (H+1) - Permutation Importance pada Data Uji', fontsize=13, fontweight='bold', color='#1E3A8A')
fig.tight_layout(rect=[0, 0, 1, 0.95])
p2 = os.path.join(FIG_DIR, 'fig_model2_feature_importance.png')
fig.savefig(p2, dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('saved', p2)

for var in ALL_TARGETS_FOR_IMPORTANCE:
    print(f"\nTop 10 features for {var} (H+1, algo={algo_used[f'{var}_h1']}):")
    print(perm_imp[f'{var}_h1'].sort_values(ascending=False).head(10))

# ------------------------------------------------------------------------------
# FIG 3: Actual vs predicted time series - all 6 regression targets (H+1), for the
# 10 stations with the most complete data in the 30-day test window (most
# representative comparison; a station with only a handful of valid test days
# would produce a near-empty, uninformative chart).
# ------------------------------------------------------------------------------
_ref_target_col = target_cols['temp_avg_h1']
_valid_test_counts = (
    test_df.dropna(subset=feature_cols + [_ref_target_col])
    .groupby('stnname').size().sort_values(ascending=False)
)
station_ids = list(_valid_test_counts.head(10).index.astype(str))
print(f"\nFIG 3: 10 stasiun terpilih (baris uji valid terbanyak): {station_ids}")

fig3_files = []
for station_id in station_ids:
    stn_test = test_df[test_df['stnname'].astype(str) == station_id].sort_values('date_dt')
    stn_name_display = station_id

    fig, axes = plt.subplots(2, 3, figsize=(16, 8.5))
    axes = axes.flatten()
    for ax, var in zip(axes, REG_TARGETS):
        target_col = target_cols[f'{var}_h1']
        valid = stn_test.dropna(subset=feature_cols + [target_col])
        X = valid[feature_cols]
        y_actual = valid[target_col].values
        y_pred = models[f'{var}_h1'].predict(X)
        dates = valid['date_dt'].values

        ax.plot(dates, y_actual, marker='o', markersize=3.5, color='#0F172A', linewidth=1.5, label='Aktual')
        ax.plot(dates, y_pred, marker='x', markersize=3.5, color='#DC2626', linewidth=1.3, linestyle='--', label=f'Prediksi H+1 ({algo_used[f"{var}_h1"]})')
        ax.set_title(LABELS[var], fontsize=10, fontweight='bold')
        ax.set_ylabel(LABELS[var].split('(')[-1].rstrip(')'), fontsize=8)
        ax.tick_params(axis='x', labelrotation=30, labelsize=7)
        ax.tick_params(axis='y', labelsize=7.5)
        ax.legend(fontsize=6.5)
        ax.grid(True, alpha=0.3, linestyle='--')

    fig.suptitle(f'Deret Waktu Aktual vs Prediksi Model (H+1) - 6 Target Regresi, Stasiun AWS {stn_name_display} (30 Hari Uji)', fontsize=12.5, fontweight='bold', color='#1E3A8A')
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    p3 = os.path.join(FIG_DIR, f'fig_model3_actual_vs_predicted_{station_id}.png')
    fig.savefig(p3, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    fig3_files.append(os.path.basename(p3))
    print('saved', p3)

with open(os.path.join(FIG_DIR, 'fig_model3_stations.json'), 'w', encoding='utf-8') as f:
    json.dump({'station_ids': station_ids, 'files': fig3_files}, f, indent=2)

print("\nAll figures regenerated successfully.")
