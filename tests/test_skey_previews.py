from __future__ import annotations

import unittest
from unittest.mock import patch

from thlib.ui.skey_previews import (
    SearchKeyPreviewResolver,
    display_html_without_skeys,
    extract_skeys,
)


class SearchKeyPreviewTests(unittest.TestCase):
    def test_snapshot_activity_opens_exact_snapshot_in_workspace(self):
        class DockModel:
            def __init__(self):
                self.panels = []

            def show_panel(self, panel):
                self.panels.append(panel)

        class Application:
            def __init__(self):
                self.keys = []
                self.dock_model = DockModel()

            def open_search_key(self, search_key):
                self.keys.append(search_key)

        snapshot_key = "skey://sthpw/snapshot?code=SNAP001"
        resolver = SearchKeyPreviewResolver.__new__(SearchKeyPreviewResolver)
        resolver._application = Application()
        resolver._communication = None
        resolver._cache = {}

        resolver.open_in_context(
            snapshot_key,
            "skey://demo/asset?project=demo&code=ASSET001",
            "render",
        )

        self.assertEqual(resolver._application.keys, [snapshot_key])
        self.assertEqual(resolver._application.dock_model.panels, ["snapshot"])

    def test_note_activity_opens_parent_in_explicit_process(self):
        class DockModel:
            def __init__(self):
                self.panels = []

            def show_panel(self, panel):
                self.panels.append(panel)

        class Application:
            def __init__(self):
                self.calls = []
                self.dock_model = DockModel()

            def open_search_key_in_process(self, search_key, process):
                self.calls.append((search_key, process))

        class Communication:
            def __init__(self):
                self.focused = []
                self.task_contexts = []

            def activate_task_context(self, task_code, parent_key, process):
                self.task_contexts.append((task_code, parent_key, process))

            def show_note(self, search_key):
                self.focused.append(search_key)

        note_key = "skey://sthpw/note?code=NOTE001"
        parent_key = "skey://demo/asset?project=demo&code=ASSET001"
        resolver = SearchKeyPreviewResolver.__new__(SearchKeyPreviewResolver)
        resolver._application = Application()
        resolver._communication = Communication()
        resolver._cache = {}

        resolver.open_in_context(
            note_key, parent_key, "model", "TASK001"
        )

        self.assertEqual(
            resolver._application.calls, [(parent_key, "model")]
        )
        self.assertEqual(resolver._application.dock_model.panels, ["notes"])
        self.assertEqual(resolver._communication.focused, [note_key])
        self.assertEqual(
            resolver._communication.task_contexts,
            [("TASK001", parent_key, "model")],
        )

    def test_extracts_unique_keys_without_sentence_punctuation(self):
        snapshot = "skey://sthpw/snapshot?code=SNAP001"
        task = "skey://sthpw/task?code=TASK001"
        self.assertEqual(
            extract_skeys("{}; {} and {}.".format(snapshot, task, snapshot)),
            [snapshot, task],
        )

    def test_display_html_hides_skey_but_keeps_web_link(self):
        value = (
            "Review skey://sthpw/file?code=FILE001.\n"
            "https://example.test/details"
        )
        rendered = display_html_without_skeys(value)
        self.assertNotIn("skey://", rendered)
        self.assertIn("Review .<br>", rendered)
        self.assertIn('href="https://example.test/details"', rendered)

    def test_display_html_keeps_saved_search_link_clickable(self):
        value = (
            "tactic-search://open?project=demo"
            "&search_type=demo%2Fasset&view=link_search%3Apublished"
        )

        rendered = display_html_without_skeys(value)

        escaped = value.replace("&", "&amp;")
        self.assertIn('href="{}"'.format(escaped), rendered)
        self.assertIn(">{}</a>".format(escaped), rendered)

    def test_display_html_keeps_ftp_link_clickable(self):
        rendered = display_html_without_skeys(
            "ftp://files.example.test/reference.mov"
        )
        self.assertIn(
            'href="ftp://files.example.test/reference.mov"', rendered
        )

    def test_knowledge_search_key_opens_native_knowledge_dock(self):
        opened = []

        class Knowledge:
            def open_search_key(self, value):
                opened.append(value)

        key = "skey://demo/th_knowledge_article?code=DOC0001"
        resolver = SearchKeyPreviewResolver.__new__(SearchKeyPreviewResolver)
        resolver._knowledge = Knowledge()
        resolver._cache = {}
        resolver._application = None
        resolver._messages = None
        resolver._users = None
        resolver._communication = None

        resolver.open(key)

        self.assertEqual(opened, [key])
        self.assertEqual(
            SearchKeyPreviewResolver._guess_kind(key), "knowledge"
        )

    def test_knowledge_preview_uses_article_content_not_technical_type(self):
        class SObject:
            @staticmethod
            def get_info():
                return {
                    "code": "DOC0001",
                    "name": "Lighting guide",
                    "description": "How lighting reviews are organized",
                    "kind": "article",
                    "content_text": "Prepare references before the review.",
                    "parent_code": "SEC0001",
                    "project_code": "demo",
                }

            @staticmethod
            def get_title():
                return "Lighting guide"

            @staticmethod
            def get_stype():
                return None

        key = "skey://demo/th_knowledge_article?code=DOC0001"
        parsed = SearchKeyPreviewResolver._direct_key(key)
        resolver = SearchKeyPreviewResolver.__new__(
            SearchKeyPreviewResolver
        )

        descriptor = resolver._describe(key, parsed, SObject())

        self.assertEqual(descriptor["kind"], "knowledge")
        self.assertEqual(descriptor["articleKind"], "article")
        self.assertEqual(descriptor["title"], "Lighting guide")
        self.assertEqual(
            descriptor["description"],
            "How lighting reviews are organized",
        )
        self.assertEqual(
            descriptor["excerpt"],
            "Prepare references before the review.",
        )
        self.assertEqual(descriptor["parentCode"], "SEC0001")
        self.assertEqual(descriptor["detail"], "")
        self.assertEqual(descriptor["subtitle"], "")

    def test_all_supported_builtin_types_have_distinct_kinds(self):
        expected = {
            "task": "task",
            "snapshot": "snapshot",
            "file": "file",
            "note": "note",
            "message_log": "message",
            "login": "user",
            "project": "project",
        }
        for search_type, kind in expected.items():
            with self.subTest(search_type=search_type):
                self.assertEqual(
                    SearchKeyPreviewResolver._guess_kind(
                        "skey://sthpw/{}?code=ITEM001".format(search_type)
                    ),
                    kind,
                )

    def test_parent_key_preserves_project(self):
        self.assertEqual(
            SearchKeyPreviewResolver._parent_key({
                "search_type": "show/asset?project=demo",
                "search_code": "ASSET001",
                "project_code": "demo",
            }),
            "skey://show/asset?project=demo&code=ASSET001",
        )

    def test_direct_key_reads_deprecated_id_links(self):
        parsed = SearchKeyPreviewResolver._direct_key(
            "skey://sthpw/message_log?id=145"
        )
        self.assertEqual(parsed["identifier_field"], "id")
        self.assertEqual(parsed["identifier"], "145")
        self.assertEqual(parsed["item_code"], "145")

    def test_non_image_snapshot_file_is_not_used_as_preview(self):
        class File:
            def get_icon_preview(self):
                return None

            def get_filename_with_ext(self):
                return "archive.zip"

        class Snapshot:
            def get_files_objects(self, group_by=None):
                return {"main": [File()]}

        self.assertIsNone(
            SearchKeyPreviewResolver._preview_file(Snapshot())
        )

    def test_snapshot_preview_matches_workspace_snapshot_selector(self):
        class File:
            def __init__(self, name):
                self.name = name

            def get_icon_preview(self):
                return self

            def get_filename_with_ext(self):
                return self.name

        main_file = File("published.png")

        class Snapshot:
            def get_files_objects(self, group_by=None):
                return {
                    "main": [main_file],
                    "unrelated": [File("other.png")],
                }

        self.assertIs(
            SearchKeyPreviewResolver._preview_file(Snapshot()),
            main_file,
        )

    def test_snapshot_display_uses_published_file_values(self):
        class File:
            def get_type(self):
                return "main"

            def get_meta_file_object(self):
                return None

            def get_filename_with_ext(self):
                return "scene.zip"

            def get_file_size(self):
                return 4 * 1024 * 1024

            def get_ext(self):
                return "zip"

            def is_exists(self):
                return True

            def get_metadata(self):
                return {}

            def get_icon_preview(self):
                return None

        class Snapshot:
            def get_snapshot(self):
                return {
                    "code": "SNAP001", "context": "publish",
                    "description": "Drag-Drop Checkin", "version": 3,
                    "revision": 1, "login": "artist",
                    "timestamp": "2026-08-03 12:30:00.123",
                    "repo": "base", "is_latest": True,
                }

            def get_files_objects(self, group_by=None):
                grouped = {"main": [File()]}
                return grouped if group_by else [File()]

            def is_latest(self):
                return True

            def is_versionless(self):
                return False

        record = SearchKeyPreviewResolver._snapshot_display(Snapshot())
        self.assertEqual(record["title"], "scene.zip")
        self.assertEqual(record["fileSize"], "4.0 MB")
        self.assertEqual(record["version"], "v003")
        self.assertEqual(record["revision"], "r001")
        self.assertEqual(record["description"], "Drag-Drop Checkin")
        self.assertEqual(record["context"], "publish")
        self.assertTrue(record["isLatest"])

    def test_sobject_preview_uses_workspace_item_process_order(self):
        class File:
            def __init__(self, name):
                self.name = name

            def get_icon_preview(self):
                return self

            def get_filename_with_ext(self):
                return self.name

        class Snapshot:
            def __init__(self, file_object):
                self.file_object = file_object

            def get_files_objects(self, group_by=None):
                return {"icon": [self.file_object]}

        class Context:
            def __init__(self, snapshot):
                self.snapshot = snapshot

            def get_versionless(self):
                return {"current": self.snapshot}

            def get_versions(self):
                return {}

        class Process:
            def __init__(self, snapshot):
                self.context = Context(snapshot)

            def get_contexts(self):
                return {"main": self.context}

        random_file = File("random.png")
        icon_file = File("official.png")

        class SObject:
            def get_all_processes(self):
                return {
                    "animation": Process(Snapshot(random_file)),
                    "icon": Process(Snapshot(icon_file)),
                }

        self.assertIs(
            SearchKeyPreviewResolver._sobject_preview_file(SObject()),
            icon_file,
        )

    def test_note_preview_contains_body_links_and_attachments(self):
        linked = "skey://sthpw/task?code=TASK001"

        class File:
            def get_type(self):
                return "main"

            def get_filename_with_ext(self):
                return "review.pdf"

            def get_ext(self):
                return "pdf"

            def get_file_size(self):
                return 2048

        class Snapshot:
            def get_code(self):
                return "SNAP001"

            def get_search_key(self):
                return "skey://sthpw/snapshot?code=SNAP001"

            def get_files_objects(self):
                return [File()]

        class Context:
            def get_versions(self):
                return {"SNAP001": Snapshot()}

            def get_versionless(self):
                return {}

        class Process:
            def get_contexts(self):
                return {"attachment": Context()}

        class Note:
            def get_info(self):
                return {
                    "code": "NOTE001", "login": "artist",
                    "process": "publish", "note": "Review {}".format(linked),
                    "timestamp": "2026-08-03 12:00:00",
                }
            def get_stype(self):
                return None

            def get_title(self):
                return "NOTE001"

            def get_process(self, process):
                return Process() if process == "attachment" else None

        resolver = SearchKeyPreviewResolver.__new__(SearchKeyPreviewResolver)
        descriptor = resolver._describe(
            "skey://sthpw/note?code=NOTE001",
            {"item_code": "NOTE001", "project": "sthpw"},
            Note(),
            defer_preview=True,
        )

        self.assertEqual(descriptor["body"], "Review")
        self.assertEqual(descriptor["_nestedKeys"], [linked])
        self.assertEqual(descriptor["attachmentCount"], 1)
        self.assertEqual(descriptor["attachments"][0]["title"], "review.pdf")

    def test_direct_note_link_reuses_note_history_attachment_loading(self):
        class File:
            def get_type(self):
                return "main"

            def get_filename_with_ext(self):
                return "review.png"

            def get_ext(self):
                return "png"

            def get_file_size(self):
                return 4096

            def get_web_preview(self):
                return self

        preview = File()

        class Snapshot:
            def get_code(self):
                return "SNAP001"

            def get_search_key(self):
                return "skey://sthpw/snapshot?code=SNAP001"

            def get_files_objects(self):
                return [preview]

        class Context:
            def get_versions(self):
                return {"SNAP001": Snapshot()}

            def get_versionless(self):
                return {}

        class Process:
            def get_contexts(self):
                return {"attachment": Context()}

        class Note:
            def __init__(self, hydrated=False):
                self.hydrated = hydrated

            def get_code(self):
                return "NOTE001"

            def get_info(self):
                return {
                    "code": "NOTE001", "login": "artist",
                    "process": "publish", "note": "Review image",
                    "timestamp": "2026-08-03 12:00:00",
                    "search_type": "show/asset",
                    "search_code": "ASSET001",
                    "project_code": "demo",
                }

            def get_stype(self):
                return None

            def get_title(self):
                return "NOTE001"

            def get_timestamp(self, **_kwargs):
                return "2026-08-03 12:00:00"

            def get_process(self, process):
                if self.hydrated and process == "attachment":
                    return Process()
                return None

        unresolved = Note()
        resolved = Note(hydrated=True)
        resolver = SearchKeyPreviewResolver.__new__(SearchKeyPreviewResolver)
        search_key = "skey://sthpw/note?code=NOTE001"

        with patch(
            "thlib.tactic_classes.get_sobjects",
            return_value={search_key: unresolved},
        ), patch(
            "thlib.tactic_classes.get_notes_with_attachments",
            return_value={"NOTE001": resolved},
        ) as get_history:
            descriptor = resolver._resolve_batch([search_key])[0]

        get_history.assert_called_once_with(
            ["NOTE001"], "demo"
        )
        self.assertEqual(descriptor["attachmentCount"], 1)
        self.assertEqual(descriptor["attachments"][0]["title"], "review.png")
        self.assertIs(descriptor["attachments"][0]["_previewFile"], preview)

    def test_message_preview_contains_message_bubble_data_and_access(self):
        search_key = "skey://sthpw/message_log?code=MESSAGE_LOG00001"
        class Message:
            def get_info(self):
                return {
                    "code": "MESSAGE_LOG00001",
                    "message_code": "CHAT001",
                    "login": "artist",
                    "message": "Ready for review",
                    "timestamp": "not-a-timestamp",
                }

            def get_stype(self):
                return None

            def get_title(self):
                return "MESSAGE_LOG00001"

        resolver = SearchKeyPreviewResolver.__new__(SearchKeyPreviewResolver)
        descriptor = resolver._describe(
            search_key,
            {"item_code": "MESSAGE_LOG00001", "project": "sthpw"},
            Message(),
            defer_preview=True,
        )

        self.assertEqual(descriptor["kind"], "message")
        self.assertEqual(descriptor["body"], "Ready for review")
        self.assertEqual(descriptor["author"], "artist")
        self.assertEqual(descriptor["conversationId"], "CHAT001")
        self.assertEqual(descriptor["itemCode"], search_key)
        self.assertFalse(descriptor["canOpen"])

    def test_message_preview_reuses_current_chat_navigation(self):
        search_key = "skey://sthpw/message_log?code=MESSAGE_LOG00001"

        class Messages:
            conversationId = "CHAT001"

            def __init__(self):
                self.shown = []
                self.forwarded = []

            def show_message(self, message_id):
                self.shown.append(message_id)

            def open_forwarded_message(self, conversation_id, message_id):
                self.forwarded.append((conversation_id, message_id))

        resolver = SearchKeyPreviewResolver.__new__(SearchKeyPreviewResolver)
        resolver._messages = Messages()
        resolver._users = None
        resolver._cache = {
            (*resolver._scope(), search_key): {
                "kind": "message",
                "canOpen": True,
                "conversationId": "CHAT001",
                "itemCode": search_key,
            }
        }

        resolver.open(search_key)

        self.assertEqual(resolver._messages.shown, [search_key])
        self.assertEqual(resolver._messages.forwarded, [])

    def test_uncached_user_link_uses_code_instead_of_requesting_login(self):
        search_key = "skey://sthpw/login?code=artist"

        class Users:
            def __init__(self):
                self.opened = []

            def open_profile(self, login):
                self.opened.append(login)

        resolver = SearchKeyPreviewResolver.__new__(SearchKeyPreviewResolver)
        resolver._messages = None
        resolver._users = Users()
        resolver._cache = {}

        resolver.open(search_key)

        self.assertEqual(resolver._users.opened, ["artist"])


if __name__ == "__main__":
    unittest.main()
