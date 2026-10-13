import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from api.config import Settings
from api.retention import (
    cleanup_model_bundles,
    cleanup_run_logs,
    format_size,
    get_retention_status,
    is_protected_bundle,
    run_all_retention,
)
from scripts.cleanup_retention import main as cli_main


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.tmp_dir.name)
        self.models_dir = self.base_path / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir = self.base_path / "logs" / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _create_bundle(self, filename: str, content: bytes = b"dummy model data", mtime: float | None = None) -> Path:
        path = self.models_dir / filename
        path.write_bytes(content)
        if mtime is not None:
            os.utime(path, (mtime, mtime))
        return path

    def _create_log(self, filename: str, content: str = "dummy log text", mtime: float | None = None) -> Path:
        path = self.runs_dir / filename
        path.write_text(content, encoding="utf-8")
        if mtime is not None:
            os.utime(path, (mtime, mtime))
        return path

    def test_protected_bundle_detection(self):
        self.assertTrue(is_protected_bundle("weather_model_latest.joblib"))
        self.assertTrue(is_protected_bundle("weather_model_latest.sum_backup.joblib"))
        self.assertTrue(is_protected_bundle("weather_model_bundle_20261012.backup.joblib"))
        self.assertTrue(is_protected_bundle(Path("models/model.backup.joblib")))
        self.assertFalse(is_protected_bundle("weather_model_bundle_20261012_100000.joblib"))
        self.assertFalse(is_protected_bundle("weather_model_bundle_20260901_000000.joblib"))

    def test_cleanup_model_bundles_below_limit(self):
        # Create 3 bundles
        for i in range(3):
            self._create_bundle(f"weather_model_bundle_20261010_00000{i}.joblib")

        res = cleanup_model_bundles(models_dir=self.models_dir, keep_count=5)
        self.assertEqual(len(res["deleted"]), 0)
        self.assertEqual(len(res["kept"]), 3)
        self.assertEqual(res["freed_bytes"], 0)
        self.assertEqual(len(list(self.models_dir.glob("weather_model_bundle_*.joblib"))), 3)

    def test_cleanup_model_bundles_exceeding_limit(self):
        # Create 5 versioned bundles with staggered mtimes
        now = time.time()
        for i in range(5):
            self._create_bundle(
                f"weather_model_bundle_20261010_00000{i}.joblib",
                content=b"x" * 100,
                mtime=now + (i * 10),
            )

        # Keep 2 newest
        res = cleanup_model_bundles(models_dir=self.models_dir, keep_count=2)
        self.assertEqual(len(res["kept"]), 2)
        self.assertEqual(len(res["deleted"]), 3)
        self.assertEqual(res["freed_bytes"], 300)

        # Ensure kept files are the newest ones
        self.assertIn("weather_model_bundle_20261010_000004.joblib", res["kept"])
        self.assertIn("weather_model_bundle_20261010_000003.joblib", res["kept"])
        # Ensure deleted files are removed from disk
        remaining = [p.name for p in self.models_dir.glob("weather_model_bundle_*.joblib")]
        self.assertEqual(set(remaining), set(res["kept"]))

    def test_protected_files_never_deleted(self):
        # Create protected files and bundles
        latest = self._create_bundle("weather_model_latest.joblib", content=b"latest" * 100)
        backup = self._create_bundle("weather_model_latest.sum_backup.joblib", content=b"backup" * 100)
        b1 = self._create_bundle("weather_model_bundle_20261010_000001.joblib")
        b2 = self._create_bundle("weather_model_bundle_20261010_000002.joblib")

        # Keep 0 bundles
        res = cleanup_model_bundles(models_dir=self.models_dir, keep_count=0)
        self.assertEqual(len(res["deleted"]), 2)
        self.assertIn(b1.name, res["deleted"])
        self.assertIn(b2.name, res["deleted"])
        self.assertNotIn("weather_model_latest.joblib", res["deleted"])
        self.assertNotIn("weather_model_latest.sum_backup.joblib", res["deleted"])

        # Protected files must remain on disk
        self.assertTrue(latest.exists())
        self.assertTrue(backup.exists())

    def test_cleanup_model_bundles_dry_run(self):
        for i in range(4):
            self._create_bundle(f"weather_model_bundle_20261010_00000{i}.joblib", content=b"z" * 50)

        res = cleanup_model_bundles(models_dir=self.models_dir, keep_count=2, dry_run=True)
        self.assertEqual(len(res["kept"]), 2)
        self.assertEqual(len(res["deleted"]), 2)
        self.assertEqual(res["freed_bytes"], 100)

        # Check all 4 files are still on disk because dry_run=True
        self.assertEqual(len(list(self.models_dir.glob("weather_model_bundle_*.joblib"))), 4)

    def test_cleanup_run_logs(self):
        now = time.time()
        for i in range(6):
            self._create_log(f"ingest-2026101000000{i}.log", content="log line\n", mtime=now + (i * 10))

        # Keep 3 newest, exclude log #0
        res = cleanup_run_logs(runs_dir=self.runs_dir, keep_count=3)
        self.assertEqual(len(res["kept"]), 3)
        self.assertEqual(len(res["deleted"]), 3)
        remaining = [p.name for p in self.runs_dir.glob("*.log")]
        self.assertEqual(len(remaining), 3)

    def test_cleanup_run_logs_with_exclusion(self):
        now = time.time()
        for i in range(4):
            self._create_log(f"run_{i}.log", content="data", mtime=now + (i * 5))

        active_log = "run_1.log"
        res = cleanup_run_logs(runs_dir=self.runs_dir, keep_count=1, exclude_files={active_log})
        self.assertNotIn(active_log, res["deleted"])
        self.assertTrue((self.runs_dir / active_log).exists())

    def test_run_all_retention(self):
        for i in range(5):
            self._create_bundle(f"weather_model_bundle_20261010_00000{i}.joblib", content=b"a" * 10)
        for i in range(5):
            self._create_log(f"task_{i}.log", content="b" * 10)

        res = run_all_retention(
            models_dir=self.models_dir,
            runs_dir=self.runs_dir,
            max_bundles=2,
            max_logs=2,
        )
        self.assertEqual(len(res["models"]["deleted"]), 3)
        self.assertEqual(len(res["logs"]["deleted"]), 3)
        self.assertEqual(res["freed_bytes"], 60)

    def test_get_retention_status(self):
        self._create_bundle("weather_model_latest.joblib", content=b"latest")
        self._create_bundle("weather_model_latest.sum_backup.joblib", content=b"backup")
        for i in range(4):
            self._create_bundle(f"weather_model_bundle_20261010_00000{i}.joblib", content=b"b" * 100)
        for i in range(3):
            self._create_log(f"task_{i}.log", content="log" * 10)

        status = get_retention_status(
            models_dir=self.models_dir,
            runs_dir=self.runs_dir,
            max_bundles=2,
            max_logs=2,
        )
        self.assertEqual(status["models"]["bundle_count"], 4)
        self.assertEqual(status["models"]["excess_count"], 2)
        self.assertEqual(status["models"]["protected_count"], 2)
        self.assertEqual(status["logs"]["log_count"], 3)
        self.assertEqual(status["logs"]["excess_count"], 1)

    def test_cli_status_and_dry_run(self):
        for i in range(3):
            self._create_bundle(f"weather_model_bundle_20261010_00000{i}.joblib", content=b"x" * 50)
        for i in range(2):
            self._create_log(f"task_{i}.log", content="log")

        # Test CLI --status
        cli_main(["--status"])

        # Test CLI --dry-run
        cli_main(["--dry-run", "--max-bundles", "1", "--max-logs", "1"])


if __name__ == "__main__":
    unittest.main()
