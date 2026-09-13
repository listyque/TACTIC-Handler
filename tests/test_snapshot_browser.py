import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import (
    QObject, QPoint, Property, Qt, QUrl, Signal, Slot,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QTest

from thlib.ui.controllers.item_operations import ItemOperationsMixin
from thlib.ui.controllers.commands import CommandsMixin
from thlib.ui.controllers.search_tabs import SearchTabsMixin
from thlib.ui.controllers.snapshot_actions import SnapshotActionsMixin
from thlib.ui.workspace_models.records import RecordListModel
from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.state import WorkspaceState
from thlib.ui.workspace_models.results_types import WorkspaceNode


class _File:
    def __init__(self, code, url=""):
        self._code = code
        self.url = url

    def get_code(self):
        return self._code

    def get_filename_with_ext(self):
        return "preview.png"

    def get_abs_path(self):
        return "C:/repository/preview.png"

    def get_full_abs_path(self):
        return self.get_abs_path()

    def get_file_size(self):
        return 1024

    def get_base_type(self):
        return "file"

    def get_type(self):
        return "icon" if self.url else "main"

    def get_web_preview(self):
        return self

    def get_icon_preview(self):
        return self

    def get_meta_file_object(self):
        return None


class _Snapshot:
    def __init__(self, code, file_object, preview_objects=None):
        self._code = code
        self._file = file_object
        self._preview_objects = list(preview_objects or [])

    def get_code(self):
        return self._code

    def get_snapshot(self):
        return {"code": self._code, "version": 1, "repo": "base"}

    def get_files_objects(self, group_by=None):
        if group_by == "type":
            return {"main": [self._file], "file": [self._file]}
        return [self._file]

    def get_previewable_files_objects(self):
        return list(self._preview_objects)


class _Node:
    def __init__(self, node_id, snapshot):
        self.node_id = node_id
        self.source = snapshot
        self.version = "v001"


class _PreviewSource:
    def __init__(self, search_key):
        self._search_key = search_key

    def get_search_key(self):
        return self._search_key


class _EditTarget:
    def __init__(self, stype):
        self._stype = stype

    def get_stype(self):
        return self._stype


class _SnapshotActionState:
    def __init__(self, file_object, selected_sobject):
        self._file_object = file_object
        self._selected_sobject = selected_sobject

    def snapshot_file_for(self, _token):
        return self._file_object


class _SnapshotActionHarness(SnapshotActionsMixin):
    def __init__(self, file_object, selected_sobject):
        self.debug_log = None
        self.workspace_state = _SnapshotActionState(
            file_object, selected_sobject
        )
        self._task_snapshot_source = None
        self._sobject_editor_request = {}
        self.opened_window = ""
        self.opened_files = []
        self.notifications = []

    def _notify(self, message):
        self.notifications.append(message)

    def open_window(self, window_id):
        self.opened_window = window_id

    def open_file_object(self, file_object):
        self.opened_files.append(file_object)


class _CallbackSignal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback, *_args):
        self.callbacks.append(callback)

    def emit(self, value):
        for callback in tuple(self.callbacks):
            callback(value)


class _SyncHandle:
    def __init__(self, task_id="open-task"):
        self.task_id = task_id
        self.downloaded = _CallbackSignal()
        self.failed = _CallbackSignal()
        self.download_count = 0

    def download(self):
        self.download_count += 1


class _RepositorySync:
    def __init__(self):
        self.handle = _SyncHandle()
        self.calls = []

    def schedule_file_object(self, file_object, **kwargs):
        self.calls.append((file_object, kwargs))
        return self.handle


class _OpenFile:
    def __init__(self, exists=False, file_type="file", snapshot=None):
        self.exists = exists
        self.file_type = file_type
        self.snapshot = snapshot
        self.open_count = 0

    def is_exists(self):
        return self.exists

    def open_file(self):
        self.open_count += 1

    def get_type(self):
        return self.file_type

    def get_snapshot(self):
        return self.snapshot


class _OpenHarness(ItemOperationsMixin):
    def __init__(self):
        self.repository_sync = _RepositorySync()
        self.notifications = []

    def _notify(self, message):
        self.notifications.append(message)


class _TriggerRecorder:
    def __init__(self):
        self.calls = []

    def run_before(self, action, context, finished):
        self.calls.append(("before", action, dict(context)))
        finished(True, "")

    def run_after(self, action, context, finished=None):
        self.calls.append(("after", action, dict(context)))
        if finished:
            finished(True, "")


class _SnapshotMenuController(QObject):
    snapshotBrowserChanged = Signal()
    snapshot_browser_show_all = Property(
        bool, lambda _self: False, constant=True,
    )
    snapshot_browser_show_more = Property(
        bool, lambda _self: False, constant=True,
    )
    snapshot_browser_content_mode = Property(
        str,
        lambda self: self._content_mode,
        notify=snapshotBrowserChanged,
    )
    snapshot_browser_orientation = Property(
        str, lambda _self: "horizontal", constant=True,
    )
    snapshot_browser_splitter_ratio = Property(
        float, lambda _self: 0.52, constant=True,
    )

    def __init__(self):
        super().__init__()
        self.invocations = []
        self._content_mode = "both"

    @Slot(result="QVariantList")
    def snapshot_browser_actions(self):
        return []

    @Slot(bool, result="QVariantList")
    def snapshot_file_actions(self, _include_check):
        return [{
            "title": "Edit info",
            "icon": "edit",
            "command": "edit",
        }]

    @Slot(str, str)
    def invoke_snapshot_file_action(self, command, token):
        self.invocations.append((command, token))

    @Slot(str)
    def toggle_snapshot_browser_option(self, _option):
        pass

    @Slot(str)
    def set_snapshot_browser_content_mode(self, mode):
        self._content_mode = mode
        self.snapshotBrowserChanged.emit()

    @Slot(str)
    def set_snapshot_browser_orientation(self, _orientation):
        pass

    @Slot(float)
    def set_snapshot_browser_splitter_ratio(self, _ratio):
        pass

    @Slot()
    def refresh_snapshot_browser(self):
        pass


class SnapshotBrowserModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_snapshot_card_renders_resolved_web_preview(self):
        qml_path = (
            Path(__file__).resolve().parents[1]
            / "thlib" / "ui"
            / "qml"
            / "WorkspaceCard.qml"
        )
        source = qml_path.read_text(encoding="utf-8")
        snapshot_component = source.split(
            "id: snapshotPreviewComponent", 1,
        )[1].split("id: processPreviewComponent", 1)[0]

        self.assertIn("source: root.cardPreviewUrl", snapshot_component)
        self.assertIn("fallbackText: root.snapshotExtension", snapshot_component)

    def test_subject_replacement_switches_preview_without_panel_animation(self):
        qml_dir = (
            Path(__file__).resolve().parents[1]
            / "thlib" / "ui" / "qml"
        )
        engine = QQmlEngine()
        engine.addImportPath(str(qml_dir))
        controller = _SnapshotMenuController()
        preview_model = RecordListModel(("token", "url", "title"))
        preview_model.replace([{
            "token": "first",
            "url": "file:///first-preview.png",
            "title": "First",
        }])
        file_model = RecordListModel(("rowType", "token", "title"))
        engine.rootContext().setContextProperty(
            "appController", controller,
        )
        engine.rootContext().setContextProperty(
            "snapshotPreviewModel", preview_model,
        )
        engine.rootContext().setContextProperty(
            "snapshotFileModel", file_model,
        )
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
ApplicationWindow {
    width: 720
    height: 520
    visible: true
    Theme {
        id: theme
        dark: true
    }
    SnapshotBrowser {
        id: browser
        objectName: "snapshotBrowser"
        anchors.fill: parent
        theme: theme
    }
}
''',
            QUrl.fromLocalFile(
                str(qml_dir / "_SnapshotReplacementTest.qml")
            ),
        )
        window = component.create()
        self.assertIsNotNone(
            window,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(30)
            preview_area = window.findChild(
                QObject, "snapshotPreviewArea"
            )
            transition = window.findChild(
                QObject, "snapshotCarouselTransition"
            )
            incoming = window.findChild(
                QObject, "snapshotIncomingPreviewLayer"
            )
            incoming_preview = window.findChild(
                QObject, "snapshotIncomingPreview"
            )
            self.assertIsNotNone(preview_area)
            self.assertIsNotNone(transition)
            self.assertEqual(
                preview_area.property("currentUrl"),
                "file:///first-preview.png",
            )

            preview_model.replace([{
                "token": "second",
                "url": "file:///second-preview.png",
                "title": "Second",
            }])
            QTest.qWait(30)

            self.assertEqual(
                preview_area.property("currentUrl"),
                "file:///second-preview.png",
            )
            self.assertFalse(transition.property("running"))
            self.assertEqual(incoming.property("opacity"), 1.0)
            self.assertFalse(
                incoming_preview.property("animateAppearance")
            )
            self.assertFalse(
                incoming_preview.property("effectsEnabled")
            )
        finally:
            window.close()
            window.deleteLater()
            QTest.qWait(10)

    def test_card_preview_prefers_native_web_derivative(self):
        icon_file = _File("ICON", "file:///icon.png")
        web_file = _File("WEB", "file:///web.png")
        icon_file.get_web_preview = lambda: web_file
        snapshot = _Snapshot("SNAPSHOT00001", icon_file)
        snapshot.get_files_objects = lambda group_by=None: {
            "icon": [icon_file],
        } if group_by == "type" else [icon_file]

        regular = WorkspaceItemModel._snapshot_preview_candidates(snapshot)
        card = WorkspaceItemModel._snapshot_card_preview_candidates(snapshot)

        self.assertIs(regular[0], icon_file)
        self.assertIs(card[0], web_file)

    def test_card_preview_can_retry_after_empty_or_failed_result(self):
        source = object()
        node = WorkspaceNode(
            node_id="snapshot-preview",
            node_type="snapshot",
            code="SNAPSHOT00001",
            title="Preview",
            search_key="sthpw/snapshot?code=SNAPSHOT00001",
            preview_source=source,
        )
        model = WorkspaceItemModel()
        model.replace_nodes([node])

        self.assertEqual(
            model.begin_card_preview_request(node.node_id),
            (node.node_type, source),
        )
        self.assertTrue(node.card_preview_requested)

        model.apply_card_preview(node.node_id, source, [])

        self.assertFalse(node.card_preview_requested)
        self.assertEqual(
            model.begin_card_preview_request(node.node_id),
            (node.node_type, source),
        )

        node.card_preview_url = "pending-preview:card-task"
        model.fail_preview("card-task")

        self.assertFalse(node.card_preview_requested)
        self.assertEqual(
            model.begin_card_preview_request(node.node_id),
            (node.node_type, source),
        )

    def test_preview_state_survives_semantic_node_replacement(self):
        search_key = "prod/asset?code=ASSET001"
        original = WorkspaceNode(
            node_id=search_key,
            node_type="sobject",
            search_key=search_key,
            code="ASSET001",
            title="Asset",
            preview_source=_PreviewSource(search_key),
            preview_url="file:///preview.png",
            card_preview_url="pending-preview:card-task",
            preview_requested=True,
            card_preview_requested=True,
            preview_revealed=True,
        )
        model = WorkspaceItemModel()
        model.replace_nodes([original])
        replacement = WorkspaceNode(
            node_id=search_key,
            node_type="sobject",
            search_key=search_key,
            code="ASSET001",
            title="Asset",
            preview_source=_PreviewSource(search_key),
        )

        model.replace_nodes([replacement])

        self.assertIs(model.node_for(search_key), replacement)
        self.assertEqual(replacement.preview_url, "file:///preview.png")
        self.assertEqual(
            replacement.card_preview_url,
            "pending-preview:card-task",
        )
        self.assertTrue(replacement.preview_requested)
        self.assertTrue(replacement.card_preview_requested)
        self.assertTrue(replacement.preview_revealed)

    def test_local_preview_url_changes_when_versionless_file_is_replaced(self):
        class LocalPreviewFile:
            def __init__(self, path):
                self.path = path

            def get_full_abs_path(self):
                return str(self.path)

            @staticmethod
            def is_local_current():
                return True

        with self.subTest("same path and size use filesystem revision"):
            from tempfile import TemporaryDirectory

            with TemporaryDirectory() as directory:
                path = Path(directory) / "publish.jpg"
                path.write_bytes(b"first")
                os.utime(path, ns=(1_000_000_000, 1_000_000_000))
                file_object = LocalPreviewFile(path)
                first_url = WorkspaceItemModel._safe_file_url(file_object)

                path.write_bytes(b"other")
                os.utime(path, ns=(2_000_000_000, 2_000_000_000))
                second_url = WorkspaceItemModel._safe_file_url(file_object)

            self.assertIn("revision=", first_url)
            self.assertIn("revision=", second_url)
            self.assertNotEqual(first_url, second_url)

    def test_inflight_preview_applies_to_rebuilt_sobject_wrapper(self):
        search_key = "prod/asset?code=ASSET001"
        original_source = _PreviewSource(search_key)
        original = WorkspaceNode(
            node_id=search_key,
            node_type="sobject",
            search_key=search_key,
            code="ASSET001",
            title="Asset",
            preview_source=original_source,
        )
        model = WorkspaceItemModel()
        model.replace_nodes([original])
        self.assertIsNotNone(model.begin_preview_request(search_key))
        replacement = WorkspaceNode(
            node_id=search_key,
            node_type="sobject",
            search_key=search_key,
            code="ASSET001",
            title="Asset",
            preview_source=_PreviewSource(search_key),
        )
        model.replace_nodes([replacement])

        with patch.object(
            model, "_preview_url", return_value="file:///preview.png",
        ):
            model.apply_preview(search_key, original_source, [object()])

        self.assertEqual(replacement.preview_url, "file:///preview.png")

    def test_regular_preview_can_retry_after_empty_result(self):
        source = object()
        node = WorkspaceNode(
            node_id="snapshot-preview",
            node_type="snapshot",
            code="SNAPSHOT00001",
            title="Preview",
            search_key="sthpw/snapshot?code=SNAPSHOT00001",
            preview_source=source,
        )
        model = WorkspaceItemModel()
        model.replace_nodes([node])
        self.assertIsNotNone(model.begin_preview_request(node.node_id))

        model.apply_preview(node.node_id, source, [])

        self.assertFalse(node.preview_requested)
        self.assertIsNotNone(model.begin_preview_request(node.node_id))

    def test_file_edit_info_opens_the_selected_file(self):
        file_object = object()
        stype = object()
        selected_sobject = _EditTarget(stype)
        controller = _SnapshotActionHarness(
            file_object, selected_sobject
        )

        controller.invoke_snapshot_file_action("edit", "file-token")

        self.assertEqual(controller.opened_window, "add_sobject")
        self.assertIs(
            controller._sobject_editor_request["sobject"],
            file_object,
        )
        self.assertIs(
            controller._sobject_editor_request["stype"], stype
        )
        self.assertTrue(
            controller._sobject_editor_request["_prepared"]
        )
        self.assertEqual(controller.notifications, [])

    def test_task_snapshot_file_edit_uses_explicit_source_schema(self):
        selected = _EditTarget(object())
        task_stype = object()
        task_source = _EditTarget(task_stype)
        file_object = object()
        controller = _SnapshotActionHarness(file_object, selected)
        controller._task_snapshot_source = task_source

        controller.invoke_snapshot_file_action("edit", "file-token")

        self.assertIs(
            controller._sobject_editor_request["sobject"], file_object
        )
        self.assertIs(
            controller._sobject_editor_request["stype"], task_stype
        )

    def test_snapshot_browser_open_uses_shared_file_operation(self):
        file_object = object()
        controller = _SnapshotActionHarness(
            file_object, _EditTarget(object())
        )

        controller.invoke_snapshot_file_action("open", "file-token")

        self.assertEqual(controller.opened_files, [file_object])

    def test_missing_file_opens_only_after_repository_download(self):
        controller = _OpenHarness()
        file_object = _OpenFile(exists=False)

        controller.open_file_object(file_object)

        self.assertEqual(file_object.open_count, 0)
        self.assertEqual(controller.repository_sync.handle.download_count, 1)
        self.assertEqual(len(controller.repository_sync.calls), 1)
        self.assertFalse(
            controller.repository_sync.calls[0][1]["is_ui_preview"]
        )

        controller.repository_sync.handle.downloaded.emit(file_object)

        self.assertEqual(file_object.open_count, 1)
        self.assertEqual(controller._pending_file_open_tasks, set())

    def test_snapshot_open_hooks_wrap_repository_download_and_file_open(self):
        snapshot = SimpleNamespace(
            get_search_key=lambda: "sthpw/snapshot?code=SNAPSHOT001",
            get_snapshot=lambda: {
                "search_type": "demo/asset",
                "search_code": "ASSET001",
                "process": "model",
                "context": "model/main",
                "code": "SNAPSHOT001",
            },
        )
        file_object = _OpenFile(exists=False, snapshot=snapshot)
        controller = _OpenHarness()
        controller._current_project_code = "demo"
        controller._script_triggers = _TriggerRecorder()

        controller.open_file_object(file_object)

        self.assertEqual(
            [(phase, action) for phase, action, _context
             in controller._script_triggers.calls],
            [("before", "snapshot.open")],
        )
        self.assertEqual(
            controller._script_triggers.calls[0][2]["search_key"],
            "demo/asset?code=ASSET001",
        )
        self.assertEqual(file_object.open_count, 0)

        controller.repository_sync.handle.downloaded.emit(file_object)

        self.assertEqual(file_object.open_count, 1)
        self.assertEqual(
            [(phase, action) for phase, action, _context
             in controller._script_triggers.calls],
            [
                ("before", "snapshot.open"),
                ("after", "snapshot.open"),
            ],
        )

    def test_snapshot_primary_file_accepts_server_defined_file_type(self):
        file_object = _OpenFile(file_type="scene_payload")

        class Snapshot:
            @staticmethod
            def get_files_objects(group_by=None):
                if group_by == "type":
                    return {"scene_payload": [file_object]}
                return [file_object]

        self.assertIs(
            ItemOperationsMixin._file_object_from_snapshot(Snapshot()),
            file_object,
        )

    def test_file_menu_keeps_target_until_delayed_action_dispatch(self):
        qml_dir = (
            Path(__file__).resolve().parents[1]
            / "thlib" / "ui" / "qml"
        )
        engine = QQmlEngine()
        engine.addImportPath(str(qml_dir))
        warnings = []
        engine.warnings.connect(
            lambda errors: warnings.extend(
                error.toString() for error in errors
            )
        )
        controller = _SnapshotMenuController()
        preview_model = RecordListModel(("token", "url", "title"))
        file_model = RecordListModel(("rowType", "token", "title"))
        engine.rootContext().setContextProperty(
            "appController", controller,
        )
        engine.rootContext().setContextProperty(
            "snapshotPreviewModel", preview_model,
        )
        engine.rootContext().setContextProperty(
            "snapshotFileModel", file_model,
        )
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
ApplicationWindow {
    width: 720
    height: 520
    visible: true
    Theme {
        id: theme
        dark: true
        popupAnimationsEnabled: false
    }
    SnapshotBrowser {
        id: browser
        objectName: "snapshotBrowser"
        anchors.fill: parent
        theme: theme
    }
}
''',
            QUrl.fromLocalFile(
                str(qml_dir / "_SnapshotFileMenuDispatchTest.qml")
            ),
        )
        window = component.create()
        self.assertIsNotNone(
            window,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            browser = window.findChild(QObject, "snapshotBrowser")
            menu = window.findChild(QObject, "snapshotFileMenu")
            self.assertIsNotNone(browser)
            self.assertIsNotNone(menu)
            browser.setProperty("contextFileToken", "file-token")
            menu.setProperty(
                "actions", controller.snapshot_file_actions(True),
            )

            menu.open()
            QTest.qWait(60)
            self.assertTrue(
                menu.property("opened"), "\n".join(warnings),
            )
            popup_window = next(
                candidate
                for candidate in QGuiApplication.allWindows()
                if candidate is not window
                and candidate.isVisible()
                and candidate.transientParent() is window
            )
            QTest.mouseClick(
                popup_window,
                Qt.LeftButton,
                Qt.NoModifier,
                QPoint(
                    popup_window.width() // 2,
                    popup_window.height() // 2,
                ),
            )
            QTest.qWait(80)

            self.assertEqual(
                controller.invocations, [("edit", "file-token")],
            )
            self.assertEqual(browser.property("contextFileToken"), "")
        finally:
            window.close()
            window.deleteLater()
            QTest.qWait(10)

    def test_duplicate_snapshot_and_file_codes_are_ignored(self):
        state = WorkspaceState()
        file_object = _File("FILE00001")
        snapshot = _Snapshot("SNAPSHOT00001", file_object)

        state._build_snapshot_browser_models([
            _Node("snapshot-one", snapshot),
            _Node("snapshot-copy", snapshot),
        ])

        rows = state.snapshot_file_model._records
        self.assertEqual(
            1,
            sum(row["rowType"] == "snapshot" for row in rows),
        )
        self.assertEqual(
            1,
            sum(row["rowType"] == "file" for row in rows),
        )

    def test_hidden_snapshot_browser_defers_model_publication(self):
        state = WorkspaceState()
        state.snapshot_preview_model.replace([{
            "token": "old", "title": "Old", "url": "file:///old.png",
            "kind": "icon", "snapshotNodeId": "old",
        }])
        state.set_snapshot_presentation_visible(False)
        file_object = _File("FILE00001", "file:///new.png")
        snapshot = _Snapshot("SNAPSHOT00001", file_object, [file_object])

        with patch.object(
            state._preview_helper, "_preview_url",
            side_effect=lambda candidate: candidate.url,
        ):
            state._build_snapshot_browser_models([
                _Node("new", snapshot),
            ])

        self.assertEqual(
            state.snapshot_preview_model.get(0)["token"], "old"
        )
        self.assertTrue(state._snapshot_preview_records)

        state.set_snapshot_presentation_visible(True)

        self.assertNotEqual(
            state.snapshot_preview_model.get(0)["token"], "old"
        )

    def test_icon_preview_is_first_without_duplicating_selected_preview(self):
        state = WorkspaceState()
        selected_file = _File("FILE00001", "file:///selected.png")
        icon_file = _File("FILE00002", "file:///icon.png")
        duplicate_icon = _File("FILE00003", "file:///icon.png")
        selected = _Snapshot(
            "SNAPSHOT00001", selected_file,
            [selected_file, duplicate_icon],
        )
        icon = _Snapshot("SNAPSHOT00002", icon_file, [icon_file])

        with patch.object(
            state._preview_helper, "_preview_url",
            side_effect=lambda file_object: file_object.url,
        ):
            state._build_snapshot_browser_models(
                [_Node("selected", selected)],
                [_Node("icon", icon)],
            )

        previews = state.snapshot_preview_model._records
        self.assertEqual(previews[0]["url"], "file:///icon.png")
        self.assertEqual(
            [item["url"] for item in previews].count("file:///icon.png"),
            1,
        )
        self.assertEqual(previews[1]["url"], "file:///selected.png")

    def test_task_projection_loads_full_snapshot_data_once_when_needed(self):
        class Source:
            def __init__(self):
                self.processes = {"icon": object()}
                self.update_count = 0

            def get_all_processes(self):
                return self.processes

            def update_snapshots(self, order_bys=None):
                self.update_count += 1
                self.processes = {
                    "icon": object(), "model": object(),
                }

        source = Source()
        model = WorkspaceItemModel()

        def snapshot_nodes(process, *_args, **_kwargs):
            return [WorkspaceNode(
                node_id=process,
                node_type="snapshot",
                search_key="snapshot-" + process,
                code="SNAPSHOT-" + process,
                title=process,
                process=process,
                context="model/main" if process == "model" else "icon",
                source=object(),
            )]

        with patch.object(model, "_snapshot_nodes", snapshot_nodes):
            selected, icons = model.snapshot_nodes_for_source(
                source, "prod/asset?code=ASSET001",
                "model", "model/main",
            )

        self.assertEqual(source.update_count, 1)
        self.assertEqual([node.process for node in selected], ["model"])
        self.assertEqual([node.process for node in icons], ["icon"])

    def test_content_mode_keeps_only_the_requested_surface_active(self):
        qml_dir = (
            Path(__file__).resolve().parents[1]
            / "thlib" / "ui" / "qml"
        )
        engine = QQmlEngine()
        engine.addImportPath(str(qml_dir))
        warnings = []
        engine.warnings.connect(
            lambda errors: warnings.extend(
                error.toString() for error in errors
            )
        )
        controller = _SnapshotMenuController()
        preview_model = RecordListModel(("token", "url", "title"))
        preview_model.replace([{
            "token": "preview",
            "url": "",
            "title": "Preview",
        }])
        file_model = RecordListModel((
            "rowType", "token", "title", "fileType", "size", "path",
            "repository", "baseType", "depth", "exists", "previewType",
            "checking", "matchesRemote",
        ))
        file_model.replace([{
            "rowType": "file", "token": "file", "title": "scene.ma",
            "fileType": "main", "size": "1 KB", "path": "C:/scene.ma",
            "repository": "base", "baseType": "file", "depth": 0,
            "exists": True, "previewType": False, "checking": False,
            "matchesRemote": True,
        }])
        context = engine.rootContext()
        context.setContextProperty("appController", controller)
        context.setContextProperty("snapshotPreviewModel", preview_model)
        context.setContextProperty("snapshotFileModel", file_model)
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Controls
ApplicationWindow {
    width: 720
    height: 520
    visible: true
    Theme {
        id: theme
        dark: true
        clickAnimationsEnabled: false
        hoverAnimationsEnabled: false
        fadeAnimationsEnabled: false
        popupAnimationsEnabled: false
    }
    SnapshotBrowser {
        objectName: "snapshotBrowser"
        anchors.fill: parent
        theme: theme
    }
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_SnapshotContentModeTest.qml")),
        )
        window = component.create()
        self.assertIsNotNone(
            window,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(30)
            preview = window.findChild(QObject, "snapshotPreviewArea")
            files = window.findChild(QObject, "snapshotFilesPanel")
            files_view = window.findChild(QObject, "snapshotFilesView")
            splitter = window.findChild(QObject, "snapshotSplitterHandle")
            settings_menu = window.findChild(
                QObject, "snapshotBrowserOptionsMenu"
            )
            self.assertIsNotNone(settings_menu)
            self.assertTrue(preview.property("visible"))
            self.assertTrue(files.property("visible"))
            self.assertTrue(splitter.property("visible"))
            self.assertEqual(files_view.property("count"), 1)

            settings_menu.triggered.emit("content_preview")
            QTest.qWait(20)
            self.assertTrue(preview.property("visible"))
            self.assertFalse(files.property("visible"))
            self.assertFalse(splitter.property("visible"))
            self.assertEqual(files_view.property("count"), 0)
            self.assertGreater(preview.property("height"), 400)

            settings_menu.triggered.emit("content_files")
            QTest.qWait(20)
            self.assertFalse(preview.property("visible"))
            self.assertTrue(files.property("visible"))
            self.assertFalse(splitter.property("visible"))
            self.assertEqual(files_view.property("count"), 1)
            self.assertGreater(files.property("height"), 400)

            window.setWidth(360)
            window.setHeight(280)
            QTest.qWait(20)
            self.assertGreater(files.property("width"), 300)
            self.assertGreater(files.property("height"), 190)

            settings_menu.triggered.emit("content_preview")
            window.setWidth(1200)
            window.setHeight(760)
            QTest.qWait(20)
            self.assertGreater(preview.property("width"), 1100)
            self.assertGreater(preview.property("height"), 650)
            snapshot_warnings = [
                warning for warning in warnings
                if "SnapshotBrowser.qml" in warning
            ]
            self.assertEqual(snapshot_warnings, [])
        finally:
            window.close()
            window.deleteLater()
            engine.deleteLater()
            QTest.qWait(10)

    def test_content_mode_menu_and_persistence_share_one_owner(self):
        class Harness(CommandsMixin, SearchTabsMixin):
            def __init__(self):
                self._snapshot_browser_content_mode = "both"
                self._snapshot_browser_show_all = False
                self._snapshot_browser_show_more = False
                self._snapshot_browser_orientation = "horizontal"
                self._settings = {}
                self.writes = 0
                self.snapshot_browser_changed = SimpleNamespace(
                    emit=lambda: None,
                )

            def _write_settings(self):
                self.writes += 1

        controller = Harness()
        actions = {
            action.get("command"): action
            for action in controller.snapshot_browser_actions()
            if not action.get("separator")
        }

        self.assertTrue(actions["content_both"]["checked"])
        self.assertFalse(actions["content_preview"]["checked"])
        self.assertFalse(actions["content_files"]["checked"])

        controller.set_snapshot_browser_content_mode("preview")

        self.assertEqual(controller._snapshot_browser_content_mode, "preview")
        self.assertEqual(
            controller._settings["snapshotBrowser/contentMode"], "preview",
        )
        self.assertEqual(controller.writes, 1)


if __name__ == "__main__":
    unittest.main()
