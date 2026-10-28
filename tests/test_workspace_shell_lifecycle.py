from pathlib import Path
import json
import subprocess
import sys
import unittest


class WorkspaceShellLifecycleTests(unittest.TestCase):
    def test_first_dashboard_mounts_without_search_grip_or_dock_context_errors(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, "-X", "utf8", "-m", "tests.run_workspace_shell_lifecycle"],
                                cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(len(data["cycles"]), 3)
        self.assertEqual(data["warnings"], [])


if __name__ == "__main__":
    unittest.main()
