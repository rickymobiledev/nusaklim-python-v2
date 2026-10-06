# ==============================================================================
# BENCHMARK ALGORITMA (RIDGE VS RANDOM FOREST VS LIGHTGBM) - TARGET CURAH HUJAN
# Dijalankan pada horizon H+1 DAN H+7 untuk mengecek apakah pemenang di H+1
# tetap unggul di H+7 (per catatan review 2026-09-08).
# ==============================================================================
import os, time, json
import numpy as np
import pandas as pd
from datetime import timedelta
import lightgbm as lgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE_DIR = r"D:\Projects\Kodepanda\Nusaklim\nusaklim"
DATA_PATH = os.path.join(BASE_DIR, "nusaklim_daily_aggregated.csv")

from retrain_pipeline import build_features_and_targets

print("Loading data & building features...")
df_daily = pd.read_csv(DATA_PATH)
df_featured, feature_cols, target_cols, target_types = build_features_and_targets(df_daily)

# Drop the categorical column for Ridge/RF (LightGBM handles it natively;
# for a fair apples-to-apples numeric comparison we one-hot the categorical)
cat_cols = ['wind_direction_today_cat']
num_feature_cols = [c for c in feature_cols if c not in cat_cols]
df_ohe = pd.get_dummies(df_featured[feature_cols + ['date_dt']], columns=cat_cols, dummy_na=True)
ohe_feature_cols = [c for c in df_ohe.columns if c != 'date_dt']

max_date = df_featured['date_dt'].max()
split_date = max_date - timedelta(days=30)
train_mask = df_featured['date_dt'] <= split_date
test_mask = df_featured['date_dt'] > split_date

results = []

for h in [1, 7]:
    target_col = target_cols[f'rainfall_total_mm_h{h}']
    y_full = df_featured[target_col]

    valid_train = train_mask & df_featured[feature_cols].notna().all(axis=1) & y_full.notna()
    valid_test = test_mask & df_featured[feature_cols].notna().all(axis=1) & y_full.notna()

    # --- LightGBM (native categorical) ---
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
    results.append({
        'Horizon': f'H+{h}', 'Algoritma': 'LightGBM (Gradient Boosting)',
        'MAE': mean_absolute_error(y_test, p_lgb), 'RMSE': np.sqrt(mean_squared_error(y_test, p_lgb)),
        'R2': r2_score(y_test, p_lgb), 'Training_s': round(t_lgb, 2),
    })

    # --- Ridge & Random Forest (numeric one-hot features) ---
    X_train_num = df_ohe.loc[valid_train, ohe_feature_cols].fillna(0)
    X_test_num = df_ohe.loc[valid_test, ohe_feature_cols].fillna(0)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_num)
    X_test_scaled = scaler.transform(X_test_num)

    t0 = time.time()
    m_rd = Ridge(alpha=1.0)
    m_rd.fit(X_train_scaled, y_train)
    t_rd = time.time() - t0
    p_rd = m_rd.predict(X_test_scaled)
    results.append({
        'Horizon': f'H+{h}', 'Algoritma': 'Ridge Regression (Linear Baseline)',
        'MAE': mean_absolute_error(y_test, p_rd), 'RMSE': np.sqrt(mean_squared_error(y_test, p_rd)),
        'R2': r2_score(y_test, p_rd), 'Training_s': round(t_rd, 2),
    })

    t0 = time.time()
    m_rf = RandomForestRegressor(n_estimators=70, max_depth=14, random_state=42, n_jobs=-1)
    m_rf.fit(X_train_num, y_train)
    t_rf = time.time() - t0
    p_rf = m_rf.predict(X_test_num)
    results.append({
        'Horizon': f'H+{h}', 'Algoritma': 'Random Forest (Ensemble Bagging)',
        'MAE': mean_absolute_error(y_test, p_rf), 'RMSE': np.sqrt(mean_squared_error(y_test, p_rf)),
        'R2': r2_score(y_test, p_rf), 'Training_s': round(t_rf, 2),
    })

    print(f"Horizon H+{h} done. n_train={len(y_train):,} n_test={len(y_test):,}")

df_res = pd.DataFrame(results)
pd.set_option('display.width', 160)
print("\n=== BENCHMARK CURAH HUJAN (mm): RIDGE vs RANDOM FOREST vs LIGHTGBM @ H+1 & H+7 ===")
print(df_res.to_string(index=False))

out_path = os.path.join(BASE_DIR, "benchmark_algo_h1_h7_rain.json")
df_res.to_json(out_path, orient='records', indent=2)
print(f"\nSaved to {out_path}")
