import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 9.5
plt.rcParams['axes.titlesize'] = 10.5
plt.rcParams['axes.labelsize'] = 9

data_path = r"D:\Projects\Kodepanda\Nusaklim\nusaklim\nusaklim_daily_aggregated.csv"
figures_dir = r"D:\Projects\Kodepanda\Nusaklim\nusaklim\figures"
output_path = os.path.join(figures_dir, "fig2_distributions.png")

print(f"Reading dataset from {data_path}...")
df = pd.read_csv(data_path)

# Variables to plot
vars_config = [
    {
        'col': 'temp_avg',
        'name': 'Suhu Rata-rata (°C)',
        'color': '#2563EB',
        'unit': '°C',
        'data': df['temp_avg'].dropna()
    },
    {
        'col': 'humidity_avg',
        'name': 'Kelembapan Rata-rata (%)',
        'color': '#059669',
        'unit': '%',
        'data': df['humidity_avg'].dropna()
    },
    {
        'col': 'pressure_avg_hpa',
        'name': 'Tekanan Udara (hPa)',
        'color': '#D97706',
        'unit': 'hPa',
        'data': df['pressure_avg_hpa'].dropna()
    },
    {
        'col': 'rainfall_total_mm',
        'name': 'Curah Hujan > 0 mm/hari (Log Scale)',
        'color': '#0284C7',
        'unit': 'mm',
        'data': df[df['rainfall_total_mm'] > 0]['rainfall_total_mm'].dropna(),
        'log_scale': (True, False)
    },
    {
        'col': 'solar_radiation_avg',
        'name': 'Akumulasi Radiasi Solar (W/m²)',
        'color': '#EA580C',
        'unit': 'W/m²',
        'data': df[df['solar_radiation_avg'] > 0]['solar_radiation_avg'].dropna()
    },
    {
        'col': 'wind_speed_avg',
        'name': 'Kecepatan Angin Rata-rata (km/h)',
        'color': '#7C3AED',
        'unit': 'km/h',
        'data': df['wind_speed_avg'].dropna()
    }
]

# Create 2x3 main blocks, each having [boxplot (top), hist/kde (bottom)]
fig = plt.figure(figsize=(14.5, 9.2), dpi=300)
outer_grid = fig.add_gridspec(2, 3, wspace=0.28, hspace=0.35)

for idx, cfg in enumerate(vars_config):
    row = idx // 3
    col = idx % 3
    
    # Sub-grid for boxplot + hist
    inner_grid = outer_grid[row, col].subgridspec(2, 1, height_ratios=[0.22, 0.78], hspace=0.06)
    
    ax_box = fig.add_subplot(inner_grid[0])
    ax_hist = fig.add_subplot(inner_grid[1], sharex=ax_box)
    
    s = cfg['data']
    color = cfg['color']
    
    # 1. Boxplot (Horizontal)
    sns.boxplot(
        x=s, ax=ax_box, color=color, 
        fliersize=2, boxprops=dict(alpha=0.75),
        medianprops=dict(color='#DC2626', linewidth=2)
    )
    ax_box.set(xlabel='')
    ax_box.set_title(cfg['name'], fontweight='bold', pad=4, color='#0F172A')
    ax_box.tick_params(axis='x', labelbottom=False, bottom=False)
    ax_box.set_yticks([])
    for spine in ['top', 'right', 'left', 'bottom']:
        ax_box.spines[spine].set_visible(False)
    ax_box.grid(True, axis='x', linestyle=':', alpha=0.4)
    
    # 2. Histogram + KDE
    log_scale = cfg.get('log_scale', False)
    sns.histplot(
        s, kde=True, ax=ax_hist, color=color, bins=35,
        log_scale=log_scale, alpha=0.55, edgecolor=color
    )
    
    # Add vertical dashed lines for Q1, Median, Q3
    q1 = s.quantile(0.25)
    med = s.median()
    q3 = s.quantile(0.75)
    
    ax_hist.axvline(med, color='#DC2626', linestyle='--', linewidth=1.5, label=f"Median: {med:.2f}")
    ax_hist.axvline(q1, color='#475569', linestyle=':', linewidth=1.1, label=f"Q1: {q1:.2f}")
    ax_hist.axvline(q3, color='#475569', linestyle=':', linewidth=1.1, label=f"Q3: {q3:.2f}")
    
    ax_hist.set_xlabel(f"{cfg['name'].split('(')[0].strip()} ({cfg['unit']})", fontweight='bold')
    ax_hist.set_ylabel('Frekuensi', fontweight='bold')
    ax_hist.legend(loc='upper right', frameon=True, fontsize=7.8, framealpha=0.85)
    ax_hist.grid(True, linestyle='--', alpha=0.3)
    
    # Improve spines
    ax_hist.spines['top'].set_visible(False)
    ax_hist.spines['right'].set_visible(False)

plt.suptitle("Distribusi Frekuensi & Boxplot Parameter Cuaca Harian NusaKlim AWS (PPKS)", fontsize=13, fontweight='bold', y=0.98, color='#1E3A8A')

plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"SUCCESS: Generated distribution plot with boxplots at {output_path}")
print(f"File size: {os.path.getsize(output_path):,} bytes")

