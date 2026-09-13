import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QLocale, QObject, Signal

from tests.qt_application import gui_test_application
from thlib.ui.communication_feed import ActivityFeedController
from thlib.ui.activity import (
    JOURNAL_ACTIVITY_KINDS,
    activity_record,
    present_activity_records,
)
from thlib.ui.user_identity import user_avatar_color
from thlib.ui.notifications import NotificationController
from thlib.ui.server_clock import ServerClock
from thlib.ui.workspace_models.records import RecordListModel
from tests.support.async_scenarios import DeferredWorker


class _Repository(QObject):
    downloads_finished = Signal()
    task_failed = Signal(str)


class _WindowModel:
    def __init__(self):
        self.opened = []

    def show_window(self, window_id):
        self.opened.append(str(window_id))


class _Application(QObject):
    project_changed = Signal(str, str)
    notification_changed = Signal(str)
    loading_changed = Signal()
    activity_log_changed = Signal()

    def __init__(self):
        super().__init__()
        self.repository_sync = _Repository(self)
        self.window_model = _WindowModel()
        self.current_project_code = "demo"
        self.loading = False
        self.loading_message = ""
        self.activity_log = []


class _Messages(QObject):
    newMessageNotification = Signal("QVariantMap")

    def __init__(self):
        super().__init__()
        self.opened = []

    def open_conversation(self, conversation_id):
        self.opened.append(str(conversation_id))


def _users(records=()):
    return RecordListModel(
        ("login", "displayName", "initials", "avatarUrl", "avatarColor"),
        list(records),
    )


class TopBarActivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        from thlib.environment import env_mode

        self._original_config_root = env_mode.get_current_path()
        self._config_root = tempfile.TemporaryDirectory()
        env_mode.set_current_path(self._config_root.name)

    def tearDown(self):
        from thlib.environment import env_mode

        env_mode.set_current_path(self._original_config_root)
        self._config_root.cleanup()

    def test_notification_history_can_filter_operation_groups(self):
        application = _Application()
        controller = NotificationController(application)
        controller.set_visible(True)
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

    def test_notification_history_uses_pretty_and_exact_timestamp_labels(self):
        application = _Application()
        controller = NotificationController(application)
        controller.set_visible(True)

        controller.push("info", "Cache refreshed")

        record = controller.history.get(0)
        self.assertTrue(record["timestampPretty"])
        self.assertTrue(record["timestampFull"])
        self.assertNotIn("T", record["timestampPretty"])
        self.assertNotEqual(record["timestampPretty"], record["timestamp"])
        controller.shutdown()

    def test_hidden_notification_history_defers_model_publication(self):
        application = _Application()
        controller = NotificationController(application)

        controller.push("info", "Cache refreshed")

        self.assertEqual(controller.history.count(), 0)
        self.assertEqual(len(controller._history_records), 1)

        controller.set_visible(True)

        self.assertEqual(controller.history.count(), 1)
        self.assertEqual(
            controller.history.get(0)["message"], "Cache refreshed"
        )
        controller.shutdown()

    def test_activity_badge_uses_persisted_read_cursor(self):
        application = _Application()
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("thlib.environment.env_server.get_server", return_value="server"),
            patch("thlib.environment.env_server.get_user", return_value="artist"),
        ):
            controller = ActivityFeedController(application)
            controller._settings = {}
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
            with patch.object(controller, "_load") as load:
                controller.set_visible(True)
            load.assert_called_once_with(
                reset=True, bypass_cache=True,
            )
            self.assertEqual(controller.unreadCount, 0)
            self.assertEqual(
                controller._read_cursor, "2026-08-04 12:01:00"
            )

    def test_activity_notification_preference_is_persisted_by_feed_owner(self):
        application = _Application()
        controller = ActivityFeedController(application)

        self.assertTrue(controller.notificationsEnabled)
        controller.set_notifications_enabled(False)
        self.assertFalse(controller.notificationsEnabled)

        restored = ActivityFeedController(application)
        self.assertFalse(restored.notificationsEnabled)

    def test_remote_activity_uses_notification_stack_without_replaying(self):
        application = _Application()
        users = _users([{
            "login": "supervisor",
            "displayName": "Sam Supervisor",
            "initials": "SS",
            "avatarUrl": "",
            "avatarColor": "#78909c",
        }])
        activity = ActivityFeedController(application, users=users)
        activity._read_cursor_exists = True
        activity._read_cursor = "2026-08-04 12:00:00"
        notifications = NotificationController(
            application, activity=activity
        )
        remote_event = {
            "code": "SNAPSHOT00001",
            "__kind__": "publication",
            "login": "supervisor",
            "search_code": "Robot",
            "process": "publish",
            "__event_timestamp__": "2026-08-04 12:01:00",
        }

        with patch(
            "thlib.environment.env_server.get_user",
            return_value="artist",
        ), patch.object(activity, "_request_notification_enrichment"):
            activity.apply_server_batch({
                "initialActivity": True,
                "activity": [{
                    **remote_event,
                    "code": "SNAPSHOT_INITIAL",
                    "__event_timestamp__": "2026-08-04 12:00:30",
                }],
            })
            self.assertEqual(notifications.model.count(), 0)
            activity.apply_server_batch({
                "initialActivity": False,
                "activity": [remote_event],
            })
            activity.apply_server_batch({
                "initialActivity": False,
                "activity": [remote_event],
            })
            activity.apply_server_batch({
                "initialActivity": False,
                "activity": [{
                    **remote_event,
                    "code": "SNAPSHOT00002",
                    "login": "artist",
                    "__event_timestamp__": "2026-08-04 12:02:00",
                }],
            })
            self.assertEqual(notifications.model.count(), 0)
            activity._publish_pending_notifications([{
                "eventId": "publication:SNAPSHOT00001",
                "kind": "publication",
                "actor": "supervisor",
                "timestamp": "2026-08-04 12:01:00",
                "targetSearchKey": "skey://demo/asset?code=ROBOT",
                "targetTitle": "Robot",
                "targetType": "demo/asset",
                "process": "publish",
            }], tuple(activity._pending_notification_events))

        self.assertEqual(notifications.model.count(), 1)
        notice = notifications.model.get(0)
        self.assertEqual(notice["message"], "Sam Supervisor")
        self.assertEqual(notice["action"], "activity")
        self.assertEqual(notice["sourceType"], "activity")
        self.assertEqual(notice["sourceTitle"], "New publication")
        self.assertEqual(notice["avatarText"], "SS")
        self.assertEqual(notice["avatarColor"], "#78909c")
        self.assertEqual(notice["sourceIcon"], "snapshot")
        self.assertIn("Robot", notice["detail"])
        self.assertIn("publish", notice["detail"])
        self.assertNotIn("__kind__", notice["detail"])

        with patch(
            "thlib.environment.env_server.get_user", return_value="artist",
        ), patch.object(activity, "_request_notification_enrichment"):
            activity.apply_server_batch({
                "initialActivity": False,
                "activity": [{
                    **remote_event,
                    "code": "SNAPSHOT00002",
                    "__event_timestamp__": "2026-08-04 12:01:30",
                }],
            })
            activity._publish_pending_notifications([{
                "eventId": "publication:SNAPSHOT00002",
                "kind": "publication",
                "actor": "supervisor",
                "timestamp": "2026-08-04 12:01:30",
                "targetTitle": "Robot",
                "targetType": "demo/asset",
                "process": "publish",
            }], tuple(activity._pending_notification_events))
        self.assertEqual(notifications.model.count(), 2)

        activity.set_notifications_enabled(False)
        with patch(
            "thlib.environment.env_server.get_user", return_value="artist",
        ), patch.object(activity, "_request_notification_enrichment"):
            activity.apply_server_batch({
                "initialActivity": False,
                "activity": [{
                    **remote_event,
                    "code": "SNAPSHOT00003",
                    "__event_timestamp__": "2026-08-04 12:03:00",
                }],
            })
        self.assertEqual(notifications.model.count(), 2)

        notifications.activate(1)
        self.assertEqual(application.window_model.opened, ["activity_feed"])
        self.assertEqual(notifications.model.count(), 1)
        notifications.shutdown()

    def test_activity_toast_waits_for_enriched_feed_author_and_action(self):
        application = _Application()
        users = _users([{
            "login": "admin",
            "displayName": "Admin User",
            "initials": "AU",
            "avatarUrl": "file:///avatars/admin.png",
            "avatarColor": "#78909c",
        }])
        activity = ActivityFeedController(application, users=users)
        activity._read_cursor_exists = True
        activity._read_cursor = "2026-08-30 23:00:00"
        notifications = NotificationController(
            application, activity=activity,
        )
        raw = {
            "code": "CHANGE0001",
            "__kind__": "change",
            "search_type": "demo/th_knowledge_article",
            "search_code": "ARTICLE0001",
            "__event_timestamp__": "2026-08-30 23:08:42",
        }

        with patch(
            "thlib.environment.env_server.get_user", return_value="artist",
        ), patch.object(activity, "_request_notification_enrichment"):
            activity.apply_server_batch({"activity": [raw]})
            self.assertEqual(notifications.model.count(), 0)
            activity._publish_pending_notifications([{
                "eventId": "audit:TRANSACTION0001:0",
                "kind": "change",
                "actor": "admin",
                "timestamp": "2026-08-30 23:08:42",
                "targetSearchKey": (
                    "skey://demo/th_knowledge_article?code=ARTICLE0001"
                ),
                "targetTitle": "Article for several objects",
                "targetType": "demo/th_knowledge_article",
                "changes": [{
                    "field": "s_status",
                    "before": "draft",
                    "after": "",
                }],
            }], tuple(activity._pending_notification_events))

        self.assertEqual(notifications.model.count(), 1)
        notice = notifications.model.get(0)
        self.assertEqual(notice["sourceType"], "activity")
        self.assertEqual(notice["sourceTitle"], "Object updated")
        self.assertEqual(notice["message"], "Admin User")
        self.assertEqual(notice["previewUrl"], "file:///avatars/admin.png")
        self.assertIn("th knowledge article", notice["detail"])
        self.assertIn("Article for several objects", notice["detail"])
        self.assertIn("s status: draft", notice["detail"])
        self.assertNotIn("__kind__", notice["detail"])
        notifications.shutdown()

    def test_enriched_author_removes_own_raw_event_before_notification(self):
        application = _Application()
        activity = ActivityFeedController(application)
        activity._read_cursor_exists = True
        activity._read_cursor = "2026-08-30 23:00:00"
        notifications = NotificationController(
            application, activity=activity,
        )
        raw = {
            "code": "CHANGE0002",
            "__kind__": "change",
            "search_code": "ARTICLE0002",
            "__event_timestamp__": "2026-08-30 23:09:00",
        }

        with patch(
            "thlib.environment.env_server.get_user", return_value="artist",
        ), patch.object(activity, "_request_notification_enrichment"):
            activity.apply_server_batch({"activity": [raw]})
            self.assertEqual(activity.unreadCount, 1)
            activity._publish_pending_notifications([{
                "eventId": "change:CHANGE0002",
                "kind": "change",
                "actor": "artist",
                "timestamp": "2026-08-30 23:09:00",
                "itemCode": "ARTICLE0002",
                "targetTitle": "My draft",
            }], tuple(activity._pending_notification_events))

        self.assertEqual(activity.unreadCount, 0)
        self.assertEqual(notifications.model.count(), 0)
        notifications.shutdown()

    def test_hidden_feed_coalesces_notification_into_bounded_journal_query(self):
        from thlib.environment import env_inst

        class Pool:
            is_stopped = False

            def __init__(self):
                self.calls = []
                self.workers = []

            def add_task(self, operation, *args):
                self.calls.append((operation, args))
                worker = DeferredWorker(operation)
                self.workers.append(worker)
                return worker

        pool = Pool()
        application = _Application()
        activity = ActivityFeedController(application)
        activity._read_cursor_exists = True
        activity._read_cursor = "2026-08-30 23:00:00"

        with patch.object(env_inst, "server_pool", pool):
            notifications = NotificationController(
                application, activity=activity,
            )
            with patch(
                "thlib.environment.env_server.get_user",
                return_value="artist",
            ):
                activity.apply_server_batch({"activity": [{
                    "code": "NOTE0001",
                    "__kind__": "note",
                    "login": "admin",
                    "__event_timestamp__": "2026-08-30 23:10:00",
                }]})
                activity.apply_server_batch({"activity": [{
                    "code": "NOTE0001",
                    "__kind__": "note",
                    "login": "admin",
                    "__event_timestamp__": "2026-08-30 23:10:00",
                }]})

                self.assertEqual(len(pool.workers), 1)
                operation, args = pool.calls[0]
                self.assertIs(
                    operation.__func__, ActivityFeedController._query.__func__,
                )
                self.assertEqual(args[0], "all")
                self.assertEqual(args[2], 0)
                self.assertLessEqual(args[3], 100)
                self.assertTrue(args[9])
                self.assertFalse(args[11])
                self.assertEqual(notifications.model.count(), 0)

                pool.workers[0].resolve({"records": [{
                    "eventId": "note:NOTE0001",
                    "kind": "note",
                    "actor": "admin",
                    "timestamp": "2026-08-30 23:10:00",
                    "targetTitle": "Episode 1",
                    "detail": "Please review the render",
                }]})

            self.assertEqual(notifications.model.count(), 1)
            self.assertEqual(
                notifications.model.get(0)["message"], "admin",
            )
            notifications.shutdown()

    def test_message_notification_keeps_sender_preview_and_opens_chat(self):
        application = _Application()
        messages = _Messages()
        notifications = NotificationController(
            application, messages=messages
        )

        messages.newMessageNotification.emit({
            "conversationId": "conversation-7",
            "conversationTitle": "Lighting",
            "senderLogin": "supervisor",
            "senderTitle": "Sam Supervisor",
            "excerpt": "The render is ready for review.",
            "avatarUrl": "file:///avatars/sam.png",
            "initials": "SS",
            "avatarColor": "#78909c",
        })

        self.assertEqual(notifications.model.count(), 1)
        notice = notifications.model.get(0)
        self.assertEqual(notice["message"], "Sam Supervisor")
        self.assertEqual(notice["detail"], "The render is ready for review.")
        self.assertEqual(notice["sourceType"], "message")
        self.assertEqual(notice["sourceTitle"], "Lighting")
        self.assertEqual(notice["previewUrl"], "file:///avatars/sam.png")
        self.assertEqual(notice["avatarText"], "SS")
        self.assertEqual(notice["avatarColor"], "#78909c")

        notifications.activate(0)

        self.assertEqual(messages.opened, ["conversation-7"])
        self.assertEqual(notifications.model.count(), 0)
        notifications.shutdown()

    def test_own_live_activity_refreshes_history_but_not_badge(self):
        controller = ActivityFeedController(_Application())
        controller._read_cursor_exists = True
        controller._read_cursor = "2026-08-04 12:00:00"
        own_event = {
            "code": "SNAPSHOT00001",
            "__kind__": "publication",
            "login": "Artist",
            "__event_timestamp__": "2026-08-04 12:01:00",
        }

        with (
            patch(
                "thlib.environment.env_server.get_user",
                return_value="artist",
            ),
            patch.object(controller, "_load") as load,
        ):
            controller.apply_server_batch({
                "initialActivity": False,
                "activity": [own_event],
            })

        self.assertEqual(controller.unreadCount, 0)
        self.assertEqual(
            controller._latest_activity_timestamp,
            "2026-08-04 12:01:00",
        )
        self.assertTrue(controller._live_refresh_pending)
        load.assert_not_called()

        controller._live_refresh_pending = False
        controller._exclude_own_activity = True
        with patch(
            "thlib.environment.env_server.get_user", return_value="artist"
        ):
            controller.apply_server_batch({
                "initialActivity": False,
                "activity": [own_event],
            })
        self.assertFalse(controller._live_refresh_pending)
        self.assertEqual(controller.unreadCount, 0)

        with patch(
            "thlib.environment.env_server.get_user", return_value="artist"
        ):
            controller._track_activity([{
                "code": "NOTE00001",
                "__kind__": "note",
                "login": "supervisor",
                "__event_timestamp__": "2026-08-04 12:02:00",
            }])
        self.assertEqual(controller.unreadCount, 1)

    def test_own_activity_is_only_removed_when_feed_switch_is_enabled(self):
        controller = ActivityFeedController(_Application())
        controller._request_id = "request"
        records = [{
            "eventId": "publication:mine",
            "kind": "publication",
            "actor": "Artist",
            "timestamp": "2026-08-04 12:00:00",
        }, {
            "eventId": "publication:theirs",
            "kind": "publication",
            "actor": "supervisor",
            "timestamp": "2026-08-04 12:01:00",
        }]

        with patch(
            "thlib.environment.env_server.get_user", return_value="artist"
        ):
            controller._ready("request", {"records": records}, True, 0)

        self.assertEqual(controller.model.count(), 2)

        with (
            patch(
                "thlib.environment.env_server.get_user",
                return_value="artist",
            ),
            patch.object(controller, "_load") as load,
        ):
            controller.set_exclude_own_activity(True)
        self.assertTrue(controller.excludeOwnActivity)
        load.assert_called_once_with(reset=True)

        self.assertEqual(controller.model.count(), 1)
        self.assertEqual(
            controller.model.get(0)["eventId"], "publication:theirs"
        )

    def test_task_login_is_used_as_the_stable_activity_actor(self):
        controller = ActivityFeedController(_Application())
        controller._read_cursor_exists = True
        controller._read_cursor = "2026-08-04 12:00:00"

        with patch(
            "thlib.environment.env_server.get_user", return_value="artist"
        ):
            controller._track_activity([{
                "code": "TASK00001",
                "__kind__": "task",
                "login": "artist",
                "__event_timestamp__": "2026-08-04 12:01:00",
            }])

        self.assertEqual(controller.unreadCount, 0)

    def test_feed_uses_same_enriched_activity_api_as_user_profile(self):
        enriched = [{
            "eventId": "note:NOTE001",
            "kind": "note",
            "title": "Added note",
            "detail": "Review this",
            "actor": "supervisor",
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
            payload = ActivityFeedController._query(
                "all", "demo", 0, 25
            )
            records = payload["records"]

        query.assert_called_once_with(
            "", project_code="demo", limit=26, offset=0,
            kinds=JOURNAL_ACTIVITY_KINDS,
            assigned_login="", include_day_counts=False,
            counts_only=False, counts_from_day="", day="",
            logins=[], instance_relations={}, exclude_login="",
        )
        self.assertEqual(records[0]["targetTitle"], "Robot")
        self.assertEqual(records[0]["process"], "model")

    def test_all_feed_does_not_reuse_a_pre_complete_journal_cache_page(self):
        stale_page = {
            "records": [{
                "eventId": "publication:old",
                "kind": "publication",
            }],
        }

        def read_entry(_domain, cache_key, _project_code):
            contract = json.loads(cache_key).get("contract")
            if contract == ActivityFeedController.CACHE_CONTRACT:
                return None
            return stale_page

        with (
            patch("thlib.environment.env_server.get_user", return_value="artist"),
            patch("thlib.server_cache.read_entry", side_effect=read_entry),
            patch("thlib.server_cache.write_entry"),
            patch("thlib.server_cache.token", return_value=0),
            patch(
                "thlib.tactic_classes.get_user_recent_activity",
                return_value={
                    "records": [{
                        "eventId": "note:NOTE001",
                        "kind": "note",
                        "detail": "Visible in All",
                    }],
                },
            ) as query,
        ):
            payload = ActivityFeedController._query("all", "demo", 0, 25)

        query.assert_called_once()
        self.assertEqual(payload["records"][0]["kind"], "note")

    def test_instance_relation_catalog_uses_every_project_schema_relation(self):
        class Schema:
            def __init__(self, children=(), parents=()):
                self.children = list(children)
                self.parents = list(parents)

        class SearchType:
            def __init__(self, code, schema):
                self.code = code
                self.schema = schema

            def get_code(self):
                return self.code

            def get_schema(self):
                return self.schema

        class Project:
            def get_stypes(self):
                return {
                    "demo/scene": SearchType("demo/scene", Schema(children=[{
                        "from": "demo/asset",
                        "relationship": "instance",
                        "instance_type": "demo/assets_in_scenes",
                    }])),
                    "demo/asset": SearchType("demo/asset", Schema(children=[{
                        "from": "demo/texture",
                        "relationship": "instance",
                        "instance_type": "demo/texture_in_assets",
                    }])),
                    "demo/texture": SearchType("demo/texture", Schema()),
                }

        with patch(
            "thlib.environment.env_inst.projects", {"demo": Project()}
        ):
            catalog = ActivityFeedController._instance_relation_catalog(
                "demo"
            )

        self.assertEqual(catalog, {
            "demo/assets_in_scenes": ["demo/asset", "demo/scene"],
            "demo/texture_in_assets": ["demo/texture", "demo/asset"],
        })

    def test_activity_uses_pretty_and_exact_timestamp_labels(self):
        previous_locale = QLocale()
        try:
            QLocale.setDefault(QLocale("en_US"))
            record = activity_record({
                "timestamp": "2026-08-04 12:00:00",
            })
        finally:
            QLocale.setDefault(previous_locale)

        self.assertTrue(record["timestampPretty"])
        self.assertEqual(
            record["timestampFull"], "4 August 2026, 12:00:00"
        )

    def test_loaded_activity_is_reprojected_after_clock_synchronizes(self):
        clock = ServerClock()
        controller = ActivityFeedController(_Application(), clock=clock)
        controller._replace_records([activity_record({
            "eventId": "snapshot:SNAPSHOT00001",
            "timestamp": "2026-08-30 15:10:00",
        }, clock=clock)])
        before = controller.model.get(0)["timestampFull"]
        client_started = datetime(
            2026, 8, 30, 10, 0, tzinfo=timezone.utc
        ).timestamp()

        clock.observe(
            {
                "utcStarted": "2026-08-30T12:00:00.050000Z",
                "utcEnded": "2026-08-30T12:00:00.150000Z",
                "localEnded": "2026-08-30T15:00:00.150000",
            },
            client_started,
            client_started + 0.2,
            session=("server", "artist"),
        )

        record = controller.model.get(0)
        self.assertEqual(record["timestamp"], "2026-08-30 15:10:00")
        self.assertNotEqual(record["timestampFull"], before)

    def test_activity_never_falls_back_to_a_raw_transport_timestamp(self):
        record = activity_record({
            "timestamp": "invalid-server-timestamp",
            "timestampPretty": "invalid-server-timestamp",
            "timestampFull": "invalid-server-timestamp",
        })

        self.assertEqual(record["timestampPretty"], "")
        self.assertEqual(record["timestampFull"], "")

    def test_activity_preserves_structured_audit_changes(self):
        record = activity_record({
            "kind": "change",
            "changes": [{
                "field": "assigned",
                "before": "admin",
                "after": "artist",
            }],
        })

        self.assertEqual(record["changes"], [{
            "field": "assigned",
            "before": "admin",
            "after": "artist",
        }])

    def test_enriched_work_hour_keeps_task_navigation_and_time_details(self):
        record = activity_record({
            "eventId": "work_hour:WORK0001:2026-08-25 14:30:00",
            "kind": "work_hour",
            "actor": "listy",
            "timestamp": "2026-08-25 14:30:00",
            "searchKey": "skey://sthpw/work_hour?code=WORK0001",
            "taskCode": "TASK0001",
            "targetSearchKey": "skey://demo/asset?code=ASSET001",
            "targetTitle": "Bathroom",
            "targetType": "demo/asset",
            "process": "model",
            "context": "model/retopo",
            "hours": 4.0,
            "workDay": "2026-08-25 00:00:00",
            "workHourAction": "change",
            "workHourCategory": "regular",
            "workHourStatus": "approved",
            "workHourOwner": "artist",
        })

        self.assertEqual(record["kind"], "work_hour")
        self.assertEqual(record["actor"], "listy")
        self.assertEqual(record["workHourOwner"], "artist")
        self.assertEqual(record["hours"], 4.0)
        self.assertEqual(record["taskCode"], "TASK0001")
        self.assertEqual(
            record["targetSearchKey"],
            "skey://demo/asset?code=ASSET001",
        )

    def test_day_navigation_counts_and_filters_loaded_activity(self):
        controller = ActivityFeedController(_Application())
        controller._request_id = "request"
        controller._ready("request", [
            {"eventId": "one", "timestamp": "2026-08-04 12:00:00"},
            {"eventId": "two", "timestamp": "2026-08-04 11:00:00"},
            {"eventId": "three", "timestamp": "2026-08-03 10:00:00"},
        ], True, 0)

        self.assertEqual(controller.calendarCounts["2026-08-04"], 2)
        self.assertEqual(controller.calendarCounts["2026-08-03"], 1)

        with patch.object(controller, "_load") as load:
            controller.select_day("2026-08-04")
            load.assert_called_once_with(reset=True)
        self.assertEqual(controller.selectedDay, "2026-08-04")
        self.assertEqual(controller.model.count(), 2)

        with patch.object(controller, "_load"):
            controller.select_day("")
        self.assertEqual(controller.model.count(), 3)

    def test_activity_search_filters_loaded_journal_and_keeps_day_roles(self):
        controller = ActivityFeedController(_Application())
        controller._request_id = "request"
        with patch(
            "thlib.environment.env_server.get_user", return_value="current"
        ):
            controller._ready("request", [
                {
                    "eventId": "publication:one",
                    "kind": "publication",
                    "actor": "supervisor",
                    "targetTitle": "Bathroom",
                    "process": "publish",
                    "timestamp": "2026-08-04 12:00:00",
                },
                {
                    "eventId": "task:two",
                    "kind": "task",
                    "actor": "admin",
                    "targetTitle": "Kitchen",
                    "process": "model",
                    "timestamp": "2026-08-03 10:00:00",
                },
            ], True, 0)

        controller.set_search_text("bath publish")

        self.assertEqual(controller.searchText, "bath publish")
        self.assertEqual(controller.model.count(), 1)
        self.assertEqual(
            controller.model.get(0)["eventId"], "publication:one"
        )
        self.assertEqual(controller.model.get(0)["dayKey"], "2026-08-04")

        controller.set_search_text("")
        self.assertEqual(controller.model.count(), 2)

    def test_hidden_activity_feed_defers_live_model_publication(self):
        controller = ActivityFeedController(_Application())
        controller.set_visible(False)

        with patch.object(controller, "_track_activity"):
            controller.apply_server_batch({
                "activity": [{
                    "__kind__": "note",
                    "code": "NOTE001",
                    "note": "Review the render",
                    "login": "artist",
                    "timestamp": "2026-08-04 12:00:00",
                }],
            })

        self.assertEqual(controller.model.count(), 0)
        self.assertEqual(controller._all_records, [])
        self.assertTrue(controller._live_refresh_pending)

        with patch.object(controller, "_load") as load:
            controller.set_visible(True)

        load.assert_called_once_with(reset=True, bypass_cache=True)
        self.assertEqual(controller.model.count(), 0)

    def test_calendar_counts_cover_server_history_not_only_loaded_page(self):
        controller = ActivityFeedController(_Application())
        controller._request_id = "request"
        controller._ready("request", {
            "records": [{
                "eventId": "publication:one",
                "timestamp": "2026-08-04 12:00:00",
            }],
            "dayCounts": [
                {"dateKey": "2026-08-04", "count": 21},
                {"dateKey": "2026-07-18", "count": 7},
            ],
        }, True, 0)

        self.assertEqual(controller.calendarCounts["2026-08-04"], 21)
        self.assertEqual(controller.calendarCounts["2026-07-18"], 7)
        self.assertEqual(len(controller.calendarCounts), 2)

    def test_notes_filter_queries_latest_project_notes(self):
        with (
            patch("thlib.environment.env_server.get_user", return_value="artist"),
            patch(
                "thlib.tactic_classes.get_user_recent_activity",
                return_value={
                    "records": [{
                        "eventId": "note:NOTE001",
                        "kind": "note",
                        "detail": "Please check the render",
                        "timestamp": "2026-08-04 12:00:00",
                    }],
                    "dayCounts": [{"dateKey": "2026-08-04", "count": 8}],
                },
            ) as query,
        ):
            payload = ActivityFeedController._query(
                "notes", "demo", 0, 25,
                include_day_counts=True,
            )

        self.assertEqual(payload["records"][0]["kind"], "note")
        self.assertEqual(payload["dayCounts"][0]["count"], 8)
        query.assert_called_once_with(
            "", project_code="demo", limit=26, offset=0,
            kinds=("note",), assigned_login="",
            include_day_counts=True, counts_only=False,
            counts_from_day="", day="",
            logins=[], instance_relations={}, exclude_login="",
        )

    def test_initial_feed_query_does_not_scan_calendar_history(self):
        with (
            patch("thlib.environment.env_server.get_user", return_value="artist"),
            patch(
                "thlib.tactic_classes.get_user_recent_activity",
                return_value=[],
            ) as query,
        ):
            payload = ActivityFeedController._query(
                "all", "demo", 0, 25
            )

        self.assertNotIn("dayCounts", payload)
        self.assertFalse(query.call_args.kwargs["include_day_counts"])
        self.assertFalse(query.call_args.kwargs["counts_only"])

    def test_calendar_query_requests_counts_without_activity_page(self):
        with (
            patch("thlib.environment.env_server.get_user", return_value="artist"),
            patch(
                "thlib.tactic_classes.get_user_recent_activity",
                return_value={
                    "records": [],
                    "dayCounts": [{"dateKey": "2026-08-04", "count": 8}],
                },
            ) as query,
        ):
            payload = ActivityFeedController._query(
                "all", "demo", 0, 1, include_day_counts=True,
                counts_only=True,
            )

        self.assertEqual(payload["records"], [])
        self.assertEqual(payload["dayCounts"][0]["count"], 8)
        self.assertTrue(query.call_args.kwargs["include_day_counts"])
        self.assertTrue(query.call_args.kwargs["counts_only"])

    def test_cached_calendar_replaces_only_the_delta_window(self):
        controller = ActivityFeedController(_Application())
        controller._calendar_counts = {
            "2026-08-20": 4,
            "2026-08-24": 7,
        }
        controller._calendar_request_id = "calendar-request"

        with patch.object(controller, "_save_calendar_counts") as save:
            controller._calendar_ready("calendar-request", {
                "records": [],
                "countsFromDay": "2026-08-24",
                "dayCounts": [
                    {"dateKey": "2026-08-24", "count": 9},
                    {"dateKey": "2026-08-25", "count": 2},
                ],
            })

        self.assertEqual(controller.calendarCounts, {
            "2026-08-20": 4,
            "2026-08-24": 9,
            "2026-08-25": 2,
        })
        save.assert_called_once_with()

    def test_all_calendar_is_seeded_from_complete_category_caches(self):
        controller = ActivityFeedController(_Application())
        controller._filter = "all"
        controller._selected_users = []

        caches = {
            "all": {},
            "notes": {
                "completeHistory": True,
                "dayCounts": {
                    "2026-08-20": 2,
                    "2026-08-21": 1,
                },
            },
            "publications": {
                "completeHistory": True,
                "dayCounts": {
                    "2026-08-20": 5,
                    "2026-08-22": 3,
                },
            },
        }

        with (
            patch.object(
                controller, "_calendar_cache_unique_id",
                side_effect=lambda feed_filter=None, selected_users=None:
                    str(feed_filter or controller._filter),
            ),
            patch(
                "thlib.server_cache.read_entry",
                side_effect=lambda _domain, key, _project: caches.get(
                    str(key).removeprefix("calendar:"), {}
                ),
            ),
        ):
            controller._restore_calendar_counts()

        self.assertEqual(controller.calendarCounts, {
            "2026-08-20": 7,
            "2026-08-21": 1,
            "2026-08-22": 3,
        })
        self.assertFalse(controller._calendar_cache_complete)

    def test_seeded_calendar_requires_full_history_before_using_delta(self):
        controller = ActivityFeedController(_Application())
        controller._calendar_counts = {"2026-08-24": 7}
        controller._calendar_cache_complete = False

        self.assertEqual(controller._calendar_delta_start(), "")

        controller._calendar_cache_complete = True
        self.assertEqual(
            controller._calendar_delta_start(), "2026-08-24"
        )

    def test_stale_complete_calendar_is_visible_while_full_recount_is_due(self):
        controller = ActivityFeedController(_Application())
        stale = {
            "all": {
                "completeHistory": True,
                "dayCounts": {
                    "2026-08-24": 7,
                    "2025-03-12": 42,
                },
            },
        }

        with (
            patch.object(
                controller, "_calendar_cache_unique_id",
                side_effect=lambda feed_filter=None, selected_users=None:
                    str(feed_filter or controller._filter),
            ),
            patch("thlib.server_cache.read_entry", return_value=None),
            patch(
                "thlib.server_cache.read_stale_entry",
                side_effect=lambda _domain, key, _project: stale.get(
                    str(key).removeprefix("calendar:"), {}
                ),
            ),
        ):
            controller._restore_calendar_counts()

        self.assertEqual(controller.calendarCounts, stale["all"]["dayCounts"])
        self.assertFalse(controller._calendar_cache_complete)
        self.assertEqual(controller._calendar_delta_start(), "")

    def test_live_activity_uses_the_current_filter_authoritative_query(self):
        controller = ActivityFeedController(_Application())
        controller._filter = "notes"
        controller._visible = True
        with (
            patch.object(controller, "_track_activity"),
            patch.object(controller, "_load") as load,
        ):
            controller.apply_server_batch({
                "activity": [
                    {
                        "__kind__": "publication",
                        "code": "SNAPSHOT001",
                        "timestamp": "2026-08-04 12:01:00",
                    },
                    {
                        "__kind__": "note",
                        "code": "NOTE001",
                        "note": "Please check the render",
                        "login": "artist",
                        "timestamp": "2026-08-04 12:00:00",
                    },
                ],
            })

        load.assert_called_once_with(reset=True, bypass_cache=True)
        self.assertEqual(controller.model.count(), 0)

    def test_activity_feed_does_not_accept_chat_messages(self):
        controller = ActivityFeedController(_Application())
        with patch.object(controller, "_track_activity"):
            controller.apply_server_batch({
                "messages": [{
                    "code": "MESSAGE001",
                    "message_code": "CHAT001",
                    "message": "Chat belongs in Messages",
                    "login": "artist",
                    "timestamp": "2026-08-04 12:00:00",
                }],
            })

        self.assertNotIn("messages", controller.FILTERS)
        self.assertEqual(controller.model.count(), 0)

    def test_user_filter_is_deduplicated_and_sent_to_server(self):
        controller = ActivityFeedController(_Application())
        controller._filter = "my_tasks"
        controller._selected_day = "2026-08-04"
        with patch.object(controller, "_load") as load:
            controller.set_users(["artist", "artist", "admin", ""])

        self.assertEqual(controller.selectedUsers, ["artist", "admin"])
        self.assertEqual(controller.currentFilter, "all")
        self.assertEqual(controller.selectedDay, "")
        load.assert_called_once_with(reset=True)

        with (
            patch("thlib.environment.env_server.get_user", return_value="listy"),
            patch(
                "thlib.tactic_classes.get_user_recent_activity",
                return_value=[],
            ) as query,
        ):
            ActivityFeedController._query(
                "all", "demo", 0, 25,
                selected_users=controller.selectedUsers,
            )
        query.assert_called_once_with(
            "", project_code="demo", limit=26, offset=0,
            kinds=JOURNAL_ACTIVITY_KINDS,
            assigned_login="", include_day_counts=False,
            counts_only=False, counts_from_day="", day="",
            logins=["artist", "admin"], instance_relations={},
            exclude_login="",
        )

    def test_profile_user_scope_forces_full_feed_with_one_refresh(self):
        controller = ActivityFeedController(_Application())
        controller._filter = "publications"
        with patch.object(controller, "_load") as load:
            controller.select_user_feed("artist")

        self.assertEqual(controller.currentFilter, "all")
        self.assertEqual(controller.selectedUsers, ["artist"])
        load.assert_called_once_with(reset=True)

    def test_activity_status_colors_follow_project_workflow(self):
        class TaskPipeline:
            pipeline = {
                "In Progress": {"color": "#f9a825"},
                "Done": {"color": "#43a047"},
            }

        class Workflow:
            def get_by_pipeline_code(self, _stype, code):
                return TaskPipeline() if code == "asset_tasks" else None

            def get_by_process_node_type(self, _stype, _node_type):
                return TaskPipeline()

        class Pipeline:
            def get_process_info(self, process):
                return {
                    "color": "#42a5f5",
                    "task_pipeline": "asset_tasks",
                } if process == "model" else {}

            def get_pipeline_process(self, _process):
                return {}

        class SearchType:
            def get_stype_color(self, fmt="hex"):
                return "#7e57c2"

            def get_pipeline(self):
                return {"asset": Pipeline()}

            def get_workflow(self):
                return Workflow()

        class Project:
            def get_stypes(self):
                return {"demo/asset": SearchType()}

        from thlib.environment import env_inst
        with patch.object(env_inst, "projects", {"demo": Project()}):
            record = present_activity_records([{
                "kind": "status",
                "project": "demo",
                "targetType": "demo/asset",
                "process": "model",
                "statusBefore": "In Progress",
                "statusAfter": "Done",
            }], [])[0]

        self.assertEqual(record["typeColor"], "#7e57c2")
        self.assertEqual(record["processColor"], "#42a5f5")
        self.assertEqual(record["statusBeforeColor"], "#f9a825")
        self.assertEqual(record["statusAfterColor"], "#43a047")

    def test_instance_relation_keeps_endpoint_identity_and_schema_style(self):
        class SearchType:
            def __init__(self, title, color):
                self.title = title
                self.color = color

            def get_pretty_name(self):
                return self.title

            def get_stype_color(self, fmt="hex"):
                return self.color

            def get_pipeline(self):
                return {}

        class Project:
            def get_stypes(self):
                return {
                    "demo/asset": SearchType("Assets", "#ef5350"),
                    "demo/scene": SearchType("Scenes", "#5c6bc0"),
                }

        from thlib.environment import env_inst
        with patch.object(env_inst, "projects", {"demo": Project()}):
            record = present_activity_records([activity_record({
                "kind": "create",
                "project": "demo",
                "relationAction": "link",
                "searchKey": "skey://demo/asset?code=ASSET001",
                "itemTitle": "Baby Shark",
                "itemType": "demo/asset",
                "targetSearchKey": "skey://demo/scene?code=SCENE001",
                "targetTitle": "Episode 79",
                "targetType": "demo/scene",
            })], [])[0]

        self.assertEqual(record["relationAction"], "link")
        self.assertEqual(record["itemTypeTitle"], "Assets")
        self.assertEqual(record["itemTypeColor"], "#ef5350")
        self.assertEqual(record["targetTypeTitle"], "Scenes")
        self.assertEqual(record["typeColor"], "#5c6bc0")
        self.assertTrue(record["canOpen"])

    def test_task_activity_opens_parent_scope_and_selects_exact_task(self):
        class Tasks:
            def __init__(self):
                self.calls = []

            def open_object_context(self, *args):
                self.calls.append(args)

        tasks = Tasks()
        application = _Application()
        controller = ActivityFeedController(
            application, tasks=tasks
        )
        controller.model.replace([controller._normalize_record({
            "eventId": "task:TASK001",
            "kind": "task",
            "searchKey": "skey://sthpw/task?code=TASK001",
            "targetSearchKey": "skey://demo/asset?code=ASSET001",
            "targetTitle": "Bathroom",
            "taskCode": "TASK001",
            "process": "model",
        })])

        with patch.object(
                application, "open_search_key", create=True
        ) as open_search_key:
            controller.open_item(0)

        self.assertEqual(tasks.calls, [(
            "skey://demo/asset?code=ASSET001", "TASK001", "model",
        )])
        open_search_key.assert_not_called()

    def test_task_without_resolved_actor_is_not_assumed_server_generated(self):
        record = activity_record({
            "kind": "task",
            "taskCode": "TASK001",
            "actor": "",
        })

        self.assertFalse(record["serverGenerated"])

    def test_explicit_server_task_is_presented_as_server_generated(self):
        record = activity_record({
            "kind": "task",
            "taskCode": "TASK001",
            "actor": "",
            "serverGenerated": True,
        })

        self.assertTrue(record["serverGenerated"])
        self.assertEqual(record["actorInitials"], "")

    def test_feed_projects_actor_avatar_name_and_initials(self):
        users = _users([{
            "login": "artist",
            "displayName": "Ada Artist",
            "initials": "AA",
            "avatarUrl": "file:///avatars/artist.png",
        }])
        controller = ActivityFeedController(
            _Application(), users=users
        )
        controller._request_id = "request"

        controller._ready("request", [{
            "eventId": "note:NOTE001",
            "kind": "note",
            "actor": "artist",
        }], True, 0)

        record = controller.model.get(0)
        self.assertEqual(record["actorLabel"], "Ada Artist")
        self.assertEqual(record["actorInitials"], "AA")
        self.assertEqual(
            record["actorAvatar"], "file:///avatars/artist.png"
        )

    def test_same_actor_keeps_legacy_login_color_across_event_types(self):
        records = present_activity_records([
            {
                "actor": "artist",
                "kind": "publication",
                "processColor": "#ff0000",
            },
            {
                "actor": "artist",
                "kind": "task",
                "processColor": "#00ff00",
            },
        ], [])

        expected = user_avatar_color("artist")
        self.assertEqual(records[0]["actorColor"], expected)
        self.assertEqual(records[1]["actorColor"], expected)
        self.assertNotIn(expected, {"#ff0000", "#00ff00"})

    def test_feed_refreshes_identity_when_user_directory_changes(self):
        users = _users()
        controller = ActivityFeedController(
            _Application(), users=users
        )
        controller.model.replace([controller._normalize_record({
            "eventId": "task:TASK001",
            "kind": "task",
            "actor": "listy",
        })])
        self.assertEqual(controller.model.get(0)["actorInitials"], "L")

        users.replace([{
            "login": "listy",
            "displayName": "Listy User",
            "initials": "LU",
            "avatarUrl": "file:///avatars/listy.png",
        }])

        record = controller.model.get(0)
        self.assertEqual(record["actorLabel"], "Listy User")
        self.assertEqual(record["actorInitials"], "LU")
        self.assertEqual(record["actorAvatar"], "file:///avatars/listy.png")

    def test_feed_activity_navigation_reuses_context_resolver(self):
        class Resolver:
            def __init__(self):
                self.calls = []

            def open_in_context(self, *args):
                self.calls.append(args)

        resolver = Resolver()
        controller = ActivityFeedController(
            _Application(), resolver
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
