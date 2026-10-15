"""Snapshot data & model yang dipakai Laporan 3 / 3b (terbit dengan titik data 19 Agustus 2026).

Dipakai bersama oleh generate_model_pdf.py, gen_figures_model.py, dan gen_figures_merged.py supaya
jendela uji 30 hari (21 Juli - 19 Agustus 2026), metrik, gambar, dan tabel ramalan tidak bergeser
ketika data harian bertambah atau model `latest` dilatih ulang.

Dua berkas data karena asal-usul keduanya memang berbeda pada laporan terbit:
- REPORT_RAW_CSV (sum_backup, 114,507 baris): sumber angka teks/tabel Laporan 3 (jumlah baris, baseline arah angin).
- REPORT_FIG_CSV (114,505 baris): sumber gambar deret waktu uji 30 hari (Gambar 4 & 7).
Gambar trajektori (Gambar 8) memakai CSV harian lengkap karena membandingkan dengan realisasi setelah 19 Agustus.
"""
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_CUTOFF = pd.Timestamp('2026-08-19')
REPORT_BUNDLE = os.path.join(BASE_DIR, 'models', 'weather_model_bundle_20261012_141427.joblib')
REPORT_RAW_CSV = os.path.join(BASE_DIR, 'nusaklim_daily_aggregated.sum_backup.csv')
REPORT_FIG_CSV = os.path.join(BASE_DIR, 'nusaklim_daily_aggregated.report_snapshot.csv')


def load_report_daily():
    return pd.read_csv(REPORT_RAW_CSV).rename(columns={'solar_radiation_total': 'solar_radiation_avg'})


def load_report_fig_daily():
    return pd.read_csv(REPORT_FIG_CSV)
