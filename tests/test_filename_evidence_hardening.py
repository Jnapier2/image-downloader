from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from image_downloader import (
    ImageDownloader,
    evidence_reference_fields,
    redact_sensitive_text,
    redact_url_for_evidence,
    reference_sha256,
    sanitize_filename,
)


class FilenameEvidenceHardeningTests(unittest.TestCase):
    def test_windows_reserved_device_names_are_neutralized(self) -> None:
        expected = {
            "CON": "_CON",
            "con.png": "_con.png",
            "PRN.jpg": "_PRN.jpg",
            "AUX": "_AUX",
            "NUL .gif": "_NUL .gif",
            "COM1.webp": "_COM1.webp",
            "com9.bmp": "_com9.bmp",
            "LPT1.tiff": "_LPT1.tiff",
            "lpt9.svg": "_lpt9.svg",
            "COM10.png": "COM10.png",
            "LPT10.png": "LPT10.png",
        }
        for source, result in expected.items():
            with self.subTest(source=source):
                self.assertEqual(sanitize_filename(source), result)

    def test_unicode_bidirectional_controls_are_removed(self) -> None:
        controls = "\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
        self.assertEqual(sanitize_filename(f"photo{controls}gnp.exe"), "photognp.exe")

    def test_signed_url_evidence_redacts_secrets_but_keeps_ordinary_query(self) -> None:
        raw = (
            "https://alice:password@example.org/image.png?"
            "X-Amz-Credential=credential-secret&X-Amz-Signature=signature-secret&"
            "Policy=policy-secret&Expires=1700000000&Credential=generic-secret&"
            "Access-Credential=access-secret&size=large"
        )
        redacted = redact_url_for_evidence(raw)

        self.assertIn("https://<REDACTED>@example.org/image.png?", redacted)
        self.assertIn("X-Amz-Credential=<REDACTED>", redacted)
        self.assertIn("X-Amz-Signature=<REDACTED>", redacted)
        self.assertIn("Policy=<REDACTED>", redacted)
        self.assertIn("Expires=<REDACTED>", redacted)
        self.assertIn("Credential=<REDACTED>", redacted)
        self.assertIn("Access-Credential=<REDACTED>", redacted)
        self.assertIn("size=large", redacted)
        for secret in (
            "alice", "password", "credential-secret", "signature-secret", "policy-secret",
            "1700000000", "generic-secret", "access-secret",
        ):
            self.assertNotIn(secret, redacted)

        fields = evidence_reference_fields("url", raw)
        self.assertEqual(fields["url"], redacted)
        self.assertEqual(fields["url_sha256"], hashlib.sha256(raw.encode("utf-8")).hexdigest())
        self.assertEqual(fields["url_sha256"], reference_sha256(raw))
        embedded = redact_sensitive_text(f"request failed for {raw}")
        self.assertIn("size=large", embedded)
        self.assertNotIn("credential-secret", embedded)

    def test_persisted_run_state_and_resume_metadata_use_redacted_references(self) -> None:
        url = "https://example.org/image.png?X-Amz-Signature=url-secret&size=large"
        source = "https://example.org/gallery?Policy=source-secret&size=large"
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            downloader = ImageDownloader(root)
            try:
                downloader._start_run(url)
                downloader._record_failure(url, f"failed after {source}", source=source, stage="test")
                downloader._finish_run("error")

                recent = json.loads((root / "state" / "recent_run_summary.json").read_text(encoding="utf-8"))
                failures = json.loads((root / "state" / "recent_failures_errors.json").read_text(encoding="utf-8"))
                self.assertEqual(recent["input_url_sha256"], reference_sha256(url))
                self.assertIn("X-Amz-Signature=<REDACTED>", recent["input_url"])
                self.assertIn("size=large", recent["input_url"])
                self.assertEqual(failures[0]["url_sha256"], reference_sha256(url))
                self.assertEqual(failures[0]["source_sha256"], reference_sha256(source))
                self.assertNotIn("url-secret", json.dumps(recent))
                self.assertNotIn("source-secret", json.dumps(failures))
                log_text = (root / "logs" / "image_downloader.log").read_text(encoding="utf-8")
                self.assertIn(reference_sha256(url), log_text)
                self.assertIn("size=large", log_text)
                self.assertNotIn("url-secret", log_text)
                self.assertNotIn("source-secret", log_text)

                retained = root / "downloads" / "image.png"
                retained.parent.mkdir(parents=True, exist_ok=True)
                retained.write_bytes(b"image")
                downloader._save_file_record(url, "a" * 64, retained, 5, "image/png", 1, 1)
                downloader._save_download_index()
                index_text = (root / "state" / "download_index.json").read_text(encoding="utf-8")
                index = json.loads(index_text)
                self.assertIn(reference_sha256(url), index["urls"])
                self.assertTrue(downloader._state_url_record_exists(url))
                self.assertNotIn("url-secret", index_text)
                self.assertIn("size=large", index_text)

                part_path, meta_path = downloader._partial_paths(url)
                part_path.write_bytes(b"partial")
                downloader._write_partial_metadata(meta_path, {"url": url, "final_url": url, "etag": '"test"'})
                partial_text = meta_path.read_text(encoding="utf-8")
                partial = json.loads(partial_text)
                self.assertEqual(partial["url_sha256"], reference_sha256(url))
                self.assertEqual(partial["final_url_sha256"], reference_sha256(url))
                self.assertNotIn("url-secret", partial_text)
                self.assertEqual(downloader._load_partial_metadata(url, part_path, meta_path)["bytes_present"], 7)
            finally:
                downloader.close()
                for handler in list(downloader.logger.handlers):
                    handler.close()
                downloader.logger.handlers.clear()

    def test_legacy_state_migration_redacts_active_index_and_backup(self) -> None:
        url = "https://example.org/legacy.png?X-Amz-Credential=legacy-secret&size=large"
        digest = "b" * 64
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            state_dir = root / "state"
            output = root / "downloads" / "legacy.png"
            state_dir.mkdir(parents=True)
            output.parent.mkdir(parents=True)
            output.write_bytes(b"image")
            legacy_record = {
                "url": url,
                "path": "downloads\\legacy.png",
                "sha256": digest,
                "bytes": 5,
                "saved_at": "2026-01-01T00:00:00-06:00",
            }
            (state_dir / "download_index.json").write_text(
                json.dumps({
                    "version": 2,
                    "state_schema_version": 2,
                    "urls": {url: legacy_record},
                    "hashes": {digest: legacy_record},
                    "visual_hashes": {"legacy-fingerprint": legacy_record},
                }),
                encoding="utf-8",
            )

            downloader = ImageDownloader(root)
            try:
                correlation = reference_sha256(url)
                self.assertEqual(downloader.state["state_schema_version"], 3)
                self.assertIn(correlation, downloader.state["urls"])
                self.assertIn("X-Amz-Credential=<REDACTED>", downloader.state["urls"][correlation]["url"])
                self.assertIn("size=large", downloader.state["urls"][correlation]["url"])
                downloader._save_download_index()

                active_text = (state_dir / "download_index.json").read_text(encoding="utf-8")
                backups = list((state_dir / "migration_backups").glob("download_index_state_schema2_to_3_*.json"))
                self.assertEqual(len(backups), 1)
                backup_text = backups[0].read_text(encoding="utf-8")
                for persisted_text in (active_text, backup_text):
                    self.assertNotIn("legacy-secret", persisted_text)
                    self.assertNotIn(url, persisted_text)
                    self.assertIn(correlation, persisted_text)
                    self.assertIn("X-Amz-Credential=<REDACTED>", persisted_text)
                    self.assertIn("size=large", persisted_text)
            finally:
                downloader.close()
                for handler in list(downloader.logger.handlers):
                    handler.close()
                downloader.logger.handlers.clear()


if __name__ == "__main__":
    unittest.main()
