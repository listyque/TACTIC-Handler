"""Real native input for B08 production presenters."""

import unittest
from pathlib import Path
from PySide6.QtCore import (
    QObject,
    Property,
    Signal,
    Slot,
    QUrl,
    Qt,
    QCoreApplication,
    QEvent,
)
from PySide6.QtGui import QInputMethodEvent
from PySide6.QtQml import QQmlEngine, QQmlComponent, QQmlExpression
from PySide6.QtQuick import QQuickWindow, QQuickItem
from PySide6.QtTest import QTest
from tests.qt_application import gui_test_application
from tests.profile_ui_responsiveness import frame
from tests.test_sidebar_editor_qml import SidebarEditorQmlTests
from thlib.ui.icon_font import qml_icon_bindings

ROOT = Path(__file__).resolve().parents[1]


class _Watch(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.values = {"path": "assets/robot", "repositories": []}
        self.calls = []

    @Property("QVariantMap", notify=changed)
    def editor(self):
        return dict(self.values)

    @Property("QVariantList", constant=True)
    def repositories(self):
        return [
            {"value": "main", "label": "Main repository"},
            {"value": "backup", "label": "Backup repository"},
        ]

    @Property(bool, constant=True)
    def busy(self):
        return False

    @Property(str, constant=True)
    def message(self):
        return ""

    @Property(bool, notify=changed)
    def canSaveEditor(self):
        return bool(self.values["repositories"])

    @Slot(str, "QVariant")
    def set_editor_value(self, key, value):
        self.values[key] = value
        self.calls.append(("value", key, value))
        self.changed.emit()

    @Slot(str, bool)
    def toggle_editor_repository(self, value, selected):
        values = list(self.values["repositories"])
        if selected and value not in values:
            values.append(value)
        elif not selected and value in values:
            values.remove(value)
        self.values["repositories"] = values
        self.calls.append(("repository", value, selected))
        self.changed.emit()

    @Slot()
    def save_edit(self):
        self.calls.append(("save",))

    @Slot()
    def cancel_edit(self):
        self.calls.append(("cancel",))


class FrameObjectsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        self.engine = QQmlEngine()
        self.warnings = []
        self.engine.warnings.connect(
            lambda errors: self.warnings.extend(error.toString() for error in errors)
        )
        for name, value in qml_icon_bindings(ROOT, self.app).items():
            self.engine.rootContext().setContextProperty(name, value)
        self.watch = _Watch()
        self.engine.rootContext().setContextProperty(
            "watchFoldersController", self.watch
        )
        self.themeComponent = QQmlComponent(
            self.engine, QUrl.fromLocalFile(str(ROOT / "thlib/ui/qml/Theme.qml"))
        )
        self.theme = self.themeComponent.createWithInitialProperties(
            {
                "dark": True,
                "clickAnimationsEnabled": False,
                "hoverAnimationsEnabled": False,
                "popupAnimationsEnabled": False,
                "fadeAnimationsEnabled": False,
            }
        )
        self.assertIsNotNone(self.theme)
        self.window = QQuickWindow()
        self.window.resize(520, 420)
        self.root = None

    def tearDown(self):
        self.window.close()
        if self.root:
            self.root.setParentItem(None)
            self.root.deleteLater()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.assertEqual(self.warnings, [])
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def load(self, name, **props):
        self.component = QQmlComponent(
            self.engine, QUrl.fromLocalFile(str(ROOT / "thlib/ui/qml" / name))
        )
        self.root = self.component.createWithInitialProperties(
            dict(theme=self.theme, width=520, height=420, **props)
        )
        self.assertIsNotNone(self.root, [e.toString() for e in self.component.errors()])
        self.root.setParentItem(self.window.contentItem())
        self.window.show()
        frame(self.window)

    def item(self, name):
        return next(
            item
            for item in SidebarEditorQmlTests.descendants(self.window.contentItem())
            if item.objectName() == name and item.isVisible()
        )

    def click(self, name):
        from PySide6.QtCore import QPointF

        item = self.item(name)
        point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
        QTest.mouseClick(self.window, Qt.LeftButton, pos=point.toPoint())
        frame(self.window)

    def expression(self, item, text):
        value = QQmlExpression(QQmlEngine.contextForObject(item), item, text)
        result, undefined = value.evaluate()
        self.assertFalse(value.hasError(), value.error().toString())
        self.assertFalse(undefined)
        return result

    def test_dependency_rows_keep_variable_heights_scroll_and_virtualization(self):
        rows = [
            dict(
                searchKey=f"sthpw/note?code=N{i}",
                title=f"Note {i}",
                details="admin · model" if i % 2 else "",
                position=i,
                groupIndex=0,
                iconName="notes",
            )
            for i in range(100)
        ]
        self.load("features/objects/ObjectDependencyList.qml", rows=rows)
        self.root.setHeight(200)
        frame(self.window)
        self.assertEqual(self.expression(self.root, "itemAtIndex(0).height"), 44)
        self.assertEqual(self.expression(self.root, "itemAtIndex(1).height"), 52)
        self.assertGreater(self.root.property("contentHeight"), 4000)
        self.root.setProperty("contentY", 500)
        frame(self.window)
        self.root.setProperty("rows", [dict(row) for row in rows])
        frame(self.window)
        frame(self.window)
        self.assertAlmostEqual(self.root.property("contentY"), 500)
        painted = [
            item
            for item in SidebarEditorQmlTests.descendants(self.root)
            if item.objectName().startswith("dependency_")
        ]
        self.assertLess(len(painted), 200)

    def test_description_ime_save_and_retained_value(self):
        self.load("DescriptionEditor.qml", value="Original", editing=True, dirty=True)
        values = []
        saves = []
        self.root.valueEdited.connect(
            lambda value: (values.append(value), self.root.setProperty("value", value))
        )
        self.root.saveRequested.connect(
            lambda: saves.append(self.root.property("value"))
        )
        self.click("descriptionTextInput")
        QTest.keyClick(self.window, Qt.Key_A, Qt.ControlModifier)
        event = QInputMethodEvent()
        event.setCommitString("Черновик")
        QCoreApplication.sendEvent(self.item("descriptionTextInput"), event)
        frame(self.window)
        self.assertEqual(values[-1], "Черновик")
        self.assertEqual(
            self.item("descriptionTextInput").property("font").pixelSize(), 11
        )
        self.click("description_save")
        self.assertEqual(saves, ["Черновик"])
        self.root.setProperty("value", "Another object")
        frame(self.window)
        self.assertEqual(
            self.item("descriptionTextInput").property("text"), "Another object"
        )

    def test_description_state_aligns_right(self):
        self.load("DescriptionEditor.qml", value="Pinned", pinned=True)
        self.assertTrue(
            self.expression(
                self.item("descriptionState"),
                "Number(horizontalAlignment) === Number(Qt.AlignRight)",
            )
        )

    def test_unmanaged_description_finishes_on_focus_loss(self):
        self.load(
            "DescriptionEditor.qml",
            value="Queue description",
            managed=False,
            compact=True,
        )
        finished = []
        self.root.editingFinished.connect(finished.append)
        self.click("descriptionTextInput")
        QTest.keyClick(self.window, Qt.Key_End)
        QTest.keyClick(self.window, Qt.Key_X)
        self.assertEqual(
            self.item("descriptionTextInput").property("text"), "Queue descriptionx"
        )
        other = QQuickItem(self.window.contentItem())
        other.forceActiveFocus()
        frame(self.window)
        self.assertFalse(self.item("descriptionTextInput").hasActiveFocus())
        self.assertTrue(finished)
        self.assertEqual(finished[-1], "Queue descriptionx")

    def test_watch_folder_add_remove_and_save_use_existing_commands(self):
        self.load("WatchFolderEditorView.qml")
        self.click("watchRepositoryAdd")
        self.assertEqual(self.watch.values["repositories"], ["main"])
        self.click("watchEditorSave")
        self.assertIn(("save",), self.watch.calls)
        self.click("watchRepositoryRemove")
        self.assertEqual(self.watch.values["repositories"], [])
        self.click("watchEditorCancel")
        self.assertEqual(self.watch.calls[-1], ("cancel",))

    def test_summary_preserves_middle_elision(self):
        self.load(
            "SnapshotSummary.qml",
            title="long_snapshot_geometry_name.ma",
            version="v001",
        )
        self.assertTrue(
            self.expression(
                self.item("snapshotSummaryTitle"),
                "Number(elide) === Number(Text.ElideMiddle)",
            )
        )

    def test_snapshot_tree_expands_and_passes_each_file_to_its_native_port(self):
        from thlib.ui.workspace_models.records import RecordListModel

        controller = _SnapshotController()
        group = {
            "value": "model",
            "label": "Model",
            "accent": "#78a6c4",
            "snapshotCount": 1,
            "fileCount": 2,
            "sizeText": "12 B",
            "snapshots": [
                {
                    "modelIndex": 7,
                    "searchKey": "sthpw/snapshot?code=S1",
                    "title": "Model snapshot",
                    "context": "model",
                    "version": "v001",
                    "author": "admin",
                    "repository": "base",
                    "fileCount": 2,
                    "sizeText": "12 B",
                    "timestampPretty": "today",
                }
            ],
            "files": [
                {
                    "token": token,
                    "title": title,
                    "extension": "txt",
                    "previewUrl": "",
                    "sizeText": "6 B",
                    "exists": True,
                }
                for token, title in [("a", "First.txt"), ("b", "Second.txt")]
            ],
        }
        from copy import deepcopy

        model = RecordListModel(tuple(group), [deepcopy(group)])
        self.load(
            "SObjectSnapshotTree.qml",
            metrics={"snapshots": 1, "files": 2},
            snapshotProcessModel=model,
            controller=controller,
        )
        self.window.resize(900, 1100)
        self.root.setWidth(900)
        self.root.setHeight(1100)
        frame(self.window)
        self.click("objectSnapshotProcess_0")
        self.click("objectReportSnapshot_0_0")
        self.assertEqual(controller.calls, [("snapshot", 7)])
        cards = [
            item
            for item in SidebarEditorQmlTests.descendants(self.window.contentItem())
            if item.property("title") in ("First.txt", "Second.txt")
        ]
        self.assertEqual(
            {item.property("title") for item in cards}, {"First.txt", "Second.txt"}
        )
        from PySide6.QtCore import QPointF

        card = next(item for item in cards if item.property("title") == "Second.txt")
        QTest.mouseClick(
            self.window,
            Qt.LeftButton,
            pos=card.mapToScene(QPointF(card.width() / 2, card.height() / 2)).toPoint(),
        )
        frame(self.window)
        self.assertEqual(controller.calls[-1], ("file", "b"))
        group["files"][1]["title"] = "Changed.txt"
        model.replace([group])
        frame(self.window)
        self.assertTrue(
            any(
                item.property("title") == "Changed.txt"
                for item in SidebarEditorQmlTests.descendants(self.window.contentItem())
            )
        )

    def test_delete_dependencies_toggle_expand_and_confirm_use_existing_commands(self):
        controller = _DeleteController()
        self.deleteController = controller
        self.engine.rootContext().setContextProperty(
            "sobjectDeleteController", controller
        )
        self.load("DeleteSObjectView.qml")
        self.window.resize(900, 750)
        self.root.setWidth(900)
        self.root.setHeight(750)
        frame(self.window)
        self.click("deleteDependencyExpand_0")
        self.assertEqual(controller.calls[-1], ("expand", 0))
        self.assertTrue(
            any(
                item.property("text") == "Review note"
                for item in SidebarEditorQmlTests.descendants(self.window.contentItem())
            )
        )
        self.click("deleteDependencyCheck_0")
        self.assertFalse(controller.data["groups"][0]["checked"])
        self.click("deleteSubmit")
        self.assertEqual(controller.calls[-1], ("delete",))
        controller.data.update(ready=False, error="Read failed")
        controller.changed.emit()
        frame(self.window)
        self.assertFalse(self.item("deleteSubmit").isEnabled())
        self.click("deleteRetry")
        self.assertEqual(controller.calls[-1], ("retry",))

    def test_inspector_status_progress_and_actions_route_through_existing_owner(self):
        self.load(
            "features/objects/ObjectInspectorQuick.qml",
            model={
                "hasTask": True,
                "canCreate": True,
                "canEdit": True,
                "dirty": True,
                "title": "Model task",
                "assignedLabel": "Admin",
                "status": "Ready",
                "statuses": [
                    {"value": "Ready", "label": "Ready", "color": "#789abc"},
                    {"value": "Done", "label": "Done", "color": "#88aa77"},
                ],
                "assigned": "admin",
                "users": [
                    {
                        "value": "admin",
                        "label": "Admin",
                        "displayName": "Admin",
                        "initials": "AD",
                    }
                ],
                "start": "2026-10-17 09:00:00",
                "end": "2026-10-18 18:00:00",
                "progress": 25,
                "progressEditable": True,
            },
        )
        self.recorder = _EventRecorder()
        events = self.recorder.calls
        self.engine.rootContext().setContextProperty("eventsRecorder", self.recorder)
        expression = QQmlExpression(
            QQmlEngine.contextForObject(self.root),
            self.root,
            "event.connect(function(action,source){eventsRecorder.record(action);})",
        )
        expression.evaluate()
        self.assertFalse(expression.hasError(), expression.error().toString())
        self.click("taskInspector_save")
        self.assertEqual(events[-1]["type"], "save")
        # The production status port remains the native combo box.
        port = self.item("taskInspectorStatusField")
        combo = self.expression(port, "item")
        self.assertEqual(combo.property("count"), 3)
        from PySide6.QtCore import QPointF

        self.window.requestActivate()
        frame(self.window)
        QTest.mouseClick(
            self.window,
            Qt.LeftButton,
            pos=combo.mapToScene(
                QPointF(combo.width() / 2, combo.height() / 2)
            ).toPoint(),
        )
        frame(self.window)
        popup = combo.findChild(QQuickItem, "comboBoxPopupList")
        self.assertIsNotNone(popup)
        QTest.keyClick(popup.window(), Qt.Key_Down)
        QTest.keyClick(popup.window(), Qt.Key_Return)
        frame(self.window)
        self.assertEqual(
            events[-1], {"type": "change", "field": "status", "value": "Done"}
        )
        slider = self.expression(self.item("taskInspectorProgress"), "item")
        QTest.mouseClick(
            self.window,
            Qt.LeftButton,
            pos=slider.mapToScene(
                QPointF(slider.width() * 0.8, slider.height() / 2)
            ).toPoint(),
        )
        frame(self.window)
        self.assertEqual(events[-1]["field"], "progress")
        self.assertGreater(events[-1]["value"], 25)
        self.assertEqual(events[-1]["value"] % 5, 0)
        self.click("taskInspector_discard")
        self.assertEqual(events[-1]["type"], "discard")

    def test_note_body_measures_rich_text_and_files_without_clipping(self):
        self.owner = _NoteOwner()
        self.load(
            "features/objects/NoteBody.qml",
            controller=self.owner,
            model={
                "entryType": "note",
                "body": "A long note\nSecond line",
                "displayHtml": "A long note<br>Second line",
                "skeyPreviews": [],
                "attachments": [
                    {
                        "title": "Review.txt",
                        "extension": "TXT",
                        "token": "file1",
                        "size": "24 B",
                        "local": False,
                    }
                ],
            },
        )
        for _ in range(6):
            frame(self.window)
        self.assertGreater(self.root.implicitHeight(), 80)
        self.assertEqual(
            self.item("noteBodyText").property("rawText"), "A long note\nSecond line"
        )
        self.root.setWidth(140)
        frame(self.window)
        body = self.item("noteBodyText")
        self.assertGreater(body.height(), 0)
        self.assertGreaterEqual(
            self.root.implicitHeight(), body.property("contentHeight") + 64 + 6
        )

    def test_note_editor_keeps_draft_on_error_and_delete_is_modal(self):
        self.owner = _NoteOwner()
        self.engine.rootContext().setContextProperty("noteOwner", self.owner)
        self.component = QQmlComponent(self.engine)
        self.component.setData(
            b'import QtQuick\nimport "features/objects" as Objects\nItem {id:fixtureRoot;required property var theme; Objects.NoteEditDialog{id:edit;objectName:"noteEditorDialog";theme:fixtureRoot.theme;controller:noteOwner;row:0;initialText:"Original note";width:400} Objects.NoteDeleteDialog{id:deletion;objectName:"noteDeleteDialog";theme:fixtureRoot.theme;controller:noteOwner;row:0;width:360}}',
            QUrl.fromLocalFile(str(ROOT / "thlib/ui/qml/B08NoteTest.qml")),
        )
        self.root = self.component.createWithInitialProperties(
            {"theme": self.theme, "width": 520, "height": 420}
        )
        self.assertIsNotNone(
            self.root, [error.toString() for error in self.component.errors()]
        )
        self.root.setParentItem(self.window.contentItem())
        self.window.show()
        frame(self.window)
        from PySide6.QtCore import QMetaObject

        editor = self.root.findChild(QObject, "noteEditorDialog")
        QMetaObject.invokeMethod(editor, "open")
        frame(self.window)
        self.assertFalse(editor.property("modal"))
        field = self.item("noteEditText")
        self.click("noteEditText")
        QTest.keyClick(self.window, Qt.Key_A, Qt.ControlModifier)
        ime = QInputMethodEvent()
        ime.setCommitString("Retained draft")
        QCoreApplication.sendEvent(self.window.activeFocusItem(), ime)
        frame(self.window)
        self.click("noteEditSave")
        self.assertEqual(self.owner.calls, [("edit", 0, "Retained draft")])
        self.owner.fail("Revision changed")
        frame(self.window)
        self.assertTrue(editor.property("opened"))
        self.assertEqual(self.item("noteEditText").property("text"), "Retained draft")
        self.owner.unknown = True
        self.owner.stateChanged.emit()
        frame(self.window)
        self.assertFalse(self.item("noteEditSave").isEnabled())
        self.click("noteEditCancel")
        frame(self.window)
        self.owner.unknown = False
        self.owner.message = ""
        self.owner.stateChanged.emit()
        deletion = self.root.findChild(QObject, "noteDeleteDialog")
        QMetaObject.invokeMethod(deletion, "open")
        frame(self.window)
        self.assertTrue(deletion.property("modal"))
        self.click("noteDeleteConfirm")
        self.assertEqual(self.owner.calls[-1], ("delete", 0))
        self.owner.fail("Delete rejected")
        frame(self.window)
        self.assertTrue(deletion.property("opened"))
        self.click("noteDeleteCancel")


class _NoteOwner(QObject):
    stateChanged = Signal()

    def __init__(self):
        super().__init__()
        self.pending = False
        self.message = ""
        self.unknown = False
        self.calls = []

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self.pending

    @Property(bool, notify=stateChanged)
    def uncertain(self):
        return self.unknown

    @Property(str, notify=stateChanged)
    def error(self):
        return self.message

    @Slot(int, str, str, result=bool)
    def edit(self, row, text, expected_key=""):
        self.calls.append(("edit", row, text))
        self.pending = True
        self.stateChanged.emit()
        return True

    @Slot(int, str)
    def remove(self, row, expected_key=""):
        self.calls.append(("delete", row))
        self.pending = True
        self.stateChanged.emit()

    def fail(self, message):
        self.pending = False
        self.message = message
        self.stateChanged.emit()


class _EventRecorder(QObject):
    def __init__(self):
        super().__init__()
        self.calls = []

    @Slot("QVariant")
    def record(self, value):
        self.calls.append(value.toVariant() if hasattr(value, "toVariant") else value)


class _SnapshotController(QObject):
    def __init__(self):
        super().__init__()
        self.calls = []

    @Slot(int)
    def open_snapshot(self, index):
        self.calls.append(("snapshot", index))

    @Slot(str)
    def activate_file(self, token):
        self.calls.append(("file", token))

    @Slot(str)
    def show_file_folder(self, token):
        self.calls.append(("folder", token))


class _DeleteController(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.calls = []
        self.data = {
            "targets": [{"title": "Robot", "searchKey": "demo/assets?code=A"}],
            "targetCount": 1,
            "ready": True,
            "groups": [
                {
                    "searchType": "sthpw/note",
                    "searchTypeTitle": "Notes",
                    "count": 1,
                    "checked": True,
                    "defaultChecked": True,
                    "expanded": False,
                    "iconName": "notes",
                    "items": [
                        {
                            "title": "Review note",
                            "details": "admin",
                            "searchKey": "sthpw/note?code=N",
                        }
                    ],
                }
            ],
        }

    @Property("QVariantMap", notify=changed)
    def presentation(self):
        return self.data

    @Slot(int, bool)
    def set_group_checked(self, index, value):
        self.data["groups"][index]["checked"] = value
        self.calls.append(("check", index, value))
        self.changed.emit()

    @Slot(int)
    def toggle_group(self, index):
        self.data["groups"][index]["expanded"] = not self.data["groups"][index][
            "expanded"
        ]
        self.calls.append(("expand", index))
        self.changed.emit()

    @Slot()
    def confirm_delete(self):
        self.calls.append(("delete",))

    @Slot()
    def retry(self):
        self.calls.append(("retry",))

    @Slot()
    def cancel(self):
        self.calls.append(("cancel",))


if __name__ == "__main__":
    unittest.main()
