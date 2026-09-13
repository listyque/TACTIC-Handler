from __future__ import annotations

import os
from pathlib import Path
import unittest
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QPoint, Qt, QUrl, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QTest

from thlib.ui.editor_tools import ScreenshotController


QML = Path(__file__).resolve().parents[1] / "thlib" / "ui" / "qml"


class _WindowModel(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.close_calls = []

    @Slot(str)
    def close_window(self, window_id):
        self.close_calls.append(window_id)


class ScreenshotControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        self.debug_log = Mock()
        self.commit_queue = Mock()
        self.controller = ScreenshotController(
            self.debug_log, self.commit_queue
        )

    def tearDown(self):
        self.controller.shutdown()
        self.controller.deleteLater()

    def test_standalone_capture_without_queue_operation_is_rejected(self):
        self.controller.begin_capture()

        self.assertFalse(self.controller.selecting)
        self.assertEqual(
            self.controller.error,
            "Select a Commit Queue operation before capturing a preview",
        )
        self.commit_queue.add_preview_paths.assert_not_called()

    def test_capture_session_requires_and_clears_explicit_operation(self):
        self.controller.prepare_for_operation("operation-7")

        self.controller.begin_capture()

        self.assertTrue(self.controller.selecting)
        self.assertEqual(self.controller.targetOperationId, "operation-7")

        self.controller.cancel_capture()

        self.assertFalse(self.controller.selecting)
        self.assertEqual(self.controller.targetOperationId, "")

    def test_capture_restores_the_explicit_invoking_window(self):
        source = QQuickWindow()
        source.show()
        self.app.processEvents()
        self.addCleanup(source.close)
        self.controller.prepare_for_operation("operation-7")

        self.controller.begin_capture(source)

        self.assertIs(self.controller._active_window, source)
        self.assertFalse(source.isVisible())
        self.controller.cancel_capture()
        self.assertTrue(source.isVisible())

    def test_capture_waits_for_overlay_hidden_event_not_a_timer(self):
        self.controller.prepare_for_operation("operation-7")
        self.controller._capture = Mock()

        self.controller.capture(10, 20, 300, 200)

        self.controller._capture.assert_not_called()
        self.controller.finish_capture()
        self.controller._capture.assert_called_once_with(
            10, 20, 300, 200, "operation-7"
        )

    def test_click_creates_a_capture_area_and_escape_restores_windows(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        engine.rootContext().setContextProperty(
            "screenshotController", self.controller
        )
        window_model = _WindowModel(engine)
        engine.rootContext().setContextProperty("windowModel", window_model)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "ScreenshotMakerView.qml"))
        )
        source_window = QQuickWindow()
        source_window.setTitle("Commit Queue")
        source_window.show()
        host_window = QQuickWindow()
        host_window.setTransientParent(source_window)
        host_window.show()
        self.controller.prepare_for_operation("operation-7")
        view = component.createWithInitialProperties({"theme": theme})
        self.assertIsNotNone(
            view,
            "\n".join(error.toString() for error in component.errors()),
        )
        view.setParentItem(host_window.contentItem())
        try:
            QTest.qWait(40)
            capture_window = next(
                window
                for window in self.app.allWindows()
                if window.title() == "Screenshot Maker"
            )
            self.assertEqual(window_model.close_calls, [])
            self.assertFalse(host_window.isVisible())
            self.assertFalse(source_window.isVisible())
            QTest.mouseClick(
                capture_window,
                Qt.MouseButton.LeftButton,
                pos=QPoint(200, 200),
            )
            selection = capture_window.findChild(
                QObject, "screenshotSelection"
            )
            self.assertTrue(selection.property("ready"))
            self.assertEqual(selection.property("width"), 128.0)
            self.assertEqual(selection.property("height"), 128.0)
            self.assertTrue(
                capture_window.findChild(
                    QObject, "screenshotCaptureButton"
                ).property("visible")
            )

            QTest.keyClick(capture_window, Qt.Key.Key_Escape)
            QTest.qWait(20)
            self.assertFalse(self.controller.selecting)
            self.assertFalse(capture_window.isVisible())
            self.assertTrue(source_window.isVisible())
            self.assertEqual(
                window_model.close_calls, ["screenshot_maker"]
            )
        finally:
            self.controller.cancel_capture()
            host_window.close()
            source_window.close()
            view.deleteLater()
            theme.deleteLater()
            engine.deleteLater()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
