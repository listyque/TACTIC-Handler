"""Public API contracts: real native objects, isolated server mutations."""

from copy import deepcopy
import os
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tactic_handler_api import (
    ConcurrentEdit,
    DirtyObject,
    HandlerAPI,
    get_api,
    NotFound,
    NotReady,
    QueueFull,
    SearchKey,
    SearchResult,
)
from tactic_handler_api.operations import Executor
from tactic_handler_api.api import _bind_current


class _WorkerTestCase(unittest.TestCase):
    def run(self, result=None):
        # Exercise the public synchronous API on its supported execution thread,
        # even when another suite has already created a Qt application.
        worker = threading.Thread(target=super().run, args=(result,))
        worker.start()
        worker.join(30)
        if worker.is_alive():
            raise TimeoutError("API test worker did not finish")
        return result


class HandlerApiTests(_WorkerTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        with patch.dict(os.environ, TACTIC_QML_TEST_SETTINGS_DIR=self.directory.name):
            from thlib import tactic_classes as tc
            from thlib.environment import env_mode
        self.addCleanup(setattr, env_mode, "current_path", env_mode.current_path)
        env_mode.current_path = self.directory.name
        self.tc = tc
        self.project = tc.Project({"code": "demo"})
        self.stype = tc.SType(
            {
                "code": "types/object",
                "column_info": {
                    "code": {},
                    "description": {},
                    "pipeline_code": {},
                },
            },
            project=self.project,
        )
        self.project.stypes = {"types/object": self.stype}
        self.environment = SimpleNamespace(projects={"demo": self.project})
        self.records = {
            "O1": {
                "__search_key__": "types/object?project=demo&code=O1",
                "code": "O1",
                "description": "before",
                "pipeline_code": "original",
            },
            "O2": {
                "__search_key__": "types/object?project=demo&code=O2",
                "code": "O2",
                "description": "second",
            },
        }
        self.server = Mock()
        self.server.update.side_effect = self.update
        server_patch = patch.object(tc, "server_start", return_value=self.server)
        server_patch.start()
        self.addCleanup(server_patch.stop)
        self.core = SimpleNamespace(
            SObject=tc.SObject,
            get_sobjects=Mock(side_effect=self.query),
            insert_sobjects=Mock(side_effect=self.insert),
            edit_multiple_instance_sobjects=Mock(),
        )
        self.api = HandlerAPI(self.core, self.environment)
        self.addCleanup(self.api.close)

    def test_running_api_is_obtained_explicitly(self):
        _bind_current(self.api)
        self.assertIs(get_api(), self.api)
        self.api.close()
        with self.assertRaisesRegex(NotReady, "not running"):
            get_api()

    def query(self, search_type, **kwargs):
        records = list(self.records.values())
        for column, operator, value in kwargs["filters"]:
            self.assertEqual(operator, "=")
            records = [row for row in records if row.get(column) == value]
        total = len(records)
        offset, limit = kwargs["offset"], kwargs["limit"]
        return (
            {
                row["__search_key__"]: self.tc.SObject(deepcopy(row), self.project)
                for row in records[offset : offset + limit]
            },
            {"total_sobjects_query_count": total},
        )

    def update(self, key, data, triggers=True):
        code = SearchKey.parse(key).value
        self.records[code].update(deepcopy(data))
        return deepcopy(self.records[code])

    def insert(self, search_type, project_code, data, **kwargs):
        code = "O3"
        row = {
            **deepcopy(data),
            "code": code,
            "__search_key__": str(SearchKey(search_type, project_code, "code", code)),
        }
        self.records[code] = row
        return deepcopy(row)

    def test_edit_is_local_until_commit_and_preserves_legacy_object(self):
        obj = self.api.sobject(self.records["O1"]["__search_key__"])
        legacy = obj._native
        obj.set_value("description", "after")
        self.assertEqual(obj.get_value("description"), "after")
        self.assertEqual(legacy.get_value("description"), "before")
        self.server.update.assert_not_called()
        self.assertIs(obj.commit(), obj)
        self.assertEqual(self.records["O1"]["description"], "after")
        self.assertEqual(legacy.get_value("description"), "before")
        self.assertEqual(obj.changes(), {})
        obj.commit()
        self.server.update.assert_called_once()

    def test_failure_retains_edit_and_confirmed_state(self):
        obj = self.api.sobject(self.records["O1"]["__search_key__"])
        obj.set_value("description", "after")
        self.server.update.side_effect = OSError("offline")
        with self.assertRaisesRegex(OSError, "offline"):
            obj.commit()
        self.assertEqual(obj._info["description"], "before")
        self.assertEqual(obj.changes(), {"description": "after"})
        with self.assertRaises(DirtyObject):
            obj.refresh()
        obj.discard_changes()
        self.assertEqual(obj.get_value("description"), "before")

    def test_create_keeps_pipeline_and_explicit_relationship(self):
        stype = self.api.project("demo").stype("types/object")
        child = stype.new(
            {"name": "child", "pipeline_code": "chosen_pipeline"},
            parent=self.records["O1"]["__search_key__"],
            relation="types/instance",
        )
        with self.assertRaises(NotReady):
            child.get_search_key()
        child.commit(triggers=False)
        self.assertEqual(child.get_value("pipeline_code"), "chosen_pipeline")
        self.assertEqual(
            self.core.insert_sobjects.call_args.kwargs,
            {
                "parent_key": self.records["O1"]["__search_key__"],
                "instance_type": "types/instance",
                "instance_path": "child",
                "triggers": False,
            },
        )

    def test_related_resolves_the_native_search_type(self):
        obj = self.api.sobject(self.records["O1"]["__search_key__"])
        related = self.tc.SObject(deepcopy(self.records["O2"]), self.project)
        obj._native.get_related_sobjects = Mock(
            return_value={related.get_search_key(): related}
        )

        result = obj.related(search_type="types/object")

        self.assertEqual([item.get_code() for item in result], ["O2"])
        self.assertIs(
            obj._native.get_related_sobjects.call_args.kwargs["child_stype"],
            self.stype,
        )

    def test_link_connects_an_existing_object_through_the_domain_api(self):
        parent = self.api.sobject(self.records["O1"]["__search_key__"])
        child = self.api.sobject(self.records["O2"]["__search_key__"])

        parent.link(child, relation="types/instance")

        self.core.edit_multiple_instance_sobjects.assert_called_once_with(
            "demo",
            insert_search_keys=[child.get_search_key()],
            parent_key=parent.get_search_key(),
            instance_type="types/instance",
            path=None,
        )

    def test_search_result_and_empty_results_keep_one_shape(self):
        stype = self.api.project("demo").stype("types/object")
        result = stype.query(limit=1)
        self.assertIsInstance(result, SearchResult)
        self.assertEqual(result.total, 2)
        self.assertEqual((result.offset, result.limit), (0, 1))
        self.assertTrue(result.has_more)
        self.assertEqual(result.items[0].get_code(), "O1")
        last = result.next()
        self.assertIsInstance(last, SearchResult)
        self.assertEqual(last.offset, 1)
        self.assertEqual(last.items[0].get_code(), "O2")
        self.assertFalse(last.has_more)
        calls = self.core.get_sobjects.call_count
        empty = last.next()
        self.assertIsInstance(empty, SearchResult)
        self.assertEqual(empty.items, ())
        self.assertEqual(self.core.get_sobjects.call_count, calls)
        with self.assertRaises(NotFound):
            stype.get(code="missing")
        self.assertEqual(stype.query([("code", "=", "missing")]).items, ())
        stype.query(order_by=["description desc"])
        self.assertEqual(
            self.core.get_sobjects.call_args.kwargs["order_bys"],
            ["description desc", "code"],
        )
        with self.assertRaises(TypeError):
            stype.query(order_by="description")

    def test_invalid_identity_and_paging_are_rejected_before_network(self):
        for key in (
            "types/object?code=O1",
            "types/object?project=demo&code=O1&id=1",
            "types/object?project=demo&code=O1&code=O2",
        ):
            with self.assertRaises(ValueError):
                self.api.sobject(key)
        stype = self.api.project("demo").stype("types/object")
        for limit in (0, 1001, True):
            with self.assertRaises(ValueError):
                stype.query(limit=limit)
        self.core.get_sobjects.assert_not_called()

    def test_concurrent_mutation_of_one_editor_is_rejected(self):
        obj = self.api.sobject(self.records["O1"]["__search_key__"])
        obj.set_value("description", "after")
        entered, release = threading.Event(), threading.Event()

        def delayed(*args, **kwargs):
            entered.set()
            if not release.wait(3):
                raise TimeoutError("test gate")
            return self.update(*args, **kwargs)

        self.server.update.side_effect = delayed
        operation = self.api.submit(obj.commit)
        try:
            self.assertTrue(entered.wait(3))
            with self.assertRaises(ConcurrentEdit):
                obj.set_value("description", "race")
        finally:
            release.set()
        self.assertIs(operation.wait(3), obj)


class ExecutorTests(_WorkerTestCase):
    def test_nonblocking_close_drains_running_domain_operation(self):
        entered, release = threading.Event(), threading.Event()
        api = HandlerAPI(None, None)

        def work():
            entered.set()
            if not release.wait(3):
                raise TimeoutError("test gate")
            api._check()
            return 42

        operation = api.submit(work)
        try:
            self.assertTrue(entered.wait(3))
            api.close(wait=False)
            with self.assertRaises(RuntimeError):
                api.submit(lambda: None)
            with self.assertRaises(RuntimeError):
                api._check()
            release.set()
            self.assertEqual(operation.wait(3), 42)
        finally:
            release.set()
            api.close()

    def test_bounded_work_callbacks_and_cancellation(self):
        executor = Executor(1, 2)
        entered, release = threading.Event(), threading.Event()

        def gated():
            entered.set()
            if not release.wait(3):
                raise TimeoutError("test gate")
            return 42

        first = executor.submit(gated)
        try:
            self.assertTrue(entered.wait(3))
            second = executor.submit(lambda: None)
            with self.assertRaises(QueueFull):
                executor.submit(lambda: None)
            with self.assertRaises(NotReady):
                first.result()
            self.assertTrue(second.cancel())
            self.assertFalse(first.cancel())
            values = []
            called = threading.Event()
            first.on_done(lambda value: (values.append(value), called.set()))
            first.on_done(lambda value: self.fail("disconnected callback")).close()
            release.set()
            self.assertEqual(first.wait(3), 42)
            self.assertTrue(called.wait(3))
            self.assertEqual(values, [42])
        finally:
            release.set()
            executor.close()
        with self.assertRaises(RuntimeError):
            executor.submit(lambda: None)


if __name__ == "__main__":
    unittest.main()
