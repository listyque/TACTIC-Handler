"""The native title bar must not acquire a QML gap during window resize."""

import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MainResizeQmlTests(unittest.TestCase):
    def test_top_bar_stays_at_content_origin_across_resize(self):
        source = (ROOT / "thlib/ui/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("topPadding: 0", source)

        result = subprocess.run(
            [sys.executable, "-m", "tests.profile_main_resize"],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        samples = json.loads(result.stdout.strip().splitlines()[-1])["samples"]
        self.assertTrue(samples)
        for sample in samples:
            with self.subTest(width=sample["width"], height=sample["height"]):
                self.assertEqual(sample["topPadding"], 0)
                self.assertEqual(sample["topBarY"], 0)


if __name__ == "__main__":
    unittest.main()
