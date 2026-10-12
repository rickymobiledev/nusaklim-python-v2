import importlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pydantic import ValidationError

# Import configuration without requiring a developer's .env or real API key.
with patch.dict(os.environ, {"NUSAKLIM_WEATHER_API_KEY": "test-key"}):
    config = importlib.import_module("api.config")
    serve = importlib.import_module("api.serve")


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"NUSAKLIM_WEATHER_API_KEY": "test-key"}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_default_paths_follow_checkout(self):
        settings = config.Settings(_env_file=None)
        self.assertEqual(settings.base_dir, str(config.CHECKOUT_ROOT))
        self.assertEqual(settings.model_bundle_path, str(config.CHECKOUT_ROOT / "models" / "weather_model_latest.joblib"))
        self.assertEqual(settings.incoming_dir, str(config.CHECKOUT_ROOT / "data_raw" / "incoming"))

    def test_project_root_from_dotenv_controls_default_paths(self):
        with tempfile.TemporaryDirectory() as root:
            env_file = Path(root) / ".env"
            project_root = Path(root) / "project"
            env_file.write_text(f'NUSAKLIM_PROJECT_ROOT="{project_root.as_posix()}"\n', encoding="utf-8")
            settings = config.Settings(_env_file=env_file)
            self.assertEqual(Path(settings.project_root), project_root)
            self.assertEqual(Path(settings.base_dir), project_root)
            self.assertEqual(Path(settings.model_bundle_path), project_root / "models" / "weather_model_latest.joblib")
            self.assertEqual(Path(settings.incoming_dir), project_root / "data_raw" / "incoming")
            os.environ["NUSAKLIM_PROJECT_ROOT"] = str(Path(root) / "override")
            settings = config.Settings(_env_file=env_file)
            self.assertEqual(Path(settings.base_dir), Path(root) / "override")

    def test_project_root_alias_and_relative_base_dir(self):
        os.environ["PROJECT_ROOT"] = "custom-project"
        os.environ["NUSAKLIM_BASE_DIR"] = "data-project"
        settings = config.Settings(_env_file=None)
        self.assertEqual(Path(settings.project_root), config.CHECKOUT_ROOT / "custom-project")
        self.assertEqual(Path(settings.base_dir), config.CHECKOUT_ROOT / "custom-project" / "data-project")

    def test_path_overrides_and_child_defaults(self):
        with tempfile.TemporaryDirectory() as root:
            os.environ.update(NUSAKLIM_BASE_DIR=root, NUSAKLIM_RAW_DATA_DIR="custom-raw",
                              NUSAKLIM_LOG_DIR=str(Path(root) / "absolute-logs"))
            settings = config.Settings(_env_file=None)
            self.assertEqual(Path(settings.raw_csv_path), Path(root) / "custom-raw" / "nusaklim-aws-reduce.csv")
            self.assertEqual(Path(settings.upload_staging_dir), Path(root) / "custom-raw" / "staging")
            self.assertEqual(Path(settings.log_dir), Path(root) / "absolute-logs")

    def test_dotenv_and_process_environment_precedence(self):
        with tempfile.TemporaryDirectory() as root:
            env_file = Path(root) / ".env"
            env_file.write_text('NUSAKLIM_PORT=9001\nNUSAKLIM_RELOAD=false\n'
                                'NUSAKLIM_APP_NAME="Custom API"\n'
                                'NUSAKLIM_CORS_ORIGINS=["https://example.com"]\n', encoding="utf-8")
            os.environ["NUSAKLIM_PORT"] = "9002"
            settings = config.Settings(_env_file=env_file)
            self.assertEqual(settings.port, 9002)
            self.assertFalse(settings.reload)
            self.assertEqual(settings.app_name, "Custom API")
            self.assertEqual(settings.cors_origins, ["https://example.com"])

    def test_generic_port_alias(self):
        os.environ["PORT"] = "9003"
        self.assertEqual(config.Settings(_env_file=None).port, 9003)
        os.environ["NUSAKLIM_PORT"] = "9004"
        self.assertEqual(config.Settings(_env_file=None).port, 9004)

    def test_invalid_port_and_limits_fail(self):
        for name, value in (("NUSAKLIM_PORT", "0"), ("NUSAKLIM_PORT", "65536"),
                            ("NUSAKLIM_PORT", "bad"), ("NUSAKLIM_MAX_BULK_STATIONS", "0"),
                            ("NUSAKLIM_MAX_INGEST_RECORDS", "-1")):
            with self.subTest(name=name, value=value), patch.dict(os.environ, {name: value}):
                with self.assertRaises(ValidationError):
                    config.Settings(_env_file=None)

    def test_key_must_be_supplied(self):
        os.environ.pop("NUSAKLIM_WEATHER_API_KEY")
        with self.assertRaises(ValidationError):
            config.Settings(_env_file=None)
        os.environ["NUSAKLIM_WEATHER_API_KEY"] = ""
        with self.assertRaises(ValidationError):
            config.Settings(_env_file=None)

    def test_server_uses_configured_host_port_and_reload(self):
        settings = config.Settings(_env_file=None, host="0.0.0.0", port=9010, reload=False)
        with patch.object(serve, "settings", settings), patch("sys.argv", ["serve", "--open-browser"]), \
                patch.object(serve.uvicorn, "run") as run, patch.object(serve.webbrowser, "open") as browser:
            serve.main()
        run.assert_called_once_with("api.main:app", host="0.0.0.0", port=9010, reload=False)
        browser.assert_called_once_with("http://127.0.0.1:9010/docs")


if __name__ == "__main__":
    unittest.main()
