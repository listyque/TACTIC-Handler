from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QObject, Signal

from thlib.ui.communication_feed import (
    MessagesController,
    _chat_data,
    _link_user_mentions,
    _message_identity,
    _message_skey,
)
from thlib.environment import env_inst
from thlib.ui.workspace_models.records import RecordListModel


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
            reset=True, background=True
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
