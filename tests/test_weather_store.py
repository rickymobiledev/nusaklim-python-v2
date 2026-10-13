"""Integration tests use a disposable PostgreSQL schema, never production tables."""
import importlib
import os
from pathlib import Path
import tempfile
import unittest
import uuid
import sys
from types import ModuleType
from unittest.mock import patch

import pandas as pd
import psycopg
from psycopg import sql

with patch.dict(os.environ, {"NUSAKLIM_WEATHER_API_KEY": "test-key"}):
    store = importlib.import_module("api.weather_store")


@unittest.skipUnless(os.environ.get("NUSAKLIM_TEST_DATABASE_URL"), "Set NUSAKLIM_TEST_DATABASE_URL for PostgreSQL tests")
class WeatherStoreTests(unittest.TestCase):
    def setUp(self):
        self.url = os.environ["NUSAKLIM_TEST_DATABASE_URL"]
        self.schema = "test_weather_" + uuid.uuid4().hex
        with psycopg.connect(self.url) as conn:
            conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(self.schema)))
        self.addCleanup(self.drop_schema)
        self.settings_patch = patch.multiple(store.settings, storage_backend="postgres", database_url=self.url)
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)
        self.connect_patch = patch.object(store, "connect", self.db_connect)
        self.connect_patch.start()
        self.addCleanup(self.connect_patch.stop)
        with self.db_connect() as conn:
            store.initialize(conn)

    def db_connect(self):
        return psycopg.connect(self.url, options=f"-c search_path={self.schema}")

    def drop_schema(self):
        with psycopg.connect(self.url) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(self.schema)))

    def count_raw(self):
        with self.db_connect() as conn:
            return conn.execute("SELECT count(*) FROM weather_raw").fetchone()[0]

    def test_import_duplicates_late_data_and_missing_sensors(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "history.csv"
            pd.DataFrame([
                dict(stnname="001", utctime="1787136600.0", tempout="---"),
                dict(stnname="001", utctime="1787136600", tempout="99"),
            ]).reindex(columns=store.RAW_COLUMNS).to_csv(path, index=False)
            result = store.import_raw_csv(path, chunk_size=1)
            self.assertEqual(result["rows_added"], 1)
            self.assertEqual(store.import_raw_csv(path)["rows_added"], 0)
        result = store.ingest_records([
            dict(stnname="001", utctime=1787136600, tempout=100),
            dict(stnname="001", utctime=1787136000, humout=80),
            dict(stnname="002", utctime=1787136600),
            dict(stnname="002", utctime=1787136600),
        ])
        self.assertEqual(result["rows_added"], 2)
        self.assertEqual(result["rows_skipped"], 2)
        chunks = list(store.iter_raw_chunks(chunk_size=1))
        self.assertEqual(sum(len(c) for c in chunks), 3)
        frame = pd.concat(chunks)
        first = frame[(frame.stnname == "001") & (frame.utctime == "1787136600")].iloc[0]
        self.assertEqual(first.tempout, "---")
        self.assertTrue(pd.isna(first.humout))

    def test_import_failure_rolls_back_earlier_batches(self):
        def broken_batches():
            yield [dict(stnname="rollback", utctime=1787136600)]
            raise ValueError("bad second batch")
        with self.assertRaises(ValueError):
            store._ingest_batches(broken_batches())
        self.assertEqual(self.count_raw(), 0)

    def test_replace_rejected_without_changing_history(self):
        store.ingest_records([dict(stnname="001", utctime=1787136600)])
        with self.assertRaises(store.UploadValidationError):
            store.ingest_records([], "replace")
        self.assertEqual(self.count_raw(), 1)

    def test_cleaning_database_matches_csv(self):
        from process_nusaklim import run_nusaklim_pipeline
        records = [dict(stnname="001", utctime=1787136600 + i * 600,
                        tempout=80, humout=70, bar=29.8, solar=100, rain15=0.1,
                        windspd=5, winddir=90) for i in range(5)]
        store.ingest_records(records)
        with tempfile.TemporaryDirectory() as root:
            raw_path = Path(root) / "raw.csv"
            daily_path = Path(root) / "daily.csv"
            pd.DataFrame(records).to_csv(raw_path, index=False)
            csv_result = run_nusaklim_pipeline(str(raw_path), str(daily_path), root,
                                               chunk_size=2, storage_backend="csv")
            db_result = run_nusaklim_pipeline(figures_output_dir=root, chunk_size=2,
                                              storage_backend="postgres")
            pd.testing.assert_frame_equal(csv_result, db_result)
        daily = store.load_daily()
        pd.testing.assert_frame_equal(daily, db_result, check_dtype=False)
        with self.assertRaises(ValueError):
            store.save_daily(daily.iloc[:0])
        self.assertEqual(len(store.load_daily()), 1)

    def test_daily_failed_write_keeps_previous_snapshot(self):
        row = dict.fromkeys(store.DAILY_COLUMNS, 1.0)
        row.update(stnname="001", date="2026-08-19", wind_direction_name="Timur", records_count=10)
        original = pd.DataFrame([row])
        store.save_daily(original)
        invalid = original.copy()
        invalid["date"] = "invalid-date"
        with self.assertRaises(ValueError):
            store.save_daily(invalid)
        pd.testing.assert_frame_equal(store.load_daily(), original, check_dtype=False)

    def test_json_endpoint_persists_before_background_and_releases_lock(self):
        from fastapi.testclient import TestClient
        from unittest.mock import Mock
        forecast_stub = ModuleType("api.forecast_service")
        forecast_stub.engine = Mock()
        with patch.dict(sys.modules, {"api.forecast_service": forecast_stub}):
            main = importlib.import_module("api.main")
        headers = {"X-API-Key": main.settings.weather_api_key}
        client = TestClient(main.app)
        body = {"mode": "append", "records": [{"stnname": "001", "utctime": 1787136600}]}
        def check_saved(*args, **kwargs):
            self.assertEqual(self.count_raw(), 1)
            self.assertEqual(kwargs["trigger"], "api:/ingest/json")
            self.assertEqual(kwargs["ingestion_stats"]["rows_added"], 1)
            return True
        with patch.object(main, "run_pipeline", side_effect=check_saved) as pipeline:
            response = client.post("/api/v1/ingest/json", json=body, headers=headers)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["status"], "Accepted")
            pipeline.assert_called_once()
        self.assertFalse(main._is_training)
        with patch.object(store, "ingest_records", side_effect=RuntimeError("private database URL")):
            response = client.post("/api/v1/ingest/json", json=body, headers=headers)
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("private database URL", response.text)
        self.assertFalse(main._is_training)
        self.assertEqual(client.post("/api/v1/ingest/json", json={**body, "mode": "replace"}, headers=headers).status_code, 400)
        self.assertEqual(client.post("/api/v1/ingest/json", json=body).status_code, 401)

    def test_training_features_and_model_read_database_without_csv(self):
        from retrain_pipeline import build_features_and_targets, build_model_for
        frame = pd.DataFrame([
            {**dict.fromkeys(store.DAILY_COLUMNS, 10.0),
             "stnname": "001", "date": str(date.date()), "wind_direction_name": "Timur",
             "records_count": 100, "temp_avg": 25 + i % 7}
            for i, date in enumerate(pd.date_range("2026-01-01", periods=65))
        ])
        store.save_daily(frame)
        featured, cols, targets, _ = build_features_and_targets(store.load_daily())
        valid = featured.dropna(subset=cols + [targets["temp_avg_h1"]])
        model = build_model_for("Ridge Regression (Linear Baseline)", "regression", cols)
        model.fit(valid[cols], valid[targets["temp_avg_h1"]])
        self.assertEqual(len(model.predict(valid[cols].iloc[-1:])), 1)

    def test_import_and_load_stations(self):
        with tempfile.TemporaryDirectory() as root:
            csv_path = Path(root) / "stations.csv"
            pd.DataFrame([
                dict(id="001", name="PPKS Bukit Sentang", brand="Davis", latitude="3.95", longitude="98.31"),
                dict(id="211", name="PPKS Marihat", brand="Davis", latitude="2.91", longitude="99.09"),
            ]).to_csv(csv_path, index=False)
            res = store.import_stations_csv(csv_path)
            self.assertEqual(res["rows_in_file"], 2)
            self.assertEqual(res["stations_saved"], 2)

            # Idempotency / upsert update
            pd.DataFrame([
                dict(id="001", name="PPKS Bukit Sentang Updated", brand="Davis New", latitude="3.96", longitude="98.32"),
            ]).to_csv(csv_path, index=False)
            res2 = store.import_stations_csv(csv_path)
            self.assertEqual(res2["stations_saved"], 1)

        stations = store.load_stations()
        self.assertEqual(len(stations), 2)
        s001 = stations[stations.id == "001"].iloc[0]
        self.assertEqual(s001["name"], "PPKS Bukit Sentang Updated")
        self.assertEqual(s001["brand"], "Davis New")

    def test_import_stations_validations(self):
        with tempfile.TemporaryDirectory() as root:
            # Missing file
            with self.assertRaises(FileNotFoundError):
                store.import_stations_csv(Path(root) / "nonexistent.csv")

            # Missing required columns
            bad_csv = Path(root) / "bad.csv"
            pd.DataFrame([{"wrong_col": "value"}]).to_csv(bad_csv, index=False)
            with self.assertRaises(ValueError):
                store.import_stations_csv(bad_csv)

    def test_ensure_stations_exist(self):
        with self.db_connect() as conn:
            store.ensure_stations_exist(conn, ["999", "888"])
            count = conn.execute("SELECT count(*) FROM weather_stations WHERE id IN ('999', '888')").fetchone()[0]
            self.assertEqual(count, 2)
            # Idempotent call
            store.ensure_stations_exist(conn, ["999"])
            count2 = conn.execute("SELECT count(*) FROM weather_stations WHERE id IN ('999', '888')").fetchone()[0]
            self.assertEqual(count2, 2)


if __name__ == "__main__":
    unittest.main()
