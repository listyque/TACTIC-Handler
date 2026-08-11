from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QObject, Signal

from modern_ui.communication_feed import (
    MessagesController,
    _chat_data,
    _link_user_mentions,
    _message_identity,
    _message_skey,
)
from thlib.environment import env_inst


class CommunicationFeedTests(unittest.TestCase):
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
            "records": [{
                "messageId": "MESSAGE_LOG00002",
                "body": "Second chat",
            }],
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
        controller._settings = Mock()
        controller._settings_flush_timer = Mock()
        controller._settings.value.return_value = "CHAT001"

        controller._remember_conversation("CHAT002", ("server", "artist"))

        controller._settings.setValue.assert_called_once()
        controller._settings.sync.assert_not_called()
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
            "records": [{
                "messageId": "MESSAGE_LOG00002",
                "body": "Cached message",
            }],
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


if __name__ == "__main__":
    unittest.main()
