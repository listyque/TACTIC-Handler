"""Advanced Search suggestion payloads cross the real worker/model boundary."""

import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PySide6.QtCore import QEventLoop, QObject, QTimer, Signal

from tests.qt_application import gui_test_application
from thlib.pool import ThreadsPool
from thlib.ui.controllers.advanced_search import AdvancedSearchMixin
from thlib.ui.workspace_models.records import RecordListModel


class _Controller(AdvancedSearchMixin, QObject):
    advanced_filter_suggestions_changed = Signal()

    def __init__(self):
        super().__init__()
        self._filter_suggestion_worker = None
        self._filter_suggestion_request_id = ""
        self._pending_filter_suggestion = None
        self.errors = []
        self.workspace_state = SimpleNamespace(
            advanced_filter_suggestion_model=RecordListModel(
                ("title", "description", "keyword", "values"),
            ),
            filter_model=RecordListModel(("column", "value")),
        )
        self.workspace_state.filter_model.replace([{"column": "name", "value": ""}])

    def _active_stype(self):
        return SimpleNamespace(
            get_columns_info=lambda: {"name": {}, "code": {}, "description": {}},
            get_code=lambda: "demo/asset",
            get_project=lambda: SimpleNamespace(get_code=lambda: "demo"),
        )

    def _report_error_payload(self, payload, _group, _worker):
        self.errors.append(payload)

    def _notify(self, message):
        self.errors.append(message)


class AdvancedSearchSuggestionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def test_list_response_is_one_payload_and_can_be_accepted(self):
        for records in ([], [
            {"name": "Chair", "description": "first\nline"},
            {"name": "Chest", "description": "second"},
        ]):
            with self.subTest(records=records):
                pool = ThreadsPool(max_threads=1)
                controller = _Controller()
                loop = QEventLoop()
                timeout = QTimer()
                timeout.setSingleShot(True)
                timeout.timeout.connect(loop.quit)
                pool.finished.connect(loop.quit)
                query_threads = []

                def query(**_kwargs):
                    query_threads.append(threading.get_ident())
                    return records

                try:
                    with patch("thlib.environment.env_inst", SimpleNamespace(server_pool=pool)), \
                            patch("thlib.tactic_classes.server_query", side_effect=query):
                        timeout.start(2000)
                        controller.request_advanced_filter_suggestions(0, "name", "Ch")
                        loop.exec()
                    self.assertTrue(timeout.isActive(), "Worker did not settle")
                    self.assertEqual(controller.errors, [])
                    self.assertEqual(len(query_threads), 1)
                    self.assertNotEqual(query_threads[0], threading.get_ident())
                    suggestions = controller.workspace_state.advanced_filter_suggestion_model
                    self.assertEqual(suggestions.count(), len(records))
                    if records:
                        self.assertEqual(suggestions.get(0)["description"], "first line")
                        controller.accept_advanced_filter_suggestion(0, 1)
                        self.assertEqual(
                            controller.workspace_state.filter_model.get(0)["value"], "Chest",
                        )
                        self.assertEqual(suggestions.count(), 0)
                finally:
                    timeout.stop()
                    pool.exit(1000)


if __name__ == "__main__":
    unittest.main()
