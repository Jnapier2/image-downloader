from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LauncherIntegrityOrderTests(unittest.TestCase):
    def test_integrity_decision_precedes_project_write(self) -> None:
        launcher = (ROOT / "GatewayImageDownloader.bat").read_text(encoding="utf-8").replace("\r\n", "\n")
        main_flow = launcher.split("\n:diagnostics_export\n", 1)[0]
        self.assertLess(main_flow.index("call :verify_release_integrity"), main_flow.index('call :verify_write_dir "%BOT_DIR%"'))

        diagnostics = launcher.split("\n:diagnostics_export\n", 1)[1].split("\n:verify_write_dir\n", 1)[0]
        self.assertLess(diagnostics.index("--verify-release"), diagnostics.index('call :verify_write_dir "%BOT_DIR%"'))
        self.assertLess(diagnostics.index('call :verify_write_dir "%BOT_DIR%"'), diagnostics.index("--export-support"))

    def test_python_and_dependency_contracts_are_single_source(self) -> None:
        launcher = (ROOT / "GatewayImageDownloader.bat").read_text(encoding="utf-8")
        self.assertNotIn("(3,9)", launcher)
        self.assertGreaterEqual(launcher.count("(3,11)"), 3)
        self.assertIn(r'.venv\Scripts\python.exe', launcher)
        self.assertLess(launcher.index(r'.venv\Scripts\python.exe'), launcher.index("where py"))
        self.assertIn(r'-r "%BOT_DIR%\requirements.txt"', launcher)
        self.assertIn(r'-r "%BOT_DIR%\requirements-browser.txt"', launcher)
        self.assertNotIn("beautifulsoup4>=4.12", launcher)
        self.assertNotIn("playwright>=1.45", launcher)

    def test_no_security_policy_bypass_was_added(self) -> None:
        launcher = (ROOT / "GatewayImageDownloader.bat").read_text(encoding="utf-8").lower()
        self.assertNotIn("executionpolicy bypass", launcher)
        for term in ("disable defender", "disable norton", "disable smartscreen"):
            self.assertNotIn(term, launcher)


if __name__ == "__main__":
    unittest.main()
