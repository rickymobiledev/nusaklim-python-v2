import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import pandas as pd

from scripts.import_data import (
    normalize_epoch,
    format_duration,
    format_number,
    main,
)


class TestImportDataScript(unittest.TestCase):
    def test_normalize_epoch(self):
        self.assertEqual(normalize_epoch("1787136600.0"), "1787136600")
        self.assertEqual(normalize_epoch("1787136600"), "1787136600")
        self.assertEqual(normalize_epoch("---"), "---")
        self.assertEqual(normalize_epoch(None), "")
        self.assertEqual(normalize_epoch(""), "")

    def test_format_duration(self):
        self.assertEqual(format_duration(35.2), "35.2s")
        self.assertEqual(format_duration(65), "1m 05s")
        self.assertEqual(format_duration(3665), "1h 01m 05s")

    def test_format_number(self):
        self.assertEqual(format_number(1000), "1,000")
        self.assertEqual(format_number(1234567), "1,234,567")

    def test_argparse_conflict_options(self):
        with self.assertRaises(SystemExit) as ctx:
            main(["--stations-only", "--weather-only"])
        self.assertNotEqual(ctx.exception.code, 0)

    def test_argparse_invalid_chunk_size(self):
        with self.assertRaises(SystemExit) as ctx:
            main(["--chunk-size", "0"])
        self.assertNotEqual(ctx.exception.code, 0)

    def test_status_flag(self):
        ret = main(["--status"])
        self.assertEqual(ret, 0)


if __name__ == "__main__":
    unittest.main()
