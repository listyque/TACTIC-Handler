import os
from pathlib import Path
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
os.environ.setdefault('QT_QUICK_CONTROLS_STYLE', 'Basic')

from PySide6.QtCore import QObject, Property, QPointF, Q_ARG, QMetaObject, Qt, QUrl, Slot
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest
from tests.qt_application import gui_test_application


class Controller(QObject):
    advancedBusy = Property(bool, lambda self: False, constant=True)
    advancedSaving = Property(bool, lambda self: False, constant=True)

    def __init__(self):
        super().__init__()
        self.edits = []

    @Slot(str, str, str, str, result=bool)
    def stage_advanced_context_value(self, task, parent, field, value):
        self.edits.append((task, parent, field, value))
        return True


def items(root):
    yield root
    for child in root.childItems():
        yield from items(child)


class TaskInlineEditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def test_progress_slider_hours_stepper_and_paired_dates(self):
        qml = Path(__file__).resolve().parents[1] / 'thlib/ui/qml'
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
        theme_component = QQmlComponent(engine, QUrl.fromLocalFile(str(qml / 'Theme.qml')))
        theme = theme_component.createWithInitialProperties({'dark': True})
        theme.setProperty('popupAnimationsEnabled', False)
        component = QQmlComponent(engine, QUrl.fromLocalFile(str(qml / 'features/tasks/TaskInlinePopup.qml')))
        capture = os.environ.get('TASK_EDITOR_CAPTURE')
        if capture:
            from PySide6.QtGui import QFontDatabase
            from thlib.ui.icon_font import qml_icon_bindings
            for font in ('segoeui.ttf', 'seguisb.ttf', 'segoeuib.ttf'):
                QFontDatabase.addApplicationFont('C:/Windows/Fonts/' + font)
            for name, value in qml_icon_bindings(qml.parents[2]).items():
                engine.rootContext().setContextProperty(name, value)
            Path(capture).mkdir(parents=True, exist_ok=True)
        controller = Controller()
        window = QQuickWindow()
        window.resize(800, 600)
        anchor = QQuickItem(window.contentItem())
        anchor.setPosition(QPointF(24, 24))
        anchor.setWidth(180)
        anchor.setHeight(32)
        window.show()
        QTest.qWait(30)
        try:
            for field in ('progress', 'hours', 'dates'):
                popup = component.createWithInitialProperties({
                    'theme': theme, 'controller': controller, 'field': field,
                    'parent': window.contentItem(), 'usePopupWindow': False,
                    'record': {'taskCode': 'TASK1', 'parentKey': 'demo/asset?code=ASSET1',
                               'plannedHours': 2, 'progress': 20, 'start': '', 'end': ''},
                })
                self.assertIsNotNone(popup, [e.toString() for e in component.errors()])
                QMetaObject.invokeMethod(popup, 'openBelow', Q_ARG('QVariant', anchor))
                QTest.qWait(60)
                content = popup.property('contentItem')
                named = {i.objectName(): i for i in items(content) if i.objectName()}
                if field == 'progress':
                    slider = named['taskInlineProgress']
                    slider.forceActiveFocus()
                    QTest.keyClick(window, Qt.Key_Right)
                    self.assertEqual(slider.property('value'), 21)
                    self.assertEqual(controller.edits[-1][-2:], ('progress', '21'))
                elif field == 'hours':
                    spin = named['taskInlineHours']
                    spin.forceActiveFocus()
                    QTest.keyClick(window, Qt.Key_Up)
                    self.assertEqual(spin.property('realValue'), 2.25)
                    self.assertEqual(controller.edits[-1][-2:], ('plannedHours', '2.25'))
                else:
                    self.assertIn('taskInlineStart', named)
                    self.assertIn('taskInlineDeadline', named)
                if capture:
                    origin = window.contentItem().mapToScene(QPointF(popup.property('x'), popup.property('y')))
                    window.grabWindow().copy(int(origin.x()), int(origin.y()), int(popup.property('width')), int(popup.property('height'))).save(str(Path(capture) / ('native-' + field + '.png')))
                QMetaObject.invokeMethod(popup, 'close')
                popup.deleteLater()
                QTest.qWait(30)
            self.assertTrue(all(edit[:2] == ('TASK1', 'demo/asset?code=ASSET1') for edit in controller.edits))
            self.assertEqual(warnings, [])
        finally:
            window.close()
