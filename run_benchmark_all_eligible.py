"""
Benchmark Model Individu (Lokal) vs Global untuk seluruh stasiun yang eligible
(memiliki data lengkap: >= 365 hari latih dan >= 25 hari uji valid pada 7 indikator).
"""
import os
import sys
import json
import joblib
import time
import numpy as np
import pandas as pd
from sklearn.metrics import (mean_absolute_error, mean_squared_error, r2_score, accuracy_score,
                             f1_score, precision_score, recall_score)

BASE_DIR = r'D:\Projects\Kodepanda\Nusaklim\nusaklim'
sys.path.insert(0, BASE_DIR)
from station_sampling import build_station_roster, eligible_stations
from retrain_pipeline import build_features_and_targets, REGRESSION_TARGETS, CLASSIFICATION_TARGET, build_model_for

def main():
    start_time = time.time()
    prod_bundle = joblib.load(os.path.join(BASE_DIR, 'models', 'weather_model_latest.joblib'))
    feature_cols = prod_bundle['feature_cols']
    algo_used = prod_bundle['algo_used']
    global_models = prod_bundle['models']

    roster, n_data_stns, _ = build_station_roster()
    elig = eligible_stations()
    roster_elig = roster[roster['stnname'].map(lambda x: elig.get(str(x), {}).get('eligible', False))].reset_index(drop=True)
    n_elig = len(roster_elig)
    print(f"Total stasiun data: {n_data_stns} | Stasiun eligible berdata lengkap: {n_elig}")

    print("Building features & targets...")
    df_daily = pd.read_csv(os.path.join(BASE_DIR, 'nusaklim_daily_aggregated.csv'))
    df, feature_cols_built, target_cols, _ = build_features_and_targets(df_daily, horizons=[1])
    assert feature_cols_built == feature_cols

    df['date_dt'] = pd.to_datetime(df['date'])
    max_date_all = df['date_dt'].max()
    split_date = max_date_all - pd.Timedelta(days=30)
    train_mask_all = df['date_dt'] <= split_date
    test_mask_all = df['date_dt'] > split_date

    WIND_CLASSES = ['Barat', 'Selatan', 'Timur', 'Utara']
    indicators = list(REGRESSION_TARGETS.items()) + [(CLASSIFICATION_TARGET, 'Arah Mata Angin')]

    results = {'stations': {}, 'excluded': {}, 'algo_used': {k: algo_used[f'{k}_h1'] for k, _ in indicators}}

    for i, row in roster_elig.iterrows():
        sid, sname = str(row['stnname']), row['name']
        if (i + 1) % 10 == 0 or i == 0 or (i + 1) == n_elig:
            print(f"[{i+1}/{n_elig}] Memproses Stasiun {sid} - {sname}...")
        df_stn = df[df['stnname'].astype(str) == sid]
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

            if len(stn_train) < 60 or len(stn_test) < 5:
                results['excluded'].setdefault(var, []).append({'station': sid, 'n_train': len(stn_train), 'n_test': len(stn_test)})
                continue

            X_train, X_test = stn_train[feature_cols], stn_test[feature_cols]
            y_train_raw, y_test_raw = stn_train[tcol], stn_test[tcol]
            ttype = 'classification' if is_clf else 'regression'

            m_local = build_model_for(algo, ttype, feature_cols)
            y_train = y_train_raw.astype(str) if is_clf else y_train_raw
            m_local.fit(X_train, y_train)
            p_local = m_local.predict(X_test)

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

    out_path = os.path.join(BASE_DIR, 'local_benchmark_v3.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    elapsed = time.time() - start_time
    print(f"\nBenchmark berhasil selesai dalam {elapsed:.1f} detik!")
    print(f"Total stasiun dievaluasi: {len(results['stations'])}")
    print(f"Hasil disimpan di: {out_path}")

if __name__ == '__main__':
    main()

