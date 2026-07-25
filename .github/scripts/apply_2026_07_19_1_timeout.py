#!/usr/bin/env python3
"""Apply the reviewed Image Downloader 2026.07.19.1 timeout patch once.

Copyright © 2026 Gateway Information Group LLC. All rights reserved.
"""
from __future__ import annotations

from pathlib import Path


FINAL_CI = '''name: CI

on:
  push:
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    runs-on: windows-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version: "3.11"
          cache: pip
      - name: Install dependencies
        run: python -m pip install -r requirements.txt
      - name: Compile
        run: python -m compileall -q image_downloader.py tests
      - name: Test
        run: python -m unittest discover -s tests -v

# Copyright © 2026 Gateway Information Group LLC. All rights reserved.
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    source_path = Path("image_downloader.py")
    text = source_path.read_text(encoding="utf-8")
    text = replace_once(text, 'APP_VERSION = "2026.07.18.1"', 'APP_VERSION = "2026.07.19.1"', "app version")
    text = replace_once(text, 'BUILD_DATE = "2026-07-18 CDT"', 'BUILD_DATE = "2026-07-19 CDT"', "build date")
    text = replace_once(
        text,
        '        "timeout": 20,\n        "connect_timeout": 7,\n        "read_timeout": 20,\n        "request_wall_clock_timeout_seconds": 120,\n        "page_wall_clock_timeout_seconds": 60,',
        '        "timeout": 5,\n        "connect_timeout": 3,\n        "read_timeout": 5,\n        "request_wall_clock_timeout_seconds": 5,\n        "page_wall_clock_timeout_seconds": 60,',
        "default timeout block",
    )
    source_path.write_text(text, encoding="utf-8", newline="\n")

    example_path = Path("image_downloader_config.example.json")
    example = example_path.read_text(encoding="utf-8")
    example = replace_once(
        example,
        '  "timeout": 20,\n  "connect_timeout": 7,\n  "read_timeout": 20,\n  "workers": 6,',
        '  "timeout": 5,\n  "connect_timeout": 3,\n  "read_timeout": 5,\n  "request_wall_clock_timeout_seconds": 5,\n  "page_wall_clock_timeout_seconds": 60,\n  "workers": 6,',
        "example timeout block",
    )
    example_path.write_text(example, encoding="utf-8", newline="\n")

    readme_path = Path("README.md")
    readme = readme_path.read_text(encoding="utf-8")
    marker = "- Validator-gated partial resume, atomic finalization, adaptive concurrency, bounded retries, and single-instance ownership.\n"
    addition = marker + "- A strict five-second per-image network budget covers HEAD preflight, GET attempts, bounded backoff, reconnects, and streamed transfer; page discovery keeps its separate limit.\n"
    if readme.count(marker) != 1:
        raise SystemExit("README timeout insertion point is not unique")
    readme_path.write_text(readme.replace(marker, addition, 1), encoding="utf-8", newline="\n")

    Path(".github/workflows/ci.yml").write_text(FINAL_CI, encoding="utf-8", newline="\n")

    Path("tests/test_release_timeout_defaults.py").write_text(
        '''from __future__ import annotations

import json
import unittest
from pathlib import Path

import image_downloader as app


class ReleaseTimeoutDefaultsTests(unittest.TestCase):
    def test_release_identity_and_five_second_image_budget(self) -> None:
        self.assertEqual(app.APP_VERSION, "2026.07.19.1")
        config = app.default_config()
        self.assertEqual(config["timeout"], 5)
        self.assertEqual(config["connect_timeout"], 3)
        self.assertEqual(config["read_timeout"], 5)
        self.assertEqual(config["request_wall_clock_timeout_seconds"], 5)
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
        self.assertEqual(payload["request_wall_clock_timeout_seconds"], 5)
        self.assertEqual(payload["page_wall_clock_timeout_seconds"], 60)
        self.assertFalse(payload["hide_downloaded_media"])


if __name__ == "__main__":
    unittest.main()
''',
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
