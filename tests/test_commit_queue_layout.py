"""Actual queue layout, persisted resize and special-file policy through Qt input."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import QObject, Slot, QPoint, QPointF, Qt, QUrl, QEvent
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from tests.qt_application import gui_test_application
from tests.profile_ui_responsiveness import frame
from tests.test_commit_queue import payload
from tests.test_frame_queue import Screenshot, visual
from tests.frame_files_fixture import Locale
from thlib.environment import env_mode, env_write_config
from thlib.ui.commit_queue import CommitQueueController
from thlib.ui.icon_font import qml_icon_bindings
from thlib.ui.localization import CatalogTranslator

ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib/ui/qml"


class Windows(QObject):
    def __init__(self):
        super().__init__()
        self.help_calls = []

    @Slot(str)
    def open_help(self, topic):
        self.help_calls.append(topic)


class CommitQueueLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        directory = self.enterContext(tempfile.TemporaryDirectory())
        self.enterContext(patch.object(env_mode, "current_path", directory))
        self.enterContext(patch("thlib.environment.env_tactic.get_all_base_dirs", return_value=[]))
        self.source = Path(directory) / "source.txt"
        self.source.write_bytes(b"queue layout")
        self.controller = CommitQueueController()
        self.engine = QQmlEngine()
        self.warnings = []
        self.engine.warnings.connect(lambda errors: self.warnings.extend(error.toString() for error in errors))
        self.windows, self.screenshot, self.locale = Windows(), Screenshot(), Locale("ru")
        self.translator = CatalogTranslator(QML.parent / "translations/ru.json")
        self.app.installTranslator(self.translator)
        self.addCleanup(self.app.removeTranslator, self.translator)
        context = self.engine.rootContext()
        for name, value in dict(qml_icon_bindings(ROOT, self.engine),
                commitQueueController=self.controller, commitQueueModel=self.controller.model,
                screenshotController=self.screenshot, windowModel=self.windows,
                localizationController=self.locale).items():
            context.setContextProperty(name, value)
        self.components = []
        self.theme = self.create("Theme.qml", {"dark": True, "clickAnimationsEnabled": False})
        self.view = self.create("CommitQueueView.qml", {"theme": self.theme})
        self.window = QQuickWindow()
        self.view.setParentItem(self.window.contentItem())
        self.window.show()
        self.resize(1280, 800)
        self.addCleanup(self.dispose)

    def create(self, name, properties):
        component = QQmlComponent(self.engine, QUrl.fromLocalFile(str(QML / name)))
        item = component.createWithInitialProperties(properties)
        self.assertIsNotNone(item, str(component.errors()))
        self.components.append(component)
        return item

    def dispose(self):
        self.controller.shutdown()
        self.window.close()
        for item in [self.view, self.window, self.controller, self.theme, *self.components, self.engine]:
            item.deleteLater()
        self.app.sendPostedEvents(None, QEvent.DeferredDelete)
        self.app.processEvents()
        self.assertFalse(self.warnings, self.warnings)

    def resize(self, width, height):
        self.window.resize(width, height)
        self.view.setWidth(width)
        self.view.setHeight(height)
        frame(self.window)

    def item(self, name):
        item = visual(self.window.contentItem(), name)
        self.assertIsNotNone(item, name)
        return item

    def click(self, name):
        item = self.item(name)
        QTest.mouseClick(self.window, Qt.LeftButton, pos=item.mapToScene(QPointF(item.width()/2, item.height()/2)).toPoint())
        frame(self.window)

    def inside(self, name, parent):
        item, pane = self.item(name), self.item(parent) if isinstance(parent, str) else parent
        position = item.mapToItem(pane, QPointF())
        self.assertGreaterEqual(position.x(), -0.1, name)
        self.assertGreaterEqual(position.y(), -0.1, name)
        self.assertLessEqual(position.x() + item.width(), pane.width() + 0.1, name)
        self.assertLessEqual(position.y() + item.height(), pane.height() + 0.1, name)

    def test_splitter_drag_persists_and_actions_fit_when_panels_shrink(self):
        ids = self.controller.add_prepared_many([(payload(self.source, str(i)), str(i)) for i in range(3)])
        self.controller._set_record(ids[0], status="Completed")
        self.controller._set_record(ids[2], status="Failed", error="test failure")
        self.controller.select_row(1)
        for width in (1280, 760):
            self.resize(width, 800)
            for ratio in (0.15, 0.85):
                self.controller.set_splitter_ratio(ratio)
                frame(self.window)
                for name in ("commitQueueHelpButton", "commitQueueAutoCleanSwitch", "commitQueueTool_up", "commitQueueTool_down", "commitQueueTool_clear", "commitQueueTool_completed", "commitQueueServerSwitch"):
                    self.inside(name, "commitQueueFilesDock")
                for name in ("commitQueuePrimarySendButton", "commitQueueSendOverflowButton", "commitQueueApplyToChecked"):
                    self.inside(name, "commitQueueDetailsPanel")
        self.controller.set_splitter_ratio(0.36)
        self.resize(1280, 800)
        handle = self.item("commitQueueMainSplitter")
        start = handle.mapToScene(QPointF(handle.width()/2, handle.height()/2)).toPoint()
        before = self.item("commitQueueFilesDock").width()
        with patch("thlib.ui.commit_queue.env_write_config", wraps=env_write_config) as writes:
            QTest.mousePress(self.window, Qt.LeftButton, pos=start)
            QTest.mouseMove(self.window, start + QPoint(120, 0), delay=20)
            frame(self.window)
            self.assertGreater(self.item("commitQueueFilesDock").width(), before + 60)
            self.assertEqual(writes.call_count, 0)
            QTest.mouseRelease(self.window, Qt.LeftButton, pos=start + QPoint(120, 0))
            frame(self.window)
            self.assertEqual(writes.call_count, 1)
        ratio = self.controller.splitterRatio
        before_cancel = self.item("commitQueueFilesDock").width()
        handle = self.item("commitQueueMainSplitter")
        start = handle.mapToScene(QPointF(handle.width()/2, handle.height()/2)).toPoint()
        with patch("thlib.ui.commit_queue.env_write_config", wraps=env_write_config) as writes:
            QTest.mousePress(self.window, Qt.LeftButton, pos=start)
            QTest.mouseMove(self.window, start - QPoint(30, 0), delay=20)
            frame(self.window)
            self.assertEqual(self.controller.splitterRatio, ratio)
            self.window.hide()
            self.app.processEvents()
            self.window.show()
            frame(self.window)
            self.assertAlmostEqual(self.item("commitQueueFilesDock").width(), before_cancel)
            self.assertEqual(writes.call_count, 0)
            QTest.mouseRelease(self.window, Qt.LeftButton, pos=start)
            self.item("commitQueueMainSplitter").forceActiveFocus()
            QTest.keyClick(self.window, Qt.Key_Right)
            frame(self.window)
            self.assertEqual(writes.call_count, 1)
        ratio = self.controller.splitterRatio
        self.controller.shutdown()
        restored = CommitQueueController()
        try:
            self.assertAlmostEqual(restored.splitterRatio, ratio)
        finally:
            restored.shutdown()
            restored.deleteLater()

    def test_special_checkins_disable_versionless_controls_and_regular_file_keeps_them(self):
        self.controller.set_advanced_options_expanded(True)
        self.resize(1280, 1400)
        special = [dict(checkinType=kind) for kind in ("multi_file", "dir", "sequence")]
        special.append(dict(checkinType="file", groupCheckin=True))
        for index, options in enumerate(special + [dict(checkinType="file")]):
            identity = self.controller.add_prepared(dict(payload(self.source), **options, context=str(index)), "Asset")
            self.controller.select_row(index)
            frame(self.window)
            for field in ("updateVersionless", "onlyVersionless"):
                name = "commitQueueOption_" + field
                control = self.item(name)
                allowed = index == len(special)
                self.assertEqual(control.isEnabled(), allowed)
                before = bool(self.controller.operation(identity).get(field))
                self.click(name)
                after = bool(self.controller.operation(identity).get(field))
                self.assertEqual(after, not before if allowed else False)

    def test_narrow_split_panels_keep_their_content_inside_bounds(self):
        self.resize(760, 640)
        self.assertIsNotNone(self.item("commitQueueWelcomeIcon"))
        self.click("commitQueueHelpButton")
        self.assertEqual(self.windows.help_calls, ["commit_queue"])
        self.controller.add_prepared(payload(self.source), "Asset publish")
        for width in (760, 640, 390):
            self.resize(width, 700)
            self.view.setProperty("detailsVisible", False)
            frame(self.window)
            self.inside("commitQueueAutoCleanSwitch", "commitQueueFilesDock")
            self.inside("commitQueueTool_clear", "commitQueueFilesDock")
            self.click("commitQueueTool_clear")
            dialog = self.view.findChild(QObject, "commitQueueClearConfirmation")
            self.assertTrue(dialog.property("opened"))
            self.inside("confirmationAccept", dialog.property("contentItem"))
            self.inside("confirmationReject", dialog.property("contentItem"))
            self.click("confirmationReject")
            self.assertEqual(self.controller.count, 1)
            self.view.setProperty("detailsVisible", width < 700)
            frame(self.window)
            self.inside("commitQueueActionFooter", "commitQueueDetailsPanel")


if __name__ == "__main__":
    unittest.main()
