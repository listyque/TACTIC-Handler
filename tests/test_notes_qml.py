from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QPointF, Qt, QUrl, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QSignalSpy, QTest

from thlib.ui.communication import CommunicationController
from thlib.ui.controllers.item_operations import ItemOperationsMixin
from thlib.ui.controllers.selection import SelectionMixin
from thlib.ui.controllers.types import SearchTabSession
from thlib.ui.controllers.snapshot_details import SnapshotDetailsMixin
from thlib.ui.message_attachments import (
    AttachmentUploadController,
    ChatAttachmentController,
)
from thlib.ui.workspace_models.records import RecordListModel
from tests.support.async_scenarios import SignalStub


class _RepositorySync(QObject):
    file_download_done = Signal(object)


class _WorkspacePreviewModel(QObject):
    dataChanged = Signal(object, object, object)

    def __init__(self, preview_url):
        super().__init__()
        self.preview_url = preview_url

    def preview_url_for_search_key(self, _search_key):
        return self.preview_url


class _Workspace(QObject):
    selection_changed = Signal()

    def __init__(self):
        super().__init__()
        self._selected_sobject = None
        self._task_sobjects = []
        self._note_sobjects = []
        self._notes_loaded = False
        self._notes_process = None
        self.note_model = RecordListModel((
            "noteId", "searchKey", "author", "time", "body", "bodyHtml",
            "status", "process", "isOwn", "unread", "attachments",
            "attachmentCount", "entryType", "authorDisplay", "avatarUrl",
            "initials", "authorColor", "timePretty", "timeSimple",
            "statusFrom", "statusTo", "statusColor", "canEdit", "canDelete",
        ))
        self.task_model = RecordListModel(("process", "status"))
        self.snapshot_model = RecordListModel(("nodeId", "title", "version"))


class _Application(QObject):
    def __init__(self):
        super().__init__()
        self.workspace_state = _Workspace()
        self.repository_sync = _RepositorySync()
        self._selected_detail_process = ""
        self.opened_search_key = ""

    def open_search_key(self, value):
        self.opened_search_key = value


class _SObject:
    def __init__(self, info, search_key):
        self.info = info
        self.search_key = search_key
        self.note_counts = {}

    def get_info(self):
        return self.info

    def get_search_key(self):
        return self.search_key

    def get_title(self):
        return self.info.get("name") or self.info.get("code") or ""

    def get_timestamp(self, pretty=False, simple=False):
        return self.info.get("timestamp") or ""

    def get_process(self, _process):
        return None

    def get_notes_count(self, process=None):
        if process:
            return self.note_counts.get(process)
        return self.note_counts

    def set_notes_count(self, process, count):
        self.note_counts[process] = count

    def set_value(self, key, value):
        self.info[key] = value

    def commit(self, triggers=False):
        return {"triggers": triggers}


class _Task(_SObject):
    def __init__(self, info, statuses):
        code = str(info.get("code") or "TASK001")
        info = dict(info)
        info["code"] = code
        super().__init__(info, "sthpw/task?code=" + code)
        self.statuses = statuses

    def get_status_log(self):
        return self.statuses


class _SnapshotDetails(SnapshotDetailsMixin):
    def __init__(self, sobject, snapshots):
        self.workspace_model = SimpleNamespace(
            source_for_search_key=lambda _key: sobject,
            snapshot_nodes_for=lambda _key, refresh=False: snapshots,
        )


class _SelectionHarness(SelectionMixin):
    def __init__(self, node, nodes=None):
        self.node = node
        self.nodes = dict(nodes or {node.node_id: node})
        self.loaded = None
        self.workspace_model = SimpleNamespace(
            node_for=lambda node_id: self.nodes.get(node_id)
        )
        self.tab = SimpleNamespace(
            selected_node_id=node.node_id,
            detail_process_override="",
        )

    def _current_tab(self):
        return self.tab

    def _load_sobject_details(self, *args):
        self.loaded = args


class NotesQmlTests(unittest.TestCase):

    def test_same_selected_context_does_not_reset_task_inspector(self):
        application = _Application()
        target = _SObject(
            {"code": "ASSET001"}, "asset/asset?code=ASSET001"
        )
        task = _Task({
            "code": "TASK001", "process": "publish", "status": "Pending",
        }, [])
        other_task = _Task({
            "code": "TASK002", "process": "publish", "status": "Pending",
        }, [])
        application.workspace_state._selected_sobject = target
        application.workspace_state._task_sobjects = [task, other_task]
        with patch("thlib.ui.communication.env_read_config", return_value={}):
            controller = CommunicationController(application)
        controller._visible = True
        controller._process_tasks = [task, other_task]
        controller._selected_task_code = "TASK001"
        controller._loaded_task_context = (
            target.get_search_key(), "publish", "TASK001"
        )
        controller._note_records = [{"noteId": "NOTE001"}]
        controller._sync_selection_presentation()
        state_changes = QSignalSpy(controller.stateChanged)

        with patch.object(controller, "refresh") as refresh, patch.object(
            controller, "_refresh_process_counts"
        ):
            application.workspace_state.selection_changed.emit()
            application.workspace_state._selected_sobject = _SObject(
                dict(target.info), target.get_search_key()
            )
            replacement = _Task(dict(task.info), [])
            application.workspace_state._task_sobjects = [
                _Task(dict(other_task.info), []), replacement,
            ]
            application.workspace_state.selection_changed.emit()
            refresh.assert_not_called()
            self.assertEqual(state_changes.count(), 0)
            self.assertEqual(controller._note_records, [{"noteId": "NOTE001"}])
            self.assertEqual(controller.selectedTaskCode, "TASK001")
            self.assertEqual(
                controller._loaded_task_context,
                (target.get_search_key(), "publish", "TASK001"),
            )

            controller._visible = False
            controller._selection_presentation_dirty = False
            application.workspace_state.selection_changed.emit()
            self.assertTrue(controller._selection_presentation_dirty)
            controller.set_visible(True)
            refresh.assert_not_called()

            controller._loading = True
            controller._request_id = "still-loading"
            application.workspace_state.selection_changed.emit()
            self.assertEqual(controller._request_id, "still-loading")
            self.assertTrue(controller.loading)
            controller._loading = False

            controller._process = "model"
            controller._loading = True
            application.workspace_state.selection_changed.emit()
            self.assertEqual(controller.process, "publish")
            refresh.assert_called_once_with()
            refresh.reset_mock()

            replacement.info["status"] = "Complete"
            application.workspace_state.selection_changed.emit()
            refresh.assert_called_once_with()
            self.assertEqual(controller._note_records, [])

            application._selected_detail_process = "model"
            application.workspace_state.selection_changed.emit()
            self.assertEqual(controller.process, "model")
            self.assertEqual(refresh.call_count, 2)

            application.workspace_state._selected_sobject = _SObject(
                {"code": "ASSET002"}, "asset/asset?code=ASSET002"
            )
            application.workspace_state._task_sobjects = []
            application._selected_detail_process = ""
            application.workspace_state.selection_changed.emit()
            self.assertEqual(controller.process, "publish")
            self.assertEqual(refresh.call_count, 3)


    def test_note_text_drafts_follow_sobject_and_task_context(self):
        application = _Application()
        first = _SObject(
            {"code": "ASSET001"}, "asset/asset?code=ASSET001"
        )
        second = _SObject(
            {"code": "ASSET002"}, "asset/asset?code=ASSET002"
        )
        application.workspace_state._selected_sobject = first

        with patch(
            "thlib.ui.communication.env_read_config", return_value={}
        ), patch(
            "thlib.ui.communication.env_write_config"
        ):
            controller = CommunicationController(application)
            controller.set_draft_text("First object")

            application.workspace_state._selected_sobject = second
            controller._selection_changed()
            self.assertEqual(controller.draftText, "")
            controller.set_draft_text("Second object")

            application.workspace_state._selected_sobject = first
            controller._selection_changed()
            self.assertEqual(controller.draftText, "First object")

            first_task = _Task(
                {"code": "TASK001", "process": "publish"}, []
            )
            second_task = _Task(
                {"code": "TASK002", "process": "publish"}, []
            )
            controller._process_tasks = [first_task, second_task]
            controller._selected_task_code = "TASK001"
            controller._activate_draft_context()
            controller.set_draft_text("First task")

            controller.select_task("TASK002")
            self.assertEqual(controller.draftText, "")
            controller.set_draft_text("Second task")
            controller.select_task("TASK001")
            self.assertEqual(controller.draftText, "First task")

    def test_additional_task_sends_to_task_parent_branch(self):
        application = _Application()
        parent = _SObject(
            {"code": "ASSET001"}, "asset/asset?code=ASSET001"
        )
        application.workspace_state._selected_sobject = parent
        controller = CommunicationController(application)
        first = _Task({
            "code": "TASK001", "process": "publish", "context": "publish",
        }, [])
        second = _Task({
            "code": "TASK002", "process": "publish", "context": "review",
        }, [])
        controller._process_tasks = [first, second]
        captured = []
        controller._send_payload = lambda _attachments: captured.append(
            controller._pending_target
        )

        controller._selected_task_code = "TASK001"
        self.assertTrue(controller.send("Main branch"))
        controller._selected_task_code = "TASK002"
        self.assertTrue(controller.send("Task branch"))

        self.assertEqual(captured, [
            (parent.get_search_key(), "publish"),
            (second.get_search_key(), "publish"),
        ])

    def test_context_task_note_uses_the_parent_objects_project(self):
        application = _Application()
        parent = _SObject(
            {"code": "ASSET001"}, "asset/asset?code=ASSET001"
        )
        parent.get_project = lambda: SimpleNamespace(
            get_code=lambda: "demo"
        )
        application.workspace_state._selected_sobject = parent
        controller = CommunicationController(application)
        first = _Task({
            "code": "TASK001", "process": "model", "context": "model",
        }, [])
        contextual = _Task({
            "code": "TASK002", "process": "model", "context": "review",
        }, [])
        controller._process = "model"
        controller._process_tasks = [first, contextual]
        controller._selected_task_code = "TASK002"

        with patch.object(
            controller, "_run",
            side_effect=lambda callback, **_kwargs: callback(),
        ), patch(
            "thlib.tactic_classes.add_note",
            return_value={"code": "NOTE001"},
        ) as add_note, patch(
            "thlib.environment.env_server.get_user", return_value="artist",
        ):
            self.assertTrue(controller.send("Context note"))

        add_note.assert_called_once_with(
            contextual.get_search_key(), "model", "model", "Context note",
            "artist", attachments=[], project_code="demo",
        )

    def test_attachment_drafts_are_isolated_and_restored_after_restart(self):
        application = _Application()
        stored = {}

        def read_config(**kwargs):
            return stored.get(kwargs["unique_id"], {})

        def write_config(values, **kwargs):
            stored[kwargs["unique_id"]] = {
                "contexts": {
                    key: [dict(record) for record in records]
                    for key, records in values.get("contexts", {}).items()
                },
            }

        with TemporaryDirectory() as directory, patch(
            "thlib.ui.message_attachments.env_read_config",
            side_effect=read_config,
        ), patch(
            "thlib.ui.message_attachments.env_write_config",
            side_effect=write_config,
        ):
            first_path = Path(directory) / "first.txt"
            second_path = Path(directory) / "second.txt"
            first_path.write_text("first", encoding="utf-8")
            second_path.write_text("second", encoding="utf-8")

            controller = ChatAttachmentController(application)
            controller.activate_context("server-user/CHAT001")
            controller.add_files([QUrl.fromLocalFile(str(first_path))])
            controller.activate_context("server-user/CHAT002")
            self.assertEqual(controller.count, 0)
            controller.add_files([QUrl.fromLocalFile(str(second_path))])
            controller.activate_context("server-user/CHAT001")
            self.assertEqual(
                [record["title"] for record in controller.model._records],
                ["first.txt"],
            )
            controller.shutdown()
            self.assertNotIn(
                "version", stored["cache/communication/messages"]
            )

            restored = ChatAttachmentController(application)
            restored.activate_context("server-user/CHAT002")
            self.assertEqual(
                [record["title"] for record in restored.model._records],
                ["second.txt"],
            )
            restored.activate_context("server-user/CHAT001")
            self.assertEqual(
                [record["title"] for record in restored.model._records],
                ["first.txt"],
            )

    def test_attachment_draft_can_retarget_without_losing_staged_files(self):
        application = _Application()
        with TemporaryDirectory() as directory, patch(
            "thlib.ui.message_attachments.env_read_config",
            return_value={},
        ), patch(
            "thlib.ui.message_attachments.env_write_config",
        ):
            file_path = Path(directory) / "guide.png"
            file_path.write_bytes(b"preview")
            controller = AttachmentUploadController(
                application, draft_namespace="knowledge"
            )
            controller.activate_context("knowledge:new:demo")
            controller.add_files([QUrl.fromLocalFile(str(file_path))])

            self.assertTrue(controller.retarget_context(
                "skey://demo/th_knowledge_article?code=DOC0001"
            ))

            self.assertEqual(controller.count, 1)
            self.assertEqual(controller.model._records[0]["title"], "guide.png")
            controller.activate_context("knowledge:new:demo")
            self.assertEqual(controller.count, 0)
            controller.activate_context(
                "skey://demo/th_knowledge_article?code=DOC0001"
            )
            self.assertEqual(controller.count, 1)

    def test_partial_upload_reports_failure_instead_of_uploaded(self):
        with patch(
            "thlib.ui.message_attachments.env_read_config", return_value={}
        ), patch("thlib.ui.message_attachments.env_write_config"):
            controller = ChatAttachmentController(_Application())
            records = [
                {"token": "one", "title": "one.png", "path": "one.png"},
                {"token": "two", "title": "two.png", "path": "two.png"},
            ]
            controller._upload_records = records
            controller.model.replace(records)
            controller._busy = True
            uploaded = QSignalSpy(controller.uploaded)
            failed = QSignalSpy(controller.failed)

            controller._ready({
                "target": "sthpw/message?code=CHAT001\nattachment/chat",
                "snapshots": {"one": "sthpw/snapshot?code=SNAP001"},
            })

            self.assertEqual(uploaded.count(), 0)
            self.assertEqual(failed.count(), 1)
            self.assertEqual(controller.model._records[1]["status"], "failed")

    def test_open_notes_on_sobject_resets_process_to_publish(self):
        node = SimpleNamespace(
            node_id="skey://demo/asset?code=ASSET001",
            node_type="sobject",
            search_key="skey://demo/asset?code=ASSET001",
            process="",
            context="",
        )
        emitted = []
        opened = []
        controller = SimpleNamespace(
            workspace_model=SimpleNamespace(
                node_for=lambda node_id: node if node_id == node.node_id else None
            ),
            workspace_state=SimpleNamespace(
                selection_changed=SimpleNamespace(
                    emit=lambda: emitted.append(True)
                )
            ),
            dock_model=SimpleNamespace(
                show_panel=lambda panel: opened.append(panel)
            ),
            _selected_detail_process="model",
            _current_tab=lambda: SimpleNamespace(
                selected_node_id=node.node_id
            ),
            select_result_node=lambda *args: None,
        )

        ItemOperationsMixin._show_process_details(
            controller, node.node_id, "notes"
        )

        self.assertEqual(controller._selected_detail_process, "publish")
        self.assertEqual(emitted, [True])
        self.assertEqual(opened, ["notes"])

    def test_process_picker_opens_exact_process_and_marks_it_seen(self):
        node = SimpleNamespace(
            node_id="skey://demo/asset?code=ASSET001",
            node_type="sobject",
            search_key="skey://demo/asset?code=ASSET001",
            process="",
            context="",
        )
        seen = []
        opened = []
        controller = SimpleNamespace(
            workspace_model=SimpleNamespace(
                node_for=lambda node_id: (
                    node if node_id == node.node_id else None
                ),
                mark_process_seen=lambda *args: seen.append(args),
            ),
            workspace_state=SimpleNamespace(
                selection_changed=SimpleNamespace(emit=lambda: None)
            ),
            dock_model=SimpleNamespace(
                show_panel=lambda panel: opened.append(panel)
            ),
            _selected_detail_process="publish",
            _current_tab=lambda: SimpleNamespace(
                selected_node_id=node.node_id
            ),
            select_result_node=lambda *args: None,
        )
        controller._show_process_details = lambda *args, **kwargs: (
            ItemOperationsMixin._show_process_details(
                controller, *args, **kwargs
            )
        )

        ItemOperationsMixin.open_process_details(
            controller, node.node_id, "notes", "rig"
        )

        self.assertEqual(seen, [(node.node_id, "notes", "rig")])
        self.assertEqual(controller._selected_detail_process, "rig")
        self.assertEqual(opened, ["notes"])

    def test_closed_task_inspector_keeps_picked_process_during_delayed_load(self):
        node = SimpleNamespace(
            node_id="asset", node_type="sobject", parent_id="",
            search_key="demo/asset?code=ASSET001", process="", context="",
        )
        tab = SearchTabSession(tab_id="tab", title="Assets")
        tab.selected_node_id = "previous"
        opened = []
        controller = SimpleNamespace(
            workspace_model=SimpleNamespace(node_for=lambda _id: node),
            workspace_state=SimpleNamespace(
                selection_changed=SimpleNamespace(emit=lambda: None),
            ),
            dock_model=SimpleNamespace(show_panel=opened.append),
            _registry=SimpleNamespace(invoke=lambda _command: False),
            _selected_detail_process="publish",
            _current_tab=lambda: tab,
            select_result_node=lambda node_id, *_args: setattr(
                tab, "selected_node_id", node_id
            ),
        )

        ItemOperationsMixin._show_process_details(
            controller, node.node_id, "tasks", process_override="light"
        )
        details = SelectionMixin._selected_detail_parameters(
            controller, node.node_id, node.search_key
        )

        self.assertEqual(details[1], "light")
        self.assertEqual(opened, ["tasks"])

    def test_selecting_another_object_clears_picked_process(self):
        first = SimpleNamespace(
            node_id="first", node_type="sobject", source=None,
            search_key="demo/asset?code=ASSET001", process="", context="",
        )
        second = SimpleNamespace(
            node_id="second", node_type="sobject", source=None,
            search_key="demo/asset?code=ASSET002", process="", context="",
        )
        nodes = {first.node_id: first, second.node_id: second}
        tab = SearchTabSession(tab_id="tab", title="Assets")
        tab.selected_node_id = first.node_id
        tab.selected_node_ids = [first.node_id]
        tab.detail_process_override = "light"
        controller = SimpleNamespace(
            workspace_model=SimpleNamespace(node_for=nodes.get),
            _current_tab=lambda: tab,
            selected_node_changed=SimpleNamespace(emit=lambda: None),
            _cancel_selected_payload_worker=lambda: None,
            _cancel_versions_worker=lambda: None,
            versions_model=SimpleNamespace(clear=lambda: None),
            _selection_load_timer=SimpleNamespace(start=lambda: None),
            _save_search_cache=lambda: None,
        )

        SelectionMixin.select_result_node(
            controller, second.node_id, second.search_key, "sobject"
        )
        details = SelectionMixin._selected_detail_parameters(
            controller, second.node_id, second.search_key
        )

        self.assertEqual(tab.detail_process_override, "")
        self.assertEqual(details[1], "publish")

    def test_task_picker_opens_exact_task_context(self):
        root = SimpleNamespace(
            node_id="asset", node_type="sobject", parent_id="",
            search_key="demo/asset?code=ASSET001",
        )
        process = SimpleNamespace(
            node_id="process:model", node_type="process",
            parent_id=root.node_id, search_key=root.search_key,
        )
        nodes = {root.node_id: root, process.node_id: process}
        shown = []
        requested = []
        controller = SimpleNamespace(
            _node_for_any=lambda node_id: nodes.get(node_id),
            _show_process_details=lambda *args, **kwargs: shown.append(
                (args, kwargs)
            ),
            taskContextRequested=SimpleNamespace(
                emit=lambda *args: requested.append(args)
            ),
        )

        ItemOperationsMixin.open_process_task_details(
            controller, process.node_id, "notes", "model", "TASK002"
        )

        self.assertEqual(
            shown,
            [((process.node_id, "notes"), {"process_override": "model"})],
        )
        self.assertEqual(requested, [(
            "TASK002", root.search_key, "model",
        )])

    def test_tasks_action_uses_selected_workspace_command_for_items_and_processes(self):
        for node_type, process, expected_process in (
            ("sobject", "", "publish"),
            ("process", "model", "model"),
        ):
            with self.subTest(node_type=node_type):
                node = SimpleNamespace(
                    node_id="node-" + node_type,
                    node_type=node_type,
                    search_key="skey://demo/asset?code=ASSET001",
                    process=process,
                    context=process,
                )
                invoked = []
                opened = []
                controller = SimpleNamespace(
                    workspace_model=SimpleNamespace(
                        node_for=lambda node_id: (
                            node if node_id == node.node_id else None
                        )
                    ),
                    workspace_state=SimpleNamespace(
                        selection_changed=SimpleNamespace(emit=lambda: None)
                    ),
                    dock_model=SimpleNamespace(
                        show_panel=lambda panel: opened.append(panel)
                    ),
                    _registry=SimpleNamespace(
                        invoke=lambda command: (
                            invoked.append(command) or True
                        )
                    ),
                    _selected_detail_process="",
                    _current_tab=lambda: SimpleNamespace(
                        selected_node_id=node.node_id
                    ),
                    select_result_node=lambda *args: None,
                )

                ItemOperationsMixin._show_process_details(
                    controller, node.node_id, "tasks"
                )

                self.assertEqual(
                    invoked, ["show_selected_tasks_workspace"]
                )
                self.assertEqual(opened, [])
                self.assertEqual(
                    controller._selected_detail_process, expected_process
                )
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_grouped_message_without_avatar_releases_preview_rendering(self):
        root = Path(__file__).resolve().parents[1]
        qml_dir = root / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        engine.addImportPath(str(qml_dir))
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "MessageTimelineFrame.qml")),
        )
        frame = component.createWithInitialProperties({
            "theme": theme,
            "width": 420,
            "groupLast": False,
            "avatarUrl": "file:///avatar-that-must-not-load.png",
        })
        self.assertIsNotNone(
            frame,
            "\n".join(error.toString() for error in component.errors()),
        )
        self.app.processEvents()

        source_image = frame.findChild(QObject, "previewSourceImage")
        mask_loader = frame.findChild(QObject, "previewMaskLoader")
        self.assertIsNotNone(source_image)
        self.assertIsNotNone(mask_loader)
        self.assertTrue(source_image.property("source").isEmpty())
        self.assertFalse(mask_loader.property("active"))
        self.assertIsNone(
            frame.findChild(QObject, "messageTimelineGroupTail")
        )

        frame.deleteLater()
        theme.deleteLater()

    def test_message_knowledge_link_uses_article_card_and_opens_it(self):
        qml_dir = Path(__file__).resolve().parents[1] / "thlib/ui/qml"
        engine = QQmlEngine()
        engine.addImportPath(str(qml_dir))
        message_model = RecordListModel((
            "messageId", "sender", "senderDisplay", "avatarUrl",
            "initials", "senderColor", "body", "bodyHtml", "displayHtml",
            "skeyPreviews", "timestamp", "timePretty", "timeSimple",
            "isOwn", "unread", "attachments", "canEdit", "edited",
            "pinned", "editedBy", "editedAt", "editHistory", "replyTo",
            "forwardedFrom", "forwardSelected", "reactions",
            "reactionPending", "deliveryStatus", "deliveryRecipientCount",
            "deliveryDeliveredCount", "deliveryReadCount", "groupFirst",
            "groupLast",
        ), [{
            "messageId": "MESSAGE_LOG0001",
            "sender": "artist",
            "senderDisplay": "Artist",
            "avatarUrl": "",
            "initials": "AR",
            "senderColor": "#4f91c7",
            "body": "skey://demo/th_knowledge_article?code=DOC0001",
            "bodyHtml": "",
            "displayHtml": "",
            "skeyPreviews": [{
                "searchKey": (
                    "skey://demo/th_knowledge_article?code=DOC0001"
                ),
                "status": "ready",
                "kind": "knowledge",
                "articleKind": "article",
                "title": "Lighting guide",
                "description": "How lighting reviews are organized",
                "excerpt": "Prepare references before the review.",
            }],
            "timestamp": "2026-08-31 10:00:00",
            "timePretty": "now",
            "timeSimple": "2026-08-31 10:00:00",
            "isOwn": False,
            "unread": False,
            "attachments": [],
            "canEdit": False,
            "edited": False,
            "pinned": False,
            "editedBy": "",
            "editedAt": "",
            "editHistory": [],
            "replyTo": {},
            "forwardedFrom": {},
            "forwardSelected": False,
            "reactions": [],
            "reactionPending": False,
            "deliveryStatus": "",
            "deliveryRecipientCount": 0,
            "deliveryDeliveredCount": 0,
            "deliveryReadCount": 0,
            "groupFirst": True,
            "groupLast": True,
        }])
        engine.rootContext().setContextProperty(
            "testMessageModel", message_model
        )
        component = QQmlComponent(engine)
        component.setData(b'''import QtQuick
import QtQuick.Window
import "." as App
Window {
    id: host
    width: 560
    height: 300
    visible: true
    property string openedKey: ""
    property bool messagePresentationReady: true
    property var timelineReactions: ({"messageId": ""})
    QtObject {
        id: controller
        property bool busy: false
        property int forwardSelectionCount: 0
        property string conversationId: "CHAT001"
        property string messageSearch: ""
        function open_skey_preview(value) { host.openedKey = value }
    }
    App.Theme { id: theme; dark: true }
    App.MessagesTimeline {
        anchors.fill: parent
        theme: theme
        host: host
        controller: controller
        timelineModel: testMessageModel
        current: true
        historyHasMore: false
    }
}''', QUrl.fromLocalFile(str(qml_dir / "_KnowledgeMessageCardTest.qml")))
        window = component.create()
        self.assertIsNotNone(
            window,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            self.assertTrue(QTest.qWaitForWindowExposed(window))
            self.app.processEvents()
            timeline = window.findChild(QObject, "messageTimelineList")
            self.assertIsNotNone(timeline)
            self.assertFalse(timeline.property("reuseItems"))
            def visual_items(parent):
                pending = [parent]
                while pending:
                    item = pending.pop()
                    yield item
                    pending.extend(item.childItems())

            def visual_item_named(parent, object_name):
                for item in visual_items(parent):
                    if item.objectName() == object_name:
                        return item
                return None

            card = visual_item_named(
                timeline, "messageSkeyPreviewCard-0"
            )
            title = visual_item_named(
                timeline, "knowledgeSkeyPreviewTitle"
            )
            description = visual_item_named(
                timeline, "knowledgeSkeyPreviewDescription"
            )
            self.assertEqual(timeline.property("count"), 1)
            self.assertIsNotNone(
                card,
                "Timeline has one row but did not create its Knowledge card",
            )
            self.assertIsNotNone(title)
            self.assertIsNotNone(description)
            self.assertEqual(title.property("text"), "Lighting guide")
            self.assertEqual(
                description.property("text"),
                "How lighting reviews are organized",
            )
            visible_text = " ".join(
                str(item.property("text") or "")
                for item in visual_items(timeline)
                if item.property("text") is not None
            )
            self.assertNotIn("TH KNOWLEDGE ARTICLE", visible_text)

            point = card.mapToScene(QPointF(20, card.height() / 2))
            QTest.mouseClick(
                window, Qt.LeftButton, pos=point.toPoint()
            )
            self.app.processEvents()
            self.assertEqual(
                window.property("openedKey"),
                "skey://demo/th_knowledge_article?code=DOC0001",
            )
        finally:
            window.close()
            window.deleteLater()
            engine.deleteLater()

    def test_notes_components_compile(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        for name in (
                "controls/AttachmentDropArea.qml",
                "AttachmentStagingPanel.qml", "MessageComposerField.qml",
                "MessagesConversationList.qml",
                "MessageReactionPicker.qml",
                "MessageSendButton.qml", "MessageReplyPreview.qml",
                "MessageForwardPreview.qml", "MessageTimelineFrame.qml",
                "AttachmentCard.qml", "SnapshotSummary.qml",
                "WorkspaceResultItem.qml", "SKeyPreviewCard.qml",
                "TaskInspector.qml", "QuickFilterEditorView.qml",
                "ActivityEventCard.qml",
                "CommunicationView.qml", "MessagesView.qml"):
            component = QQmlComponent(engine, QUrl.fromLocalFile(str(qml_dir / name)))
            self.assertNotEqual(
                component.status(),
                QQmlComponent.Status.Error,
                "\n".join(error.toString() for error in component.errors()),
            )

    def test_skey_preview_owns_load_state_without_overriding_item_state(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "SKeyPreviewCard.qml"))
        )
        card = component.createWithInitialProperties({
            "theme": theme,
            "preview": {"status": "loading", "kind": "sobject"},
        })
        try:
            self.assertIsNotNone(
                card,
                "\n".join(error.toString() for error in component.errors()),
            )
            self.assertEqual(card.property("loadState"), "loading")
            self.assertEqual(card.property("state"), "")

            card.setProperty(
                "preview", {"status": "error", "kind": "sobject"}
            )
            self.app.processEvents()
            self.assertEqual(card.property("loadState"), "error")
            self.assertTrue(card.property("failed"))
        finally:
            if card is not None:
                card.deleteLater()
            if theme is not None:
                theme.deleteLater()
            engine.deleteLater()

    def test_notes_and_messages_share_attachment_drop_area(self):
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        notes_source = (qml_dir / "CommunicationView.qml").read_text(
            encoding="utf-8"
        )
        messages_source = (qml_dir / "MessagesView.qml").read_text(
            encoding="utf-8"
        )
        control_source = (
            qml_dir / "controls" / "AttachmentDropArea.qml"
        ).read_text(encoding="utf-8")

        self.assertEqual(
            notes_source.count("Controls.AttachmentDropArea {"), 1
        )
        self.assertEqual(
            messages_source.count("Controls.AttachmentDropArea {"), 1
        )
        self.assertIn(
            "attachmentController: noteAttachments", notes_source
        )
        self.assertIn(
            "attachmentController: messageAttachments", messages_source
        )
        self.assertIn(
            "root.attachmentController.add_files(urls)", control_source
        )
        self.assertIn("drop.acceptProposedAction()", control_source)

    def test_notes_keep_compact_metrics_and_messages_use_external_avatar(self):
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        notes_source = (qml_dir / "CommunicationView.qml").read_text(
            encoding="utf-8"
        )
        messages_source = (qml_dir / "MessagesView.qml").read_text(
            encoding="utf-8"
        ) + (qml_dir / "MessagesTimeline.qml").read_text(encoding="utf-8")
        frame_source = (qml_dir / "MessageTimelineFrame.qml").read_text(
            encoding="utf-8"
        )
        body_source = (qml_dir / "MessageBodyText.qml").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "spacing: root.theme.communicationListSpacing", notes_source
        )
        self.assertIn("spacing: 0", messages_source)
        self.assertIn("messageRow.groupLast", messages_source)
        self.assertIn("messageRow.groupFirst", messages_source)
        self.assertIn(
            'objectName: "messageMetadataSpacer"', messages_source
        )
        self.assertIn(
            "visible: !messageRow.groupFirst", messages_source
        )
        self.assertNotIn("messageRow.groupFirst", notes_source)
        self.assertIn(
            "root.theme.communicationBubblePadding * 2", notes_source
        )
        self.assertIn(
            "root.theme.communicationContentSpacing", notes_source
        )
        for source in (notes_source, frame_source):
            self.assertIn(
                "root.theme.communicationAvatarSpacing", source
            )
        self.assertIn("root.bubblePadding * 2", frame_source)
        self.assertIn("spacing: root.bubbleSpacing", frame_source)
        self.assertIn("MessageTimelineFrame {", messages_source)
        self.assertNotIn("MessageTimelineFrame {", notes_source)
        self.assertIn('objectName: "messageTimelineAvatar"', frame_source)
        self.assertIn("readonly property real avatarExtent", frame_source)
        self.assertNotIn(
            'timelineRow.entryType === "status" ? 10 : 0', notes_source
        )
        status_content = notes_source[
            notes_source.index('name: "status"'):
            notes_source.index("MessageBodyText {")
        ]
        self.assertIn("font.pointSize: Controls.Typography.body", status_content)
        self.assertNotIn("font.pixelSize", status_content)
        self.assertIn("font.pointSize:", body_source)
        self.assertIn(": Controls.Typography.body", body_source)
        self.assertNotIn("font.pixelSize", body_source)

    def test_message_avatar_stays_outside_bubble_on_both_sides(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "MessageTimelineFrame.qml")),
        )
        frame = component.createWithInitialProperties({
            "theme": theme,
            "width": 640,
            "outgoing": False,
        })
        self.assertIsNotNone(
            frame,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            self.app.processEvents()
            avatar = frame.findChild(QQuickItem, "messageTimelineAvatar")
            bubble = frame.findChild(QQuickItem, "messageTimelineBubble")
            self.assertIsNotNone(avatar)
            self.assertIsNotNone(bubble)
            self.assertEqual(avatar.property("width"), 40.0)
            self.assertLessEqual(
                self._item_right(avatar, frame),
                self._item_x(bubble, frame),
            )

            frame.setProperty("outgoing", True)
            self.app.processEvents()
            self.assertLessEqual(
                self._item_right(bubble, frame),
                self._item_x(avatar, frame),
            )

            frame.setProperty("width", 340)
            self.app.processEvents()
            self.assertEqual(avatar.property("width"), 34.0)
            self.assertGreaterEqual(
                self._item_x(bubble, frame), 0
            )
            self.assertLessEqual(
                self._item_right(avatar, frame), frame.property("width")
            )
        finally:
            frame.deleteLater()
            theme.deleteLater()

    def test_message_group_uses_one_bottom_avatar_and_tail(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "MessageTimelineFrame.qml")),
        )
        frame = component.createWithInitialProperties({
            "theme": theme,
            "width": 640,
            "outgoing": False,
            "groupFirst": True,
            "groupLast": False,
        })
        self.assertIsNotNone(
            frame,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            self.app.processEvents()
            avatar = frame.findChild(QQuickItem, "messageTimelineAvatar")
            bubble = frame.findChild(QQuickItem, "messageTimelineBubble")
            outline = frame.findChild(QQuickItem, "messageTimelineOutline")
            self.assertIsNotNone(avatar)
            self.assertIsNotNone(bubble)
            self.assertIsNotNone(outline)
            self.assertEqual(outline.property("tailExtent"), 0)
            radius = frame.property("bubbleCornerRadius")
            self.assertFalse(avatar.property("visible"))

            frame.setProperty("groupFirst", False)
            frame.setProperty("groupLast", True)
            self.app.processEvents()

            self.assertTrue(avatar.property("visible"))
            self.assertGreater(outline.property("tailExtent"), 0)
            self.assertEqual(frame.property("bubbleCornerRadius"), radius)
            avatar_bottom = (
                avatar.mapToScene(QPointF()).y()
                - frame.mapToScene(QPointF()).y()
                + avatar.property("height")
            )
            self.assertAlmostEqual(avatar_bottom, frame.property("height"))
            self.assertLess(
                outline.property("tailExtent"), avatar.property("width") / 2
            )

            frame.setProperty("outgoing", True)
            self.app.processEvents()
            self.assertEqual(frame.property("bubbleCornerRadius"), radius)
        finally:
            frame.deleteLater()
            theme.deleteLater()

    def test_short_message_frame_uses_content_width_and_compact_height(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        component = QQmlComponent(engine)
        component.setData(
            b'''\
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."

Item {
    width: 720
    height: frame.height
    Theme { id: appTheme; dark: true }
    MessageTimelineFrame {
        id: frame
        objectName: "compactMessageFrame"
        width: parent.width
        theme: appTheme
        RowLayout {
            Label { text: "Admin" }
            Label { text: "1 week ago" }
        }
        Label { text: "Hello" }
    }
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_CompactMessageTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            self.app.processEvents()
            frame = owner.findChild(QQuickItem, "compactMessageFrame")
            bubble = frame.findChild(QQuickItem, "messageTimelineBubble")
            self.assertGreaterEqual(frame.property("bubblePadding"), 7)
            self.assertLess(bubble.property("width"), 280)
            self.assertLess(bubble.property("height"), 80)
        finally:
            owner.deleteLater()
            engine.deleteLater()

    def test_messages_timeline_keeps_a_usable_split_width(self):
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        messages_source = (qml_dir / "MessagesView.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn('objectName: "messagesTimelinePane"', messages_source)
        self.assertIn("SplitView.minimumWidth: 440", messages_source)

        engine = QQmlEngine()
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls

Item {
    id: host
    width: 796
    height: 500
    property real requestedConversationWidth: 252
    property alias timelineWidth: timeline.width

    SplitView {
        anchors.fill: parent
        orientation: Qt.Horizontal
        handle: Item { implicitWidth: 8 }

        Item {
            SplitView.preferredWidth: host.requestedConversationWidth
            SplitView.minimumWidth: 210
        }
        Item {
            id: timeline
            SplitView.fillWidth: true
            SplitView.minimumWidth: 440
        }
    }
}
''',
            QUrl(),
        )
        host = component.create()
        self.assertIsNotNone(
            host,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            self.app.processEvents()
            self.assertGreaterEqual(host.property("timelineWidth"), 440)
            host.setProperty("requestedConversationWidth", 700)
            self.app.processEvents()
            self.assertGreaterEqual(host.property("timelineWidth"), 440)
        finally:
            host.deleteLater()

    def test_direct_message_header_renders_shared_presence(self):
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        messages_source = (qml_dir / "MessagesView.qml").read_text(
            encoding="utf-8"
        )
        notes_source = (qml_dir / "CommunicationView.qml").read_text(
            encoding="utf-8"
        )

        self.assertIn("selectedConversationPresenceText", messages_source)
        self.assertIn("selectedConversation.peerLogin", messages_source)
        self.assertIn("selectedConversation.online", messages_source)
        self.assertNotIn("selectedConversationPresenceText", notes_source)

    @staticmethod
    def _item_right(item, parent):
        return (
            NotesQmlTests._item_x(item, parent)
            + item.property("width")
        )

    @staticmethod
    def _item_x(item, parent):
        return (
            item.mapToScene(QPointF()).x()
            - parent.mapToScene(QPointF()).x()
        )

    def test_message_body_uses_project_body_type_at_runtime(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "MessageBodyText.qml"))
        )
        body = component.createWithInitialProperties({
            "theme": theme,
            "rawText": "Two lines\nwith compact text",
            "sourceHtml": "Two lines<br>with compact text",
            "width": 320,
        })
        self.assertIsNotNone(
            body,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            self.app.processEvents()
            font = body.property("font")
            self.assertAlmostEqual(font.pointSizeF(), 9.25)
            self.assertEqual(body.property("topPadding"), 0.0)
            self.assertEqual(body.property("bottomPadding"), 0.0)
            self.assertGreater(body.property("contentHeight"), 0.0)
        finally:
            body.deleteLater()
            theme.deleteLater()

    def test_dropped_attachment_paths_are_deduplicated(self):
        application = _Application()
        controller = AttachmentUploadController(application)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "preview.png"
            path.write_bytes(b"preview")
            url = QUrl.fromLocalFile(str(path))

            controller.add_files([url, url])
            controller.add_files([url])

            self.assertEqual(controller.count, 1)
            self.assertEqual(
                controller.model._records[0]["path"], str(path.resolve())
            )

    def test_attachment_drop_area_stages_urls_at_runtime(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "controls" as Controls
Window {
    id: window
    width: 360
    height: 240
    visible: true
    property int stagedCount: 0
    Theme { id: theme; dark: true }
    QtObject {
        id: attachments
        function add_files(urls) { window.stagedCount = urls.length }
    }
    Controls.AttachmentDropArea {
        id: dropArea
        objectName: "attachmentDropArea"
        anchors.fill: parent
        theme: theme
        attachmentController: attachments
    }
    Component.onCompleted: {
        dropArea.stageUrls(["file:///first.txt", "file:///second.txt"])
    }
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_AttachmentDropAreaTest.qml")),
        )
        window = component.create()
        self.assertIsNotNone(
            window,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            self.app.processEvents()
            drop_area = window.findChild(QObject, "attachmentDropArea")
            self.assertIsNotNone(drop_area)
            self.assertEqual(drop_area.property("width"), 360.0)
            self.assertEqual(drop_area.property("height"), 240.0)
            self.assertEqual(window.property("stagedCount"), 2)
        finally:
            window.close()
            window.deleteLater()

    def test_message_composer_enter_submits_and_control_enter_adds_line(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
Window {
    id: window
    width: 420
    height: 120
    visible: true
    signal submitted()
    QtObject {
        id: attachments
        function clipboard_has_text() { return false }
        function clipboard_has_image() { return false }
        function add_clipboard_image() {}
    }
    Theme { id: theme; dark: true }
    MessageComposerField {
        id: composer
        objectName: "messageComposer"
        anchors.fill: parent
        theme: theme
        emojiCatalogModel: null
        attachmentController: attachments
        onSubmitRequested: window.submitted()
    }
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_MessageComposerKeyTest.qml")),
        )
        window = component.create()
        self.assertIsNotNone(
            window,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            composer = window.findChild(QObject, "messageComposer")
            editor = window.findChild(QObject, "messageComposerTextArea")
            self.assertIsNotNone(composer)
            self.assertIsNotNone(editor)
            submitted = QSignalSpy(window.submitted)
            editor.forceActiveFocus()
            QTest.qWait(20)

            composer.setProperty("text", "First message")
            composer.setProperty("cursorPosition", len("First message"))
            QTest.keyClick(
                window,
                Qt.Key.Key_Return,
                Qt.KeyboardModifier.NoModifier,
            )
            self.assertEqual(submitted.count(), 1)
            self.assertEqual(composer.property("text"), "First message")

            composer.setProperty("text", "First line")
            composer.setProperty("cursorPosition", len("First line"))
            QTest.keyClick(
                window,
                Qt.Key.Key_Return,
                Qt.KeyboardModifier.ControlModifier,
            )
            self.assertEqual(submitted.count(), 1)
            self.assertEqual(composer.property("text"), "First line\n")

            QTest.keyClick(
                window,
                Qt.Key.Key_Enter,
                Qt.KeyboardModifier.NoModifier,
            )
            self.assertEqual(submitted.count(), 2)
        finally:
            window.close()
            window.deleteLater()

    def test_message_lists_use_a_bottom_anchor(self):
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        notes_source = (qml_dir / "CommunicationView.qml").read_text(
            encoding="utf-8"
        )
        messages_source = (qml_dir / "MessagesView.qml").read_text(
            encoding="utf-8"
        ) + (qml_dir / "MessagesTimeline.qml").read_text(encoding="utf-8")

        self.assertIn("Controls.SmoothListView {", notes_source)
        self.assertIn("bottomAnchored: true", notes_source)
        self.assertIn(
            "topMargin: Math.max(0, height - contentHeight)",
            messages_source,
        )
        self.assertIn(
            "function onMessageAppendedForConversation(conversationId)",
            messages_source,
        )

    def test_smooth_list_view_bottom_anchor_layout(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        component = QQmlComponent(engine)
        source = """import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import "controls" as Controls
Window {
    width: 320
    height: 300
    visible: true
    Theme { id: theme; dark: true }
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        Item { Layout.fillWidth: true; Layout.preferredHeight: 40 }
        Controls.SmoothListView {
            id: list
            theme: theme
            objectName: \"bottomAnchoredList\"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 6
            bottomAnchored: true
            model: 1
            delegate: Rectangle {
                width: list.width
                height: 50
            }
            Component.onCompleted: Qt.callLater(positionViewAtEnd)
        }
    }
}
"""
        component.setData(
            source.encode("utf-8"),
            QUrl.fromLocalFile(str(qml_dir / "_BottomAnchorTest.qml")),
        )
        window = component.create()
        self.assertIsNotNone(
            window,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            for _pass in range(10):
                self.app.processEvents()
            view = window.findChild(QObject, "bottomAnchoredList")
            self.assertIsNotNone(view)
            self.assertAlmostEqual(view.property("contentHeight"), 50.0)
            self.assertAlmostEqual(view.property("height"), 254.0)
            self.assertAlmostEqual(view.property("topMargin"), 204.0)
            self.assertAlmostEqual(view.property("contentY"), -204.0)
        finally:
            window.close()
            window.deleteLater()

    def test_forward_dialog_uses_registered_conversation_model(self):
        path = (
            Path(__file__).parents[1] / "thlib" / "ui" / "qml" / "MessagesView.qml"
        )
        source = path.read_text(encoding="utf-8")
        self.assertIn("model: messageConversationModel", source)
        self.assertNotIn("model: messagesController.conversations", source)

    def test_pin_history_entries_open_their_message(self):
        path = (
            Path(__file__).parents[1] / "thlib" / "ui" / "qml" / "MessagesView.qml"
        )
        source = path.read_text(encoding="utf-8")
        self.assertIn("id: pinHistoryEntry", source)
        self.assertIn("messagesController.show_message(messageId)", source)

    def test_notes_controls_require_selected_sobject(self):
        application = _Application()
        controller = CommunicationController(application)
        self.assertFalse(controller.hasTarget)

        application.workspace_state._selected_sobject = _SObject(
            {"code": "ASSET001"}, "asset/asset?code=ASSET001"
        )
        with patch.object(
                controller, "_object_record", return_value={"code": "ASSET001"}
        ), patch.object(
                controller, "_build_process_choices", return_value=[]
        ), patch.object(controller, "refresh"), patch.object(
                controller, "_refresh_process_counts"):
            controller._selection_changed()
        self.assertTrue(controller.hasTarget)

    def test_empty_process_projects_the_shared_quick_task_into_inspector(self):
        application = _Application()
        application.workspace_state._selected_sobject = _SObject(
            {"code": "ASSET001"}, "asset/asset?code=ASSET001"
        )
        controller = CommunicationController(application)
        controller._process = "publish"
        begin_create = Mock()
        controller._tasks_controller = SimpleNamespace(
            task_inspector_process_record=lambda process: {
                "process": process,
                "processRow": 3,
                "hasTask": False,
                "currentTaskCode": "",
                "assigned": "artist",
                "assignedLabel": "Artist",
                "status": "Ready",
            },
            begin_create_for_process=begin_create,
        )

        task = controller.currentTask

        self.assertEqual(task["code"], "")
        self.assertEqual(task["process"], "publish")
        self.assertEqual(task["processRow"], 3)
        self.assertEqual(task["assignedDisplay"], "Artist")
        controller.create_task_for_process()
        begin_create.assert_called_once_with(3)

    def test_note_focus_remains_pending_until_the_view_acknowledges_it(self):
        application = _Application()
        with patch(
            "thlib.ui.communication.env_read_config", return_value={}
        ):
            controller = CommunicationController(application)
        note_key = "skey://sthpw/note?code=NOTE001"
        application.workspace_state.note_model.replace([{
            "noteId": "NOTE001",
            "searchKey": note_key,
        }])
        focused = QSignalSpy(controller.noteFocusRequested)

        self.assertTrue(controller.show_note(note_key))

        self.assertEqual(controller.pendingNoteFocus, note_key)
        self.assertEqual(focused.count(), 1)
        controller.acknowledge_note_focus(note_key)
        self.assertEqual(controller.pendingNoteFocus, "")

    def test_task_activation_refreshes_a_new_task_context(self):
        application = _Application()
        target = _SObject(
            {"code": "ASSET001"}, "asset/asset?code=ASSET001"
        )
        first = _Task({"code": "TASK001", "process": "model"}, [])
        second = _Task({"code": "TASK002", "process": "model"}, [])
        controller = CommunicationController(application)
        application.workspace_state._selected_sobject = target
        controller._visible = True
        controller._process = "model"
        controller._process_tasks = [first, second]
        controller._selected_task_code = "TASK001"
        controller._loaded_task_context = (
            target.get_search_key(), "model", "TASK001"
        )
        controller._task_expanded = False

        with patch.object(controller, "refresh") as refresh, patch(
            "thlib.ui.communication.env_write_config"
        ):
            controller.activate_task_context(
                "TASK002", target.get_search_key(), "model"
            )

        self.assertEqual(controller.selectedTaskCode, "TASK002")
        self.assertFalse(controller.taskExpanded)
        refresh.assert_called_once_with()

    def test_task_activation_reuses_an_already_loaded_context(self):
        application = _Application()
        target = _SObject(
            {"code": "ASSET001"}, "asset/asset?code=ASSET001"
        )
        task = _Task({"code": "TASK001", "process": "model"}, [])
        controller = CommunicationController(application)
        application.workspace_state._selected_sobject = target
        controller._visible = True
        controller._process = "model"
        controller._process_tasks = [task]
        controller._selected_task_code = "TASK001"
        controller._loaded_task_context = (
            target.get_search_key(), "model", "TASK001"
        )

        with patch.object(controller, "refresh") as refresh:
            controller.activate_task_context(
                "TASK001", target.get_search_key(), "model"
            )

        refresh.assert_not_called()

    def test_task_activation_follows_a_different_parent_into_inspector(self):
        application = _Application()
        old_target = _SObject(
            {"code": "ASSET001"}, "asset/asset?code=ASSET001"
        )
        new_target = _SObject(
            {"code": "ASSET002"}, "asset/asset?code=ASSET002"
        )
        selected_task = _Task(
            {"code": "TASK002", "process": "model", "assigned": "artist"},
            [],
        )
        controller = CommunicationController(application)
        application.workspace_state._selected_sobject = old_target
        controller._visible = True
        controller._task_expanded = False

        with patch("thlib.ui.communication.env_write_config"):
            controller.activate_task_context(
                "TASK002", new_target.get_search_key(), "model"
            )

        application.workspace_state._selected_sobject = new_target
        application.workspace_state._task_sobjects = [selected_task]
        application.workspace_state._note_sobjects = []
        application.workspace_state._notes_loaded = True
        application.workspace_state._notes_process = "model"
        with patch.object(
            controller, "_object_record", return_value={"code": "ASSET002"}
        ), patch.object(
            controller,
            "_build_process_choices",
            return_value=[{
                "label": "Model", "value": "model", "type": "",
                "color": "", "count": 0,
            }],
        ), patch.object(controller, "_refresh_process_counts"):
            controller._selection_changed()

        self.assertEqual(controller.selectedTaskCode, "TASK002")
        self.assertEqual(controller.currentTask["code"], "TASK002")
        self.assertEqual(controller.currentTask["process"], "model")
        self.assertFalse(controller.taskExpanded)

    def test_task_inspector_reuses_selected_result_preview(self):
        application = _Application()
        application.workspace_model = _WorkspacePreviewModel(
            "pending-preview:42"
        )
        controller = CommunicationController(application)
        stype = SimpleNamespace(
            get_pretty_name=lambda: "Asset",
            get_code=lambda: "demo/asset",
        )
        sobject = SimpleNamespace(
            get_info=lambda: {"code": "ASSET001"},
            get_title=lambda: "Hero asset",
            get_stype=lambda: stype,
            get_search_key=lambda: "demo/asset?code=ASSET001",
        )

        controller._selected_object = controller._object_record(sobject)
        self.assertEqual(
            controller.selectedObject["previewUrl"], "pending-preview:42"
        )

        changes = []
        controller.stateChanged.connect(lambda: changes.append(True))
        application.workspace_model.preview_url = "file:///preview.png"
        application.workspace_model.dataChanged.emit(None, None, [])
        self.assertEqual(
            controller.selectedObject["previewUrl"], "file:///preview.png"
        )
        self.assertEqual(len(changes), 1)

    def test_history_merges_notes_and_task_status(self):
        application = _Application()
        controller = CommunicationController(application)
        note = _SObject({
            "code": "NOTE001", "login": "artist", "note": "Ready",
            "process": "publish", "timestamp": "2026-08-02 10:02:00",
        }, "sthpw/note?code=NOTE001")
        status = _SObject({
            "code": "LOG001", "login": "artist", "from_status": "In Progress",
            "to_status": "Complete", "timestamp": "2026-08-02 10:01:00",
        }, "sthpw/status_log?code=LOG001")
        task = _Task({"process": "publish", "pipeline_code": "task"}, [status])
        controller._request_id = "request"
        controller._history_ready(
            "request", ({"TASK001": task}, {"NOTE001": note})
        )
        records = application.workspace_state.note_model._records
        self.assertEqual([record["entryType"] for record in records], ["status", "note"])
        self.assertEqual(records[0]["statusTo"], "Complete")
        self.assertEqual(records[0]["statusColor"], "#ffffff")
        self.assertEqual(records[1]["body"], "Ready")
        self.assertTrue(records[1]["authorColor"].startswith("#"))

    def test_status_timeline_connects_only_adjacent_status_entries(self):
        application = _Application()
        controller = CommunicationController(application)
        note = _SObject({
            "code": "NOTE001", "login": "artist", "note": "Pause",
            "process": "publish", "timestamp": "2026-08-02 10:02:00",
        }, "sthpw/note?code=NOTE001")
        statuses = [
            _SObject({
                "code": "LOG001", "login": "artist",
                "to_status": "Assigned", "timestamp": "2026-08-02 10:00:00",
            }, "sthpw/status_log?code=LOG001"),
            _SObject({
                "code": "LOG002", "login": "artist",
                "to_status": "In Progress", "timestamp": "2026-08-02 10:01:00",
            }, "sthpw/status_log?code=LOG002"),
            _SObject({
                "code": "LOG003", "login": "artist",
                "to_status": "Complete", "timestamp": "2026-08-02 10:03:00",
            }, "sthpw/status_log?code=LOG003"),
        ]
        task = _Task({"process": "publish", "pipeline_code": "task"}, statuses)
        controller._request_id = "request"
        controller._history_ready(
            "request", ({"TASK001": task}, {"NOTE001": note})
        )

        records = application.workspace_state.note_model._records
        self.assertEqual(
            [record["entryType"] for record in records],
            ["status", "status", "note", "status"],
        )
        self.assertEqual(
            [(record["statusTimelineBefore"],
              record["statusTimelineAfter"]) for record in records],
            [(False, True), (True, False), (False, False), (False, False)],
        )

    def test_task_selection_keeps_notes_and_uses_only_selected_history(self):
        application = _Application()
        controller = CommunicationController(application)
        application.workspace_state._selected_sobject = _SObject(
            {"code": "ASSET001"}, "asset/asset?code=ASSET001"
        )
        note = _SObject({
            "code": "NOTE001", "login": "artist", "note": "Shared note",
            "process": "publish", "timestamp": "2026-08-02 10:02:00",
        }, "sthpw/note?code=NOTE001")
        task_note = _SObject({
            "code": "NOTE002", "login": "lead", "note": "Task branch",
            "process": "publish", "timestamp": "2026-08-02 10:03:00",
            "search_type": "sthpw/task?project=demo",
            "search_code": "TASK002",
        }, "sthpw/note?code=NOTE002")
        first_status = _SObject({
            "code": "LOG001", "login": "artist",
            "to_status": "In Progress", "timestamp": "2026-08-02 10:00:00",
        }, "sthpw/status_log?code=LOG001")
        second_status = _SObject({
            "code": "LOG002", "login": "lead",
            "to_status": "Review", "timestamp": "2026-08-02 10:01:00",
        }, "sthpw/status_log?code=LOG002")
        first = _Task({
            "code": "TASK001", "process": "publish", "assigned": "artist",
        }, [first_status])
        second = _Task({
            "code": "TASK002", "process": "publish", "assigned": "lead",
        }, [second_status])
        first.set_notes_count("publish", 1)
        second.set_notes_count("publish", 1)
        controller._request_id = "request"
        branch_counts = []
        controller.taskNoteCountsChanged.connect(
            lambda parent_key, process, counts, _codes: branch_counts.append(
                (parent_key, process, dict(counts or {}))
            )
        )

        with patch("thlib.environment.env_server.get_user", return_value="artist"):
            controller._history_ready(
                "request", (
                    {"TASK001": first, "TASK002": second},
                    {"NOTE001": note, "NOTE002": task_note},
                )
            )
            self.assertEqual(controller.selectedTaskCode, "TASK001")
            self.assertEqual(controller.currentTask["taskCount"], 2)
            self.assertEqual(
                [record["statusTo"] for record in application.workspace_state.note_model._records
                 if record["entryType"] == "status"],
                ["In Progress"],
            )

            controller.select_task("TASK002")

        records = application.workspace_state.note_model._records
        self.assertEqual(controller.selectedTaskCode, "TASK002")
        self.assertEqual(
            [record["body"] for record in records if record["entryType"] == "note"],
            ["Task branch"],
        )
        self.assertEqual(
            [record["statusTo"] for record in records if record["entryType"] == "status"],
            ["Review"],
        )
        controller.select_task("TASK001")
        self.assertEqual(
            [record["body"] for record in application.workspace_state.note_model._records
             if record["entryType"] == "note"],
            ["Shared note"],
        )
        self.assertEqual(branch_counts[-1], (
            application.workspace_state._selected_sobject.get_search_key(),
            "publish", {"TASK001": 1, "TASK002": 1},
        ))

    def test_workspace_task_activation_selects_matching_notes_task(self):
        application = _Application()
        controller = CommunicationController(application)
        selected = _SObject(
            {"code": "ASSET001"}, "asset/asset?code=ASSET001"
        )
        application.workspace_state._selected_sobject = selected
        first = _Task({"code": "TASK001", "process": "publish"}, [])
        second = _Task({"code": "TASK002", "process": "publish"}, [])
        controller._process = "publish"
        controller._process_tasks = [first, second]
        controller._selected_task_code = "TASK001"

        controller.select_task_context(
            selected.get_search_key(), "publish", "TASK002"
        )

        self.assertEqual(controller.selectedTaskCode, "TASK002")
        controller.select_task_context(
            "asset/asset?code=OTHER", "publish", "TASK001"
        )
        self.assertEqual(controller.selectedTaskCode, "TASK002")
        self.assertEqual(
            controller._preferred_tasks[
                ("asset/asset?code=OTHER", "publish")
            ],
            "TASK001",
        )

    def test_task_activation_adapter_preserves_signal_argument_order(self):
        application = _Application()
        controller = CommunicationController(application)
        selected = _SObject(
            {"code": "ASSET001"}, "asset/asset?code=ASSET001"
        )
        application.workspace_state._selected_sobject = selected
        first = _Task({"code": "TASK001", "process": "publish"}, [])
        second = _Task({"code": "TASK002", "process": "publish"}, [])
        controller._process = "publish"
        controller._process_tasks = [first, second]
        controller._selected_task_code = "TASK001"

        controller.activate_task_context(
            "TASK002", selected.get_search_key(), "publish"
        )

        self.assertEqual(controller.selectedTaskCode, "TASK002")

    def test_selected_process_task_survives_local_history_rebuild(self):
        application = _Application()
        controller = CommunicationController(application)
        application.workspace_state._selected_sobject = _SObject(
            {"code": "ASSET001"}, "asset/asset?code=ASSET001"
        )
        tasks = {
            "TASK001": _Task({
                "code": "TASK001", "process": "publish", "assigned": "artist",
            }, []),
            "TASK002": _Task({
                "code": "TASK002", "process": "publish", "assigned": "lead",
            }, []),
        }
        controller._request_id = "first"
        controller._history_ready("first", (tasks, {}))
        controller.select_task("TASK002")
        controller._request_id = "second"

        controller._history_ready("second", (tasks, {}))

        self.assertEqual(controller.selectedTaskCode, "TASK002")

    def test_status_color_comes_from_task_pipeline(self):
        application = _Application()
        controller = CommunicationController(application)
        pipeline = SimpleNamespace(
            get_pipeline_process=lambda status: {
                "process": status, "color": "#2f7d4a"
            }
        )
        workflow = SimpleNamespace(
            get_by_stype_code=lambda code: {"task_pipeline": pipeline}
            if code == "sthpw/task" else {}
        )
        stype = SimpleNamespace(get_workflow=lambda: workflow)
        selected = _SObject({}, "asset/asset?code=ASSET001")
        selected.get_stype = lambda: stype
        application.workspace_state._selected_sobject = selected
        task = _Task({"pipeline_code": "task_pipeline"}, [])

        self.assertEqual(controller._status_color(task, "Complete"), "#2f7d4a")

    def test_snapshot_search_key_is_a_navigation_link(self):
        application = _Application()
        controller = CommunicationController(application)
        value = "skey://sthpw/snapshot?code=SNAP001"
        self.assertIn('href="{0}"'.format(value), controller._display_html(value))
        controller.open_link(value)
        self.assertEqual(application.opened_search_key, value)

    def test_snapshot_search_key_selects_exact_snapshot(self):
        sobject = _SObject({}, "asset/shot?code=SHOT001")
        sobject.get_tasks_sobjects = (
            lambda process=None, include_status_log=False: ({},)
        )
        sobject.get_notes_sobjects = lambda process=None: ({},)
        wanted = SimpleNamespace(
            code="SNAP002", node_id="snapshot-2", is_versionless=False,
            process="publish", context="publish/main", source=object(),
        )
        other = SimpleNamespace(
            code="SNAP001", node_id="snapshot-1", is_versionless=False,
            process="publish", context="publish/main", source=object(),
        )
        result = _SnapshotDetails(sobject, [other, wanted])._prepare_sobject_details(
            sobject.get_search_key(), process="publish", snapshot_code="SNAP002"
        )
        self.assertEqual(result[3], [wanted])

    def test_restored_sobject_details_include_task_status_history(self):
        sobject = _SObject({}, "asset/shot?code=SHOT001")
        requests = []

        def task_query(process=None, include_status_log=False):
            requests.append((process, include_status_log))
            return ({},)

        sobject.get_tasks_sobjects = task_query
        sobject.get_notes_sobjects = lambda process=None: ({},)

        _SnapshotDetails(sobject, [])._prepare_sobject_details(
            sobject.get_search_key()
        )

        self.assertEqual(requests, [(None, True)])

    def test_attachment_context_has_no_request_directory(self):
        payload = AttachmentUploadController._target_payload(
            "asset/shot?code=SHOT001",
            "attachment/publish",
            "Note attachment",
            {"path": "C:/files/checkin_out.txt", "fileType": "file"},
        )
        self.assertEqual(payload["context"], "attachment/publish/checkin_out")

    def test_named_attachment_uses_owner_code_for_tactic_filename(self):
        payload = AttachmentUploadController._target_payload(
            "demo/th_knowledge_article?code=DOC0002",
            "attachment/knowledge",
            "Knowledge Base attachment",
            {
                "path": "C:/files/статья.png",
                "fileType": "preview",
                "token": "attachment001",
            },
            "DOC0002",
        )

        self.assertEqual(
            payload["explicitFilename"], "DOC0002_attachment001"
        )
        self.assertEqual(
            payload["filesDict"][0][0], "DOC0002_attachment001"
        )
        self.assertNotIn("статья", repr(payload["filesDict"]))

    def test_chat_attachment_context_does_not_repeat_conversation_code(self):
        payload = AttachmentUploadController._payload(
            "CHAT001",
            {"path": "C:/files/image.png", "fileType": "preview"},
            "request-1",
        )
        self.assertEqual(payload["context"], "attachment/chat/image")
        self.assertNotIn("CHAT001", payload["context"])

    def test_message_attachments_use_stable_unique_batch_context_and_names(self):
        batch_token = "a" * 32
        controller = SimpleNamespace(
            model=SimpleNamespace(_records=[
                {"token": batch_token, "path": "C:/files/image.png"},
                {"token": "b" * 32, "path": "C:/other/image.png"},
            ]),
            begin_named_target=Mock(return_value=True),
        )

        self.assertTrue(ChatAttachmentController.begin(controller, "CHAT001"))
        self.assertTrue(ChatAttachmentController.begin(controller, "CHAT001"))

        self.assertEqual(controller.begin_named_target.call_count, 2)
        first = controller.begin_named_target.call_args_list[0]
        self.assertEqual(first, controller.begin_named_target.call_args_list[1])
        self.assertEqual(first.args[0], "sthpw/message?code=CHAT001")
        self.assertEqual(
            first.args[1], "attachment/chat/CHAT001/" + batch_token
        )
        self.assertEqual(first.args[3], "CHAT001")
        filenames = [
            AttachmentUploadController._target_payload(
                first.args[0], first.args[1], first.args[2], record,
                first.args[3],
            )["explicitFilename"]
            for record in controller.model._records
        ]
        self.assertEqual(filenames, [
            "CHAT001_" + batch_token, "CHAT001_" + "b" * 32,
        ])
        controller.model._records = [
            {"token": "c" * 32, "path": "C:/files/image.png"}
        ]
        ChatAttachmentController.begin(controller, "CHAT001")
        self.assertNotEqual(
            controller.begin_named_target.call_args.args[1], first.args[1]
        )
        controller.model._records = [
            {"token": "../unsafe", "path": "C:/files/image.png"}
        ]
        controller.stateChanged = SimpleNamespace(emit=Mock())
        self.assertFalse(ChatAttachmentController.begin(controller, "CHAT001"))
        self.assertEqual(controller.begin_named_target.call_count, 3)

    def test_attachment_collision_retries_once_with_next_version(self):
        controller = SimpleNamespace(
            _cancel=threading.Event(),
            _target_payload=AttachmentUploadController._target_payload,
        )
        calls = []

        def execute(
            payload, _repository, progress_signal=None, cancel_event=None
        ):
            calls.append(dict(payload))
            if len(calls) == 1:
                raise RuntimeError(
                    "This path [/repo/image_attachment_v001.png] already exists"
                )
            return {"__search_key__": "sthpw/snapshot?code=SNAP002"}

        with patch(
                "thlib.checkin_operation.execute_checkin_payload",
                side_effect=execute):
            result = AttachmentUploadController._upload_all(
                controller,
                "sthpw/message?code=CHAT001",
                "attachment/chat",
                "Chat attachment",
                [{
                    "token": "file-1", "title": "image.png",
                    "path": "C:/files/image.png", "fileType": "preview",
                }],
                {},
                "sthpw/message?code=CHAT001\nattachment/chat",
                {},
            )

        self.assertEqual(calls[0]["version"], None)
        self.assertEqual(calls[1]["version"], 2)
        self.assertEqual(
            result["snapshots"]["file-1"],
            "sthpw/snapshot?code=SNAP002",
        )

    def test_attachment_collision_advances_until_free_version(self):
        controller = SimpleNamespace(
            _cancel=threading.Event(),
            _target_payload=AttachmentUploadController._target_payload,
        )
        versions = []

        def execute(
            payload, _repository, progress_signal=None, cancel_event=None
        ):
            versions.append(payload.get("version"))
            if len(versions) < 3:
                version = len(versions)
                raise RuntimeError(
                    "This path [/repo/image_attachment_v{0:03d}.png] "
                    "already exists".format(version)
                )
            return {"__search_key__": "sthpw/snapshot?code=SNAP003"}

        with patch(
                "thlib.checkin_operation.execute_checkin_payload",
                side_effect=execute):
            result = AttachmentUploadController._upload_all(
                controller,
                "sthpw/message?code=CHAT001",
                "attachment/chat",
                "Chat attachment",
                [{
                    "token": "file-1", "title": "image.png",
                    "path": "C:/files/image.png", "fileType": "preview",
                }],
                {},
                "sthpw/message?code=CHAT001\nattachment/chat",
                {},
            )

        self.assertEqual(versions, [None, 2, 3])
        self.assertEqual(
            result["snapshots"]["file-1"],
            "sthpw/snapshot?code=SNAP003",
        )

    def test_note_process_choices_come_from_sobject_pipeline(self):
        application = _Application()
        controller = CommunicationController(application)
        pipeline = SimpleNamespace(
            get_all_pipeline_names=lambda: ["model", "render"],
            get_process_info=lambda name: {
                "type": "manual", "color": "#123456",
            },
            get_process_label=lambda name: {
                "model": "Modeling", "render": "Rendering",
            }[name],
        )
        stype = SimpleNamespace(get_pipeline=lambda: {"asset": pipeline})
        sobject = _SObject({}, "asset/asset?code=ASSET001")
        sobject.note_counts = {"model": 3, "render": 1}
        sobject.get_stype = lambda: stype
        sobject.get_pipeline_code = lambda: "asset"
        with patch(
                "thlib.global_functions.get_value_from_config",
                return_value=0):
            choices = controller._build_process_choices(sobject)
        values = [choice["value"] for choice in choices]
        self.assertEqual(values[:2], ["model", "render"])
        self.assertNotIn("publish", values)
        self.assertEqual(choices[0]["label"], "Modeling")
        self.assertEqual(choices[0]["count"], 3)
        with patch(
                "thlib.global_functions.get_value_from_config",
                return_value=1):
            visible_builtins = controller._build_process_choices(sobject)
        self.assertIn("publish", [
            choice["value"] for choice in visible_builtins
        ])
        attachment = next(
            choice for choice in visible_builtins
            if choice["value"] == "attachment"
        )
        self.assertEqual(attachment["label"], "Attachment")
        self.assertEqual(attachment["type"], "built-in")

    def test_note_process_choice_uses_pipeline_process_color(self):
        application = _Application()
        controller = CommunicationController(application)
        pipeline = SimpleNamespace(
            get_all_pipeline_names=lambda: ["rig"],
            get_process_info=lambda _name: {"type": "manual"},
            get_pipeline_process=lambda _name: {"color": "#5966d9"},
            get_process_label=lambda _name: "Rig",
        )
        stype = SimpleNamespace(get_pipeline=lambda: {"asset": pipeline})
        sobject = _SObject({}, "asset/asset?code=ASSET001")
        sobject.get_stype = lambda: stype
        sobject.get_pipeline_code = lambda: "asset"

        with patch(
                "thlib.global_functions.get_value_from_config",
                return_value=0):
            choices = controller._build_process_choices(sobject)

        self.assertEqual(choices[0]["color"], "#5966d9")

    def test_progress_choice_keeps_completion_counts(self):
        application = _Application()
        controller = CommunicationController(application)
        pipeline = SimpleNamespace(
            get_all_pipeline_names=lambda: ["assets_progress"],
            get_process_info=lambda _name: {"type": "progress"},
            get_pipeline_process=lambda _name: {},
            get_process_label=lambda _name: "Assets progress",
        )
        sobject = _SObject({}, "project/episode?code=EP001")
        sobject.get_stype = lambda: SimpleNamespace(
            get_pipeline=lambda: {"episode": pipeline}
        )
        sobject.get_pipeline_code = lambda: "episode"
        sobject.get_progress_count = lambda _name, kind: (
            2 if kind == "approved_count" else 3
        )

        choices = controller._build_process_choices(sobject)

        self.assertEqual(choices[0]["type"], "progress")
        self.assertEqual((choices[0]["approved"], choices[0]["total"]), (2, 3))

    def test_progress_tasks_require_real_schema_relationship(self):
        child_type = SimpleNamespace(
            get_code=lambda: "project/asset",
            get_schema=lambda: SimpleNamespace(
                get_parent=lambda _parent, _child: None
            ),
        )
        schema = SimpleNamespace(get_child=lambda _child, _parent: None)
        pipeline = SimpleNamespace(
            get_process_info=lambda _name: {"type": "progress"},
            get_pipeline_process=lambda _name: {
                "workflow": {"search_type": "project/asset"}
            },
        )
        stype = SimpleNamespace(
            get_code=lambda: "project/episode",
            get_schema=lambda: schema,
            get_pipeline=lambda: {"episode": pipeline},
        )
        project = SimpleNamespace(get_search_type=lambda _code: child_type)
        sobject = SimpleNamespace(
            get_stype=lambda: stype,
            get_pipeline_code=lambda: "episode",
            get_project=lambda: project,
            get_related_sobjects=Mock(side_effect=AssertionError(
                "must not guess a relationship"
            )),
        )

        result = CommunicationController._load_related_tasks(
            sobject, "assets_progress"
        )

        self.assertEqual(result["state"], "unrelated")
        sobject.get_related_sobjects.assert_not_called()

    def test_progress_tasks_show_tasks_of_related_objects(self):
        child_type = SimpleNamespace(get_code=lambda: "project/asset")
        pipeline = SimpleNamespace(
            get_process_info=lambda _name: {"type": "progress"},
            get_pipeline_process=lambda _name: {
                "workflow": {"search_type": "project/asset"}
            },
        )
        stype = SimpleNamespace(
            get_code=lambda: "project/episode",
            get_schema=lambda: SimpleNamespace(
                get_child=lambda _child, _parent: {"relationship": "code"}
            ),
            get_pipeline=lambda: {"episode": pipeline},
        )
        project = SimpleNamespace(
            get_search_type=lambda _code: child_type,
            get_code=lambda: "project",
        )
        child = SimpleNamespace(
            get_code=lambda: "ASSET001",
            get_title=lambda: "Hero",
            get_search_key=lambda: "project/asset?code=ASSET001",
        )
        sobject = SimpleNamespace(
            get_stype=lambda: stype,
            get_pipeline_code=lambda: "episode",
            get_project=lambda: project,
            get_related_sobjects=lambda _stype, path: ({"child": child}, {}),
        )
        task = SimpleNamespace(get_info=lambda: {
            "search_code": "ASSET001", "search_type": "project/asset",
            "process": "model", "status": "Ready", "assigned": "artist",
        })
        with patch("thlib.tactic_classes.get_sobjects", return_value=(
            {"task": task}, {}
        )) as query:
            result = CommunicationController._load_related_tasks(
                sobject, "assets_progress"
            )

        self.assertEqual(result["objectCount"], 1)
        self.assertEqual(result["items"][0]["parentTitle"], "Hero")
        self.assertEqual(result["items"][0]["process"], "model")
        self.assertEqual(
            result["parentKeys"], ["project/asset?code=ASSET001"]
        )
        self.assertEqual(query.call_count, 1)

        stype.get_schema = lambda: SimpleNamespace(
            get_child=lambda _child, _parent: None
        )
        child_type.get_schema = lambda: SimpleNamespace(
            get_parent=lambda _parent, _child: {"relationship": "code"}
        )
        paths = []
        sobject.get_related_sobjects = lambda _stype, path: (
            paths.append(path) or {"parent": child}, {}
        )
        with patch("thlib.tactic_classes.get_sobjects", return_value=(
            {"task": task}, {}
        )):
            CommunicationController._load_related_tasks(
                sobject, "assets_progress"
            )
        self.assertEqual(paths, ["parent"])

    def test_stale_progress_tasks_do_not_change_task_manager_scope(self):
        controller = CommunicationController(_Application())
        tasks = Mock()
        controller._tasks_controller = tasks
        controller._related_tasks_request_id = "current"
        result = {
            "state": "ready", "items": [], "objectCount": 1,
            "parentKeys": ["project/asset?code=ASSET001"],
        }

        controller._related_tasks_ready("stale", result)
        tasks.use_related_objects.assert_not_called()
        controller._related_tasks_ready("current", result)
        tasks.use_related_objects.assert_called_once_with(
            ["project/asset?code=ASSET001"]
        )

    def test_note_process_counts_update_menu_data(self):
        application = _Application()
        controller = CommunicationController(application)
        sobject = _SObject({}, "asset/asset?code=ASSET001")
        controller._process_choices = [
            {"value": "model", "label": "Modeling", "count": 0},
            {"value": "render", "label": "Rendering", "count": 0},
        ]
        controller._process_count_request_id = "counts"

        controller._process_counts_ready(
            "counts", sobject, {"notes": {"model": 4, "render": 2}}
        )

        self.assertEqual(
            [choice["count"] for choice in controller.processChoices], [4, 2]
        )
        self.assertEqual(sobject.get_notes_count("render"), 2)

    def test_selecting_main_sobject_uses_publish_notes(self):
        node = SimpleNamespace(
            node_id="sobject-1", node_type="sobject", parent_id="",
            search_key="asset/asset?code=ASSET001", process="",
        )
        harness = _SelectionHarness(node)

        harness._load_selected_details(node.node_id, node.search_key)

        self.assertEqual(harness.loaded[0], node.search_key)
        self.assertEqual(harness.loaded[1], "publish")

    def test_selecting_related_sobject_uses_its_own_details(self):
        root = SimpleNamespace(
            node_id="root", node_type="sobject", parent_id="",
            search_key="asset/asset?code=ASSET001", process="",
        )
        relation = SimpleNamespace(
            node_id="relation", node_type="relation", parent_id="root",
            search_key=root.search_key, process="",
        )
        related = SimpleNamespace(
            node_id="related", node_type="sobject", parent_id="relation",
            search_key="asset/shot?code=SHOT001", process="",
        )
        harness = _SelectionHarness(
            related,
            {item.node_id: item for item in (root, relation, related)},
        )

        harness._load_selected_details(
            related.node_id, related.search_key
        )

        self.assertEqual(harness.loaded[0], related.search_key)
        self.assertEqual(harness.loaded[1], "publish")

    def test_selecting_related_process_uses_nearest_sobject(self):
        root = SimpleNamespace(
            node_id="root", node_type="sobject", parent_id="",
            search_key="asset/asset?code=ASSET001", process="",
        )
        relation = SimpleNamespace(
            node_id="relation", node_type="relation", parent_id="root",
            search_key=root.search_key, process="",
        )
        related = SimpleNamespace(
            node_id="related", node_type="sobject", parent_id="relation",
            search_key="asset/shot?code=SHOT001", process="",
        )
        process = SimpleNamespace(
            node_id="process", node_type="process", parent_id="related",
            search_key=related.search_key, process="animation",
        )
        harness = _SelectionHarness(
            process,
            {
                item.node_id: item
                for item in (root, relation, related, process)
            },
        )

        harness._load_selected_details(
            process.node_id, process.search_key
        )

        self.assertEqual(harness.loaded[0], related.search_key)
        self.assertEqual(harness.loaded[1], "animation")

    def test_mouse_selection_loads_details_without_global_loading_state(self):
        node = SimpleNamespace(
            node_id="sobject-1", node_type="sobject", parent_id="",
            search_key="asset/asset?code=ASSET001", process="",
        )
        harness = _SelectionHarness(node)
        harness.tab.view_mode = "compact"
        harness._pending_selection_load = (
            node.node_id, node.search_key, node.node_type
        )
        stale_cancellations = []
        harness._detail_worker = SimpleNamespace(
            cancel=lambda: stale_cancellations.append(True)
        )
        harness._task_snapshot_source = None
        harness._task_snapshot_identity = ("", "", "")
        harness._versions_request_id = ""
        harness._selected_detail_key = ""
        harness._selected_detail_process = ""
        harness._selected_detail_snapshot_node_id = ""
        harness._detail_request_id = ""
        harness.debug_log = None
        harness.loading_calls = []
        harness._set_loading = lambda *args: harness.loading_calls.append(args)

        class Worker:
            def __init__(self):
                self.result = SignalStub()
                self.error = SignalStub()
                self.settled = SignalStub()
                self.started = False
                self.metadata = None

            def add_result_data(self, metadata):
                self.metadata = metadata

            def get_result_data(self):
                return self.metadata

            def start(self):
                self.started = True

        worker = Worker()
        pool = SimpleNamespace(
            is_stopped=False,
            add_task=lambda *_args: worker,
        )
        from thlib.environment import env_inst

        with patch.object(env_inst, "server_pool", pool):
            harness._flush_selected_loads()

        self.assertEqual(stale_cancellations, [True])
        self.assertTrue(worker.started)
        self.assertEqual(harness.loading_calls, [])

        harness._async_selected_payload_result((
            [],
            (None, [], [], []),
            worker.metadata,
        ))
        self.assertEqual(harness.loading_calls, [])

        harness._detail_worker = worker
        harness._report_error_payload = lambda *_args: None
        harness._notify = lambda *_args: None
        harness._async_selected_payload_error((
            {"exception": RuntimeError("details failed")},
            worker,
        ))
        self.assertEqual(harness.loading_calls, [])

    def test_existing_note_can_be_edited(self):
        import thlib.tactic_classes as tc
        application = _Application()
        controller = CommunicationController(application)
        from thlib.environment import env_server
        author = str(env_server.get_user() or "artist")
        note = _SObject({
            "note": "Before", "login": author,
            "timestamp": datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }, "sthpw/note?code=NOTE001")
        application.workspace_state.note_model.replace([{
            "searchKey": note.get_search_key(), "body": "Before",
            "entryType": "note", "canEdit": True,
        }])
        controller._notes[note.get_search_key()] = note
        controller._run = lambda callback, clear_composer=False: callback()
        with patch.object(env_server, "get_user", return_value=author), patch.object(
                tc, "change_note", return_value={"edited": True}) as change_note:
            self.assertTrue(controller.edit(0, "After"))
        change_note.assert_called_once_with(
            note.get_search_key(), "edit", "After", project_code=None
        )

    def test_message_menu_uses_live_permission_from_controller(self):
        from thlib.environment import env_server
        from thlib.ui.communication_feed import MessagesController

        class MessageApplication(_Application):
            project_changed = Signal(str, str)

        application = MessageApplication()
        controller = MessagesController(application)
        controller.load = Mock()
        controller.set_visible = Mock()
        controller.messages.replace([{
            "messageId": "MSG001", "sender": "artist", "body": "Hello",
            "timestamp": datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }])
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        engine.addImportPath(str(qml_dir))
        context = engine.rootContext()
        context.setContextProperty("messagesController", controller)
        context.setContextProperty("messageConversationModel", controller.conversations)
        context.setContextProperty("messageSurfaceModel", controller.message_surfaces)
        context.setContextProperty("userController", QObject())
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "MessagesView.qml"))
        )
        view = component.createWithInitialProperties({
            "theme": theme, "width": 1100, "height": 700,
        })
        self.assertIsNotNone(
            view, "\n".join(error.toString() for error in component.errors())
        )
        try:
            with patch.object(env_server, "get_user", return_value="artist"):
                view.prepareMessageActions({
                    "messageId": "MSG001", "body": "Hello",
                    "pinned": False, "editHistory": [],
                }, None)
                self.assertTrue(view.property("actionMessageCanEdit"))
                self.assertTrue(view.property("actionMessageCanDelete"))
                actions = view.property("timelineActions").property(
                    "displayedActions"
                ).toVariant()
                visible_titles = [
                    action.get("title") for action in actions
                    if action.get("visible") is not False
                ]
                self.assertIn("Edit message", visible_titles)
                self.assertIn("Delete message", visible_titles)
                controller.messages.set_value(
                    0, "timestamp",
                    (datetime.now(timezone.utc) - timedelta(hours=2))
                        .strftime("%Y-%m-%d %H:%M:%S"),
                )
                view.prepareMessageActions({
                    "messageId": "MSG001", "body": "Hello",
                    "pinned": False, "editHistory": [],
                }, None)
                self.assertFalse(view.property("actionMessageCanEdit"))
                self.assertFalse(view.property("actionMessageCanDelete"))
                actions = view.property("timelineActions").property(
                    "displayedActions"
                ).toVariant()
                visible_titles = [
                    action.get("title") for action in actions
                    if action.get("visible") is not False
                ]
                self.assertNotIn("Edit message", visible_titles)
                self.assertNotIn("Delete message", visible_titles)
        finally:
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_message_text_has_compact_header_gap_and_side_padding(self):
        from thlib.ui.communication_feed import MessagesController

        class MessageApplication(_Application):
            project_changed = Signal(str, str)

        application = MessageApplication()
        controller = MessagesController(application)
        controller.load = Mock()
        controller.set_visible = Mock()
        controller._initialized = True
        controller._conversation_id = "CHAT001"
        controller.conversations.replace([{
            "conversationId": "CHAT001", "title": "Notes",
            "isPersonalNotes": True, "messageCount": 1,
        }])
        controller.messages.replace([{
            "messageId": "MSG001", "sender": "testuser",
            "senderDisplay": "Test User", "avatarUrl": "", "initials": "TU",
            "senderColor": "#ba68c8", "body": "Админ верни ленту!",
            "bodyHtml": "Админ верни ленту!",
            "displayHtml": "Админ верни ленту!", "skeyPreviews": [],
            "timestamp": "2026-09-22 10:00:00", "timePretty": "1 min ago",
            "timeSimple": "", "isOwn": False, "unread": False,
            "attachments": [], "canEdit": False, "edited": False,
            "pinned": False, "editedBy": "", "editedAt": "",
            "editHistory": [], "replyTo": {}, "forwardedFrom": {},
            "forwardSelected": False, "reactions": [],
            "reactionPending": False, "deliveryStatus": "sent",
            "deliveryRecipientCount": 0, "deliveryDeliveredCount": 0,
            "deliveryReadCount": 0, "groupFirst": True, "groupLast": True,
        }])
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        engine.addImportPath(str(qml_dir))
        context = engine.rootContext()
        context.setContextProperty("messagesController", controller)
        context.setContextProperty("messageConversationModel", controller.conversations)
        context.setContextProperty("messageSurfaceModel", controller.message_surfaces)
        context.setContextProperty("userController", QObject())
        component = QQmlComponent(engine)
        component.setData(b'''
import QtQuick
import QtQuick.Window
import "."
Window {
    width: 920; height: 500; visible: true
    Theme { id: appTheme; dark: true; hoverAnimationsEnabled: false }
    MessagesView {
        objectName: "spacingMessagesView"
        anchors.fill: parent
        theme: appTheme
    }
}
''', QUrl.fromLocalFile(str(qml_dir / "_MessageSpacingTest.qml")))
        window = component.create()
        self.assertIsNotNone(
            window, "\n".join(error.toString() for error in component.errors())
        )
        try:
            self.assertTrue(QTest.qWaitForWindowExposed(window))
            for _pass in range(3):
                self.app.processEvents()
            pending = [window.contentItem()]
            found = {}
            while pending:
                item = pending.pop()
                if item.objectName() in (
                    "messageTimelineBubble", "messageSenderLabel",
                    "messageBodyText", "messageActionsButton",
                    "messageTimeLabel", "messagesChatHeader",
                    "chatActionsButton", "chatBusySlot",
                    "messageViewport", "messagesTimelinePane",
                ):
                    found[item.objectName()] = item
                pending.extend(item.childItems())
            bubble = found["messageTimelineBubble"]
            sender = found["messageSenderLabel"]
            body = found["messageBodyText"]
            for width, minimum_inset in ((920, 12), (520, 10)):
                window.setWidth(width)
                self.app.processEvents()
                left_inset = (
                    body.mapToScene(QPointF()).x()
                    - bubble.mapToScene(QPointF()).x()
                )
                header_gap = (
                    body.mapToScene(QPointF()).y()
                    - sender.mapToScene(QPointF(0, sender.height())).y()
                )
                self.assertGreaterEqual(header_gap, 6)
                self.assertLessEqual(header_gap, 10)
                self.assertGreaterEqual(left_inset, minimum_inset)

            window.setWidth(920)
            self.app.processEvents()
            if os.environ.get("TH_MESSAGE_SPACING_PREVIEW"):
                self.assertTrue(window.grabWindow().save(
                    os.environ["TH_MESSAGE_SPACING_PREVIEW"]
                ))
            button = found["messageActionsButton"]
            self.assertGreaterEqual(button.width(), 28)
            self.assertGreaterEqual(button.height(), 28)
            QTest.mouseMove(
                window, bubble.mapToScene(QPointF(20, 12)).toPoint()
            )
            self.app.processEvents()
            self.assertTrue(button.property("enabled"))
            if os.environ.get("TH_MESSAGE_HOVER_PREVIEW"):
                self.assertTrue(window.grabWindow().save(
                    os.environ["TH_MESSAGE_HOVER_PREVIEW"]
                ))
            QTest.mouseClick(
                window, Qt.LeftButton,
                pos=button.mapToScene(QPointF(
                    button.width() / 2, button.height() - 2
                )).toPoint(),
            )
            self.app.processEvents()
            view = window.findChild(QObject, "spacingMessagesView")
            self.assertEqual(view.property("actionMessageId"), "MSG001")

            header = found["messagesChatHeader"]
            chat_action = found["chatActionsButton"]
            busy_slot = found["chatBusySlot"]
            viewport = found["messageViewport"]
            pane = found["messagesTimelinePane"]
            for width in (920, 700):
                window.setWidth(width)
                window.grabWindow()
                self.assertAlmostEqual(
                    viewport.mapToScene(QPointF()).x(),
                    header.mapToScene(QPointF()).x(), delta=1,
                )
                self.assertAlmostEqual(
                    viewport.mapToScene(QPointF(viewport.width(), 0)).x(),
                    header.mapToScene(QPointF(header.width(), 0)).x(),
                    delta=1,
                )
                scrollbar_room = (
                    pane.mapToScene(QPointF(pane.width(), 0)).x()
                    - viewport.mapToScene(
                        QPointF(viewport.width(), 0)
                    ).x()
                )
                self.assertGreaterEqual(scrollbar_room, 9)
                self.assertLessEqual(scrollbar_room, 12)
                self.assertFalse(busy_slot.isVisible())
                idle_inset = (
                    header.mapToScene(QPointF(header.width(), 0)).x()
                    - chat_action.mapToScene(
                        QPointF(chat_action.width(), 0)
                    ).x()
                )
                self.assertLessEqual(idle_inset, 14)
                controller._busy = True
                controller.stateChanged.emit()
                window.grabWindow()
                self.assertTrue(busy_slot.isVisible())
                busy_inset = (
                    header.mapToScene(QPointF(header.width(), 0)).x()
                    - chat_action.mapToScene(
                        QPointF(chat_action.width(), 0)
                    ).x()
                )
                self.assertGreater(busy_inset, idle_inset + 20)
                controller._busy = False
                controller.stateChanged.emit()
                window.grabWindow()

            controller.messages.set_value(0, "groupFirst", False)
            controller.messages.set_value(0, "isOwn", True)
            self.app.processEvents()
            time_label = found["messageTimeLabel"]
            time_gap = (
                body.mapToScene(QPointF()).y()
                - time_label.mapToScene(QPointF(0, time_label.height())).y()
            )
            self.assertGreaterEqual(time_gap, 6)
            self.assertLessEqual(time_gap, 10)
            self.assertGreaterEqual(
                body.mapToScene(QPointF()).x()
                - bubble.mapToScene(QPointF()).x(), 12,
            )
            media_message = dict(controller.messages._records[0])
            media_message["attachments"] = [{
                "token": "wide-image", "title": "wide.png", "size": 1024,
                "extension": "PNG", "previewUrl": "", "local": True,
                "hasWebPreview": True, "snapshotCode": "SNAP001",
            }]
            controller.messages.replace([media_message])
            self.app.processEvents()
            window.grabWindow()
            frame = bubble.parentItem()
            self.assertTrue(frame.property("mediaAttachments"))
            pending = [window.contentItem()]
            attachment = None
            while pending:
                item = pending.pop()
                if item.objectName() == "messageAttachmentCard-wide-image":
                    attachment = item
                    break
                pending.extend(item.childItems())
            self.assertIsNotNone(attachment)
            self.assertAlmostEqual(bubble.width(), frame.width() * 0.7, delta=1)
            self.assertGreater(
                body.mapToScene(QPointF()).y(),
                attachment.mapToScene(QPointF()).y() + attachment.height(),
            )
        finally:
            window.close()
            window.deleteLater()
            engine.deleteLater()

    def test_empty_favorites_chat_is_visible_in_conversation_list(self):
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        engine.addImportPath(str(qml_dir))
        model = RecordListModel((
            "title", "status", "lastMessage", "lastMessageSummary",
            "lastMessageLinkedCount", "lastSender", "unread",
            "mentionCount", "selected", "avatarUrl", "initials",
            "participantCount", "memberSummary", "acronym", "colorIndex",
            "isPersonalNotes",
        ))
        model.replace([{
            "title": "Notes", "status": "", "lastMessage": "",
            "lastMessageSummary": "", "lastMessageLinkedCount": 0,
            "lastSender": "", "unread": 0, "mentionCount": 0,
            "selected": False, "avatarUrl": "", "initials": "",
            "participantCount": 1, "memberSummary": "",
            "acronym": "", "colorIndex": 0, "isPersonalNotes": True,
        }])
        engine.rootContext().setContextProperty("favoriteModel", model)
        component = QQmlComponent(engine)
        component.setData(b'''
import QtQuick
import QtQuick.Window
import "."

Window {
    width: 300
    height: 400
    visible: true
    Theme { id: appTheme; dark: true }
    MessagesConversationList {
        anchors.fill: parent
        theme: appTheme
        conversationModel: favoriteModel
    }
}
''', QUrl.fromLocalFile(str(qml_dir / "_FavoritesListTest.qml")))
        view = component.create()
        self.assertIsNotNone(
            view, "\n".join(error.toString() for error in component.errors())
        )
        try:
            self.assertTrue(QTest.qWaitForWindowExposed(view))
            for _pass in range(3):
                self.app.processEvents()
            list_view = view.findChild(QObject, "messagesConversationListView")
            self.assertEqual(list_view.property("count"), 1)
            pending = [list_view]
            visible_text = []
            while pending:
                item = pending.pop()
                if item.property("text") is not None:
                    visible_text.append(item.property("text"))
                pending.extend(item.childItems())
            self.assertIn(
                "Favorites",
                visible_text,
            )
        finally:
            view.close()
            view.deleteLater()
            engine.deleteLater()

    def test_note_menu_hides_edit_and_delete_when_not_allowed(self):
        application = _Application()
        controller = CommunicationController(application)
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        engine.addImportPath(str(qml_dir))
        context = engine.rootContext()
        context.setContextProperty("communicationController", controller)
        context.setContextProperty("noteModel", application.workspace_state.note_model)
        context.setContextProperty("noteAttachmentDraftModel", RecordListModel(()))
        context.setContextProperty("emojiCatalog", QObject())
        context.setContextProperty("tasksController", QObject())
        context.setContextProperty("userController", QObject())
        context.setContextProperty("messagesController", QObject())
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "CommunicationView.qml"))
        )
        view = component.createWithInitialProperties({
            "theme": theme, "visible": False, "width": 700, "height": 500,
        })
        self.assertIsNotNone(
            view, "\n".join(error.toString() for error in component.errors())
        )
        try:
            self.assertEqual(
                [action["title"] for action in view.messageMenuActions().toVariant()
                 if "title" in action],
                ["Copy sKey"],
            )
            view.setProperty("messageMenuCanEdit", True)
            view.setProperty("messageMenuCanDelete", True)
            self.assertEqual(
                [action["title"] for action in view.messageMenuActions().toVariant()
                 if "title" in action],
                ["Copy sKey", "Edit note", "Delete note"],
            )
        finally:
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()

    def test_note_actions_check_author_role_and_publication_time(self):
        from thlib.environment import env_server

        application = _Application()
        controller = CommunicationController(application)
        note = _SObject({
            "note": "Original", "login": "artist",
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=30))
                .strftime("%Y-%m-%d %H:%M:%S"),
        }, "sthpw/note?code=NOTE001")
        application.workspace_state.note_model.replace([{
            "searchKey": note.get_search_key(), "body": "Original",
            "entryType": "note", "canEdit": True, "canDelete": True,
        }])
        controller._notes[note.get_search_key()] = note
        controller._run = Mock()

        with patch.object(env_server, "get_user", return_value="artist"):
            self.assertTrue(controller.can_change_note(0))
            note.info["timestamp"] = (
                datetime.now(timezone.utc) - timedelta(hours=2)
            ).strftime("%Y-%m-%d %H:%M:%S")
            self.assertFalse(controller.can_change_note(0))
            self.assertFalse(controller.edit(0, "Changed"))
            controller.remove(0)
            controller._run.assert_not_called()

        with patch.object(env_server, "get_user", return_value="other"):
            self.assertFalse(controller.can_change_note(0))
            application.can_manage_tools = True
            self.assertTrue(controller.can_change_note(0))


if __name__ == "__main__":
    unittest.main()
