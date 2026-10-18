"""Real queue owner, QML controls and pointer/keyboard paths in an isolated tree."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_CONTROLS_STYLE', 'Basic')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
from PySide6.QtCore import QObject, Property, Slot, QPointF, Qt, QUrl, QEvent
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlEngine, QQmlComponent, QQmlExpression
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from tests.frame_files_fixture import Fixture
from tests.profile_ui_responsiveness import frame
from tests.test_commit_queue import payload
from thlib.ui.commit_queue import CommitQueueController

QML = Path(__file__).resolve().parents[1] / 'thlib/ui/qml'

def visual(item, name):
    if item.objectName() == name:
        return item
    for child in item.childItems():
        result = visual(child, name)
        if result is not None:
            return result

class Screenshot(QObject):
    @Property(bool, constant=True)
    def clipboardHasImage(self):
        return False

    @Slot(str)
    def prepare_for_operation(self, value):
        pass

class FrameQueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_owner_input_options_menus_and_virtualization(self):
        with Fixture() as fixture, tempfile.TemporaryDirectory() as tmp:
            fixture.enter_context(patch('thlib.ui.commit_queue.env_read_config', return_value={}))
            fixture.enter_context(patch('thlib.ui.commit_queue.env_write_config'))
            fixture.enter_context(patch('thlib.environment.env_tactic.get_all_base_dirs', return_value=[]))
            queue = CommitQueueController()
            screenshot = Screenshot()
            for index in range(2):
                path = Path(tmp) / f'source_{index}.txt'
                path.write_text('queue input', encoding='utf-8')
                queue.add_prepared(payload(path), f'Asset {index}')
            queue.select_row(0)
            first_id = queue.selectedId
            engine = QQmlEngine()
            warnings = []
            engine.warnings.connect(lambda errors: warnings.extend(str(error) for error in errors))
            for key, value in dict(fixture.context(), commitQueueController=queue,
                                   commitQueueModel=queue.model, screenshotController=screenshot).items():
                engine.rootContext().setContextProperty(key, value)
            theme_component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / 'Theme.qml')))
            theme = theme_component.createWithInitialProperties({'dark': True})
            component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / 'CommitQueueView.qml')))
            view = component.createWithInitialProperties({'theme': theme})
            self.assertIsNotNone(view, '\n'.join(str(error) for error in component.errors()))
            window = QQuickWindow()
            view.setParentItem(window.contentItem())
            window.resize(1000, 700)
            view.setWidth(1000)
            view.setHeight(700)
            window.show()
            def click(name, button=Qt.LeftButton):
                item = visual(window.contentItem(), name)
                self.assertIsNotNone(item, name)
                QTest.mouseClick(window, button, pos=item.mapToScene(QPointF(item.width()/2, item.height()/2)).toPoint())
                frame(window)
            def type_text(name, text):
                click(name)
                QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
                for char in text:
                    QTest.keyClick(window, Qt.Key(ord(char.upper())))
                frame(window)
            try:
                frame(window)
                self.assertEqual(warnings, [])
                expression = QQmlExpression(engine.rootContext(), view, 'controller.row_for_id(controller.selectedId)')
                self.assertEqual(expression.evaluate()[0], 0)
                click('commitQueueCheck_' + first_id)
                self.assertFalse(queue.selectedRecord['checked'])
                click('commitQueueSelect_' + first_id)
                QTest.keyClick(window, Qt.Key_Down)
                frame(window)
                self.assertEqual(queue.selectedRow, 1)
                QTest.keyClick(window, Qt.Key_Home)
                frame(window)
                self.assertEqual(queue.selectedRow, 0)
                click('commitQueueSelect_' + first_id, Qt.RightButton)
                self.assertIsNotNone(visual(window.contentItem(), 'commitQueueTitle_' + first_id))
                QTest.keyClick(self.app.focusWindow() or window, Qt.Key_Escape)
                frame(window)
                click('commitQueueAdvancedToggle')
                type_text('commitQueueField_version', 'bad')
                QTest.keyClick(window, Qt.Key_Tab)
                frame(window)
                self.assertTrue(view.property('versionError'))
                self.assertEqual(queue.selectedRecord['version'], 0)
                type_text('commitQueueField_version', '12')
                QTest.keyClick(window, Qt.Key_Return)
                frame(window)
                self.assertEqual(queue.selectedRecord['version'], 12)
                self.assertFalse(view.property('versionError'))
                click('commitQueueContextChip')
                type_text('commitQueueContextField', 'review')
                QTest.keyClick(window, Qt.Key_Return)
                frame(window)
                self.assertEqual(queue.selectedRecord['context'], 'publish/review')
                click('commitQueueTool_clear')
                dialog = view.findChild(QObject, 'commitQueueClearConfirmation')
                self.assertTrue(dialog.property('opened'))
                QTest.keyClick(window, Qt.Key_Escape)
                frame(window)
                self.assertEqual(queue.count, 2)
                for width, height in ((680, 760), (390, 700), (1000, 700)):
                    window.resize(width, height)
                    view.setWidth(width)
                    view.setHeight(height)
                    frame(window)
                    name = 'commitQueueDetailsPanel' if width >= 700 else 'commitQueueFilesDock'
                    item = visual(view, name)
                    self.assertIsNotNone(item, name)
                    point = item.mapToScene(QPointF())
                    self.assertGreaterEqual(point.x(), 0)
                    self.assertLessEqual(point.x() + item.width(), width)
                    self.assertLessEqual(point.y() + item.height(), height)
                splitter = visual(view, 'commitQueueMainSplitter')
                before = queue.splitterRatio
                point = splitter.mapToScene(QPointF(splitter.width()/2, splitter.height()/2)).toPoint()
                QTest.mousePress(window, Qt.LeftButton, pos=point)
                QTest.mouseMove(window, point + QPointF(48, 0).toPoint(), delay=30)
                QTest.mouseRelease(window, Qt.LeftButton, pos=point + QPointF(48, 0).toPoint())
                frame(window)
                self.assertGreater(queue.splitterRatio, before)
                template = dict(queue.selectedRecord)
                queue.model.append_records([dict(template, operationId=f'virtual_{index}', title=f'File {index}') for index in range(1000)])
                frame(window)
                lst = visual(view, 'commitQueueRows')
                self.assertLess(len(lst.property('contentItem').childItems()), 50)
                self.assertEqual(warnings, [])
            finally:
                window.close()
                view.deleteLater()
                window.deleteLater()
                theme.deleteLater()
                self.app.sendPostedEvents(None, QEvent.DeferredDelete)
                self.app.processEvents()

if __name__ == '__main__':
    unittest.main()
