from __future__ import annotations

import json
import unittest
import sys
from types import ModuleType
from unittest.mock import Mock, patch
from urllib.error import HTTPError
from xmlrpc.client import Fault

from PySide6.QtCore import QObject, Signal

from thlib.ui.server_updates import ServerUpdateService
from thlib import tactic_query
from thlib.request_retry import transient_error_reporting_deferred


class _Application(QObject):
    project_changed = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.current_project_code = "demo"
        self._settings = {}

    def _write_settings(self):
        pass


class _SignalStub:
    def connect(self, callback, *_args):
        self.callback = callback


class _WorkerStub:
    def __init__(self):
        self.result = _SignalStub()
        self.error = _SignalStub()
        self.started = False

    def start(self):
        self.started = True


class _PoolStub:
    is_stopped = False

    def __init__(self):
        self.operation = None
        self.worker = _WorkerStub()

    def add_task(self, operation):
        self.operation = operation
        return self.worker


class _InitializedSearchType:
    @staticmethod
    def get_columns(_search_type):
        return ["metadata"]


class ServerUpdateServiceTests(unittest.TestCase):
    def test_new_install_defaults_to_30_second_updates(self):
        service = ServerUpdateService(_Application())

        self.assertEqual(service.poll_interval, 30)

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
        search_module.SearchType = _InitializedSearchType
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

    def test_shared_poll_includes_receipts_and_presence_heartbeat(self):
        from thlib import server_cache
        import thlib.tactic_classes as tc
        from thlib.environment import env_inst, env_server

        pool = _PoolStub()
        service = ServerUpdateService(_Application())
        service._running = True
        service._messages_visible = False
        service._session = ("server", "artist", "ticket")

        with (
            patch.object(env_inst, "server_pool", pool),
            patch.object(env_inst, "logins", {"artist": object()}),
            patch.object(env_server, "get_ticket", return_value="ticket"),
            patch.object(env_server, "get_server", return_value="server"),
            patch.object(env_server, "get_user", return_value="artist"),
        ):
            service.poll()

        self.assertTrue(pool.worker.started)
        self.assertIsNotNone(pool.operation)
        with (
            patch.object(tc, "get_server_updates", return_value={}) as query,
            patch.object(server_cache, "read_cursor", return_value=""),
        ):
            pool.operation()

        options = query.call_args.kwargs
        self.assertTrue(options["include_messages"])
        self.assertTrue(options["include_reactions"])
        self.assertTrue(options["include_presence"])
        self.assertTrue(options["heartbeat_presence"])
        self.assertEqual(options["presence_ttl"], 90)

    def test_cancelled_poll_stops_before_server_request(self):
        from thlib import server_cache
        import thlib.tactic_classes as tc
        from thlib.environment import env_inst, env_server

        pool = _PoolStub()
        service = ServerUpdateService(_Application())
        service._running = True
        service._session = ("server", "artist", "ticket")

        with (
            patch.object(env_inst, "server_pool", pool),
            patch.object(env_inst, "logins", {"artist": object()}),
            patch.object(env_server, "get_ticket", return_value="ticket"),
            patch.object(env_server, "get_server", return_value="server"),
            patch.object(env_server, "get_user", return_value="artist"),
        ):
            service.poll()

        def cancel_after_cache_read(*_args):
            service.stop()
            return ""

        with (
            patch.object(server_cache, "read_cursor", side_effect=cancel_after_cache_read),
            patch.object(tc, "get_server_updates") as query,
        ):
            self.assertIsNone(pool.operation())

        query.assert_not_called()

    def test_successful_authentication_wakes_an_already_running_service(self):
        from thlib.environment import env_inst, env_server

        service = ServerUpdateService(_Application())
        service._running = True
        service._busy = False

        with (
            patch.object(env_inst, "logins", {"artist": object()}),
            patch.object(env_server, "get_ticket", return_value="ticket"),
            patch.object(env_server, "get_server", return_value="server"),
            patch.object(env_server, "get_user", return_value="artist"),
            patch.object(service, "poll") as poll,
        ):
            service.sync_authentication()

        poll.assert_called_once_with()

    def test_expired_session_stops_updates_with_cached_ticket_and_logins(self):
        from thlib.environment import env_inst, env_server

        application = _Application()
        application.authentication_required = True
        service = ServerUpdateService(application)
        service._running = True
        pool = _PoolStub()
        with (
            patch.object(env_inst, "server_pool", pool),
            patch.object(env_inst, "logins", {"artist": object()}),
            patch.object(env_server, "get_ticket", return_value="rejected-ticket"),
        ):
            service.sync_authentication()
            self.assertFalse(service.running)
            service.start()
            self.assertFalse(service.running)
            self.assertIsNone(pool.operation)
            application.authentication_required = False
            service.sync_authentication()
            self.assertTrue(service.running)
            self.assertTrue(pool.worker.started)
            service.stop()

    def test_sign_out_stops_background_updates(self):
        from thlib.environment import env_inst, env_server

        service = ServerUpdateService(_Application())
        service._running = True

        with (
            patch.object(env_inst, "logins", None),
            patch.object(env_server, "get_ticket", return_value=""),
            patch.object(service, "stop") as stop,
        ):
            service.sync_authentication()

        stop.assert_called_once_with()

    def test_hidden_messages_do_not_start_message_polling(self):
        searched_types = []

        class Search:
            def __init__(self, search_type):
                searched_types.append(search_type)

        class SearchKey:
            pass

        search_module = ModuleType("pyasm.search")
        search_module.Search = Search
        search_module.SearchKey = SearchKey
        search_module.SearchType = _InitializedSearchType
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
                include_messages=False,
            )

        self.assertFalse(result["messagePollAttempted"])
        self.assertNotIn("sthpw/subscription", searched_types)

    def test_uninitialized_messages_skip_all_chat_and_presence_work(self):
        searched_types = []

        class Search:
            def __init__(self, search_type):
                searched_types.append(search_type)

        class SearchKey:
            pass

        class SearchType:
            @staticmethod
            def get_columns(_search_type):
                return []

        search_module = ModuleType("pyasm.search")
        search_module.Search = Search
        search_module.SearchKey = SearchKey
        search_module.SearchType = SearchType
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
                include_messages=True,
                include_reactions=True,
                include_presence=True,
                heartbeat_presence=True,
            )

        self.assertFalse(result["messagesInitialized"])
        self.assertFalse(result["messagePollAttempted"])
        self.assertEqual(result["messages"], [])
        self.assertEqual(result["reactions"], [])
        self.assertEqual(result["presence"], [])
        self.assertEqual(searched_types, [])

    def test_undefined_message_search_type_is_an_uninitialized_schema(self):
        searched_types = []

        class Search:
            def __init__(self, search_type):
                searched_types.append(search_type)

        class SearchKey:
            pass

        class SearchType:
            @staticmethod
            def get_columns(_search_type):
                raise AttributeError(
                    "'Undefined' object has no attribute 'get_columns'"
                )

        search_module = ModuleType("pyasm.search")
        search_module.Search = Search
        search_module.SearchKey = SearchKey
        search_module.SearchType = SearchType
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
                include_messages=True,
                include_reactions=True,
                include_presence=True,
            )

        self.assertFalse(result["messagesInitialized"])
        self.assertFalse(result["messagePollAttempted"])
        self.assertEqual(result["messages"], [])
        self.assertEqual(result["presence"], [])
        self.assertEqual(searched_types, [])

    def test_conversation_query_reports_undefined_schema_as_missing(self):
        class Search:
            def __init__(self, _search_type):
                pass

        class SearchKey:
            pass

        class SearchType:
            @staticmethod
            def get_columns(_search_type):
                raise AttributeError(
                    "'Undefined' object has no attribute 'get_columns'"
                )

        class Security:
            @staticmethod
            def is_admin():
                return True

        class Environment:
            @staticmethod
            def get_security():
                return Security()

        search_module = ModuleType("pyasm.search")
        search_module.Search = Search
        search_module.SearchKey = SearchKey
        search_module.SearchType = SearchType
        common_module = ModuleType("pyasm.common")
        common_module.Environment = Environment
        biz_module = ModuleType("pyasm.biz")
        biz_module.Snapshot = object
        pyasm_module = ModuleType("pyasm")
        pyasm_module.biz = biz_module
        pyasm_module.search = search_module
        pyasm_module.common = common_module
        fake_server = type("Server", (), {
            "get_login": staticmethod(lambda: "admin"),
        })()

        with patch.dict(sys.modules, {
            "pyasm": pyasm_module,
            "pyasm.biz": biz_module,
            "pyasm.common": common_module,
            "pyasm.search": search_module,
        }), patch.object(tactic_query, "server", fake_server, create=True):
            result = json.loads(tactic_query.query_chat_conversations())

        self.assertFalse(result["initialized"])
        self.assertTrue(result["canInitialize"])
        self.assertEqual(
            [item["searchType"] for item in result["missingColumns"]],
            ["sthpw/message", "sthpw/message_log"],
        )

    def test_missing_chat_tables_skip_column_queries(self):
        class Search:
            def __init__(self, _search_type):
                raise AssertionError("chat tables must not be queried")

        class SearchKey:
            pass

        class Sql:
            @staticmethod
            def table_exists(_table):
                return False

        class SearchType:
            @staticmethod
            def get_sql_by_search_type(_search_type):
                return Sql()

            @staticmethod
            def get_columns(_search_type):
                raise AssertionError("missing tables have no columns")

        class Security:
            @staticmethod
            def is_admin():
                return True

        class Environment:
            @staticmethod
            def get_security():
                return Security()

        search_module = ModuleType("pyasm.search")
        search_module.Search = Search
        search_module.SearchKey = SearchKey
        search_module.SearchType = SearchType
        common_module = ModuleType("pyasm.common")
        common_module.Environment = Environment
        biz_module = ModuleType("pyasm.biz")
        biz_module.Snapshot = object
        pyasm_module = ModuleType("pyasm")
        pyasm_module.biz = biz_module
        pyasm_module.search = search_module
        pyasm_module.common = common_module
        fake_server = type("Server", (), {
            "get_login": staticmethod(lambda: "admin"),
        })()

        with patch.dict(sys.modules, {
            "pyasm": pyasm_module,
            "pyasm.biz": biz_module,
            "pyasm.common": common_module,
            "pyasm.search": search_module,
        }), patch.object(tactic_query, "server", fake_server, create=True):
            conversations = json.loads(
                tactic_query.query_chat_conversations()
            )
            updates = tactic_query.query_server_updates(
                include_activity=False,
                include_messages=True,
                include_reactions=True,
                include_presence=True,
            )

        self.assertFalse(conversations["initialized"])
        self.assertFalse(updates["messagesInitialized"])
        self.assertFalse(updates["messagePollAttempted"])

    def test_server_update_query_includes_a_clock_sample(self):
        class Search:
            def __init__(self, _search_type):
                pass

        class SearchKey:
            pass

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
                include_messages=False,
            )

        self.assertEqual(
            set(result["serverClock"]),
            {"utcStarted", "utcEnded"},
        )

    def test_server_source_query_errors_are_not_masked(self):
        class Search:
            def __init__(self, search_type):
                self.search_type = search_type

            def add_filter(self, *_args, **_kwargs):
                pass

            def add_order_by(self, *_args, **_kwargs):
                pass

            def set_limit(self, *_args, **_kwargs):
                pass

            def get_sobjects(self):
                if self.search_type in {
                    "sthpw/subscription", "sthpw/status_log",
                }:
                    raise RuntimeError(
                        'do_query error: SELECT "sthpw"."public".'
                        '"{}".* LIMIT 0'.format(
                            self.search_type.rsplit("/", 1)[-1]
                        )
                    )
                return []

        class SearchKey:
            pass

        search_module = ModuleType("pyasm.search")
        search_module.Search = Search
        search_module.SearchKey = SearchKey
        search_module.SearchType = _InitializedSearchType
        pyasm_module = ModuleType("pyasm")
        pyasm_module.search = search_module
        fake_server = type("Server", (), {
            "get_login": staticmethod(lambda: "artist"),
        })()

        with patch.dict(sys.modules, {
            "pyasm": pyasm_module,
            "pyasm.search": search_module,
        }), patch.object(tactic_query, "server", fake_server, create=True):
            with self.assertRaisesRegex(RuntimeError, "subscription"):
                tactic_query.query_server_updates(
                    include_activity=False,
                    include_reactions=False,
                )
            with self.assertRaisesRegex(RuntimeError, "status_log"):
                tactic_query.query_server_updates(
                    project_code="demo",
                    include_cache_changes=False,
                    include_messages=False,
                    include_presence=False,
                )

    def test_retire_log_uses_search_type_scope_before_presence(self):
        searches = []

        class Record:
            def __init__(self, values):
                self.values = dict(values)

            def get_value(self, key, no_exception=False):
                return self.values.get(key)

            def get_code(self):
                return self.values.get("code")

            def get_data(self):
                return dict(self.values)

        presence = Record({
            "code": "ONLINE_STATUS_ARTIST",
            "category": "online_status",
            "login": "artist",
            "message": "2026-08-25T12:00:00Z",
            "metadata": {
                "lastSeen": "2026-08-25T12:00:00Z",
            },
        })

        class Search:
            def __init__(self, search_type):
                self.search_type = search_type
                self.filters = []
                searches.append(self)

            def add_filter(self, *args, **kwargs):
                self.filters.append((args, kwargs))

            def add_order_by(self, *_args, **_kwargs):
                pass

            def set_limit(self, *_args, **_kwargs):
                pass

            def get_sobjects(self):
                if self.search_type == "sthpw/message":
                    return [presence]
                return []

            def get_sobject(self):
                records = self.get_sobjects()
                return records[0] if records else None

        class SearchKey:
            @staticmethod
            def get_by_sobject(record, use_id=False):
                return "sthpw/message?code={}".format(record.get_code())

        search_module = ModuleType("pyasm.search")
        search_module.Search = Search
        search_module.SearchKey = SearchKey
        search_module.SearchType = _InitializedSearchType
        pyasm_module = ModuleType("pyasm")
        pyasm_module.search = search_module
        fake_server = type("Server", (), {
            "get_login": staticmethod(lambda: "artist"),
            "update": staticmethod(lambda *_args, **_kwargs: None),
        })()

        with patch.dict(sys.modules, {
            "pyasm": pyasm_module,
            "pyasm.search": search_module,
        }), patch.object(tactic_query, "server", fake_server, create=True):
            result = tactic_query.query_server_updates(
                project_code="demo",
                include_cache_changes=True,
                include_activity=False,
                include_messages=False,
                include_presence=True,
            )

        retire_searches = [
            search for search in searches
            if search.search_type == "sthpw/retire_log"
        ]
        self.assertEqual(len(retire_searches), 2)
        retire_filters = [
            (args[0], args[1], kwargs.get("op"))
            for search in retire_searches
            for args, kwargs in search.filters
        ]
        self.assertNotIn("project_code", [
            column for column, _value, _operator in retire_filters
        ])
        self.assertIn(
            ("search_type", "%project=demo%", "like"),
            retire_filters,
        )
        self.assertIn(
            ("search_type", "sthpw/%", "like"),
            retire_filters,
        )
        self.assertEqual(result["presence"][0]["login"], "artist")

    def test_presence_roster_can_refresh_without_publishing_a_heartbeat(self):
        searches = []

        class Record:
            def __init__(self, values):
                self.values = dict(values)

            def get_value(self, key, no_exception=False):
                return self.values.get(key)

        presence = Record({
            "login": "artist",
            "message": "2026-08-31T12:00:00Z",
            "metadata": {"lastSeen": "2026-08-31T12:00:00Z"},
        })

        class Search:
            def __init__(self, search_type):
                self.search_type = search_type
                searches.append(self)

            def add_filter(self, *_args, **_kwargs):
                pass

            def add_order_by(self, *_args, **_kwargs):
                pass

            def get_sobjects(self):
                return [presence] if self.search_type == "sthpw/message" else []

        class SearchKey:
            pass

        search_module = ModuleType("pyasm.search")
        search_module.Search = Search
        search_module.SearchKey = SearchKey
        search_module.SearchType = _InitializedSearchType
        pyasm_module = ModuleType("pyasm")
        pyasm_module.search = search_module
        fake_server = Mock()
        fake_server.get_login.return_value = "artist"

        with patch.dict(sys.modules, {
            "pyasm": pyasm_module,
            "pyasm.search": search_module,
        }), patch.object(tactic_query, "server", fake_server, create=True):
            result = tactic_query.query_server_updates(
                include_activity=False,
                include_reactions=False,
                include_messages=False,
                include_presence=True,
                heartbeat_presence=False,
            )

        self.assertEqual(result["presence"][0]["login"], "artist")
        self.assertEqual(
            [search.search_type for search in searches],
            ["sthpw/message"],
        )
        fake_server.update.assert_not_called()
        fake_server.insert.assert_not_called()

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

    def test_ready_updates_shared_clock_before_publishing_batch(self):
        clock = Mock()
        service = ServerUpdateService(_Application(), clock=clock)
        service._running = True
        service._session = ("server", "artist", "ticket")
        batches = []
        service.batchReady.connect(batches.append)

        with patch.object(service, "_schedule"):
            service._ready({
                "messages": [],
                "activity": [{
                    "code": "NOTE00001",
                    "__event_timestamp__": "2026-08-30 12:00:00",
                }],
                "reactions": [],
                "serverClock": {
                    "utcStarted": "2026-08-30T10:00:00Z",
                    "utcEnded": "2026-08-30T10:00:00.100000Z",
                    "localEnded": "2026-08-30T13:00:00.100000",
                },
                "__clientClockStartedEpoch": 100.0,
                "__clientClockReceivedEpoch": 100.2,
            })

        clock.observe.assert_called_once_with(
            {
                "utcStarted": "2026-08-30T10:00:00Z",
                "utcEnded": "2026-08-30T10:00:00.100000Z",
                "localEnded": "2026-08-30T13:00:00.100000",
            },
            100.0,
            100.2,
            session=("server", "artist", "ticket"),
        )
        self.assertEqual(len(batches), 1)

    def test_sse_closed_connection_logs_and_retries_without_modal(self):
        from thlib.ui.server_event_stream import ServerEventStream
        application = _Application()
        application.debug_log = Mock()
        service = ServerUpdateService(application)
        service._running = True
        service._update_mode = 'sse'
        modal_errors = []
        service.errorRaised.connect(lambda *args: modal_errors.append(args))
        failure = ServerEventStream._error({'error': 'Stream closed', 'error_code': 'stream_closed'}, 200)
        details = {'endpoint': '/admin/server-events', 'http_status': 200, 'network_error': 'NoError'}
        with patch.object(service, '_schedule') as schedule:
            service._stream_failed(service._request_generation, {'exception': failure, 'details': details})
        self.assertEqual(modal_errors, [])
        self.assertEqual(service._failure_count, 1)
        self.assertGreater(schedule.call_args.args[0], 0)
        self.assertLess(schedule.call_args.args[0], 3000)
        args, kwargs = application.debug_log.log.call_args
        self.assertEqual(args, ('ERROR', 'Stream closed'))
        self.assertEqual(kwargs['group'], 'communication/server-updates')
        self.assertEqual(json.loads(kwargs['details']), dict(details, attempt=1))
        application.debug_log.log.reset_mock()
        service._stream_failed(service._request_generation-1, {'exception': failure})
        application.debug_log.log.assert_not_called()

    def test_sse_failure_is_written_with_default_debug_log_filters(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from thlib.ui.debug_logging import DebugLogController
        from thlib.ui.server_event_stream import ServerEventStream
        with TemporaryDirectory() as folder, patch('thlib.ui.debug_logging.env_read_config', return_value={}):
            application = _Application()
            application.debug_log = DebugLogController(Path(folder))
            service = ServerUpdateService(application)
            service._running = True
            try:
                error = ServerEventStream._error({'error': 'Stream closed', 'error_code': 'stream_closed'}, 200)
                with patch.object(service, '_schedule'):
                    service._stream_failed(service._request_generation, {'exception': error, 'details': {'endpoint': '/admin/server-events'}})
                self.assertEqual(len(application.debug_log._live_entries), 1)
                record = application.debug_log._live_entries[0]
                self.assertEqual(record['level'], 'ERROR')
                self.assertIn('/admin/server-events', record['details'])
            finally:
                application.debug_log.shutdown()
            records = application.debug_log._read_session_records(application.debug_log._json_log)
            self.assertEqual(records[-1]['message'], 'Stream closed')

    def test_sse_permanent_error_is_logged_and_authentication_is_preserved(self):
        from thlib.ui.server_event_stream import ServerEventStream
        for code, status in (('permission_denied', 403), ('authentication_failed', 403), ('transport_error', 200)):
            with self.subTest(code=code):
                application = _Application()
                application.debug_log = Mock()
                application.request_authentication = Mock()
                service = ServerUpdateService(application)
                service._running = True
                errors = []
                service.errorRaised.connect(lambda *args: errors.append(args))
                failure = ServerEventStream._error({'error': code, 'error_code': code}, status)
                with patch.object(service, '_schedule'):
                    service._stream_failed(service._request_generation, {'exception': failure})
                self.assertEqual(bool(errors), code == 'permission_denied')
                self.assertEqual(application.request_authentication.called, code == 'authentication_failed')
                self.assertEqual(application.debug_log.log.call_args.args[0], 'ERROR')

    def test_502_is_a_transient_error(self):
        error = HTTPError(
            "http://server/tactic/default/Api/", 502,
            "Proxy Error", {}, None,
        )
        try:
            self.assertTrue(ServerUpdateService._is_transient_error(error))
        finally:
            error.close()

    def test_sudo_context_fault_is_deferred_to_the_next_poll(self):
        from thlib import server_cache
        import thlib.tactic_classes as tc
        from thlib.environment import env_inst, env_server

        pool = _PoolStub()
        service = ServerUpdateService(_Application())
        service._running = True
        reporting_states = []

        with (
            patch.object(env_inst, "server_pool", pool),
            patch.object(env_inst, "logins", {"artist": object()}),
            patch.object(env_server, "get_ticket", return_value="ticket"),
            patch.object(env_server, "get_server", return_value="server"),
            patch.object(env_server, "get_user", return_value="artist"),
        ):
            service.poll()

        def fail_temporarily(**_options):
            reporting_states.append(transient_error_reporting_deferred())
            raise Fault(1, "('count of sudo: ', 0)")

        with (
            patch.object(
                tc, "get_server_updates", side_effect=fail_temporarily
            ),
            patch.object(server_cache, "read_cursor", return_value=""),
        ):
            result = pool.operation()

        self.assertTrue(result["__transient_error__"])
        self.assertEqual(reporting_states, [True])

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

    def test_poll_health_changes_only_after_failures_and_recovers(self):
        service = ServerUpdateService(_Application())
        service._running = True
        health = []
        service.connectionChecked.connect(health.append)
        with patch.object(service, "_schedule"):
            for _ in range(4):
                service._transient_failed({"message": "offline"})
            self.assertEqual(health, [])
            service._transient_failed({"message": "offline"})
            service._ready({})
        self.assertEqual(health, [False, True])

    def test_poll_interval_restarts_normal_schedule(self):
        service = ServerUpdateService(_Application())
        service._running = True
        service._busy = False
        target = 60 if service.poll_interval != 60 else 30
        with patch.object(service, "_schedule") as schedule:
            service.set_poll_interval(target)
        self.assertEqual(service.poll_interval, target)
        schedule.assert_called_once_with(target * 1000)

    def test_batch_delay_is_persisted_and_updates_live_transport(self):
        application = _Application()
        service = ServerUpdateService(application)
        self.assertEqual(service.batch_delay, 200)
        service._stream = type('Stream', (), {'batch_delay': 200})()
        service.set_batch_delay(1000)
        self.assertEqual(service.batch_delay, 1000)
        self.assertEqual(service._stream.batch_delay, 1000)
        self.assertEqual(application._settings['network/serverUpdateBatchDelay'], 1000)
        service.set_batch_delay(0)
        self.assertEqual(service.batch_delay, 1000)
        application._settings['network/serverUpdateBatchDelay'] = [500]
        self.assertEqual(ServerUpdateService(application).batch_delay, 200)

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
