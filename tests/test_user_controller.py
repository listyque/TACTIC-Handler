import unittest
from unittest.mock import patch

from modern_ui.user import UserController
from modern_ui.group_authority import primary_group, ranked_groups


class FakeTaskPipeline:
    pipeline = {"Paid": {"color": "#27ae60"}}


class FakeWorkflow:
    def get_by_pipeline_code(self, search_type, pipeline_code):
        if search_type == "sthpw/task" and pipeline_code == "task_pipe":
            return FakeTaskPipeline()
        return None


class FakeParentPipeline:
    def get_process_info(self, process):
        if process == "script":
            return {
                "label": "Script", "color": "#b54f3e",
                "task_pipeline": "task_pipe",
            }
        return {}

    def get_pipeline_process(self, process):
        return {"color": "#b54f3e"} if process == "script" else None


class FakeSType:
    def get_code(self):
        return "niki_friends/episodes"

    def get_pipeline(self):
        return {"dialog": FakeParentPipeline()}


class FakeProject:
    def get_workflow(self):
        return FakeWorkflow()

    def get_stypes(self):
        return {"niki_friends/episodes": FakeSType()}


class UserActivityTests(unittest.TestCase):
    @staticmethod
    def _profile_controller():
        class WindowModel:
            def __init__(self):
                self.shown = []

            def show_window(self, window_id):
                self.shown.append(window_id)

        class Application:
            def __init__(self):
                self.window_model = WindowModel()
                self.authentication_requested = False

            def request_authentication(self):
                self.authentication_requested = True

        controller = UserController.__new__(UserController)
        controller._application = Application()
        controller._selected_login = "artist"
        controller._directory_visible = True
        controller._rebuild = lambda: None
        controller.refresh = lambda: None
        return controller

    def test_my_profile_hides_user_directory(self):
        controller = self._profile_controller()
        controller._current_login = lambda: "artist"

        controller.open_current()

        self.assertFalse(controller._directory_visible)
        self.assertEqual(
            controller._application.window_model.shown, ["user_profile"]
        )

    def test_users_mode_keeps_directory_while_selecting_profile(self):
        controller = self._profile_controller()

        controller.open_users()
        controller.select_profile("supervisor")

        self.assertTrue(controller._directory_visible)
        self.assertEqual(controller._selected_login, "supervisor")

    def test_primary_group_prefers_explicit_access_level(self):
        groups = [
            {"code": "lighter", "label": "Lighter", "accessLevel": "low"},
            {"code": "generalist", "label": "Generalist", "accessLevel": "low"},
            {"code": "supervisor", "label": "Supervisor", "accessLevel": "high"},
        ]

        self.assertEqual(primary_group(groups)["code"], "supervisor")
        self.assertEqual(ranked_groups(groups)[0]["label"], "Supervisor")

    def test_zero_access_level_does_not_hide_supervisor_role(self):
        groups = [
            {"code": "lighter", "label": "Lighter", "accessLevel": "0"},
            {"code": "generalist", "label": "Generalist", "accessLevel": "0"},
            {"code": "supervisor", "label": "Supervisor", "accessLevel": "0"},
        ]

        self.assertEqual(primary_group(groups)["code"], "supervisor")

    def test_primary_group_uses_rules_before_name_fallback(self):
        groups = [
            {"code": "artist", "label": "Artist", "accessRules": ""},
            {
                "code": "production_control",
                "label": "Production Control",
                "accessRules": (
                    '<rules><rule group="task" access="allow" '
                    'name="approve"/></rules>'
                ),
            },
        ]

        self.assertEqual(
            primary_group(groups)["code"], "production_control"
        )

    def test_recent_note_navigation_keeps_activity_process(self):
        class ActivityModel:
            _records = [{
                "searchKey": "skey://sthpw/note?code=NOTE001",
                "targetSearchKey": (
                    "skey://demo/asset?project=demo&code=ASSET001"
                ),
                "process": "model",
                "context": "model/review",
            }]

        class Resolver:
            def __init__(self):
                self.calls = []

            def open_in_context(self, *args):
                self.calls.append(args)

        controller = UserController.__new__(UserController)
        controller.activity = ActivityModel()
        controller._skey_previews = Resolver()

        controller.open_activity("skey://sthpw/note?code=NOTE001")

        self.assertEqual(controller._skey_previews.calls, [(
            "skey://sthpw/note?code=NOTE001",
            "skey://demo/asset?project=demo&code=ASSET001",
            "model",
        )])

    def test_task_summary_style_uses_cached_workflow_colors(self):
        style = UserController._workflow_task_style({
            "search_type": "niki_friends/episodes?project=niki_friends",
            "pipeline_code": "task_pipe",
            "process": "script",
            "status": "Paid",
        }, FakeProject())

        self.assertEqual(style["processLabel"], "Script")
        self.assertEqual(style["processColor"], "#b54f3e")
        self.assertEqual(style["statusColor"], "#27ae60")

    def test_presence_uses_server_state_and_current_login_fallback(self):
        controller = UserController.__new__(UserController)
        controller._presence_by_login = {
            "other": {
                "online": True,
                "lastSeen": "2026-08-11T10:00:00Z",
            },
        }
        self.assertEqual(
            controller._presence("other", "artist", "online"),
            {
                "presenceKnown": True,
                "online": True,
                "lastSeen": "2026-08-11T10:00:00Z",
            },
        )
        self.assertEqual(
            controller._presence("artist", "artist", "offline"),
            {"presenceKnown": True, "online": False, "lastSeen": ""},
        )
        self.assertEqual(
            controller._presence("unknown", "artist", "online"),
            {"presenceKnown": False, "online": False, "lastSeen": ""},
        )

    def test_recent_activity_uses_aggregated_server_query(self):
        activity = {
            "searchKey": "skey://sthpw/status_log?id=1",
            "title": "TASK0001",
            "detail": "Pending -> In Progress",
            "timestamp": "2026-08-10 12:00:00",
            "project": "test",
        }
        with patch(
                "thlib.tactic_classes.get_user_profile_data",
                return_value={
                    "activity": [activity], "tasks": [], "taskTotal": 0,
                    "taskSummary": {}, "statusSummary": [],
                    "processSummary": [],
                }) as activity_query:
            result = UserController._load_related("artist", "test")

        activity_query.assert_called_once_with(
            "artist", project_code="test", activity_limit=25
        )
        self.assertEqual(len(result["activity"]), 1)
        self.assertEqual(result["activity"][0]["title"], "TASK0001")
        self.assertEqual(
            result["activity"][0]["detail"], "Pending -> In Progress"
        )
        self.assertEqual(result["activityError"], "")


if __name__ == "__main__":
    unittest.main()
