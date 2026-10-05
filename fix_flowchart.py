# Regenerates fig_end_to_end_flowchart.png for Laporan 6 (Dokumentasi Master).
# Fixes: mojibake ("?" -> deg/x), stale "37 fitur + station embedding" claim,
# fabricated "3x Lebih Presisi (+35%)" claim, old Suhu-based benchmark numbers
# (now Curah Hujan per this session's Report 4 revision), and a few jargon terms.
# 2026-10-01: realigned with the 30-fitur / per-variabel-champion / 5-algoritma
# revision (Ridge Regression menggantikan LightGBM seragam untuk 4 dari 7
# variabel, retraining penuh ~21 menit untuk 49 sub-model, bukan 61 detik).
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D

BASE_DIR = r'D:\Projects\Kodepanda\Nusaklim\nusaklim'
fig_dir = os.path.join(BASE_DIR, 'figures')

plt.rcParams['font.family'] = 'DejaVu Sans'

steps = [
    {
        'title': 'STEP 01', 'subtitle': 'DATA CLEANING & QC\n(14,8 Juta Baris Data Sensor)',
        'color': '#1E3A8A', 'bg': '#EFF4FE',
        'items': [
            'Filter Reset Jam Alat Tahun 2000 (3.567 baris)',
            'Filter ID Uji Internal (WiFiLogger)',
            'Isolasi Eror Sensor (jadi NaN)',
            'Konversi Satuan (\u00b0C, hPa, mm, WIB)',
            'Output: nusaklim_cleaned_interval.csv',
        ],
    },
    {
        'title': 'STEP 02', 'subtitle': 'DAILY AGGREGATION &\nSTANDARISASI NOTULEN',
        'color': '#0D9488', 'bg': '#ECFDF7',
        'items': [
            'Agregasi 15-menit -> Harian (114k baris)',
            'SUM: Curah Hujan & Radiasi; MEAN: Suhu, Kelembapan, Tekanan, Angin',
            'Ekstrem Harian (Suhu Min, Suhu Max)',
            '4 Arah Angin Kardinal (U/T/S/B)',
            'Output: nusaklim_daily_aggregated.csv',
        ],
    },
    {
        'title': 'STEP 03', 'subtitle': 'FEATURE ENGINEERING &\nMODEL TRAINING (LANGKAH 1)',
        'color': '#C2660A', 'bg': '#FEF6E9',
        'items': [
            '30 Fitur Prediktor (Riwayat 1/3/7 Hari, Rata-rata Bergerak)',
            'Dinamika Atmosfer & Siklus Musiman Tahunan (sin/cos)',
            '49 Sub-Model per Horizon (H+1 s/d H+7), Algoritma Juara per Variabel',
            'Hasil: Suhu MAE \u00b10.76\u00b0C di H+1',
            'Output: weather_model_latest.joblib',
        ],
    },
    {
        'title': 'STEP 04', 'subtitle': 'BENCHMARKING 5 ALGORITMA &\nAUDIT KETAHANAN DATA',
        'color': '#DB2467', 'bg': '#FDF0F5',
        'items': [
            'Uji 5 Algoritma per Variabel: LightGBM, Ridge, RF, LSTM, GRU',
            '3 Algoritma ML (bukan DL) Tetap Jadi Juara Deployable',
            'Kelengkapan Data 84,5% (Median 92,5%)',
            'Uji Ketahanan (0-50% Data Hilang Disimulasikan)',
            '4 Pilar Ketahanan Model, Tidak Pernah Gagal Total',
        ],
    },
    {
        'title': 'STEP 05', 'subtitle': 'VALIDASI OPEN-METEO API\n(LANGKAH 2 ROADMAP)',
        'color': '#7C3AED', 'bg': '#F5F0FE',
        'items': [
            'Penarikan Data API 4 Stasiun Kunci (30 Hari)',
            'Open-Meteo Global: Suhu MAE 1.00\u00b0C',
            'NusaKlim Local AI: Suhu MAE 0.76\u00b0C',
            'NusaKlim Lebih Akurat di Suhu & Kelembapan;',
            'Open-Meteo Sedikit Lebih Baik di Curah Hujan',
        ],
    },
    {
        'title': 'STEP 06', 'subtitle': 'FASTAPI REST BACKEND &\nMLOPS PIPELINE (LANGKAH 3)',
        'color': '#0E7490', 'bg': '#ECF9FC',
        'items': [
            'REST Endpoints (/forecast, /stations)',
            'Rekomendasi Agronomi (Pemupukan, Panen TBS)',
            'Latensi Inferensi Cepat < 30 ms',
            'Pipeline Retraining Otomatis (\u00b121 Menit, 49 Sub-Model)',
            'Swagger UI & Siap Produksi',
        ],
    },
]

fig, ax = plt.subplots(figsize=(18, 12))
ax.set_xlim(0, 18)
ax.set_ylim(0, 12)
ax.axis('off')

ax.text(9, 11.6, 'FLOWCHART END-TO-END ARSITEKTUR & PIPELINE PROYEK NUSAKLIM WEATHER AI',
        ha='center', va='center', fontsize=17, fontweight='bold', color='#1E3A8A')
ax.text(9, 11.2, 'Dari 14,8 Juta Data Sensor Mentah Menuju Layanan REST API Prediksi Cuaca 7 Hari & Rekomendasi Agronomi PPKS',
        ha='center', va='center', fontsize=10.5, color='#475569')

box_w, box_h = 5.3, 4.5
gap_x, gap_y = 0.55, 0.65
row1_y = 10.35
row2_y = row1_y - box_h - gap_y
xs = [0.4, 0.4 + box_w + gap_x, 0.4 + 2 * (box_w + gap_x)]

positions = [(xs[0], row1_y), (xs[1], row1_y), (xs[2], row1_y),
             (xs[0], row2_y), (xs[1], row2_y), (xs[2], row2_y)]

def draw_box(ax, x, y, w, h, step):
    header_h = 0.6
    box = FancyBboxPatch((x, y - h), w, h, boxstyle='round,pad=0.02,rounding_size=0.08',
                          linewidth=1.8, edgecolor=step['color'], facecolor=step['bg'], zorder=2)
    ax.add_patch(box)
    header = FancyBboxPatch((x, y - header_h), w, header_h, boxstyle='round,pad=0.02,rounding_size=0.08',
                             linewidth=0, facecolor=step['color'], zorder=3)
    ax.add_patch(header)
    ax.text(x + w / 2, y - header_h / 2, step['title'], ha='center', va='center',
            fontsize=11, fontweight='bold', color='white', zorder=4)
    ax.text(x + w / 2, y - header_h - 0.35, step['subtitle'], ha='center', va='top',
            fontsize=9.3, fontweight='bold', color='#0F172A', zorder=4, linespacing=1.3)
    ax.plot([x + 0.25, x + w - 0.25], [y - header_h - 1.15, y - header_h - 1.15],
            color=step['color'], lw=0.8, linestyle=':', zorder=4)
    item_y = y - header_h - 1.42
    for item in step['items']:
        ax.text(x + 0.25, item_y, f'- {item}', ha='left', va='top', fontsize=7.6,
                color='#1E293B', zorder=4, wrap=True)
        item_y -= 0.58

for (x, y), step in zip(positions, steps):
    draw_box(ax, x, y, box_w, box_h, step)

def h_arrow(x0, y0, x1, y1, color):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle='-|>', mutation_scale=22,
                                  linewidth=2.2, color=color, zorder=5))

h_arrow(xs[0] + box_w, row1_y - box_h / 2, xs[1], row1_y - box_h / 2, steps[0]['color'])
h_arrow(xs[1] + box_w, row1_y - box_h / 2, xs[2], row1_y - box_h / 2, steps[1]['color'])
h_arrow(xs[2] + box_w / 2, row1_y - box_h, xs[2] + box_w / 2, row2_y, steps[2]['color'])
h_arrow(xs[0] + box_w, row2_y - box_h / 2, xs[1], row2_y - box_h / 2, steps[3]['color'])
h_arrow(xs[1] + box_w, row2_y - box_h / 2, xs[2], row2_y - box_h / 2, steps[4]['color'])

# dashed connector row1 -> row2 (step order continues right-to-left visually, matching original)
ax.plot([xs[0] + box_w / 2, xs[1] + box_w / 2], [row1_y - box_h - 0.05, row1_y - box_h - 0.05],
        color='#94A3B8', lw=1.4, linestyle='--', zorder=1)
ax.annotate('', xy=(xs[0] + box_w / 2, row1_y - box_h), xytext=(xs[0] + box_w / 2, row1_y - box_h - 0.15),
            arrowprops=dict(arrowstyle='-|>', color='#94A3B8', lw=1.4))

plt.tight_layout()
out_p = os.path.join(fig_dir, 'fig_end_to_end_flowchart.png')
plt.savefig(out_p, dpi=280, facecolor='white')
plt.close()
print(f'Saved {out_p}')
