# ==============================================================================
# NUSAKLIM AWS - AUTOMATED CONTINUOUS RETRAINING & 7-DAY FORECAST PIPELINE
# Pusat Penelitian Kelapa Sawit (PPKS)
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
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE_DIR = r"d:\Downloads\nusaklim"
DATA_PATH = os.path.join(BASE_DIR, "nusaklim_daily_aggregated.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

# ------------------------------------------------------------------------------
# 1. FEATURE ENGINEERING PIPELINE
# ------------------------------------------------------------------------------
def build_features_and_targets(df_daily, horizons=[1, 2, 3, 4, 5, 6, 7]):
    print("Building temporal lag features and multi-horizon targets...")
    df = df_daily.copy()
    df['date_dt'] = pd.to_datetime(df['date'])
    df = df.sort_values(['stnname', 'date_dt']).reset_index(drop=True)
    
    # 1. Cyclical time features (Monsoon & Seasonality)
    doy = df['date_dt'].dt.dayofyear
    df['sin_doy'] = np.sin(2 * np.pi * doy / 365.25)
    df['cos_doy'] = np.cos(2 * np.pi * doy / 365.25)
    df['month'] = df['date_dt'].dt.month
    
    # 2. Physics & Meteorological interaction features
    df['temp_range'] = df['temp_max'] - df['temp_min']
    df['hum_deficit'] = 100.0 - df['humidity_avg']
    
    # 3. Lag features per station
    feature_cols = ['sin_doy', 'cos_doy', 'month', 'temp_range', 'hum_deficit']
    base_vars = ['temp_avg', 'temp_min', 'temp_max', 'humidity_avg', 'pressure_avg_hpa', 
                 'rainfall_total_mm', 'solar_radiation_total', 'wind_speed_avg']
    
    for var in base_vars:
        for lag in [1, 2, 3, 7]:
            col_name = f"{var}_lag{lag}"
            df[col_name] = df.groupby('stnname')[var].shift(lag)
            feature_cols.append(col_name)
            
        # Rolling stats (3-day and 7-day moving averages)
        df[f"{var}_roll_mean3"] = df.groupby('stnname')[var].shift(1).rolling(3, min_periods=1).mean().values
        df[f"{var}_roll_mean7"] = df.groupby('stnname')[var].shift(1).rolling(7, min_periods=1).mean().values
        feature_cols.extend([f"{var}_roll_mean3", f"{var}_roll_mean7"])
        
    # Pressure difference (Barometric trend drop is storm indicator)
    df['delta_pressure_1d'] = df['pressure_avg_hpa_lag1'] - df['pressure_avg_hpa_lag2']
    feature_cols.append('delta_pressure_1d')
    
    # Categorical Station ID
    df['stnname_cat'] = df['stnname'].astype('category')
    feature_cols.append('stnname_cat')
    
    # 4. Multi-Horizon Future Targets (H+1 to H+7)
    target_cols = {}
    for h in horizons:
        # Future temperature
        t_col = f"target_temp_h{h}"
        df[t_col] = df.groupby('stnname')['temp_avg'].shift(-h)
        target_cols[f"temp_h{h}"] = t_col
        
        # Future rainfall
        r_col = f"target_rain_h{h}"
        df[r_col] = df.groupby('stnname')['rainfall_total_mm'].shift(-h)
        target_cols[f"rain_h{h}"] = r_col
        
        # Future humidity
        rh_col = f"target_rh_h{h}"
        df[rh_col] = df.groupby('stnname')['humidity_avg'].shift(-h)
        target_cols[f"rh_h{h}"] = rh_col

    return df, feature_cols, target_cols

# ------------------------------------------------------------------------------
# 2. AUTOMATED TRAINING & VALIDATION PIPELINE
# ------------------------------------------------------------------------------
def train_and_evaluate(df_featured, feature_cols, target_cols, test_days=30):
    print(f"\nInitiating automated training (Split: Last {test_days} days as Validation)...")
    max_date = df_featured['date_dt'].max()
    split_date = max_date - timedelta(days=test_days)
    
    train_mask = df_featured['date_dt'] <= split_date
    test_mask = df_featured['date_dt'] > split_date
    
    train_df = df_featured[train_mask]
    test_df = df_featured[test_mask]
    
    print(f"Training records: {len(train_df):,} | Test validation records: {len(test_df):,}")
    
    trained_models = {}
    metrics_summary = {}
    
    for target_key, target_col in target_cols.items():
        # Clean rows with valid features and valid target
        valid_train = train_df.dropna(subset=feature_cols + [target_col])
        valid_test = test_df.dropna(subset=feature_cols + [target_col])
        
        X_train = valid_train[feature_cols]
        y_train = valid_train[target_col]
        X_test = valid_test[feature_cols]
        y_test = valid_test[target_col]
        
        # LightGBM Regressor
        model = lgb.LGBMRegressor(
            n_estimators=150,
            learning_rate=0.05,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=-1,
            n_jobs=-1
        )
        
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        
        mae = mean_absolute_error(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        r2 = r2_score(y_test, preds)
        
        trained_models[target_key] = model
        metrics_summary[target_key] = {
            'MAE': round(mae, 3),
            'RMSE': round(rmse, 3),
            'R2': round(r2, 3)
        }
        
    print("\n=== VALIDATION PERFORMANCE SUMMARY (7-DAY HORIZON) ===")
    print(pd.DataFrame(metrics_summary).T)
    
    # Save Model Bundle with metadata
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    bundle_filename = f"weather_model_bundle_{timestamp_str}.joblib"
    bundle_path = os.path.join(MODEL_DIR, bundle_filename)
    latest_bundle_path = os.path.join(MODEL_DIR, "weather_model_latest.joblib")
    
    model_bundle = {
        'timestamp': timestamp_str,
        'feature_cols': feature_cols,
        'target_cols': target_cols,
        'models': trained_models,
        'metrics': metrics_summary,
        'train_samples': len(train_df),
        'max_train_date': str(max_date.date())
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
        df_featured, _, _ = build_features_and_targets(df_daily)
        
    # Get the latest observation row for this station
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
        
        # Predict parameters
        t_avg = models[f"temp_h{h}"].predict(X_curr)[0]
        rh_avg = models[f"rh_h{h}"].predict(X_curr)[0]
        r_tot = max(0.0, models[f"rain_h{h}"].predict(X_curr)[0])
        
        # Calculate Probability and Condition
        if r_tot < 0.5:
            condition = "? Cerah Berawan"
            prob_rain = int(min(30, max(10, r_tot * 25)))
        elif r_tot < 20.0:
            condition = "??? Hujan Ringan"
            prob_rain = int(min(80, max(55, 50 + r_tot * 1.5)))
        elif r_tot < 50.0:
            condition = "?? Hujan Sedang"
            prob_rain = int(min(90, max(75, 70 + r_tot * 0.4)))
        else:
            condition = "?? Hujan Lebat"
            prob_rain = 95
            
        forecast_rows.append({
            'Day': f"H+{h}",
            'Date': f_date.strftime("%Y-%m-%d (%A)"),
            'Condition': condition,
            'Temp_Avg_C': round(t_avg, 1),
            'Humidity_Avg_Pct': round(rh_avg, 1),
            'Rain_Total_mm': round(r_tot, 1),
            'Rain_Prob_Pct': f"{prob_rain}%"
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
    print(f"Loaded daily dataset: {len(df_daily):,} rows from 184 stations.")
    
    df_featured, feature_cols, target_cols = build_features_and_targets(df_daily)
    model_bundle = train_and_evaluate(df_featured, feature_cols, target_cols, test_days=30)
    
    # Generate test sample forecast for Station 227
    print("\nTesting 7-day inference on Station 227:")
    generate_7day_forecast(station_id="227", df_featured=df_featured)
    
    print(f"\nRETRAINING PIPELINE FINISHED SUCCESSFULLY IN {time.time() - start_time:.2f} SECONDS!")

if __name__ == '__main__':
    execute_retrain_pipeline()
