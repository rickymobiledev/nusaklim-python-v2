"""
DEMO PERFORMA MODEL NUSAKLIM - menampilkan performa model produksi satu per satu
(per indikator, per horizon H+1..H+7) pada data uji 30 hari terakhir, lalu menyimpan
hasilnya ke file yang mudah dibaca (Markdown + CSV) di folder logs/demo/.

Semua angka dihitung LANGSUNG saat skrip dijalankan dari model produksi
(models/weather_model_latest.joblib) dan data harian (nusaklim_daily_aggregated.csv),
bukan disalin dari laporan.

CARA PAKAI (dari folder proyek, dengan virtual environment proyek):
    .venv\\Scripts\\python.exe demo_performa_model.py                     # semua indikator, semua horizon
    .venv\\Scripts\\python.exe demo_performa_model.py --indikator suhu    # satu indikator saja
    .venv\\Scripts\\python.exe demo_performa_model.py --indikator hujan --horizon 1,7
    .venv\\Scripts\\python.exe demo_performa_model.py --hanya-stasiun 222 # nilai performa di satu stasiun
    .venv\\Scripts\\python.exe demo_performa_model.py --cepat             # pakai metrik tersimpan di model (tanpa hitung ulang, tanpa pembanding)
    .venv\\Scripts\\python.exe demo_performa_model.py --stasiun 248       # stasiun untuk contoh ramalan 7 hari

Nama indikator: suhu, kelembapan, hujan, radiasi, tekanan, angin, arah (atau 'semua').
"""
import os
import sys
import json
import argparse
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, f1_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from retrain_pipeline import (build_features_and_targets, generate_7day_forecast, REGRESSION_TARGETS,
                              CLASSIFICATION_TARGET, DATA_PATH, MODEL_DIR)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ALIAS = {'suhu': 'temp_avg', 'kelembapan': 'humidity_avg', 'hujan': 'rainfall_total_mm', 'radiasi': 'solar_radiation_avg',
         'tekanan': 'pressure_avg_hpa', 'angin': 'wind_speed_avg', 'arah': 'wind_direction_name'}
LABELS = dict(REGRESSION_TARGETS)
LABELS[CLASSIFICATION_TARGET] = 'Arah Mata Angin'
UNITS = {'temp_avg': '°C', 'humidity_avg': '%', 'rainfall_total_mm': 'mm', 'solar_radiation_avg': 'W/m²',
         'pressure_avg_hpa': 'hPa', 'wind_speed_avg': 'km/h'}
ORDER = list(REGRESSION_TARGETS) + [CLASSIFICATION_TARGET]

ap = argparse.ArgumentParser(description='Demo performa model NusaKlim per indikator dan horizon')
ap.add_argument('--indikator', default='semua', help='suhu,kelembapan,hujan,radiasi,tekanan,angin,arah (boleh beberapa, pisahkan koma) atau semua')
ap.add_argument('--horizon', default='semua', help='contoh: 1 atau 1,7 atau semua')
ap.add_argument('--hanya-stasiun', default=None, help='hitung performa hanya pada data uji satu stasiun (mis. 222)')
ap.add_argument('--stasiun', default='222', help='stasiun untuk contoh ramalan 7 hari (default 222)')
ap.add_argument('--cepat', action='store_true', help='pakai metrik yang tersimpan di model (tanpa hitung ulang)')
ap.add_argument('--tanpa-ramalan', action='store_true', help='lewati contoh ramalan 7 hari')
args = ap.parse_args()

if args.indikator == 'semua':
    selected = ORDER
else:
    selected = []
    for tok in args.indikator.split(','):
        tok = tok.strip().lower()
        key = ALIAS.get(tok, tok)
        if key not in ORDER:
            sys.exit(f'Indikator tidak dikenal: {tok}. Pilihan: {", ".join(ALIAS)} atau semua')
        selected.append(key)
horizons = list(range(1, 8)) if args.horizon == 'semua' else [int(x) for x in args.horizon.split(',')]
if any(h < 1 or h > 7 for h in horizons):
    sys.exit('Horizon harus antara 1 dan 7')

out = []          # baris Markdown / teks yang sama dengan tampilan layar


def emit(line=''):
    print(line)
    out.append(line)


def md_table(headers, rows):
    emit('| ' + ' | '.join(headers) + ' |')
    emit('|' + '|'.join(['---'] * len(headers)) + '|')
    for r in rows:
        emit('| ' + ' | '.join(str(c) for c in r) + ' |')
    emit()


started = datetime.now()
emit('# Demo Performa Model NusaKlim')
emit()
emit(f'Dijalankan: {started.strftime("%Y-%m-%d %H:%M:%S")}  ')
emit(f'Perintah: `python demo_performa_model.py {" ".join(sys.argv[1:])}`'.rstrip() + '  ')

# ------------------------------------------------------------------ 1. info model
bundle_path = os.path.join(MODEL_DIR, 'weather_model_latest.joblib')
bundle = joblib.load(bundle_path)
models, feature_cols, target_cols, algo_used = bundle['models'], bundle['feature_cols'], bundle['target_cols'], bundle['algo_used']
_n_train = f'{bundle["train_samples"]:,}'.replace(',', '.')
emit(f'Model: `models/weather_model_latest.joblib` (dilatih {bundle["timestamp"]}, {_n_train} baris latih)  ')
emit()
emit('## 1. Algoritma yang dipakai per indikator')
emit()
md_table(['Indikator', 'Algoritma produksi'], [[f'{LABELS[v]}', algo_used[f'{v}_h1']] for v in ORDER])

# ------------------------------------------------------------------ 2. fitur
emit(f'## 2. Fitur input model ({len(feature_cols)} fitur)')
emit()
groups = {'Lag 1/3/7 hari (nilai hari-hari sebelumnya)': [], 'Rata-rata 7 hari terakhir': [], 'Dinamika tekanan & suhu': [],
          'Day of the Year (sin/cos)': [], 'Langsung dari dataset (tidak dihitung ulang)': []}
for c in feature_cols:
    if '_lag' in c:
        groups['Lag 1/3/7 hari (nilai hari-hari sebelumnya)'].append(c)
    elif c.endswith('roll_mean7'):
        groups['Rata-rata 7 hari terakhir'].append(c)
    elif c in ('delta_pressure_1d', 'temp_range'):
        groups['Dinamika tekanan & suhu'].append(c)
    elif c in ('sin_doy', 'cos_doy'):
        groups['Day of the Year (sin/cos)'].append(c)
    else:
        groups['Langsung dari dataset (tidak dihitung ulang)'].append(c)
md_table(['Kelompok', 'Jumlah', 'Nama kolom'], [[g, len(v), ', '.join(f'`{x}`' for x in v)] for g, v in groups.items()])

# ------------------------------------------------------------------ 3. data uji + 4. performa
rows_csv = []
if args.cepat:
    emit('## 3. Performa model produksi (metrik tersimpan di model, mode --cepat)')
    emit()
    metrics = bundle['metrics']
    for var in selected:
        emit(f'### {LABELS[var]}  —  {algo_used[f"{var}_h1"]}')
        emit()
        if var == CLASSIFICATION_TARGET:
            md_table(['Horizon', 'Accuracy', 'F1-Macro', 'n uji'], [[f'H+{h}', f'{metrics[f"{var}_h{h}"]["Accuracy"] * 100:.1f}%',
                     f'{metrics[f"{var}_h{h}"]["F1_Macro"] * 100:.1f}%', metrics[f'{var}_h{h}']['n_test']] for h in horizons])
            for h in horizons:
                m = metrics[f'{var}_h{h}']
                rows_csv.append({'indikator': LABELS[var], 'horizon': f'H+{h}', 'algoritma': algo_used[f'{var}_h{h}'], 'n_uji': m['n_test'],
                                 'accuracy': m['Accuracy'], 'f1_macro': m['F1_Macro']})
        else:
            md_table(['Horizon', f'MAE ({UNITS[var]})', f'RMSE ({UNITS[var]})', 'R²', 'n uji'], [[f'H+{h}', f'{metrics[f"{var}_h{h}"]["MAE"]:.3f}',
                     f'{metrics[f"{var}_h{h}"]["RMSE"]:.3f}', f'{metrics[f"{var}_h{h}"]["R2"]:.3f}', metrics[f'{var}_h{h}']['n_test']] for h in horizons])
            for h in horizons:
                m = metrics[f'{var}_h{h}']
                rows_csv.append({'indikator': LABELS[var], 'horizon': f'H+{h}', 'algoritma': algo_used[f'{var}_h{h}'], 'n_uji': m['n_test'],
                                 'mae': m['MAE'], 'rmse': m['RMSE'], 'r2': m['R2']})
    df_featured = None
else:
    print('\n[1/3] Membangun fitur dari data harian ...')
    df_daily = pd.read_csv(DATA_PATH)
    df_featured, fcols, tcols, ttypes = build_features_and_targets(df_daily)
    assert fcols == feature_cols, 'Fitur data tidak cocok dengan model - jalankan retrain_pipeline.py'
    max_date = df_featured['date_dt'].max()
    split_date = max_date - pd.Timedelta(days=30)
    train_df = df_featured[df_featured['date_dt'] <= split_date]
    test_df = df_featured[df_featured['date_dt'] > split_date]
    if args.hanya_stasiun:
        test_df = test_df[test_df['stnname'].astype(str) == str(args.hanya_stasiun)]
        if test_df.empty:
            sys.exit(f'Stasiun {args.hanya_stasiun} tidak punya data uji.')
    emit()
    emit('## 3. Data uji (tidak pernah dilihat model saat latihan)')
    emit()
    emit(f'- Periode uji: **{(split_date + pd.Timedelta(days=1)).date()} s/d {max_date.date()}** (30 hari terakhir)')
    emit(f'- Cakupan: **{"stasiun " + str(args.hanya_stasiun) if args.hanya_stasiun else str(test_df["stnname"].nunique()) + " stasiun"}**, {len(test_df):,} baris stasiun-hari'.replace(',', '.'))
    emit('- Cara menghitung: model memprediksi nilai H+n dari kondisi hari ini; hasilnya dibandingkan dengan nilai aktual sensor AWS n hari kemudian.')
    emit('- **Pembanding sederhana (persistence):** menebak bahwa besok sama dengan hari ini. Model yang baik harus lebih baik dari tebakan ini.')
    emit()
    emit('## 4. Performa model produksi per indikator dan horizon')
    emit()
    print('[2/3] Menghitung performa tiap indikator dan horizon...')
    for var in selected:
        emit(f'### {LABELS[var]}  —  {algo_used[f"{var}_h1"]}')
        emit()
        tab = []
        for h in horizons:
            key = f'{var}_h{h}'
            tcol = tcols[key]
            sub = test_df.dropna(subset=feature_cols + [tcol, var])
            if var == CLASSIFICATION_TARGET:
                sub = sub[sub[tcol].isin(['Utara', 'Timur', 'Selatan', 'Barat']) & sub[var].isin(['Utara', 'Timur', 'Selatan', 'Barat'])]
            if sub.empty:
                tab.append([f'H+{h}', '-', '-', '-', '-', '-', 0])
                continue
            pred = models[key].predict(sub[feature_cols])
            if var == CLASSIFICATION_TARGET:
                y = sub[tcol].astype(str)
                pred = pd.Series(pred).astype(str).values
                acc, f1 = accuracy_score(y, pred), f1_score(y, pred, average='macro')
                base_acc = accuracy_score(y, sub[var].astype(str))
                train_major = train_df[tcols[f'{var}_h1']].dropna().mode().iloc[0]
                maj_acc = float((y == train_major).mean())
                tab.append([f'H+{h}', f'{acc * 100:.1f}%', f'{f1 * 100:.1f}%', f'{base_acc * 100:.1f}%', f'{maj_acc * 100:.1f}% ({train_major})', '', len(sub)])
                rows_csv.append({'indikator': LABELS[var], 'horizon': f'H+{h}', 'algoritma': algo_used[key], 'n_uji': len(sub), 'accuracy': round(acc, 4),
                                 'f1_macro': round(f1, 4), 'accuracy_persistence': round(base_acc, 4), 'accuracy_kelas_mayoritas': round(maj_acc, 4)})
            else:
                y = sub[tcol]
                if var == 'rainfall_total_mm':
                    pred = np.clip(pred, 0, None)
                mae = mean_absolute_error(y, pred)
                rmse = float(np.sqrt(mean_squared_error(y, pred)))
                r2 = r2_score(y, pred) if len(sub) > 1 else float('nan')
                base_mae = mean_absolute_error(y, sub[var])
                gain = (1 - mae / base_mae) * 100 if base_mae > 0 else float('nan')
                tab.append([f'H+{h}', f'{mae:.3f}', f'{rmse:.3f}', f'{r2:.3f}', f'{base_mae:.3f}', f'{gain:+.0f}%', len(sub)])
                rows_csv.append({'indikator': LABELS[var], 'horizon': f'H+{h}', 'algoritma': algo_used[key], 'n_uji': len(sub), 'mae': round(mae, 4),
                                 'rmse': round(rmse, 4), 'r2': round(r2, 4), 'mae_persistence': round(base_mae, 4), 'perbaikan_vs_persistence_pct': round(gain, 1)})
        if var == CLASSIFICATION_TARGET:
            md_table(['Horizon', 'Accuracy', 'F1-Macro', 'Accuracy persistence', 'Accuracy kelas mayoritas', '', 'n uji'], tab)
        else:
            md_table(['Horizon', f'MAE ({UNITS[var]})', f'RMSE ({UNITS[var]})', 'R²', f'MAE persistence ({UNITS[var]})', 'Perbaikan vs persistence', 'n uji'], tab)
        if var != CLASSIFICATION_TARGET:
            emit('MAE/RMSE: makin kecil makin baik. R²: 1 = sempurna, 0 = sama dengan menebak rata-rata, negatif = lebih buruk dari menebak rata-rata. '
                 '"Perbaikan vs persistence" positif berarti model lebih baik dari tebakan "besok sama dengan hari ini".')
            emit()

# ------------------------------------------------------------------ 5. perbandingan algoritma
bench_path = os.path.join(BASE_DIR, 'benchmark_merged_5algo_h1_h7.json')
if os.path.exists(bench_path):
    bdf = pd.DataFrame(json.load(open(bench_path, encoding='utf-8')))
    emit('## 5. Perbandingan algoritma (benchmark H+1 dan H+7)')
    emit()
    emit('Sumber: `benchmark_merged_5algo_h1_h7.json` (3 algoritma ML dari Laporan 3 + LSTM/GRU dari eksperimen Deep Learning). '
         'Hanya ML yang dipakai produksi; LSTM/GRU bersifat indikatif.')
    emit()
    for var in selected:
        sub = bdf[bdf['Variabel'] == var]
        if sub.empty:
            continue
        emit(f'### {LABELS[var]}')
        emit()
        if var == CLASSIFICATION_TARGET:
            md_table(['Algoritma', 'Horizon', 'Accuracy', 'F1-Macro'], [[r['Algoritma'], r['Horizon'], f'{r["Accuracy"] * 100:.1f}%', f'{r["F1_Macro"] * 100:.1f}%']
                                                                          for _, r in sub.sort_values(['Horizon', 'Algoritma']).iterrows()])
        else:
            md_table(['Algoritma', 'Horizon', f'MAE ({UNITS[var]})', f'RMSE ({UNITS[var]})', 'R²'], [[r['Algoritma'], r['Horizon'], f'{r["MAE"]:.3f}', f'{r["RMSE"]:.3f}', f'{r["R2"]:.3f}']
                                                                                                    for _, r in sub.sort_values(['Horizon', 'MAE']).iterrows()])

# ------------------------------------------------------------------ 6. fitur terpenting
imp_path = os.path.join(BASE_DIR, 'figures_model', 'permutation_importance_h1.json')
if os.path.exists(imp_path):
    imp = json.load(open(imp_path, encoding='utf-8'))
    emit('## 6. Lima fitur paling berpengaruh per indikator (H+1, permutation importance)')
    emit()
    md_table(['Indikator', 'Lima fitur teratas'], [[LABELS[v], ', '.join(f'`{k}`' for k, _ in sorted(imp[f'{v}_h1'].items(), key=lambda kv: -kv[1])[:5])]
                                                    for v in selected if f'{v}_h1' in imp])

# ------------------------------------------------------------------ 7. contoh ramalan
if not args.tanpa_ramalan:
    emit(f'## 7. Contoh ramalan 7 hari, stasiun {args.stasiun}')
    emit()
    print('[3/3] Membuat contoh ramalan 7 hari...')
    _real_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')       # fungsi ramalan mencetak tabelnya sendiri; kita cetak versi Markdown
    try:
        fc = generate_7day_forecast(args.stasiun, df_featured=df_featured)
    finally:
        sys.stdout.close()
        sys.stdout = _real_stdout
    md_table(list(fc.columns), fc.values.tolist())

emit(f'_Selesai dalam {(datetime.now() - started).total_seconds():.0f} detik._')

# ------------------------------------------------------------------ simpan
out_dir = os.path.join(BASE_DIR, 'logs', 'demo')
os.makedirs(out_dir, exist_ok=True)
stamp = started.strftime('%Y%m%d_%H%M%S')
md_path = os.path.join(out_dir, f'performa_model_{stamp}.md')
with open(md_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(out) + '\n')
paths = [md_path]
if rows_csv:
    csv_path = os.path.join(out_dir, f'performa_model_{stamp}.csv')
    pd.DataFrame(rows_csv).to_csv(csv_path, index=False, encoding='utf-8-sig')   # utf-8-sig agar terbaca benar di Excel
    paths.append(csv_path)
print('\nHasil disimpan di:')
for p in paths:
    print('  ' + p)
