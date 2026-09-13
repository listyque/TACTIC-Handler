from __future__ import annotations

import json
import sys
from types import ModuleType
import unittest
from unittest.mock import patch

from thlib.ui.script_history import script_history_request


class _Record:
    def __init__(self, values):
        self.values = dict(values)

    def get_value(self, name, no_exception=False):
        return self.values.get(name)

    def get_id(self):
        return self.values.get("id")

    def get_data(self):
        return dict(self.values)


class _Script(_Record):
    def get_base_search_type(self):
        return "config/custom_script"

    def get_search_type(self):
        return "config/custom_script?project=demo"


class ScriptHistoryTests(unittest.TestCase):
    def test_transaction_log_reconstructs_a_saved_script_version(self):
        script = _Script({
            "id": 1,
            "code": "CUSTOM_SCRIPT00001",
            "script": "print('current')",
            "folder": "tools",
            "title": "runner",
            "language": "local_python",
        })
        object_logs = [
            _Record({
                "id": 12,
                "search_type": "config/custom_script?project=demo",
                "search_id": 1,
                "transaction_log_id": 102,
                "timestamp": "2026-09-06 12:00:00",
            }),
            _Record({
                "id": 11,
                "search_type": "config/custom_script?project=demo",
                "search_id": 1,
                "transaction_log_id": 101,
                "timestamp": "2026-09-05 12:00:00",
            }),
        ]
        transactions = [
            _Record({
                "id": 102,
                "code": "TX_UPDATE",
                "login": "editor",
                "timestamp": "2026-09-06 12:00:00",
                "transaction": """
                    <transaction>
                      <sobject search_type="config/custom_script"
                               search_code="CUSTOM_SCRIPT00001"
                               action="update">
                        <column name="script" from="print('previous')"
                                to="print('current')"/>
                      </sobject>
                    </transaction>
                """,
            }),
            _Record({
                "id": 101,
                "code": "TX_CREATE",
                "login": "creator",
                "timestamp": "2026-09-05 12:00:00",
                "transaction": """
                    <transaction>
                      <sobject search_type="config/custom_script"
                               search_code="CUSTOM_SCRIPT00001"
                               action="insert">
                        <column name="script" from=""
                                to="print('previous')"/>
                      </sobject>
                    </transaction>
                """,
            }),
        ]

        class Search:
            def __init__(self, search_type):
                self.search_type = search_type
                self.filters = []

            def add_filter(self, name, value):
                self.filters.append((name, value))

            def add_filters(self, name, values):
                self.filters.append((name, list(values)))

            def add_order_by(self, _name, direction="asc"):
                return None

            def set_limit(self, _limit):
                return None

            def get_sobjects(self):
                records = (
                    transactions
                    if self.search_type == "sthpw/transaction_log"
                    else object_logs
                    if self.search_type == "sthpw/sobject_log"
                    else []
                )
                return [
                    record for record in records
                    if all(
                        record.get_value(name) in value
                        if isinstance(value, list)
                        else record.get_value(name) == value
                        for name, value in self.filters
                    )
                ]

        pyasm = ModuleType("pyasm")
        biz = ModuleType("pyasm.biz")
        search = ModuleType("pyasm.search")
        biz.Project = type(
            "Project", (), {"get_project_code": staticmethod(lambda: "demo")}
        )
        search.Search = Search
        search.SearchKey = type(
            "SearchKey",
            (),
            {"get_by_search_key": staticmethod(lambda _key: script)},
        )
        with patch.dict(sys.modules, {
            "pyasm": pyasm,
            "pyasm.biz": biz,
            "pyasm.search": search,
        }):
            history = json.loads(script_history_request(
                "history",
                "demo",
                "config/custom_script?project=demo&code=CUSTOM_SCRIPT00001",
            ))
            revision = json.loads(script_history_request(
                "revision",
                "demo",
                "config/custom_script?project=demo&code=CUSTOM_SCRIPT00001",
                "TX_CREATE",
            ))

        self.assertEqual(
            [entry["revisionId"] for entry in history["history"]],
            ["TX_UPDATE", "TX_CREATE"],
        )
        self.assertTrue(history["history"][0]["current"])
        self.assertEqual(
            revision["revision"]["script"], "print('previous')"
        )
        self.assertEqual(revision["revision"]["actor"], "creator")


if __name__ == "__main__":
    unittest.main()
