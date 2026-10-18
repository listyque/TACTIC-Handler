"""Region gestures and capture handoff use native input; no desktop pixels are read."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_CONTROLS_STYLE', 'Basic')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
from PySide6.QtCore import QPoint, QPointF, Qt, QUrl, QEvent
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlEngine, QQmlComponent
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
import tests.test_screenshot_controller as CaptureFixtures
from tests.profile_ui_responsiveness import frame
from thlib.ui.editor_tools import ScreenshotController

QML = Path(__file__).resolve().parents[1] / 'thlib/ui/qml'

class FrameScreenshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_draw_move_resize_redraw_capture_handoff(self):
        engine = QQmlEngine()
        controller = ScreenshotController(Mock(), Mock())
        windows = CaptureFixtures._WindowModel()
        engine.rootContext().setContextProperty('screenshotController', controller)
        engine.rootContext().setContextProperty('windowModel', windows)
        warnings = []
        engine.warnings.connect(lambda errors: warnings.extend(str(error) for error in errors))
        theme_component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / 'Theme.qml')))
        theme = theme_component.createWithInitialProperties({'dark': True, 'popupAnimationsEnabled': False})
        source_window, host_window = QQuickWindow(), QQuickWindow()
        source_window.show()
        host_window.setTransientParent(source_window)
        host_window.show()
        controller.prepare_for_operation('operation-7')
        component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / 'ScreenshotMakerView.qml')))
        view = component.createWithInitialProperties({'theme': theme})
        self.assertIsNotNone(view, '\n'.join(str(error) for error in component.errors()))
        view.setParentItem(host_window.contentItem())
        try:
            self.app.processEvents()
            capture_window = next(window for window in self.app.allWindows() if window.title() == 'Screenshot Maker')
            frame(capture_window)
            def drag(start, end):
                QTest.mousePress(capture_window, Qt.LeftButton, pos=start)
                QTest.mouseMove(capture_window, (start + end) / 2)
                QTest.mouseMove(capture_window, end)
                QTest.mouseRelease(capture_window, Qt.LeftButton, pos=end)
                frame(capture_window)
            def click(name):
                item = CaptureFixtures._visual(capture_window.contentItem(), name)
                self.assertIsNotNone(item, name)
                point = item.mapToScene(QPointF(item.width()/2, item.height()/2))
                self.assertGreaterEqual(point.x(), 0)
                self.assertLessEqual(point.x(), capture_window.width())
                self.assertGreaterEqual(point.y(), 0)
                self.assertLessEqual(point.y(), capture_window.height())
                QTest.mouseClick(capture_window, Qt.LeftButton, pos=point.toPoint())
                if capture_window.isVisible():
                    frame(capture_window)
                else:
                    self.app.processEvents()
            drag(QPoint(100, 100), QPoint(350, 260))
            selection = CaptureFixtures._visual(capture_window.contentItem(), 'screenshotSelection')
            self.assertTrue(selection.property('ready'))
            self.assertEqual((selection.width(), selection.height()), (250, 160))
            drag(QPoint(150, 150), QPoint(200, 180))
            self.assertEqual((selection.x(), selection.y()), (150, 130))
            handle = CaptureFixtures._visual(capture_window.contentItem(), 'screenshotResizeHandle')
            point = handle.mapToScene(QPointF(12, 12)).toPoint()
            drag(point, point + QPoint(40, 30))
            self.assertGreater(selection.width(), 250)
            self.assertGreater(selection.height(), 160)
            click('screenshotDrawAgainButton')
            self.assertFalse(selection.property('ready'))
            QTest.mouseClick(capture_window, Qt.LeftButton, pos=QPoint(5, 5))
            frame(capture_window)
            self.assertEqual((selection.x(), selection.y(), selection.width(), selection.height()), (0, 0, 128, 128))
            capture_window.resize(390, 700)
            frame(capture_window)
            for name in ('screenshotDrawAgainButton', 'screenshotCaptureButton'):
                button = CaptureFixtures._visual(capture_window.contentItem(), name)
                self.assertFalse(CaptureFixtures._visual(button, 'buttonLabel').property('truncated'))
            controller._capture = Mock()
            click('screenshotCaptureButton')
            controller._capture.assert_called_once_with(capture_window.x(), capture_window.y(), 128, 128, 'operation-7')
            self.assertFalse(capture_window.isVisible())
            self.assertIsNone(controller._pending_capture)
            self.assertEqual(warnings, [])
        finally:
            controller._busy = False
            controller._restore_windows()
            controller.shutdown()
            host_window.close()
            source_window.close()
            for item in (view, theme, engine, host_window, source_window, controller, windows):
                item.deleteLater()
            self.app.sendPostedEvents(None, QEvent.DeferredDelete)
            self.app.processEvents()

if __name__ == '__main__':
    unittest.main()
