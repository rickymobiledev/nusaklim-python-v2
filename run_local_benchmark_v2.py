"""
Benchmark Model Individu (Lokal) vs Global: untuk 30 stasiun (sampel acak,
lihat station_sampling.json) x 7 indikator cuaca, membandingkan model yang
dilatih HANYA dari data stasiun itu sendiri ("Lokal") vs model produksi
global yang sama (weather_model_latest.joblib, dilatih dari seluruh 183
stasiun) - Laporan 3b (revisi 01-10-2026).

Desain (revisi Notulen 01-10-2026, menggantikan desain "2 algoritma ML tetap"
sebelumnya):
  - SEJALAN dengan Laporan 3 Tabel 3.3 dan Laporan 4 Bab 3.4: setiap indikator
    punya algoritma juaranya sendiri (mis. Suhu->Ridge, Curah Hujan->LightGBM),
    BUKAN 2 algoritma yang sama dipaksakan ke semua 7 indikator. Algoritma per
    indikator diambil langsung dari bundle['algo_used'] produksi, sehingga
    Laporan 3b konsisten dengan keputusan algoritma produksi yang sebenarnya.
  - Model Global TIDAK dilatih ulang di sini - memakai model produksi yang
    sama persis dari weather_model_latest.joblib (retrain_pipeline.py), hanya
    di-skor ulang pada baris test milik stasiun yang sedang dibahas (apple-to-
    apple: baris test identik dengan yang dipakai model Lokal).
  - Model Lokal dibangun memakai retrain_pipeline.build_model_for() - fungsi
    yang SAMA dipakai pipeline produksi - supaya praproses (one-hot arah angin,
    scaling utk Ridge/Logistic) identik & konsisten, bukan implementasi
    terpisah yang bisa drift dari produksi.
  - DL (LSTM/GRU) tidak diuji ulang di tahap lokal - data per-stasiun jauh
    lebih sedikit (ratusan baris) drpd data gabungan (puluhan ribu baris),
    dan RNN dikenal butuh volume data jauh lebih besar utk generalisasi baik
    (Goodfellow, Bengio & Courville, "Deep Learning", MIT Press 2016, Bab 5 & 11).
"""
import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (mean_absolute_error, mean_squared_error, r2_score, accuracy_score,
                              f1_score, precision_score, recall_score)

BASE_DIR = r'D:\Projects\Kodepanda\Nusaklim\nusaklim'
sys.path.insert(0, BASE_DIR)
from retrain_pipeline import build_features_and_targets, REGRESSION_TARGETS, CLASSIFICATION_TARGET, build_model_for

MIN_TRAIN, MIN_TEST = 60, 5

with open(os.path.join(BASE_DIR, 'station_sampling.json'), encoding='utf-8') as f:
    sampling = json.load(f)

prod_bundle = joblib.load(os.path.join(BASE_DIR, 'models', 'weather_model_latest.joblib'))
feature_cols = prod_bundle['feature_cols']
algo_used = prod_bundle['algo_used']
global_models = prod_bundle['models']

WIND_CLASSES = ['Barat', 'Selatan', 'Timur', 'Utara']
CLASS_TO_IDX = {c: i for i, c in enumerate(WIND_CLASSES)}

print('Algoritma produksi per indikator (dipakai juga sebagai algoritma Model Lokal, H+1):')
indicators = list(REGRESSION_TARGETS.items()) + [(CLASSIFICATION_TARGET, 'Arah Mata Angin')]
for var, label in indicators:
    print(f'  - {var}: {algo_used[f"{var}_h1"]}')

print('\nLoading & building features...')
df_daily = pd.read_csv(os.path.join(BASE_DIR, 'nusaklim_daily_aggregated.csv'))
df, feature_cols_built, target_cols, target_types = build_features_and_targets(df_daily, horizons=[1])
assert feature_cols_built == feature_cols, 'Feature set mismatch vs weather_model_latest.joblib'
df['date_dt'] = pd.to_datetime(df['date'])
# Split 30 hari OOT identik dgn retrain_pipeline.train_and_evaluate() (test_days=30),
# dihitung langsung dari data (bukan dari bundle['max_train_date'] - nama field itu
# sebenarnya menyimpan tanggal observasi terakhir keseluruhan, bukan batas latih/uji).
max_date_all = df['date_dt'].max()
split_date = max_date_all - pd.Timedelta(days=30)
train_mask_all = df['date_dt'] <= split_date
test_mask_all = df['date_dt'] > split_date

results = {'stations': {}, 'excluded': {}, 'algo_used': {k: algo_used[f'{k}_h1'] for k, _ in indicators}}
local_30 = sampling['local_30']

for i, stn in enumerate(local_30):
    sid, sname = stn['stnname'], stn['name']
    print(f'\n[{i+1}/{len(local_30)}] Stasiun {sid} - {sname}')
    df_stn = df[df['stnname'].astype(str) == str(sid)]
    results['stations'][sid] = {'name': sname, 'indicators': {}}

    for var, label in indicators:
        is_clf = var == CLASSIFICATION_TARGET
        algo = algo_used[f'{var}_h1']
        tcol = target_cols[f'{var}_h1']
        stn_train = df_stn[train_mask_all.loc[df_stn.index]].dropna(subset=feature_cols + [tcol])
        stn_test = df_stn[test_mask_all.loc[df_stn.index]].dropna(subset=feature_cols + [tcol])
        if is_clf:
            stn_train = stn_train[stn_train[tcol].isin(WIND_CLASSES)]
            stn_test = stn_test[stn_test[tcol].isin(WIND_CLASSES)]

        if len(stn_train) < MIN_TRAIN or len(stn_test) < MIN_TEST:
            results['excluded'].setdefault(var, []).append({'station': sid, 'n_train': len(stn_train), 'n_test': len(stn_test)})
            continue

        X_train, X_test = stn_train[feature_cols], stn_test[feature_cols]
        y_train_raw, y_test_raw = stn_train[tcol], stn_test[tcol]
        ttype = 'classification' if is_clf else 'regression'

        # LOCAL: dilatih ulang khusus stasiun ini, algoritma = juara produksi indikator ini
        m_local = build_model_for(algo, ttype, feature_cols)
        y_train = y_train_raw.astype(str) if is_clf else y_train_raw
        m_local.fit(X_train, y_train)
        p_local = m_local.predict(X_test)

        # GLOBAL: model produksi yang sama persis, hanya diskor di baris test stasiun ini
        gm = global_models[f'{var}_h1']
        p_global = gm.predict(X_test)

        if is_clf:
            y_test_s = y_test_raw.astype(str)
            entry_local = {'Accuracy': round(accuracy_score(y_test_s, p_local), 4),
                            'Precision_Macro': round(precision_score(y_test_s, p_local, average='macro', zero_division=0), 4),
                            'Recall_Macro': round(recall_score(y_test_s, p_local, average='macro', zero_division=0), 4),
                            'F1_Macro': round(f1_score(y_test_s, p_local, average='macro'), 4)}
            entry_global = {'Accuracy': round(accuracy_score(y_test_s, p_global), 4),
                             'Precision_Macro': round(precision_score(y_test_s, p_global, average='macro', zero_division=0), 4),
                             'Recall_Macro': round(recall_score(y_test_s, p_global, average='macro', zero_division=0), 4),
                             'F1_Macro': round(f1_score(y_test_s, p_global, average='macro'), 4)}
        else:
            entry_local = {'MAE': round(mean_absolute_error(y_test_raw, p_local), 4),
                            'RMSE': round(float(np.sqrt(mean_squared_error(y_test_raw, p_local))), 4),
                            'R2': round(r2_score(y_test_raw, p_local), 4)}
            entry_global = {'MAE': round(mean_absolute_error(y_test_raw, p_global), 4),
                             'RMSE': round(float(np.sqrt(mean_squared_error(y_test_raw, p_global))), 4),
                             'R2': round(r2_score(y_test_raw, p_global), 4)}

        results['stations'][sid]['indicators'][var] = {
            'algo': algo, 'n_train_local': int(len(X_train)), 'n_test': int(len(X_test)),
            'local': entry_local, 'global': entry_global,
        }
        if is_clf:
            print(f'  {var} ({algo}): n_tr={len(X_train)} n_te={len(X_test)} | Local Acc={entry_local["Accuracy"]:.3f} Global Acc={entry_global["Accuracy"]:.3f}')
        else:
            print(f'  {var} ({algo}): n_tr={len(X_train)} n_te={len(X_test)} | Local MAE={entry_local["MAE"]:.3f} Global MAE={entry_global["MAE"]:.3f}')

n_excluded_total = sum(len(v) for v in results['excluded'].values())
out_path = os.path.join(BASE_DIR, 'local_benchmark_v3.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f'\nExcluded (data kurang): {n_excluded_total} kombinasi stasiun x indikator')
print(f'Saved: {out_path}')
