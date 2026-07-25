from __future__ import annotations

import re
import unittest
from pathlib import Path


class DependencyContractTests(unittest.TestCase):
    def test_direct_runtime_and_browser_dependencies_are_exactly_pinned(self) -> None:
        for filename in ("requirements.txt", "requirements-browser.txt"):
            lines = Path(filename).read_text(encoding="utf-8").splitlines()
            for raw in lines:
                line = raw.strip()
                if not line or line.startswith("#") or line.startswith("-r "):
                    continue
                self.assertRegex(
                    line,
                    re.compile(r"^[A-Za-z0-9_.-]+==[^=<>!~;\s]+$"),
                    msg=f"{filename} contains a non-exact direct dependency: {line}",
                )


if __name__ == "__main__":
    unittest.main()
