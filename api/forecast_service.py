# ==============================================================================
# INFERENCE FORECASTING SERVICE & AGRONOMIC ADVISORY ENGINE
# ==============================================================================

import os
import sys
import time
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from api.config import settings
from api.stations_db import get_station_metadata
from api.models_schema import (
    DailyForecastItem, ForecastResponse, StationInfo,
    PhysicalForecastDay, PhysicalForecastData, PhysicalForecastResponse
)

sys.path.insert(0, settings.base_dir)
from retrain_pipeline import build_features_and_targets, REGRESSION_TARGETS, CLASSIFICATION_TARGET

# Day names in Indonesian
DAY_NAMES_ID = {
    0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis", 4: "Jumat", 5: "Sabtu", 6: "Minggu"
}

class ForecastEngine:
    def __init__(self):
        self.bundle = None
        self.df_daily = None
        self.df_featured = None
        self.feature_cols = None
        self.target_cols = None
        self.last_loaded_time = None
        self.temp_min_offset = {}   # per-stasiun: rata-rata historis (temp_avg - temp_min)
        self.temp_max_offset = {}   # per-stasiun: rata-rata historis (temp_max - temp_avg)
        self.temp_min_offset_global = 4.0
        self.temp_max_offset_global = 4.5
        self.rain_tau = 4.83  # skala peluruhan utk peluang hujan dari mm prediksi, lihat _compute_rain_tau()
        self.winddir_deg_map = {}   # (stnname, kategori_kardinal) -> rata-rata historis wind_direction_deg
        self.winddir_deg_global = {'Utara': 0.0, 'Timur': 90.0, 'Selatan': 180.0, 'Barat': 270.0}
        self.load_models()

    def load_models(self):
        print(f"[Engine] Loading Model Bundle from {settings.model_bundle_path}...")
        if os.path.exists(settings.model_bundle_path):
            self.bundle = joblib.load(settings.model_bundle_path)
            self.feature_cols = self.bundle['feature_cols']
            self.last_loaded_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[Engine] Successfully loaded {len(self.bundle['models'])} target model groups.")
        else:
            print("[Warning] Model bundle not found. Inference will run in fallback mode.")

        print(f"[Engine] Loading Daily Aggregated Data from {settings.daily_csv_path}...")
        if os.path.exists(settings.daily_csv_path):
            self.df_daily = pd.read_csv(settings.daily_csv_path)
            self.df_daily['date'] = pd.to_datetime(self.df_daily['date'])
            self.df_daily['stnname'] = self.df_daily['stnname'].astype(str)
            print(f"[Engine] Loaded {len(self.df_daily):,} historical station days.")

            if self.bundle is not None:
                print("[Engine] Building engineered features (lag/rolling/kalender) for inference...")
                self.df_featured, built_cols, self.target_cols, _ = build_features_and_targets(self.df_daily)
                assert built_cols == self.feature_cols, "Feature set mismatch antara model bundle & build_features_and_targets - model perlu di-retrain ulang."
                self.df_featured['stnname'] = self.df_featured['stnname'].astype(str)

                # PENTING (ketahanan model): 4 dari 7 variabel produksi memakai Ridge/
                # Logistic Regression (lihat retrain_pipeline.algo_used), yang BERBEDA
                # dari LightGBM - scikit-learn menolak input NaN secara keras (ValueError),
                # sedangkan LightGBM menangani NaN secara native. Tanpa langkah ini, satu
                # nilai kosong di fitur lag/rolling akan membuat endpoint /forecast gagal
                # total (500 error) untuk Suhu/Kelembapan/Tekanan/Angin pada stasiun yang
                # baru saja mengalami gap data - justru skenario yang paling sering terjadi.
                # Forward-fill per stasiun: isi nilai kosong dengan observasi valid
                # terakhir stasiun itu sendiri (konsisten dengan prinsip "estimasi
                # cadangan saat offline" - Laporan Audit Gap Data Pilar 4).
                numeric_feat_cols = [c for c in self.feature_cols if c != 'wind_direction_today_cat']
                self.df_featured[numeric_feat_cols] = (
                    self.df_featured.groupby('stnname')[numeric_feat_cols].ffill()
                )
                n_still_nan = int(self.df_featured[self.feature_cols].isna().any(axis=1).sum())
                print(f"[Engine] Feature engineering selesai: {len(self.df_featured):,} baris, {len(self.feature_cols)} fitur "
                      f"({n_still_nan:,} baris masih punya fitur kosong setelah forward-fill - stasiun baru tanpa riwayat).")

                # Offset suhu min/max per-stasiun (model produksi tidak punya target temp_min/
                # temp_max tersendiri - lihat retrain_pipeline.REGRESSION_TARGETS) dihitung dari
                # pola historis stasiun ybs, bukan noise acak seperti versi sebelumnya.
                off = self.df_daily.dropna(subset=['temp_avg', 'temp_min', 'temp_max']).copy()
                off['min_off'] = off['temp_avg'] - off['temp_min']
                off['max_off'] = off['temp_max'] - off['temp_avg']
                per_stn = off.groupby('stnname')[['min_off', 'max_off']].mean()
                self.temp_min_offset = per_stn['min_off'].to_dict()
                self.temp_max_offset = per_stn['max_off'].to_dict()
                self.temp_min_offset_global = float(off['min_off'].mean())
                self.temp_max_offset_global = float(off['max_off'].mean())

                # Skala peluruhan utk memetakan prediksi rainfall_total_mm (titik estimasi,
                # bukan probabilitas) menjadi peluang hujan 0-100%: median curah hujan pada
                # hari-hari basah historis (lihat Laporan 2 Bab 6.2) - prediksi di sekitar median
                # ini -> peluang ~63%, mendekati 0mm -> peluang mendekati 0%.
                wet_days = self.df_daily.loc[self.df_daily['rainfall_total_mm'] > 0, 'rainfall_total_mm']
                if len(wet_days) > 0:
                    self.rain_tau = float(wet_days.median())

                # Model produksi hanya mengklasifikasi arah angin ke 4 kategori kardinal
                # (wind_direction_name), bukan derajat kontinu. Untuk memetakan balik ke
                # derajat (dibutuhkan endpoint format fisik /weather), pakai rata-rata
                # SIRKULER (sin/cos, bukan rata-rata aritmatika - salah di sekitar wrap
                # 360/0) derajat historis per stasiun & kategori, konsisten dengan prinsip
                # sirkular yang dipakai di Laporan 2 Bab 6.
                wd = self.df_daily.dropna(subset=['wind_direction_deg', 'wind_direction_name']).copy()
                wd = wd[wd['wind_direction_name'] != '---']
                wd_rad = np.radians(wd['wind_direction_deg'])
                wd['sin_d'] = np.sin(wd_rad)
                wd['cos_d'] = np.cos(wd_rad)

                for (stn, cat), g in wd.groupby(['stnname', 'wind_direction_name']):
                    mean_deg = float(np.degrees(np.arctan2(g['sin_d'].mean(), g['cos_d'].mean())) % 360)
                    self.winddir_deg_map[(stn, cat)] = mean_deg

                for cat, g in wd.groupby('wind_direction_name'):
                    mean_deg = float(np.degrees(np.arctan2(g['sin_d'].mean(), g['cos_d'].mean())) % 360)
                    self.winddir_deg_global[cat] = mean_deg

    def generate_advisory(self, rain_mm: float, rain_prob: int, temp_max: float, rh_avg: float) -> tuple[str, str, str]:
        # Weather Condition & Icon
        if rain_prob >= 70 and rain_mm >= 20.0:
            cond = "Hujan Lebat"
            icon = "rain-heavy"
            adv = "PERINGATAN: Tunda total pemupukan & semprot hama (risiko hanyut tinggi). Waspadai genangan air di jalan kebun."
        elif rain_prob >= 60 or rain_mm >= 10.0:
            cond = "Hujan Sedang"
            icon = "rain-moderate"
            adv = "Tunda pemupukan kimia. Utamakan pemeliharaan drainase piringan dan persiapan jalur angkut TBS."
        elif rain_prob >= 40 or rain_mm >= 1.0:
            cond = "Hujan Ringan"
            icon = "rain-light"
            adv = "Kondisi aman untuk panen TBS & pengangkutan. Pemupukan pagi hari dapat dilaksanakan."
        elif temp_max >= 34.0:
            cond = "Cerah Panas"
            icon = "sun"
            adv = "Suhu tinggi & evaporasi cepat. Optimalkan kastrasi/sanitasi tanaman sawit muda di pagi hari."
        else:
            cond = "Cerah Berawan"
            icon = "cloud-sun"
            adv = "Kondisi mikroklimat sangat optimal untuk seluruh operasional kebun, penyerbukan, dan transportasi TBS."
            
        return cond, icon, adv

    def _rain_probability(self, rain_mm: float) -> int:
        """Peluang hujan diturunkan dari prediksi titik rainfall_total_mm (model tidak
        mengeluarkan probabilitas langsung) via fungsi saturasi monoton: 0mm -> ~0%,
        mendekati median hari basah historis (self.rain_tau) -> ~63%, menuju 100%
        untuk prediksi yang jauh lebih besar."""
        prob = 100.0 * (1.0 - np.exp(-max(0.0, rain_mm) / self.rain_tau))
        return int(np.clip(round(prob), 0, 97))

    def _resolve_inference_context(self, stn_str: str):
        """Cari baris fitur terakhir (lengkap) suatu stasiun untuk jadi titik awal
        peramalan H+1..H+7. Dipakai bersama oleh predict_7_days() & predict_7_days_physical()
        agar logika fallback (stasiun baru/gap data/model belum termuat) tidak terduplikasi."""
        can_predict = self.bundle is not None and self.df_featured is not None
        stn_rows = self.df_featured[self.df_featured['stnname'] == stn_str] if can_predict else pd.DataFrame()

        if can_predict and len(stn_rows) > 0:
            stn_rows = stn_rows.sort_values('date_dt')
            latest_row = stn_rows.iloc[-1:]
            if latest_row[self.feature_cols].isna().any(axis=1).iloc[0]:
                # Fallback langka: forward-fill (load_models) tidak cukup (mis. stasiun
                # baru tanpa riwayat sebelum gap-nya) - pakai observasi lengkap terakhir
                # yang tersedia, bukan memaksakan baris dengan fitur kosong ke predict().
                complete_rows = stn_rows.dropna(subset=self.feature_cols)
                if len(complete_rows) > 0:
                    latest_row = complete_rows.iloc[-1:]
                else:
                    latest_row = stn_rows.iloc[0:0]  # kosongkan - masuk ke jalur fallback statistik
            min_off = self.temp_min_offset.get(stn_str, self.temp_min_offset_global)
            max_off = self.temp_max_offset.get(stn_str, self.temp_max_offset_global)
            if len(latest_row) > 0:
                base_date = pd.to_datetime(latest_row['date_dt'].values[0])
                X = latest_row[self.feature_cols]
                latest_wind = str(latest_row['wind_direction_name'].values[0]) if 'wind_direction_name' in latest_row.columns else 'Selatan'
            else:
                base_date = pd.to_datetime(stn_rows['date_dt'].values[-1])
                X = None
                latest_wind = 'Selatan'
        else:
            # Fallback: stasiun tidak ditemukan di data historis / model belum termuat
            base_date = pd.to_datetime("2026-08-19")
            X = None
            min_off, max_off = self.temp_min_offset_global, self.temp_max_offset_global
            latest_wind = 'Selatan'

        return X, base_date, min_off, max_off, latest_wind

    def predict_7_days(self, station_id: str) -> ForecastResponse:
        stn_str = str(station_id).strip()
        meta = get_station_metadata(stn_str)
        station_info = StationInfo(**meta)

        X, base_date, min_off, max_off, latest_wind = self._resolve_inference_context(stn_str)

        forecast_items = []

        for h in range(1, 8):
            target_date = base_date + timedelta(days=h)
            day_name = DAY_NAMES_ID[target_date.weekday()]

            if X is not None:
                models = self.bundle['models']
                t_avg = round(float(models[f'temp_avg_h{h}'].predict(X)[0]), 2)
                rh_avg = round(float(np.clip(models[f'humidity_avg_h{h}'].predict(X)[0], 0.0, 100.0)), 1)
                rain_mm = round(max(0.0, float(models[f'rainfall_total_mm_h{h}'].predict(X)[0])), 1)
                wind_dir = str(models[f'wind_direction_name_h{h}'].predict(X)[0])
                t_min = round(t_avg - min_off, 2)
                t_max = round(t_avg + max_off, 2)
                rain_prob = self._rain_probability(rain_mm)
            else:
                # Statistik historis nasional sebagai fallback terakhir (bukan simulasi acak)
                t_avg = round(27.4 + float(np.sin(h) * 0.3), 2)
                t_min = round(t_avg - min_off, 2)
                t_max = round(t_avg + max_off, 2)
                rh_avg = round(84.0 + float(np.cos(h) * 2.0), 1)
                rain_mm = 3.5
                rain_prob = self._rain_probability(rain_mm)
                wind_dir = latest_wind

            cond, icon, adv = self.generate_advisory(rain_mm, rain_prob, t_max, rh_avg)

            item = DailyForecastItem(
                horizon=f"H+{h}",
                date=target_date.strftime("%Y-%m-%d"),
                day_name=day_name,
                temp_avg=t_avg,
                temp_min=t_min,
                temp_max=t_max,
                humidity_avg=rh_avg,
                rainfall_total_mm=rain_mm,
                rain_probability_pct=rain_prob,
                weather_condition=cond,
                weather_icon=icon,
                wind_direction=wind_dir,
                agronomic_advisory=adv
            )
            forecast_items.append(item)

        if self.bundle is not None:
            algo_used = self.bundle.get('algo_used', {})
            model_algorithm = f"Multi-Algoritma per Variabel ({', '.join(sorted(set(a.split(' (')[0] for a in algo_used.values())))}) - lihat Laporan 3 Tabel 3.3"
            model_version = f"NusaKlim-v2-{self.bundle.get('timestamp', 'unknown')}"
            mae_temp = self.bundle.get('metrics', {}).get('temp_avg_h1', {}).get('MAE', 0.801)
        else:
            model_algorithm = "Fallback (model bundle tidak termuat)"
            model_version = "NusaKlim-fallback"
            mae_temp = 0.801

        return ForecastResponse(
            station=station_info,
            generated_at_wib=datetime.now().strftime("%Y-%m-%d %H:%M:%S WIB"),
            model_version=model_version,
            model_algorithm=model_algorithm,
            evaluation_mae_temp=mae_temp,
            forecast=forecast_items
        )

    def predict_7_days_physical(self, station_id: str) -> PhysicalForecastResponse:
        """Format alternatif untuk integrasi web existing: nilai fisik mentah
        (suhu/kelembapan/radiasi/hujan/tekanan/angin) tanpa rekomendasi agronomi,
        meniru skema {stationId, stationName, latitude, longitude, forecast[], units}."""
        stn_str = str(station_id).strip()
        meta = get_station_metadata(stn_str)

        X, base_date, _min_off, _max_off, latest_wind = self._resolve_inference_context(stn_str)

        forecast_days = []
        for h in range(1, 8):
            target_date = base_date + timedelta(days=h)

            if X is not None:
                models = self.bundle['models']
                t_avg = float(models[f'temp_avg_h{h}'].predict(X)[0])
                rh_avg = float(np.clip(models[f'humidity_avg_h{h}'].predict(X)[0], 0.0, 100.0))
                rain_mm = max(0.0, float(models[f'rainfall_total_mm_h{h}'].predict(X)[0]))
                solar_raw = max(0.0, float(models[f'solar_radiation_avg_h{h}'].predict(X)[0]))
                press = float(models[f'pressure_avg_hpa_h{h}'].predict(X)[0])
                wind_v = max(0.0, float(models[f'wind_speed_avg_h{h}'].predict(X)[0]))
                wind_cat = str(models[f'wind_direction_name_h{h}'].predict(X)[0])
            else:
                # Statistik historis nasional sebagai fallback terakhir (konsisten dgn predict_7_days)
                t_avg = 27.4 + float(np.sin(h) * 0.3)
                rh_avg = 84.0 + float(np.cos(h) * 2.0)
                rain_mm = 3.5
                solar_raw = 165.0  # rata-rata historis nasional (W/m2)
                press = 1007.0
                wind_v = 0.82
                wind_cat = latest_wind

            wind_deg = self.winddir_deg_map.get(
                (stn_str, wind_cat),
                self.winddir_deg_global.get(wind_cat, 180.0)
            )

            # solar_radiation_avg = rata-rata harian W/m2; energi harian MJ/m2 = W/m2 * 86400 s / 1e6
            radiation_mj = solar_raw * 0.0864

            forecast_days.append(PhysicalForecastDay(
                date=target_date.strftime("%Y-%m-%d"),
                temperature=round(t_avg, 1),
                humidity=round(rh_avg, 1),
                radiation=round(radiation_mj, 2),
                rainfall=round(rain_mm, 1),
                airPressure=round(press, 1),
                windSpeed=round(wind_v, 2),
                windDirectionDeg=round(wind_deg, 0),
            ))

        return PhysicalForecastResponse(
            data=PhysicalForecastData(
                stationId=meta['station_id'],
                stationName=meta['estate_name'],
                latitude=meta['lat'],
                longitude=meta['lon'],
                generatedAt=datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00"),
                dataSource="model" if X is not None else "fallback_statistik",
                forecast=forecast_days,
            )
        )

    def predict_7_days_physical_bulk(self, station_ids: list[str]):
        """Panggilan batch untuk server lain yang menarik banyak stasiun sekaligus -
        kegagalan satu stasiun (ID tidak valid dsb.) tidak menggagalkan stasiun lain."""
        results, errors = [], []
        for sid in station_ids:
            try:
                results.append(self.predict_7_days_physical(sid).data)
            except Exception as e:
                errors.append({"stationId": str(sid), "error": str(e)})
        return results, errors

engine = ForecastEngine()
