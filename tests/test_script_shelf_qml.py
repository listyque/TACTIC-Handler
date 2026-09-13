import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QPointF, Property, Qt, QUrl, Signal, Slot
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QTest

from tests.profile_ui_responsiveness import frame
from tests import test_process_menu_latency as workspace
from thlib.ui.workspace_models.records import RecordListModel


class _Shelf(QObject):
    stateChanged = Signal()

    def __init__(self, button_count=1, maya_connected=False):
        super().__init__()
        self.buttons = RecordListModel((
            "buttonId", "title", "description", "iconName", "script",
            "available", "running",
        ))
        self.buttons.replace([{
            "buttonId": "save" if index == 0 else f"script_{index}",
            "title": "Save" if index == 0 else f"Script {index}",
            "description": "Save the current scene",
            "iconName": "content-save",
            "script": "tools/save",
            "available": True,
            "running": False,
        } for index in range(button_count)])
        self.started = []
        self.dcc_shelves_exported = []
        self._mode = "shared"
        self._maya_connected = maya_connected

    @Property(QObject, constant=True)
    def model(self):
        return self.buttons

    @Property(str, notify=stateChanged)
    def activeMode(self):
        return self._mode

    @Property("QVariantList", notify=stateChanged)
    def activeModeOptions(self):
        return [
            {"value": "personal", "label": "My shelf", "icon": "user"},
            {"value": "shared", "label": "Shared", "icon": "users"},
        ]

    @Property(bool, notify=stateChanged)
    def busy(self):
        return False

    @Property(bool, notify=stateChanged)
    def executionBusy(self):
        return False

    @Property(bool, notify=stateChanged)
    def canExportDccShelf(self):
        return self._maya_connected

    @Property(bool, notify=stateChanged)
    def dccShelfBusy(self):
        return False

    @Property(str, notify=stateChanged)
    def dccShelfName(self):
        return "TACTIC Assets"

    @Slot(str)
    def run(self, button_id):
        self.started.append(button_id)

    @Slot(str)
    def set_active_mode(self, mode):
        self._mode = mode
        self.stateChanged.emit()

    @Slot()
    def open_editor(self):
        pass

    @Slot(str)
    def export_dcc_shelf(self, name):
        self.dcc_shelves_exported.append(name)


class _TreeController(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filters = []

    @Slot(str)
    def set_tree_filter(self, value):
        self.filters.append(value)

    @Slot(str)
    def toggle_folder(self, _path):
        pass


class _ShelfEditor(QObject):
    stateChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._assignment_pending = False
        self._can_remove = False
        self._dirty = False
        self._editor_view = "script_shelf@global"
        self._editor_title = "Shared shelf"
        self._remove_target_title = "Shared shelf"
        self._shared_options = [{
            "value": "script_shelf@global",
            "label": "Shared shelf",
        }, {
            "value": "script_shelf@old",
            "label": "Assets shelf",
        }]
        self.saved_titles = []
        self.applied_views = []
        self.buttons = RecordListModel((
            "buttonId", "title", "description", "iconName", "script",
            "available", "running",
        ))
        self.buttons.replace([{
            "buttonId": "textures",
            "title": "Textures",
            "description": "Check textures",
            "iconName": "image",
            "script": "tools/textures",
            "available": True,
            "running": False,
        }])

    @Property(bool, notify=stateChanged)
    def canManage(self):
        return True

    @Property(bool, notify=stateChanged)
    def busy(self):
        return False

    @Property(str, notify=stateChanged)
    def editorMode(self):
        return "shared"

    @Property(str, notify=stateChanged)
    def personalScope(self):
        return "global"

    @Property(str, notify=stateChanged)
    def sharedScope(self):
        return (
            "global" if self._editor_view == "script_shelf@global"
            else "tab"
        )

    @Property(str, notify=stateChanged)
    def editorView(self):
        return self._editor_view

    @Property(str, notify=stateChanged)
    def editorTitle(self):
        return self._editor_title

    @Property(bool, notify=stateChanged)
    def canRename(self):
        return self._editor_view != "script_shelf@global"

    @Property(str, notify=stateChanged)
    def error(self):
        return ""

    @Property(bool, notify=stateChanged)
    def canRemove(self):
        return self._can_remove

    @Property(str, notify=stateChanged)
    def removeTargetTitle(self):
        return self._remove_target_title

    @Property(bool, notify=stateChanged)
    def editorDirty(self):
        return self._dirty

    @Property(bool, notify=stateChanged)
    def assignmentPending(self):
        return self._assignment_pending

    @Slot(str)
    def set_editor_title(self, title):
        self._editor_title = title
        self._dirty = True
        self.stateChanged.emit()

    @Slot()
    def create_shared(self):
        self._editor_view = "script_shelf@new"
        self._editor_title = "New shelf"
        self._dirty = True
        self.stateChanged.emit()

    @Slot()
    def discard(self):
        self._dirty = False
        self.stateChanged.emit()

    @Slot()
    def save(self):
        self.saved_titles.append(self._editor_title)
        self._dirty = False
        self._can_remove = True
        self._remove_target_title = self._editor_title
        self.stateChanged.emit()

    @Slot()
    def apply_to_current_tab(self):
        self.applied_views.append(self._editor_view)
        self._assignment_pending = False
        self.stateChanged.emit()

    @Property(QObject, constant=True)
    def editorModel(self):
        return self.buttons

    @Property("QVariantList", notify=stateChanged)
    def personalScopeOptions(self):
        return [
            {"value": "global", "label": "All tabs"},
            {"value": "tab", "label": "Only this tab: Assets"},
        ]

    @Property("QVariantList", notify=stateChanged)
    def sharedTabOptions(self):
        return self._shared_options[1:]

    @Property("QVariantList", notify=stateChanged)
    def sharedOptions(self):
        return self._shared_options

    @Property("QVariantList", notify=stateChanged)
    def scriptOptions(self):
        return [{"value": "tools/textures", "label": "Textures"}]


class ScriptShelfQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workspace.ProcessMenuLatencyTests.setUpClass()

    def setUp(self):
        self.fixture = workspace.ProcessMenuLatencyTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    @staticmethod
    def _item(view, name):
        return next(
            item for item in workspace.visual_items(view)
            if item.objectName() == name
        )

    @staticmethod
    def _click(window, item):
        center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
        QTest.mouseClick(window, Qt.LeftButton, pos=center.toPoint())
        frame(window)

    def test_toolbar_button_opens_shelf_and_runs_its_saved_script(self):
        shelf = _Shelf()
        with self.fixture.scene(width=720, shelf=shelf) as (window, view):
            toggle = self._item(view, "scriptShelfButton")
            self.assertEqual(toggle.property("iconName"), "code")
            self._click(window, toggle)

            loader = self._item(view, "scriptShelfLoader")
            self.assertEqual(loader.height(), 48)
            mode = self._item(view, "scriptShelfMode")
            self.assertLessEqual(mode.width(), 26)
            self.assertLessEqual(mode.height(), 46)
            personal = self._item(view, "scriptShelfMode_personal")
            shared = self._item(view, "scriptShelfMode_shared")
            self.assertAlmostEqual(personal.x(), shared.x())
            self.assertLess(personal.y(), shared.y())
            action = self._item(view, "scriptShelfAction_save")
            self.assertEqual(action.width(), 40)
            self.assertEqual(action.height(), 40)
            self.assertEqual(
                action.property("toolTip"), "Save the current scene"
            )
            icon = action.findChild(QObject, "scriptShelfActionIcon")
            label = action.findChild(QObject, "scriptShelfActionLabel")
            self.assertIsNotNone(icon)
            self.assertIsNotNone(label)
            self.assertEqual(label.property("text"), "Save")
            self.assertEqual(label.width(), action.width())
            self.assertGreater(label.property("contentWidth"), 0)
            self.assertEqual(icon.x(), round(icon.x()))
            self.assertEqual(icon.y(), round(icon.y()))
            self.assertGreaterEqual(
                label.y(), icon.y() + icon.height() + 4
            )
            self.assertFalse(icon.property("nativeRendering"))
            self._click(window, action)

        self.assertEqual(shelf.started, ["save"])

    def test_search_help_button_opens_search_article(self):
        with self.fixture.scene(width=720, shelf=_Shelf()) as (window, view):
            self._click(
                window, self._item(view, "searchWorkspaceHelpButton")
            )

        self.assertEqual(
            self.fixture.controller.window_model.helpTopic, "search"
        )

    def test_shelf_keeps_actions_visible_at_narrow_and_wide_sizes(self):
        for width in (480, 1400):
            with self.subTest(width=width):
                shelf = _Shelf()
                with self.fixture.scene(width=width, shelf=shelf) as (window, view):
                    self._click(window, self._item(view, "scriptShelfButton"))

                    self.assertGreater(
                        self._item(view, "scriptShelfButtons").width(), 0
                    )
                    self.assertGreater(
                        self._item(view, "scriptShelfAction_save").width(), 0
                    )

    def test_dcc_shelf_action_only_appears_for_a_capable_client(self):
        shelf = _Shelf(maya_connected=False)
        with self.fixture.scene(width=720, shelf=shelf) as (window, view):
            self._click(window, self._item(view, "scriptShelfButton"))
            action = self._item(view, "exportDccShelfButton")
            self.assertFalse(action.isVisible())

            shelf._maya_connected = True
            shelf.stateChanged.emit()
            frame(window)
            self.assertTrue(action.isVisible())
            self.assertEqual(action.property("iconName"), "upload")
            self._click(window, action)
            field = view.findChild(QObject, "dccShelfNameField")
            self.assertIsNotNone(field)
            self.assertEqual(field.property("text"), "TACTIC Assets")
            field.setProperty("text", "My Maya Tools")
            self._click(
                window,
                view.findChild(QObject, "confirmExportDccShelfButton"),
            )

        self.assertEqual(shelf.dcc_shelves_exported, ["My Maya Tools"])

    def test_overflowing_shelf_exposes_horizontal_scrollbar(self):
        shelf = _Shelf(button_count=12)
        with self.fixture.scene(width=480, shelf=shelf) as (window, view):
            self._click(window, self._item(view, "scriptShelfButton"))
            buttons = self._item(view, "scriptShelfButtons")
            scroll_bar = self._item(view, "scriptShelfScrollBar")

            self.assertGreater(
                buttons.property("contentWidth"), buttons.width()
            )
            self.assertTrue(scroll_bar.isVisible())

    def test_shelf_mode_switch_selects_personal_or_shared_buttons(self):
        shelf = _Shelf()
        with self.fixture.scene(width=720, shelf=shelf) as (window, view):
            self._click(window, self._item(view, "scriptShelfButton"))
            self._click(
                window,
                self._item(view, "scriptShelfMode_personal"),
            )

        self.assertEqual(shelf.activeMode, "personal")


    def test_script_picker_selects_from_the_script_editor_tree(self):
        tree = RecordListModel((
            "token", "nodeType", "path", "folder", "title", "language",
            "depth", "expanded", "hasChildren",
        ))
        tree.replace([{
            "token": "folder:tools", "nodeType": "folder",
            "path": "tools", "folder": "", "title": "tools",
            "language": "", "depth": 0, "expanded": True,
            "hasChildren": True,
        }, {
            "token": "script:save", "nodeType": "script",
            "path": "tools", "folder": "tools", "title": "save",
            "language": "local_python", "depth": 1, "expanded": False,
            "hasChildren": False,
        }])
        engine = QQmlEngine()
        tree_controller = _TreeController(engine)
        for name, value in {
            **workspace.ProcessMenuLatencyTests.icon_bindings,
            "appController": self.fixture.controller,
            "pickerTreeModel": tree,
            "pickerTreeController": tree_controller,
        }.items():
            engine.rootContext().setContextProperty(name, value)
        component = QQmlComponent(engine)
        component.setData(b'''
import QtQuick
import QtQuick.Controls
import "." as App
ApplicationWindow {
    width: 520; height: 600; visible: true
    property string picked: ""
    App.Theme {
        id: theme; dark: true; popupAnimationsEnabled: false
    }
    Button { id: opener; width: 300; height: 40 }
    App.ScriptTreePicker {
        id: picker
        parent: Overlay.overlay
        usePopupWindow: false
        theme: theme
        treeModel: pickerTreeModel
        treeController: pickerTreeController
        scriptOptions: [{value: "tools/save"}]
        onScriptSelected: script => picked = script
    }
    Component.onCompleted: picker.openFor(opener, "")
}
''', QUrl.fromLocalFile(str(workspace.QML / "_ShelfTreeTest.qml")))
        window = component.create()
        self.assertIsNotNone(
            window, [error.toString() for error in component.errors()]
        )
        try:
            frame(window)
            search = self._item(
                window.contentItem(), "shelfScriptTreeSearch"
            )
            search.forceActiveFocus()
            for character in "save":
                QTest.keyClick(window, character)
            frame(window)
            self.assertEqual(tree_controller.filters[-1], "save")

            row = self._item(
                window.contentItem(), "shelfScriptTreeRow_script_save"
            )
            self._click(window, row)
            self.assertEqual(window.property("picked"), "tools/save")
            self.assertEqual(tree_controller.filters[-1], "")
        finally:
            window.close()
            window.deleteLater()
            engine.deleteLater()

    def test_editor_uses_compact_preset_and_button_panes(self):
        engine = QQmlEngine()
        shelf = _ShelfEditor(engine)
        tree = RecordListModel((
            "token", "nodeType", "path", "folder", "title", "language",
            "depth", "expanded", "hasChildren",
        ))
        tree_controller = _TreeController(engine)
        for name, value in {
            **workspace.ProcessMenuLatencyTests.icon_bindings,
            "appController": self.fixture.controller,
            "editorShelf": shelf,
            "scriptEditorModel": tree,
            "scriptEditorController": tree_controller,
            "windowModel": self.fixture.controller.window_model,
        }.items():
            engine.rootContext().setContextProperty(name, value)
        component = QQmlComponent(engine)
        component.setData(b'''
import QtQuick
import QtQuick.Controls
import "." as App
ApplicationWindow {
    width: 1080; height: 700; visible: true
    App.Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    App.ScriptShelfEditorView {
        anchors.fill: parent
        theme: theme
        controller: editorShelf
    }
}
''', QUrl.fromLocalFile(str(workspace.QML / "_ShelfEditorTest.qml")))
        window = component.create()
        self.assertIsNotNone(
            window, [error.toString() for error in component.errors()]
        )
        try:
            frame(window)
            self._click(
                window,
                self._item(window.contentItem(), "scriptShelfHelpButton"),
            )
            self.assertEqual(
                self.fixture.controller.window_model.helpTopic,
                "script_shelf",
            )
            preset_pane = self._item(
                window.contentItem(), "scriptShelfPresetPane"
            )
            editor_pane = self._item(
                window.contentItem(), "scriptShelfEditorPane"
            )
            self.assertLess(preset_pane.x(), editor_pane.x())
            self.assertLess(preset_pane.width(), editor_pane.width() / 2)
            self.assertIsNone(
                window.findChild(QObject, "scriptShelfSelector")
            )
            preset_list = self._item(
                window.contentItem(), "scriptShelfPresetList"
            )
            self.assertEqual(preset_list.property("count"), 1)
            global_shelf = self._item(
                window.contentItem(), "scriptShelfGlobalPreset"
            )
            self.assertTrue(global_shelf.property("highlighted"))
            global_divider = self._item(
                window.contentItem(), "scriptShelfGlobalDivider"
            )
            self.assertLessEqual(
                global_shelf.mapToScene(QPointF(0, 0)).y()
                + global_shelf.height(),
                global_divider.mapToScene(QPointF(0, 0)).y(),
            )
            self.assertLess(
                global_divider.mapToScene(QPointF(0, 0)).y(),
                preset_list.mapToScene(QPointF(0, 0)).y(),
            )

            title = self._item(window.contentItem(), "scriptShelfTitle")
            fixed_title = self._item(
                window.contentItem(), "scriptShelfFixedTitle"
            )
            self.assertFalse(title.isVisible())
            self.assertTrue(fixed_title.isVisible())
            self.assertEqual(fixed_title.property("text"), "Shared shelf")
            self.assertFalse(self._item(
                window.contentItem(), "applyScriptShelfButton"
            ).isVisible())
            editor_list = self._item(
                window.contentItem(), "scriptShelfEditorList"
            )
            button_row = self._item(
                window.contentItem(), "scriptShelfButtonRow_0"
            )
            self.assertEqual(button_row.height(), 88)

            owner_mode = self._item(
                window.contentItem(), "scriptShelfOwnerMode"
            )
            self.assertGreaterEqual(
                owner_mode.mapToScene(QPointF(0, 0)).y(),
                preset_pane.mapToScene(QPointF(0, 0)).y(),
            )

            create = self._item(
                window.contentItem(), "newScriptShelfButton"
            )
            self.assertEqual(create.property("toolTip"), "New shelf")
            self.assertTrue(create.isEnabled())
            self._click(window, create)
            self.assertFalse(create.isEnabled())
            self.assertFalse(self._item(
                window.contentItem(), "scriptShelfOwnerMode"
            ).isEnabled())
            self.assertFalse(self._item(
                window.contentItem(),
                "scriptShelfGlobalPreset",
            ).isEnabled())
            self.assertTrue(title.isVisible())
            self.assertFalse(fixed_title.isVisible())

            title.forceActiveFocus()
            QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
            for character in "New shelf for Assets":
                QTest.keyClick(window, character)
            frame(window)
            self.assertEqual(shelf._editor_title, "New shelf for Assets")
            apply_shelf = self._item(
                window.contentItem(), "applyScriptShelfButton"
            )
            self.assertTrue(apply_shelf.isVisible())
            self.assertFalse(apply_shelf.isEnabled())
            save = self._item(
                window.contentItem(), "saveScriptShelfButton"
            )
            self.assertTrue(save.isEnabled())
            add = self._item(
                window.contentItem(), "addScriptShelfButton"
            )
            self.assertLess(
                add.mapToScene(QPointF(0, 0)).y(),
                editor_list.mapToScene(QPointF(0, 0)).y(),
            )
            self.assertGreaterEqual(
                add.mapToScene(QPointF(0, 0)).y(),
                title.mapToScene(QPointF(0, 0)).y() + title.height(),
            )
            self._click(window, save)
            self.assertEqual(shelf.saved_titles, ["New shelf for Assets"])
            shelf._assignment_pending = True
            shelf.stateChanged.emit()
            frame(window)
            self.assertTrue(apply_shelf.isEnabled())
            self.assertEqual(apply_shelf.property("text"), "Apply to this tab")
            self._click(window, apply_shelf)
            self.assertEqual(shelf.applied_views, ["script_shelf@new"])
            self.assertFalse(apply_shelf.isEnabled())
            self.assertEqual(apply_shelf.property("text"), "Used on this tab")

            window.resize(720, 480)
            frame(window)
            self.assertGreater(editor_pane.width(), preset_pane.width())
            self.assertGreater(editor_list.height(), button_row.height())
            self.assertLessEqual(
                button_row.x() + button_row.width(),
                editor_list.x() + editor_list.width(),
            )

            shelf._remove_target_title = "Original shelf for Assets"
            shelf.stateChanged.emit()
            frame(window)
            self.assertLessEqual(
                editor_pane.x() + editor_pane.width(), window.width()
            )

            delete = self._item(
                window.contentItem(), "deleteScriptShelfButton"
            )
            self.assertGreater(
                delete.mapToScene(QPointF(0, 0)).y(),
                editor_list.mapToScene(QPointF(0, 0)).y(),
            )
            self.assertEqual(
                delete.property("text"),
                "Delete “Original shelf for Assets”",
            )
            self._click(window, delete)
            dialog = window.findChild(QObject, "removeScriptShelfDialog")
            message = self._item(
                window.contentItem(), "removeScriptShelfMessage"
            )
            self.assertIsNotNone(dialog)
            self.assertTrue(dialog.property("visible"))
            self.assertEqual(
                dialog.property("title"),
                "Delete “Original shelf for Assets”?",
            )
            self.assertIn(
                "Original shelf for Assets", message.property("text")
            )
        finally:
            window.close()
            window.deleteLater()
            engine.deleteLater()


if __name__ == "__main__":
    unittest.main()
