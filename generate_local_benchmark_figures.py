"""Grafik untuk Laporan 3b (revisi 06-10-2026) - dari local_benchmark_v3.json.
Hanya Fig 1 (proporsi stasiun yang lebih akurat dengan Model Lokal vs Global per
indikator). Hitungan kemenangan memakai local_vs_global_stats.station_wins - sumber
yang sama dengan teks laporan, supaya gambar dan narasi selalu konsisten."""
import os, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['figure.dpi'] = 300

BASE_DIR = r'D:\Projects\Kodepanda\Nusaklim\nusaklim'
FIG_DIR = os.path.join(BASE_DIR, 'figures_per_station')
os.makedirs(FIG_DIR, exist_ok=True)

with open(os.path.join(BASE_DIR, 'local_benchmark_v3.json'), encoding='utf-8') as f:
    R = json.load(f)

import sys
sys.path.insert(0, BASE_DIR)
from retrain_pipeline import REGRESSION_TARGETS, CLASSIFICATION_TARGET
from local_vs_global_stats import station_wins

INDICATORS = list(REGRESSION_TARGETS.items()) + [(CLASSIFICATION_TARGET, 'Arah Mata Angin')]

rows = []
for var, label in INDICATORS:
    algo = R['algo_used'][var]
    n_local, n_global, n_tie, n_total = station_wins(R, var, CLASSIFICATION_TARGET)
    rows.append({'var': var, 'label': f'{label}\n({algo})', 'n_local': n_local, 'n_global': n_global, 'n_tie': n_tie, 'n_total': n_total})

df_win = pd.DataFrame(rows)
for c in ('local', 'global', 'tie'):
    df_win[f'pct_{c}'] = df_win[f'n_{c}'] / df_win['n_total'] * 100

n_stn = len(R['stations'])
fig, ax = plt.subplots(figsize=(10, 6))
y = np.arange(len(df_win))
ax.barh(y, df_win['pct_local'], color='#0D9488', label='Model Lokal lebih akurat')
ax.barh(y, df_win['pct_tie'], left=df_win['pct_local'], color='#E2E8F0', label='Seri')
ax.barh(y, df_win['pct_global'], left=df_win['pct_local'] + df_win['pct_tie'], color='#64748B', label='Model Global lebih akurat')
ax.axvline(50, color='#0F172A', linestyle=':', linewidth=1)
ax.set_yticks(y)
ax.set_yticklabels(df_win['label'], fontsize=8.5)
ax.invert_yaxis()
ax.set_xlabel(f'% Stasiun (dari {n_stn} stasiun uji)', fontsize=9, fontweight='bold')
ax.set_title(f'Proporsi Stasiun yang Lebih Akurat: Model Lokal vs Model Global per Indikator ({n_stn} stasiun)\n'
             '(Algoritma juara produksi masing-masing indikator, lihat Tabel 3.3 Laporan 3)', fontsize=10, fontweight='bold')
for i, r in df_win.iterrows():
    if r['n_local'] > 0:
        ax.text(1.5, i, f"Lokal {r['n_local']}/{r['n_total']}", va='center', ha='left', fontsize=7.5, color='white', fontweight='bold')
    if r['n_global'] > 0:
        ax.text(98.5, i, f"Global {r['n_global']}/{r['n_total']}", va='center', ha='right', fontsize=7.5, color='white', fontweight='bold')
ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=8.5)
ax.set_xlim(0, 100)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'fig_local1_winrate_per_indicator.png'), bbox_inches='tight')
plt.close()

print('Saved 1 figure to', FIG_DIR)
