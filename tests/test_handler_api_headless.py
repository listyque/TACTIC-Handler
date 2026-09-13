"""The public object API must not require an installed Qt binding."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class HeadlessApiTests(unittest.TestCase):
    def test_native_objects_and_files_import_without_qt(self):
        probe = """
import importlib.abc
import sys
class NoQt(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(("PySide", "PyQt", "thlib.side.Qt", "thlib.ui")):
            raise AssertionError("Headless import requested " + fullname)
sys.meta_path.insert(0, NoQt())
from thlib import tactic_classes as tc
from thlib import global_functions as gf
from thlib.environment import env_inst
from tactic_handler_api import local, from_client
from thlib.checkin_operation import execute_checkin_payload
from thlib.repository_download import DownloadOperation
with local() as api:
    assert api.files.match(["test.txt"])
    assert api.commit_queue().items() == []
    assert api.submit(lambda: 42).wait(3) == 42
class UnusedClient:
    def request(self, *args, **kwargs):
        raise AssertionError("An unused API must not open a remote session")
with from_client(UnusedClient()) as api:
    assert callable(api.ui.show)
    assert api.ui.window("commit_queue").id == "commit_queue"
project = tc.Project({"code": "demo"})
obj = tc.SObject({"code": "O1", "description": "before"}, project)
obj.set_value("description", "after")
assert obj.get_value("description") == "before"  # Preserve legacy semantics.
assert gf.MatchTemplate(["$FILENAME.$EXT"]).get_files_objects(["test.txt"])
assert not any(name in vars(env_inst) for name in ("server_pool", "local_pool", "commit_pool"))
env_inst.exit_pools()
"""
        with tempfile.TemporaryDirectory() as directory:
            environment = dict(os.environ, TACTIC_QML_TEST_SETTINGS_DIR=directory)
            completed = subprocess.run(
                [sys.executable, "-c", probe],
                cwd=Path(__file__).resolve().parents[1],
                env=environment,
                capture_output=True,
                text=True,
                timeout=30,
            )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
