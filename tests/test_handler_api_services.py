"""Real API-to-native file/queue boundaries, with only TACTIC isolated."""

from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from types import SimpleNamespace
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

from tests import test_handler_api as helpers
from tactic_handler_api import ConcurrentEdit
from tactic_handler_api.checkin import HeadlessQueue
from tactic_handler_api.operations import Executor, report_progress


class ServiceTests(helpers._WorkerTestCase):
    setUp = helpers.HandlerApiTests.setUp
    query = helpers.HandlerApiTests.query
    insert = helpers.HandlerApiTests.insert
    update = helpers.HandlerApiTests.update

    def test_local_repository_catalog_initializes_base_directories(self):
        from tactic_handler_api import local
        from thlib.environment import env_tactic

        repository = {
            "name": "base",
            "value": [self.directory.name, "Base", "", "base", True],
        }
        with (
            patch.object(env_tactic, "get_base_dirs") as initialize,
            patch.object(
                env_tactic,
                "get_all_base_dirs",
                return_value=[("base", repository)],
            ),
            local() as api,
        ):
            self.assertEqual(api.repositories.list(), [repository])
        initialize.assert_called_once_with()

    def test_headless_queue_stages_native_files_and_returns_confirmed_snapshot(self):
        from thlib import global_functions as gf

        source = Path(self.directory.name) / "source.txt"
        source.write_text("check-in bytes", encoding="utf-8")
        repository = {
            "name": "test",
            "value": [self.directory.name, "Test", "", "repo", True],
        }
        self.api._file_module = gf
        self.api._repositories = lambda: [repository]
        self.core.Snapshot = self.tc.Snapshot
        self.core.server_start = Mock(return_value=self.server)
        result = {
            "__search_key__": "sthpw/snapshot?project=demo&code=S1",
            "code": "S1",
            "version": 1,
        }
        self.server.query_snapshots.side_effect = lambda **kwargs: [
            {**result, "__files__": [], "snapshot": "<snapshot/>"},
        ]
        virtual = [
            (
                "source",
                {
                    "versioned": {
                        "names": [["O1_v001", "", ".txt"]],
                        "paths": ["objects"],
                    }
                },
            )
        ]
        with (
            patch.object(self.tc, "get_virtual_snapshot", return_value=virtual),
            patch.object(self.tc, "checkin_snapshot", return_value=result) as checkin,
        ):
            queue = self.api.commit_queue("demo")
            item = queue.add(
                self.records["O1"]["__search_key__"],
                context="publish/main",
                files=[source],
                repository="repo",
                generate_previews=False,
                mode="copy",
            )
            self.assertEqual(item.state, "prepared")
            with self.assertRaisesRegex(ValueError, "already exists"):
                queue.add(
                    self.records["O1"]["__search_key__"],
                    context="publish/main",
                    files=[source],
                    repository="repo",
                    generate_previews=False,
                )
            item.set_description("Approved")
            snapshot = item.submit().wait(3)
            self.assertEqual(snapshot.get_code(), "S1")
            self.assertEqual(
                (Path(self.directory.name) / "objects" / "O1_v001.txt").read_bytes(),
                source.read_bytes(),
            )
            self.assertEqual(item.commit().get_code(), "S1")
            checkin.assert_called_once()
            self.assertEqual(checkin.call_args.kwargs["description"], "Approved")
            self.assertEqual(checkin.call_args.kwargs["mode"], "inplace")
            self.assertEqual(checkin.call_args.kwargs["context"], "publish/main")
            self.assertEqual(queue.remove_completed(), 1)
            self.assertEqual(queue.items(), [])

    def test_uncertain_checkin_never_automatically_retries(self):
        repository = {"value": [self.directory.name, "Test", "", "repo", True]}
        queue = HeadlessQueue(lambda: [repository])
        payload = {
            "searchKey": self.records["O1"]["__search_key__"],
            "context": "publish",
            "repository": "repo",
            "files": [{"path": "source.txt"}],
            "filesDict": [("source", {})],
        }
        identity = queue.add(payload, "Object")
        with patch(
            "thlib.checkin_operation.execute_checkin_payload",
            side_effect=OSError("reply lost"),
        ) as execute:
            with self.assertRaises(OSError):
                queue.commit(identity)
            self.assertEqual(queue.get(identity)["state"], "uncertain")
            with self.assertRaises(ConcurrentEdit):
                queue.commit(identity)
            execute.assert_called_once()

    def test_definition_edit_preserves_expression_unknown_xml_and_exact_owner(self):
        self.core.server_start = Mock(return_value=self.server)
        row = {
            "code": "W1",
            "view": "edit",
            "search_type": "types/object",
            "login": "alice",
            "__search_key__": "config/widget_config?project=demo&code=W1",
            "config": '<config><!--keep--><edit custom="yes"><element name="category"><display class="SelectWdg"><values_expr>@GET(types/category.code)</values_expr><labels_expr>@GET(types/category.name)</labels_expr></display><custom><nested value="1"/></custom></element></edit></config>',
        }
        self.server.query.return_value = [deepcopy(row)]
        self.server.update.side_effect = lambda key, data, **options: {**row, **data}
        definition = (
            self.api.project("demo").stype("types/object").definitions.get("W1")
        )
        definition.element("category").set_option("display", "empty", "-- Select --")
        root = ET.fromstring(definition.xml)
        self.assertEqual(root.find(".//values_expr").text, "@GET(types/category.code)")
        self.assertEqual(root.find(".//labels_expr").text, "@GET(types/category.name)")
        self.assertEqual(root.find(".//nested").get("value"), "1")
        self.assertIn("<!--keep-->", definition.xml)
        definition.commit()
        self.assertEqual(self.server.update.call_args.args[0], row["__search_key__"])
        self.assertEqual(set(self.server.update.call_args.args[1]), {"config"})
        self.assertEqual(definition.login, "alice")
        before = definition.xml
        with self.assertRaises(ET.ParseError):
            definition.set_xml("<config>")
        self.assertEqual(definition.xml, before)

    def test_headless_queue_claims_latest_edits_after_repository_discovery(self):
        entered, release = threading.Event(), threading.Event()

        def repositories():
            entered.set()
            if not release.wait(3):
                raise TimeoutError("test gate")
            return [{"value": [self.directory.name, "Test", "", "repo", True]}]

        queue = HeadlessQueue(repositories)
        identity = queue.add(
            {
                "searchKey": self.records["O1"]["__search_key__"],
                "context": "publish",
                "repository": "repo",
                "files": [{"path": "source.txt"}],
                "filesDict": [("source", {})],
                "description": "Before",
            },
            "Object",
        )
        with patch(
            "thlib.checkin_operation.execute_checkin_payload",
            return_value={"code": "S1"},
        ) as execute:
            operation = self.api.submit(queue.commit, identity)
            try:
                self.assertTrue(entered.wait(3))
                queue.update(identity, {"description": "Latest edit"})
            finally:
                release.set()
            self.assertEqual(operation.wait(3), {"code": "S1"})
        self.assertEqual(execute.call_args.args[0]["description"], "Latest edit")

    def test_repository_download_uses_native_destination_and_http_size(self):
        contents = b"repository data"

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Length", str(len(contents)))
                self.end_headers()
                self.wfile.write(contents)

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        worker = threading.Thread(
            target=server.serve_forever, kwargs={"poll_interval": 0.05}
        )
        worker.start()
        destination = Path(self.directory.name) / "download.txt"
        other_transfer = destination.with_suffix(".txt.part")
        other_transfer.write_bytes(b"another runtime's staging file")
        native = SimpleNamespace(
            get_full_abs_path=lambda: str(destination),
            get_full_web_path=lambda: f"http://127.0.0.1:{server.server_port}/file",
            get_unique_id=lambda: "FILE1",
            get_filename_with_ext=lambda: destination.name,
            get_timestamp=lambda **kwargs: None,
            get_file_size=lambda: 999,
            get_md5=lambda: "",
            is_exists=destination.is_file,
            prepare_repo=Mock(return_value=str(destination)),
        )
        try:
            self.assertEqual(self.api.files.ensure_local(native), destination)
            self.assertEqual(destination.read_bytes(), contents)
            self.assertEqual(
                other_transfer.read_bytes(), b"another runtime's staging file"
            )
            self.assertEqual(list(destination.parent.glob("*.part")), [other_transfer])
            native.prepare_repo.assert_called_once()
            with self.assertRaises(InterruptedError):
                self.api.files.ensure_local(native)
            self.assertEqual(
                self.api.files.ensure_local(native, overwrite="skip"), destination
            )
            self.assertEqual(destination.read_bytes(), contents)
        finally:
            server.shutdown()
            worker.join(3)
            server.server_close()

    def test_download_failure_preserves_actual_traceback(self):
        from thlib.repository_download import DownloadOperation, SyncTask

        destination = Path(self.directory.name) / "failed.txt"
        signals = SimpleNamespace(
            failed=Mock(), finished=Mock(), cancelled=Mock(), progress=Mock()
        )
        native = SimpleNamespace(
            is_exists=lambda: False, prepare_repo=lambda: str(destination)
        )
        task = SyncTask(
            "1",
            "file",
            native,
            "File",
            "publish",
            str(destination),
            "http://example.invalid/file",
            0,
        )
        with patch("urllib.request.urlopen", side_effect=OSError("transfer failed")):
            DownloadOperation(task, signals, retries=0).run()
        signals.failed.emit.assert_called_once()
        details = signals.failed.emit.call_args.args[2]
        self.assertIn("OSError: transfer failed", details)
        self.assertIn("Traceback", details)
        self.assertEqual(list(destination.parent.glob("*.part")), [])


class ObserverTests(helpers._WorkerTestCase):
    def test_progress_observer_failure_does_not_fail_write_and_disconnects(self):
        entered, release = threading.Event(), threading.Event()
        executor = Executor(1, 1)

        def work():
            entered.set()
            if not release.wait(3):
                raise TimeoutError("test gate")
            report_progress({"percent": 50})
            return "committed"

        def bad_observer(value):
            raise ValueError("observer failure")

        operation = executor.submit(work)
        self.assertTrue(entered.wait(3))
        subscription = operation.on_progress(bad_observer)
        try:
            with self.assertLogs("tactic_handler_api.operations", "ERROR"):
                release.set()
                self.assertEqual(operation.wait(3), "committed")
            self.assertIsInstance(subscription.error, ValueError)
            self.assertIsNone(subscription._callback)
            callbacks, values = [], []
            operation.on_done(values.append, dispatch=callbacks.append)
            self.assertEqual(values, [])
            callbacks[0]()
            self.assertEqual(values, ["committed"])
        finally:
            release.set()
            executor.close()
