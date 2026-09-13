from __future__ import annotations

import json
from pathlib import Path
import unittest

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QMimeData,
    QObject,
    QMetaObject,
    QPoint,
    QPointF,
    Property,
    QTemporaryDir,
    Signal,
    Qt,
    QUrl,
    Slot,
    qInstallMessageHandler,
)
from PySide6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QGuiApplication,
    QImage,
)
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.records import RecordListModel
from thlib.ui.workspace_models.results_types import WorkspaceNode
from tests.qt_application import gui_test_application


ROOT = Path(__file__).resolve().parents[1]
QML_RENDER_BUDGETS = json.loads(
    (ROOT / "tests" / "contracts" / "qml_render_budgets.json").read_text(
        encoding="utf-8"
    )
)


def _visual_child(parent, object_name):
    pending = list(parent.childItems())
    while pending:
        child = pending.pop()
        if child.objectName() == object_name:
            return child
        pending.extend(child.childItems())
    return None


class _WorkspaceAppController(QObject):
    maya_dcc_selected_changed = Signal()

    def __init__(self):
        super().__init__()
        self.revealed_previews = []
        self.preview_requests = []
        self.card_preview_requests = []
        self.drop_requests = []
        self.item_actions = []
        self.dcc_application_value = "standalone"

    @Property(bool, notify=maya_dcc_selected_changed)
    def maya_dcc_selected(self):
        return self.dcc_application_value == "maya"

    @Property(str, notify=maya_dcc_selected_changed)
    def selected_dcc_application(self):
        return self.dcc_application_value

    def set_maya_dcc_selected(self, selected):
        application = "maya" if selected else "standalone"
        self.set_dcc_application(application)

    def set_dcc_application(self, application):
        application = str(application or "standalone").lower()
        if self.dcc_application_value == application:
            return
        self.dcc_application_value = application
        self.maya_dcc_selected_changed.emit()

    @Property(bool, constant=True)
    def description_limit_enabled(self):
        return False

    @Property(int, constant=True)
    def description_limit(self):
        return 200

    @Property(str, constant=True)
    def results_view_mode(self):
        return "continious"

    @Property(float, constant=True)
    def results_splitter_ratio(self):
        return 0.58

    @Property(bool, constant=True)
    def card_can_go_back(self):
        return False

    @Property(str, constant=True)
    def loading_mode(self):
        return "pages"

    @Property(bool, constant=True)
    def card_compact_level(self):
        return False

    @Property("QVariantList", constant=True)
    def selected_result_node_ids(self):
        return []

    @Slot(str, result=str)
    def get_acronym(self, value):
        return value[:2].upper()

    @Slot(str)
    def request_item_preview(self, node_id):
        self.preview_requests.append(node_id)

    @Slot(str)
    def request_item_card_preview(self, node_id):
        self.card_preview_requests.append(node_id)

    @Slot(str)
    def mark_item_preview_revealed(self, node_id):
        self.revealed_previews.append(node_id)

    @Slot(str, result="QVariantMap")
    def item_drag_payload(self, node_id):
        return {"text/plain": node_id}

    @Slot("QVariantList", result=bool)
    def can_drop_as_icon(self, urls):
        return bool(urls)

    @Slot(str, "QVariantList", str)
    def queue_dropped_files(self, node_id, urls, target):
        self.drop_requests.append((node_id, list(urls), target))

    @Slot(str, str)
    def invoke_item_action(self, command, node_id):
        self.item_actions.append((command, node_id))

    @Slot(str, result="QVariantList")
    def item_quick_actions(self, node_id):
        maya = self.dcc_application_value == "maya"
        dcc = self.dcc_application_value != "standalone"
        dcc_title = self.dcc_application_value.title()
        actions = [{
            "title": (
                "Save scene" if maya else
                f"Save {dcc_title} scene" if dcc else "Save snapshot"
            ),
            "icon": "save",
            "command": "dcc_save_scene" if dcc else "save",
            "replaces": "save",
            "dccActionId": "save" if dcc else "",
        }]
        if "without-snapshot" in node_id:
            return actions
        actions.append({
            "title": (
                "Open scene" if maya else
                f"Open {dcc_title} scene" if dcc else "Open snapshot"
            ),
            "icon": "folder_open",
            "command": "dcc_open" if dcc else "open",
            "replaces": "open",
            "dccActionId": "open" if dcc else "",
        })
        if dcc:
            actions.extend([
                {
                    "title": "Import",
                    "icon": "input",
                    "command": "dcc_import",
                    "dccActionId": "import",
                },
                {
                    "title": "Create Reference",
                    "icon": "link",
                    "command": "dcc_reference",
                    "dccActionId": "reference",
                },
            ])
        return actions

    @Slot()
    def clear_result_selection(self):
        pass

    @Slot(str, bool)
    def toggle_result_node_recursive(self, _node_id, _recursive):
        pass

    @Slot()
    def select_all_result_siblings(self):
        pass


class WorkspaceResultItemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        self.source = (
            ROOT / "thlib" / "ui" / "qml" / "WorkspaceResultItem.qml"
        ).read_text(encoding="utf-8")

    @staticmethod
    def item_properties(theme, **updates):
        properties = {
            "index": 0,
            "nodeId": "relation:asset",
            "nodeType": "relation",
            "searchKey": "",
            "itemCode": "asset",
            "title": "Assets",
            "subtitle": "",
            "status": "",
            "accent": "#607d8b",
            "comments": 0,
            "tasks": 0,
            "depth": 2,
            "expanded": True,
            "hasChildren": True,
            "context": "",
            "version": "",
            "filePath": "",
            "fileSize": "",
            "infoChips": [],
            "parentId": "asset:1",
            "process": "",
            "author": "",
            "timestamp": "",
            "timestampPretty": "",
            "timestampSimple": "",
            "revision": "",
            "repository": "",
            "repositoryColor": "",
            "previewUrl": "",
            "previewRevealed": False,
            "previewRequested": False,
            "relationship": "instance",
            "watchState": "none",
            "fileExists": False,
            "isLatest": False,
            "isVersionless": False,
            "isMultiple": False,
            "needsSync": False,
            "childCount": 12,
            "itemControls": [],
            "progressItems": [],
            "nodeLoading": False,
            "compactMode": True,
            "theme": theme,
            "width": 260,
        }
        properties.update(updates)
        return properties

    @staticmethod
    def card_properties(theme, **updates):
        properties = {
            "index": 0,
            "nodeId": "card:asset",
            "nodeType": "sobject",
            "searchKey": "demo/asset?code=ASSET001",
            "title": "Asset",
            "subtitle": "",
            "status": "",
            "accent": "#607d8b",
            "comments": 0,
            "tasks": 0,
            "childCount": 0,
            "isLatest": False,
            "hasChildren": False,
            "process": "",
            "author": "",
            "timestamp": "",
            "version": "",
            "repository": "",
            "cardPreviewUrl": "",
            "previewRevealed": False,
            "cardPreviewRequested": True,
            "progressItems": [],
            "infoChips": [],
            "itemControls": [],
            "nodeLoading": False,
            "theme": theme,
            "width": 260,
            "height": 250,
        }
        properties.update(updates)
        return properties

    def test_child_relation_rows_are_taller_than_process_rows(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml"))
        )
        relation = component.createWithInitialProperties(
            self.item_properties(theme, nodeType="relation", compactMode=True)
        )
        process = component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="process:model",
                nodeType="process",
                title="model",
                compactMode=True,
            )
        )
        for item in (relation, process):
            self.assertIsNotNone(
                item,
                "\n".join(error.toString() for error in component.errors()),
            )
        self.app.processEvents()

        self.assertEqual(process.property("height"), 32)
        self.assertEqual(relation.property("height"), 38)
        self.assertAlmostEqual(
            relation.property("height") / process.property("height"),
            1.2,
            delta=0.02,
        )

        relation.deleteLater()
        process.deleteLater()
        theme.deleteLater()

    def test_workspace_file_drop_uses_one_smoothed_adaptive_presenter(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        presenter = (qml_dir / "WorkspaceFileDropTarget.qml").read_text(
            encoding="utf-8"
        )
        result_item = (qml_dir / "WorkspaceResultItem.qml").read_text(
            encoding="utf-8"
        )
        card = (qml_dir / "WorkspaceCard.qml").read_text(encoding="utf-8")

        self.assertIn("WorkspaceFileDropTarget {", result_item)
        self.assertIn("WorkspaceFileDropTarget {", card)
        self.assertNotIn('title": "Add Icon"', result_item)
        self.assertNotIn('title": "Add Icon"', card)
        self.assertGreaterEqual(presenter.count("antialiasing: true"), 2)
        self.assertGreaterEqual(presenter.count("clip: true"), 2)
        self.assertIn("controller.can_drop_as_icon(urls || [])", presenter)
        self.assertIn('root.nodeType === "relation"', presenter)
        self.assertIn('"target": "ingest"', presenter)
        self.assertIn("iconDropAvailable ? iconZones : fileZones", presenter)
        self.assertIn("visible: !root.spacious", presenter)
        self.assertIn("elide: Text.ElideRight", presenter)
        self.assertLess(
            presenter.index("drop.acceptProposedAction()", presenter.index(
                "onDropped: function(drop)"
            )),
            presenter.index("controller.queue_dropped_files", presenter.index(
                "onDropped: function(drop)"
            )),
        )

    def test_process_file_drop_presenter_retains_its_process_target(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "WorkspaceFileDropTarget.qml")),
        )
        target = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "nodeId": "asset:1:process:render",
            "nodeType": "process",
            "nodeTitle": "Render",
            "targetProcess": "render",
            "width": 280,
            "height": 32,
        })
        self.assertIsNotNone(
            target,
            "\n".join(error.toString() for error in component.errors()),
        )
        target.setProperty("activeZone", 0)

        self.assertEqual(target.activeTarget(), "render")

        target.deleteLater()
        theme.deleteLater()

    def test_relation_file_drop_presenter_targets_child_ingest(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "WorkspaceFileDropTarget.qml")),
        )
        target = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "nodeId": "episode:1:relation:shots",
            "nodeType": "relation",
            "nodeTitle": "Shots",
            "targetProcess": "",
            "width": 280,
            "height": 38,
        })
        self.assertIsNotNone(
            target,
            "\n".join(error.toString() for error in component.errors()),
        )
        target.setProperty("activeZone", 0)

        self.assertTrue(target.property("enabled"))
        self.assertEqual(target.activeTarget(), "ingest")

        target.deleteLater()
        theme.deleteLater()

    def test_process_row_accepts_a_real_file_drop_before_dispatch(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "WorkspaceFileDropTarget.qml")),
        )
        target = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "nodeId": "asset:1:process:render",
            "nodeType": "process",
            "nodeTitle": "Render",
            "targetProcess": "render",
            "width": 280,
            "height": 32,
        })
        self.assertIsNotNone(
            target,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.setGeometry(0, 0, 280, 32)
        target.setParentItem(window.contentItem())
        window.show()
        self.app.processEvents()
        mime = QMimeData()
        url = QUrl.fromLocalFile("D:/plate/render.mov")
        mime.setUrls([url])
        enter = QDragEnterEvent(
            QPoint(140, 16),
            Qt.CopyAction,
            mime,
            Qt.LeftButton,
            Qt.NoModifier,
        )

        QCoreApplication.sendEvent(window, enter)
        self.app.processEvents()

        self.assertTrue(enter.isAccepted())
        self.assertTrue(target.property("containsDrag"))
        presentation = target.findChild(
            QObject, "workspaceFileDropPresentation"
        )
        self.assertIsNotNone(presentation)
        self.assertIsNotNone(presentation.property("item"))
        drop = QDropEvent(
            QPointF(140, 16),
            Qt.CopyAction,
            mime,
            Qt.LeftButton,
            Qt.NoModifier,
        )

        QCoreApplication.sendEvent(window, drop)
        self.app.processEvents()

        self.assertTrue(drop.isAccepted())
        self.assertEqual(len(controller.drop_requests), 1)
        self.assertEqual(
            controller.drop_requests[0][0::2],
            ("asset:1:process:render", "render"),
        )

        window.hide()
        target.deleteLater()
        window.deleteLater()
        theme.deleteLater()

    def test_visible_delegates_retry_preview_after_model_invalidation(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        item_component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml")),
        )
        card_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "WorkspaceCard.qml"))
        )
        old_preview = "file:///D:/repository/publish.jpg?revision=old"
        item = item_component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="asset:publish",
                nodeType="sobject",
                searchKey="demo/asset?code=ASSET001",
                previewUrl=old_preview,
                previewRequested=True,
                compactMode=False,
            )
        )
        card = card_component.createWithInitialProperties(
            self.card_properties(
                theme,
                nodeId="card:publish",
                cardPreviewUrl=old_preview,
                cardPreviewRequested=True,
            )
        )
        self.assertIsNotNone(
            item,
            "\n".join(error.toString() for error in item_component.errors()),
        )
        self.assertIsNotNone(
            card,
            "\n".join(error.toString() for error in card_component.errors()),
        )
        self.app.processEvents()
        controller.preview_requests.clear()
        controller.card_preview_requests.clear()

        item.setProperty("previewUrl", "")
        item.setProperty("previewRequested", False)
        card.setProperty("cardPreviewUrl", "")
        card.setProperty("cardPreviewRequested", False)
        self.app.processEvents()

        self.assertEqual(controller.preview_requests, ["asset:publish"])
        self.assertEqual(
            controller.card_preview_requests, ["card:publish"]
        )

        item.deleteLater()
        card.deleteLater()
        theme.deleteLater()

    def test_pointer_selection_preserves_keyboard_modifiers(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml"))
        )
        item = component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="asset:1",
                nodeType="sobject",
                searchKey="demo/asset?project=demo&code=ASSET001",
                title="Asset 1",
                hasChildren=False,
                depth=0,
                compactMode=False,
                width=640,
            )
        )
        self.assertIsNotNone(
            item,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(660, 160)
        item.setParentItem(window.contentItem())
        received = []
        item.selectedRequested.connect(
            lambda *arguments: received.append(arguments)
        )
        window.show()
        QTest.qWait(30)

        QTest.mouseClick(
            window,
            Qt.LeftButton,
            Qt.ShiftModifier | Qt.ControlModifier,
            QPoint(360, 42),
        )
        QTest.qWait(20)

        self.assertEqual(len(received), 1)
        modifiers = received[0][3]
        self.assertTrue(modifiers & Qt.ShiftModifier.value)
        self.assertTrue(modifiers & Qt.ControlModifier.value)

        window.close()
        item.deleteLater()
        theme.deleteLater()

    def test_middle_click_requests_a_new_tab_for_the_sobject(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml"))
        )
        item = component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="asset:1",
                nodeType="sobject",
                searchKey="demo/asset?project=demo&code=ASSET001",
                title="Asset 1",
                hasChildren=False,
                depth=0,
                compactMode=False,
                width=640,
            )
        )
        self.assertIsNotNone(
            item,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(660, 160)
        item.setParentItem(window.contentItem())
        window.show()
        QTest.qWait(30)

        QTest.mouseClick(window, Qt.MiddleButton, pos=QPoint(360, 42))
        QTest.qWait(20)

        self.assertEqual(controller.item_actions, [("new_tab", "asset:1")])

        window.close()
        item.deleteLater()
        theme.deleteLater()

    def test_sobject_count_buttons_request_the_process_picker(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml")),
        )
        item = component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="asset:1",
                nodeType="sobject",
                searchKey="demo/asset?code=ASSET001",
                title="Asset 1",
                hasChildren=False,
                depth=0,
                tasks=4,
                comments=3,
                compactMode=False,
                width=640,
            )
        )
        self.assertIsNotNone(
            item,
            "\n".join(error.toString() for error in component.errors()),
        )
        requests = []
        item.processCountMenuRequested.connect(
            lambda node_id, panel, anchor: requests.append((
                node_id,
                panel,
                anchor.objectName(),
            ))
        )

        task_button = item.findChild(QObject, "workspaceTaskCountButton")
        note_button = item.findChild(QObject, "workspaceNoteCountButton")
        self.assertIsNotNone(task_button)
        self.assertIsNotNone(note_button)
        self.assertTrue(QMetaObject.invokeMethod(task_button, "clicked"))
        self.assertTrue(QMetaObject.invokeMethod(note_button, "clicked"))

        self.assertEqual(requests, [
            ("asset:1", "tasks", "workspaceTaskCountButton"),
            ("asset:1", "notes", "workspaceNoteCountButton"),
        ])

        item.deleteLater()
        theme.deleteLater()

    def test_process_count_buttons_request_the_task_picker(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml")),
        )
        item = component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="asset:1/process:model",
                nodeType="process",
                searchKey="demo/asset?code=ASSET001",
                title="Model",
                process="model",
                hasChildren=True,
                depth=1,
                tasks=2,
                comments=3,
                compactMode=False,
                width=640,
            )
        )
        self.assertIsNotNone(
            item,
            "\n".join(error.toString() for error in component.errors()),
        )
        requests = []
        item.processCountMenuRequested.connect(
            lambda node_id, panel, anchor: requests.append((
                node_id, panel, anchor.objectName(),
            ))
        )

        self.assertTrue(QMetaObject.invokeMethod(
            item.findChild(QObject, "workspaceTaskCountButton"), "clicked"
        ))
        self.assertTrue(QMetaObject.invokeMethod(
            item.findChild(QObject, "workspaceNoteCountButton"), "clicked"
        ))

        self.assertEqual(requests, [
            ("asset:1/process:model", "tasks", "workspaceTaskCountButton"),
            ("asset:1/process:model", "notes", "workspaceNoteCountButton"),
        ])

        item.deleteLater()
        theme.deleteLater()

    def test_preview_is_marked_revealed_when_image_becomes_ready(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        temporary = QTemporaryDir()
        self.assertTrue(temporary.isValid())
        image_path = Path(temporary.path()) / "preview.png"
        image = QImage(32, 32, QImage.Format_ARGB32)
        image.fill(QColor("#4f78d1"))
        self.assertTrue(image.save(str(image_path)))

        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml"))
        )
        item = component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="asset:preview",
                nodeType="sobject",
                searchKey="demo/asset?project=demo&code=ASSET001",
                title="Preview asset",
                hasChildren=False,
                depth=0,
                previewUrl=QUrl.fromLocalFile(str(image_path)).toString(),
                previewRevealed=False,
                compactMode=False,
                width=640,
            )
        )
        self.assertIsNotNone(
            item,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(660, 160)
        item.setParentItem(window.contentItem())
        window.show()

        source_image = item.findChild(QObject, "previewSourceImage")
        self.assertIsNotNone(source_image)
        for _attempt in range(40):
            if float(source_image.property("progress") or 0) >= 1:
                break
            QTest.qWait(10)

        self.assertGreaterEqual(
            float(source_image.property("progress") or 0), 1
        )
        self.assertEqual(controller.revealed_previews, ["asset:preview"])

        local_url = QUrl.fromLocalFile(str(image_path)).toString()
        self.assertEqual(
            item.property("dragImageSource").toString(), local_url
        )
        messages = []
        previous_handler = qInstallMessageHandler(
            lambda _kind, _context, message: messages.append(message)
        )
        try:
            item.setProperty(
                "previewUrl", "pending-preview:preview-download"
            )
            QTest.qWait(20)
        finally:
            qInstallMessageHandler(previous_handler)
        self.assertEqual(item.property("dragImageSource").toString(), "")
        self.assertFalse(any(
            "pending-preview:" in message for message in messages
        ), messages)

        window.close()
        item.deleteLater()
        theme.deleteLater()
        temporary.remove()

    def test_search_width_and_compact_view_share_the_compact_density(self):
        search_view = (
            ROOT / "thlib" / "ui" / "qml" / "SearchWorkspaceView.qml"
        ).read_text(encoding="utf-8")
        result_surface = (
            ROOT / "thlib" / "ui" / "qml" / "SearchResultSurface.qml"
        ).read_text(encoding="utf-8")
        self.assertIn("readonly property bool autoCompact: width < 445", search_view)
        self.assertIn(
            'autoCompact || appController.results_view_mode === "compact"',
            search_view,
        )
        self.assertIn("compactMode: root.compactRows", result_surface)
        results_area_start = search_view.index("id: resultsArea")
        results_area = search_view[
            results_area_start:
            search_view.index("id: results", results_area_start + 1)
        ]
        self.assertIn("color: root.theme.workspace", results_area)
        self.assertNotIn("remove: Transition", results_area)

    def test_snapshot_date_shows_pretty_value_and_exact_value_on_hover(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml"))
        )
        item = component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="snapshot:1",
                nodeType="snapshot",
                searchKey="sthpw/snapshot?code=SNAPSHOT00001",
                title="Asset_Publish.ma",
                version="v012",
                timestamp="2026-08-23 10:52:28",
                timestampPretty="2 hours ago",
                timestampSimple="2026 August 23 10:52:28",
                infoChips=[{
                    "label": "Maya",
                    "value": "Autodesk Maya 2025",
                    "url": "",
                }],
                fileExists=True,
                compactMode=False,
                width=640,
            )
        )
        self.assertIsNotNone(
            item,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(660, 120)
        item.setParentItem(window.contentItem())
        window.show()
        QTest.qWait(30)

        date_label = item.findChild(QObject, "workspaceSnapshotDate")
        snapshot_info = item.findChild(QObject, "workspaceSnapshotInfo")
        self.assertIsNotNone(date_label)
        self.assertIsNotNone(snapshot_info)
        self.assertTrue(snapshot_info.property("visible"))
        pending = list(snapshot_info.childItems())
        maya_label = None
        while pending and maya_label is None:
            child = pending.pop()
            pending.extend(child.childItems())
            if child.objectName() == "infoValueText":
                maya_label = child
        self.assertIsNotNone(maya_label)
        self.assertEqual(maya_label.property("text"), "Maya: Autodesk Maya 2025")
        self.assertGreater(snapshot_info.property("width"), 0)
        item.setProperty("width", 460)
        window.resize(480, 120)
        self.app.processEvents()
        self.assertGreater(snapshot_info.property("width"), 0)
        self.assertLessEqual(
            snapshot_info.property("x") + snapshot_info.property("width"),
            snapshot_info.parent().property("width"),
        )
        self.assertEqual(date_label.property("text"), "2 hours ago")
        center = date_label.mapToItem(
            window.contentItem(),
            QPointF(
                date_label.property("width") / 2,
                date_label.property("height") / 2,
            ),
        )
        QTest.mouseMove(window, QPoint(round(center.x()), round(center.y())))
        QTest.qWait(20)
        self.assertEqual(
            date_label.property("text"), "2026 August 23 10:52:28"
        )

        window.close()
        item.deleteLater()
        theme.deleteLater()

    def test_item_surface_elevation_avoids_per_delegate_shader_effects(self):
        surface = (
            ROOT / "thlib" / "ui" / "qml" / "controls" / "ItemSurface.qml"
        ).read_text(encoding="utf-8")
        self.assertIn('objectName: "itemSurfaceShadow"', surface)
        self.assertNotIn("Qt5Compat.GraphicalEffects", surface)
        self.assertNotIn("DropShadow", surface)

    def test_idle_workspace_delegates_stay_inside_render_object_budget(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml"))
        )
        cases = {
            "sobject": {
                "nodeType": "sobject",
                "searchKey": "demo/asset?code=ASSET001",
                "hasChildren": True,
                "depth": 0,
                "compactMode": False,
            },
            "snapshot": {
                "nodeType": "snapshot",
                "hasChildren": True,
                "depth": 2,
                "compactMode": False,
            },
            "file": {
                "nodeType": "file",
                "hasChildren": False,
                "depth": 3,
                "compactMode": False,
            },
            "relation": {
                "nodeType": "relation",
                "hasChildren": True,
                "depth": 1,
                "compactMode": True,
            },
        }
        items = []
        for kind, updates in cases.items():
            item = component.createWithInitialProperties(
                self.item_properties(
                    theme,
                    nodeId=f"budget:{kind}",
                    title=kind,
                    width=640,
                    **updates,
                )
            )
            self.assertIsNotNone(
                item,
                "\n".join(error.toString() for error in component.errors()),
            )
            items.append(item)
        self.app.processEvents()

        budgets = QML_RENDER_BUDGETS["WorkspaceResultItem"]
        for kind, item in zip(cases, items):
            budget = budgets[kind]
            self.assertLessEqual(
                len(item.findChildren(QObject)),
                budget["qobjects"],
                f"{kind} exceeded its idle QObject budget",
            )
            self.assertLessEqual(
                len(item.findChildren(QQuickItem)),
                budget["quickItems"],
                f"{kind} exceeded its idle QQuickItem budget",
            )

        for item in items:
            drop_presentation = item.findChild(
                QObject, "workspaceFileDropPresentation"
            )
            self.assertIsNotNone(drop_presentation)
            self.assertFalse(drop_presentation.property("active"))
            for ripple_loader in item.findChildren(
                QObject, "materialRippleVisualLoader"
            ):
                self.assertFalse(ripple_loader.property("active"))
                self.assertIsNone(ripple_loader.property("item"))
            for mask_loader in item.findChildren(
                QObject, "previewMaskLoader"
            ):
                self.assertFalse(mask_loader.property("active"))
                self.assertIsNone(mask_loader.property("item"))

        for item in items:
            item.deleteLater()
        theme.deleteLater()

    def test_idle_workspace_cards_stay_inside_render_object_budget(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "WorkspaceCard.qml"))
        )
        cases = {
            "sobject": {"nodeType": "sobject", "hasChildren": True},
            "snapshot": {"nodeType": "snapshot", "hasChildren": True},
            "file": {"nodeType": "file"},
            "relation": {"nodeType": "relation", "hasChildren": True},
        }
        cards = []
        for kind, updates in cases.items():
            card = component.createWithInitialProperties(
                self.card_properties(
                    theme,
                    nodeId=f"card-budget:{kind}",
                    title=kind,
                    **updates,
                )
            )
            self.assertIsNotNone(
                card,
                "\n".join(error.toString() for error in component.errors()),
            )
            cards.append(card)
        self.app.processEvents()

        budgets = QML_RENDER_BUDGETS["WorkspaceCard"]
        for kind, card in zip(cases, cards):
            budget = budgets[kind]
            self.assertLessEqual(
                len(card.findChildren(QObject)), budget["qobjects"],
                f"{kind} card exceeded its idle QObject budget",
            )
            self.assertLessEqual(
                len(card.findChildren(QQuickItem)), budget["quickItems"],
                f"{kind} card exceeded its idle QQuickItem budget",
            )
            count_controls = card.findChild(
                QObject, "workspaceCardCountControls"
            )
            self.assertIsNotNone(count_controls)
            self.assertEqual(
                count_controls.property("active"),
                kind == "sobject",
            )
            for ripple_loader in card.findChildren(
                QObject, "materialRippleVisualLoader"
            ):
                self.assertFalse(ripple_loader.property("active"))
                self.assertIsNone(ripple_loader.property("item"))
            for mask_loader in card.findChildren(
                QObject, "previewMaskLoader"
            ):
                self.assertFalse(mask_loader.property("active"))
                self.assertIsNone(mask_loader.property("item"))

        for card in cards:
            card.deleteLater()
        theme.deleteLater()

    def test_shared_disclosure_button_has_no_hover_or_pressed_surface(self):
        disclosure = (
            ROOT / "thlib" / "ui" / "qml" / "controls"
            / "DisclosureButton.qml"
        ).read_text(encoding="utf-8")
        self.assertNotIn("Rectangle {", disclosure)
        self.assertNotIn("pointer.containsMouse", disclosure)
        self.assertNotIn("pointer.pressed", disclosure)
        self.assertIn("loading && loadingRequested", disclosure)

    def test_regular_rows_do_not_alternate_background_color(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml"))
        )
        items = [
            component.createWithInitialProperties(
                self.item_properties(
                    theme,
                    index=index,
                    nodeId=f"process:{index}",
                    nodeType="process",
                    title=f"Process {index}",
                    depth=1,
                    compactMode=False,
                    width=640,
                )
            )
            for index in (0, 1)
        ]
        for item in items:
            self.assertIsNotNone(
                item,
                "\n".join(error.toString() for error in component.errors()),
            )
        self.app.processEvents()
        surfaces = [
            item.findChild(QObject, "workspaceItemSurface") for item in items
        ]
        self.assertTrue(all(surface is not None for surface in surfaces))
        self.assertEqual(
            surfaces[0].property("normalColor"),
            surfaces[1].property("normalColor"),
        )
        self.assertNotIn("root.index % 2", self.source)

        for item in items:
            item.deleteLater()
        theme.deleteLater()

    def test_nested_items_use_guides_indent_and_semantic_rails(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml"))
        )

        sobject = component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="sobject:child",
                nodeType="sobject",
                searchKey="demo/asset?project=demo&code=CHILD",
                title="Nested child",
                depth=2,
                compactMode=False,
                width=900,
            )
        )
        self.assertIsNotNone(
            sobject,
            "\n".join(error.toString() for error in component.errors()),
        )
        self.app.processEvents()

        surface = sobject.findChild(QObject, "workspaceItemSurface")
        guide = sobject.findChild(QObject, "workspaceHierarchyGuide")
        reveal = sobject.findChild(QObject, "hierarchyRevealAnimation").parent()
        animation = sobject.findChild(QObject, "hierarchyRevealAnimation")
        disclosure = sobject.findChild(QObject, "workspaceDisclosureIcon")
        self.assertIsNotNone(surface)
        self.assertIsNotNone(guide)
        self.assertIsNotNone(reveal)
        self.assertIsNotNone(animation)
        self.assertIsNotNone(disclosure)
        self.assertEqual(sobject.property("indent"), 48)
        self.assertEqual(surface.property("x"), 48)
        self.assertTrue(surface.property("railVisible"))
        self.assertTrue(guide.property("visible"))
        self.assertEqual(guide.property("depth"), 2)
        self.assertEqual(guide.property("indentStep"), 24)

        spinner = sobject.findChild(QObject, "workspaceDisclosureSpinner")
        self.assertIsNone(spinner)
        sobject.setProperty("nodeLoading", True)
        self.app.processEvents()
        disclosure_area = sobject.findChild(
            QObject, "workspaceDisclosureArea"
        )
        disclosure_area.setProperty("loadingRequested", True)
        self.app.processEvents()
        spinner = sobject.findChild(QObject, "workspaceDisclosureSpinner")
        self.assertIsNotNone(spinner)
        self.assertTrue(disclosure_area.property("showLoading"))
        QTest.qWait(int(theme.property("motionFast")) + 20)
        self.assertTrue(spinner.property("visible"))
        sobject.setProperty("nodeLoading", False)
        self.app.processEvents()
        self.assertFalse(
            disclosure_area.property("loadingRequested")
        )

        reveal.setProperty("progress", 0.0)
        self.assertTrue(QMetaObject.invokeMethod(animation, "start"))
        QTest.qWait(int(theme.property("motionMedium")) + 50)
        self.assertAlmostEqual(
            reveal.property("progress"), 1.0, places=2
        )

        self.assertEqual(disclosure.property("rotation"), 90)

        snapshot = component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="snapshot:child",
                nodeType="snapshot",
                title="publish.ma",
                fileSize="4.10 MB",
                depth=1,
                compactMode=False,
                width=900,
            )
        )
        leaf_snapshot = component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="snapshot:leaf",
                nodeType="snapshot",
                title="ep_79_Sh_123_render_publish_v001.mov",
                fileSize="2.75 MB",
                depth=1,
                hasChildren=False,
                compactMode=True,
                width=420,
            )
        )
        process = component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="process:model",
                nodeType="process",
                title="model",
                depth=1,
                compactMode=False,
                width=900,
            )
        )
        leaf_process = component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="process:leaf",
                nodeType="process",
                title="cache",
                depth=1,
                hasChildren=False,
                compactMode=True,
                width=900,
            )
        )
        relation = component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="relation:assets",
                nodeType="relation",
                title="Assets",
                depth=1,
                compactMode=False,
                width=900,
            )
        )
        for item in (
            snapshot, leaf_snapshot, process, leaf_process, relation
        ):
            self.assertIsNotNone(
                item,
                "\n".join(error.toString() for error in component.errors()),
            )
            self.app.processEvents()
            item_surface = item.findChild(QObject, "workspaceItemSurface")
            self.assertIsNotNone(item_surface)
            self.assertEqual(
                item_surface.property("railVisible"),
                item.property("nodeType") == "relation",
            )

        snapshot_surface = snapshot.findChild(
            QObject, "workspaceItemSurface"
        )
        self.assertEqual(snapshot.property("indent"), 24)
        self.assertEqual(snapshot.property("height"), 84)
        self.assertEqual(
            snapshot_surface.property("x"), snapshot.property("indent")
        )
        self.assertEqual(snapshot_surface.property("borderWidth"), 0)
        self.assertEqual(
            snapshot_surface.property("cornerRadius"),
            theme.property("snapshotRadius"),
        )
        self.assertLess(
            snapshot_surface.property("cornerRadius"),
            surface.property("cornerRadius"),
        )
        self.assertFalse(snapshot_surface.property("elevated"))
        self.assertNotIn("transform: Translate", self.source)

        snapshot_disclosure = snapshot.findChild(
            QObject, "workspaceDisclosureArea"
        )
        snapshot_preview = snapshot.findChild(
            QObject, "workspaceItemPreview"
        )
        snapshot_size_badge = snapshot.findChild(
            QObject, "workspaceSnapshotSizeBadge"
        )
        self.assertIsNotNone(snapshot_size_badge)
        self.assertTrue(snapshot_size_badge.property("visible"))
        self.assertEqual(snapshot_size_badge.property("height"), 24)
        self.assertEqual(
            snapshot_size_badge.property("radius"),
            snapshot_size_badge.property("height") / 2,
        )
        self.assertEqual(snapshot_preview.property("y"), 13)
        snapshot_border_left = (
            snapshot_surface.property("x")
            + snapshot_surface.property("inset")
        )
        disclosure_center = (
            snapshot_disclosure.property("x")
            + snapshot_disclosure.property("width") / 2
        )
        self.assertAlmostEqual(
            disclosure_center,
            (snapshot_border_left + snapshot_preview.property("x")) / 2,
            delta=1,
        )

        leaf_surface = leaf_snapshot.findChild(
            QObject, "workspaceItemSurface"
        )
        leaf_preview = leaf_snapshot.findChild(
            QObject, "workspaceItemPreview"
        )
        self.assertEqual(leaf_snapshot.property("height"), 56)
        self.assertEqual(leaf_preview.property("y"), 9)
        leaf_border_left = (
            leaf_surface.property("x") + leaf_surface.property("inset")
        )
        self.assertEqual(leaf_preview.property("x") - leaf_border_left, 12)
        self.assertLess(
            leaf_preview.property("x"), snapshot_preview.property("x")
        )
        compact_snapshot_size = leaf_snapshot.findChild(
            QObject, "workspaceCompactSnapshotSizeBadge"
        )
        self.assertIsNotNone(compact_snapshot_size)
        self.assertTrue(compact_snapshot_size.property("visible"))
        self.assertEqual(compact_snapshot_size.property("text"), "2.75 MB")
        compact_title = leaf_snapshot.findChild(
            QObject, "workspaceCompactTitle"
        )
        compact_body = compact_snapshot_size.parent()
        self.assertAlmostEqual(
            compact_snapshot_size.property("x")
                + compact_snapshot_size.property("width"),
            compact_body.property("width"),
            delta=1,
        )
        self.assertLessEqual(
            compact_title.property("x") + compact_title.property("width"),
            compact_snapshot_size.property("x") - 7,
        )

        process_surface = process.findChild(
            QObject, "workspaceItemSurface"
        )
        process_disclosure = process.findChild(
            QObject, "workspaceDisclosureArea"
        )
        process_preview = process.findChild(
            QObject, "workspaceItemPreview"
        )
        self.assertEqual(
            process_surface.property("x"), process.property("indent") + 32
        )
        self.assertLessEqual(
            process_disclosure.property("x")
                + process_disclosure.property("width"),
            process_surface.property("x"),
        )
        leaf_process_preview = leaf_process.findChild(
            QObject, "workspaceItemPreview"
        )
        self.assertEqual(
            leaf_process_preview.property("x"),
            process_preview.property("x"),
        )
        compact_process_title = leaf_process.findChild(
            QObject, "workspaceCompactTitle"
        )
        self.assertIsNotNone(compact_process_title)
        self.assertGreater(
            compact_process_title.property("font").pointSizeF(), 9.0
        )

        relation_surface = relation.findChild(
            QObject, "workspaceItemSurface"
        )
        self.assertEqual(
            relation_surface.property("x"), relation.property("indent") + 32
        )
        self.assertEqual(
            relation_surface.property("railX"),
            relation_surface.property("inset") + 3,
        )

        for item in (
            sobject, snapshot, leaf_snapshot, process, leaf_process, relation
        ):
            item.deleteLater()
        theme.deleteLater()

    def test_inserted_child_rows_arm_one_reveal_generation(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        controls_url = QUrl.fromLocalFile(str(qml_dir / "controls")).toString()
        engine = QQmlEngine()
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(engine)
        component.setData(
            f'''import QtQuick
import "{controls_url}" as Controls
Item {{
    id: host
    property var uiTheme
    property real contentY: 0
    property real originY: 0
    property real contentHeight: 100
    property int firstDelay: motion.staggerDelay(1, 1)
    property int laterDelay: motion.staggerDelay(4, 1)
    function cancelWheelScroll() {{}}
    function forceLayout() {{}}
    function triggerInsert() {{
        motion.pendingOwnerId = "owner"
        rows.append({{"key": "child"}})
    }}
    function triggerCollapse() {{ motion.toggle("owner", false, false) }}
    function cancelCollapseWithSecondClick() {{
        motion.toggle("owner", false, false)
        motion.toggle("owner", false, false)
    }}
    property int toggleCalls: 0
    ListModel {{
        id: rows
        ListElement {{ key: "owner" }}
    }}
    Controls.TreeExpansionMotion {{
        id: motion
        objectName: "testedTreeExpansionMotion"
        theme: host.uiTheme
        view: host
        model: rows
        ownerRowForId: function(nodeId) {{ return nodeId === "owner" ? 0 : -1 }}
        descendantEndRowForId: function(nodeId) {{ return 1 }}
        toggleNode: function(nodeId, recursive) {{ host.toggleCalls += 1 }}
    }}
}}'''.encode("utf-8"),
            QUrl.fromLocalFile(str(qml_dir / "TreeExpansionMotionTest.qml")),
        )
        host = component.createWithInitialProperties({"uiTheme": theme})
        self.assertIsNotNone(
            host,
            "\n".join(error.toString() for error in component.errors()),
        )
        motion = host.findChild(QObject, "testedTreeExpansionMotion")
        self.assertIsNotNone(motion)
        self.assertTrue(QMetaObject.invokeMethod(host, "triggerInsert"))
        self.app.processEvents()
        self.assertEqual(motion.property("generation"), 1)
        self.assertEqual(motion.property("firstRow"), 1)
        self.assertEqual(motion.property("lastRow"), 1)
        self.assertTrue(motion.property("active"))
        self.assertEqual(host.property("firstDelay"), 0)
        self.assertGreater(host.property("laterDelay"), 0)
        self.assertTrue(QMetaObject.invokeMethod(host, "triggerCollapse"))
        self.app.processEvents()
        self.assertTrue(motion.property("collapseActive"))
        QTest.qWait(int(theme.property("motionMedium")) + 60)
        self.assertFalse(motion.property("collapseActive"))
        committed_calls = host.property("toggleCalls")
        self.assertTrue(
            QMetaObject.invokeMethod(host, "cancelCollapseWithSecondClick")
        )
        self.app.processEvents()
        self.assertFalse(motion.property("collapseActive"))
        self.assertEqual(motion.property("collapseOwnerId"), "")
        self.assertEqual(host.property("toggleCalls"), committed_calls)

        host.deleteLater()
        theme.deleteLater()

    def test_new_child_delegate_starts_transparent_before_deferred_fade(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        controls_url = QUrl.fromLocalFile(str(qml_dir / "controls")).toString()
        engine = QQmlEngine()
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(engine)
        component.setData(
            f'''import QtQuick
import "{controls_url}" as Controls
Item {{
    property var uiTheme
    function startCollapse() {{
        fakeView.treeCollapseActive = true
        fakeView.treeCollapseGeneration += 1
    }}
    function cancelCollapse() {{ fakeView.treeCollapseActive = false }}
    QtObject {{
        id: fakeView
        property bool treeRevealActive: true
        property int treeRevealGeneration: 7
        property int treeRevealFirstRow: 1
        property int treeRevealLastRow: 3
        property bool treeCollapseActive: false
        property int treeCollapseGeneration: 0
        property int treeCollapseFirstRow: 1
        property int treeCollapseLastRow: 3
        function treeStaggerDelay(row, firstRow) {{ return 0 }}
    }}
    Controls.HierarchyReveal {{
        objectName: "newChildReveal"
        theme: parent.uiTheme
        view: fakeView
        identity: "child"
        row: 2
    }}
}}'''.encode("utf-8"),
            QUrl.fromLocalFile(str(qml_dir / "HierarchyRevealTest.qml")),
        )
        host = component.createWithInitialProperties({"uiTheme": theme})
        self.assertIsNotNone(
            host,
            "\n".join(error.toString() for error in component.errors()),
        )
        reveal = host.findChild(QObject, "newChildReveal")
        self.assertIsNotNone(reveal)
        self.assertEqual(reveal.property("progress"), 0)
        self.app.processEvents()
        QTest.qWait(int(theme.property("motionMedium")) + 30)
        self.assertAlmostEqual(reveal.property("progress"), 1.0, places=2)
        self.assertTrue(QMetaObject.invokeMethod(host, "startCollapse"))
        QTest.qWait(max(20, int(theme.property("motionMedium")) // 3))
        self.assertLess(reveal.property("progress"), 1.0)
        self.assertTrue(QMetaObject.invokeMethod(host, "cancelCollapse"))
        QTest.qWait(int(theme.property("motionFast")) + 30)
        self.assertAlmostEqual(reveal.property("progress"), 1.0, places=2)

        host.deleteLater()
        theme.deleteLater()

    def test_deferred_delegate_work_stops_when_delegate_is_destroyed(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        messages = []
        previous_handler = qInstallMessageHandler(
            lambda _kind, _context, message: messages.append(message)
        )
        item = None
        theme = None
        try:
            engine = QQmlEngine()
            controller = _WorkspaceAppController()
            engine.rootContext().setContextProperty(
                "appController", controller
            )
            theme_component = QQmlComponent(
                engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
            )
            theme = theme_component.createWithInitialProperties({"dark": True})
            for filename, properties in (
                ("WorkspaceResultItem.qml", self.item_properties),
                ("WorkspaceCard.qml", self.card_properties),
            ):
                with self.subTest(component=filename):
                    messages.clear()
                    component = QQmlComponent(
                        engine, QUrl.fromLocalFile(str(qml_dir / filename))
                    )
                    for rearm in (False, True):
                        item = component.createWithInitialProperties(
                            properties(theme)
                        )
                        self.assertIsNotNone(
                            item,
                            "\n".join(
                                error.toString() for error in component.errors()
                            ),
                        )
                        if rearm:
                            self.app.processEvents()
                            armed = QMetaObject.invokeMethod(
                                item, "armTransientAnimations"
                            )
                            self.assertTrue(armed)

                        # Both initial creation and delegate reuse can queue
                        # work just before a model reset destroys the item.
                        item.deleteLater()
                        QCoreApplication.sendPostedEvents(
                            item, QEvent.DeferredDelete
                        )
                        item = None
                        self.app.processEvents()
                    self.assertEqual(messages, [])
        finally:
            qInstallMessageHandler(previous_handler)
            if item is not None:
                item.deleteLater()
            if theme is not None:
                theme.deleteLater()

    def test_card_animation_arm_is_immediate_and_has_no_stale_work(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "WorkspaceCard.qml"))
        )
        card = component.createWithInitialProperties(self.card_properties(theme))
        self.assertIsNotNone(
            card, "\n".join(error.toString() for error in component.errors())
        )
        try:
            self.assertFalse(card.property("transientAnimationsSuppressed"))
            cancelled = QMetaObject.invokeMethod(
                card, "cancelTransientAnimationArm"
            )
            self.assertTrue(cancelled)
            self.app.processEvents()
            self.assertTrue(card.property("transientAnimationsSuppressed"))

            card.setProperty("viewPooled", True)
            armed = QMetaObject.invokeMethod(card, "armTransientAnimations")
            self.assertTrue(armed)
            self.app.processEvents()
            self.assertTrue(card.property("transientAnimationsSuppressed"))

            card.setProperty("viewPooled", False)
            armed = QMetaObject.invokeMethod(card, "armTransientAnimations")
            self.assertTrue(armed)
            self.app.processEvents()
            self.assertFalse(card.property("transientAnimationsSuppressed"))
        finally:
            card.deleteLater()
            QCoreApplication.sendPostedEvents(card, QEvent.DeferredDelete)
            theme.deleteLater()

    def test_workspace_deferrals_do_not_capture_recycled_delegates(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        hierarchy_source = (
            qml_dir / "controls" / "HierarchyReveal.qml"
        ).read_text(encoding="utf-8")
        search_source = (
            qml_dir / "SearchWorkspaceView.qml"
        ).read_text(encoding="utf-8")

        card_source = (qml_dir / "WorkspaceCard.qml").read_text(encoding="utf-8")
        for source in (self.source, card_source, hierarchy_source):
            self.assertNotIn("Qt.callLater", source)
        self.assertIn(
            "const surface = root.activeResultSurface",
            search_source,
        )
        self.assertNotIn("id: transientAnimationArm", self.source)
        self.assertNotIn("id: deferredSync", hierarchy_source)
        self.assertIn(
            "searchTabsView.schedulePositionAtIndex(index)", search_source
        )
        self.assertNotIn("searchTab.index, ListView.Contain", search_source)

        engine = QQmlEngine()
        search_component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "SearchWorkspaceView.qml")),
        )
        self.assertNotEqual(
            search_component.status(),
            QQmlComponent.Status.Error,
            "\n".join(
                error.toString() for error in search_component.errors()
            ),
        )

    def test_reused_nested_tree_rows_never_keep_zero_opacity(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        controls_url = QUrl.fromLocalFile(str(qml_dir / "controls")).toString()
        engine = QQmlEngine()
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(engine)
        component.setData(
            f'''import QtQuick
import "{controls_url}" as Controls
Item {{
    id: host
    width: 360
    height: 220
    property var uiTheme
    property bool rootExpanded: false
    property bool childExpanded: false
    property int pooledCount: 0
    property int reusedCount: 0

    function rowFor(nodeId) {{
        for (let row = 0; row < rows.count; ++row) {{
            if (rows.get(row).nodeId === nodeId)
                return row
        }}
        return -1
    }}
    function descendantEnd(nodeId) {{
        const owner = rowFor(nodeId)
        if (owner < 0)
            return -1
        const depth = rows.get(owner).depth
        let end = owner
        while (end + 1 < rows.count && rows.get(end + 1).depth > depth)
            end += 1
        return end
    }}
    function toggleRoot() {{
        motion.toggle("root", false, !rootExpanded)
    }}
    function toggleChild() {{
        motion.toggle("child", false, !childExpanded)
    }}
    function mutateBranch(nodeId) {{
        if (nodeId === "root") {{
            if (rootExpanded) {{
                if (rows.count > 1)
                    rows.remove(1, rows.count - 1)
                rootExpanded = false
                childExpanded = false
            }} else {{
                rows.append({{"nodeId": "child", "depth": 1}})
                rows.append({{"nodeId": "rootProcess", "depth": 1}})
                rootExpanded = true
            }}
            return
        }}
        if (childExpanded) {{
            rows.remove(2, 2)
            childExpanded = false
        }} else {{
            rows.insert(2, {{"nodeId": "childSnapshot", "depth": 2}})
            rows.insert(3, {{"nodeId": "childProcess", "depth": 2}})
            childExpanded = true
        }}
    }}

    ListModel {{
        id: rows
        ListElement {{ nodeId: "root"; depth: 0 }}
    }}
    ListView {{
        id: treeList
        objectName: "recyclingTreeList"
        anchors.fill: parent
        model: rows
        reuseItems: true
        cacheBuffer: 0
        property alias treeRevealGeneration: motion.generation
        property alias treeRevealFirstRow: motion.firstRow
        property alias treeRevealLastRow: motion.lastRow
        property alias treeRevealActive: motion.active
        property alias treeCollapseGeneration: motion.collapseGeneration
        property alias treeCollapseFirstRow: motion.collapseFirstRow
        property alias treeCollapseLastRow: motion.collapseLastRow
        property alias treeCollapseActive: motion.collapseActive
        property alias treeCollapseOwnerId: motion.collapseOwnerId
        function cancelWheelScroll() {{}}
        function treeStaggerDelay(row, firstRow) {{
            return motion.staggerDelay(row, firstRow)
        }}

        delegate: Item {{
            id: treeDelegate
            required property int index
            required property string nodeId
            required property int depth
            property bool pooledState: false
            objectName: "treeDelegate_" + nodeId
            width: treeList.width
            height: 30
            opacity: reveal.progress
            ListView.onPooled: {{
                pooledState = true
                host.pooledCount += 1
            }}
            ListView.onReused: {{
                pooledState = false
                host.reusedCount += 1
            }}
            Controls.HierarchyReveal {{
                id: reveal
                theme: host.uiTheme
                view: treeList
                identity: treeDelegate.nodeId
                row: treeDelegate.index
                pooled: treeDelegate.pooledState
            }}
        }}
    }}
    Controls.TreeExpansionMotion {{
        id: motion
        theme: host.uiTheme
        view: treeList
        model: rows
        ownerRowForId: function(nodeId) {{ return host.rowFor(nodeId) }}
        descendantEndRowForId: function(nodeId) {{
            return host.descendantEnd(nodeId)
        }}
        toggleNode: function(nodeId, recursive) {{ host.mutateBranch(nodeId) }}
    }}
}}'''.encode("utf-8"),
            QUrl.fromLocalFile(str(qml_dir / "TreeReuseTest.qml")),
        )
        host = component.createWithInitialProperties({"uiTheme": theme})
        self.assertIsNotNone(
            host,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(360, 220)
        host.setParentItem(window.contentItem())
        window.show()
        wait_time = int(theme.property("motionMedium") * 2 + 50)

        def visible_delegate(node_id):
            pending = list(host.childItems())
            while pending:
                child = pending.pop()
                if child.objectName() == f"treeDelegate_{node_id}":
                    return child
                pending.extend(child.childItems())
            return None

        def assert_visible(*node_ids):
            for node_id in node_ids:
                delegate = visible_delegate(node_id)
                self.assertIsNotNone(delegate, node_id)
                self.assertAlmostEqual(
                    delegate.property("opacity"), 1.0, places=2,
                    msg=node_id,
                )

        self.assertTrue(QMetaObject.invokeMethod(host, "toggleRoot"))
        QTest.qWait(wait_time)
        assert_visible("child", "rootProcess")
        for _cycle in range(6):
            self.assertTrue(QMetaObject.invokeMethod(host, "toggleChild"))
            QTest.qWait(wait_time)
            assert_visible("childSnapshot", "childProcess", "rootProcess")
            self.assertTrue(QMetaObject.invokeMethod(host, "toggleChild"))
            QTest.qWait(wait_time)
            assert_visible("child", "rootProcess")
        for _cycle in range(4):
            self.assertTrue(QMetaObject.invokeMethod(host, "toggleRoot"))
            QTest.qWait(wait_time)
            self.assertTrue(QMetaObject.invokeMethod(host, "toggleRoot"))
            QTest.qWait(wait_time)
            assert_visible("child", "rootProcess")

        self.assertTrue(QMetaObject.invokeMethod(host, "toggleChild"))
        QTest.qWait(wait_time)
        assert_visible("childSnapshot", "childProcess", "rootProcess")
        self.assertGreater(host.property("pooledCount"), 0)
        self.assertGreater(host.property("reusedCount"), 0)

        window.close()
        window.deleteLater()
        host.deleteLater()
        theme.deleteLater()

    def test_process_and_relation_rows_use_readable_compact_typography(self):
        process_start = self.source.index("id: processBodyComponent")
        relation_start = self.source.index(
            "id: relationBodyComponent", process_start
        )
        file_start = self.source.index("id: fileBodyComponent", relation_start)

        process = self.source[process_start:relation_start]
        relation = self.source[relation_start:file_start]

        self.assertIn("font.pointSize: Controls.Typography.label", process)
        self.assertIn("font.pointSize: Controls.Typography.label", relation)

    def test_relation_child_count_stays_right_of_item_actions(self):
        self.assertIn(
            "anchors.rightMargin: 0", self.source
        )
        self.assertIn(
            'root.nodeType === "relation"',
            self.source[self.source.index("id: hoverControls"):],
        )
        self.assertIn(
            "? root.relationCountTrailingReserve", self.source
        )

    def test_narrow_relation_actions_appear_only_on_hover(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        self.assertIsNotNone(
            theme,
            "\n".join(error.toString() for error in theme_component.errors()),
        )
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml"))
        )
        item = component.createWithInitialProperties(
            self.item_properties(theme, itemControls=[
                {"command": "link_related", "icon": "link", "tip": "Link"},
                {"command": "add_related", "icon": "add", "tip": "Add"},
            ])
        )
        self.assertIsNotNone(
            item,
            "\n".join(error.toString() for error in component.errors()),
        )
        QTest.qWait(20)
        actions = item.findChild(QObject, "workspaceItemActions")
        count = item.findChild(QObject, "workspaceRelationChildCount")
        self.assertIsNotNone(actions)
        self.assertIsNotNone(count)
        self.assertFalse(actions.property("active"))
        self.assertTrue(count.property("visible"))
        self.assertEqual(count.property("text"), "|  12")

        window = QQuickWindow()
        window.resize(300, 100)
        item.setParentItem(window.contentItem())
        window.show()
        QTest.qWait(30)

        QTest.mouseMove(window, QPoint(150, 19))
        QTest.qWait(20)
        self.assertTrue(actions.property("active"))
        self.assertGreater(actions.property("implicitWidth"), 0)

        actions_right = actions.mapToItem(
            item, QPointF(actions.property("width"), 0)
        ).x()
        count_left = count.mapToItem(item, QPointF(0, 0)).x()
        self.assertLessEqual(actions_right, count_left)
        self.assertLessEqual(
            count.mapToItem(
                item, QPointF(count.property("width"), 0)
            ).x(),
            item.property("width"),
        )

        window.close()
        window.deleteLater()
        item.deleteLater()
        theme.deleteLater()

    def test_active_item_actions_use_the_dense_content_palette(self):
        controls_start = self.source.index("id: hoverControlsComponent")
        controls_end = self.source.index(
            "id: communicationControls", controls_start
        )
        controls = self.source[controls_start:controls_end]
        self.assertIn("root.theme.contentSelection", controls)
        self.assertIn("root.theme.contentSelectionText", controls)
        self.assertNotIn(
            "modelData.active ? root.theme.selected", controls
        )

        card = (
            ROOT / "thlib" / "ui" / "qml" / "WorkspaceCard.qml"
        ).read_text(encoding="utf-8")
        self.assertIn("modelData.active", card)
        self.assertIn("root.theme.contentSelection", card)
        self.assertIn("root.theme.contentAccent", card)

    def test_persistent_knowledge_button_invokes_the_native_item_action(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml"))
        )
        item = component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="sobject:asset:wiki",
                nodeType="sobject",
                searchKey="demo/assets?code=HERO",
                depth=0,
                itemControls=[{
                    "command": "knowledge_article",
                    "icon": "book-open",
                    "tip": "Open linked Knowledge Base article",
                    "persistent": True,
                    "success": True,
                }],
            )
        )
        self.assertIsNotNone(
            item,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(300, 100)
        item.setParentItem(window.contentItem())
        window.show()
        self.app.processEvents()

        pending = list(item.childItems())
        action = None
        while pending:
            child = pending.pop()
            if child.objectName() == "workspaceItemAction_knowledge_article":
                action = child
                break
            pending.extend(child.childItems())
        self.assertIsNotNone(action)
        self.assertTrue(action.property("visible"))
        center = action.mapToScene(QPointF(
            action.width() / 2, action.height() / 2,
        ))
        QTest.mouseClick(window, Qt.LeftButton, pos=center.toPoint())
        self.app.processEvents()

        self.assertEqual(controller.item_actions, [(
            "knowledge_article", "sobject:asset:wiki",
        )])

        window.close()
        window.deleteLater()
        item.deleteLater()
        theme.deleteLater()
        engine.deleteLater()

    def test_persistent_knowledge_button_does_not_move_on_hover(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml"))
        )
        item = component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="sobject:asset:wiki-position",
                nodeType="sobject",
                searchKey="demo/assets?code=HERO",
                depth=0,
                width=420,
                itemControls=[
                    {
                        "command": "repo_sync",
                        "icon": "repository-sync",
                    },
                    {
                        "command": "relations",
                        "icon": "sitemap",
                    },
                    {
                        "command": "knowledge_article",
                        "icon": "book-open",
                        "persistent": True,
                        "success": True,
                    },
                ],
            )
        )
        self.assertIsNotNone(
            item,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(440, 120)
        item.setParentItem(window.contentItem())
        window.show()
        self.assertTrue(QTest.qWaitForWindowExposed(window))
        self.app.processEvents()

        def action(command):
            pending = list(item.childItems())
            while pending:
                child = pending.pop()
                if child.objectName() == f"workspaceItemAction_{command}":
                    return child
                pending.extend(child.childItems())
            return None

        knowledge = action("knowledge_article")
        repo_sync = action("repo_sync")
        relations = action("relations")
        self.assertIsNotNone(knowledge)
        self.assertIsNotNone(repo_sync)
        self.assertIsNotNone(relations)

        QTest.mouseMove(window, QPoint(430, 110))
        self.app.processEvents()
        self.assertFalse(repo_sync.property("visible"))
        resting_x = knowledge.mapToScene(QPointF(0, 0)).x()

        item.setProperty("transientAnimationsSuppressed", False)
        QTest.mouseMove(window, QPoint(200, 32))
        self.app.processEvents()
        self.assertTrue(repo_sync.property("visible"))
        hovered_x = knowledge.mapToScene(QPointF(0, 0)).x()

        self.assertAlmostEqual(hovered_x, resting_x)

        window.close()
        window.deleteLater()
        item.deleteLater()
        theme.deleteLater()
        engine.deleteLater()

    def test_reused_action_rows_keep_one_stable_vertical_position(self):
        hover_start = self.source.index("id: hoverControls")
        communication_start = self.source.index(
            "id: communicationControls", hover_start
        )
        communication_end = self.source.index(
            "MaterialRipple {", communication_start
        )
        hover = self.source[hover_start:communication_start]
        communication = self.source[
            communication_start:communication_end
        ]

        self.assertIn(
            "y: Math.round((root.height - height) / 2)", hover
        )
        self.assertIn(
            "y: Math.round((root.height - height) / 2)", communication
        )
        for source in (hover, communication):
            self.assertNotIn("anchors.verticalCenter", source)
            self.assertNotIn("anchors.bottom:", source)

    def test_full_sobject_uses_three_line_card_and_inline_actions(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml"))
        )
        item = component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="sobject:asset:1",
                nodeType="sobject",
                searchKey="demo/asset?project=demo&code=ASSET001",
                title="Ep_23_2",
                subtitle="Add the intro and place the character",
                compactMode=False,
                depth=0,
                comments=3,
                tasks=7,
                fileExists=True,
                itemControls=[
                    {"command": "repo_sync", "icon": "repository-sync"},
                    {"command": "watch_folder", "icon": "visibility_off"},
                    {"command": "relations", "icon": "sitemap"},
                ],
                progressItems=[{
                    "name": "progress",
                    "label": "0 / 0",
                    "color": "#d65b67",
                }],
                infoChips=[{
                    "kind": "link",
                    "text": "Script",
                    "url": "https://example.invalid/script",
                }],
                width=900,
            )
        )
        self.assertIsNotNone(
            item,
            "\n".join(error.toString() for error in component.errors()),
        )
        self.app.processEvents()

        surface = item.findChild(QObject, "workspaceItemSurface")
        shadow = item.findChild(QObject, "itemSurfaceShadow")
        disclosure = item.findChild(QObject, "workspaceDisclosureArea")
        preview = item.findChild(QObject, "workspaceItemPreview")
        body = item.findChild(QObject, "workspaceObjectBody")
        title = item.findChild(QObject, "workspaceObjectTitle")
        subtitle = item.findChild(QObject, "workspaceObjectSubtitle")
        metadata = item.findChild(QObject, "workspaceObjectMetadata")
        actions = item.findChild(QObject, "workspaceItemActions")
        communication = item.findChild(
            QObject, "workspaceCommunicationControls"
        )
        info_strip = item.findChild(QObject, "infoValueStrip")

        for child in (
            surface, shadow, disclosure, preview, body, title, subtitle, metadata,
            actions, communication, info_strip,
        ):
            self.assertIsNotNone(child)
        self.assertEqual(item.property("height"), 100)
        self.assertEqual(surface.property("borderWidth"), 1)
        self.assertGreater(surface.property("cornerRadius"), 8)
        self.assertTrue(surface.property("elevated"))
        self.assertTrue(surface.property("railVisible"))
        self.assertEqual(surface.property("railWidth"), 4)
        self.assertTrue(shadow.property("visible"))
        self.assertLess(
            surface.property("railX"), disclosure.property("x")
        )
        self.assertEqual(disclosure.property("width"), 36)
        self.assertEqual(preview.property("width"), 68)
        self.assertGreater(preview.property("x"), disclosure.property("x"))
        self.assertFalse(actions.property("active"))
        self.assertEqual(title.property("rightPadding"), 0)
        self.assertAlmostEqual(
            title.property("width"), title.property("implicitWidth")
        )
        item.setProperty("transientAnimationsSuppressed", False)
        item.setProperty("controlHoverActive", True)
        self.app.processEvents()
        self.assertTrue(actions.property("active"))
        self.assertGreater(actions.property("implicitWidth"), 0)
        self.assertEqual(info_strip.property("separatorText"), "|")

        action_center = actions.mapToItem(
            item, QPointF(0, actions.property("height") / 2)
        ).y()
        communication_center = communication.mapToItem(
            item, QPointF(0, communication.property("height") / 2)
        ).y()
        self.assertAlmostEqual(action_center, item.property("height") / 2, 1)
        self.assertAlmostEqual(
            communication_center, item.property("height") / 2, 1
        )
        title_right = title.mapToItem(
            item, QPointF(title.property("width"), 0)
        ).x()
        actions_left = actions.mapToItem(item, QPointF(0, 0)).x()
        self.assertLessEqual(title_right, actions_left)
        self.assertLess(
            metadata.mapToItem(item, QPointF(0, 0)).y(),
            item.property("height"),
        )

        item.deleteLater()
        theme.deleteLater()

    def test_sobject_title_keeps_priority_over_trailing_actions(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml"))
        )
        item = component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="sobject:asset:narrow",
                nodeType="sobject",
                title="Episodes",
                compactMode=False,
                depth=0,
                comments=3,
                tasks=7,
                itemControls=[
                    {"command": "repo_sync", "icon": "repository-sync"},
                    {"command": "watch_folder", "icon": "visibility_off"},
                    {"command": "relations", "icon": "sitemap"},
                ],
                width=320,
            )
        )
        self.assertIsNotNone(
            item,
            "\n".join(error.toString() for error in component.errors()),
        )
        QTest.qWait(20)

        title = item.findChild(QObject, "workspaceObjectTitle")
        quick_actions = item.findChild(
            QObject, "workspaceObjectInlineSnapshotActions"
        )
        self.assertFalse(
            title.property("truncated"),
            f"width={title.property('width')} "
            f"implicit={title.property('implicitWidth')} "
            f"content={title.property('implicitContentWidth')} "
            f"text={title.property('text')!r}",
        )
        self.assertAlmostEqual(
            title.property("width"), title.property("titleWidth")
        )
        self.assertFalse(quick_actions.property("revealed"))

        item.deleteLater()
        theme.deleteLater()
        engine.deleteLater()

    def test_title_hover_exposes_direct_snapshot_actions(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml"))
        )

        for node_type, title_name, actions_name, compact in (
            (
                "sobject",
                "workspaceObjectTitle",
                "workspaceObjectInlineSnapshotActions",
                False,
            ),
            (
                "snapshot",
                "workspaceSnapshotTitle",
                "workspaceSnapshotInlineSnapshotActions",
                False,
            ),
            (
                "sobject",
                "workspaceObjectTitle",
                "workspaceObjectInlineSnapshotActions",
                True,
            ),
            (
                "snapshot",
                "workspaceCompactTitle",
                "workspaceSnapshotInlineSnapshotActions",
                True,
            ),
        ):
            controller.set_maya_dcc_selected(False)
            density = "compact" if compact else "full"
            node_id = f"{node_type}:quick-actions:{density}"
            item = component.createWithInitialProperties(
                self.item_properties(
                    theme,
                    nodeId=node_id,
                    nodeType=node_type,
                    title="egg_face.ma" if node_type == "snapshot" else "egg_face",
                    compactMode=compact,
                    depth=0,
                    fileExists=True,
                    width=900,
                )
            )
            self.assertIsNotNone(
                item,
                "\n".join(error.toString() for error in component.errors()),
            )
            window = QQuickWindow()
            window.resize(920, 140)
            item.setParentItem(window.contentItem())
            window.show()
            self.assertTrue(QTest.qWaitForWindowExposed(window))
            self.app.processEvents()

            title = item.findChild(QObject, title_name)
            actions = item.findChild(QObject, actions_name)
            for child in (title, actions):
                self.assertIsNotNone(child)

            self.assertFalse(actions.property("revealed"))
            self.assertIsNone(
                item.findChild(QObject, "workspaceInlineSaveAction")
            )

            title_center = title.mapToScene(QPointF(
                title.property("width") / 2,
                title.property("height") / 2,
            ))
            QTest.mouseMove(window, title_center.toPoint())
            QTest.qWait(20)
            self.assertTrue(actions.property("revealed"))
            save = _visual_child(actions, "workspaceInlineSaveAction")
            open_action = _visual_child(actions, "workspaceInlineOpenAction")
            import_action = _visual_child(actions, "workspaceInlineImportAction")
            reference_action = _visual_child(
                actions, "workspaceInlineReferenceAction"
            )
            for child in (save, open_action):
                self.assertIsNotNone(child)
                self.assertEqual(child.property("width"), 24 if compact else 28)
            self.assertIsNone(import_action)
            self.assertIsNone(reference_action)
            self.assertEqual(save.property("toolTip"), "Save snapshot")
            self.assertEqual(open_action.property("toolTip"), "Open snapshot")

            open_center = open_action.mapToScene(QPointF(
                open_action.property("width") / 2,
                open_action.property("height") / 2,
            ))
            QTest.mouseClick(window, Qt.LeftButton, pos=open_center.toPoint())
            self.assertEqual(controller.item_actions[-1], ("open", node_id))
            QTest.qWait(
                QGuiApplication.styleHints().mouseDoubleClickInterval() + 20
            )

            title_text = title.property("text")
            controller.set_maya_dcc_selected(True)
            QTest.qWait(20)
            self.assertEqual(title.property("text"), title_text)
            save = _visual_child(actions, "workspaceInlineSaveAction")
            open_action = _visual_child(actions, "workspaceInlineOpenAction")
            import_action = _visual_child(actions, "workspaceInlineImportAction")
            reference_action = _visual_child(
                actions, "workspaceInlineReferenceAction"
            )
            for child in (
                save, open_action, import_action, reference_action,
            ):
                self.assertIsNotNone(child)
                self.assertTrue(child.property("visible"))
            self.assertEqual(save.property("toolTip"), "Save scene")
            self.assertEqual(open_action.property("toolTip"), "Open scene")
            self.assertEqual(open_action.property("iconName"), "folder_open")
            title_content_right = title.mapToItem(
                item, QPointF(title.property("width"), 0)
            ).x() - title.property("rightPadding")
            save_left = save.mapToItem(item, QPointF(0, 0)).x()
            self.assertAlmostEqual(
                save_left - title_content_right,
                6 if compact else 8,
                delta=1,
            )

            save_center = save.mapToScene(QPointF(
                save.property("width") / 2,
                save.property("height") / 2,
            ))
            QTest.mouseMove(window, save_center.toPoint())
            QTest.qWait(20)
            self.assertTrue(actions.property("revealed"))
            QTest.mouseClick(window, Qt.LeftButton, pos=save_center.toPoint())

            open_center = open_action.mapToScene(QPointF(
                open_action.property("width") / 2,
                open_action.property("height") / 2,
            ))
            QTest.mouseMove(window, open_center.toPoint())
            QTest.qWait(20)
            QTest.mouseClick(window, Qt.LeftButton, pos=open_center.toPoint())

            import_center = import_action.mapToScene(QPointF(
                import_action.property("width") / 2,
                import_action.property("height") / 2,
            ))
            QTest.mouseMove(window, import_center.toPoint())
            QTest.mouseClick(window, Qt.LeftButton, pos=import_center.toPoint())

            reference_center = reference_action.mapToScene(QPointF(
                reference_action.property("width") / 2,
                reference_action.property("height") / 2,
            ))
            QTest.mouseMove(window, reference_center.toPoint())
            QTest.mouseClick(
                window, Qt.LeftButton, pos=reference_center.toPoint()
            )
            self.assertEqual(controller.item_actions[-4:], [
                ("dcc_save_scene", node_id),
                ("dcc_open", node_id),
                ("dcc_import", node_id),
                ("dcc_reference", node_id),
            ])

            window.close()
            item.deleteLater()

        controller.set_maya_dcc_selected(True)
        item = component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="sobject:without-snapshot",
                nodeType="sobject",
                title="Sh2",
                compactMode=False,
                depth=0,
                width=900,
            )
        )
        self.assertIsNotNone(
            item,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(920, 140)
        item.setParentItem(window.contentItem())
        window.show()
        self.assertTrue(QTest.qWaitForWindowExposed(window))
        title = item.findChild(QObject, "workspaceObjectTitle")
        title_center = title.mapToScene(QPointF(
            title.property("width") / 2,
            title.property("height") / 2,
        ))
        QTest.mouseMove(window, title_center.toPoint())
        QTest.qWait(20)

        actions = item.findChild(
            QObject, "workspaceObjectInlineSnapshotActions"
        )
        self.assertTrue(
            _visual_child(actions, "workspaceInlineSaveAction").property(
                "visible"
            )
        )
        for object_name in (
            "workspaceInlineOpenAction",
            "workspaceInlineImportAction",
            "workspaceInlineReferenceAction",
        ):
            self.assertIsNone(_visual_child(actions, object_name))

        window.close()
        item.deleteLater()
        theme.deleteLater()
        engine.deleteLater()

    def test_selected_sobject_uses_content_selection_foreground(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({
            "dark": True,
            "accentColor": QColor("#b4bec6"),
            "baseColor": QColor("#303336"),
        })
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml"))
        )
        item = component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="sobject:contrast",
                nodeType="sobject",
                searchKey="demo/asset?project=demo&code=CONTRAST",
                title="Bathroom",
                subtitle="Selected description",
                compactMode=False,
                depth=0,
                selected=True,
                externalMenuVisible=True,
                itemControls=[{
                    "command": "repo_sync",
                    "icon": "repository-sync",
                    "tip": "Repository Sync",
                }],
                infoChips=[{"text": "locations"}],
                width=900,
            )
        )
        self.assertIsNotNone(
            item,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(920, 140)
        item.setParentItem(window.contentItem())
        window.show()
        QTest.qWait(30)

        foreground = theme.property("contentSelectionText")
        self.assertNotEqual(foreground, theme.property("selectedText"))
        title = item.findChild(QObject, "workspaceObjectTitle")
        actions = item.findChild(QObject, "workspaceItemActions")
        self.assertIsNotNone(actions)
        self.assertTrue(actions.property("active"))
        action_row = actions.property("item")
        self.assertIsNotNone(action_row)

        def visual_descendants(parent):
            pending = list(parent.childItems())
            descendants = []
            while pending:
                child = pending.pop()
                descendants.append(child)
                pending.extend(child.childItems())
            return descendants

        visual_items = visual_descendants(action_row)
        action = next((
            child for child in visual_items
            if child.metaObject().indexOfProperty("iconColor") >= 0
            and child.property("iconName") == "repository-sync"
        ), None)
        info_strip = item.findChild(QObject, "infoValueStrip")
        self.assertIsNotNone(info_strip)
        info_items = visual_descendants(info_strip)
        info_value = next((
            child for child in info_items
            if child.objectName() == "infoValueText"
        ), None)
        self.assertIsNotNone(title, "selected title was not instantiated")
        self.assertIsNotNone(action, "selected action was not instantiated")
        self.assertIsNotNone(
            info_value, "selected information value was not instantiated"
        )
        self.assertEqual(title.property("color"), foreground)
        self.assertEqual(action.property("iconColor"), foreground)
        self.assertEqual(info_value.property("color"), foreground)

        window.close()
        window.deleteLater()
        item.deleteLater()
        theme.deleteLater()

    def test_compact_sobject_keeps_card_hierarchy_with_tighter_geometry(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml"))
        )
        item = component.createWithInitialProperties(
            self.item_properties(
                theme,
                nodeId="sobject:asset:compact",
                nodeType="sobject",
                searchKey="demo/asset?project=demo&code=COMPACT",
                title="Compact asset",
                subtitle="Compact description",
                compactMode=True,
                depth=0,
                tasks=2,
                comments=1,
                itemControls=[{
                    "command": "watch_folder",
                    "icon": "visibility",
                    "persistent": True,
                    "success": True,
                }],
                progressItems=[{
                    "name": "progress",
                    "label": "1 / 3",
                    "color": "#607d8b",
                }],
                infoChips=[{"text": "12 min"}],
                width=420,
            )
        )
        self.assertIsNotNone(
            item,
            "\n".join(error.toString() for error in component.errors()),
        )
        self.app.processEvents()

        surface = item.findChild(QObject, "workspaceItemSurface")
        shadow = item.findChild(QObject, "itemSurfaceShadow")
        disclosure = item.findChild(QObject, "workspaceDisclosureArea")
        preview = item.findChild(QObject, "workspaceItemPreview")
        body = item.findChild(QObject, "workspaceObjectBody")
        title = item.findChild(QObject, "workspaceObjectTitle")
        metadata = item.findChild(QObject, "workspaceObjectMetadata")
        actions = item.findChild(QObject, "workspaceItemActions")
        communication = item.findChild(
            QObject, "workspaceCommunicationControls"
        )

        for child in (
            surface, shadow, disclosure, preview, body, title, metadata,
            actions, communication,
        ):
            self.assertIsNotNone(child)
        self.assertEqual(item.property("height"), 64)
        self.assertEqual(surface.property("railWidth"), 3)
        self.assertTrue(surface.property("elevated"))
        self.assertTrue(shadow.property("visible"))
        self.assertEqual(disclosure.property("width"), 30)
        self.assertEqual(preview.property("width"), 42)
        self.assertTrue(actions.property("active"))
        self.assertLess(
            surface.property("railX"), disclosure.property("x")
        )
        title_right = title.mapToItem(
            item, QPointF(title.property("width"), 0)
        ).x()
        actions_left = actions.mapToItem(item, QPointF(0, 0)).x()
        self.assertLessEqual(title_right, actions_left)
        self.assertLess(
            metadata.mapToItem(item, QPointF(0, 0)).y()
                + metadata.property("height"),
            item.property("height"),
        )

        item.deleteLater()
        theme.deleteLater()

    def test_result_views_keep_the_workspace_model_while_hidden(self):
        source = (
            ROOT / "thlib" / "ui" / "qml" / "SearchResultSurface.qml"
        ).read_text(encoding="utf-8")
        results = source[source.index("id: results"):source.index(
            "id: tileViewport"
        )]
        tiles = source[source.index("id: resultTiles"):source.index(
            "id: initialTilePresentation"
        )]
        for view in (results, tiles):
            self.assertIn("model: root.resultModel", view)
            self.assertNotIn(
                "model: visible ? root.resultModel : null", view
            )
            self.assertIn("cacheBuffer: 280", view)
            self.assertIn("reuseItems: true", view)

    def test_process_delegate_reacts_to_completed_checkin_refresh(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty(
            "appController", controller
        )
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "SearchResultSurface.qml")),
        )
        process = WorkspaceNode(
            node_id="asset:process:render",
            node_type="process",
            search_key="demo/asset?code=ASSET001",
            code="render",
            title="Render",
            depth=1,
            parent_id="asset",
            process="render",
            loaded=True,
        )
        root = WorkspaceNode(
            node_id="asset",
            node_type="sobject",
            search_key="demo/asset?code=ASSET001",
            code="ASSET001",
            title="Asset",
            expanded=True,
            has_children=True,
            loaded=True,
            children=[process],
        )
        model = WorkspaceItemModel()
        model.replace_nodes([root])
        surface = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "resultModel": model,
            "current": True,
            "viewMode": "continious",
            "splitterRatio": 0.58,
        })
        self.assertIsNotNone(
            surface,
            "\n".join(error.toString() for error in component.errors()),
        )
        surface.setWidth(420)
        surface.setHeight(260)

        def find_node(item, node_id):
            pending = [item]
            while pending:
                candidate = pending.pop()
                if (
                        candidate.property("nodeId") == node_id
                        and candidate.property("depth") is not None):
                    return candidate
                if isinstance(candidate, QQuickItem):
                    pending.extend(candidate.childItems())
            return None

        window = QQuickWindow()
        window.resize(420, 260)
        surface.setParentItem(window.contentItem())
        window.show()
        try:
            QTest.qWait(60)
            delegate = find_node(surface, process.node_id)
            self.assertIsNotNone(delegate)
            self.assertFalse(delegate.property("hasChildren"))
            self.assertFalse(delegate.property("expanded"))

            snapshot = WorkspaceNode(
                node_id="asset:process:render:snapshot:SNAPSHOT001",
                node_type="snapshot",
                search_key="sthpw/snapshot?code=SNAPSHOT001",
                code="SNAPSHOT001",
                title="render_v001.ma",
                depth=2,
                parent_id=process.node_id,
                process="render",
                context="render",
                loaded=True,
            )
            model.apply_snapshot_branch_refresh({"roots": [{
                "rootId": root.node_id,
                "processBranches": [{
                    "nodeId": process.node_id,
                    "processObject": object(),
                    "snapshots": [snapshot],
                }],
                "revealNodeId": snapshot.node_id,
            }]})
            QTest.qWait(100)

            refreshed_delegate = find_node(surface, process.node_id)
            self.assertIs(refreshed_delegate, delegate)
            self.assertTrue(delegate.property("hasChildren"))
            self.assertTrue(delegate.property("expanded"))
            self.assertEqual(delegate.property("childCount"), 1)
            disclosure = delegate.findChild(
                QObject, "workspaceDisclosureArea"
            )
            self.assertIsNotNone(disclosure)
            self.assertTrue(disclosure.property("hasChildren"))
            self.assertTrue(disclosure.property("expanded"))
        finally:
            window.close()
            surface.setParentItem(None)
            surface.deleteLater()
            window.deleteLater()
            theme.deleteLater()

    def test_loaded_search_tabs_retain_their_delegate_instances(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty(
            "appController", controller
        )
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "SearchResultSurface.qml")),
        )
        first_model = WorkspaceItemModel()
        second_model = WorkspaceItemModel()
        first_model.replace_nodes([WorkspaceNode(
            node_id="first",
            node_type="sobject",
            search_key="demo/asset?code=FIRST",
            code="FIRST",
            title="First",
        )])
        second_model.replace_nodes([WorkspaceNode(
            node_id="second",
            node_type="sobject",
            search_key="demo/asset?code=SECOND",
            code="SECOND",
            title="Second",
        )])
        model_updates = []
        first_model.dataChanged.connect(
            lambda *_args: model_updates.append("first")
        )
        second_model.dataChanged.connect(
            lambda *_args: model_updates.append("second")
        )

        def create_surface(model, current):
            surface = component.createWithInitialProperties({
                "theme": theme,
                "controller": controller,
                "resultModel": model,
                "current": current,
                "viewMode": "continious",
                "splitterRatio": 0.58,
            })
            self.assertIsNotNone(
                surface,
                "\n".join(
                    error.toString() for error in component.errors()
                ),
            )
            surface.setWidth(420)
            surface.setHeight(260)
            return surface

        def delegate_for(surface, node_id):
            pending = [surface]
            while pending:
                candidate = pending.pop()
                if candidate.property("nodeId") == node_id:
                    return candidate
                if isinstance(candidate, QQuickItem):
                    pending.extend(candidate.childItems())
            return None

        def item_named(surface, object_name):
            pending = [surface]
            while pending:
                candidate = pending.pop()
                if candidate.objectName() == object_name:
                    return candidate
                if isinstance(candidate, QQuickItem):
                    pending.extend(candidate.childItems())
            return None

        window = QQuickWindow()
        window.resize(420, 260)
        first_surface = create_surface(first_model, True)
        second_surface = create_surface(second_model, False)
        first_surface.setParentItem(window.contentItem())
        second_surface.setParentItem(window.contentItem())
        window.show()
        try:
            QTest.qWait(60)
            first_delegate = delegate_for(first_surface, "first")
            self.assertIsNotNone(first_delegate)
            results_view = item_named(
                first_surface, "searchResultsListView"
            )
            tiles_view = item_named(
                first_surface, "searchResultsGridView"
            )
            self.assertIsNotNone(results_view)
            self.assertIsNotNone(tiles_view)
            self.assertTrue(results_view.property("clip"))
            self.assertTrue(tiles_view.property("clip"))

            first_surface.setProperty("current", False)
            second_surface.setProperty("current", True)
            QTest.qWait(60)
            second_delegate = delegate_for(second_surface, "second")
            self.assertIsNotNone(second_delegate)

            second_surface.setProperty("current", False)
            first_surface.setProperty("current", True)
            QTest.qWait(30)
            self.assertIs(
                delegate_for(first_surface, "first"), first_delegate
            )
            self.assertIs(
                delegate_for(second_surface, "second"), second_delegate
            )
            self.assertEqual(model_updates, [])
        finally:
            window.close()
            first_surface.deleteLater()
            second_surface.deleteLater()
            window.deleteLater()
            theme.deleteLater()

    def test_tab_model_roles_create_a_retained_result_surface(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        engine.rootContext().setContextProperty(
            "appController", controller
        )
        result_model = WorkspaceItemModel()
        result_model.replace_nodes([WorkspaceNode(
            node_id="asset",
            node_type="sobject",
            search_key="demo/asset?code=ASSET",
            code="ASSET",
            title="Asset",
        )])
        second_result_model = WorkspaceItemModel()
        second_result_model.replace_nodes([WorkspaceNode(
            node_id="shot",
            node_type="sobject",
            search_key="demo/shot?code=SHOT",
            code="SHOT",
            title="Shot",
        )])
        surfaces_model = RecordListModel((
            "surfaceKey", "current",
            "resultModel", "viewMode", "splitterRatio",
        ), [{
            "surfaceKey": "section::tab",
            "current": True,
            "resultModel": result_model,
            "viewMode": "continious",
            "splitterRatio": 0.58,
        }, {
            "surfaceKey": "section::second-tab",
            "current": False,
            "resultModel": second_result_model,
            "viewMode": "continious",
            "splitterRatio": 0.58,
        }])
        engine.rootContext().setContextProperty(
            "workspaceResultSurfacesModel", surfaces_model
        )
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(engine)
        component.setData(f'''import QtQuick
import "."
Item {{
    id: host
    width: 420
    height: 260
    required property var uiTheme
    Repeater {{
        model: workspaceResultSurfacesModel
        delegate: SearchResultSurface {{
            objectName: "cachedSearchTabSurface"
            anchors.fill: parent
            theme: host.uiTheme
            controller: appController
            presentationActive: current
        }}
    }}
}}
'''.encode("utf-8"), QUrl.fromLocalFile(
            str(qml_dir / "RetainedSearchTabsTest.qml")
        ))
        host = component.createWithInitialProperties({"uiTheme": theme})
        try:
            self.assertIsNotNone(
                host,
                "\n".join(
                    error.toString() for error in component.errors()
                ),
            )
            self.app.processEvents()
            pending = [host]
            surfaces = []
            while pending:
                candidate = pending.pop()
                if candidate.objectName() == "cachedSearchTabSurface":
                    surfaces.append(candidate)
                if isinstance(candidate, QQuickItem):
                    pending.extend(candidate.childItems())
            self.assertEqual(len(surfaces), 2)
            first_surface = next(
                surface for surface in surfaces
                if surface.property("resultModel") is result_model
            )
            second_surface = next(
                surface for surface in surfaces
                if surface.property("resultModel") is second_result_model
            )
            self.assertTrue(first_surface.property("current"))
            self.assertFalse(second_surface.property("current"))

            surfaces_model.update_record(0, {"current": False})
            surfaces_model.update_record(1, {"current": True})
            QTest.qWait(30)

            self.assertFalse(first_surface.property("current"))
            self.assertTrue(second_surface.property("current"))
            self.assertIs(first_surface.property("resultModel"), result_model)
            self.assertIs(
                second_surface.property("resultModel"), second_result_model
            )
        finally:
            if host is not None:
                host.deleteLater()
            theme.deleteLater()

    def test_hidden_result_surfaces_suspend_preview_and_layout_work(self):
        source = (
            ROOT / "thlib" / "ui" / "qml" / "SearchResultSurface.qml"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "presentationActive: root.presentationActive && results.visible",
            source,
        )
        self.assertIn(
            "presentationActive: root.presentationActive && resultTiles.visible",
            source,
        )
        self.assertIn(
            "enabled: root.presentationActive && results.visible",
            source,
        )
        self.assertIn(
            "enabled: root.presentationActive && resultTiles.visible",
            source,
        )
        row_source = (
            ROOT / "thlib" / "ui" / "qml" / "WorkspaceResultItem.qml"
        ).read_text(encoding="utf-8")
        card_source = (
            ROOT / "thlib" / "ui" / "qml" / "WorkspaceCard.qml"
        ).read_text(encoding="utf-8")
        self.assertIn("active: !root.viewPooled", row_source)
        self.assertEqual(card_source.count("active: !root.viewPooled"), 3)

    def test_tab_switch_does_not_invalidate_global_animation_bindings(self):
        source = (
            ROOT / "thlib" / "ui" / "qml" / "Main.qml"
        ).read_text(encoding="utf-8")

        self.assertNotIn(
            "appController.search_tab_switch_monitor.switching",
            source,
        )

    def test_neighbor_item_menus_share_the_compact_anchored_style(self):
        source = (
            ROOT / "thlib" / "ui" / "qml" / "SearchResultsPane.qml"
        ).read_text(encoding="utf-8")
        action_menu = source[source.index("id: resultsActionMenu"):]
        action_menu = action_menu[:action_menu.index("id: itemActionMenu")]
        self.assertNotIn("processPickerStyle: true", action_menu)
        item_menu = source[source.index("id: itemActionMenu"):]
        item_menu = item_menu[:item_menu.index("id: processCountMenu")]
        self.assertIn("preferredWidth: 212", item_menu)
        self.assertIn("processPickerStyle: true", item_menu)
        self.assertIn("alignBelowRight: true", item_menu)
        self.assertIn("anchorPointerVisible: true", item_menu)
        self.assertEqual(source.count("itemActionMenu.openBelow(anchorItem)"), 1)
        self.assertNotIn(
            "resultsActionMenu.visible\n"
            "                && resultsActionMenuNodeId === nodeId",
            source,
        )

    def test_result_delegates_release_pooled_preview_textures(self):
        card = (
            ROOT / "thlib" / "ui" / "qml" / "WorkspaceCard.qml"
        ).read_text(encoding="utf-8")
        self.assertIn("GridView.onPooled", card)
        self.assertIn("root.viewPooled = true", card)
        self.assertGreaterEqual(
            card.count("active: !root.viewPooled"),
            3,
        )
        self.assertIn("ListView.onPooled", self.source)
        self.assertIn("root.viewPooled = true", self.source)
        self.assertIn(
            "active: !root.viewPooled",
            self.source,
        )

    def test_drag_attached_state_is_not_bound_to_its_ancestor_handler(self):
        self.assertIn("Drag.active: root.itemDragActive", self.source)
        self.assertIn("root.itemDragActive = active", self.source)
        self.assertNotIn("Drag.active: itemDragHandler.active", self.source)

    def test_sobject_drag_does_not_report_an_active_binding_loop(self):
        if QGuiApplication.platformName().lower() == "windows":
            self.skipTest("Windows OLE drag loop cannot be closed by QTest")
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        messages = []
        previous_handler = qInstallMessageHandler(
            lambda _kind, _context, message: messages.append(message)
        )
        window = None
        item = None
        theme = None
        try:
            engine = QQmlEngine()
            controller = _WorkspaceAppController()
            engine.rootContext().setContextProperty(
                "appController", controller
            )
            theme_component = QQmlComponent(
                engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
            )
            theme = theme_component.createWithInitialProperties({"dark": True})
            component = QQmlComponent(
                engine,
                QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml")),
            )
            item = component.createWithInitialProperties(
                self.item_properties(
                    theme,
                    nodeId="sobject:asset:1",
                    nodeType="sobject",
                    searchKey="demo/asset?project=demo&code=ASSET001",
                    title="Asset 1",
                    compactMode=False,
                    depth=0,
                )
            )
            self.assertIsNotNone(
                item,
                "\n".join(error.toString() for error in component.errors()),
            )
            window = QQuickWindow()
            window.resize(420, 160)
            item.setParentItem(window.contentItem())
            window.show()
            QTest.qWait(30)

            start = QPoint(160, 38)
            QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, start)
            QTest.mouseMove(window, QPoint(164, 40), delay=8)
            release_point = QPoint(245, 76)
            QTest.mouseMove(window, release_point, delay=8)
            QTest.mouseRelease(
                window, Qt.LeftButton, Qt.NoModifier, release_point
            )
            QTest.qWait(40)
        finally:
            qInstallMessageHandler(previous_handler)
            if window is not None:
                window.close()
                window.deleteLater()
            if item is not None:
                item.deleteLater()
            if theme is not None:
                theme.deleteLater()

        binding_loops = [
            message for message in messages
            if "Binding loop detected for property \"active\"" in message
            and "WorkspaceResultItem" in message
        ]
        self.assertEqual(binding_loops, [])


    def test_visible_quick_actions_refresh_between_non_maya_dcc_clients(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _WorkspaceAppController()
        controller.set_dcc_application("nuke")
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "WorkspaceResultItem.qml"))
        )
        item = component.createWithInitialProperties(self.item_properties(
            theme,
            nodeId="snapshot:dcc-switch",
            nodeType="snapshot",
            title="scene.nk",
            compactMode=False,
            depth=0,
            fileExists=True,
            width=900,
        ))
        self.assertIsNotNone(
            item, "\n".join(error.toString() for error in component.errors())
        )
        window = QQuickWindow()
        window.resize(920, 140)
        item.setParentItem(window.contentItem())
        window.show()
        self.assertTrue(QTest.qWaitForWindowExposed(window))
        title = item.findChild(QObject, "workspaceSnapshotTitle")
        QTest.mouseMove(window, QPoint(1, 1))
        QTest.qWait(10)
        center = title.mapToScene(QPointF(
            title.property("width") / 2, title.property("height") / 2
        ))
        QTest.mouseMove(window, center.toPoint())
        QTest.qWait(20)
        actions = item.findChild(
            QObject, "workspaceSnapshotInlineSnapshotActions"
        )
        self.assertTrue(actions.property("revealed"))
        save = _visual_child(actions, "workspaceInlineSaveAction")
        self.assertEqual(save.property("toolTip"), "Save Nuke scene")

        controller.set_dcc_application("blender")
        QTest.qWait(20)
        save = _visual_child(actions, "workspaceInlineSaveAction")
        self.assertEqual(save.property("toolTip"), "Save Blender scene")

        window.close()
        item.deleteLater()
        theme.deleteLater()
        engine.deleteLater()


class ItemPreviewLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def test_inactive_preview_unloads_the_internal_image_source(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        temporary = QTemporaryDir()
        image_path = Path(temporary.path()) / "preview.png"
        source_image = QImage(96, 96, QImage.Format.Format_RGBA8888)
        source_image.fill(0xff607d8b)
        self.assertTrue(source_image.save(str(image_path)))
        engine = QQmlEngine()
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "controls" / "ItemPreview.qml"))
        )
        preview = component.createWithInitialProperties({
            "theme": theme,
            "source": QUrl.fromLocalFile(str(image_path)),
            "width": 64,
            "height": 64,
        })
        self.assertIsNotNone(
            preview,
            "\n".join(error.toString() for error in component.errors()),
        )
        image = preview.findChild(QObject, "previewSourceImage")
        self.assertIsNotNone(image)
        self.assertTrue(image.property("retainWhileLoading"))
        self.assertFalse(image.property("source").isEmpty())
        for _attempt in range(20):
            if image.property("progress") >= 1.0:
                break
            QTest.qWait(10)
        self.assertEqual(image.property("progress"), 1.0)

        mask_loader = preview.findChild(QObject, "previewMaskLoader")
        self.assertIsNotNone(mask_loader)
        self.assertTrue(mask_loader.property("active"))
        preview.setProperty("effectsEnabled", False)
        self.app.processEvents()
        self.assertFalse(mask_loader.property("active"))
        self.assertFalse(image.property("source").isEmpty())
        self.assertTrue(image.property("visible"))

        preview.setProperty("active", False)
        self.app.processEvents()

        self.assertTrue(image.property("source").isEmpty())
        preview.deleteLater()
        theme.deleteLater()

    def test_preview_assigned_during_tab_swap_never_replays_appearance(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                qml_dir / "controls" / "ItemPreview.qml"
            )),
        )
        preview = component.createWithInitialProperties({
            "theme": theme,
            "width": 64,
            "height": 64,
        })
        self.assertIsNotNone(
            preview,
            "\n".join(error.toString() for error in component.errors()),
        )

        theme.setProperty("suppressTransientMotion", True)
        preview.setProperty("source", QUrl("file:///cached-preview.png"))
        self.app.processEvents()
        self.assertFalse(preview.property("appearanceAnimationEnabled"))

        theme.setProperty("suppressTransientMotion", False)
        self.app.processEvents()
        self.assertFalse(preview.property("appearanceAnimationEnabled"))

        preview.setProperty("source", QUrl("file:///new-preview.png"))
        self.app.processEvents()
        self.assertTrue(preview.property("appearanceAnimationEnabled"))

        preview.deleteLater()
        theme.deleteLater()

    def test_round_preview_stays_round_when_scroll_effects_are_disabled(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        temporary = QTemporaryDir()
        image_path = Path(temporary.path()) / "round-preview.png"
        source_image = QImage(96, 96, QImage.Format.Format_RGBA8888)
        source_image.fill(0xff2e9b62)
        self.assertTrue(source_image.save(str(image_path)))

        engine = QQmlEngine()
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "controls" / "ItemPreview.qml"))
        )
        preview = component.createWithInitialProperties({
            "theme": theme,
            "source": QUrl.fromLocalFile(str(image_path)),
            "width": 64,
            "height": 64,
            "round": True,
            "effectsEnabled": True,
            "animateAppearance": False,
        })
        self.assertIsNotNone(
            preview,
            "\n".join(error.toString() for error in component.errors()),
        )
        image = preview.findChild(QObject, "previewSourceImage")
        mask_loader = preview.findChild(QObject, "previewMaskLoader")
        self.assertIsNotNone(image)
        self.assertIsNotNone(mask_loader)
        for _attempt in range(20):
            if image.property("progress") >= 1.0:
                break
            QTest.qWait(10)
        self.assertTrue(mask_loader.property("active"))
        mask_item = mask_loader.property("item")
        self.assertIsNotNone(mask_item)
        preview.setProperty("effectsEnabled", False)
        self.app.processEvents()
        self.assertTrue(mask_loader.property("active"))
        self.assertEqual(mask_loader.property("item"), mask_item)
        self.assertFalse(image.property("visible"))

        window = QQuickWindow()
        window.setColor(QColor("#ff00ff"))
        window.resize(64, 64)
        preview.setParentItem(window.contentItem())
        window.show()
        QTest.qWait(30)
        rendered = window.grabWindow()
        self.assertFalse(rendered.isNull())
        corner = rendered.pixelColor(0, rendered.height() - 1)
        center = rendered.pixelColor(
            rendered.width() // 2, rendered.height() // 2
        )
        self.assertGreater(corner.red(), 200)
        self.assertGreater(corner.blue(), 200)
        self.assertGreater(center.green(), center.red())
        self.assertNotEqual(center.name(), corner.name())

        window.close()
        window.deleteLater()
        preview.deleteLater()
        theme.deleteLater()
