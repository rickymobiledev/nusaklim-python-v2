import os
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 9.5

data_path = r"D:\Projects\Kodepanda\Nusaklim\nusaklim\nusaklim_daily_aggregated.csv"
device_path = r"D:\Projects\Kodepanda\Nusaklim\nusaklim\device_nusaklim.csv"
figures_dir = r"D:\Projects\Kodepanda\Nusaklim\nusaklim\figures"
output_path = os.path.join(figures_dir, "fig6_rainfall_classification.png")

df = pd.read_csv(data_path)
device = pd.read_csv(device_path)
device['id_str'] = device['id'].astype(str)
name_map = device.set_index('id_str')['name'].to_dict()

r = df['rainfall_total_mm'].dropna()
bins = [
    (-0.001, 0, 'Tidak Hujan\n(0 mm)'),
    (0, 20, 'Ringan\n(0.1-20 mm)'),
    (20, 50, 'Sedang\n(20-50 mm)'),
    (50, 100, 'Lebat\n(50-100 mm)'),
    (100, 150, 'Sgt Lebat\n(100-150 mm)'),
    (150, float('inf'), 'Ekstrem\n(>150 mm)'),
]
labels = [b[2] for b in bins]
counts = [int(((r > lo) & (r <= hi)).sum()) for lo, hi, _ in bins]
pcts = [100 * c / len(r) for c in counts]
colors_bmkg = ['#94A3B8', '#38BDF8', '#0284C7', '#2563EB', '#7C3AED', '#DC2626']

# Stasiun yang sebagian besar hari tercatatnya persis di batas maksimum alat (300 mm) dikeluarkan
# dari peringkat "tertinggi" -- pola ini mencerminkan kemungkinan gangguan sensor, bukan hujan asli.
pct_at_cap = df[df['rainfall_total_mm'] == 300.0].groupby('stnname').size() / df.groupby('stnname').size() * 100
anomalous_stations = pct_at_cap[pct_at_cap > 20].index.tolist()

rain_sum = df[~df['stnname'].isin(anomalous_stations)].groupby('stnname')['rainfall_total_mm'].sum()
top10 = rain_sum.sort_values(ascending=False).head(10)
top10_labels = [f"{sid} - {name_map.get(str(sid), 'N/A')}" for sid in top10.index]

fig, axes = plt.subplots(1, 2, figsize=(19.5, 7.5), dpi=200)

ax0 = axes[0]
bars0 = ax0.barh(labels[::-1], counts[::-1], color=colors_bmkg[::-1])
for bar, c, p in zip(bars0, counts[::-1], pcts[::-1]):
    ax0.text(bar.get_width() + max(counts) * 0.01, bar.get_y() + bar.get_height() / 2,
              f"{c:,} ({p:.1f}%)", va='center', fontsize=9, fontweight='bold')
ax0.set_title('Klasifikasi Intensitas Curah Hujan Harian (Standar BMKG)', fontweight='bold', fontsize=12)
ax0.set_xlabel('Frekuensi Hari', fontweight='bold')
ax0.spines['top'].set_visible(False)
ax0.spines['right'].set_visible(False)
ax0.set_xlim(0, max(counts) * 1.18)

ax1 = axes[1]
bars1 = ax1.barh(top10_labels[::-1], top10.values[::-1], color='#0D9488')
for bar, v in zip(bars1, top10.values[::-1]):
    ax1.text(bar.get_width() + top10.values.max() * 0.01, bar.get_y() + bar.get_height() / 2,
              f"{v:,.0f} mm", va='center', fontsize=8.5, fontweight='bold')
ax1.set_title('Top 10 Stasiun Akumulasi Hujan Tertinggi (Total mm)\n(stasiun dengan indikasi gangguan sensor sudah dikeluarkan)', fontweight='bold', fontsize=11)
ax1.set_xlabel('Total Akumulasi Curah Hujan (mm)', fontweight='bold')
ax1.set_ylabel('Stasiun AWS (ID - Nama)', fontweight='bold', fontsize=9)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.set_xlim(0, top10.values.max() * 1.2)
ax1.tick_params(axis='y', labelsize=8.5)

plt.tight_layout()
plt.savefig(output_path, dpi=200, bbox_inches='tight')
plt.close()
print(f"Saved {output_path}")
print("BMKG counts:", dict(zip([l.split(chr(10))[0] for l in labels], counts)))
print("Total valid rainfall days:", len(r))
