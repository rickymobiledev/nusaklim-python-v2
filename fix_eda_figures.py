# ==============================================================================
# Regenerate fig1_cleaning_summary.png, fig3_correlation.png, fig4_timeseries_trend.png
# for Laporan Preprocessing & EDA -- fixes mojibake ("?" instead of degree/superscript)
# by using a Unicode-safe font, and recomputes fig3/fig4 from the CURRENT dataset so
# numbers stay consistent with generate_pdf.py's narrative text.
# ==============================================================================
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE_DIR = r'D:\Projects\Kodepanda\Nusaklim\nusaklim'
fig_dir = os.path.join(BASE_DIR, 'figures')

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['figure.dpi'] = 300

df = pd.read_csv(os.path.join(BASE_DIR, 'nusaklim_daily_aggregated.csv'))
df['date'] = pd.to_datetime(df['date'])

# ------------------------------------------------------------------------------
# FIG 1: Cleaning Summary -- numbers loaded directly from interval_cleaning_stats.json
# (the same source generate_pdf.py's QC table in Bab 2.1 uses), so the chart's bars
# always match the report's cleaning_table_data one-for-one.
# ------------------------------------------------------------------------------
import json
with open(os.path.join(BASE_DIR, 'interval_cleaning_stats.json')) as f:
    qc_stats = json.load(f)

fig, axes = plt.subplots(1, 2, figsize=(20, 8.3))

ax = axes[0]
vol_labels = ['Total Raw Input', 'Valid Clean Interval', 'Aggregated Station-Days']
vol_values = [qc_stats['total_raw_rows'], qc_stats['retained_valid_rows'], 114507]
bars = ax.bar(vol_labels, vol_values, color=['#64748B', '#1E3A8A', '#059669'])
ax.set_ylabel('Jumlah Baris Data', fontweight='bold', fontsize=11)
ax.set_title('Volume Data: Raw vs Clean vs Harian', fontweight='bold', fontsize=13)
for bar, v in zip(bars, vol_values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(vol_values)*0.012, f'{v:,}',
            ha='center', va='bottom', fontsize=10, fontweight='bold')
ax.set_ylim(0, max(vol_values)*1.12)

ax2 = axes[1]
qc = qc_stats['qc_masked_to_nan']
anomaly_labels = [
    'Suhu (T<0\u00b0C / >100\u00b0C)',
    'Arah Angin (Sentinel 32767\u00b0 / >360\u00b0)',
    'Radiasi Solar (Sentinel 32767 W/m\u00b2 / >2000 W/m\u00b2)',
    'Tekanan Udara (<500 / >1200 hPa)',
    'Kelembapan (Sentinel -1/255)',
    'Kec. Angin (Sentinel 255 / >100 km/jam)',
    'Curah Hujan (<0 / >1000 mm)',
]
anomaly_values = [qc['temp'], qc['winddir'], qc['solar'], qc['pressure'], qc['humidity'], qc['windspd'], qc['rain']]
bars2 = ax2.barh(anomaly_labels, anomaly_values, color='#DC2626')
ax2.set_xlabel('Jumlah Nilai Dimask Menjadi NaN (per parameter)', fontweight='bold', fontsize=11)
ax2.set_title('Frekuensi Error Sensor per Parameter (Kode Eror & QC Limits)', fontweight='bold', fontsize=13)
ax2.invert_yaxis()
for bar, v in zip(bars2, anomaly_values):
    ax2.text(bar.get_width() + max(anomaly_values)*0.012, bar.get_y() + bar.get_height()/2, f'{v:,}',
             ha='left', va='center', fontsize=9.5, fontweight='bold')
ax2.set_xlim(0, max(anomaly_values)*1.18)

plt.tight_layout()
fig1_p = os.path.join(fig_dir, 'fig1_cleaning_summary.png')
plt.savefig(fig1_p, dpi=300)
plt.close()
print(f'Saved {fig1_p}')

# ------------------------------------------------------------------------------
# FIG 3: Pearson correlation matrix -- recomputed from the CURRENT daily aggregated CSV
# ------------------------------------------------------------------------------
corr_vars = ['temp_avg', 'humidity_avg', 'pressure_avg_hpa',
             'rainfall_total_mm', 'solar_radiation_avg', 'wind_speed_avg', 'wind_direction_deg']
corr_labels = ['Suhu Avg (\u00b0C)', 'Kelembapan Avg (%)',
               'Tekanan (hPa)', 'Curah Hujan (mm)', 'Radiasi Solar', 'Kec. Angin', 'Arah Angin (\u00b0)']
corr = df[corr_vars].corr()
corr.index = corr_labels
corr.columns = corr_labels

mask = np.triu(np.ones_like(corr, dtype=bool))
n = len(corr_labels)

fig, ax = plt.subplots(figsize=(13.5, 10.5))
cmap = plt.get_cmap('RdBu_r')
im_data = np.ma.masked_where(mask, corr.values)
im = ax.imshow(im_data, cmap=cmap, vmin=-1, vmax=1, aspect='equal')

for i in range(n):
    for j in range(n):
        if not mask[i, j]:
            val = corr.values[i, j]
            txt_color = 'white' if abs(val) > 0.55 else '#0F172A'
            ax.text(j, i, f'{val:.2f}', ha='center', va='center', fontsize=11.5, color=txt_color)

ax.set_xticks(range(n))
ax.set_yticks(range(n))
ax.set_xticklabels(corr_labels, rotation=90, fontsize=10.5)
ax.set_yticklabels(corr_labels, fontsize=10.5)
ax.set_xlim(-0.5, n - 1.5)
ax.set_ylim(n - 0.5, 0.5)
ax.set_title('Matriks Korelasi Pearson Antar Variabel Cuaca Harian', fontweight='bold', fontsize=14, pad=14)
for spine in ax.spines.values():
    spine.set_visible(False)
ax.grid(which='major', color='white', linewidth=1.5)
ax.set_xticks(np.arange(-0.5, n, 1), minor=True)
ax.set_yticks(np.arange(-0.5, n, 1), minor=True)
ax.grid(which='minor', color='white', linewidth=2)
ax.tick_params(which='minor', length=0)

cbar = fig.colorbar(im, ax=ax, shrink=0.85)
cbar.ax.tick_params(labelsize=10)

plt.tight_layout()
fig3_p = os.path.join(fig_dir, 'fig3_correlation.png')
plt.savefig(fig3_p, dpi=300)
plt.close()
print(f'Saved {fig3_p}')

# Print the exact numbers referenced in generate_pdf.py's Bab 5.1 narrative so the
# text can be kept in sync with this regenerated matrix.
def r(a, b):
    return corr.loc[a, b]

SUHU_AVG, KELEMBAPAN, TEKANAN, HUJAN, RADIASI, ANGIN, ARAH_ANGIN = corr_labels

print('\n=== Correlation values for Bab 5.1 narrative (cross-check against report text) ===')
print(f"Suhu Avg vs Kelembapan:      {r(SUHU_AVG, KELEMBAPAN):+.2f}")
print(f"Radiasi Solar vs Suhu Avg:   {r(RADIASI, SUHU_AVG):+.2f}")
print(f"Radiasi Solar vs Kelembapan: {r(RADIASI, KELEMBAPAN):+.2f}")
print(f"Curah Hujan vs Suhu Avg:     {r(HUJAN, SUHU_AVG):+.2f}")
print(f"Curah Hujan vs Kelembapan:   {r(HUJAN, KELEMBAPAN):+.2f}")
print(f"Curah Hujan vs Tekanan:      {r(HUJAN, TEKANAN):+.2f}")
print(f"Curah Hujan vs Radiasi:      {r(HUJAN, RADIASI):+.2f}")
print(f"Curah Hujan vs Kec. Angin:   {r(HUJAN, ANGIN):+.2f}")
print(f"Curah Hujan vs Arah Angin:   {r(HUJAN, ARAH_ANGIN):+.2f}")

# ------------------------------------------------------------------------------
# FIG 4: National daily time-series trend (7-day MA), gaps left as real gaps
# (no artificial straight-line connection across missing dates).
# ------------------------------------------------------------------------------
daily = df.groupby('date').agg(
    temp_avg=('temp_avg', 'mean'),
    humidity_avg=('humidity_avg', 'mean'),
    rainfall_total_mm=('rainfall_total_mm', 'mean'),
).sort_index()

full_range = pd.date_range(daily.index.min(), daily.index.max(), freq='D')
daily = daily.reindex(full_range)
daily.index.name = 'date'

temp_ma = daily['temp_avg'].rolling(7, min_periods=1).mean()
hum_ma = daily['humidity_avg'].rolling(7, min_periods=1).mean()

fig, axes = plt.subplots(3, 1, figsize=(20, 13), sharex=True)

axes[0].plot(daily.index, temp_ma, color='#DC2626', lw=1.3, label='Suhu Rata-rata (7-day MA)')
axes[0].set_ylabel('Suhu (\u00b0C)', fontweight='bold', fontsize=11)
axes[0].legend(loc='upper right')
axes[0].set_title('Tren Rangkaian Waktu Cuaca Harian Nasional (2022 - 2026)', fontweight='bold', fontsize=14)

axes[1].plot(daily.index, hum_ma, color='#059669', lw=1.3, label='Kelembapan (7-day MA)')
axes[1].set_ylabel('Kelembapan (%)', fontweight='bold', fontsize=11)
axes[1].legend(loc='upper right')

axes[2].bar(daily.index, daily['rainfall_total_mm'], color='#2563EB', width=1.0, label='Curah Hujan Harian Rata-rata (mm)')
axes[2].set_ylabel('Curah Hujan (mm)', fontweight='bold', fontsize=11)
axes[2].set_xlabel('Tanggal Pengamatan', fontweight='bold', fontsize=11)
axes[2].legend(loc='upper right')

plt.tight_layout()
fig4_p = os.path.join(fig_dir, 'fig4_timeseries_trend.png')
plt.savefig(fig4_p, dpi=300)
plt.close()
print(f'Saved {fig4_p}')

# ------------------------------------------------------------------------------
# FIG 4b: National daily time-series trend (7-day MA) for the remaining numeric
# parameters not covered by Fig 4 -- pressure, solar radiation, wind speed, and
# wind direction. Wind direction is circular (0-360 deg wraps around), so both
# its daily station-average and its 7-day MA are computed as a circular mean via
# sin/cos vector components, not a naive arithmetic mean (which would be wrong
# near the 0/360 boundary, e.g. averaging 350 deg and 10 deg would wrongly give
# 180 deg instead of 0 deg).
# ------------------------------------------------------------------------------
wind_dir_rad = np.deg2rad(df['wind_direction_deg'])
df['_winddir_sin'] = np.sin(wind_dir_rad)
df['_winddir_cos'] = np.cos(wind_dir_rad)

daily_b = df.groupby('date').agg(
    pressure_avg_hpa=('pressure_avg_hpa', 'mean'),
    solar_radiation_avg=('solar_radiation_avg', 'mean'),
    wind_speed_avg=('wind_speed_avg', 'mean'),
    _winddir_sin=('_winddir_sin', 'mean'),
    _winddir_cos=('_winddir_cos', 'mean'),
).sort_index()

full_range_b = pd.date_range(daily_b.index.min(), daily_b.index.max(), freq='D')
daily_b = daily_b.reindex(full_range_b)
daily_b.index.name = 'date'

pressure_ma = daily_b['pressure_avg_hpa'].rolling(7, min_periods=1).mean()
solar_ma = daily_b['solar_radiation_avg'].rolling(7, min_periods=1).mean()
windspd_ma = daily_b['wind_speed_avg'].rolling(7, min_periods=1).mean()

sin_ma = daily_b['_winddir_sin'].rolling(7, min_periods=1).mean()
cos_ma = daily_b['_winddir_cos'].rolling(7, min_periods=1).mean()
winddir_ma = np.rad2deg(np.arctan2(sin_ma, cos_ma)) % 360

fig, axes = plt.subplots(2, 2, figsize=(20, 11), sharex=True)

axes[0, 0].plot(daily_b.index, pressure_ma, color='#D97706', lw=1.3, label='Tekanan Udara (7-day MA)')
axes[0, 0].set_ylabel('Tekanan (hPa)', fontweight='bold', fontsize=11)
axes[0, 0].legend(loc='upper right')
axes[0, 0].set_title('Tren Rangkaian Waktu Cuaca Harian Nasional – Parameter Tambahan (2022 - 2026)', fontweight='bold', fontsize=13)

axes[0, 1].plot(daily_b.index, solar_ma, color='#EA580C', lw=1.3, label='Radiasi Solar (7-day MA)')
axes[0, 1].set_ylabel('Radiasi Solar (W/m²)', fontweight='bold', fontsize=11)
axes[0, 1].legend(loc='upper right')

axes[1, 0].plot(daily_b.index, windspd_ma, color='#7C3AED', lw=1.3, label='Kecepatan Angin (7-day MA)')
axes[1, 0].set_ylabel('Kec. Angin (km/jam)', fontweight='bold', fontsize=11)
axes[1, 0].set_xlabel('Tanggal Pengamatan', fontweight='bold', fontsize=11)
axes[1, 0].legend(loc='upper right')

axes[1, 1].plot(daily_b.index, winddir_ma, color='#0EA5E9', lw=1.3, label='Arah Angin (7-day circular MA)')
axes[1, 1].set_ylabel('Arah Angin (°)', fontweight='bold', fontsize=11)
axes[1, 1].set_xlabel('Tanggal Pengamatan', fontweight='bold', fontsize=11)
axes[1, 1].set_ylim(0, 360)
axes[1, 1].set_yticks([0, 90, 180, 270, 360])
axes[1, 1].legend(loc='upper right')

plt.tight_layout()
fig4b_p = os.path.join(fig_dir, 'fig4b_timeseries_trend_extra.png')
plt.savefig(fig4b_p, dpi=300)
plt.close()
print(f'Saved {fig4b_p}')

df.drop(columns=['_winddir_sin', '_winddir_cos'], inplace=True)

# ------------------------------------------------------------------------------
# FIG 8: Station observation-length histogram -- recomputed from current data,
# fixes wrong station count baked into the old chart title ("184" -> real 183).
# ------------------------------------------------------------------------------
days_per_station = df.groupby('stnname')['date'].count()
n_stations = df['stnname'].nunique()
median_days = days_per_station.median()

fig, ax = plt.subplots(figsize=(20, 10))
counts, bins, patches = ax.hist(days_per_station, bins=30, color='#8B87E8', edgecolor='black', alpha=0.85)
ax.axvline(median_days, color='red', linestyle='--', lw=2, label=f'Median Durasi: {median_days:.0f} Hari (~{median_days/365:.1f} Tahun)')

# Smooth KDE-style trend line over the histogram (matches original chart's visual style)
from scipy.stats import gaussian_kde
kde = gaussian_kde(days_per_station)
x_grid = np.linspace(days_per_station.min(), days_per_station.max(), 200)
bin_width = bins[1] - bins[0]
ax.plot(x_grid, kde(x_grid) * len(days_per_station) * bin_width, color='#4B3F9E', lw=2.5)

ax.set_xlabel('Jumlah Hari Aktif Beroperasi (Hari)', fontweight='bold', fontsize=12)
ax.set_ylabel('Jumlah Stasiun AWS', fontweight='bold', fontsize=12)
ax.set_title(f'Distribusi Kelengkapan Hari Pengamatan per Stasiun AWS (Total {n_stations} Stasiun)', fontweight='bold', fontsize=15)
ax.legend(loc='upper right', fontsize=11)

plt.tight_layout()
fig8_p = os.path.join(fig_dir, 'fig8_station_longevity.png')
plt.savefig(fig8_p, dpi=300)
plt.close()
print(f'Saved {fig8_p} (n_stations={n_stations}, median_days={median_days:.0f})')
