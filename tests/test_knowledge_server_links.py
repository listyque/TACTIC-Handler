from __future__ import annotations

import json
import sys
from types import ModuleType
import unittest
from unittest.mock import patch

from thlib.ui.knowledge_api import knowledge_request


class _FakeItem:
    def __init__(self, environment, item_id: int):
        self.environment = environment
        self.retired = False
        self.values = {
            "id": item_id,
            "code": f"KB{item_id:04d}",
            "name": "",
            "description": "",
            "kind": "article",
            "parent_code": "",
            "content": "",
            "content_text": "",
            "sort_order": 0,
            "updated_by": "",
            "linked_skeys": "[]",
            "login": "",
            "s_status": "",
            "timestamp": "",
            "last_update": "",
        }

    def get_value(self, name, no_exception=False):
        return self.values.get(name)

    def get_id(self):
        return self.values["id"]

    def set_value(self, name, value):
        self.values[name] = value

    def commit(self):
        self.environment.commit_count += 1
        stamp = (
            "2026-08-30 10:00:00"
            if self.environment.commit_count == 1
            else "2026-08-31 12:00:00"
        )
        if not self.values["timestamp"]:
            self.values["timestamp"] = stamp
        # Project tables on the real TACTIC server do not necessarily expose
        # or maintain last_update.  The native object log is the authoritative
        # modification timestamp in that case.
        self.values["last_update"] = None
        self.environment.object_logs.insert(0, _FakeAuditItem({
            "id": 100 + self.environment.commit_count,
            "search_type": (
                self.environment.knowledge_search_type + "?project=demo"
            ),
            "search_id": self.get_id(),
            "transaction_log_id": 900 + self.environment.commit_count,
            "timestamp": stamp,
        }))

    def retire(self):
        self.retired = True

    def get_connections(self, context=None):
        return []


class _FakeFile:
    def __init__(self, name="guide.png", file_type="main"):
        self.values = {
            "file_name": name,
            "type": file_type,
            "base_type": "file",
            "relative_dir": "demo/knowledge",
            "st_size": 128,
            "metadata": {},
        }

    def get_data(self):
        return dict(self.values)


class _FakeSnapshot:
    def __init__(self, code="SNAP0001"):
        self.retired = False
        self.files = [_FakeFile()]
        self.values = {
            "id": 101,
            "code": code,
            "context": "attachment/knowledge/guide",
            "version": 1,
            "is_latest": True,
            "timestamp": "2026-08-31 12:00:00",
            "snapshot": "<snapshot/>",
        }

    def get_code(self): return self.values["code"]
    def get_id(self): return self.values["id"]
    def get_value(self, name, no_exception=False): return self.values.get(name)
    def get_version(self): return self.values["version"]
    def is_latest(self): return self.values["is_latest"]
    def get_data(self): return dict(self.values)
    def get_base_search_type(self): return "sthpw/snapshot"
    def retire(self): self.retired = True


class _FakeAuditItem:
    def __init__(self, values):
        self.values = dict(values)

    def get_value(self, name, no_exception=False):
        return self.values.get(name)

    def get_id(self):
        return self.values.get("id")

    def get_data(self):
        return dict(self.values)


class _FakeTacticEnvironment:
    project_code = "demo"
    knowledge_search_type = "demo/th_knowledge_article"
    knowledge_columns = {
        "id", "code", "name", "description", "kind", "parent_code",
        "content", "content_text", "sort_order", "updated_by",
        "linked_skeys", "login", "timestamp", "last_update",
        "s_status",
    }

    def __init__(self, *, registered: bool = True):
        self.registered = registered
        self.undefined_message_schema = False
        self.items: list[_FakeItem] = []
        self.snapshots: list[_FakeSnapshot] = []
        self.article_query_count = 0
        self.commit_count = 0
        self.current_login = "admin"
        self.object_logs: list[_FakeAuditItem] = []
        self.transaction_logs: list[_FakeAuditItem] = []
        self.modules = self._make_modules()

    def create_item(self):
        item = _FakeItem(self, len(self.items) + 1)
        self.items.append(item)
        return item

    def request(self, action: str, **kwargs):
        with patch.dict(sys.modules, self.modules):
            return json.loads(knowledge_request(
                action,
                self.project_code,
                **kwargs,
            ))

    def _make_modules(self):
        environment = self

        class Search:
            def __init__(self, search_type):
                self.search_type = search_type
                self.filters = []

            def add_filter(self, name, value, op=None):
                self.filters.append((name, value, op))

            def add_filters(self, name, values):
                self.filters.append((name, list(values), "in"))

            def add_order_by(self, _name, direction="asc"):
                return None

            def set_limit(self, _value):
                return None

            def add_column(self, _name):
                return None

            def add_op(self, _name):
                return None

            def _matches(self, item):
                for name, value, operation in self.filters:
                    candidate = item.get_value(name)
                    if operation == "like":
                        needle = str(value).strip("%").casefold()
                        if needle not in str(candidate or "").casefold():
                            return False
                    elif operation == "in":
                        if candidate not in value:
                            return False
                    elif candidate != value:
                        return False
                return True

            def get_sobject(self):
                if self.search_type == "sthpw/search_object":
                    return object() if environment.registered else None
                if self.search_type == environment.knowledge_search_type:
                    environment.article_query_count += 1
                    return next((
                        item for item in environment.items
                        if not item.retired and self._matches(item)
                    ), None)
                return None

            def get_sobjects(self):
                if self.search_type == "sthpw/login_in_group":
                    return []
                if self.search_type == environment.knowledge_search_type:
                    environment.article_query_count += 1
                    return [
                        item for item in environment.items
                        if not item.retired and self._matches(item)
                    ]
                if self.search_type == "sthpw/sobject_log":
                    return [
                        item for item in environment.object_logs
                        if self._matches(item)
                    ]
                if self.search_type == "sthpw/transaction_log":
                    return [
                        item for item in environment.transaction_logs
                        if self._matches(item)
                    ]
                return []

        class SearchType:
            @staticmethod
            def get_columns(search_type):
                if search_type in {"sthpw/message", "sthpw/message_log"}:
                    if environment.undefined_message_schema:
                        raise AttributeError(
                            "'Undefined' object has no attribute 'get_columns'"
                        )
                    return ["metadata"]
                if (
                    search_type == environment.knowledge_search_type
                    and environment.registered
                ):
                    return list(environment.knowledge_columns)
                return []

            @staticmethod
            def create(search_type):
                if search_type != environment.knowledge_search_type:
                    raise AssertionError("Unexpected fake search type")
                return environment.create_item()

            @staticmethod
            def clear_column_cache(_search_type):
                return None

        class SearchKey:
            @staticmethod
            def get_by_sobject(item, use_id=False):
                if isinstance(item, _FakeSnapshot):
                    return f"sthpw/snapshot?code={item.get_code()}"
                return (
                    f"{environment.knowledge_search_type}"
                    f"?id={item.get_id()}"
                )

            @staticmethod
            def get_by_search_key(value):
                value = str(value or "")
                return next((
                    snapshot for snapshot in environment.snapshots
                    if snapshot.get_code() in value and not snapshot.retired
                ), None)

        class Snapshot:
            @staticmethod
            def get_by_sobjects(_items):
                return [
                    snapshot for snapshot in environment.snapshots
                    if not snapshot.retired
                ]

            @staticmethod
            def get_files_dict_by_snapshots(_snapshots):
                return {
                    snapshot.get_code(): list(snapshot.files)
                    for snapshot in _snapshots
                }

        class Project:
            @staticmethod
            def get_project_code():
                return environment.project_code

        class Security:
            @staticmethod
            def is_admin():
                return True

        class Environment:
            @staticmethod
            def get_security():
                return Security()

        class Api:
            @staticmethod
            def get_login():
                return environment.current_login

        class TacticServerStub:
            @staticmethod
            def get(protocol="local"):
                return Api()

        modules = {
            "pyasm": ModuleType("pyasm"),
            "pyasm.biz": ModuleType("pyasm.biz"),
            "pyasm.common": ModuleType("pyasm.common"),
            "pyasm.search": ModuleType("pyasm.search"),
            "tactic_client_lib": ModuleType("tactic_client_lib"),
        }
        modules["pyasm.biz"].Project = Project
        modules["pyasm.biz"].Snapshot = Snapshot
        modules["pyasm.common"].Environment = Environment
        modules["pyasm.search"].Search = Search
        modules["pyasm.search"].SearchKey = SearchKey
        modules["pyasm.search"].SearchType = SearchType
        modules["tactic_client_lib"].TacticServerStub = TacticServerStub
        return modules


class KnowledgeServerLinkTests(unittest.TestCase):
    @staticmethod
    def _article(title, linked_search_keys=(), *, sort_order=0):
        return {
            "title": title,
            "description": f"Summary for {title}",
            "kind": "article",
            "parentCode": "",
            "contentMarkdown": title,
            "contentText": title,
            "linkedSearchKeys": list(linked_search_keys),
            "sortOrder": sort_order,
        }

    def test_uninitialized_store_returns_empty_index_without_article_query(self):
        environment = _FakeTacticEnvironment(registered=False)

        result = environment.request("link_index")

        self.assertFalse(result["initialized"])
        self.assertEqual(result["links"], [])
        self.assertEqual(environment.article_query_count, 0)

    def test_undefined_message_schema_does_not_break_knowledge_catalog(self):
        environment = _FakeTacticEnvironment()
        environment.undefined_message_schema = True

        result = environment.request("list")

        self.assertTrue(result["initialized"])
        self.assertFalse(result["messagesInitialized"])
        self.assertEqual(result["catalog"], [])

    def test_save_normalizes_deduplicates_and_load_round_trips_links(self):
        environment = _FakeTacticEnvironment()
        result = environment.request(
            "save",
            document=self._article("Hero", [
                " demo/assets?code=HERO ",
                "skey://demo/assets?code=HERO",
                "skey://demo/shots?code=SHOT_010",
            ]),
        )

        expected = [
            "skey://demo/assets?code=HERO",
            "skey://demo/shots?code=SHOT_010",
        ]
        self.assertEqual(result["document"]["linkedSearchKeys"], expected)
        self.assertEqual(
            environment.items[0].values["linked_skeys"],
            json.dumps(expected, separators=(",", ":")),
        )

        loaded = environment.request("load", identity=result["identity"])

        self.assertEqual(loaded["document"]["linkedSearchKeys"], expected)
        self.assertEqual(loaded["links"], [{
            "identity": result["identity"],
            "title": "Hero",
            "linkedSearchKeys": expected,
            "sortOrder": 0,
        }])

    def test_reserved_article_is_owner_only_and_publish_removes_draft_status(self):
        environment = _FakeTacticEnvironment()

        reserved = environment.request(
            "reserve", document=self._article("Work in progress")
        )

        self.assertTrue(reserved["document"]["draft"])
        self.assertEqual(environment.items[0].values["s_status"], "draft")
        self.assertEqual(reserved["links"], [])
        self.assertTrue(reserved["catalog"][0]["draft"])

        environment.current_login = "another-supervisor"
        hidden = environment.request("list")
        self.assertEqual(hidden["catalog"], [])

        environment.current_login = "admin"
        updated_document = dict(
            reserved["document"],
            title="Work in progress, saved",
        )
        saved_draft = environment.request(
            "save_draft",
            identity=reserved["identity"],
            expected_revision=reserved["revision"],
            document=updated_document,
        )

        self.assertTrue(saved_draft["document"]["draft"])
        self.assertEqual(
            saved_draft["document"]["title"],
            "Work in progress, saved",
        )
        self.assertEqual(environment.items[0].values["s_status"], "draft")
        self.assertEqual(saved_draft["links"], [])

        published = environment.request(
            "save",
            identity=saved_draft["identity"],
            expected_revision=saved_draft["revision"],
            document=saved_draft["document"],
        )

        self.assertFalse(published["document"]["draft"])
        self.assertEqual(environment.items[0].values["s_status"], "")
        self.assertEqual(len(published["links"]), 1)

    def test_article_metadata_preserves_creator_and_tracks_last_editor(self):
        environment = _FakeTacticEnvironment()
        environment.current_login = "creator"

        created = environment.request(
            "save", document=self._article("Authored guide")
        )

        self.assertEqual(created["articleMetadata"], {
            "author": "creator",
            "createdAt": "2026-08-30 10:00:00",
            "updatedBy": "creator",
            "updatedAt": "2026-08-30 10:00:00",
        })

        environment.current_login = "editor"
        updated_document = dict(created["document"], title="Edited guide")
        updated = environment.request(
            "save",
            identity=created["identity"],
            expected_revision=created["revision"],
            document=updated_document,
        )

        self.assertEqual(environment.items[0].values["login"], "creator")
        self.assertEqual(updated["articleMetadata"], {
            "author": "creator",
            "createdAt": "2026-08-30 10:00:00",
            "updatedBy": "editor",
            "updatedAt": "2026-08-31 12:00:00",
        })

    def test_project_qualified_log_reconstructs_previous_article_revisions(self):
        environment = _FakeTacticEnvironment()
        environment.current_login = "creator"
        created = environment.request(
            "save", document=self._article("First title")
        )
        environment.current_login = "editor"
        updated = environment.request(
            "save",
            identity=created["identity"],
            expected_revision=created["revision"],
            document=dict(
                created["document"],
                title="Current title",
                contentMarkdown="Current body",
                contentText="Current body",
            ),
        )
        item = environment.items[0]
        environment.object_logs = [
            _FakeAuditItem({
                "id": 12,
                "search_type": (
                    environment.knowledge_search_type + "?project=demo"
                ),
                "search_id": item.get_id(),
                "transaction_log_id": 102,
                "timestamp": "2026-08-31 12:00:00",
            }),
            _FakeAuditItem({
                "id": 11,
                "search_type": (
                    environment.knowledge_search_type + "?project=demo"
                ),
                "search_id": item.get_id(),
                "transaction_log_id": 101,
                "timestamp": "2026-08-30 10:00:00",
            }),
        ]
        environment.transaction_logs = [
            _FakeAuditItem({
                "id": 102,
                "code": "TX_UPDATE",
                "login": "editor",
                "timestamp": "2026-08-31 12:00:00",
                "transaction": """
                    <transaction>
                      <sobject search_type="demo/th_knowledge_article"
                               search_code="KB0001" action="update">
                        <column name="name" from="First title"
                                to="Current title"/>
                        <column name="content"
                                from="First title"
                                to="Current body"/>
                        <column name="content_text" from="First title"
                                to="Current body"/>
                        <column name="updated_by" from="creator"
                                to="editor"/>
                      </sobject>
                    </transaction>
                """,
            }),
            _FakeAuditItem({
                "id": 101,
                "code": "TX_CREATE",
                "login": "creator",
                "timestamp": "2026-08-30 10:00:00",
                "transaction": """
                    <transaction>
                      <sobject search_type="demo/th_knowledge_article"
                               search_code="KB0001" action="insert">
                        <column name="name" from="" to="First title"/>
                        <column name="content" from=""
                                to="First title"/>
                        <column name="content_text" from=""
                                to="First title"/>
                      </sobject>
                    </transaction>
                """,
            }),
        ]

        history = environment.request(
            "history", identity=updated["identity"]
        )

        self.assertEqual(
            [entry["revisionId"] for entry in history["history"]],
            ["TX_UPDATE", "TX_CREATE"],
        )
        self.assertTrue(history["history"][0]["current"])
        self.assertFalse(history["history"][1]["current"])
        self.assertNotIn("document", history["history"][1])

        previous = environment.request(
            "history_revision",
            identity=updated["identity"],
            history_revision="TX_CREATE",
        )["historyRevision"]

        self.assertEqual(previous["document"]["title"], "First title")
        self.assertEqual(
            previous["document"]["contentMarkdown"],
            "First title",
        )
        self.assertEqual(previous["actor"], "creator")
        self.assertEqual(previous["articleMetadata"]["author"], "creator")

    def test_link_index_is_deterministic_and_excludes_section_links(self):
        environment = _FakeTacticEnvironment()
        later = environment.request(
            "save",
            document=self._article(
                "Zulu", ["demo/assets?code=ZULU"], sort_order=2,
            ),
        )
        section = environment.request("save", document={
            "title": "Characters",
            "kind": "section",
            "linkedSearchKeys": ["demo/assets?code=IGNORED"],
            "sortOrder": 0,
        })
        earlier = environment.request(
            "save",
            document=self._article(
                "Alpha", ["demo/assets?code=ALPHA"], sort_order=1,
            ),
        )

        first = environment.request("link_index")
        second = environment.request("link_index")

        self.assertEqual(first, second)
        self.assertEqual(
            [entry["identity"] for entry in first["links"]],
            [earlier["identity"], later["identity"]],
        )
        self.assertEqual(section["document"]["linkedSearchKeys"], [])
        section_item = next(
            item for item in environment.items
            if str(item.get_id()) == section["identity"]
        )
        self.assertEqual(section_item.values["linked_skeys"], "[]")

    def test_link_change_invalidates_an_earlier_revision(self):
        environment = _FakeTacticEnvironment()
        original_document = self._article(
            "Hero", ["demo/assets?code=HERO"],
        )
        saved = environment.request("save", document=original_document)
        old_revision = saved["revision"]
        environment.items[0].values["linked_skeys"] = json.dumps([
            "skey://demo/assets?code=VILLAIN",
        ])

        with self.assertRaisesRegex(ValueError, "changed on the server"):
            environment.request(
                "save",
                identity=saved["identity"],
                expected_revision=old_revision,
                document=original_document,
            )

    def test_attachment_list_and_delete_are_scoped_to_the_article(self):
        environment = _FakeTacticEnvironment()
        saved = environment.request(
            "save", document=self._article("Hero guide")
        )
        snapshot = _FakeSnapshot()
        environment.snapshots.append(snapshot)

        listed = environment.request(
            "attachments", identity=saved["identity"]
        )

        self.assertEqual(len(listed["attachmentSnapshots"]), 1)
        self.assertEqual(
            listed["attachmentSnapshots"][0]["__files__"][0]["file_name"],
            "guide.png",
        )

        deleted = environment.request(
            "delete_attachment",
            identity=saved["identity"],
            attachment_key="skey://sthpw/snapshot?code=SNAP0001",
        )

        self.assertTrue(snapshot.retired)
        self.assertEqual(deleted["attachmentSnapshots"], [])

    def test_organize_reparents_and_orders_existing_entries(self):
        environment = _FakeTacticEnvironment()
        section = environment.request("save", document={
            "title": "Characters",
            "kind": "section",
            "parentCode": "",
            "sortOrder": 10,
        })
        hero = environment.request(
            "save", document=self._article("Hero", sort_order=20)
        )
        villain = environment.request(
            "save", document=self._article("Villain", sort_order=30)
        )

        result = environment.request("organize", organization=[{
            "identity": hero["identity"],
            "parentCode": section["identity"],
            "sortOrder": 10,
        }, {
            "identity": villain["identity"],
            "parentCode": section["identity"],
            "sortOrder": 20,
        }])

        self.assertTrue(result["organizationSaved"])
        self.assertEqual(environment.items[1].values["parent_code"], "1")
        self.assertEqual(environment.items[1].values["sort_order"], 10)
        self.assertEqual(environment.items[2].values["parent_code"], "1")
        self.assertEqual(environment.items[2].values["sort_order"], 20)

    def test_organize_rejects_a_section_cycle_before_committing(self):
        environment = _FakeTacticEnvironment()
        parent = environment.request("save", document={
            "title": "Characters",
            "kind": "section",
            "parentCode": "",
            "sortOrder": 10,
        })
        child = environment.request("save", document={
            "title": "Heroes",
            "kind": "section",
            "parentCode": parent["identity"],
            "sortOrder": 10,
        })

        with self.assertRaisesRegex(ValueError, "inside its child"):
            environment.request("organize", organization=[{
                "identity": parent["identity"],
                "parentCode": child["identity"],
                "sortOrder": 10,
            }])

        self.assertEqual(environment.items[0].values["parent_code"], "")
        self.assertEqual(environment.items[1].values["parent_code"], "1")


if __name__ == "__main__":
    unittest.main()
