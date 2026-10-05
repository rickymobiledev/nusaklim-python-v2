# ==============================================================================
# Dekomposisi Time Series Bulanan (Observed/Trend/Seasonal/Residual, Additive)
# per parameter cuaca -- 1 grafik per parameter, untuk Bab 6 Laporan Preprocessing & EDA.
# ==============================================================================
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose

BASE_DIR = r'D:\Projects\Kodepanda\Nusaklim\nusaklim'
fig_dir = os.path.join(BASE_DIR, 'figures')

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['figure.dpi'] = 200

df = pd.read_csv(os.path.join(BASE_DIR, 'nusaklim_daily_aggregated.csv'))
df['date'] = pd.to_datetime(df['date'])

daily = df.groupby('date').agg(
    temp_avg=('temp_avg', 'mean'),
    humidity_avg=('humidity_avg', 'mean'),
    pressure_avg_hpa=('pressure_avg_hpa', 'mean'),
    rainfall_total_mm=('rainfall_total_mm', 'mean'),
    solar_radiation_avg=('solar_radiation_avg', 'mean'),
    wind_speed_avg=('wind_speed_avg', 'mean'),
).sort_index()

# Jan-Agu 2022 dan Jan-Mar 2023 dikeluarkan dari dekomposisi: jaringan AWS baru berjalan
# 1-18 stasiun pada periode tersebut (dibanding 183 stasiun penuh), termasuk 1 bulan (Agu
# 2022) yang hanya berisi 1 baris data -- rata-rata nasional pada periode ini tidak
# representatif dan akan mendistorsi komponen tren/musiman jika diikutsertakan.
DECOMP_START = '2023-05-01'
full_range = pd.date_range(DECOMP_START, daily.index.max(), freq='D')
daily = daily.reindex(full_range)
daily.index.name = 'date'

monthly = daily.resample('MS').mean()

PARAMS = [
    dict(col='temp_avg', slug='suhu', title='Suhu Rata-rata', unit='\u00b0C', color='#DC2626'),
    dict(col='humidity_avg', slug='kelembapan', title='Kelembapan Rata-rata', unit='%', color='#0284C7'),
    dict(col='pressure_avg_hpa', slug='tekanan', title='Tekanan Udara Rata-rata', unit='hPa', color='#7C3AED'),
    dict(col='rainfall_total_mm', slug='hujan', title='Curah Hujan Rata-rata Nasional', unit='mm/hari', color='#2563EB'),
    dict(col='solar_radiation_avg', slug='radiasi', title='Radiasi Solar Rata-rata', unit='W/m\u00b2', color='#EA580C'),
    dict(col='wind_speed_avg', slug='angin', title='Kecepatan Angin Rata-rata', unit='km/jam', color='#059669'),
]

MONTH_ID = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']

summary = {}

for p in PARAMS:
    series = monthly[p['col']].interpolate(limit_direction='both')
    result = seasonal_decompose(series, model='additive', period=12, extrapolate_trend='period')

    fig, axes = plt.subplots(4, 1, figsize=(11, 9), sharex=True)

    axes[0].plot(series.index, result.observed, color=p['color'], lw=1.4)
    axes[0].set_ylabel('Observed')
    axes[0].set_title(f"Dekomposisi Time Series Bulanan {p['title']} (Additive Model)", fontweight='bold', fontsize=12.5)

    axes[1].plot(series.index, result.trend, color='#EA580C', lw=1.6)
    axes[1].set_ylabel('Trend')

    axes[2].plot(series.index, result.seasonal, color='#16A34A', lw=1.3)
    axes[2].set_ylabel('Seasonal')
    axes[2].axhline(0, color='#94A3B8', lw=0.8, ls='--')

    axes[3].scatter(series.index, result.resid, color='#DC2626', s=14)
    axes[3].axhline(0, color='#334155', lw=0.9, ls='--')
    axes[3].set_ylabel('Residual')
    axes[3].set_xlabel('Bulan')

    for ax in axes:
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out_p = os.path.join(fig_dir, f"fig9_decomp_{p['slug']}.png")
    plt.savefig(out_p, dpi=200)
    plt.close()

    # -- Ringkasan numerik untuk narasi laporan --
    trend_clean = result.trend.dropna()
    trend_start, trend_end = trend_clean.iloc[0], trend_clean.iloc[-1]
    trend_change_pct = (trend_end - trend_start) / abs(trend_start) * 100 if trend_start != 0 else float('nan')
    trend_direction = 'naik' if trend_end > trend_start else ('turun' if trend_end < trend_start else 'stabil')

    seasonal_by_month = result.seasonal.groupby(result.seasonal.index.month).mean()
    peak_month = seasonal_by_month.idxmax()
    trough_month = seasonal_by_month.idxmin()

    resid_clean = result.resid.dropna()
    resid_std = resid_clean.std()
    resid_mean = resid_clean.mean()

    summary[p['slug']] = dict(
        title=p['title'], unit=p['unit'],
        trend_start=trend_start, trend_end=trend_end,
        trend_change_pct=trend_change_pct, trend_direction=trend_direction,
        peak_month=MONTH_ID[peak_month - 1], trough_month=MONTH_ID[trough_month - 1],
        seasonal_amplitude=result.seasonal.max() - result.seasonal.min(),
        resid_mean=resid_mean, resid_std=resid_std,
        n_months=len(series),
    )
    print(f"Saved {out_p}")

print('\n=== Ringkasan Dekomposisi (untuk narasi laporan) ===')
for slug, s in summary.items():
    print(f"\n[{s['title']} ({s['unit']})] n_bulan={s['n_months']}")
    print(f"  Trend: {s['trend_start']:.2f} -> {s['trend_end']:.2f} ({s['trend_direction']}, {s['trend_change_pct']:+.1f}%)")
    print(f"  Seasonal: puncak bulan {s['peak_month']}, terendah bulan {s['trough_month']}, amplitudo {s['seasonal_amplitude']:.2f}")
    print(f"  Residual: mean={s['resid_mean']:.4f}, std={s['resid_std']:.3f}")
