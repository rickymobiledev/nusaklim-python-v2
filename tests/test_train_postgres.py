import unittest
from pathlib import Path

from scripts.train_postgres import (
    format_duration,
    format_number,
    get_latest_model_info,
    main,
)


import os
from api.config import settings


class TestTrainPostgresScript(unittest.TestCase):
    def setUp(self):
        self.prev_backend = settings.storage_backend
        self.prev_env = os.environ.get("NUSAKLIM_STORAGE_BACKEND")

    def tearDown(self):
        settings.storage_backend = self.prev_backend
        if self.prev_env is not None:
            os.environ["NUSAKLIM_STORAGE_BACKEND"] = self.prev_env
        else:
            os.environ.pop("NUSAKLIM_STORAGE_BACKEND", None)
    def test_format_duration(self):
        self.assertEqual(format_duration(15.4), "15.4s")
        self.assertEqual(format_duration(125), "2m 05s")
        self.assertEqual(format_duration(7200), "2h 00m 00s")

    def test_format_number(self):
        self.assertEqual(format_number(500), "500")
        self.assertEqual(format_number(14771911), "14,771,911")

    def test_argparse_conflict(self):
        with self.assertRaises(SystemExit) as ctx:
            main(["--train-only", "--clean-only"])
        self.assertNotEqual(ctx.exception.code, 0)

    def test_status_flag(self):
        ret = main(["--status"])
        self.assertEqual(ret, 0)

    def test_get_latest_model_info(self):
        info = get_latest_model_info()
        self.assertIsNotNone(info)
        self.assertIn("timestamp", info)
        self.assertIn("models_count", info)
        self.assertEqual(info["models_count"], 49)


if __name__ == "__main__":
    unittest.main()
