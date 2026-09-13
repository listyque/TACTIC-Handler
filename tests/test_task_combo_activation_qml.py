"""Pointer activation and avatar parity across lazy task-cell editors."""

import os
from pathlib import Path
import tempfile
import time
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import (
    QCoreApplication, QEvent, QMetaObject, QObject, QPoint, QPointF, Qt, QUrl,
)
from PySide6.QtGui import QColor, QImage
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from tests.qt_application import gui_test_application


class TaskComboActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        from thlib.environment import env_mode
        self.directory = tempfile.TemporaryDirectory()
        self.previous_path = env_mode.current_path
        env_mode.current_path = self.directory.name
        self.engine = QQmlEngine()
        self.warnings = []
        self.engine.warnings.connect(lambda errors: self.warnings.extend(
            error.toString() for error in errors))
        self.qml_dir = Path(__file__).resolve().parents[1] / "thlib/ui/qml"
        self.engine.addImportPath(str(self.qml_dir))
        self.window = None

    def tearDown(self):
        from thlib.environment import env_mode
        if self.window is not None:
            self.window.close()
            self.window.deleteLater()
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        env_mode.current_path = self.previous_path
        self.directory.cleanup()
        self.assertEqual(self.warnings, [])

    def create_cell(self, *, hover=False, user=False, animations=True):
        self.component = QQmlComponent(self.engine)
        source = '''
import QtQuick
import "controls" as Controls
Item {
    id: root
    width: 320; height: 160
    property bool hoverEnabled: false
    Theme {
        id: probeTheme
        objectName: "probeTheme"
        dark: true
        popupAnimationsEnabled: false
    }
    HoverHandler { id: cellHover }
    TaskEditorReleaseCoordinator { id: coordinator; theme: probeTheme }
    TaskTableEditorCell {
        id: cell
        x: 20; y: 20; width: 240; height: 32
        theme: probeTheme
        releaseCoordinator: coordinator
        editorActive: root.hoverEnabled && cellHover.hovered
        displayText: "Ready"
        editorComponent: Component {
            EDITOR {
                objectName: "taskComboProbe"
                theme: probeTheme
                actionField: true
                model: [
                    {label: "Ready", value: "ready"},
                    {label: "Done", value: "done"}
                ]
                textRole: "label"; valueRole: "value"
                currentIndex: 0
                USER_MODEL
            }
        }
    }
}
'''.replace("EDITOR", "UserComboBox" if user else "Controls.ComboBox").replace(
            "USER_MODEL", "userModel: null" if user else "")
        self.component.setData(source.encode(), QUrl.fromLocalFile(
            str(self.qml_dir / "TaskComboActivationProbe.qml")))
        self.view = self.component.createWithInitialProperties({"hoverEnabled": hover})
        self.assertIsNotNone(self.view, [error.toString() for error in self.component.errors()])
        self.theme = self.view.findChild(QObject, "probeTheme")
        self.theme.setProperty("fadeAnimationsEnabled", animations)
        self.show_view()
        self.cell = self.view.findChild(QObject, "taskTableEditorCell")

    def show_view(self, width=400, height=300):
        self.window = QQuickWindow()
        self.window.resize(width, height)
        self.view.setParentItem(self.window.contentItem())
        self.view.setParent(self.window)
        self.window.show()
        self.assertTrue(QTest.qWaitForWindowExposed(self.window))

    def assert_open(self):
        self.wait_for(lambda: self.cell.property("editorPopupOpen"))
        # Wait out the release debounce: a briefly flashed popup is not success.
        QTest.qWait(self.theme.property("baseMotionSlow") * 2)
        self.assertTrue(self.cell.property("editorPopupOpen"))
        self.assertTrue(self.cell.property("editorLoaded"))

    def wait_for(self, predicate):
        deadline = time.monotonic() + 1
        while not predicate() and time.monotonic() < deadline:
            QTest.qWait(10)
        self.assertTrue(predicate())

    def test_cold_status_cell_opens_on_single_click(self):
        self.create_cell()
        self.assertFalse(self.cell.property("editorLoaded"))
        QTest.mouseClick(self.window, Qt.LeftButton, Qt.NoModifier, QPoint(100, 36))
        self.assert_open()

    def test_hovered_status_cell_opens_on_single_click(self):
        self.create_cell(hover=True)
        QTest.mouseMove(self.window, QPoint(100, 36))
        self.wait_for(lambda: self.cell.property("editorLoaded"))
        QTest.mouseClick(self.window, Qt.LeftButton, Qt.NoModifier, QPoint(100, 36))
        self.assert_open()

    def test_cold_user_cell_opens_on_single_click(self):
        self.create_cell(user=True)
        QTest.mouseClick(self.window, Qt.LeftButton, Qt.NoModifier, QPoint(100, 36))
        self.assert_open()

    def test_hovered_user_cell_opens_without_animations_and_releases_after_escape(self):
        self.create_cell(hover=True, user=True, animations=False)
        QTest.mouseMove(self.window, QPoint(100, 36))
        self.wait_for(lambda: self.cell.property("editorLoaded"))
        QTest.mouseClick(self.window, Qt.LeftButton, Qt.NoModifier, QPoint(100, 36))
        self.assert_open()
        popup_window = next(window for window in self.app.allWindows()
                            if window.isVisible() and window != self.window)
        QTest.keyClick(popup_window, Qt.Key_Escape)
        QTest.mouseMove(self.window, QPoint(380, 280))
        self.wait_for(lambda: not self.cell.property("editorLoaded"))

    def test_cold_cell_accepts_one_touch_and_scrolling_unloads_editor(self):
        self.create_cell()
        device = QTest.createTouchDevice()
        touch = QTest.touchEvent(self.window, device, autoCommit=False)
        touch.press(0, QPoint(100, 36), self.window).commit()
        touch.release(0, QPoint(100, 36), self.window).commit()
        self.assert_open()
        self.cell.setProperty("scrolling", True)
        self.wait_for(lambda: not self.cell.property("editorLoaded"))
        self.cell.setProperty("scrolling", False)
        self.assertFalse(self.cell.property("editorLoaded"))

    def create_task_table(self):
        from tests.test_tasks_controller import FakeApplication
        from thlib.ui.tasks import TasksController
        from thlib.ui.workspace_models.records import RecordListModel

        self.application = FakeApplication()
        self.application.workspace_state._task_sobjects[0].get_info()["supervisor"] = "artist"
        self.controller = TasksController(self.application)
        self.controller.open_workspace()
        self.users = RecordListModel((
            "login", "displayName", "initials", "avatarUrl", "avatarColor"))
        for name, value in {
            "tasksController": self.controller,
            "advancedTaskModel": self.controller.advanced_model,
            "advancedTaskTableModel": self.controller.table_model,
            "userListModel": self.users,
        }.items():
            self.engine.rootContext().setContextProperty(name, value)
        self.theme_component = QQmlComponent(
            self.engine, QUrl.fromLocalFile(str(self.qml_dir / "Theme.qml")))
        self.theme = self.theme_component.createWithInitialProperties({
            "dark": True, "popupAnimationsEnabled": False,
            "fadeAnimationsEnabled": False})
        self.assertIsNotNone(self.theme, self.theme_component.errors())
        self.component = QQmlComponent(
            self.engine, QUrl.fromLocalFile(str(self.qml_dir / "TaskBrowserTable.qml")))
        self.view = self.component.createWithInitialProperties({"theme": self.theme})
        self.assertIsNotNone(self.view, self.component.errors())
        self.theme.setParent(self.view)
        self.view.setWidth(1400)
        self.view.setHeight(640)
        self.show_view(1400, 640)
        task_list = self.view.findChild(QObject, "taskBrowserList")
        QMetaObject.invokeMethod(task_list, "forceLayout")

    def visual_items(self):
        items = [self.view]
        for item in items:
            items.extend(item.childItems())
        return items

    def test_task_table_single_click_uses_real_status_editor_and_model(self):
        self.create_task_table()
        for width in (1400, 600):
            with self.subTest(width=width):
                self.view.setWidth(width)
                self.window.resize(width, 640)
                self.app.processEvents()
                self.cell = next(item for item in self.visual_items() if
                                 item.objectName() == "taskTableEditorCell"
                                 and item.property("showAccent"))
                center = self.cell.mapToScene(QPointF(
                    self.cell.width() / 2, self.cell.height() / 2)).toPoint()
                QTest.mouseMove(self.window, center)
                self.wait_for(lambda: self.cell.property("editorLoaded"))
                QTest.mouseClick(self.window, Qt.LeftButton, Qt.NoModifier, center)
                self.assert_open()
                popup_window = next(window for window in self.app.allWindows()
                                    if window.isVisible() and window != self.window)
                previous_status = self.controller.table_model.get(0)["status"]
                QTest.keyClick(popup_window, Qt.Key_Down)
                QTest.keyClick(popup_window, Qt.Key_Return)
                self.wait_for(lambda: not self.cell.property("editorPopupOpen"))
                self.assertNotEqual(
                    self.controller.table_model.get(0)["status"], previous_status)
                QTest.mouseMove(self.window, QPoint(width - 20, 600))
                self.wait_for(lambda: not self.cell.property("editorLoaded"))

    def test_task_avatars_resolve_live_profiles_before_hover(self):
        self.create_task_table()
        self.controller.set_task_column_visible("supervisor", True)
        self.app.processEvents()
        QTest.mouseMove(self.window, QPoint(1380, 600))
        cells = [item for item in self.visual_items()
                 if item.objectName() == "taskTableEditorCell"
                 and item.property("showAvatar") and item.isVisible()]
        self.assertEqual(len(cells), 2)  # Assignee and supervisor.
        # Populate the catalog after delegates already exist, as on startup.
        picture = QImage(24, 24, QImage.Format_RGB32)
        picture.fill(QColor("#5378b1"))
        picture_path = Path(self.directory.name) / "avatar.png"
        self.assertTrue(picture.save(str(picture_path)))
        avatar_url = QUrl.fromLocalFile(str(picture_path)).toString()
        self.users.replace([{
            "login": "artist", "displayName": "Artist",
            "initials": "AR", "avatarUrl": avatar_url, "avatarColor": "#804bba",
        }])
        self.app.processEvents()
        for cell in cells:
            with self.subTest(column=cell.property("displayText")):
                self.wait_for(lambda: not cell.property("editorLoaded"))
                avatar = next(item for item in cell.findChildren(QObject)
                              if item.metaObject().indexOfProperty("previewSize") >= 0)
                self.assertEqual(avatar.property("source").toString(), avatar_url)
                self.assertEqual(avatar.property("accent"), QColor("#804bba"))
                preview_image = avatar.findChild(QObject, "previewSourceImage")
                self.wait_for(lambda: preview_image.property("progress") == 1.0)
                before = [avatar.property(name) for name in
                          ("source", "accent", "fallbackText")]
                center = cell.mapToScene(QPointF(
                    cell.width() / 2, cell.height() / 2)).toPoint()
                QTest.mouseMove(self.window, center)
                self.wait_for(lambda: cell.property("editorLoaded"))
                current_avatar = cell.findChild(QObject, "userComboBoxCurrentAvatar")
                self.assertEqual(before, [current_avatar.property(name) for name in
                                          ("source", "accent", "fallbackText")])
                QTest.mouseMove(self.window, QPoint(1380, 600))
                self.wait_for(lambda: not cell.property("editorLoaded"))


if __name__ == "__main__":
    unittest.main()
