"""Keep current security guidance distinct from content-handling safeguards.

These are documentation regressions, not tests of network isolation.
Copyright © 2026 Gateway Information Group LLC. All rights reserved.
"""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DocumentedBoundaryTests(unittest.TestCase):
    def test_readme_and_security_describe_the_current_network_limit(self):
        for name in ("README.md", "SECURITY.md"):
            with self.subTest(document=name):
                text = (ROOT / name).read_text(encoding="utf-8")
                self.assertIn("does not provide private-network isolation", text)
                self.assertIn("trusted", text)
                self.assertNotIn("blocks loopback, private", text)
                self.assertNotIn("Network destination checks block", text)

    def test_browser_import_check_is_not_presented_as_isolation_testing(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("do not establish browser isolation", text)
        self.assertNotIn("browser-route guardrails", text)


if __name__ == "__main__":
    unittest.main()
