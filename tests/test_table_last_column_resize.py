"""The last adaptive column must survive a width drag across the viewport edge."""
import json
import os
from pathlib import Path
import unittest
from PySide6.QtCore import QPointF, Qt, Slot
from PySide6.QtTest import QTest
import tests.test_frame_table as frames
from tests.test_columns_table_view import _TableColumns, _TableController
from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.results_types import WorkspaceNode
from thlib.ui.icon_font import qml_icon_bindings


class ResizeColumns(_TableColumns):
    @Slot(str, int, result='QVariantMap')
    def row_cells(self, key, revision=0):
        return {}


class LastColumnResizeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()

    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close
    item = frames.FrameTableTests.item

    def test_last_column_grip_accepts_the_outer_side_of_the_divider(self):
        columns = ResizeColumns()
        columns._columns = [dict(row=0, name='code', label='Code', width=160, hideOrder=0),
            dict(row=1, name='notes', label='Notes', width=160, hideOrder=1)]
        model = WorkspaceItemModel()
        model.replace_nodes([WorkspaceNode(node_id='A', node_type='sobject', search_key='A', code='A0', title='Workshop')])
        window, table = self.create('SearchResultTable.qml', dict(controller=_TableController(),
            columnsController=columns, resultModel=model), width=424, height=160)
        column = self.item(table, 'tableColumnHeaderLabel_notes').parentItem()
        start = column.mapToScene(QPointF(column.width() + 3, column.height()/2)).toPoint()
        QTest.mouseMove(window, start)
        frames.frame(window)
        self.assertTrue(self.item(table, 'tableColumnResize_notes').property('containsMouse'))
        QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, start)
        QTest.mouseMove(window, start + QPointF(32, 0).toPoint(), 20)
        QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, start + QPointF(32, 0).toPoint())
        frames.frame(window)
        self.assertEqual(columns.width_changes, [(1, 192)])
        columns._columns = []
        columns.stateChanged.emit()
        frames.frame(window)
        with self.assertRaises(StopIteration):
            self.item(table, 'tableColumnResize_notes')

    def test_last_visible_column_remains_present_and_commits_its_drag(self):
        columns = ResizeColumns()
        columns._columns = [dict(row=0, name='code', label='Code', width=160, hideOrder=0),
            dict(row=1, name='notes', label='Notes', width=160, hideOrder=1)]
        model = WorkspaceItemModel()
        model.replace_nodes([WorkspaceNode(node_id='A', node_type='sobject', search_key='A', code='A0', title='Workshop')])
        window, table = self.create('SearchResultTable.qml', dict(controller=_TableController(),
            columnsController=columns, resultModel=model), width=424, height=160,
            context=qml_icon_bindings(Path(__file__).resolve().parents[1], self.app))
        window.setColor(table.property('theme').property('workspace'))
        captures = []
        def capture(stage):
            frames.frame(window)
            captures.append(dict(stage=stage, width=self.item(table, 'tableColumnHeaderLabel_notes').parentItem().width()))
            if os.environ.get('TABLE_RESIZE_OUTPUT'):
                output = Path(os.environ['TABLE_RESIZE_OUTPUT'])
                output.mkdir(parents=True, exist_ok=True)
                window.grabWindow().save(str(output/f'native-{stage}.png'))
        capture('initial')
        handle = self.item(table, 'tableColumnResize_notes')
        start = handle.mapToScene(QPointF(handle.width()/2, handle.height()/2)).toPoint()
        end = start + QPointF(48, 0).toPoint()
        QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, start)
        QTest.mouseMove(window, end, 20)
        QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, end)
        frames.frame(window)
        self.assertEqual(columns.width_changes, [(1, 208)])
        self.assertEqual(columns.apply_calls, 1)
        self.assertEqual(self.item(table, 'tableColumnHeaderLabel_notes').parentItem().width(), 208)
        capture('drag')
        bar = self.item(table, 'tableHorizontalScrollBar')
        self.assertTrue(bar.property('hasOverflow'))
        rows = self.item(table, 'searchResultsTableView')
        rows.setProperty('contentX', rows.property('contentWidth') - rows.width())
        frames.frame(window)
        handle = self.item(table, 'tableColumnResize_notes')
        start = handle.mapToScene(QPointF(handle.width()/2, handle.height()/2)).toPoint()
        QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, start)
        QTest.mouseMove(window, start - QPointF(24, 0).toPoint(), 20)
        handle.ungrabMouse()
        QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, start)
        frames.frame(window)
        self.assertEqual(columns.width_changes, [(1, 208)])
        handle = self.item(table, 'tableColumnResize_notes')
        self.assertEqual(self.item(table, 'tableColumnHeaderLabel_notes').parentItem().width(), 208)
        capture('cancel')
        handle.forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Left)
        frames.frame(window)
        self.assertEqual(columns.width_changes[-1], (1, 200))
        self.assertEqual(self.item(table, 'tableColumnHeaderLabel_notes').parentItem().width(), 200)
        capture('keyboard')
        columns._columns[1] = dict(columns._columns[1], width=120)
        columns.stateChanged.emit()
        frames.frame(window)
        self.assertEqual(self.item(table, 'tableColumnHeaderLabel_notes').parentItem().width(), 120)
        capture('server')
        if os.environ.get('TABLE_RESIZE_OUTPUT'):
            (Path(os.environ['TABLE_RESIZE_OUTPUT'])/'native.json').write_text(json.dumps(captures), encoding='utf-8')
