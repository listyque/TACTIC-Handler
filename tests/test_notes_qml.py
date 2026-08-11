from __future__ import annotations

import os
from pathlib import Path
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine

from modern_ui.communication import CommunicationController
from modern_ui.controllers.item_operations import ItemOperationsMixin
from modern_ui.controllers.selection import SelectionMixin
from modern_ui.controllers.snapshot_details import SnapshotDetailsMixin
from modern_ui.message_attachments import AttachmentUploadController
from modern_ui.workspace_models.records import RecordListModel


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
    def __init__(self, node):
        self.node = node
        self.loaded = None
        self.workspace_model = SimpleNamespace(
            node_for=lambda node_id: self.node if node_id == self.node.node_id else None
        )
        self.tab = SimpleNamespace(selected_node_id=node.node_id)

    def _current_tab(self):
        return self.tab

    def _load_sobject_details(self, *args):
        self.loaded = args


class NotesQmlTests(unittest.TestCase):

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
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_notes_components_compile(self):
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "modern_ui" / "qml"
        for name in (
                "AttachmentStagingPanel.qml", "MessageComposerField.qml",
                "MessageSendButton.qml", "MessageReplyPreview.qml",
                "MessageForwardPreview.qml",
                "AttachmentCard.qml", "SnapshotSummary.qml",
                "WorkspaceResultItem.qml", "SKeyPreviewCard.qml",
                "TaskInspector.qml", "QuickFilterEditorDialog.qml",
                "ActivityEventCard.qml",
                "CommunicationView.qml", "MessagesView.qml"):
            component = QQmlComponent(engine, QUrl.fromLocalFile(str(qml_dir / name)))
            self.assertNotEqual(
                component.status(),
                QQmlComponent.Status.Error,
                "\n".join(error.toString() for error in component.errors()),
            )

    def test_forward_dialog_uses_registered_conversation_model(self):
        path = (
            Path(__file__).parents[1] / "modern_ui" / "qml" / "MessagesView.qml"
        )
        source = path.read_text(encoding="utf-8")
        self.assertIn("model: messageConversationModel", source)
        self.assertNotIn("model: messagesController.conversations", source)

    def test_pin_history_entries_open_their_message(self):
        path = (
            Path(__file__).parents[1] / "modern_ui" / "qml" / "MessagesView.qml"
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

        with patch.object(controller, "refresh") as refresh:
            controller.activate_task_context(
                "TASK002", target.get_search_key(), "model"
            )

        self.assertEqual(controller.selectedTaskCode, "TASK002")
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
        controller._request_id = "request"

        with patch("thlib.environment.env_server.get_user", return_value="artist"):
            controller._history_ready(
                "request", ({"TASK001": first, "TASK002": second}, {"NOTE001": note})
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
            ["Shared note"],
        )
        self.assertEqual(
            [record["statusTo"] for record in records if record["entryType"] == "status"],
            ["Review"],
        )

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

    def test_chat_attachment_context_does_not_repeat_conversation_code(self):
        payload = AttachmentUploadController._payload(
            "CHAT001",
            {"path": "C:/files/image.png", "fileType": "preview"},
            "request-1",
        )
        self.assertEqual(payload["context"], "attachment/chat/image")
        self.assertNotIn("CHAT001", payload["context"])

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
                "modern_ui.checkin_operation.execute_checkin_payload",
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
                "modern_ui.checkin_operation.execute_checkin_payload",
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

    def test_existing_note_can_be_edited(self):
        application = _Application()
        controller = CommunicationController(application)
        note = _SObject({"note": "Before"}, "sthpw/note?code=NOTE001")
        application.workspace_state.note_model.replace([{
            "searchKey": note.get_search_key(), "body": "Before",
            "entryType": "note", "canEdit": True,
        }])
        controller._notes[note.get_search_key()] = note
        controller._run = lambda callback, clear_composer=False: callback()
        self.assertTrue(controller.edit(0, "After"))
        self.assertEqual(note.get_info()["note"], "After")
        metadata = note.get_info()["metadata"]
        self.assertEqual(metadata["editHistory"][0]["body"], "Before")


if __name__ == "__main__":
    unittest.main()
