"""Window content URLs keep their QML-root contract after host organization."""
import os
from pathlib import Path
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')

from PySide6.QtCore import QCoreApplication, QEvent, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from tests.qt_application import gui_test_application
from tests.profile_ui_responsiveness import frame

QML = Path(__file__).resolve().parents[1] / 'thlib/ui/qml'


class WindowContentTests(unittest.TestCase):
    def test_root_relative_absolute_and_fallback_sources(self):
        app = gui_test_application()
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
        theme_component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / 'Theme.qml')))
        theme = theme_component.createWithInitialProperties({'dark': True})
        self.assertIsNotNone(theme, theme_component.errors())
        component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / 'shell/windows/WindowContent.qml')))
        self.assertTrue(component.isReady(), component.errors())
        host = component.createWithInitialProperties({'theme': theme, 'contentSource': '', 'width': 400, 'height': 200})
        self.assertIsNotNone(host, component.errors())
        window = QQuickWindow()
        window.resize(400, 200)
        host.setParentItem(window.contentItem())
        window.show()
        try:
            for source in ['', 'shell/windows/UnregisteredWindow.qml', QUrl.fromLocalFile(str(QML / 'shell/windows/UnregisteredWindow.qml')).toString()]:
                with self.subTest(source=source):
                    host.setProperty('contentSource', source)
                    frame(window)
                    loader = host.childItems()[0]
                    item = loader.property('item')
                    self.assertIsNotNone(item, warnings)
                    self.assertEqual(host.property('contentItem'), item)
                    self.assertEqual(item.width(), 400)
                    self.assertEqual(item.height(), 200)
            self.assertEqual(warnings, [])
        finally:
            window.close()
            host.setParentItem(None)
            host.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
            theme.deleteLater()
            window.deleteLater()
            app.processEvents()


if __name__ == '__main__':
    unittest.main()
