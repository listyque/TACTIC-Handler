from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
import json
import sys
import textwrap
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtCore import QObject, Signal

from thlib.ui.communication_feed import (
    MessagesController,
    _chat_data,
    _link_user_mentions,
    _message_identity,
    _message_skey,
)
from thlib.ui.communication_permissions import can_change_published_text
from thlib.environment import env_inst
from thlib.ui.workspace_models.records import RecordListModel
from tests.support.async_scenarios import DeferredPool


class CommunicationFeedTests(unittest.TestCase):
    @staticmethod
    def _application():
        class Repository(QObject):
            file_download_done = Signal(object)

        class Application(QObject):
            project_changed = Signal(str, str)

            def __init__(self):
                super().__init__()
                self.repository_sync = Repository(self)

        return Application()

    def test_published_text_permission_has_a_strict_one_hour_boundary(self):
        now = datetime(2026, 9, 22, 12, tzinfo=timezone.utc)
        fresh = now - timedelta(minutes=59, seconds=59)
        expired = now - timedelta(hours=1)
        self.assertTrue(can_change_published_text(
            "artist", fresh, "artist", False, now=now
        ))
        self.assertFalse(can_change_published_text(
            "artist", expired, "artist", True, now=now
        ))
        self.assertFalse(can_change_published_text(
            "artist", now + timedelta(seconds=1), "artist", False, now=now
        ))
        self.assertFalse(can_change_published_text(
            "artist", None, "artist", False, now=now
        ))
        self.assertFalse(can_change_published_text(
            "artist", fresh, "other", False, now=now
        ))
        self.assertTrue(can_change_published_text(
            "artist", expired, "other", True, now=now
        ))
        clock = Mock()
        clock.presentation_datetime.return_value = fresh
        self.assertTrue(can_change_published_text(
            "artist", "server timestamp", "artist", False,
            clock=clock, now=now,
        ))
        clock.presentation_datetime.assert_called_once_with("server timestamp")

    def test_message_actions_recheck_current_rights(self):
        from thlib.environment import env_server

        application = self._application()
        controller = MessagesController(application)
        controller.messages.replace([{
            "messageId": "MSG001", "sender": "artist", "body": "Original",
            "timestamp": datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "canEdit": True,
        }])
        controller._run_mutation = Mock()
        with patch.object(env_server, "get_user", return_value="artist"):
            self.assertTrue(controller.can_change_message("MSG001"))
            self.assertTrue(controller.delete_message("MSG001"))
            controller._run_mutation.assert_called_once()
            controller._run_mutation.reset_mock()
            controller.messages.set_value(
                0, "timestamp",
                (datetime.now(timezone.utc) - timedelta(hours=2)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            )
            self.assertFalse(controller.can_change_message("MSG001"))
            self.assertFalse(controller.edit_message("MSG001", "Changed"))
            self.assertFalse(controller.delete_message("MSG001"))
            controller._run_mutation.assert_not_called()

        with patch.object(env_server, "get_user", return_value="other"):
            self.assertFalse(controller.can_change_message("MSG001"))
            application.can_manage_tools = True
            self.assertTrue(controller.can_change_message("MSG001"))

    def test_chat_server_rechecks_author_role_and_age(self):
        from thlib import tactic_query as tq

        message = {
            "code": "MSG001", "message_code": "CHAT001",
            "login": "artist", "message": "Original",
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2))
                .strftime("%Y-%m-%d %H:%M:%S"),
        }
        identity = {"login": "artist", "admin": False}
        updates = Mock()

        class MessageLog:
            def get_code(self):
                return message["code"]

            def get_id(self):
                return 3

            def get_value(self, key):
                return message.get(key)

        class Search:
            def __init__(self, search_type):
                self.search_type = search_type

            def add_filter(self, *_args, **_kwargs):
                pass

            def get_sobject(self):
                if self.search_type == "sthpw/message_log":
                    return MessageLog()
                if self.search_type == "sthpw/subscription":
                    return object()
                return None

            def get_sobjects(self):
                if self.search_type == "sthpw/subscription":
                    return [SimpleNamespace(get_value=lambda _key: identity["login"])]
                return []

        search_module = ModuleType("pyasm.search")
        search_module.Search = Search
        search_module.SearchKey = SimpleNamespace(
            get_by_sobject=lambda *_args, **_kwargs: "sthpw/message_log?code=MSG001"
        )
        common_module = ModuleType("pyasm.common")
        common_module.Environment = SimpleNamespace(
            get_security=lambda: SimpleNamespace(is_admin=lambda: identity["admin"])
        )
        pyasm_module = ModuleType("pyasm")
        pyasm_module.search = search_module
        pyasm_module.common = common_module
        server = SimpleNamespace(
            get_login=lambda: identity["login"], update=updates,
        )
        with patch.dict(sys.modules, {
            "pyasm": pyasm_module, "pyasm.search": search_module,
            "pyasm.common": common_module,
        }), patch.object(tq, "server", server, create=True):
            for mutate in (
                lambda: tq.edit_chat_message("MSG001", "Changed"),
                lambda: tq.delete_chat_message("MSG001"),
            ):
                with self.assertRaisesRegex(RuntimeError, "within one hour"):
                    mutate()
            identity["admin"] = True
            with self.assertRaisesRegex(RuntimeError, "within one hour"):
                tq.delete_chat_message("MSG001")
            identity["admin"] = False
            updates.assert_not_called()

            identity["login"] = "other"
            for mutate in (
                lambda: tq.edit_chat_message("MSG001", "Changed"),
                lambda: tq.delete_chat_message("MSG001"),
            ):
                with self.assertRaisesRegex(RuntimeError, "administrators"):
                    mutate()
            updates.assert_not_called()

            identity["admin"] = True
            self.assertTrue(json.loads(tq.delete_chat_message("MSG001"))["deleted"])
            self.assertTrue(json.loads(tq.edit_chat_message("MSG001", "Changed"))["edited"])
            self.assertEqual(updates.call_count, 2)

            identity.update(login="artist", admin=False)
            message["timestamp"] = datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            updates.reset_mock()
            self.assertTrue(json.loads(tq.delete_chat_message("MSG001"))["deleted"])
            updates.assert_called_once()

    def test_note_server_rechecks_rights_and_preserves_edit_history(self):
        from thlib import tactic_query as tq

        note = {
            "login": "artist", "note": "Original", "metadata": {},
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2))
                .strftime("%Y-%m-%d %H:%M:%S"),
        }
        identity = {"login": "artist", "admin": False}
        delete = Mock()
        update = Mock()

        class Note:
            def get_base_search_type(self):
                return "sthpw/note"

            def get_value(self, key):
                return note.get(key)

            def delete(self):
                delete()

        class Search:
            @staticmethod
            def get_by_search_key(_key):
                return Note()

            def __init__(self, _search_type):
                pass

            def add_filter(self, *_args):
                pass

            def get_sobjects(self):
                return []

        search_module = ModuleType("pyasm.search")
        search_module.Search = Search
        search_module.SearchKey = SimpleNamespace(
            get_by_sobject=lambda *_args, **_kwargs: "sthpw/note?code=NOTE001"
        )
        common_module = ModuleType("pyasm.common")
        common_module.Environment = SimpleNamespace(
            get_security=lambda: SimpleNamespace(is_admin=lambda: identity["admin"])
        )
        pyasm_module = ModuleType("pyasm")
        pyasm_module.search = search_module
        pyasm_module.common = common_module
        server = SimpleNamespace(
            get_login=lambda: identity["login"], update=update,
        )
        with patch.dict(sys.modules, {
            "pyasm": pyasm_module, "pyasm.search": search_module,
            "pyasm.common": common_module,
        }), patch.object(tq, "server", server, create=True):
            with self.assertRaisesRegex(RuntimeError, "within one hour"):
                tq.change_note("sthpw/note?code=NOTE001", "delete")
            identity["admin"] = True
            with self.assertRaisesRegex(RuntimeError, "within one hour"):
                tq.change_note("sthpw/note?code=NOTE001", "edit", "Changed")
            identity["admin"] = False
            identity["login"] = "other"
            with self.assertRaisesRegex(RuntimeError, "administrators"):
                tq.change_note("sthpw/note?code=NOTE001", "edit", "Changed")
            delete.assert_not_called()
            update.assert_not_called()

            identity["admin"] = True
            self.assertTrue(json.loads(tq.change_note(
                "sthpw/note?code=NOTE001", "edit", "Changed"
            ))["edited"])
            changes = update.call_args.args[1]
            self.assertEqual(changes["note"], "Changed")
            self.assertEqual(changes["metadata"]["editHistory"][0]["body"], "Original")
            self.assertEqual(changes["metadata"]["editHistory"][0]["editedBy"], "other")

            identity.update(login="artist", admin=False)
            note["timestamp"] = datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            self.assertTrue(json.loads(tq.change_note(
                "sthpw/note?code=NOTE001", "delete"
            ))["deleted"])
            delete.assert_called_once()

    def test_changed_server_procedures_serialize_as_valid_python(self):
        from thlib import tactic_query as tq

        for procedure, arguments in (
            (tq.change_note, {
                "note_search_key": "sthpw/note?code=NOTE001",
                "action": "edit", "body": "Changed",
            }),
            (tq.edit_chat_message, {
                "message_log_code": "MSG001", "message": "Changed",
            }),
            (tq.delete_chat_message, {"message_log_code": "MSG001"}),
        ):
            with self.subTest(procedure=procedure.__name__):
                script = tq.prepare_serverside_script(
                    procedure, arguments, shrink=False, catch_traceback=False,
                )["code"]
                compile(
                    "def execute():\n" + textwrap.indent(script, "    "),
                    "<TACTIC server procedure>", "exec",
                )

    def test_message_timestamps_use_the_shared_server_clock(self):
        clock = Mock()
        controller = MessagesController(self._application(), clock=clock)

        with patch(
            "thlib.ui.communication_feed.activity_timestamp_labels",
            return_value=("local relative", "local exact"),
        ) as labels:
            result = controller._message_timestamp(
                "2026-08-30 15:00:00"
            )

        self.assertEqual(result, ("local relative", "local exact"))
        labels.assert_called_once_with(
            "2026-08-30 15:00:00", clock
        )

    def test_missing_message_columns_publish_first_run_state(self):
        from thlib.environment import env_server

        controller = MessagesController(self._application())
        controller._request_id = "first-run"
        controller._busy = True

        with (
            patch.object(env_server, "get_server", return_value="server"),
            patch.object(env_server, "get_user", return_value="artist"),
        ):
            controller._conversations_ready("first-run", {
                "initialized": False,
                "canInitialize": True,
                "missingColumns": [
                    {
                        "searchType": "sthpw/message",
                        "column": "metadata",
                    },
                ],
                "conversations": [],
            })

        self.assertFalse(controller.initialized)
        self.assertTrue(controller.canInitialize)
        self.assertFalse(controller.busy)
        self.assertEqual(controller.conversations.count(), 0)
        self.assertEqual(controller.error, "")

    def test_authentication_refreshes_hidden_conversation_summaries(self):
        from thlib.environment import env_server

        controller = MessagesController(self._application())
        controller.load = Mock()
        controller.refresh = Mock()

        with (
            patch.object(env_server, "get_ticket", return_value="ticket"),
            patch.object(env_inst, "logins", {"artist": object()}),
        ):
            controller.sync_authentication()

        controller.refresh.assert_called_once_with()
        controller.load.assert_not_called()

    def test_expired_ticket_does_not_requeue_hidden_chat_reads(self):
        from pathlib import Path
        from thlib.environment import env_mode, env_server
        from thlib.ui.debug_logging import DebugLogController

        application = self._application()
        application.authentication_required = False
        application.debug_log = DebugLogController(Path(env_mode.current_path))
        self.addCleanup(application.debug_log.shutdown)
        controller = MessagesController(application)
        pool = DeferredPool()

        def require_authentication():
            application.authentication_required = True
            controller.sync_authentication()

        application.debug_log.authentication_requested.connect(require_authentication)
        with (
            patch.object(env_inst, "server_pool", pool),
            patch.object(env_inst, "logins", {"artist": object()}),
            patch.object(env_server, "get_ticket", return_value="rejected-ticket"),
        ):
            controller.sync_authentication()
            controller._conversation_id = "CHAT001"
            controller._activate_draft_context()
            controller.set_draft_text("Unsent text")
            controller.load()  # An update arrives during the rejected request.
            self.assertTrue(controller._pending_refresh)
            pool.workers[0].reject({
                "message": "Invalid or expired ticket. Session may have expired.",
            })
            self.assertTrue(application.authentication_required)
            self.assertFalse(controller.busy)
            self.assertFalse(controller._pending_refresh)
            self.assertEqual(controller.draftText, "Unsent text")
            self.assertEqual(len(pool.workers), 1)
            controller.sync_authentication()
            controller.load()
            controller.refresh()
            controller._conversation_id = "CHAT001"
            controller._conversation_opened = controller._visible = True
            controller._sync_active_polling()
            controller._poll_active_conversation()
            self.assertFalse(controller._active_poll_timer.isActive())
            self.assertEqual(len(pool.workers), 1)
            application.authentication_required = False
            controller.sync_authentication()
            self.assertEqual(len(pool.workers), 2)
            controller._active_poll_timer.stop()

    def test_refresh_reads_server_even_with_stale_conversation_cache(self):
        from thlib import server_cache
        import thlib.tactic_classes as tc

        fresh = {"conversations": [
            {"conversationId": "CHAT001", "unread": 2},
            {"conversationId": "FAVORITES", "isPersonalNotes": True},
        ]}
        with (
            patch.object(env_inst, "get_current_login_object", return_value=object()),
            patch.object(server_cache, "invalidate_domains"),
            patch.object(server_cache, "token", return_value=None),
            patch.object(server_cache, "read_entry", return_value={
                "conversations": [{"conversationId": "CHAT001", "unread": 0}],
            }) as cached,
            patch.object(tc, "get_chat_conversations", return_value=fresh) as fetch,
        ):
            result = _chat_data(True)

        self.assertEqual(result, fresh)
        cached.assert_not_called()
        fetch.assert_called_once_with()

    def test_missing_favorites_is_created_for_regular_user_even_with_stale_cache(self):
        from thlib import server_cache
        import thlib.tactic_classes as tc

        missing = {"initialized": True, "conversations": [{
            "conversationId": "CHAT001", "isPersonalNotes": False,
        }]}
        with_favorites = {"initialized": True, "conversations": [
            missing["conversations"][0],
            {"conversationId": "FAVORITES", "isPersonalNotes": True,
             "messageCount": 0},
        ]}
        with (
            patch.object(env_inst, "get_current_login_object", return_value=object()),
            patch.object(server_cache, "token", return_value=None),
            patch.object(server_cache, "read_entry", return_value=missing),
            patch.object(tc, "get_chat_conversations", side_effect=[
                missing, with_favorites,
            ]) as fetch,
            patch.object(tc, "create_chat_conversation", return_value={
                "conversationId": "FAVORITES", "created": True,
            }) as create,
        ):
            result = _chat_data()

        self.assertEqual(result, with_favorites)
        create.assert_called_once_with([])
        self.assertEqual(fetch.call_count, 2)

    def test_existing_or_uninitialized_favorites_do_not_create_a_chat(self):
        from thlib import server_cache
        import thlib.tactic_classes as tc

        for cached in (
            {"initialized": True, "conversations": [{
                "conversationId": "FAVORITES", "isPersonalNotes": True,
                "messageCount": 0,
            }]},
            {"initialized": False, "conversations": []},
        ):
            with self.subTest(cached=cached):
                with (
                    patch.object(env_inst, "get_current_login_object", return_value=object()),
                    patch.object(server_cache, "token", return_value=None),
                    patch.object(server_cache, "read_entry", return_value=cached),
                    patch.object(tc, "get_chat_conversations") as fetch,
                    patch.object(tc, "create_chat_conversation") as create,
                ):
                    self.assertEqual(_chat_data(), cached)
                    fetch.assert_not_called()
                    create.assert_not_called()

    def test_logout_clears_messages_and_rejects_previous_session_response(self):
        from thlib.environment import env_server

        controller = MessagesController(self._application())
        controller._notification_session = ("server", "artist")
        controller._request_id = "old-request"
        controller._busy = True
        controller._conversation_id = "CHAT001"
        controller._conversation_opened = True
        controller.conversations.replace([{
            "conversationId": "CHAT001", "unread": 1,
        }])
        controller.messages.replace([{
            "messageId": "MSG001", "body": "Private message",
        }])

        with patch.object(env_server, "get_ticket", return_value=None):
            controller.sync_authentication()

        self.assertEqual(controller.conversations.count(), 0)
        self.assertEqual(controller.messages.count(), 0)
        self.assertEqual(controller._conversation_id, "")
        self.assertFalse(controller._busy)

        with (
            patch.object(env_server, "get_server", return_value="server"),
            patch.object(env_server, "get_user", return_value="another-user"),
        ):
            controller._conversations_ready("old-request", {
                "initialized": True,
                "conversations": [{
                    "conversationId": "CHAT001", "unread": 1,
                }],
            })

        self.assertEqual(controller.conversations.count(), 0)
        self.assertEqual(controller._notification_session, None)

    def test_initial_hidden_load_publishes_unread_badge_and_notification(self):
        from thlib.environment import env_server

        controller = MessagesController(self._application())
        controller._request_id = "login"
        controller._busy = True
        notifications = []
        controller.newMessageNotification.connect(
            lambda payload: notifications.append(dict(payload))
        )

        with (
            patch.object(env_server, "get_server", return_value="server"),
            patch.object(env_server, "get_user", return_value="artist"),
        ):
            controller._conversations_ready("login", {
                "initialized": True,
                "conversations": [{
                    "conversationId": "CHAT001",
                    "title": "Lighting",
                    "lastMessage": "Please review",
                    "lastTimestamp": "2026-09-21 13:40:00",
                    "lastSender": "supervisor",
                    "participantCount": 2,
                    "unread": 1,
                }],
            })

        self.assertEqual(controller.unreadCount, 1)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0]["conversationId"], "CHAT001")
        self.assertEqual(notifications[0]["excerpt"], "Please review")

    def test_quick_reply_uses_message_sender_without_switching_chat(self):
        from thlib.environment import env_server

        controller = MessagesController(self._application())
        controller._conversation_id = "CHAT_OPEN"
        controller._composer.set_text("Unsaved draft")
        sent = []
        controller.quickReplySent.connect(sent.append)
        controller.refresh = Mock()
        pool = DeferredPool()
        result = {"message": {"code": "MSG_SENT", "message_code": "CHAT_REPLY"}}

        with (
            patch.object(env_inst, "server_pool", pool),
            patch.object(env_server, "get_ticket", return_value="ticket"),
            patch.object(controller, "_cache_message_mutation", side_effect=lambda value: value),
            patch("thlib.tactic_classes.send_chat_message", return_value=result) as send,
        ):
            self.assertTrue(controller.send_quick_reply(
                "notice-1", "CHAT_REPLY", "  On it  "
            ))
            worker = pool.workers[0]
            self.assertTrue(worker.started)
            self.assertEqual(worker.operation(), result)
            worker.resolve(result)

        send.assert_called_once_with("CHAT_REPLY", "On it")
        self.assertEqual(sent, ["notice-1"])
        self.assertEqual(controller._conversation_id, "CHAT_OPEN")
        self.assertEqual(controller._composer.text, "Unsaved draft")
        controller.refresh.assert_called_once_with()

    def test_shared_initialization_defers_hidden_message_reload(self):
        controller = MessagesController(self._application())
        controller._initialized = False
        controller._can_initialize = True

        with patch.object(controller, "refresh") as refresh:
            controller.apply_schema_initialization()
            refresh.assert_not_called()
            controller.set_visible(True)

        self.assertTrue(controller.initialized)
        self.assertFalse(controller.canInitialize)
        refresh.assert_called_once_with()

    def test_consecutive_messages_form_timed_author_groups(self):
        records = [
            {
                "messageId": "1", "sender": "artist",
                "timestamp": "2026-08-25 10:00:00",
            },
            {
                "messageId": "2", "sender": "ARTIST",
                "timestamp": "2026-08-25 10:02:00",
            },
            {
                "messageId": "3", "sender": "admin",
                "timestamp": "2026-08-25 10:03:00",
            },
            {
                "messageId": "4", "sender": "artist",
                "timestamp": "2026-08-25 10:04:00",
            },
            {
                "messageId": "5", "sender": "artist",
                "timestamp": "2026-08-25 10:11:00",
            },
        ]

        grouped = MessagesController._group_message_records(records)

        self.assertEqual(
            [
                (record["groupFirst"], record["groupLast"])
                for record in grouped
            ],
            [
                (True, False),
                (False, True),
                (True, True),
                (True, True),
                (True, True),
            ],
        )
        self.assertNotIn("groupFirst", records[0])

    def test_message_text_drafts_are_isolated_and_restored_after_restart(self):
        stored = {}

        def read_config(**kwargs):
            if kwargs["filename"] == "drafts":
                return {
                    "contexts": dict(stored),
                }
            return {}

        def write_config(values, **kwargs):
            if kwargs["filename"] == "drafts":
                stored.clear()
                stored.update(values.get("contexts") or {})

        with patch(
            "thlib.ui.communication_feed.env_read_config",
            side_effect=read_config,
        ), patch(
            "thlib.ui.communication_feed.env_write_config",
            side_effect=write_config,
        ):
            controller = MessagesController(self._application())
            controller._current_session = lambda: ("server", "artist")
            controller._activate_draft_context("CHAT001")
            controller.set_draft_text("First chat")
            controller._activate_draft_context("CHAT002")
            self.assertEqual(controller.draftText, "")
            controller.set_draft_text("Second chat")
            controller._activate_draft_context("CHAT001")
            self.assertEqual(controller.draftText, "First chat")
            controller.shutdown()

            restored = MessagesController(self._application())
            restored._current_session = lambda: ("server", "artist")
            restored._activate_draft_context("CHAT002")
            self.assertEqual(restored.draftText, "Second chat")
            restored._activate_draft_context("CHAT001")
            self.assertEqual(restored.draftText, "First chat")

    def test_versioned_message_draft_document_is_not_read(self):
        with patch(
            "thlib.ui.communication_feed.env_read_config",
            return_value={
                "version": 1,
                "contexts": {"server-user/CHAT001": "obsolete"},
            },
        ):
            controller = MessagesController(self._application())

        self.assertEqual(controller._composer.contexts, {})

    def test_live_message_emits_append_signal_for_active_conversation(self):
        class Repository(QObject):
            file_download_done = Signal(object)

        class Application(QObject):
            project_changed = Signal(str, str)

            def __init__(self):
                super().__init__()
                self.repository_sync = Repository(self)

        controller = MessagesController(Application())
        controller._conversation_id = "CHAT001"
        appended = []
        controller.messageAppendedForConversation.connect(appended.append)

        with patch.object(
                controller, "_message_record",
                return_value={"messageId": "MESSAGE_LOG00001"}):
            self.assertTrue(controller._append_live_message({
                "code": "MESSAGE_LOG00001",
                "message_code": "CHAT001",
                "message": "Hello",
                "timestamp": "2026-08-19 10:00:00",
            }))

        self.assertEqual(appended, ["CHAT001"])
        self.assertEqual(controller.messages.count(), 1)

    def test_delivery_summary_tracks_per_recipient_state(self):
        self.assertEqual(
            MessagesController._delivery_record({
                "recipients": {
                    "artist": {"deliveredAt": "2026-08-12 10:00:00", "readAt": ""},
                    "supervisor": {"deliveredAt": "", "readAt": ""},
                },
            }),
            {
                "deliveryStatus": "sent",
                "deliveryRecipientCount": 2,
                "deliveryDeliveredCount": 1,
                "deliveryReadCount": 0,
            },
        )
        self.assertEqual(
            MessagesController._delivery_record({
                "status": "read",
                "recipientCount": 2,
                "deliveredCount": 2,
                "readCount": 2,
            })["deliveryStatus"],
            "read",
        )

    def test_server_receipt_update_changes_visible_message_to_read(self):
        controller = MessagesController(self._application())
        controller._conversation_id = "CHAT001"
        controller.messages.replace([{
            "messageId": "skey://sthpw/message_log?code=LOG001",
            "deliveryStatus": "sent",
            "deliveryRecipientCount": 1,
            "deliveryDeliveredCount": 0,
            "deliveryReadCount": 0,
        }])

        controller.apply_server_batch({
            "reactions": [{
                "messageId": "sthpw/message_log?code=LOG001",
                "messageCode": "CHAT001",
                "reactions": {},
                "delivery": {
                    "status": "read",
                    "recipientCount": 1,
                    "deliveredCount": 1,
                    "readCount": 1,
                },
            }],
        })

        record = controller.messages.get(0)
        self.assertEqual(record["deliveryStatus"], "read")
        self.assertEqual(record["deliveryReadCount"], 1)

    def test_known_user_mention_is_linked_without_touching_email_or_url(self):
        rendered = _link_user_mentions(
            "Hello @Artist, artist@example.test https://example.test/@Artist",
            ["artist"],
        )
        self.assertIn('href="user://artist"', rendered)
        self.assertIn("artist@example.test", rendered)
        self.assertIn("https://example.test/@Artist", rendered)
        self.assertEqual(rendered.count('href="user://artist"'), 1)

    def test_unknown_user_mention_remains_plain_text(self):
        self.assertEqual(
            _link_user_mentions("Hello @missing", ["artist"]),
            "Hello @missing",
        )

    def test_message_identity_ignores_skey_prefix_and_parameter_order(self):
        self.assertEqual(
            _message_identity(
                "skey://sthpw/message_log?project=sthpw&code=LOG001"
            ),
            _message_identity(
                "sthpw/message_log?code=LOG001&project=sthpw"
            ),
        )

    def test_message_identity_matches_code_and_full_skey(self):
        self.assertEqual(
            _message_identity("MESSAGE_LOG00001"),
            _message_identity(
                "skey://sthpw/message_log?project=sthpw"
                "&code=MESSAGE_LOG00001"
            ),
        )

    def test_message_skey_uses_code_for_bare_identity(self):
        self.assertEqual(
            _message_skey("MESSAGE_LOG00001"),
            "skey://sthpw/message_log?code=MESSAGE_LOG00001",
        )

    def test_copy_message_skey_uses_all_selected_messages(self):
        class Repository(QObject):
            file_download_done = Signal(object)

        class Application(QObject):
            project_changed = Signal(str, str)

            def __init__(self):
                super().__init__()
                self.repository_sync = Repository(self)

        controller = MessagesController(Application())
        controller.messages.replace([
            {"messageId": "sthpw/message_log?code=MESSAGE_LOG00001"},
            {"messageId": "sthpw/message_log?code=MESSAGE_LOG00002"},
        ])
        controller._forward_selection = {
            "MESSAGE_LOG00001", "MESSAGE_LOG00002",
        }

        with patch("PySide6.QtGui.QGuiApplication.clipboard") as clipboard:
            self.assertTrue(controller.copy_message_skey("MESSAGE_LOG00001"))

        clipboard.return_value.setText.assert_called_once_with(
            "skey://sthpw/message_log?code=MESSAGE_LOG00001\n"
            "skey://sthpw/message_log?code=MESSAGE_LOG00002"
        )

    def test_pin_preview_compacts_service_links(self):
        class Repository(QObject):
            file_download_done = Signal(object)

        class Application(QObject):
            project_changed = Signal(str, str)

            def __init__(self):
                super().__init__()
                self.repository_sync = Repository(self)

        controller = MessagesController(Application())
        preview = controller._pin_preview({
            "messageId": "sthpw/message_log?code=MESSAGE_LOG00003",
            "sender": "artist",
            "body": (
                "skey://sthpw/message_log?code=MESSAGE_LOG00001\n"
                "skey://sthpw/message_log?code=MESSAGE_LOG00002"
            ),
        })

        self.assertEqual(preview["summary"], "Linked messages")
        self.assertEqual(preview["linkedCount"], 2)
        self.assertEqual(preview["linkedMessageCount"], 2)
        self.assertNotIn("skey://", preview["summary"])

    def test_conversation_profile_compacts_last_message_links(self):
        class Repository(QObject):
            file_download_done = Signal(object)

        class Application(QObject):
            project_changed = Signal(str, str)

            def __init__(self):
                super().__init__()
                self.repository_sync = Repository(self)

        controller = MessagesController(Application())
        profile = controller._conversation_profile({
            "title": "Production",
            "recipients": ["artist"],
            "lastMessage": (
                "skey://sthpw/message_log?code=MESSAGE_LOG00001\n"
                "skey://sthpw/message_log?code=MESSAGE_LOG00002"
            ),
        })

        self.assertEqual(profile["lastMessageSummary"], "Linked messages")
        self.assertEqual(profile["lastMessageLinkedCount"], 2)
        self.assertNotIn("skey://", profile["lastMessageSummary"])

    def test_direct_conversation_inherits_live_user_presence(self):
        class Repository(QObject):
            file_download_done = Signal(object)

        class Users(QObject):
            contentReplaced = Signal()

            def __init__(self):
                super().__init__()
                self._records = [{
                    "login": "artist",
                    "displayName": "Alex Artist",
                    "presenceKnown": True,
                    "online": True,
                    "lastSeen": "2026-08-25T12:00:00Z",
                }]

        class Application(QObject):
            project_changed = Signal(str, str)

            def __init__(self):
                super().__init__()
                self.repository_sync = Repository(self)

        users = Users()
        controller = MessagesController(Application(), users=users)
        direct = controller._conversation_profile({
            "title": "Alex Artist",
            "recipients": ["artist"],
            "isPersonalNotes": False,
        })
        group = controller._conversation_profile({
            "title": "Artists",
            "recipients": ["artist", "lead"],
            "isPersonalNotes": False,
        })

        self.assertEqual(direct["peerLogin"], "artist")
        self.assertTrue(direct["presenceKnown"])
        self.assertTrue(direct["online"])
        self.assertTrue(direct["lastSeenPretty"])
        self.assertNotEqual(
            direct["lastSeenPretty"], "2026-08-25T12:00:00Z"
        )
        self.assertNotIn("T12:00:00", direct["lastSeenPretty"])
        self.assertEqual(group["peerLogin"], "")
        self.assertFalse(group["presenceKnown"])

        controller._conversation_id = "CHAT001"
        controller.conversations.replace([{
            "conversationId": "CHAT001",
            "title": "Alex Artist",
            "recipients": ["artist"],
            "isPersonalNotes": False,
            **direct,
        }])
        changed = Mock()
        controller.stateChanged.connect(changed)
        users._records[0]["online"] = False
        users.contentReplaced.emit()

        self.assertFalse(controller.selectedConversation["online"])
        changed.assert_called()

    def test_reaction_records_include_current_user_and_display_names(self):
        class Repository(QObject):
            file_download_done = Signal(object)

        class Users(QObject):
            contentReplaced = Signal()

            def __init__(self):
                super().__init__()
                self._records = [
                    {"login": "admin", "displayName": "Administrator"},
                    {"login": "artist", "displayName": "Alex Artist"},
                ]

        class Application(QObject):
            project_changed = Signal(str, str)

            def __init__(self):
                super().__init__()
                self.repository_sync = Repository(self)

        controller = MessagesController(Application(), users=Users())
        with patch("thlib.environment.env_server.get_user", return_value="admin"):
            records = controller._reaction_records({
                "👍": ["admin", "artist"],
            })

        self.assertEqual(records[0]["count"], 2)
        self.assertTrue(records[0]["reactedByMe"])
        self.assertEqual(
            records[0]["displayNames"], ["Administrator", "Alex Artist"]
        )

    def test_same_chat_message_link_focuses_without_reloading(self):
        class Repository(QObject):
            file_download_done = Signal(object)

        class Application(QObject):
            project_changed = Signal(str, str)

            def __init__(self):
                super().__init__()
                self.repository_sync = Repository(self)
                self.window_model = type(
                    "Windows", (), {"show_window": Mock()}
                )()

        application = Application()
        controller = MessagesController(application)
        controller._conversation_id = "CHAT001"
        controller.messages.replace([{
            "messageId": (
                "sthpw/message_log?project=sthpw"
                "&code=MESSAGE_LOG00001"
            ),
        }])
        controller.open_conversation = Mock()
        focused = []
        controller.messageFocusRequested.connect(focused.append)

        self.assertTrue(controller.open_forwarded_message(
            "CHAT001", "MESSAGE_LOG00001"
        ))
        controller.open_conversation.assert_not_called()
        self.assertEqual(focused, ["MESSAGE_LOG00001"])

    def test_open_direct_conversation_reuses_loaded_chat(self):
        class Repository(QObject):
            file_download_done = Signal(object)

        class Application(QObject):
            project_changed = Signal(str, str)

            def __init__(self):
                super().__init__()
                self.repository_sync = Repository(self)
                self.window_model = type(
                    "Windows", (), {"show_window": Mock()}
                )()

        application = Application()
        controller = MessagesController(application)
        controller.conversations.replace([{
            "conversationId": "CHAT001",
            "recipients": ["artist"],
            "isPersonalNotes": False,
        }])
        controller.open_conversation = Mock()
        controller.create_conversation = Mock(return_value=True)

        self.assertTrue(controller.open_direct_conversation("artist"))

        application.window_model.show_window.assert_called_once_with(
            "messages"
        )
        controller.open_conversation.assert_called_once_with("CHAT001")
        controller.create_conversation.assert_not_called()

    def test_open_direct_conversation_uses_native_deduplicating_create(self):
        class Repository(QObject):
            file_download_done = Signal(object)

        class Application(QObject):
            project_changed = Signal(str, str)

            def __init__(self):
                super().__init__()
                self.repository_sync = Repository(self)
                self.window_model = type(
                    "Windows", (), {"show_window": Mock()}
                )()

        application = Application()
        controller = MessagesController(application)
        controller.create_conversation = Mock(return_value=True)

        self.assertTrue(controller.open_direct_conversation("artist"))

        application.window_model.show_window.assert_called_once_with(
            "messages"
        )
        controller.create_conversation.assert_called_once_with(["artist"])

    def test_cached_conversation_is_presented_without_history_reload(self):
        class Repository(QObject):
            file_download_done = Signal(object)

        class Application(QObject):
            project_changed = Signal(str, str)

            def __init__(self):
                super().__init__()
                self.repository_sync = Repository(self)

        controller = MessagesController(Application())
        controller._remember_conversation = Mock()
        controller.conversations.replace([
            {
                "conversationId": "CHAT001",
                "title": "First",
                "lastTimestamp": "2026-08-04 10:00:00",
                "selected": True,
            },
            {
                "conversationId": "CHAT002",
                "title": "Second",
                "lastTimestamp": "2026-08-04 10:01:00",
                "selected": False,
            },
        ])
        controller._conversation_id = "CHAT001"
        controller._loaded_conversation_id = "CHAT001"
        controller._loaded_server_timestamp = "2026-08-04 10:00:00"
        controller.messages.replace([{
            "messageId": "MESSAGE_LOG00001",
            "body": "First chat",
        }])
        controller._cache_current_history()
        controller._conversation_cache["CHAT002"] = {
            "model": RecordListModel(controller.messages._roles, [{
                "messageId": "MESSAGE_LOG00002",
                "body": "Second chat",
            }], identity_role="messageId"),
            "pinnedMessage": {},
            "pinHistory": [],
            "hasMore": False,
            "offset": 1,
            "files": {},
            "previewFiles": {},
            "serverTimestamp": "2026-08-04 10:01:00",
        }
        controller._load_messages = Mock()
        events = []
        controller.conversationChanging.connect(
            lambda conversation_id: events.append(
                ("changing", conversation_id)
            )
        )
        controller.conversationLoaded.connect(
            lambda: events.append(("loaded", "CHAT002"))
        )
        controller.conversationRestored.connect(
            lambda conversation_id: events.append(
                ("restored", conversation_id)
            )
        )

        controller.select_conversation(1)

        controller._load_messages.assert_not_called()
        self.assertEqual(controller.messages.get(0)["body"], "Second chat")
        self.assertEqual(events, [
            ("restored", "CHAT002"),
            ("loaded", "CHAT002"),
        ])

    def test_remembering_conversation_does_not_sync_settings_inline(self):
        class Repository(QObject):
            file_download_done = Signal(object)

        class Application(QObject):
            project_changed = Signal(str, str)

            def __init__(self):
                super().__init__()
                self.repository_sync = Repository(self)

        controller = MessagesController(Application())
        controller._settings = {
            controller._conversation_settings_key(
                ("server", "artist")
            ): "CHAT001",
        }
        controller._settings_flush_timer = Mock()

        controller._remember_conversation("CHAT002", ("server", "artist"))

        self.assertEqual(
            controller._saved_conversation(("server", "artist")),
            "CHAT002",
        )
        controller._settings_flush_timer.start.assert_called_once_with()

    def test_read_receipt_is_not_sent_for_an_already_read_chat(self):
        class Repository(QObject):
            file_download_done = Signal(object)

        class Application(QObject):
            project_changed = Signal(str, str)

            def __init__(self):
                super().__init__()
                self.repository_sync = Repository(self)

        controller = MessagesController(Application())
        controller._visible = True
        controller._conversation_opened = True
        controller._conversation_id = "CHAT001"
        controller.conversations.replace([{
            "conversationId": "CHAT001",
            "selected": True,
            "unread": 0,
            "mentionCount": 0,
        }])
        controller.messages.replace([{
            "messageId": "MESSAGE_LOG00001",
            "timestamp": "2026-08-04 10:00:00",
            "unread": False,
        }])

        with patch.object(env_inst.server_pool, "add_task") as add_task:
            controller._mark_read()

        add_task.assert_not_called()

    def test_signed_out_chat_data_is_empty(self):
        previous = env_inst.logins
        try:
            env_inst.logins = None
            self.assertIsNone(env_inst.get_current_login_object())
            self.assertEqual(_chat_data(), ([], {}))
        finally:
            env_inst.logins = previous

    def test_cached_stale_conversation_refreshes_in_background(self):
        class Repository(QObject):
            file_download_done = Signal(object)

        class Application(QObject):
            project_changed = Signal(str, str)

            def __init__(self):
                super().__init__()
                self.repository_sync = Repository(self)

        controller = MessagesController(Application())
        controller._remember_conversation = Mock()
        controller.conversations.replace([{
            "conversationId": "CHAT002",
            "title": "Second",
            "lastTimestamp": "2026-08-04 10:02:00",
            "selected": False,
        }])
        controller._conversation_cache["CHAT002"] = {
            "model": RecordListModel(controller.messages._roles, [{
                "messageId": "MESSAGE_LOG00002",
                "body": "Cached message",
            }], identity_role="messageId"),
            "hasMore": False,
            "serverTimestamp": "2026-08-04 10:01:00",
        }
        controller._load_messages = Mock()
        changing = Mock()
        restored = Mock()
        controller.conversationChanging.connect(changing)
        controller.conversationRestored.connect(restored)

        controller.select_conversation(0)

        changing.assert_not_called()
        restored.assert_called_once_with("CHAT002")
        controller._load_messages.assert_called_once_with(
            reset=True, background=True, bypass_cache=False
        )
        self.assertEqual(
            controller.messages.get(0)["body"], "Cached message"
        )

    def test_sending_state_belongs_only_to_its_conversation(self):
        class Repository(QObject):
            file_download_done = Signal(object)

        class Application(QObject):
            project_changed = Signal(str, str)

            def __init__(self):
                super().__init__()
                self.repository_sync = Repository(self)

        controller = MessagesController(Application())
        controller._sending = True
        controller._sending_conversation_id = "CHAT001"
        controller._conversation_id = "CHAT001"
        self.assertTrue(controller.sending)

        controller._conversation_id = "CHAT002"
        self.assertFalse(controller.sending)

    def test_server_echo_of_locally_applied_message_does_not_dirty_chat(self):
        class Repository(QObject):
            file_download_done = Signal(object)

        class Application(QObject):
            project_changed = Signal(str, str)

            def __init__(self):
                super().__init__()
                self.repository_sync = Repository(self)

        controller = MessagesController(Application())
        controller._conversation_id = "CHAT001"
        controller.conversations.replace([{
            "conversationId": "CHAT001", "lastTimestamp": "",
            "participantCount": 2, "selected": True,
        }])
        controller._remember_server_message("MESSAGE_LOG00001")

        controller.apply_server_batch({
            "initialMessages": False,
            "messages": [{
                "code": "MESSAGE_LOG00001", "message_code": "CHAT001",
                "message": "Sent locally", "login": "artist",
                "timestamp": "2026-08-04 10:00:00",
            }],
        })

        self.assertNotIn("CHAT001", controller._dirty_conversations)

    def test_hidden_messages_controller_notifies_without_being_loaded(self):
        from thlib.environment import env_server

        controller = MessagesController(self._application())
        controller.refresh = Mock()
        notifications = []
        rich_notifications = []
        controller.newMessage.connect(
            lambda conversation_id, title, body: notifications.append(
                (conversation_id, title, body)
            )
        )
        controller.newMessageNotification.connect(
            lambda payload: rich_notifications.append(dict(payload))
        )

        with patch.object(env_server, "get_user", return_value="artist"):
            controller.apply_server_batch({
                "initialMessages": True,
                "messages": [{
                    "code": "MESSAGE_LOG00001",
                    "message_code": "CHAT001",
                    "message": "Existing message",
                    "login": "admin",
                    "timestamp": "2026-08-31 10:00:00",
                }],
            })
            controller.apply_server_batch({
                "initialMessages": False,
                "messages": [{
                    "code": "MESSAGE_LOG00002",
                    "message_code": "CHAT001",
                    "message": "New message",
                    "login": "admin",
                    "timestamp": "2026-08-31 10:01:00",
                }],
            })

        self.assertEqual(
            notifications,
            [("CHAT001", "admin", "New message")],
        )
        self.assertEqual(len(rich_notifications), 1)
        self.assertEqual(rich_notifications[0]["senderTitle"], "admin")
        self.assertEqual(rich_notifications[0]["excerpt"], "New message")
        controller.refresh.assert_called_once_with()

    def test_unseen_message_notifies_after_summary_timestamp_race(self):
        from thlib.environment import env_server

        controller = MessagesController(self._application())
        controller.conversations.replace([{
            "conversationId": "CHAT001",
            "title": "Production",
            "lastTimestamp": "2026-09-21 14:00:00",
            "participantCount": 2,
            "unread": 1,
        }])
        controller._notification_cursors["CHAT001"] = (
            "2026-09-21 14:00:00"
        )
        notifications = []
        controller.newMessageNotification.connect(
            lambda payload: notifications.append(dict(payload))
        )

        with patch.object(env_server, "get_user", return_value="artist"):
            controller.apply_server_batch({
                "initialMessages": False,
                "messages": [{
                    "code": "MESSAGE_LOG_RACE",
                    "message_code": "CHAT001",
                    "message": "Arrived before the delta poll",
                    "login": "admin",
                    "timestamp": "2026-09-21 14:00:00",
                }],
            })

        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            notifications[0]["excerpt"], "Arrived before the delta poll"
        )

    def test_only_visible_active_conversation_polls_every_five_seconds(self):
        controller = MessagesController(self._application())
        controller._conversation_id = "CHAT001"
        controller._loaded_conversation_id = "CHAT001"
        controller._conversation_opened = True
        controller._load_messages = Mock()
        self.assertEqual(controller._active_poll_timer.interval(), 5000)
        timer = Mock()
        timer.isActive.return_value = False
        controller._active_poll_timer = timer

        controller.set_visible(True)

        timer.start.assert_called_once_with()
        controller._poll_active_conversation()
        controller._load_messages.assert_called_once_with(
            reset=True,
            background=True,
            bypass_cache=True,
        )

        controller.set_visible(False)
        timer.stop.assert_called_once_with()

    def test_background_history_catches_up_without_losing_loaded_pages(self):
        controller = MessagesController(self._application())
        self.addCleanup(controller.shutdown)
        controller._conversation_id = "CHAT001"
        controller._loaded_conversation_id = "CHAT001"
        controller._offset = 60
        controller._has_more = True
        rows = [{
            "code": f"MSG{index:03}", "login": "artist",
            "message": str(index), "timestamp": "2026-09-21 10:00:00",
        } for index in range(100)]
        controller.messages.replace([
            controller._message_record(row, "", "artist") for row in rows[:60]
        ])
        pool = Mock(is_stopped=False)
        with (
            patch.object(env_inst, "server_pool", pool),
            patch("thlib.server_cache.token", return_value=None),
            patch("thlib.tactic_classes.get_chat_history") as history,
        ):
            history.side_effect = lambda _chat, limit, **_: {
                "messages": list(reversed(rows))[:limit],
            }
            controller._load_messages(reset=True, background=True, bypass_cache=True)
            result = pool.add_task.call_args.args[0]()
        self.assertEqual([call.kwargs["limit"] for call in history.call_args_list], [31, 61])
        controller._messages_ready(
            controller._history_request_id, result, True, 0, "CHAT001",
        )
        self.assertEqual(
            [record["messageId"] for record in controller.messages._records],
            [row["code"] for row in rows],
        )
        self.assertEqual(controller._offset, 100)
        self.assertTrue(controller._has_more)

        # A complete server response is authoritative, including deletions.
        controller._history_background = True
        controller._messages_ready(
            controller._history_request_id, {"messages": [rows[-1]]},
            True, 0, "CHAT001",
        )
        self.assertEqual(controller.messages.rowCount(), 1)
        self.assertEqual(controller._offset, 1)
        self.assertFalse(controller._has_more)

    def test_reopening_chat_loads_background_history_without_forcing_focus(self):
        controller = MessagesController(self._application())
        self.addCleanup(controller.shutdown)
        controller._conversation_id = "CHAT001"
        controller._conversation_opened = True
        controller._loaded_conversation_id = "CHAT001"
        controller._load_messages = Mock()
        controller._mark_read = Mock()
        controller._active_poll_timer = Mock()
        controller.conversations.replace([{
            "conversationId": "CHAT001", "selected": True, "unread": 2,
            "lastTimestamp": "2026-09-21 12:00:00",
        }])
        controller.messages.replace([
            controller._message_record({
                "code": "old", "login": "artist", "message": "Already read",
            }, "", "artist"),
        ])
        focused = []
        controller.messageFocusRequested.connect(focused.append)

        controller.set_visible(True)

        self.assertEqual(focused, [])
        controller._load_messages.assert_called_once_with(
            reset=True, background=True, bypass_cache=True,
        )
        controller._history_request_id = "refresh"
        controller._history_background = True
        controller._messages_ready("refresh", {"messages": [{
            "code": code, "login": "colleague", "message": code,
            "timestamp": "2026-09-21 12:00:00",
        } for code in ("newest", "new", "old")]}, True, 0, "CHAT001")
        self.assertEqual(focused, [])

    def test_message_notification_preference_persists_and_only_hides_popups(self):
        from thlib.environment import env_server

        stored = {}

        def read_config(**kwargs):
            if (
                kwargs.get("filename") == "ui_settings"
                and kwargs.get("unique_id") == "ui_messages"
            ):
                return dict(stored)
            return {}

        def write_config(values, **kwargs):
            if (
                kwargs.get("filename") == "ui_settings"
                and kwargs.get("unique_id") == "ui_messages"
            ):
                stored.clear()
                stored.update(values)

        with (
            patch(
                "thlib.ui.communication_feed.env_read_config",
                side_effect=read_config,
            ),
            patch(
                "thlib.ui.communication_feed.env_write_config",
                side_effect=write_config,
            ),
            patch.object(env_server, "get_user", return_value="artist"),
        ):
            controller = MessagesController(self._application())
            controller.conversations.replace([{
                "conversationId": "CHAT001",
                "title": "Production",
                "lastTimestamp": "2026-08-31 10:00:00",
                "participantCount": 2,
                "unread": 0,
            }])
            notifications = []
            controller.newMessageNotification.connect(
                lambda payload: notifications.append(dict(payload))
            )

            self.assertTrue(controller.notificationsEnabled)
            controller.set_notifications_enabled(False)
            controller.apply_server_batch({
                "initialMessages": False,
                "messages": [{
                    "code": "MESSAGE_LOG00004",
                    "message_code": "CHAT001",
                    "message": "Unread without popup",
                    "login": "admin",
                    "timestamp": "2026-08-31 10:01:00",
                }],
            })

            self.assertFalse(controller.notificationsEnabled)
            self.assertEqual(notifications, [])
            self.assertEqual(controller.unreadCount, 1)
            self.assertEqual(
                stored, {"notifications/enabled": False}
            )

            restored = MessagesController(self._application())
            self.assertFalse(restored.notificationsEnabled)

    def test_message_notification_uses_the_readable_content_preview(self):
        from thlib.environment import env_server

        controller = MessagesController(self._application())
        controller.refresh = Mock()
        notifications = []
        controller.newMessageNotification.connect(
            lambda payload: notifications.append(dict(payload))
        )

        with patch.object(env_server, "get_user", return_value="artist"):
            controller.apply_server_batch({
                "initialMessages": False,
                "messages": [{
                    "code": "MESSAGE_LOG00003",
                    "message_code": "CHAT001",
                    "message": "skey://demo/assets?code=ROBOT",
                    "login": "admin",
                    "timestamp": "2026-08-31 10:02:00",
                }],
            })

        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            notifications[0]["excerpt"], "Linked TACTIC items"
        )
        self.assertNotIn("skey://", notifications[0]["excerpt"])

    def test_complete_history_replaces_stale_attachment_summary(self):
        class Repository(QObject):
            file_download_done = Signal(object)

        class Application(QObject):
            project_changed = Signal(str, str)

            def __init__(self):
                super().__init__()
                self.repository_sync = Repository(self)

        controller = MessagesController(Application())
        controller.conversations.replace([{
            "conversationId": "CHAT001",
            "messageCount": 40,
            "attachmentCount": 1,
        }])
        history = [
            {"messageId": f"MESSAGE_LOG{index:05d}", "attachments": []}
            for index in range(6)
        ]

        controller._has_more = False
        controller._message_search = ""
        controller._reconcile_complete_history_counts("CHAT001", history)

        conversation = controller.conversations.get(0)
        self.assertEqual(conversation["messageCount"], 6)
        self.assertEqual(conversation["attachmentCount"], 0)

    def test_empty_history_clears_stale_personal_notes_preview(self):
        controller = MessagesController(self._application())
        controller.conversations.replace([{
            "conversationId": "CHAT001", "isPersonalNotes": True,
            "lastMessage": "stale note", "lastSender": "admin",
            "lastMessageSummary": "stale note", "lastMessageLinkedCount": 0,
            "lastTimestamp": "2026-09-22 12:00:00", "messageCount": 1,
            "attachmentCount": 0,
        }])
        controller._has_more = False
        controller._message_search = ""

        controller._reconcile_complete_history_counts("CHAT001", [])

        record = controller.conversations.get(0)
        self.assertEqual(record["messageCount"], 0)
        self.assertEqual(record["lastMessage"], "")
        self.assertEqual(record["lastSender"], "")
        self.assertEqual(record["lastMessageSummary"], "")

    def test_incomplete_attachment_upload_never_sends_text_only(self):
        controller = MessagesController(self._application())
        controller._sending = True
        controller._pending_send = {"attachmentCount": 2}
        controller._send_payload = Mock()

        controller._attachments_uploaded(["sthpw/snapshot?code=SNAP001"])

        controller._send_payload.assert_not_called()
        self.assertFalse(controller._sending)
        self.assertIn("Attachment", controller.error)

    def test_incomplete_history_keeps_server_attachment_summary(self):
        class Repository(QObject):
            file_download_done = Signal(object)

        class Application(QObject):
            project_changed = Signal(str, str)

            def __init__(self):
                super().__init__()
                self.repository_sync = Repository(self)

        controller = MessagesController(Application())
        controller.conversations.replace([{
            "conversationId": "CHAT001",
            "messageCount": 40,
            "attachmentCount": 1,
        }])
        controller._has_more = True

        controller._reconcile_complete_history_counts(
            "CHAT001", [{"attachments": []}]
        )

        conversation = controller.conversations.get(0)
        self.assertEqual(conversation["messageCount"], 40)
        self.assertEqual(conversation["attachmentCount"], 1)

    def test_complete_cached_history_overrides_same_server_summary(self):
        class Repository(QObject):
            file_download_done = Signal(object)

        class Application(QObject):
            project_changed = Signal(str, str)

            def __init__(self):
                super().__init__()
                self.repository_sync = Repository(self)

        controller = MessagesController(Application())
        controller._conversation_cache["CHAT001"] = {
            "model": RecordListModel(controller.messages._roles, [
                {"messageId": str(index), "attachments": []} for index in range(6)
            ], identity_role="messageId"),
            "hasMore": False,
            "serverTimestamp": "2026-08-23 10:00:00",
        }
        record = {
            "conversationId": "CHAT001",
            "lastTimestamp": "2026-08-23 10:00:00",
            "messageCount": 40,
            "attachmentCount": 1,
        }

        controller._apply_cached_history_counts(record)

        self.assertEqual(record["messageCount"], 6)
        self.assertEqual(record["attachmentCount"], 0)


if __name__ == "__main__":
    unittest.main()
