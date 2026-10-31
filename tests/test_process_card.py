"""Compact workflow cards keep real native controls and aligned, quiet fields."""
import json
import os
from pathlib import Path
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QObject, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication, QFontDatabase, QColor
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest
from tests.test_columns_table_view import _TableColumns, _TableController, _visual_items
from thlib.ui.workspace_models.records import RecordListModel
from thlib.ui.icon_font import qml_icon_bindings

ROOT = Path(__file__).resolve().parents[1]
QML = ROOT/'thlib/ui/qml'
RECORDS = [
    {'process': 'assets', 'processLabel': 'ASSETS', 'processType': 'progress', 'processColor': '#78a6c4', 'progress': {'state': 'ready', 'complete': 3, 'total': 10}},
    {'process': 'model', 'processLabel': 'Model', 'status': 'Review', 'statusColor': '#5caa70', 'assigned': 'anna', 'assignedIdentity': {'displayName': 'Anna', 'initials': 'A', 'avatarColor': '#43796c'}, 'bidStart': '2026-10-28', 'bidEnd': '2026-11-02', 'simpleDates': True},
    {'process': 'rig', 'processLabel': 'Подготовка персонажа', 'status': 'На проверке', 'processColor': '#a48bd2'}
]


class ProcessCardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        for font in ['segoeui.ttf', 'seguisb.ttf']:
            QFontDatabase.addApplicationFont('C:/Windows/Fonts/'+font)

    def test_card_fields_are_flat_aligned_and_keep_native_actions(self):
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
        for key, value in qml_icon_bindings(ROOT).items():
            engine.rootContext().setContextProperty(key, value)
        theme_component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML/'Theme.qml')))
        theme = theme_component.createWithInitialProperties({'dark': True})
        columns, controller = _TableColumns(), _TableController()
        users = RecordListModel(('login', 'displayName', 'initials', 'avatarUrl', 'avatarColor', 'email', 'primaryGroup'))
        users.replace([{'login': 'anna', 'displayName': 'Anna', 'initials': 'A', 'avatarColor': '#43796c'}])
        component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML/'TacticTaskCards.qml')))
        cards = component.createWithInitialProperties({'theme': theme, 'controller': controller, 'columnsController': columns, 'userModel': users, 'nodeId': 'asset', 'records': RECORDS, 'cardWidth': 128, 'expanded': True, 'width': 392, 'height': 84})
        self.assertIsNotNone(cards, [error.toString() for error in component.errors()])
        window = QQuickWindow()
        window.resize(416, 108)
        window.setColor(QColor(theme.property('workspace')))
        cards.setParentItem(window.contentItem())
        cards.setPosition(QPointF(12, 12))
        window.show()
        try:
            QTest.qWait(40)
            items = {item.objectName(): item for item in _visual_items(cards) if item.objectName()}
            card = items['tableTaskRecord_0']
            self.assertEqual((card.width(), card.height()), (128, 84))
            status, assigned = items['tableTaskStatus_0'], items['tableTaskAssignee_0']
            self.assertFalse(status.property('editingAllowed'))
            self.assertFalse(assigned.property('editingAllowed'))
            for field in [status, assigned]:
                self.assertFalse(field.property('editorLoaded'))
                self.assertEqual(field.findChild(QObject, 'taskTableCellSurface').property('color').alpha(), 0)
            self.assertEqual(status.findChild(QQuickItem, 'taskTableCellDisplayLabel').x(), assigned.findChild(QQuickItem, 'taskTableCellDisplayLabel').x())
            self.assertFalse(status.isVisible())
            self.assertFalse(assigned.isVisible())
            texts = [item.property('text') for item in _visual_items(items['tableProcessProgress_0']) if item.property('text') is not None]
            self.assertIn('3/10', texts)
            self.assertTrue(any(item.objectName() == 'processProgressRing' for item in _visual_items(cards)))
            progress_action = next(item for item in _visual_items(cards) if item.objectName() == 'processProgressOpen')
            QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, progress_action.mapToScene(QPointF(progress_action.width()/2, progress_action.height()/2)).toPoint())
            self.assertEqual(controller.process_details[-1], ('asset', 'tasks', 'assets'))
            header = items['tableTaskHeader_1']
            QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, header.mapToScene(QPointF(header.width()/2, header.height()/2)).toPoint())
            self.assertEqual(controller.process_details[-1], ('asset', 'tasks', 'model'))
            output = os.environ.get('PROCESS_CARD_CAPTURE')
            if output:
                target = Path(output); target.mkdir(parents=True, exist_ok=True)
                window.grabWindow().save(str(target/'native.png'))
                (target/'records.json').write_text(json.dumps(RECORDS, ensure_ascii=False), encoding='utf-8')
                (target/'native.json').write_text(json.dumps({name: {'x': item.x(), 'y': item.y(), 'width': item.width(), 'height': item.height()} for name, item in items.items() if name.startswith(('tableTaskRecord_', 'tableTaskHeader_', 'tableTaskStatus_', 'tableTaskAssignee_', 'tableTaskDates_'))}, indent=2), encoding='utf-8')
            self.assertFalse(warnings, warnings)
        finally:
            window.close()
            cards.setParentItem(None)
            cards.deleteLater()
            theme.deleteLater()
            engine.deleteLater()
            QTest.qWait(5)
