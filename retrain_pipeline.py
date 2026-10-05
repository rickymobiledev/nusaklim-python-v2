# ==============================================================================
# NUSAKLIM AWS - AUTOMATED CONTINUOUS RETRAINING & 7-DAY FORECAST PIPELINE
# Pusat Penelitian Kelapa Sawit (PPKS)
# ==============================================================================
#
# Target variables (7, per Notulen review 2026-09-08):
#   1. Suhu Rata-rata (temp_avg)            - regresi
#   2. Kelembapan (humidity_avg)             - regresi
#   3. Curah Hujan mm (rainfall_total_mm)    - regresi
#   4. Radiasi Matahari (solar_radiation_avg) - regresi
#   5. Tekanan Udara (pressure_avg_hpa)      - regresi
#   6. Kecepatan Angin (wind_speed_avg)      - regresi
#   7. Arah Mata Angin (wind_direction_name) - klasifikasi 4 kelas
#
# Feature set (29 fitur, revisi Notulen 23-09-2026 - lihat build_features_and_targets):
#   - 6 variabel dasar x (3 lag [1,3,7] + 1 rolling mean 7-hari) = 24
#   - 2 fitur turunan fisis: delta_pressure_1d, temp_range (hum_deficit dihapus - tidak
#     dipakai model per Notulen review)
#   - 2 fitur Day of the Year: sin_doy, cos_doy (DOY mentah dihapus per review - tidak menambah fitur baru)
#   - 1 fitur kategori arah angin hari ini (persistence) - tetap dipakai model, namun
#     tidak lagi didaftarkan pada tabel "rekayasa fitur" laporan (bukan hasil lag/rolling)
#   Total = 24 + 2 + 2 + 1 = 29
#
# Rasional simplifikasi (vs desain awal 55 fitur): rolling 3-hari, lag 2-hari, dan lag
# temp_min/temp_max dihapus karena tumpang tindih secara informasi dengan lag 1/3/7-hari
# dan rolling 7-hari (redundant, meningkatkan risiko overfitting tanpa menambah sinyal -
# prinsip bias-variance / Occam's razor, Hastie/Tibshirani/Friedman "Elements of
# Statistical Learning"; temuan serupa pada kompetisi M5 bahwa GBM dengan fitur
# lag+rolling window yang ringkas mengungguli desain fitur yang berlebihan -
# Makridakis et al. 2022, "The M5 accuracy competition: Results, findings and
# conclusions", International Journal of Forecasting).
#
# Revisi 2026-09-09: fitur identitas stasiun (stnname_cat, categorical embedding
# dari nama/ID 183 AWS) DIHAPUS per catatan review - unique ID mentah bukan
# prediktor fisis dan berisiko menjadi "shortcut" model tanpa makna generalisasi.
# Alternatif pengelompokan wilayah administratif (kecamatan/kabupaten) yang
# diusulkan reviewer belum dapat diimplementasikan karena device_nusaklim.csv
# tidak memiliki kolom tersebut (hanya company_code/company_name - grouping
# korporat/holding kebun, bukan wilayah administratif - dan lat/lon yang belum
# dimanfaatkan). Model revisi ini murni berbasis 29 fitur cuaca/kalender/fisis
# tanpa fitur identitas lokasi apa pun.
# ==============================================================================

import os
import sys
import time
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import lightgbm as lgb
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, f1_score

BASE_DIR = r"D:\Projects\Kodepanda\Nusaklim\nusaklim"
DATA_PATH = os.path.join(BASE_DIR, "nusaklim_daily_aggregated.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

# Base variables used for lag/rolling engineered features (excludes wind_direction_deg:
# circular quantity - averaging/lagging raw degrees is physically invalid, e.g. mean(350,10)=180 is wrong)
BASE_VARS = ['temp_avg', 'humidity_avg', 'pressure_avg_hpa',
             'rainfall_total_mm', 'solar_radiation_avg', 'wind_speed_avg']

REGRESSION_TARGETS = {
    'temp_avg': 'Suhu Rata-rata (°C)',
    'humidity_avg': 'Kelembapan (%)',
    'rainfall_total_mm': 'Curah Hujan (mm)',
    'solar_radiation_avg': 'Radiasi Matahari (W/m²)',
    'pressure_avg_hpa': 'Tekanan Udara (hPa)',
    'wind_speed_avg': 'Kecepatan Angin (km/h)',
}
CLASSIFICATION_TARGET = 'wind_direction_name'  # Arah Mata Angin (Utara/Timur/Selatan/Barat)

CAT_FEATURE = 'wind_direction_today_cat'
BENCHMARK_JSON_PATH = os.path.join(BASE_DIR, "benchmark_algo_allvars_h1_h7.json")

REG_ALGO_ORDER = ['LightGBM (Gradient Boosting)', 'Ridge Regression (Linear Baseline)', 'Random Forest (Ensemble Bagging)']
CLF_ALGO_ORDER = ['LightGBM (Gradient Boosting)', 'Logistic Regression (Linear Baseline)', 'Random Forest (Ensemble Bagging)']

# ------------------------------------------------------------------------------
# CHAMPION ALGORITHM SELECTION (Notulen Poin 12, kriteria direvisi 23-09-2026):
# MAE-terendah SAJA bukan kriteria yang cukup adil - contoh nyata: Tekanan Udara,
# Ridge kalah tipis di MAE tapi unggul di RMSE, R2, DAN waktu latih dibanding
# LightGBM. Kriteria baru untuk regresi: rata-rata peringkat GABUNGAN dari MAE
# (makin kecil makin baik), RMSE (makin kecil makin baik), dan R2 (makin besar
# makin baik), dirata-rata lagi di kedua horizon H+1 & H+7 - algoritma menang
# kalau unggul di mayoritas metrik, bukan cuma MAE. Untuk klasifikasi, kriteria
# tetap F1-Macro (bukan Accuracy) karena kelas "Selatan" mendominasi data.
# Dipakai baik oleh pipeline training produksi di bawah, maupun oleh
# generate_model_pdf.py untuk narasi.
# ------------------------------------------------------------------------------
def multi_metric_rank(sub, horizon_col='Horizon'):
    """sub: baris benchmark satu variabel (semua algoritma & horizon), dengan
    kolom MAE/RMSE/R2. Kembalikan rata-rata peringkat gabungan MAE+RMSE+R2 per
    algoritma (di seluruh horizon yang ada di `sub`), makin kecil makin baik."""
    rank_mae = sub.pivot(index='Algoritma', columns=horizon_col, values='MAE').rank(axis=0)
    rank_rmse = sub.pivot(index='Algoritma', columns=horizon_col, values='RMSE').rank(axis=0)
    rank_r2 = sub.pivot(index='Algoritma', columns=horizon_col, values='R2').rank(axis=0, ascending=False)
    combined = pd.concat([rank_mae, rank_rmse, rank_r2], axis=1)
    return combined.mean(axis=1).sort_values()


def load_champion_algorithms(benchmark_json_path=BENCHMARK_JSON_PATH):
    with open(benchmark_json_path, 'r', encoding='utf-8') as f:
        records = json.load(f)
    df_bench = pd.DataFrame(records)
    df_bench_reg = df_bench[df_bench['Variabel'] != CLASSIFICATION_TARGET]
    df_bench_clf = df_bench[df_bench['Variabel'] == CLASSIFICATION_TARGET]

    champions = {}
    for var in REGRESSION_TARGETS.keys():
        sub = df_bench_reg[df_bench_reg['Variabel'] == var]
        champions[var] = multi_metric_rank(sub).index[0]

    piv_c = df_bench_clf.pivot(index='Algoritma', columns='Horizon', values='F1_Macro')
    avg_rank_c = piv_c.rank(axis=0, ascending=False).mean(axis=1).sort_values()
    champions[CLASSIFICATION_TARGET] = avg_rank_c.index[0]
    return champions


def _make_estimator(algo_name, ttype):
    if algo_name == 'LightGBM (Gradient Boosting)':
        if ttype == 'regression':
            return lgb.LGBMRegressor(n_estimators=150, learning_rate=0.05, num_leaves=31,
                                      subsample=0.8, colsample_bytree=0.8, random_state=42,
                                      verbosity=-1, n_jobs=-1)
        return lgb.LGBMClassifier(n_estimators=150, learning_rate=0.05, num_leaves=31,
                                   subsample=0.8, colsample_bytree=0.8, random_state=42,
                                   verbosity=-1, n_jobs=-1)
    if algo_name == 'Ridge Regression (Linear Baseline)':
        return Ridge(alpha=1.0)
    if algo_name == 'Logistic Regression (Linear Baseline)':
        return LogisticRegression(max_iter=500)
    if algo_name == 'Random Forest (Ensemble Bagging)':
        if ttype == 'regression':
            return RandomForestRegressor(n_estimators=70, max_depth=14, random_state=42, n_jobs=-1)
        return RandomForestClassifier(n_estimators=70, max_depth=14, random_state=42, n_jobs=-1)
    raise ValueError(f"Unknown algorithm: {algo_name}")


def build_model_for(algo_name, ttype, feature_cols):
    """Bangun model/pipeline siap-fit untuk (algoritma, tipe target) tertentu.
    LightGBM menangani fitur kategorikal (CAT_FEATURE) secara native, jadi cukup
    estimator mentah. Ridge & Random Forest butuh one-hot encoding untuk
    CAT_FEATURE (+ scaling khusus untuk Ridge) - dibungkus sklearn Pipeline supaya
    seluruh model di bundle punya antarmuka .predict(X[feature_cols]) yang seragam,
    tanpa perlu logika khusus di generate_7day_forecast().
    """
    estimator = _make_estimator(algo_name, ttype)
    if algo_name == 'LightGBM (Gradient Boosting)':
        return estimator

    numeric_cols = [c for c in feature_cols if c != CAT_FEATURE]
    needs_scaling = algo_name.startswith('Ridge') or algo_name.startswith('Logistic')
    num_transform = StandardScaler() if needs_scaling else 'passthrough'
    pre = ColumnTransformer([
        ('cat', OneHotEncoder(handle_unknown='ignore'), [CAT_FEATURE]),
        ('num', num_transform, numeric_cols),
    ])
    return Pipeline([('pre', pre), ('model', estimator)])


def extract_feature_importance(model, feature_cols):
    """Kembalikan |importance| sebagai pd.Series ber-index feature_cols ASLI,
    baik `model` berupa estimator LightGBM mentah maupun sklearn Pipeline
    (Ridge/Logistic Regression/RandomForest) yang membungkus ColumnTransformer
    one-hot-encoding CAT_FEATURE. Sub-kolom one-hot CAT_FEATURE dijumlahkan
    kembali jadi satu nilai importance CAT_FEATURE supaya tetap sebanding &
    konsisten lintas algoritma untuk narasi/figur Bab 5.
    """
    if isinstance(model, Pipeline):
        pre = model.named_steps['pre']
        est = model.named_steps['model']
        cat_encoder = pre.named_transformers_['cat']
        cat_names = list(cat_encoder.get_feature_names_out([CAT_FEATURE]))
        numeric_cols = [c for c in feature_cols if c != CAT_FEATURE]
        transformed_names = cat_names + numeric_cols

        if hasattr(est, 'coef_'):
            coef = np.asarray(est.coef_)
            raw_imp = np.mean(np.abs(coef), axis=0) if coef.ndim == 2 else np.abs(coef)
        elif hasattr(est, 'feature_importances_'):
            raw_imp = np.asarray(est.feature_importances_)
        else:
            raise ValueError(f"Cannot extract importance from {type(est)}")

        imp = pd.Series(raw_imp, index=transformed_names)
        cat_total = imp[cat_names].sum()
        imp_final = imp.drop(index=cat_names)
        imp_final[CAT_FEATURE] = cat_total
        return imp_final.reindex(feature_cols)

    return pd.Series(model.booster_.feature_importance(importance_type='gain'), index=feature_cols)

def compute_permutation_importance(model, X_test, y_test, ttype, n_repeats=5, random_state=42):
    """Permutation importance pada data uji: penurunan skor (MAE untuk regresi,
    F1-Macro untuk klasifikasi) saat satu kolom fitur diacak. Metode sama untuk
    semua algoritma (LightGBM, Ridge, Random Forest, Logistic Regression), jadi
    nilainya sebanding lintas algoritma. Kembalikan pd.Series (>= 0) ber-index fitur."""
    from sklearn.inspection import permutation_importance
    scoring = 'neg_mean_absolute_error' if ttype == 'regression' else 'f1_macro'
    res = permutation_importance(model, X_test, y_test, scoring=scoring,
                                 n_repeats=n_repeats, random_state=random_state, n_jobs=1)
    return pd.Series(np.clip(res.importances_mean, 0, None), index=X_test.columns)


# ------------------------------------------------------------------------------
# 1. FEATURE ENGINEERING PIPELINE (29 fitur, simetris per variabel)
# ------------------------------------------------------------------------------
def build_features_and_targets(df_daily, horizons=range(1, 8)):
    print("Building temporal lag/rolling features and multi-horizon targets (29 fitur)...")
    df = df_daily.copy()
    df['date_dt'] = pd.to_datetime(df['date'])
    df = df.sort_values(['stnname', 'date_dt']).reset_index(drop=True)

    # Only 4 valid compass categories are usable as classification labels
    df['wind_direction_name'] = df['wind_direction_name'].where(
        df['wind_direction_name'].isin(['Utara', 'Timur', 'Selatan', 'Barat']), np.nan
    )

    # QC: radiasi sudah rata-rata harian W/m2 (nilai mentah sudah difilter 0-2000 di pra-proses);
    # rata-rata harian > 1500 W/m2 tidak masuk akal secara fisika -> NaN.
    df.loc[df['solar_radiation_avg'] > 1500, 'solar_radiation_avg'] = np.nan

    feature_cols = []

    # 1. Day of the Year (sin/cos, Monsoon & seasonality) - 2 features
    #    'month' (integer) intentionally dropped: fully redundant with sin_doy/cos_doy,
    #    adds needless cardinality without new information.
    doy = df['date_dt'].dt.dayofyear
    df['sin_doy'] = np.sin(2 * np.pi * doy / 365.25)
    df['cos_doy'] = np.cos(2 * np.pi * doy / 365.25)
    feature_cols += ['sin_doy', 'cos_doy']

    # 2. Physical interaction feature - 1 feature (hum_deficit dihapus, tidak dipakai model)
    df['temp_range'] = df['temp_max'] - df['temp_min']
    feature_cols += ['temp_range']

    # 3. Lag (1,3,7 hari) + rolling mean 7-hari, simetris untuk 6 variabel dasar - 6*(3+1)=24 features
    for var in BASE_VARS:
        for lag in [1, 3, 7]:
            col_name = f"{var}_lag{lag}"
            df[col_name] = df.groupby('stnname')[var].shift(lag)
            feature_cols.append(col_name)
        roll_col = f"{var}_roll_mean7"
        df[roll_col] = df.groupby('stnname')[var].shift(1).rolling(7, min_periods=1).mean().values
        feature_cols.append(roll_col)

    # Pressure tendency (barometric drop is a storm precursor) - 1 feature
    # NOTE: masih berbasis lag1/lag2 kalender-hari (t-1 minus t-2); lag 2 sengaja
    # dipertahankan hanya di sini meski tidak lagi jadi fitur mandiri di grup Lag.
    df['pressure_avg_hpa_lag2_tmp'] = df.groupby('stnname')['pressure_avg_hpa'].shift(2)
    df['delta_pressure_1d'] = df['pressure_avg_hpa_lag1'] - df['pressure_avg_hpa_lag2_tmp']
    df.drop(columns=['pressure_avg_hpa_lag2_tmp'], inplace=True)
    feature_cols.append('delta_pressure_1d')

    # Current-day wind direction category (persistence signal for direction target) - 1 feature.
    # Tetap dipakai model (tidak dihapus fungsional), tapi TIDAK didaftarkan di tabel
    # "rekayasa fitur" laporan karena ini nilai observasi hari berjalan, bukan hasil
    # rekayasa lag/rolling/turunan.
    df['wind_direction_today_cat'] = df['wind_direction_name'].astype('category')
    feature_cols.append('wind_direction_today_cat')

    assert len(feature_cols) == 29, f"Expected 29 features, got {len(feature_cols)}"

    # 4. Multi-Horizon Future Targets (H+1 to H+7)
    target_cols = {}
    target_types = {}
    for h in horizons:
        for var, _label in REGRESSION_TARGETS.items():
            t_col = f"target_{var}_h{h}"
            df[t_col] = df.groupby('stnname')[var].shift(-h)
            key = f"{var}_h{h}"
            target_cols[key] = t_col
            target_types[key] = 'regression'

        c_col = f"target_{CLASSIFICATION_TARGET}_h{h}"
        df[c_col] = df.groupby('stnname')[CLASSIFICATION_TARGET].shift(-h)
        ckey = f"{CLASSIFICATION_TARGET}_h{h}"
        target_cols[ckey] = c_col
        target_types[ckey] = 'classification'

    return df, feature_cols, target_cols, target_types

# ------------------------------------------------------------------------------
# 2. AUTOMATED TRAINING & VALIDATION PIPELINE
# ------------------------------------------------------------------------------
def train_and_evaluate(df_featured, feature_cols, target_cols, target_types, test_days=30,
                        champion_algorithms=None):
    print(f"\nInitiating automated training (Split: Last {test_days} days as Validation)...")
    max_date = df_featured['date_dt'].max()
    split_date = max_date - timedelta(days=test_days)

    train_mask = df_featured['date_dt'] <= split_date
    test_mask = df_featured['date_dt'] > split_date

    train_df = df_featured[train_mask]
    test_df = df_featured[test_mask]

    print(f"Training records: {len(train_df):,} | Test validation records: {len(test_df):,}")

    if champion_algorithms is None:
        champion_algorithms = load_champion_algorithms()
    print("Algoritma produksi per variabel (juara benchmark, Notulen Poin 12):")
    for var, algo in champion_algorithms.items():
        print(f"  - {var}: {algo}")

    trained_models = {}
    metrics_summary = {}
    algo_used = {}

    for target_key, target_col in target_cols.items():
        ttype = target_types[target_key]
        var = target_key.rsplit('_h', 1)[0]
        algo_name = champion_algorithms[var]

        valid_train = train_df.dropna(subset=feature_cols + [target_col])
        valid_test = test_df.dropna(subset=feature_cols + [target_col])

        X_train = valid_train[feature_cols]
        y_train = valid_train[target_col]
        X_test = valid_test[feature_cols]
        y_test = valid_test[target_col]

        model = build_model_for(algo_name, ttype, feature_cols)

        if ttype == 'regression':
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            metrics_summary[target_key] = {
                'type': 'regression',
                'MAE': round(mean_absolute_error(y_test, preds), 3),
                'RMSE': round(np.sqrt(mean_squared_error(y_test, preds)), 3),
                'R2': round(r2_score(y_test, preds), 3),
                'n_train': len(y_train),
                'n_test': len(y_test),
            }
        else:
            y_train = y_train.astype(str)
            y_test = y_test.astype(str)
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            metrics_summary[target_key] = {
                'type': 'classification',
                'Accuracy': round(accuracy_score(y_test, preds), 3),
                'F1_Macro': round(f1_score(y_test, preds, average='macro'), 3),
                'n_train': len(y_train),
                'n_test': len(y_test),
            }

        trained_models[target_key] = model
        algo_used[target_key] = algo_name

    print("\n=== VALIDATION PERFORMANCE SUMMARY (7-DAY HORIZON, 7 TARGETS) ===")
    print(pd.DataFrame(metrics_summary).T)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    bundle_filename = f"weather_model_bundle_{timestamp_str}.joblib"
    bundle_path = os.path.join(MODEL_DIR, bundle_filename)
    latest_bundle_path = os.path.join(MODEL_DIR, "weather_model_latest.joblib")

    model_bundle = {
        'timestamp': timestamp_str,
        'feature_cols': feature_cols,
        'target_cols': target_cols,
        'target_types': target_types,
        'models': trained_models,
        'metrics': metrics_summary,
        'champion_algorithms': champion_algorithms,
        'algo_used': algo_used,
        'train_samples': len(train_df),
        'max_train_date': str(max_date.date()),
        'split_date': str(split_date.date()),
    }

    joblib.dump(model_bundle, bundle_path)
    joblib.dump(model_bundle, latest_bundle_path)
    print(f"\nModel successfully saved to:")
    print(f"  - Versioned: {bundle_path}")
    print(f"  - Production Latest: {latest_bundle_path}")

    return model_bundle

# ------------------------------------------------------------------------------
# 3. 7-DAY INFERENCE ENGINE
# ------------------------------------------------------------------------------
def generate_7day_forecast(station_id, df_featured=None, bundle_path=None):
    if bundle_path is None:
        bundle_path = os.path.join(MODEL_DIR, "weather_model_latest.joblib")

    bundle = joblib.load(bundle_path)
    models = bundle['models']
    feature_cols = bundle['feature_cols']

    if df_featured is None:
        df_daily = pd.read_csv(DATA_PATH)
        df_featured, _, _, _ = build_features_and_targets(df_daily)

    stn_data = df_featured[df_featured['stnname'].astype(str) == str(station_id)].sort_values('date_dt')
    if stn_data.empty:
        raise ValueError(f"Station ID {station_id} not found in dataset!")

    latest_row = stn_data.iloc[-1:]
    latest_date = latest_row['date_dt'].values[0]
    latest_date_dt = pd.to_datetime(latest_date)

    X_curr = latest_row[feature_cols]

    forecast_rows = []
    for h in range(1, 8):
        f_date = latest_date_dt + timedelta(days=h)

        t_avg = models[f"temp_avg_h{h}"].predict(X_curr)[0]
        rh_avg = models[f"humidity_avg_h{h}"].predict(X_curr)[0]
        r_tot = max(0.0, models[f"rainfall_total_mm_h{h}"].predict(X_curr)[0])
        solar = max(0.0, models[f"solar_radiation_avg_h{h}"].predict(X_curr)[0])
        press = models[f"pressure_avg_hpa_h{h}"].predict(X_curr)[0]
        wind_v = max(0.0, models[f"wind_speed_avg_h{h}"].predict(X_curr)[0])
        wind_dir = models[f"wind_direction_name_h{h}"].predict(X_curr)[0]

        if r_tot < 0.5:
            condition = "Cerah Berawan"
        elif r_tot < 20.0:
            condition = "Hujan Ringan"
        elif r_tot < 50.0:
            condition = "Hujan Sedang"
        else:
            condition = "Hujan Lebat"

        forecast_rows.append({
            'Day': f"H+{h}",
            'Date': f_date.strftime("%Y-%m-%d (%A)"),
            'Condition': condition,
            'Temp_Avg_C': round(t_avg, 1),
            'Humidity_Avg_Pct': round(rh_avg, 1),
            'Rain_Total_mm': round(r_tot, 1),
            'Solar_Wm2': round(solar, 1),
            'Pressure_hPa': round(press, 1),
            'Wind_Speed_kmh': round(wind_v, 1),
            'Wind_Direction': wind_dir,
        })

    df_fc = pd.DataFrame(forecast_rows)
    print(f"\n=== RAMALAN CUACA 7 HARI KE DEPAN: STASIUN AWS {station_id} ===")
    print(f"Titik Awal Observasi: {latest_date_dt.strftime('%Y-%m-%d')}")
    print(df_fc.to_string(index=False))
    return df_fc

# ------------------------------------------------------------------------------
# 4. MAIN RETRAINING EXECUTION CONTROLLER
# ------------------------------------------------------------------------------
def execute_retrain_pipeline():
    start_time = time.time()
    print("=" * 70)
    print("AUTOMATED NUSAKLIM WEATHER MODEL RETRAINING TRIGGERED")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Clean aggregated data not found at {DATA_PATH}. Run process_nusaklim.py first.")

    df_daily = pd.read_csv(DATA_PATH)
    print(f"Loaded daily dataset: {len(df_daily):,} rows from {df_daily['stnname'].nunique()} stations.")

    df_featured, feature_cols, target_cols, target_types = build_features_and_targets(df_daily)
    print(f"Feature count: {len(feature_cols)} | Target count: {len(target_cols)} (7 variabel x 7 horizon)")
    model_bundle = train_and_evaluate(df_featured, feature_cols, target_cols, target_types, test_days=30)

    print("\nTesting 7-day inference on Station 222:")
    generate_7day_forecast(station_id="222", df_featured=df_featured)

    print(f"\nRETRAINING PIPELINE FINISHED SUCCESSFULLY IN {time.time() - start_time:.2f} SECONDS!")
    return model_bundle

if __name__ == '__main__':
    execute_retrain_pipeline()
