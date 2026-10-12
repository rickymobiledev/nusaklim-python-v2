import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from scripts.backup_postgres import (
    parse_db_url,
    format_size,
    find_pg_dump,
    main,
)


class TestBackupPostgresScript(unittest.TestCase):
    def test_parse_db_url(self):
        url = "postgresql://myuser:mypassword@192.168.1.100:5433/mydb"
        params = parse_db_url(url)
        self.assertEqual(params["user"], "myuser")
        self.assertEqual(params["password"], "mypassword")
        self.assertEqual(params["host"], "192.168.1.100")
        self.assertEqual(params["port"], 5433)
        self.assertEqual(params["dbname"], "mydb")

    def test_parse_db_url_default(self):
        url = "postgresql://localhost/testdb"
        params = parse_db_url(url)
        self.assertEqual(params["user"], "postgres")
        self.assertEqual(params["password"], "")
        self.assertEqual(params["host"], "localhost")
        self.assertEqual(params["port"], 5432)
        self.assertEqual(params["dbname"], "testdb")

    def test_format_size(self):
        self.assertEqual(format_size(500), "500.00 B")
        self.assertEqual(format_size(1024), "1.00 KB")
        self.assertEqual(format_size(1024 * 1024 * 150), "150.00 MB")
        self.assertEqual(format_size(1024 * 1024 * 1024 * 2), "2.00 GB")

    def test_argparse_conflict_options(self):
        with self.assertRaises(SystemExit) as ctx:
            main(["--schema-only", "--data-only"])
        self.assertNotEqual(ctx.exception.code, 0)

    @patch("scripts.backup_postgres.print_status")
    def test_main_status_invoked(self, mock_status):
        main(["--status"])
        mock_status.assert_called_once()


if __name__ == "__main__":
    unittest.main()
