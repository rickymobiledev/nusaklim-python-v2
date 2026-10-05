# ==============================================================================
# BENCHMARK ALGORITMA PER-VARIABEL (7 TARGET x H+1 & H+7 x 3 ALGORITMA)
# untuk Laporan 3 (Model Prediksi Cuaca 7 Hari). Hasilnya (JSON) dipakai oleh
# retrain_pipeline.load_champion_algorithms() untuk memilih algoritma produksi
# per variabel, dan oleh generate_model_pdf.py untuk narasi Bab 3.
#
# Notulen Review 16-09-2026 & 23-09-2026:
#   - Poin 12: "tabel benchmarking dan seleksi algoritma perlu dibuat untuk
#     masing-masing parameter" (bukan hanya Curah Hujan seperti benchmark lama).
#   - Poin 14: evaluasi klasifikasi arah angin memakai Accuracy/Precision/
#     Recall/F1-score (bukan disamakan dengan metrik regresi).
#   - Baseline linear klasifikasi memakai Logistic Regression, konsisten dengan
#     run_local_benchmark_v2.py (Laporan 3b) dan run_dl_benchmark_h1_h7.py
#     (perbandingan ML vs DL, kini digabung ke Laporan 3 Bab 3.4).
#   - Kriteria juara regresi direvisi 23-09-2026: rata-rata peringkat gabungan
#     MAE+RMSE+R2 (bukan MAE saja) - lihat retrain_pipeline.multi_metric_rank().
#   - Eksperimen fitur Lag 30 hari (dulu ada di sini) dihapus per Notulen
#     23-09-2026 - tidak dipakai sebagai fitur resmi produksi.
# ==============================================================================
import os, time, json
import numpy as np
import pandas as pd
from datetime import timedelta
import lightgbm as lgb
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (mean_absolute_error, mean_squared_error, r2_score,
                              accuracy_score, f1_score, precision_score, recall_score)

BASE_DIR = r"D:\Projects\Kodepanda\Nusaklim\nusaklim"
DATA_PATH = os.path.join(BASE_DIR, "nusaklim_daily_aggregated.csv")

from retrain_pipeline import build_features_and_targets, REGRESSION_TARGETS, CLASSIFICATION_TARGET, BASE_VARS

print("Loading data & building base features (30, resmi produksi)...")
df_daily = pd.read_csv(DATA_PATH)
df_featured, feature_cols, target_cols, target_types = build_features_and_targets(df_daily)
N_FEAT = len(feature_cols)
FITUR_SET_LABEL = f'{N_FEAT} (Resmi)'

cat_cols = ['wind_direction_today_cat']
df_ohe = pd.get_dummies(df_featured[feature_cols + ['date_dt']], columns=cat_cols, dummy_na=True)
ohe_cols_base = [c for c in df_ohe.columns if c != 'date_dt']

max_date = df_featured['date_dt'].max()
split_date = max_date - timedelta(days=30)
train_mask = df_featured['date_dt'] <= split_date
test_mask = df_featured['date_dt'] > split_date


results = []
REG_VARS = list(REGRESSION_TARGETS.keys())
t_start_all = time.time()

# ------------------------------------------------------------------------------
# 1. BENCHMARK REGRESI: 6 variabel x 2 horizon x 3 algoritma (fitur 36 resmi)
# ------------------------------------------------------------------------------
for var in REG_VARS:
    for h in [1, 7]:
        target_col = target_cols[f'{var}_h{h}']
        y_full = df_featured[target_col]

        valid_train = train_mask & df_featured[feature_cols].notna().all(axis=1) & y_full.notna()
        valid_test = test_mask & df_featured[feature_cols].notna().all(axis=1) & y_full.notna()

        X_train_lgb = df_featured.loc[valid_train, feature_cols]
        X_test_lgb = df_featured.loc[valid_test, feature_cols]
        y_train = df_featured.loc[valid_train, target_col]
        y_test = df_featured.loc[valid_test, target_col]

        t0 = time.time()
        m_lgb = lgb.LGBMRegressor(n_estimators=150, learning_rate=0.05, num_leaves=31,
                                   subsample=0.8, colsample_bytree=0.8, random_state=42,
                                   verbosity=-1, n_jobs=-1)
        m_lgb.fit(X_train_lgb, y_train)
        t_lgb = time.time() - t0
        p_lgb = m_lgb.predict(X_test_lgb)
        results.append(dict(Variabel=var, Horizon=f'H+{h}', Algoritma='LightGBM (Gradient Boosting)', FiturSet=FITUR_SET_LABEL,
                             MAE=mean_absolute_error(y_test, p_lgb), RMSE=float(np.sqrt(mean_squared_error(y_test, p_lgb))),
                             R2=r2_score(y_test, p_lgb), Training_s=round(t_lgb, 2)))

        X_train_num = df_ohe.loc[valid_train, ohe_cols_base].fillna(0)
        X_test_num = df_ohe.loc[valid_test, ohe_cols_base].fillna(0)
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train_num)
        X_test_scaled = scaler.transform(X_test_num)

        t0 = time.time()
        m_rd = Ridge(alpha=1.0)
        m_rd.fit(X_train_scaled, y_train)
        t_rd = time.time() - t0
        p_rd = m_rd.predict(X_test_scaled)
        results.append(dict(Variabel=var, Horizon=f'H+{h}', Algoritma='Ridge Regression (Linear Baseline)', FiturSet=FITUR_SET_LABEL,
                             MAE=mean_absolute_error(y_test, p_rd), RMSE=float(np.sqrt(mean_squared_error(y_test, p_rd))),
                             R2=r2_score(y_test, p_rd), Training_s=round(t_rd, 2)))

        t0 = time.time()
        m_rf = RandomForestRegressor(n_estimators=70, max_depth=14, random_state=42, n_jobs=-1)
        m_rf.fit(X_train_num, y_train)
        t_rf = time.time() - t0
        p_rf = m_rf.predict(X_test_num)
        results.append(dict(Variabel=var, Horizon=f'H+{h}', Algoritma='Random Forest (Ensemble Bagging)', FiturSet=FITUR_SET_LABEL,
                             MAE=mean_absolute_error(y_test, p_rf), RMSE=float(np.sqrt(mean_squared_error(y_test, p_rf))),
                             R2=r2_score(y_test, p_rf), Training_s=round(t_rf, 2)))

        print(f"[{var} H+{h}] base-{N_FEAT} 3-algo done. n_train={len(y_train):,} n_test={len(y_test):,} "
              f"elapsed={time.time()-t_start_all:.0f}s")

# ------------------------------------------------------------------------------
# 2. BENCHMARK KLASIFIKASI ARAH ANGIN: 2 horizon x 3 algoritma
#    Metrik: Accuracy, Precision (macro), Recall (macro), F1 (macro) - Notulen Poin 14
# ------------------------------------------------------------------------------
for h in [1, 7]:
    target_col = target_cols[f'{CLASSIFICATION_TARGET}_h{h}']
    y_full = df_featured[target_col]

    valid_train_c = train_mask & df_featured[feature_cols].notna().all(axis=1) & y_full.notna()
    valid_test_c = test_mask & df_featured[feature_cols].notna().all(axis=1) & y_full.notna()

    X_train_lgb = df_featured.loc[valid_train_c, feature_cols]
    X_test_lgb = df_featured.loc[valid_test_c, feature_cols]
    y_train_c = df_featured.loc[valid_train_c, target_col].astype(str)
    y_test_c = df_featured.loc[valid_test_c, target_col].astype(str)

    def clf_row(algo_name, model, X_tr, y_tr, X_te):
        t0 = time.time()
        model.fit(X_tr, y_tr)
        t_fit = time.time() - t0
        preds = model.predict(X_te)
        return dict(Variabel=CLASSIFICATION_TARGET, Horizon=f'H+{h}', Algoritma=algo_name, FiturSet=FITUR_SET_LABEL,
                    Accuracy=accuracy_score(y_test_c, preds),
                    Precision_Macro=precision_score(y_test_c, preds, average='macro', zero_division=0),
                    Recall_Macro=recall_score(y_test_c, preds, average='macro', zero_division=0),
                    F1_Macro=f1_score(y_test_c, preds, average='macro'),
                    Training_s=round(t_fit, 2))

    m_lgb_c = lgb.LGBMClassifier(n_estimators=150, learning_rate=0.05, num_leaves=31,
                                  subsample=0.8, colsample_bytree=0.8, random_state=42,
                                  verbosity=-1, n_jobs=-1)
    results.append(clf_row('LightGBM (Gradient Boosting)', m_lgb_c, X_train_lgb, y_train_c, X_test_lgb))

    X_train_num = df_ohe.loc[valid_train_c, ohe_cols_base].fillna(0)
    X_test_num = df_ohe.loc[valid_test_c, ohe_cols_base].fillna(0)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_num)
    X_test_scaled = scaler.transform(X_test_num)

    m_lr = LogisticRegression(max_iter=500)
    results.append(clf_row('Logistic Regression (Linear Baseline)', m_lr, X_train_scaled, y_train_c, X_test_scaled))

    m_rf_c = RandomForestClassifier(n_estimators=70, max_depth=14, random_state=42, n_jobs=-1)
    results.append(clf_row('Random Forest (Ensemble Bagging)', m_rf_c, X_train_num, y_train_c, X_test_num))

    print(f"[wind_direction_name H+{h}] classification 3-algo done. elapsed={time.time()-t_start_all:.0f}s")

df_res = pd.DataFrame(results)
out_path = os.path.join(BASE_DIR, "benchmark_algo_allvars_h1_h7.json")
df_res.to_json(out_path, orient='records', indent=2)
pd.set_option('display.width', 200)
print(f"\n=== BENCHMARK SELESAI dalam {time.time()-t_start_all:.0f} detik. Disimpan ke {out_path} ===")
print(df_res.to_string(index=False))
