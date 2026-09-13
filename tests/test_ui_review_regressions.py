"""Small deterministic checks for the UI complexity review's hot paths."""

import ast
import random
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from unittest.mock import patch

from thlib.ui import script_editor_features as features
from thlib.ui.task_data import gantt_layout
from tests.qt_application import gui_test_application


class ScriptParsingTests(unittest.TestCase):
    def tearDown(self):
        features._safe_tree.cache_clear()

    def test_early_error_does_not_retry_every_trailing_line(self):
        source = "import json\n" + "x = 1\n" * 9 + "broken =\n" + "x = 2\n" * 3000
        with patch.object(features.ast, "parse", wraps=ast.parse) as parse:
            tree = features._safe_tree(source)
        self.assertIsInstance(tree, ast.Module)
        self.assertLessEqual(parse.call_count, 3)
        self.assertEqual(len(tree.body), 10)

    def test_consumers_share_the_same_revision_without_stale_results(self):
        source = "import json\ndef first():\n    pass\n"
        with patch.object(features.ast, "parse", wraps=ast.parse) as parse:
            features.document_symbols(source)
            features._imported_display_names(source)
            features._safe_tree(source)
        self.assertEqual(parse.call_count, 1)
        self.assertEqual(features.document_symbols(source.replace("first", "second"))[0]["name"], "second")

    def test_incomplete_nested_definition_keeps_completed_prefix(self):
        symbols = features.document_symbols("def first():\n    pass\n\nclass Pending:\n    def next(self):\n")
        self.assertEqual([item["name"] for item in symbols], ["first"])


class GanttOverlapTests(unittest.TestCase):
    def test_overlap_flags_match_pairwise_reference(self):
        rng = random.Random(71)
        today = date(2026, 9, 1)
        spans = [(rng.randrange(25), rng.randrange(1, 14), str(rng.randrange(4))) for _ in range(120)]
        records = [{
            "taskCode": str(index), "assigned": login,
            "start": (today + timedelta(days=start)).isoformat(),
            "end": (today + timedelta(days=start + duration - 1)).isoformat(),
        } for index, (start, duration, login) in enumerate(spans)]
        result = gantt_layout(records, today=today)
        for record in result["records"]:
            index = int(record["taskCode"])
            start, duration, login = spans[index]
            expected = any(
                other != index and other_login == login
                and start <= other_start + other_duration - 1
                and other_start <= start + duration - 1
                for other, (other_start, other_duration, other_login) in enumerate(spans)
            )
            self.assertEqual("overlapping tasks" in record["ganttWarning"], expected)
            self.assertLessEqual(record["ganttWarning"].count("overlapping tasks"), 1)


class SharedStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def test_record_lookup_invalidates_after_changes_removal_and_reset(self):
        from thlib.ui.workspace_models.records import RecordListModel

        model = RecordListModel(("login", "name"), [
            {"login": "a", "name": "First"}, {"login": "b", "name": "Second"},
        ])
        self.assertEqual(model.lookup("login", "b")["name"], "Second")
        index = model._lookup_indexes["login"]
        self.assertEqual(model.lookup("login", "a")["name"], "First")
        self.assertIs(index, model._lookup_indexes["login"])
        model.remove(0)
        self.assertEqual(model.lookup("login", "b")["name"], "Second")
        model.replace([{"login": "b", "name": "Changed"}])
        self.assertEqual(model.lookup("login", "b")["name"], "Changed")
        model.clear()
        self.assertEqual(model.lookup("login", "b"), {})

    def test_composers_share_serial_writer_and_flush_last_context_on_shutdown(self):
        from thlib.ui.composer_drafts import ComposerDrafts
        from thlib.ui.config_persistence import ConfigWriteQueue

        writes = []
        gui_thread = threading.get_ident()
        def writer(payload, **location):
            writes.append((payload, location["unique_id"], threading.get_ident()))

        queue = ConfigWriteQueue(writer=writer)
        notes = ComposerDrafts("cache/notes", {}, queue=queue)
        messages = ComposerDrafts("cache/messages", {}, queue=queue)
        try:
            notes.activate("object/model")
            notes.set_text("Keep this note")
            notes.activate("object/rig")
            notes.set_text("Another process")
            messages.activate("chat/1")
            messages.set_text("Keep this message")
            notes.shutdown()
            messages.shutdown()
            queue.flush()
            self.assertFalse(queue._closed)
            self.assertTrue(all(thread != gui_thread for _, _, thread in writes))
            final = {namespace: payload for payload, namespace, _ in writes}
            self.assertEqual(final["cache/notes"]["contexts"], {
                "object/model": "Keep this note", "object/rig": "Another process",
            })
            self.assertEqual(final["cache/messages"]["contexts"], {"chat/1": "Keep this message"})
            restored = ComposerDrafts("cache/notes", final["cache/notes"], queue=queue)
            restored.activate("object/model")
            self.assertEqual(restored.text, "Keep this note")
            restored.clear("object/rig")
            self.assertEqual(restored.text, "Keep this note")
            restored.shutdown()
        finally:
            queue.shutdown()

    def test_report_inspects_files_only_after_files_page_and_ignores_stale_result(self):
        from PySide6.QtCore import QObject, Signal
        from thlib.environment import env_inst
        from tests.test_sobject_info import FakeApplication, FakeSObject, FakeProcess, FakeContext, FakeSnapshot, FakeFile
        from thlib.ui.sobject_info import SObjectInfoController

        class Worker(QObject):
            result = Signal(object)
            error = Signal(object)
            def start(self):
                pass
            def cancel(self):
                pass

        class Pool:
            is_stopped = False
            worker = None
            def add_task(self, operation, *args):
                self.worker = Worker()
                self.operation = lambda: operation(*args)
                return self.worker

        checked_threads = []
        file = FakeFile("scene.ma")
        file.is_exists = lambda: checked_threads.append(threading.get_ident()) or True
        snapshot = FakeSnapshot("S1", 1, "artist", [file])
        application = FakeApplication()
        application.workspace_state._selected_sobject = FakeSObject(FakeProcess(FakeContext([snapshot], [])))
        pool = Pool()
        with patch.object(env_inst, "server_pool", pool):
            controller = SObjectInfoController(application)
            self.assertEqual(checked_threads, [])
            self.assertEqual(controller.files.count(), 0)
            controller.set_page(3)
            self.assertEqual(checked_threads, [])
            self.assertTrue(controller.busy)
            with ThreadPoolExecutor(max_workers=1) as executor:
                result = executor.submit(pool.operation).result()
            self.assertNotEqual(checked_threads[0], threading.get_ident())
            pool.worker.result.emit(result)
            self.app.processEvents()
            self.assertFalse(controller.busy)
            self.assertTrue(controller.files.get(0)["exists"])
            request_id = controller._file_request_id
            controller._selection_changed()
            controller._files_ready(request_id, {123: {"exists": True, "url": ""}})
            self.assertNotIn(123, controller._file_metadata)
            controller.shutdown()


if __name__ == "__main__":
    unittest.main()
