from __future__ import annotations

import unittest
import sys
from types import ModuleType
from unittest.mock import patch
from urllib.error import HTTPError

from PySide6.QtCore import QObject, Signal

from modern_ui.server_updates import ServerUpdateService
from thlib import tactic_query


class _Application(QObject):
    project_changed = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.current_project_code = "demo"


class ServerUpdateServiceTests(unittest.TestCase):
    def test_new_install_defaults_to_30_second_updates_and_120_heartbeat(self):
        class EmptySettings:
            def __init__(self, *_args):
                pass

            @staticmethod
            def value(_key, default, **_kwargs):
                return default

            @staticmethod
            def setValue(*_args):
                pass

        with patch("modern_ui.server_updates.QSettings", EmptySettings):
            service = ServerUpdateService(_Application())

        self.assertEqual(service.poll_interval, 30)
        self.assertEqual(service.presence_interval, 120)

    def test_message_polling_does_not_depend_on_reaction_polling(self):
        class Record:
            def __init__(self, values):
                self.values = dict(values)

            def get_value(self, key, no_exception=False):
                return self.values.get(key)

            def get_code(self):
                return self.values.get("code")

            def get_id(self):
                return self.values.get("id")

            def get_data(self):
                return dict(self.values)

        subscription = Record({
            "message_code": "CHAT001",
        })
        message = Record({
            "code": "MESSAGE_LOG00001",
            "message_code": "CHAT001",
            "message": "Existing message",
            "timestamp": "2026-08-04 10:00:00",
        })
        searched_types = []

        class Search:
            def __init__(self, search_type):
                self.search_type = search_type
                searched_types.append(search_type)

            def add_filter(self, *_args, **_kwargs):
                pass

            def add_filters(self, *_args, **_kwargs):
                pass

            def add_order_by(self, *_args, **_kwargs):
                pass

            def set_limit(self, *_args, **_kwargs):
                pass

            def get_sobjects(self):
                if self.search_type == "sthpw/subscription":
                    return [subscription]
                if self.search_type == "sthpw/message_log":
                    return [message]
                return []

        class SearchKey:
            @staticmethod
            def get_by_sobject(record, use_id=False):
                return "sthpw/message_log?code={}".format(
                    record.get_code()
                )

        search_module = ModuleType("pyasm.search")
        search_module.Search = Search
        search_module.SearchKey = SearchKey
        pyasm_module = ModuleType("pyasm")
        pyasm_module.search = search_module
        fake_server = type("Server", (), {
            "get_login": staticmethod(lambda: "artist"),
        })()

        with patch.dict(sys.modules, {
            "pyasm": pyasm_module,
            "pyasm.search": search_module,
        }), patch.object(tactic_query, "server", fake_server, create=True):
            result = tactic_query.query_server_updates(
                include_activity=False,
                include_reactions=False,
            )

        self.assertEqual(len(result["messages"]), 1)
        self.assertEqual(result["reactions"], [])
        self.assertNotIn("sthpw/change_timestamp", searched_types)

    def test_ready_advances_reaction_cursor_and_emits_batch(self):
        service = ServerUpdateService(_Application())
        service._running = True
        batches = []
        service.batchReady.connect(batches.append)
        with patch.object(service, "_schedule"):
            service._ready({
                "messages": [],
                "activity": [],
                "reactions": [{"messageId": "MESSAGE_LOG00001"}],
                "reactionCursor": "2026-08-03 12:00:00",
            })

        self.assertEqual(service._reaction_cursor, "2026-08-03 12:00:00")
        self.assertEqual(len(batches), 1)
        self.assertEqual(batches[0]["reactions"][0]["messageId"],
                         "MESSAGE_LOG00001")

    def test_502_is_a_transient_error(self):
        error = HTTPError(
            "http://server/tactic/default/Api/", 502,
            "Proxy Error", {}, None,
        )
        try:
            self.assertTrue(ServerUpdateService._is_transient_error(error))
        finally:
            error.close()

    def test_transient_errors_are_silent_until_fifth_attempt(self):
        service = ServerUpdateService(_Application())
        service._running = True
        warnings = []
        service.warningRaised.connect(
            lambda message, stacktrace: warnings.append((message, stacktrace))
        )

        with patch.object(service, "_schedule") as schedule:
            for attempt in range(4):
                service._transient_failed({
                    "message": "HTTP Error 502: Proxy Error",
                    "stacktrace": f"trace {attempt}",
                })
            self.assertEqual(warnings, [])
            service._transient_failed({
                "message": "HTTP Error 502: Proxy Error",
                "stacktrace": "final trace",
            })

        self.assertEqual(len(warnings), 1)
        self.assertIn("5 attempts", warnings[0][0])
        self.assertEqual(warnings[0][1], "final trace")
        schedule.assert_called_with(30000)

    def test_success_resets_transient_failure_state(self):
        service = ServerUpdateService(_Application())
        service._running = True
        service._failure_count = 5
        service._failure_reported = True
        with patch.object(service, "_schedule"):
            service._ready({"messages": [], "activity": [], "reactions": []})
        self.assertEqual(service._failure_count, 0)
        self.assertFalse(service._failure_reported)

    def test_poll_interval_restarts_normal_schedule(self):
        service = ServerUpdateService(_Application())
        service._settings = type("Settings", (), {
            "setValue": staticmethod(lambda *_args: None),
        })()
        service._running = True
        service._busy = False
        target = 60 if service.poll_interval != 60 else 30
        with patch.object(service, "_schedule") as schedule:
            service.set_poll_interval(target)
        self.assertEqual(service.poll_interval, target)
        schedule.assert_called_once_with(target * 1000)

    def test_invalid_poll_interval_is_ignored(self):
        service = ServerUpdateService(_Application())
        before = service.poll_interval
        service.set_poll_interval(0)
        self.assertEqual(service.poll_interval, before)

    def test_visibility_changes_do_not_start_duplicate_poll(self):
        service = ServerUpdateService(_Application())
        service._running = True
        with patch.object(service, "_schedule") as schedule:
            service.set_activity_enabled(True)
            service.set_tasks_visible(True)
        schedule.assert_not_called()


if __name__ == "__main__":
    unittest.main()
