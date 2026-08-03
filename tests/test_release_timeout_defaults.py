from __future__ import annotations

import json
import unittest
from pathlib import Path

import image_downloader as app


class ReleaseTimeoutDefaultsTests(unittest.TestCase):
    def test_release_identity_and_request_budget(self) -> None:
        self.assertEqual(app.APP_VERSION, "2026.08.02.1")
        self.assertEqual(app.BUILD_DATE, "2026-08-02 CDT")
        config = app.default_config()
        self.assertEqual(config["timeout"], 5)
        self.assertEqual(config["connect_timeout"], 3)
        self.assertEqual(config["read_timeout"], 5)
        self.assertEqual(config["request_wall_clock_timeout_seconds"], 15)
        self.assertEqual(app.normalize_config(dict(config))["request_wall_clock_timeout_seconds"], 15)
        self.assertEqual(config["page_wall_clock_timeout_seconds"], 60)

    def test_public_visible_output_default_is_preserved(self) -> None:
        config = app.default_config()
        self.assertFalse(config["hide_downloaded_media"])
        self.assertFalse(app.HIDE_DOWNLOADED_MEDIA_DEFAULT)

    def test_example_config_matches_bounded_defaults(self) -> None:
        payload = json.loads(Path("image_downloader_config.example.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["timeout"], 5)
        self.assertEqual(payload["connect_timeout"], 3)
        self.assertEqual(payload["read_timeout"], 5)
        self.assertEqual(payload["request_wall_clock_timeout_seconds"], 15)
        self.assertEqual(payload["page_wall_clock_timeout_seconds"], 60)
        self.assertFalse(payload["hide_downloaded_media"])


if __name__ == "__main__":
    unittest.main()
