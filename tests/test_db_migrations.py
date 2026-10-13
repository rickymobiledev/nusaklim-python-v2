"""Migration acceptance tests run only in disposable PostgreSQL schemas."""
import importlib
import os
from pathlib import Path
import tempfile
import unittest
import uuid
from unittest.mock import patch

import pandas as pd
import psycopg
from psycopg import sql


@unittest.skipUnless(
    os.environ.get("NUSAKLIM_TEST_DATABASE_URL"),
    "Set NUSAKLIM_TEST_DATABASE_URL for PostgreSQL migration tests",
)
class PostgresMigrationTests(unittest.TestCase):
    def setUp(self):
        self.url = os.environ["NUSAKLIM_TEST_DATABASE_URL"]
        self.schema = "test_migrations_" + uuid.uuid4().hex
        with psycopg.connect(self.url) as conn:
            conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(self.schema)))
        self.addCleanup(self.drop_schema)
        with patch.dict(os.environ, {"NUSAKLIM_WEATHER_API_KEY": "test-key"}):
            self.migrations = importlib.import_module("api.db_migrations")
            self.store = importlib.import_module("api.weather_store")
            self.cli = importlib.import_module("api.migrate_postgres")
        self.root = tempfile.TemporaryDirectory()
        self.addCleanup(self.root.cleanup)
        settings_patch = patch.multiple(
            self.store.settings, storage_backend="csv", database_url=self.url,
            base_dir=self.root.name,
            raw_csv_path=str(Path(self.root.name) / "raw.csv"),
            daily_csv_path=str(Path(self.root.name) / "daily.csv"),
            device_csv_path=str(Path(self.root.name) / "devices.csv"),
        )
        settings_patch.start()
        self.addCleanup(settings_patch.stop)
        connect_patch = patch.object(self.store, "connect", self.connect)
        connect_patch.start()
        self.addCleanup(connect_patch.stop)

    def connect(self):
        return psycopg.connect(self.url, options=f"-c search_path={self.schema}")

    def drop_schema(self):
        with psycopg.connect(self.url) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(self.schema)))

    def test_status_does_not_create_tables_then_apply_is_idempotent(self):
        with self.connect() as conn:
            statuses = self.migrations.migration_status(conn)
            self.assertTrue(statuses)
            self.assertTrue(all(item["status"] == "pending" for item in statuses))
            self.assertEqual(conn.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema = %s",
                (self.schema,),
            ).fetchone()[0], 0)
            applied = self.migrations.apply_migrations(conn)
            self.assertEqual(applied, [item["version"] for item in statuses])
            conn.execute("INSERT INTO weather_stations (id, name) VALUES ('001', 'Station 001')")
            conn.execute("INSERT INTO weather_raw (stnname, utctime) VALUES ('001', '1787136600')")
        with self.connect() as conn:
            self.assertEqual(self.migrations.apply_migrations(conn), [])
            self.assertEqual(conn.execute("SELECT count(*) FROM weather_raw").fetchone()[0], 1)
            self.assertEqual(conn.execute("SELECT count(*) FROM weather_daily").fetchone()[0], 0)
            recorded = conn.execute(
                "SELECT version, filename, checksum, applied_at FROM nusaklim_schema_migrations ORDER BY version"
            ).fetchall()
            self.assertEqual([row[0] for row in recorded], applied)
            self.assertTrue(all(row[1] and row[2] and row[3] for row in recorded))
            self.assertTrue(all(item["status"] == "applied"
                                for item in self.migrations.migration_status(conn)))

    def test_failed_later_migration_rolls_back_entire_transaction(self):
        directory = Path(self.root.name) / "broken"
        directory.mkdir()
        (directory / "001_create.sql").write_text("CREATE TABLE migration_probe (id integer);", encoding="utf-8")
        (directory / "002_bad.sql").write_text("THIS IS NOT VALID SQL;", encoding="utf-8")
        with self.assertRaises(psycopg.Error):
            with self.connect() as conn:
                self.migrations.apply_migrations(conn, directory=directory)
        with self.connect() as conn:
            self.assertIsNone(conn.execute("SELECT to_regclass('migration_probe')").fetchone()[0])
            self.assertIsNone(conn.execute("SELECT to_regclass('nusaklim_schema_migrations')").fetchone()[0])

    def test_modified_applied_migration_is_rejected(self):
        directory = Path(self.root.name) / "modified"
        directory.mkdir()
        migration = directory / "001_create.sql"
        migration.write_text("CREATE TABLE migration_probe (id integer);", encoding="utf-8")
        with self.connect() as conn:
            self.assertEqual(self.migrations.apply_migrations(conn, directory=directory), ["001"])
        migration.write_text("CREATE TABLE migration_probe (id integer, added text);", encoding="utf-8")
        with self.connect() as conn:
            status = self.migrations.migration_status(conn, directory=directory)
            self.assertEqual(status[0]["status"], "modified")
        with self.assertRaises(ValueError):
            with self.connect() as conn:
                self.migrations.apply_migrations(conn, directory=directory)
        with self.connect() as conn:
            columns = conn.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = 'migration_probe'",
                (self.schema,),
            ).fetchall()
            self.assertEqual(columns, [("id",)])

    def write_history(self):
        raw_path = Path(self.root.name) / "raw.csv"
        pd.DataFrame([
            dict(stnname="001", utctime=1787136600 + i * 600,
                 tempout=80, humout=70, bar=29.8, solar=100,
                 rain15=0.1, windspd=5, winddir=90)
            for i in range(5)
        ]).reindex(columns=self.store.RAW_COLUMNS).to_csv(raw_path, index=False)
        return raw_path

    def test_cli_imports_history_and_daily_when_backend_is_still_csv(self):
        raw_path = self.write_history()
        daily_path = Path(self.root.name) / "daily.csv"
        row = dict.fromkeys(self.store.DAILY_COLUMNS, 10.0)
        row.update(stnname="001", date="2026-08-19", wind_direction_name="Timur", records_count=5)
        pd.DataFrame([row]).to_csv(daily_path, index=False)
        result = self.cli.migrate(raw_csv=raw_path, daily_csv=daily_path, chunk_size=2)
        self.assertTrue(result["migrations"])
        self.assertEqual(result["raw"]["rows_added"], 5)
        self.assertEqual(result["daily_rows"], 1)
        self.assertEqual(result["verification"], dict(stations=1, raw_rows=5, daily_rows=1, raw_stations=1, daily_stations=1))
        repeated = self.cli.migrate(raw_csv=raw_path, daily_csv=daily_path, chunk_size=2)
        self.assertEqual(repeated["migrations"], [])
        self.assertEqual(repeated["raw"]["rows_added"], 0)
        self.assertEqual(repeated["verification"], result["verification"])
        self.assertEqual(self.store.settings.storage_backend, "csv")

    def test_raw_only_import_builds_daily_database_without_training(self):
        raw_path = self.write_history()
        result = self.cli.migrate(raw_csv=raw_path, chunk_size=2)
        self.assertEqual(result["verification"], dict(stations=1, raw_rows=5, daily_rows=1, raw_stations=1, daily_stations=1))
        with self.connect() as conn:
            daily = conn.execute("SELECT stnname, records_count FROM weather_daily").fetchall()
            self.assertEqual(daily, [("001", 5)])

    def test_cli_imports_device_csv(self):
        device_path = Path(self.root.name) / "devices.csv"
        pd.DataFrame([
            dict(id="001", name="PPKS 001", brand="Davis", latitude=3.5, longitude=98.5),
            dict(id="002", name="PPKS 002", brand="Meteo", latitude=2.5, longitude=99.5),
        ]).to_csv(device_path, index=False)
        result = self.cli.migrate(device_csv=device_path)
        self.assertEqual(result["stations"]["stations_saved"], 2)
        self.assertEqual(result["verification"]["stations"], 2)
        with self.connect() as conn:
            stations = self.store.load_stations(conn=conn)
            self.assertEqual(len(stations), 2)
            self.assertEqual(stations.iloc[0]["name"], "PPKS 001")


if __name__ == "__main__":
    unittest.main()
