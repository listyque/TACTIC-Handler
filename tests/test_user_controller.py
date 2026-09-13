import os
from pathlib import Path
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtTest import QTest

from thlib.ui.user import UserController
from thlib.ui.activity import JOURNAL_ACTIVITY_KINDS
from thlib.ui.group_authority import primary_group, ranked_groups
from thlib.ui.workspace_models.records import RecordListModel


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib" / "ui" / "qml"


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
                self.closed = []

            def show_window(self, window_id):
                self.shown.append(window_id)

            def close_window(self, window_id):
                self.closed.append(window_id)

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
        self.assertEqual(controller._application.window_model.closed, ["users"])

    def test_users_mode_keeps_directory_while_selecting_profile(self):
        controller = self._profile_controller()

        controller.open_users()
        controller.select_profile("supervisor")

        self.assertTrue(controller._directory_visible)
        self.assertEqual(controller._selected_login, "supervisor")
        self.assertEqual(
            controller._application.window_model.shown, ["users", "users"]
        )
        self.assertEqual(
            controller._application.window_model.closed,
            ["user_profile", "user_profile"],
        )

    def test_chat_participant_opens_profile_without_changing_identity(self):
        controller = self._profile_controller()
        controller._current_login = lambda: "artist"

        controller.open_profile("supervisor")

        self.assertEqual(controller._selected_login, "supervisor")
        self.assertFalse(controller._directory_visible)
        self.assertEqual(controller._current_login(), "artist")
        self.assertEqual(
            controller._application.window_model.shown, ["user_profile"]
        )
        self.assertEqual(
            controller._application.window_model.closed, ["users"]
        )

    def test_current_identity_does_not_follow_selected_profile(self):
        class Users:
            _records = [{
                "login": "artist",
                "displayName": "Ada Artist",
                "initials": "AA",
                "avatarUrl": "file:///avatars/artist.png",
                "avatarColor": "#123456",
            }, {
                "login": "supervisor",
                "displayName": "Sam Supervisor",
                "initials": "SS",
                "avatarUrl": "file:///avatars/supervisor.png",
                "avatarColor": "#654321",
            }]

        controller = UserController.__new__(UserController)
        QObject.__init__(controller)
        controller.users = Users()
        controller._profile = {
            "login": "supervisor",
            "displayName": "Sam Supervisor",
            "initials": "SS",
            "avatarUrl": "file:///avatars/supervisor.png",
            "avatarColor": "#654321",
        }
        controller._current_login = lambda: "artist"

        self.assertEqual(controller.login, "artist")
        self.assertEqual(controller.displayName, "Ada Artist")
        self.assertEqual(controller.initials, "AA")
        self.assertEqual(controller.avatarUrl, "file:///avatars/artist.png")
        self.assertEqual(controller.avatarColor, "#123456")
        self.assertEqual(controller.profile["login"], "supervisor")

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

    def test_profile_opens_full_activity_with_selected_user(self):
        class ActivityFeed:
            def __init__(self):
                self.users = []

            def select_user_feed(self, login):
                self.users = [login]

        controller = self._profile_controller()
        controller._profile = {"login": "supervisor"}
        controller._activity_feed = ActivityFeed()
        controller._current_login = lambda: "artist"

        controller.open_full_activity()

        self.assertEqual(controller._activity_feed.users, ["supervisor"])
        self.assertEqual(
            controller._application.window_model.shown, ["activity_feed"]
        )

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

    def test_recent_activity_uses_the_same_complete_journal_as_feed(self):
        activity = {
            "eventId": "note:NOTE0001",
            "kind": "note",
            "searchKey": "skey://sthpw/note?code=NOTE0001",
            "title": "Added note",
            "detail": "Please review",
            "timestamp": "2026-08-10 12:00:00",
            "project": "test",
        }
        with (
            patch(
                "thlib.tactic_classes.get_user_profile_data",
                return_value={
                    "taskSummary": {
                        "total": 3, "incomplete": 2,
                        "overdue": 1, "dueThisWeek": 1,
                    },
                    "workHourSummary": {
                        "loggedHours": 8.0, "approvedHours": 6.0,
                        "pendingHours": 2.0,
                        "periodStart": "2026-08-10",
                        "periodEnd": "2026-08-16",
                    },
                    "permissions": {"viewWorkHours": True},
                    "statusSummary": [], "processSummary": [],
                },
            ) as profile_query,
            patch(
                "thlib.tactic_classes.get_user_recent_activity",
                return_value={"records": [activity]},
            ) as activity_query,
        ):
            result = UserController._load_related("artist", "test")

        profile_query.assert_called_once_with(
            "artist", project_code="test"
        )
        activity_query.assert_called_once_with(
            "", project_code="test", limit=25, offset=0,
            kinds=JOURNAL_ACTIVITY_KINDS, logins=["artist"],
        )
        self.assertEqual(len(result["activity"]), 1)
        self.assertEqual(result["activity"][0]["kind"], "note")
        self.assertEqual(
            result["activity"][0]["detail"], "Please review"
        )
        self.assertEqual(result["activityError"], "")
        self.assertNotIn("tasks", result)
        self.assertNotIn("taskTotal", result)
        self.assertEqual(result["taskSummary"]["incomplete"], 2)
        self.assertEqual(result["workHourSummary"]["loggedHours"], 8.0)
        self.assertTrue(result["canViewWorkHours"])

    def test_recent_activity_uses_actor_profile_avatar_and_initials(self):
        records = UserController._present_activity_records(
            [{"actor": "artist", "title": "Published snapshot"}],
            [{
                "login": "artist",
                "displayName": "Ada Artist",
                "initials": "AA",
                "avatarUrl": "file:///avatars/artist.png",
            }],
        )

        self.assertEqual(records[0]["actorLabel"], "Ada Artist")
        self.assertEqual(records[0]["actorInitials"], "AA")
        self.assertEqual(
            records[0]["actorAvatar"], "file:///avatars/artist.png"
        )

    def test_profile_avatar_prefers_web_file_over_tiny_icon_derivative(self):
        class AvatarFile:
            def __init__(self, path):
                self.path = path
                self.web = None
                self.icon = None

            def get_web_preview(self):
                return self.web

            def get_icon_preview(self):
                return self.icon

            def get_full_abs_path(self):
                return self.path

            def is_local_current(self):
                return True

        web = AvatarFile("C:/avatars/artist-web.jpg")
        icon = AvatarFile("C:/avatars/artist-icon.jpg")
        web.web = web
        web.icon = icon
        icon.web = web
        icon.icon = icon

        class Snapshot:
            def get_files_objects(self, group_by=None):
                return {"icon": [icon], "web": [web]}

        context = type("Context", (), {
            "versionless": {"SNAPSHOT": Snapshot()}, "versions": {},
        })()
        process = type("Process", (), {
            "contexts": {"icon": context},
        })()
        login = type("Login", (), {"process": {"icon": process}})()
        controller = UserController.__new__(UserController)
        controller._pending_avatar_paths = set()
        controller._application = type("Application", (), {
            "repository_sync": object(),
        })()

        avatar_url = controller._avatar_url(login)

        self.assertIn("artist-web.jpg", avatar_url)
        self.assertNotIn("artist-icon.jpg", avatar_url)

    def test_recent_activity_falls_back_to_login_initials(self):
        records = UserController._present_activity_records(
            [{"actor": "listy"}], [],
        )

        self.assertEqual(records[0]["actorLabel"], "listy")
        self.assertEqual(records[0]["actorInitials"], "L")
        self.assertEqual(records[0]["actorAvatar"], "")


class UserActivityQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_recent_activity_delegate_receives_actor_identity_roles(self):
        model = RecordListModel((
            "actor", "actorLabel", "actorAvatar", "actorInitials",
        ))
        model.replace([{
            "actor": "artist",
            "actorLabel": "Ada Artist",
            "actorAvatar": "",
            "actorInitials": "AA",
        }])
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        engine.rootContext().setContextProperty("activityModel", model)
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "."
Window {
    width: 520
    height: 140
    visible: true
    Theme { id: theme; dark: true }
    ListView {
        objectName: "activityList"
        anchors.fill: parent
        model: activityModel
        delegate: Item {
            objectName: "activityDelegate"
            required property string actor
            required property string actorLabel
            required property string actorAvatar
            required property string actorInitials
            property alias displayedActorLabel: card.actorLabel
            property alias displayedActorInitials: card.actorInitials
            width: ListView.view.width
            height: card.implicitHeight
            ActivityEventCard {
                id: card
                objectName: "recentActivityCard"
                anchors.fill: parent
                theme: theme
                actor: parent.actor
                actorLabel: parent.actorLabel
                actorAvatar: parent.actorAvatar
                actorInitials: parent.actorInitials
            }
        }
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_UserActivityIdentityTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(30)
            activity_list = owner.findChild(QObject, "activityList")
            self.assertIsNotNone(activity_list)
            self.assertEqual(activity_list.property("count"), 1)
            delegate, undefined = QQmlExpression(
                QQmlEngine.contextForObject(activity_list),
                activity_list,
                "itemAtIndex(0)",
            ).evaluate()
            self.assertFalse(undefined)
            self.assertIsNotNone(delegate)
            self.assertEqual(
                delegate.property("displayedActorLabel"), "Ada Artist"
            )
            self.assertEqual(delegate.property("displayedActorInitials"), "AA")
        finally:
            owner.close()
            owner.deleteLater()

    def test_activity_card_renders_one_human_readable_sentence(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "."
Window {
    width: 720
    height: 160
    visible: true
    Theme { id: theme; dark: true }
    ActivityEventCard {
        anchors.fill: parent
        theme: theme
        kind: "publication"
        actorLabel: "Ada Artist"
        targetTitle: "ep_79"
        targetType: "demo/episode"
        itemTitle: "ep_79_render_v003.mov"
        detail: "Final lighting pass"
        process: "render"
        context: "render/final"
        version: "3"
        typeColor: "#5c6bc0"
        processColor: "#ef5350"
        canOpenActivity: true
        canOpenTarget: true
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_ActivitySentenceTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(30)
            sentence = owner.findChild(QObject, "activitySentence")
            self.assertIsNotNone(sentence)
            text = sentence.property("text")
            self.assertIn("ep_79", text)
            self.assertIn("render", text)
            self.assertIn("render/final", text)
            self.assertIn("ep_79_render_v003.mov", text)
            self.assertIn("Final lighting pass", text)
            self.assertIn("v003", text)
            self.assertNotIn("SNAP001", text)
            self.assertIn('href="activity"', text)
            self.assertIn('href="target"', text)
        finally:
            owner.close()
            owner.deleteLater()


if __name__ == "__main__":
    unittest.main()
