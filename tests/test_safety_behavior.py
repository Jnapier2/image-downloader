from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from image_downloader import (
    HIDE_DOWNLOADED_MEDIA_DEFAULT,
    asset_metadata_reconciliation_summary,
    default_config,
    destination_host_is_public,
    is_dangerous_content_type,
    normalize_url,
    parse_args,
    parse_content_range,
    parse_srcset,
    sanitize_filename,
    svg_has_active_content,
    windows_attributes_with_visibility,
)


class SafetyBehaviorTests(unittest.TestCase):
    def test_downloaded_media_is_visible_by_default(self) -> None:
        self.assertFalse(HIDE_DOWNLOADED_MEDIA_DEFAULT)
        self.assertFalse(default_config()["hide_downloaded_media"])

    def test_default_duplicate_controls_remain_enabled(self) -> None:
        config = default_config()
        self.assertTrue(config["duplicate_url_check"])
        self.assertTrue(config["duplicate_content_hash_check"])
        self.assertTrue(config["duplicate_visual_fingerprint_check"])
        self.assertFalse(config["sequence_discovery_enabled"])

    def test_normalize_url_accepts_only_http_schemes(self) -> None:
        self.assertIsNone(normalize_url("javascript:alert(1)"))
        self.assertIsNone(normalize_url("file:///private/image.png"))
        self.assertEqual(
            normalize_url("HTTPS://Example.ORG/a file.png#fragment"),
            "https://example.org/a%20file.png",
        )

    def test_private_and_credentialed_destinations_are_rejected(self) -> None:
        blocked = [
            "http://localhost/image.png",
            "http://127.0.0.1/image.png",
            "http://10.0.0.1/image.png",
            "http://169.254.169.254/latest/meta-data",
            "http://[::1]/image.png",
            "https://user:password@example.org/image.png",
        ]
        for url in blocked:
            with self.subTest(url=url):
                self.assertIsNone(normalize_url(url))
        self.assertTrue(destination_host_is_public("8.8.8.8", resolve_dns=False))

    def test_dangerous_content_types_are_rejected(self) -> None:
        self.assertTrue(is_dangerous_content_type("application/x-msdownload"))
        self.assertTrue(is_dangerous_content_type("application/javascript; charset=utf-8"))
        self.assertFalse(is_dangerous_content_type("image/png"))

    def test_svg_active_content_is_detected(self) -> None:
        self.assertTrue(svg_has_active_content(b"<svg><script>alert(1)</script></svg>"))
        self.assertFalse(svg_has_active_content(b"<svg><rect width='10' height='10'/></svg>"))

    def test_filename_and_srcset_helpers_are_bounded(self) -> None:
        self.assertEqual(sanitize_filename('bad<name>:image?.png'), "bad_name__image_.png")
        self.assertEqual(
            parse_srcset("small.jpg 320w, large.jpg 1200w", preference="largest"),
            ["large.jpg"],
        )

    def test_content_range_parser_handles_resume_headers(self) -> None:
        self.assertEqual(parse_content_range("bytes 100-199/500"), (100, 500))
        self.assertEqual(parse_content_range("bytes */500"), (None, 500))
        self.assertEqual(parse_content_range("invalid"), (None, None))

    def test_visibility_bit_can_be_enabled_and_cleared(self) -> None:
        hidden_bit = 0x2
        self.assertTrue(windows_attributes_with_visibility(0x20, True) & hidden_bit)
        self.assertFalse(windows_attributes_with_visibility(0x22, False) & hidden_bit)

    def test_optional_browser_mode_has_public_route_guardrails(self) -> None:
        self.assertTrue(parse_args(["--browser-mode"]).browser_mode)
        source = (Path(__file__).resolve().parents[1] / "image_downloader.py").read_text(encoding="utf-8")
        self.assertIn("class PublicOnlySession", source)
        self.assertIn("get_redirect_target", source)
        self.assertIn('self._browser_context.route("**/*", enforce_public_route)', source)
        self.assertNotIn('page.route("**/*", enforce_public_route)', source)
        self.assertIn("require_public_destination", source)
        self.assertIn('service_workers="block"', source)
        self.assertIn("max_redirects=0", source)
        self.assertIn("route.fulfill(response=response)", source)

    def test_empty_asset_registry_does_not_claim_verified(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            summary = asset_metadata_reconciliation_summary(root, root / "config.json")
        self.assertIn("Package status: not-configured", summary)
        self.assertIn("Reconciliation result: NOT EVALUATED", summary)
        self.assertNotIn("Reconciliation result: PASS", summary)

    def test_unknown_config_warning_mentions_only_supported_diagnostic_command(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "image_downloader.py").read_text(encoding="utf-8")
        self.assertIn("Run /diagnose for a redacted custom-input assurance summary.", source)
        self.assertNotIn("/diagnose or /export", source)

    def test_source_excludes_private_workflow_labels(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "image_downloader.py").read_text(encoding="utf-8").lower()
        labels = [
            "chat" + "gpt",
            "google " + "drive",
            "drive " + "vault",
            "project " + "vault",
            "hand" + "off",
            "export" + "20",
            "manifest" + ".json",
            "export-" + "chat" + "gpt",
            "v2." + "16.5",
            "v2" + "165",
            "c:" + "\\bots",
            "image_downloader_" + "bot_dir",
            "project-" + "internal",
        ]
        for label in labels:
            with self.subTest(label=label):
                self.assertNotIn(label, source)


if __name__ == "__main__":
    unittest.main()
