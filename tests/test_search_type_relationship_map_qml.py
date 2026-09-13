"""Real QML interaction for the read-only Search Type relationship map."""

import os
from pathlib import Path
import unittest

from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QSignalSpy, QTest

from tests.profile_ui_responsiveness import frame


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / 'thlib' / 'ui' / 'qml'


class SearchTypeRelationshipMapQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        os.environ.setdefault('QT_QUICK_BACKEND', 'software')
        os.environ.setdefault('QT_QUICK_CONTROLS_STYLE', 'Material')
        if os.name == 'nt':
            os.environ.setdefault(
                'QT_QPA_FONTDIR',
                str(Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'),
            )
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        self.engine = QQmlEngine()
        self.engine.addImportPath(str(QML))
        self.warnings = []
        self.engine.warnings.connect(
            lambda errors: self.warnings.extend(error.toString() for error in errors))
        self.theme_component = QQmlComponent(
            self.engine, QUrl.fromLocalFile(str(QML / 'Theme.qml')))
        self.theme = self.theme_component.createWithInitialProperties({'dark': True})
        self.component = QQmlComponent(
            self.engine,
            QUrl.fromLocalFile(str(QML / 'AdminSearchTypeRelationshipMap.qml')),
        )
        graph_data = {
            'center': 'demo/asset',
            'nodes': [
                {'identity': 'demo/asset', 'label': 'Assets', 'nodeX': 40, 'nodeY': 32,
                 'kind': 'asset', 'color': '', 'referenceOnly': True},
                {'identity': 'demo/shot', 'label': 'Shots', 'nodeX': 360, 'nodeY': 148,
                 'kind': 'shot', 'color': '', 'referenceOnly': True},
            ],
            'edges': [
                {'from': 'demo/asset', 'to': 'demo/shot', 'edgeIndex': 0, 'label': 'code'},
            ],
        }
        self.owner = self.component.createWithInitialProperties({
            'theme': self.theme, 'graphData': graph_data, 'width': 900, 'height': 480,
        })
        self.assertIsNotNone(
            self.owner, [error.toString() for error in self.component.errors()])
        self.window = QQuickWindow()
        self.window.resize(900, 480)
        self.owner.setParentItem(self.window.contentItem())
        self.addCleanup(self.close_view)
        self.window.show()
        frame(self.window)
        self.graph = self.item('adminSearchTypeRelationshipGraph')

    def close_view(self):
        self.window.close()
        self.owner.setParentItem(None)
        self.owner.deleteLater()
        self.window.deleteLater()
        self.theme.deleteLater()
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    @staticmethod
    def descendants(item):
        for child in item.childItems():
            yield child
            yield from SearchTypeRelationshipMapQmlTests.descendants(child)

    def item(self, name):
        return next(
            item for item in self.descendants(self.owner) if item.objectName() == name)

    @staticmethod
    def center(item):
        return item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()

    def test_map_is_non_editable_but_zoom_and_pan_remain_interactive(self):
        for width in (520, 900):
            with self.subTest(width=width):
                self.window.resize(width, 480)
                self.owner.setWidth(width)
                frame(self.window)
                reset = self.item('adminSearchTypeRelationshipReset')
                self.assertGreaterEqual(reset.mapToScene(QPointF()).x(), 0)
                self.assertLessEqual(
                    reset.mapToScene(QPointF(reset.width(), 0)).x(), width)
        self.assertTrue(self.graph.property('readOnly'))
        self.assertFalse(self.graph.property('selectionEnabled'))
        selected = QSignalSpy(self.graph.nodesSelected)
        QTest.mouseClick(
            self.window, Qt.LeftButton, pos=self.center(self.item('graphNode_demo/asset')))
        frame(self.window)
        self.assertEqual(selected.count(), 0)

        zoom_in = self.item('adminSearchTypeRelationshipZoomIn')
        QTest.mouseClick(self.window, Qt.LeftButton, pos=self.center(zoom_in))
        frame(self.window)
        self.assertGreater(self.graph.property('zoom'), 1)

        canvas = self.item('adminGraphCanvas')
        origin = (canvas.property('contentX'), canvas.property('contentY'))
        start = self.center(canvas)
        QTest.mousePress(self.window, Qt.MiddleButton, pos=start)
        QTest.mouseMove(self.window, start - QPoint(100, 60))
        QTest.mouseRelease(self.window, Qt.MiddleButton, pos=start - QPoint(100, 60))
        frame(self.window)
        self.assertNotEqual(
            (canvas.property('contentX'), canvas.property('contentY')), origin)
        self.assertEqual(self.warnings, [])


if __name__ == '__main__':
    unittest.main()
