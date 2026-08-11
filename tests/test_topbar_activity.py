import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QObject, QSettings, Signal

from modern_ui.communication_feed import ActivityFeedController
from modern_ui.notifications import NotificationController
from modern_ui.workspace_models.records import RecordListModel


class _Repository(QObject):
    downloads_finished = Signal()
    task_failed = Signal(str)


class _Application(QObject):
    project_changed = Signal(str, str)
    notification_changed = Signal(str)
    loading_changed = Signal()
    activity_log_changed = Signal()

    def __init__(self):
        super().__init__()
        self.repository_sync = _Repository(self)
        self.current_project_code = "demo"
        self.loading = False
        self.loading_message = ""
        self.activity_log = []


class _Messages:
    def __init__(self):
        self.conversations = RecordListModel(("conversationId", "title"))


class TopBarActivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_notification_history_can_filter_operation_groups(self):
        application = _Application()
        controller = NotificationController(application)
        application.activity_log = [
            "12:00:00  START - Loading search results",
            "12:00:01  Repository download completed",
        ]
        application.activity_log_changed.emit()

        controller.set_history_group("repository")
        self.assertEqual(controller.filtered_history.count(), 1)
        self.assertEqual(
            controller.filtered_history.get(0)["group"], "repository"
        )
        controller.shutdown()

    def test_activity_badge_uses_persisted_read_cursor(self):
        application = _Application()
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("thlib.environment.env_server.get_server", return_value="server"),
            patch("thlib.environment.env_server.get_user", return_value="artist"),
        ):
            controller = ActivityFeedController(application, _Messages())
            controller._settings = QSettings(
                str(Path(directory) / "activity.ini"), QSettings.IniFormat
            )
            controller._load_read_cursor()
            controller.apply_server_batch({
                "initialActivity": True,
                "activity": [{
                    "code": "STATUS00001",
                    "__event_timestamp__": "2026-08-04 12:00:00",
                }],
            })
            self.assertEqual(controller.unreadCount, 0)

            controller.apply_server_batch({
                "initialActivity": False,
                "activity": [{
                    "code": "STATUS00002",
                    "__event_timestamp__": "2026-08-04 12:01:00",
                }],
            })
            self.assertEqual(controller.unreadCount, 1)
            controller.set_visible(True)
            self.assertEqual(controller.unreadCount, 0)
            self.assertEqual(
                controller._read_cursor, "2026-08-04 12:01:00"
            )

    def test_feed_uses_same_enriched_activity_api_as_user_profile(self):
        enriched = [{
            "eventId": "note:NOTE001",
            "kind": "note",
            "title": "Added note",
            "detail": "Review this",
            "actor": "artist",
            "timestamp": "2026-08-04 12:00:00",
            "searchKey": "skey://sthpw/note?code=NOTE001",
            "targetSearchKey": "skey://demo/asset?code=ASSET001",
            "targetTitle": "Robot",
            "targetType": "demo/asset",
            "process": "model",
        }]
        with (
            patch("thlib.environment.env_server.get_user", return_value="artist"),
            patch(
                "thlib.tactic_classes.get_user_recent_activity",
                return_value=enriched,
            ) as query,
        ):
            records = ActivityFeedController._query(
                "all", "demo", 0, 25
            )

        query.assert_called_once_with(
            "", project_code="demo", limit=26, offset=0,
            kinds=("status", "publication", "note", "task"),
            assigned_login="",
        )
        self.assertEqual(records[0]["targetTitle"], "Robot")
        self.assertEqual(records[0]["process"], "model")

    def test_feed_activity_navigation_reuses_context_resolver(self):
        class Resolver:
            def __init__(self):
                self.calls = []

            def open_in_context(self, *args):
                self.calls.append(args)

        resolver = Resolver()
        controller = ActivityFeedController(
            _Application(), _Messages(), resolver
        )
        controller.model.replace([controller._normalize_record({
            "kind": "note",
            "searchKey": "skey://sthpw/note?code=NOTE001",
            "targetSearchKey": "skey://demo/asset?code=ASSET001",
            "targetTitle": "Robot",
            "process": "model",
        })])

        controller.open_item(0)

        self.assertEqual(resolver.calls, [(
            "skey://sthpw/note?code=NOTE001",
            "skey://demo/asset?code=ASSET001",
            "model",
        )])


if __name__ == "__main__":
    unittest.main()
