import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from tests.qt_application import gui_test_application
from thlib.ui.task_workspace import TaskWorkspaceStore


class FakeParent:
    def __init__(self, search_type, code, project="test"):
        self.search_type = search_type
        self.code = code
        self.project = project

    def get_info(self):
        return {"code": self.code, "project_code": self.project}

    def get_code(self):
        return self.code

    def get_plain_search_type(self):
        return self.search_type

    def get_search_key(self):
        return "skey://{}?project={}&code={}".format(
            self.search_type, self.project, self.code
        )

    def get_stype(self):
        return type("FakeStype", (), {
            "get_code": lambda _self: self.search_type,
        })()


class FakeTask:
    def __init__(self, code, parent_type="prod/asset", parent_code="ITEM0001"):
        self.info = {
            "code": code,
            "search_type": parent_type,
            "search_code": parent_code,
            "project_code": "test",
            "process": "model",
        }

    def get_info(self):
        return dict(self.info)


class FakeLogin:
    def __init__(self, login):
        self.login = login

    def get_login(self):
        return self.login


class FakeGroup:
    def __init__(self, code, logins):
        self.code = code
        self.logins = [FakeLogin(login) for login in logins]

    def get_code(self):
        return self.code

    def get_login_group(self):
        return self.code

    def get_logins(self):
        return list(self.logins)


class FakeCurrentLogin:
    def __init__(self, groups):
        self.groups = groups

    def get_login_groups(self):
        return list(self.groups)


class TaskWorkspaceStoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def test_parent_identity_includes_search_type_and_project(self):
        store = TaskWorkspaceStore()
        asset = FakeParent("prod/asset", "ITEM0001")
        shot = FakeParent("prod/shot", "ITEM0001")
        store.set_parents([asset, shot])

        self.assertIs(
            store.parent_for_task(FakeTask("TASK1", "prod/asset")), asset
        )
        self.assertIs(
            store.parent_for_task(FakeTask("TASK2", "prod/shot")), shot
        )

    def test_appended_page_replaces_duplicate_without_duplicate_row(self):
        store = TaskWorkspaceStore()
        original = FakeTask("TASK1")
        replacement = FakeTask("TASK1")
        second = FakeTask("TASK2")

        store.apply_source(
            [original], [], page={"loaded": 1, "hasMore": True}
        )
        store.apply_source(
            [replacement, second], [],
            page={"loaded": 2, "hasMore": False, "total": 2},
            append=True,
        )

        self.assertEqual(store.task_order, ["TASK1", "TASK2"])
        self.assertIs(store.tasks["TASK1"], replacement)
        self.assertEqual(store.offset, 3)
        self.assertFalse(store.has_more)
        self.assertEqual(store.total_count, 2)

    def test_scope_change_invalidates_active_request(self):
        store = TaskWorkspaceStore()
        request_id = store.begin_load()
        self.assertTrue(store.accepts(request_id))

        store.set_scope("project")

        self.assertFalse(store.accepts(request_id))
        self.assertFalse(store.busy)

    def test_project_page_uses_total_count_for_has_more(self):
        import thlib.tactic_classes as tc

        tasks = [FakeTask("TASK501")]
        task_result = {
            "tasks": tasks, "parents": [], "total": 501,
            "offset": 500, "limit": 500,
        }
        calls = []

        def get_page(filters, order_bys, project_code, **kwargs):
            calls.append((filters, order_bys, project_code, kwargs))
            return task_result

        with patch.object(tc, "get_task_workspace_page", side_effect=get_page):
            result = TaskWorkspaceStore.load_scope(
                "project", "", "test", None, "", [],
                offset=500, limit=500,
            )

        self.assertEqual(result["page"]["total"], 501)
        self.assertFalse(result["page"]["hasMore"])
        task_call = calls[0][3]
        self.assertEqual(task_call["offset"], 500)
        self.assertEqual(task_call["limit"], 500)

    def test_object_scope_uses_workspace_page_with_note_counts(self):
        import thlib.tactic_classes as tc

        parent = FakeParent("prod/asset", "ASSET001")
        task = FakeTask("TASK001", parent_code="ASSET001")
        server = type("FakeServer", (), {
            "build_search_type": lambda _self, value, project: (
                "{}?project={}".format(value, project)
            ),
        })()
        calls = []

        def get_page(filters, order_bys, project_code, **kwargs):
            calls.append((filters, order_bys, project_code, kwargs))
            return {"tasks": [task], "parents": [], "total": 1}

        with patch.object(tc, "server_start", return_value=server), \
                patch.object(
                    tc, "get_task_workspace_page", side_effect=get_page
                ):
            result = TaskWorkspaceStore.load_scope(
                "object", "", "test", parent, parent.get_search_key(), []
            )

        self.assertEqual(result["tasks"], [task])
        self.assertEqual(result["parents"], [parent])
        self.assertEqual(result["page"]["total"], 1)
        self.assertEqual(len(calls), 1)
        self.assertIn(
            ("search_type", "prod/asset?project=test"), calls[0][0]
        )
        self.assertIn(("search_code", "ASSET001"), calls[0][0])

    def test_object_scope_resolves_native_tactic_search_key(self):
        import thlib.tactic_classes as tc

        parent = FakeParent("prod/asset", "ASSET001")
        task = FakeTask("TASK001", parent_code="ASSET001")
        native_key = "prod/asset?project=test&code=ASSET001"
        server = type("FakeServer", (), {
            "build_search_type": lambda _self, value, project: (
                "{}?project={}".format(value, project)
            ),
        })()

        with patch.object(
                tc, "split_search_key", return_value={
                    "search_type": "prod/asset?project=test",
                    "asset_code": "ASSET001",
                    "pipeline_code": "prod/asset",
                    "project_code": "test",
                }), patch.object(
                    tc, "get_sobjects", return_value=({
                        parent.get_search_key(): parent,
                    }, {}),
                ) as get_sobjects, patch.object(
                    tc, "server_start", return_value=server,
                ), patch.object(
                    tc, "get_task_workspace_page", return_value={
                        "tasks": [task], "parents": [], "total": 1,
                    },
                ):
            result = TaskWorkspaceStore.load_scope(
                "object", "", "test", None, native_key, []
            )

        self.assertIs(result["target"], parent)
        self.assertEqual(result["tasks"], [task])
        get_sobjects.assert_called_once_with(
            "prod/asset",
            filters=[("code", "=", "ASSET001")],
            project_code="test",
            limit=1,
        )

    def test_empty_object_scope_does_not_parse_a_missing_search_key(self):
        import thlib.tactic_classes as tc

        with patch.object(tc, "parce_skey") as parse_search_key:
            result = TaskWorkspaceStore.load_scope(
                "object", "", "test", None, "", []
            )

        parse_search_key.assert_not_called()
        self.assertEqual(result["tasks"], [])
        self.assertEqual(result["parents"], [])
        self.assertEqual(result["page"]["queryCount"], 0)

    def test_multiple_scope_restores_targets_from_saved_search_keys(self):
        import thlib.tactic_classes as tc

        first = FakeParent("prod/asset", "ASSET001")
        second = FakeParent("prod/asset", "ASSET002")
        task = FakeTask("TASK001", parent_code="ASSET001")
        targets_by_key = {
            first.get_search_key(): first,
            second.get_search_key(): second,
        }

        with patch(
                "thlib.ui.task_workspace.store."
                "_resolve_target_from_search_key",
                side_effect=lambda _tc, key, _project: targets_by_key[key],
        ), patch.object(
                tc, "get_task_workspace_page",
                return_value={"tasks": [task], "parents": [first, second], "total": 1},
        ) as load_tasks:
            result = TaskWorkspaceStore.load_scope(
                "multiple", "", "test", None, "",
                [first.get_search_key(), second.get_search_key()],
            )

        self.assertEqual(load_tasks.call_count, 1)
        self.assertEqual(load_tasks.call_args.kwargs["limit"], 500)
        self.assertIn(("search_code", "ASSET001"), load_tasks.call_args.args[0])
        self.assertIn(("search_code", "ASSET002"), load_tasks.call_args.args[0])
        self.assertEqual(result["parents"], [first, second])
        self.assertEqual(result["tasks"], [task])

    def test_user_scope_uses_filtered_total_instead_of_table_total(self):
        import thlib.tactic_classes as tc

        tasks = [FakeTask("TASK{}".format(index)) for index in range(1, 8)]
        task_result = {
            "tasks": tasks, "parents": [], "total": 7,
            "offset": 0, "limit": 500,
        }

        def get_page(*_args, **_kwargs):
            return task_result

        with patch.object(tc, "get_task_workspace_page", side_effect=get_page):
            result = TaskWorkspaceStore.load_scope(
                "user", "artist", "test", None, "", [],
                offset=0, limit=500,
            )

        self.assertEqual(result["page"]["total"], 7)
        self.assertFalse(result["page"]["hasMore"])

    def test_user_scope_retains_assignee_when_payload_omits_column(self):
        store = TaskWorkspaceStore()
        task = FakeTask("TASK0001")
        store.set_scope("user", user="artist")
        store.apply_source([task], [])

        self.assertEqual(
            store.assignee_for_task_info(task.get_info()), "artist"
        )

    def test_team_scope_filters_one_task_query_by_members(self):
        import thlib.tactic_classes as tc
        from thlib.environment import env_inst

        calls = []

        def get_page(filters, order_bys, project_code, **kwargs):
            calls.append((filters, order_bys, project_code, kwargs))
            return {"tasks": [], "parents": [], "total": 0}

        login = FakeCurrentLogin([FakeGroup("artists", ["a", "b"])])
        with patch.object(env_inst, "get_current_login_object", return_value=login), \
                patch.object(tc, "get_task_workspace_page", side_effect=get_page):
            TaskWorkspaceStore.load_scope(
                "team", "artists", "test", None, "", []
            )

        self.assertEqual(len(calls), 1)
        self.assertIn(("assigned", "in", "a|b"), calls[0][0])


if __name__ == "__main__":
    unittest.main()
