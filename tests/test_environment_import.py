from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class EnvironmentImportTests(unittest.TestCase):
    def test_import_preserves_recursion_limit_and_runtime_state_is_owned(self):
        probe = """
import json
import sys

before = sys.getrecursionlimit()
from thlib.environment import Inst, env_inst, env_write_config
after = sys.getrecursionlimit()

env_write_config(
    {"performance/serverThreads": 3, "performance/localThreads": 2},
    filename="ui_settings", unique_id="ui_main", long_abs_path=True,
)

first = Inst()
second = Inst()
first.ui_main_tabs["demo"] = object()
result = {
    "before": before,
    "after": after,
    "instances_are_distinct": first is not second,
    "state_is_distinct": "demo" not in second.ui_main_tabs,
    "server_pools_are_distinct": first.server_pool is not second.server_pool,
    "commit_pools_are_distinct": first.commit_pool is not second.commit_pool,
    "local_pools_are_distinct": first.local_pool is not second.local_pool,
    "server_threads": first.server_pool.max_threads,
    "local_threads": first.local_pool.max_threads,
}
for runtime in (first, second, env_inst):
    runtime.exit_pools(1000)
print("ENVIRONMENT_PROBE=" + json.dumps(result, sort_keys=True))
"""
        with tempfile.TemporaryDirectory(
            prefix="tactic-environment-import-"
        ) as directory:
            environment = os.environ.copy()
            environment["TACTIC_QML_TEST_SETTINGS_DIR"] = directory
            completed = subprocess.run(
                [sys.executable, "-c", probe],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            isolated_settings = Path(directory) / "settings"
            self.assertTrue(isolated_settings.is_dir())

        self.assertEqual(
            completed.returncode,
            0,
            "\n".join((completed.stdout, completed.stderr)),
        )
        payload_line = next(
            line for line in completed.stdout.splitlines()
            if line.startswith("ENVIRONMENT_PROBE=")
        )
        payload = json.loads(payload_line.partition("=")[2])
        self.assertEqual(payload["before"], payload["after"])
        self.assertTrue(payload["instances_are_distinct"])
        self.assertTrue(payload["state_is_distinct"])
        self.assertTrue(payload["server_pools_are_distinct"])
        self.assertTrue(payload["commit_pools_are_distinct"])
        self.assertTrue(payload["local_pools_are_distinct"])
        self.assertEqual(payload["server_threads"], 3)
        self.assertEqual(payload["local_threads"], 2)


if __name__ == "__main__":
    unittest.main()
