"""
Pengambilan sampel acak stasiun AWS yang punya data observasi, untuk:
  - 10 stasiun (showcase ramalan 7-hari, Laporan 4 - Model Global)
  - 30 stasiun (benchmark lokal vs global, Laporan 3b - Model Individu)

Revisi 2026-10-06 (catatan review Laporan 3b): 30 stasiun untuk Laporan 3b TIDAK lagi
diambil acak dari seluruh stasiun lalu dicek kelengkapannya (yang membuat sebagian gugur
dan n berkurang). Sekarang kelengkapan data dicek DULU untuk seluruh 183 stasiun
(lihat eligible_stations), baru 30 stasiun diambil acak (seed=42) dari stasiun yang lolos.

Seed acak dikunci (42) agar sampel dapat direproduksi persis oleh skrip
benchmark lain.
"""
import json
import os
import pandas as pd
import numpy as np

BASE_DIR = r'D:\Projects\Kodepanda\Nusaklim\nusaklim'
SEED = 42


def build_station_roster():
    dev = pd.read_csv(os.path.join(BASE_DIR, 'device_nusaklim.csv'))
    dev['id_norm'] = dev['id'].astype(str).str.lstrip('0')
    df = pd.read_csv(os.path.join(BASE_DIR, 'nusaklim_daily_aggregated.csv'), usecols=['stnname'])
    data_ids = set(df['stnname'].astype(str))
    n_data_stations = df['stnname'].nunique()

    dev = dev[dev['id_norm'].isin(data_ids)].copy()
    n_unmatched = n_data_stations - len(dev)

    roster = dev[['id_norm', 'name', 'latitude', 'longitude']].rename(columns={'id_norm': 'stnname'})
    roster = roster.sort_values('stnname').reset_index(drop=True)
    return roster, n_data_stations, n_unmatched


# Kriteria "data lengkap" untuk Laporan 3b: pada SEMUA 7 indikator (H+1), stasiun punya
# >= MIN_TRAIN_DAYS hari latih (1 tahun penuh = 1 siklus musim) dan >= MIN_TEST_DAYS dari
# 30 hari uji yang valid.
MIN_TRAIN_DAYS = 365
MIN_TEST_DAYS = 25
WIND_CLASSES = ['Barat', 'Selatan', 'Timur', 'Utara']


def eligible_stations():
    import sys
    sys.path.insert(0, BASE_DIR)
    from retrain_pipeline import build_features_and_targets, REGRESSION_TARGETS, CLASSIFICATION_TARGET
    df_daily = pd.read_csv(os.path.join(BASE_DIR, 'nusaklim_daily_aggregated.csv'))
    d, feature_cols, target_cols, _ = build_features_and_targets(df_daily, horizons=[1])
    d['date_dt'] = pd.to_datetime(d['date'])
    split = d['date_dt'].max() - pd.Timedelta(days=30)
    out = {}
    for sid, g in d.groupby('stnname'):
        min_tr, min_te = 10 ** 9, 10 ** 9
        for var in list(REGRESSION_TARGETS) + [CLASSIFICATION_TARGET]:
            t = target_cols[f'{var}_h1']
            ok = g.dropna(subset=feature_cols + [t])
            if var == CLASSIFICATION_TARGET:
                ok = ok[ok[t].isin(WIND_CLASSES)]
            min_tr = min(min_tr, int((ok['date_dt'] <= split).sum()))
            min_te = min(min_te, int((ok['date_dt'] > split).sum()))
        out[str(sid)] = {'min_train': min_tr, 'min_test': min_te,
                         'eligible': min_tr >= MIN_TRAIN_DAYS and min_te >= MIN_TEST_DAYS}
    return out


def random_sample(roster, n, seed=SEED):
    rng = np.random.default_rng(seed)
    idx = rng.choice(roster.index.values, size=min(n, len(roster)), replace=False)
    return roster.loc[idx].sort_values('stnname').reset_index(drop=True)


def main():
    roster, n_data_stations, n_unmatched = build_station_roster()

    sample_10 = random_sample(roster, 10)
    elig = eligible_stations()
    roster_elig = roster[roster['stnname'].map(lambda x: elig.get(str(x), {}).get('eligible', False))].reset_index(drop=True)
    sample_30 = random_sample(roster_elig, 30)

    out = {
        'seed': SEED,
        'method': 'Sampel acak sederhana dari seluruh stasiun yang memiliki data, menggunakan numpy Generator(PCG64) seed=42.',
        'n_data_stations_total': int(n_data_stations),
        'n_stations_unmatched_no_device_metadata': int(n_unmatched),
        'n_stations_available': int(len(roster)),
        'n_global_10': 10,
        'n_local_30': 30,
        'local_30_selection': f'Dari {len(roster_elig)} stasiun berdata lengkap (semua 7 indikator: >= {MIN_TRAIN_DAYS} hari latih dan >= {MIN_TEST_DAYS} dari 30 hari uji valid), diambil 30 secara acak (seed=42).',
        'n_eligible_stations': int(len(roster_elig)),
        'criteria': {'min_train_days': MIN_TRAIN_DAYS, 'min_test_days': MIN_TEST_DAYS},
        'global_10': sample_10.to_dict('records'),
        'local_30': sample_30.to_dict('records'),
        'full_roster': roster.to_dict('records'),
    }
    out_path = os.path.join(BASE_DIR, 'station_sampling.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f'Total stasiun dgn data: {n_data_stations} | tanpa metadata: {n_unmatched} | tersedia: {len(roster)}')
    print('\n=== Sampel 10 stasiun (Laporan 4 - showcase ramalan) ===')
    print(sample_10[['stnname', 'name']].to_string(index=False))
    print('\n=== Sampel 30 stasiun (Laporan 3b - benchmark lokal) ===')
    print(sample_30[['stnname', 'name']].to_string(index=False))
    print(f'\nSaved: {out_path}')


if __name__ == '__main__':
    main()
