import sys
import types
import unittest
from unittest.mock import patch

from thlib import tactic_query


class _SObject:
    def __init__(self, data):
        self._data = dict(data)

    def get_data(self):
        return dict(self._data)

    def get_id(self):
        return self._data.get("id")

    def get_code(self):
        return self._data.get("code")

    def get_name(self):
        return self._data.get("name")

    def get_value(self, name):
        return self._data.get(name)

    def get_xml_value(self, name):
        return _XmlValue(
            self._data.get("_expanded_transaction")
            or self._data.get(name) or ""
        )


class _XmlValue:
    def __init__(self, value):
        self._value = str(value or "")

    def to_string(self, pretty=False):
        return self._value


class _Search:
    rows = {}
    instances = []

    def __init__(self, search_type):
        self.search_type = search_type
        self.limit = None
        self.filters = []
        self.__class__.instances.append(self)

    def add_filter(self, *args, **kwargs):
        self.filters.append((args, kwargs))

    def add_filters(self, *_args, **_kwargs):
        pass

    def add_order_by(self, *_args, **_kwargs):
        pass

    def add_column(self, *_args, **_kwargs):
        pass

    def set_limit(self, value, *_args, **_kwargs):
        self.limit = value

    def get_sobjects(self):
        key = self.search_type.split("?", 1)[0]
        return [_SObject(row) for row in self.rows.get(key, ())]


class _SearchKey:
    @staticmethod
    def get_by_sobject(sobject, use_id=False):
        data = sobject.get_data()
        identity = data.get("id") if use_id else data.get("code")
        return "skey://test?code={0}".format(identity or "")


class ActivityAuditQueryTests(unittest.TestCase):
    def test_excluded_login_is_removed_from_pages_and_calendar_counts(self):
        _Search.instances = []
        _Search.rows = {
            "sthpw/snapshot": [{
                "id": 1, "code": "SNAPSHOT001", "login": "Artist",
                "timestamp": "2026-08-24 10:00:00",
                "project_code": "demo", "search_type": "demo/asset",
                "search_code": "ASSET001",
            }, {
                "id": 2, "code": "SNAPSHOT002", "login": "supervisor",
                "timestamp": "2026-08-24 11:00:00",
                "project_code": "demo", "search_type": "demo/asset",
                "search_code": "ASSET001",
            }],
            "sthpw/file": [],
            "demo/asset": [{
                "id": 10, "code": "ASSET001", "name": "Bathroom",
            }],
        }
        pyasm = types.ModuleType("pyasm")
        search = types.ModuleType("pyasm.search")
        search.Search = _Search
        search.SearchKey = _SearchKey

        with patch.dict(sys.modules, {
            "pyasm": pyasm,
            "pyasm.search": search,
        }):
            payload = tactic_query.query_user_recent_activity(
                project_code="demo", kinds=("publication",),
                include_day_counts=True, exclude_login="artist",
            )

        self.assertEqual(
            [record["eventId"] for record in payload["records"]],
            ["publication:SNAPSHOT002"],
        )
        self.assertEqual(payload["dayCounts"], [{
            "dateKey": "2026-08-24", "count": 1,
        }])

    def test_object_scope_reads_legacy_parent_ids_without_search_code(self):
        class FilteringSearch(_Search):
            def add_filters(self, name, values, **kwargs):
                self.filters.append(((name, list(values)), kwargs))

            def get_sobjects(self):
                key = self.search_type.split("?", 1)[0]
                rows = list(self.rows.get(key, ()))
                for args, _kwargs in self.filters:
                    if not args:
                        continue
                    name, value = args[:2]
                    if isinstance(value, list):
                        rows = [
                            row for row in rows
                            if str(row.get(name) or "")
                            in {str(item) for item in value}
                        ]
                    else:
                        rows = [
                            row for row in rows
                            if str(row.get(name) or "") == str(value)
                        ]
                return [_SObject(row) for row in rows]

        FilteringSearch.instances = []
        FilteringSearch.rows = {
            "sthpw/task": [{
                "id": 10, "code": "TASK001",
                "search_type": "demo/asset", "search_id": 1,
                "process": "model", "status": "In Progress",
                "login": "lead", "timestamp": "2026-08-25 10:00:00",
                "project_code": "demo",
            }],
            "sthpw/status_log": [{
                "id": 11, "search_type": "sthpw/task", "search_id": 10,
                "from_status": "Ready", "to_status": "In Progress",
                "login": "lead", "timestamp": "2026-08-25 11:00:00",
                "project_code": "demo",
            }],
            "sthpw/note": [{
                "id": 12, "code": "NOTE001",
                "search_type": "demo/asset", "search_id": 1,
                "note": "Please revise", "login": "lead",
                "timestamp": "2026-08-25 12:00:00",
                "project_code": "demo",
            }],
            "sthpw/snapshot": [{
                "id": 13, "code": "SNAP001",
                "search_type": "demo/asset", "search_id": 1,
                "process": "model", "context": "model/main",
                "version": 3, "login": "artist",
                "timestamp": "2026-08-25 13:00:00",
                "project_code": "demo",
            }],
            "sthpw/change_timestamp": [],
            "sthpw/sobject_log": [],
            "sthpw/file": [],
            "demo/asset": [{
                "id": 1, "code": "ASSET001", "name": "Bathroom",
            }],
        }
        pyasm = types.ModuleType("pyasm")
        search = types.ModuleType("pyasm.search")
        search.Search = FilteringSearch
        search.SearchKey = _SearchKey

        with patch.dict(sys.modules, {
            "pyasm": pyasm,
            "pyasm.search": search,
        }):
            records = tactic_query.query_user_recent_activity(
                project_code="demo", limit=25,
                kinds=("status", "publication", "note", "task"),
                object_scope={
                    "searchType": "demo/asset",
                    "searchCode": "ASSET001",
                    "searchId": "1",
                    "taskCodes": ["TASK001"],
                    "taskIds": ["10"],
                    "indexedObjects": [{
                        "searchType": "demo/asset",
                        "searchCode": "ASSET001",
                        "searchId": "1",
                    }, {
                        "searchType": "sthpw/task",
                        "searchCode": "TASK001",
                        "searchId": "10",
                    }],
                },
            )

        self.assertEqual(
            {record["kind"] for record in records},
            {"status", "publication", "note", "task"},
        )
        self.assertTrue(all(
            record["targetTitle"] == "Bathroom" for record in records
        ))
        scoped_source_queries = [
            query for query in FilteringSearch.instances
            if query.search_type in {
                "sthpw/task", "sthpw/status_log", "sthpw/note",
                "sthpw/snapshot",
            }
        ]
        self.assertTrue(all(any(
            args and args[0] == "search_id"
            for args, _kwargs in query.filters
        ) for query in scoped_source_queries[:4]))

    def test_scoped_audit_finds_old_instance_links_before_project_limit(self):
        unrelated = [{
            "id": index,
            "code": "TX_OTHER_{0:03d}".format(index),
            "login": "artist",
            "timestamp": "2026-08-25 18:{0:02d}:00".format(index % 60),
            "namespace": "demo",
            "transaction": """
                <transaction>
                  <sobject search_type="demo/asset"
                           search_code="OTHER{0:03d}" action="update">
                    <column name="description" from="old" to="new"/>
                  </sobject>
                </transaction>
            """.format(index),
        } for index in range(100, 190)]
        link_transaction = {
            "id": 1,
            "code": "TX_LINK_OLD",
            "login": "artist",
            "timestamp": "2026-08-20 10:00:00",
            "namespace": "demo",
            "transaction": """
                <transaction>
                  <sobject search_type="demo/texture_in_assets"
                           search_code="LINK001" action="insert">
                    <column name="texture_code" to="TEXTURE001"/>
                    <column name="assets_code" to="ASSET001"/>
                  </sobject>
                </transaction>
            """,
        }
        unlink_transaction = {
            "id": 2,
            "code": "TX_UNLINK_OLD",
            "login": "artist",
            "timestamp": "2026-08-19 10:00:00",
            "namespace": "demo",
            "transaction": """
                <transaction>
                  <sobject search_type="demo/texture_in_assets"
                           search_code="LINK001" action="delete">
                    <column name="texture_code" from="TEXTURE001"/>
                    <column name="assets_code" from="ASSET001"/>
                  </sobject>
                </transaction>
            """,
        }

        class LimitingSearch(_Search):
            def add_filters(self, name, values, **kwargs):
                self.filters.append(((name, list(values)), kwargs))

            def get_sobjects(self):
                key = self.search_type.split("?", 1)[0]
                rows = list(self.rows.get(key, ()))
                for args, kwargs in self.filters:
                    if not args:
                        continue
                    name, value = args[:2]
                    if name == "transaction" and kwargs.get("op") == "like":
                        needle = str(value).strip("%")
                        rows = [
                            row for row in rows
                            if needle in str(row.get("transaction") or "")
                        ]
                    elif isinstance(value, list):
                        rows = [
                            row for row in rows
                            if row.get(name) in value
                        ]
                    else:
                        rows = [
                            row for row in rows
                            if row.get(name) == value
                        ]
                rows.sort(
                    key=lambda row: str(row.get("timestamp") or ""),
                    reverse=True,
                )
                if self.limit is not None:
                    rows = rows[:self.limit]
                return [_SObject(row) for row in rows]

        LimitingSearch.rows = {
            "sthpw/transaction_log": unrelated + [
                link_transaction, unlink_transaction,
            ],
            "sthpw/sobject_log": [],
            "sthpw/change_timestamp": [],
            "demo/asset": [{
                "id": 1, "code": "ASSET001", "name": "Bathroom",
            }],
            "demo/texture": [{
                "id": 2, "code": "TEXTURE001", "name": "Wall Texture",
            }],
        }

        class _Schema:
            @staticmethod
            def get():
                return _Schema()

            @staticmethod
            def get_foreign_keys(instance_type, endpoint_type):
                columns = {
                    ("demo/texture_in_assets", "demo/texture"):
                        "texture_code",
                    ("demo/texture_in_assets", "demo/asset"):
                        "assets_code",
                }
                column = columns.get((instance_type, endpoint_type))
                return ("code", column) if column else ()

        pyasm = types.ModuleType("pyasm")
        search = types.ModuleType("pyasm.search")
        search.Search = LimitingSearch
        search.SearchKey = _SearchKey
        biz = types.ModuleType("pyasm.biz")
        biz.Schema = _Schema

        with patch.dict(sys.modules, {
            "pyasm": pyasm,
            "pyasm.search": search,
            "pyasm.biz": biz,
        }):
            records = tactic_query.query_user_recent_activity(
                project_code="demo", kinds=("create", "delete"), limit=25,
                instance_relations={
                    "demo/texture_in_assets": [
                        "demo/texture", "demo/asset",
                    ],
                },
                object_scope={
                    "searchType": "demo/asset",
                    "searchCode": "ASSET001",
                    "searchId": "1",
                    "indexedObjects": [{
                        "searchType": "demo/asset",
                        "searchCode": "ASSET001",
                        "searchId": "1",
                    }],
                },
            )

        self.assertEqual(len(records), 2)
        self.assertEqual(
            {record["relationAction"] for record in records},
            {"link", "unlink"},
        )
        self.assertTrue(all(
            record["itemTitle"] == "Wall Texture" for record in records
        ))
        self.assertTrue(all(
            record["targetTitle"] == "Bathroom" for record in records
        ))
        transaction_queries = [
            search for search in LimitingSearch.instances
            if search.search_type == "sthpw/transaction_log"
        ]
        self.assertTrue(any(
            args[:2] == ("transaction", "%ASSET001%")
            for search in transaction_queries
            for args, _kwargs in search.filters
        ))

    def test_object_scope_includes_child_lifecycle_and_task_audit(self):
        _Search.rows = {
            "sthpw/transaction_log": [{
                "id": 90,
                "code": "TX_SCOPE_1",
                "login": "artist",
                "timestamp": "2026-08-25 16:00:00",
                "namespace": "demo",
                "transaction": """
                    <transaction>
                      <sobject search_type="demo/shot"
                               search_code="SHOT001" action="insert">
                        <column name="name" to="Shot 001"/>
                        <column name="asset_code" to="ASSET001"/>
                      </sobject>
                      <sobject search_type="sthpw/task"
                               search_code="TASK001" action="update">
                        <column name="search_type" to="demo/asset"/>
                        <column name="search_code" to="ASSET001"/>
                        <column name="process" to="model"/>
                        <column name="description" from="Old" to="New"/>
                      </sobject>
                      <sobject search_type="demo/shot"
                               search_code="SHOT002" action="delete">
                        <column name="name" from="Shot 002"/>
                        <column name="asset_code" from="ASSET001"/>
                      </sobject>
                      <sobject search_type="sthpw/note"
                               search_code="NOTE001" action="delete">
                        <column name="search_code" from="ASSET001"/>
                        <column name="note" from="Old note"/>
                      </sobject>
                      <sobject search_type="demo/asset"
                               search_code="ASSET001" action="update">
                        <column name="description" from="Old" to="New"/>
                      </sobject>
                      <sobject search_type="demo/shot"
                               search_code="SHOT999" action="insert">
                        <column name="name" to="Other shot"/>
                        <column name="asset_code" to="OTHER"/>
                      </sobject>
                    </transaction>
                """,
            }],
            "sthpw/sobject_log": [
                {
                    "id": 91,
                    "search_type": "demo/shot",
                    "transaction_log_id": 90,
                },
                {
                    "id": 92,
                    "search_type": "sthpw/task",
                    "transaction_log_id": 90,
                },
                {
                    "id": 93,
                    "search_type": "demo/asset",
                    "transaction_log_id": 90,
                },
            ],
            "sthpw/change_timestamp": [],
            "sthpw/task": [{
                "id": 10,
                "code": "TASK001",
                "search_type": "demo/asset",
                "search_code": "ASSET001",
                "process": "model",
                "context": "model",
                "status": "In Progress",
            }],
            "sthpw/status_log": [{
                "id": 11,
                "code": "STATUS001",
                "search_type": "sthpw/task",
                "search_code": "TASK001",
                "from_status": "In Progress",
                "to_status": "Approved",
                "login": "supervisor",
                "timestamp": "2026-08-25 16:05:00",
            }],
            "sthpw/snapshot": [],
            "sthpw/note": [],
            "sthpw/message_log": [],
            "demo/asset": [{
                "id": 1,
                "code": "ASSET001",
                "name": "Bathroom",
            }],
            "demo/shot": [{
                "id": 2,
                "code": "SHOT001",
                "name": "Shot 001",
            }],
        }
        pyasm = types.ModuleType("pyasm")
        search = types.ModuleType("pyasm.search")
        search.Search = _Search
        search.SearchKey = _SearchKey

        with patch.dict(sys.modules, {
            "pyasm": pyasm,
            "pyasm.search": search,
        }):
            records = tactic_query.query_user_recent_activity(
                project_code="demo",
                kinds=(
                    "status", "publication", "note", "task",
                    "create", "change", "delete", "work_hour",
                ),
                limit=100,
                object_scope={
                    "searchType": "demo/asset",
                    "searchCode": "ASSET001",
                    "searchId": "1",
                    "childTypes": ["demo/shot"],
                },
            )

        self.assertEqual(len(records), 6)
        self.assertNotIn("SHOT999", str(records))
        child_events = [
            record for record in records
            if record.get("itemType") == "demo/shot"
        ]
        self.assertEqual(
            {record["kind"] for record in child_events},
            {"create", "delete"},
        )
        self.assertEqual(
            {record["targetTitle"] for record in child_events},
            {"Bathroom"},
        )
        task_event = next(
            record for record in records
            if record.get("itemType") == "sthpw/task"
        )
        self.assertEqual(task_event["kind"], "change")
        self.assertEqual(task_event["taskCode"], "TASK001")
        self.assertEqual(task_event["process"], "model")
        self.assertEqual(
            {change["field"] for change in task_event["changes"]},
            {"process", "description"},
        )
        note_event = next(
            record for record in records
            if record.get("itemType") == "sthpw/note"
        )
        self.assertEqual(note_event["kind"], "delete")
        status_event = next(
            record for record in records if record.get("kind") == "status"
        )
        self.assertEqual(status_event["taskCode"], "TASK001")
        self.assertEqual(status_event["targetTitle"], "Bathroom")
        self.assertEqual(status_event["statusBefore"], "In Progress")
        self.assertEqual(status_event["statusAfter"], "Approved")

    def test_work_hour_transaction_is_enriched_with_task_and_parent(self):
        _Search.rows = {
            "sthpw/transaction_log": [{
                "id": 21,
                "code": "TX_WORK_1",
                "login": "listy",
                "timestamp": "2026-08-25 14:30:00",
                "namespace": "demo",
                "transaction": """
                    <transaction>
                      <sobject search_type="sthpw/work_hour"
                               search_code="WORK0001" action="insert">
                        <column name="task_code" to="TASK0001"/>
                        <column name="process" to="model"/>
                        <column name="login" to="artist"/>
                        <column name="day" to="2026-08-25 00:00:00"/>
                        <column name="straight_time" to="6.5"/>
                        <column name="over_time" to="0"/>
                        <column name="category" to="regular"/>
                        <column name="status" to="approved"/>
                        <column name="description" to="Retopology"/>
                      </sobject>
                    </transaction>
                """,
            }],
            "sthpw/sobject_log": [],
            "sthpw/change_timestamp": [],
            "sthpw/work_hour": [{
                "id": 31,
                "code": "WORK0001",
                "task_code": "TASK0001",
                "process": "model",
                "login": "artist",
                "day": "2026-08-25 00:00:00",
                "straight_time": 6.5,
                "over_time": 0,
                "category": "regular",
                "status": "approved",
                "description": "Retopology",
            }],
            "sthpw/task": [{
                "id": 41,
                "code": "TASK0001",
                "search_type": "demo/asset",
                "search_code": "ASSET001",
                "process": "model",
                "context": "model/retopo",
            }],
            "demo/asset": [{
                "id": 51,
                "code": "ASSET001",
                "name": "Bathroom",
                "pipeline_code": "asset",
            }],
        }
        pyasm = types.ModuleType("pyasm")
        search = types.ModuleType("pyasm.search")
        search.Search = _Search
        search.SearchKey = _SearchKey

        with patch.dict(sys.modules, {
            "pyasm": pyasm,
            "pyasm.search": search,
        }):
            payload = tactic_query.query_user_recent_activity(
                project_code="demo", kinds=("work_hour",), limit=25,
                include_day_counts=True,
            )
            scoped_records = tactic_query.query_user_recent_activity(
                project_code="demo", kinds=("work_hour",), limit=25,
                object_scope={
                    "searchType": "demo/asset",
                    "searchCode": "ASSET001",
                    "taskCodes": ["TASK0001"],
                },
            )

        self.assertEqual(payload["dayCounts"], [{
            "dateKey": "2026-08-25", "count": 1,
        }])
        self.assertEqual(len(payload["records"]), 1)
        record = payload["records"][0]
        self.assertEqual(record["kind"], "work_hour")
        self.assertEqual(record["actor"], "listy")
        self.assertEqual(record["workHourOwner"], "artist")
        self.assertEqual(record["hours"], 6.5)
        self.assertEqual(record["workDay"], "2026-08-25 00:00:00")
        self.assertEqual(record["workHourStatus"], "approved")
        self.assertEqual(record["workHourAction"], "create")
        self.assertEqual(record["taskCode"], "TASK0001")
        self.assertEqual(record["process"], "model")
        self.assertEqual(record["context"], "model/retopo")
        self.assertEqual(record["targetTitle"], "Bathroom")
        self.assertEqual(record["targetType"], "demo/asset")
        self.assertEqual(len(scoped_records), 1)
        self.assertEqual(scoped_records[0]["kind"], "work_hour")
        self.assertEqual(scoped_records[0]["taskCode"], "TASK0001")

    def test_task_event_resolves_actor_without_using_assignee_as_author(self):
        _Search.rows = {
            "sthpw/task": [{
                "id": 3,
                "code": "TASK0003",
                "search_type": "demo/asset",
                "search_code": "ASSET001",
                "process": "model",
                "context": "model/review",
                "status": "In Progress",
                "assigned": "artist",
                "login": "",
                "timestamp": "2026-08-25 13:00:00",
                "project_code": "demo",
            }],
            "sthpw/change_timestamp": [{
                "id": 4,
                "search_type": "sthpw/task",
                "search_code": "TASK0003",
                "transaction_code": "TX_TASK_3",
                "project_code": "demo",
            }],
            "sthpw/transaction_log": [{
                "id": 5,
                "code": "TX_TASK_3",
                "login": "listy",
                "timestamp": "2026-08-25 13:00:00",
            }],
            "demo/asset": [{
                "id": 1,
                "code": "ASSET001",
                "name": "Bathroom",
                "pipeline_code": "asset",
            }],
        }
        pyasm = types.ModuleType("pyasm")
        search = types.ModuleType("pyasm.search")
        search.Search = _Search
        search.SearchKey = _SearchKey

        with patch.dict(sys.modules, {
            "pyasm": pyasm,
            "pyasm.search": search,
        }):
            records = tactic_query.query_user_recent_activity(
                project_code="demo", kinds=("task",), limit=25
            )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["taskCode"], "TASK0003")
        self.assertEqual(records[0]["itemTitle"], "model/review")
        self.assertEqual(records[0]["targetTitle"], "Bathroom")
        self.assertEqual(records[0]["actor"], "listy")
        self.assertNotEqual(records[0]["actor"], "artist")
        self.assertFalse(records[0]["serverGenerated"])

    def test_task_is_server_generated_only_when_resolved_transaction_has_no_login(self):
        _Search.rows = {
            "sthpw/task": [{
                "id": 6,
                "code": "TASK0006",
                "search_type": "demo/asset",
                "search_code": "ASSET001",
                "process": "model",
                "assigned": "listy",
                "login": "",
                "timestamp": "2026-08-25 14:00:00",
                "project_code": "demo",
            }],
            "sthpw/change_timestamp": [{
                "id": 7,
                "search_type": "sthpw/task",
                "search_code": "TASK0006",
                "transaction_code": "TX_TASK_6",
                "project_code": "demo",
            }],
            "sthpw/transaction_log": [{
                "id": 8,
                "code": "TX_TASK_6",
                "login": "",
                "timestamp": "2026-08-25 14:00:00",
            }],
            "demo/asset": [{
                "id": 1,
                "code": "ASSET001",
                "name": "Bathroom",
            }],
        }
        pyasm = types.ModuleType("pyasm")
        search = types.ModuleType("pyasm.search")
        search.Search = _Search
        search.SearchKey = _SearchKey

        with patch.dict(sys.modules, {
            "pyasm": pyasm,
            "pyasm.search": search,
        }):
            records = tactic_query.query_user_recent_activity(
                assigned_login="listy", project_code="demo",
                kinds=("task",), limit=25,
            )

        self.assertEqual(records[0]["actor"], "")
        self.assertTrue(records[0]["serverGenerated"])

    def test_task_actor_falls_back_to_latest_sobject_log(self):
        _Search.rows = {
            "sthpw/task": [{
                "id": 12,
                "code": "TASK0012",
                "search_type": "demo/asset",
                "search_code": "ASSET001",
                "process": "model",
                "assigned": "listy",
                "login": "",
                "timestamp": "2026-08-25 15:00:00",
                "project_code": "demo",
            }],
            "sthpw/change_timestamp": [],
            "sthpw/sobject_log": [{
                "id": 13,
                "search_type": "sthpw/task",
                "search_id": 12,
                "login": "listy",
                "timestamp": "2026-08-25 15:00:00",
            }],
            "demo/asset": [{
                "id": 1,
                "code": "ASSET001",
                "name": "Bathroom",
            }],
        }
        pyasm = types.ModuleType("pyasm")
        search = types.ModuleType("pyasm.search")
        search.Search = _Search
        search.SearchKey = _SearchKey

        with patch.dict(sys.modules, {
            "pyasm": pyasm,
            "pyasm.search": search,
        }):
            records = tactic_query.query_user_recent_activity(
                assigned_login="listy", project_code="demo",
                kinds=("task",), limit=25,
            )

        self.assertEqual(records[0]["actor"], "listy")
        self.assertFalse(records[0]["serverGenerated"])

    def test_transaction_audit_is_enriched_and_change_fallback_is_deduplicated(self):
        _Search.rows = {
            "sthpw/transaction_log": [{
                "id": 7,
                "code": "TX0007",
                "login": "artist",
                "timestamp": "2026-08-25 12:00:00",
                "namespace": "demo",
                "transaction": """
                    <transaction>
                      <sobject search_type="demo/asset?project=demo"
                               search_code="ASSET001" action="update">
                        <column name="assigned" from="admin" to="artist"/>
                        <column name="timestamp" from="old" to="new"/>
                      </sobject>
                    </transaction>
                """,
            }],
            "sthpw/sobject_log": [{
                "id": 8,
                "search_type": "demo/asset",
                "search_id": 1,
                "transaction_log_id": 7,
            }],
            "sthpw/change_timestamp": [{
                "id": 9,
                "code": "CHANGE0009",
                "search_type": "demo/asset",
                "search_code": "ASSET001",
                "timestamp": "2026-08-25 12:00:00",
                "changed_on": '{"assigned":"2026-08-25 12:00:00"}',
                "changed_by": '{"assigned":"artist"}',
                "project_code": "demo",
                "transaction_code": "TX0007",
            }],
            "demo/asset": [{
                "id": 1,
                "code": "ASSET001",
                "name": "Bathroom",
                "pipeline_code": "asset",
            }],
        }
        pyasm = types.ModuleType("pyasm")
        search = types.ModuleType("pyasm.search")
        search.Search = _Search
        search.SearchKey = _SearchKey

        with patch.dict(sys.modules, {
            "pyasm": pyasm,
            "pyasm.search": search,
        }):
            records = tactic_query.query_user_recent_activity(
                project_code="demo", kinds=("change",), limit=25
            )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["eventId"], "audit:TX0007:0")
        self.assertEqual(records[0]["targetTitle"], "Bathroom")
        self.assertEqual(records[0]["targetType"], "demo/asset")
        self.assertEqual(records[0]["changes"], [{
            "field": "assigned",
            "before": "admin",
            "after": "artist",
        }])

    def test_instance_insert_names_both_linked_objects_without_connector_code(self):
        _Search.rows = {
            "sthpw/transaction_log": [{
                "id": 17,
                "code": "TX0017",
                "login": "artist",
                "timestamp": "2026-08-25 12:10:00",
                "namespace": "demo",
                "transaction": """
                    <transaction>
                      <sobject search_type="demo/asset_in_scene"
                               search_code="LINK001" action="insert">
                        <column name="asset_code" to="ASSET001"/>
                        <column name="scene_code" to="SCENE001"/>
                      </sobject>
                    </transaction>
                """,
            }, {
                "id": 18,
                "code": "TX0018",
                "login": "artist",
                "timestamp": "2026-08-25 12:11:00",
                "namespace": "demo",
                "transaction": """
                    <transaction>
                      <sobject search_type="demo/texture_in_assets"
                               search_code="TEXTURE_IN_ASSETS00141"
                               action="insert">
                        <column name="texture_code" to="TEXTURE00106"/>
                        <column name="assets_code" to="ASSETS00008"/>
                        <column name="relative_dir"
                                to="demo/texture_in_assets"/>
                      </sobject>
                    </transaction>
                """,
            }],
            "sthpw/sobject_log": [],
            "sthpw/change_timestamp": [],
            "demo/asset": [{
                "id": 21,
                "code": "ASSET001",
                "name": "Baby Shark",
            }],
            "demo/scene": [{
                "id": 22,
                "code": "SCENE001",
                "name": "Episode 79",
            }],
            "demo/texture": [{
                "id": 23,
                "code": "TEXTURE00106",
                "name": "Shark Skin",
            }],
            "demo/assets": [{
                "id": 24,
                "code": "ASSETS00008",
                "name": "Baby Shark",
            }],
        }

        class _Schema:
            @staticmethod
            def get():
                return _Schema()

            @staticmethod
            def get_foreign_keys(instance_type, endpoint_type):
                columns = {
                    ("demo/asset_in_scene", "demo/asset"): "asset_code",
                    ("demo/asset_in_scene", "demo/scene"): "scene_code",
                    (
                        "demo/texture_in_assets", "demo/texture"
                    ): "texture_code",
                    (
                        "demo/texture_in_assets", "demo/assets"
                    ): "assets_code",
                }
                column = columns.get((instance_type, endpoint_type))
                return ("code", column) if column else ()

        pyasm = types.ModuleType("pyasm")
        search = types.ModuleType("pyasm.search")
        search.Search = _Search
        search.SearchKey = _SearchKey
        biz = types.ModuleType("pyasm.biz")
        biz.Schema = _Schema

        with patch.dict(sys.modules, {
            "pyasm": pyasm,
            "pyasm.search": search,
            "pyasm.biz": biz,
        }):
            records = tactic_query.query_user_recent_activity(
                project_code="demo", kinds=("create",), limit=25,
                instance_relations={
                    "demo/asset_in_scene": ["demo/asset", "demo/scene"],
                    "demo/texture_in_assets": [
                        "demo/texture", "demo/assets",
                    ],
                },
            )
            scoped_records = tactic_query.query_user_recent_activity(
                project_code="demo", kinds=("create",), limit=25,
                instance_relations={
                    "demo/asset_in_scene": ["demo/asset", "demo/scene"],
                    "demo/texture_in_assets": [
                        "demo/texture", "demo/assets",
                    ],
                },
                object_scope={
                    "searchType": "demo/asset",
                    "searchCode": "ASSET001",
                },
            )

        self.assertEqual(len(records), 2)
        record = next(
            item for item in records
            if item["itemType"] == "demo/asset"
        )
        self.assertEqual(record["kind"], "create")
        self.assertEqual(record["relationAction"], "link")
        self.assertEqual(record["itemTitle"], "Baby Shark")
        self.assertEqual(record["itemType"], "demo/asset")
        self.assertEqual(record["targetTitle"], "Episode 79")
        self.assertEqual(record["targetType"], "demo/scene")
        self.assertTrue(record["searchKey"])
        self.assertTrue(record["targetSearchKey"])
        self.assertEqual(record["itemCode"], "")
        self.assertEqual(record["detail"], "")
        self.assertEqual(record["changes"], [])
        self.assertNotIn("LINK001", str(record))

        texture_record = next(
            item for item in records
            if item["itemType"] == "demo/texture"
        )
        self.assertEqual(texture_record["relationAction"], "link")
        self.assertEqual(texture_record["itemTitle"], "Shark Skin")
        self.assertEqual(texture_record["targetTitle"], "Baby Shark")
        self.assertEqual(texture_record["targetType"], "demo/assets")
        self.assertEqual(texture_record["changes"], [])
        self.assertNotIn("TEXTURE_IN_ASSETS00141", str(texture_record))
        self.assertNotIn("relative_dir", str(texture_record))
        self.assertEqual(len(scoped_records), 1)
        self.assertEqual(scoped_records[0]["itemTitle"], "Episode 79")
        self.assertEqual(scoped_records[0]["itemType"], "demo/scene")
        self.assertEqual(scoped_records[0]["targetTitle"], "Baby Shark")
        self.assertEqual(scoped_records[0]["targetType"], "demo/asset")

    def test_change_timestamp_fallback_decodes_field_maps(self):
        _Search.rows = {
            "sthpw/change_timestamp": [{
                "id": 9,
                "code": "CHANGE0009",
                "search_type": "demo/asset",
                "search_code": "ASSET001",
                "timestamp": "2026-08-25 11:30:00",
                "changed_on": (
                    '{"description":"2026-08-25 11:20:00",'
                    '"name":"2026-08-25 11:30:00"}'
                ),
                "changed_by": (
                    '{"description":"admin","name":"artist"}'
                ),
                "project_code": "demo",
                "transaction_code": "TX_MISSING",
            }],
            "demo/asset": [{
                "id": 1,
                "code": "ASSET001",
                "name": "Bathroom",
                "pipeline_code": "asset",
            }],
        }
        pyasm = types.ModuleType("pyasm")
        search = types.ModuleType("pyasm.search")
        search.Search = _Search
        search.SearchKey = _SearchKey

        with patch.dict(sys.modules, {
            "pyasm": pyasm,
            "pyasm.search": search,
        }):
            records = tactic_query.query_user_recent_activity(
                login="artist", project_code="demo",
                kinds=("change",), limit=25,
            )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["actor"], "artist")
        self.assertEqual(records[0]["timestamp"], "2026-08-25 11:30:00")
        self.assertEqual(records[0]["targetTitle"], "Bathroom")
        self.assertEqual(records[0]["changes"], [
            {
                "field": "description",
                "before": "",
                "after": "",
                "valuesKnown": False,
            },
            {
                "field": "name",
                "before": "",
                "after": "",
                "valuesKnown": False,
            },
        ])

    def test_compressed_delete_uses_native_xml_and_deleted_name(self):
        _Search.rows = {
            "sthpw/transaction_log": [{
                "id": 10,
                "code": "TX0010",
                "login": "artist",
                "timestamp": "2026-08-25 10:00:00",
                "namespace": "demo",
                "transaction": "zlib:compressed-payload",
                "_expanded_transaction": """
                    <transaction>
                      <sobject search_type="demo/asset"
                               search_code="ASSET002" action="delete">
                        <column name="description" from="Old room"/>
                        <column name="name" from="Deleted Bathroom"/>
                      </sobject>
                    </transaction>
                """,
            }],
            # TACTIC does not index the deleted object. Another mutation in
            # the same transaction may still leave unrelated index rows.
            "sthpw/sobject_log": [{
                "id": 13,
                "search_type": "demo/shot",
                "transaction_log_id": 10,
                "action": "update",
            }],
            "sthpw/change_timestamp": [],
            "demo/asset": [],
        }
        pyasm = types.ModuleType("pyasm")
        search = types.ModuleType("pyasm.search")
        search.Search = _Search
        search.SearchKey = _SearchKey

        with patch.dict(sys.modules, {
            "pyasm": pyasm,
            "pyasm.search": search,
        }):
            records = tactic_query.query_user_recent_activity(
                project_code="demo", kinds=("delete",), limit=25
            )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["targetTitle"], "Deleted Bathroom")
        self.assertEqual(records[0]["kind"], "delete")
        self.assertFalse(records[0]["targetSearchKey"])

    def test_calendar_counts_include_project_object_audit_events(self):
        _Search.rows = {
            "sthpw/transaction_log": [{
                "id": 11,
                "code": "TX0011",
                "login": "artist",
                "timestamp": "2026-08-24 10:00:00",
                "namespace": "demo",
                "transaction": """
                    <transaction>
                      <sobject search_type="demo/asset"
                               search_code="ASSET003" action="insert">
                        <column name="name" to="Kitchen"/>
                      </sobject>
                    </transaction>
                """,
            }],
            "sthpw/sobject_log": [{
                "id": 12,
                "search_type": "demo/asset",
                "transaction_log_id": 11,
            }],
            "sthpw/change_timestamp": [],
            "demo/asset": [{
                "id": 3,
                "code": "ASSET003",
                "name": "Kitchen",
            }],
        }
        pyasm = types.ModuleType("pyasm")
        search = types.ModuleType("pyasm.search")
        search.Search = _Search
        search.SearchKey = _SearchKey

        with patch.dict(sys.modules, {
            "pyasm": pyasm,
            "pyasm.search": search,
        }):
            payload = tactic_query.query_user_recent_activity(
                project_code="demo", kinds=("create",), limit=25,
                include_day_counts=True,
            )

        self.assertEqual(payload["dayCounts"], [{
            "dateKey": "2026-08-24",
            "count": 1,
        }])
        self.assertEqual(payload["records"][0]["targetTitle"], "Kitchen")

    def test_counts_only_does_not_build_activity_page_or_parent_enrichment(self):
        _Search.instances = []
        _Search.rows = {
            "sthpw/snapshot": [{
                "id": 1,
                "code": "SNAPSHOT001",
                "timestamp": "2026-08-24 10:00:00",
                "project_code": "demo",
                "search_type": "demo/asset",
                "search_code": "ASSET001",
            }],
        }
        pyasm = types.ModuleType("pyasm")
        search = types.ModuleType("pyasm.search")
        search.Search = _Search
        search.SearchKey = _SearchKey

        with patch.dict(sys.modules, {
            "pyasm": pyasm,
            "pyasm.search": search,
        }):
            payload = tactic_query.query_user_recent_activity(
                project_code="demo", kinds=("publication",),
                include_day_counts=True, counts_only=True,
            )

        self.assertEqual(payload["records"], [])
        self.assertEqual(payload["dayCounts"], [{
            "dateKey": "2026-08-24", "count": 1,
        }])
        self.assertEqual(
            [item.search_type for item in _Search.instances],
            ["sthpw/snapshot"],
        )
        self.assertIsNone(_Search.instances[0].limit)

    def test_cached_counts_query_starts_at_last_cached_day(self):
        _Search.instances = []
        _Search.rows = {"sthpw/snapshot": []}
        pyasm = types.ModuleType("pyasm")
        search = types.ModuleType("pyasm.search")
        search.Search = _Search
        search.SearchKey = _SearchKey

        with patch.dict(sys.modules, {
            "pyasm": pyasm,
            "pyasm.search": search,
        }):
            payload = tactic_query.query_user_recent_activity(
                project_code="demo", kinds=("publication",),
                counts_only=True, counts_from_day="2026-08-24",
            )

        self.assertEqual(payload["countsFromDay"], "2026-08-24")
        timestamp_filters = [
            (args, kwargs)
            for args, kwargs in _Search.instances[0].filters
            if args and args[0] == "timestamp"
        ]
        self.assertEqual(timestamp_filters, [(
            ("timestamp", "2026-08-24 00:00:00"), {"op": ">="},
        )])


if __name__ == "__main__":
    unittest.main()
