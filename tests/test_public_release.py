from __future__ import annotations

import json
import unittest
from pathlib import Path

import image_downloader as app


ROOT = Path(__file__).resolve().parents[1]


class PublicReleaseTests(unittest.TestCase):
    def test_release_identity_is_current_and_complete(self) -> None:
        self.assertEqual(app.APP_VERSION, "2026.08.08.1")
        self.assertEqual(app.BUILD_NAME, "v2175-queue-autosave-recovery-3worker-session-list")
        status = app.verify_release_identity(ROOT)
        self.assertEqual(status["result"], "PASS")
        self.assertEqual(status["verified_count"], 13)
        self.assertEqual(status["managed_count"], 13)
        self.assertEqual(status["mismatches"], [])

    def test_defaults_keep_work_bounded_and_recoverable(self) -> None:
        config = app.default_config()
        self.assertEqual(config["workers"], 3)
        self.assertEqual(config["adaptive_throttle_max_workers"], 3)
        self.assertEqual(config["download_queue_capacity"], 100)
        self.assertTrue(config["download_queue_autosave_enabled"])
        self.assertTrue(config["download_queue_recovery_enabled"])
        self.assertTrue(config["session_download_list_enabled"])
        self.assertTrue(config["hide_downloaded_media"])

    def test_example_config_matches_current_bounds(self) -> None:
        payload = json.loads((ROOT / "image_downloader_config.example.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["config_schema_version"], app.CONFIG_SCHEMA_VERSION)
        self.assertEqual(payload["state_schema_version"], app.STATE_SCHEMA_VERSION)
        self.assertEqual(payload["workers"], 3)
        self.assertEqual(payload["adaptive_throttle_max_workers"], 3)
        self.assertEqual(payload["download_queue_capacity"], 100)

    def test_url_and_content_helpers_reject_unsafe_inputs(self) -> None:
        for value in ("javascript:alert(1)", "file:///private/image.png", "data:image/png;base64,AAAA"):
            with self.subTest(value=value):
                self.assertIsNone(app.normalize_url(value))
        self.assertTrue(app.is_dangerous_content_type("application/x-msdownload"))
        self.assertTrue(app.svg_has_active_content(b"<svg><script>alert(1)</script></svg>"))
        self.assertFalse(app.svg_has_active_content(b"<svg><rect width='10' height='10'/></svg>"))

    def test_filename_and_resume_helpers_are_windows_safe(self) -> None:
        self.assertEqual(app.sanitize_filename("CON.png"), "_CON.png")
        self.assertEqual(app.sanitize_filename('bad<name>:image?.png'), "bad_name__image_.png")
        self.assertEqual(app.parse_content_range("bytes 100-199/500"), (100, 500))
        self.assertEqual(app.parse_srcset("small.jpg 320w, large.jpg 1200w"), ["large.jpg"])

    def test_url_evidence_redacts_credentials(self) -> None:
        raw = "https://alice:password@example.org/image.png?X-Amz-Signature=secret&size=large"
        redacted = app.redact_url_for_evidence(raw)
        self.assertNotIn("alice", redacted)
        self.assertNotIn("password", redacted)
        self.assertNotIn("secret", redacted)
        self.assertIn("size=large", redacted)


if __name__ == "__main__":
    unittest.main()
