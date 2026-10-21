"""Variable row geometry preserves focus without creating offscreen delegates."""
from pathlib import Path
import unittest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
import tests.test_frame_table as frames


class VariableRowsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()

    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close
    item = frames.FrameTableTests.item
    click = frames.FrameTableTests.click

    def rows(self, expanded=False):
        return [dict(key=key, text=key.upper(), extent=260 if expanded and key == 'b' else 40)
            for key in ('a', 'b', 'c', 'd')]

    def test_expand_above_focus_keeps_the_row_visible_and_clickable(self):
        fixture = Path(__file__).parent / 'fixtures/frame_controls/VariableRows.qml'
        window, view = self.create(fixture, dict(records=self.rows()), width=320, height=80)
        selected = []
        view.selected.connect(lambda action: selected.append(action.toVariant() if hasattr(action,"toVariant") else action))
        self.assertTrue(view.focusListRow('variableRows', 2, 'item-c'))
        frames.frame(window)
        before = self.item(view, 'item-c').mapToScene(frames.QPointF()).y()
        view.setProperty('records', self.rows(True))
        frames.frame(window)
        control = self.item(view, 'item-c')
        self.assertEqual(control.mapToScene(frames.QPointF()).y(), before)
        self.assertTrue(control.property('activeFocus'))
        self.assertEqual(self.item(view, 'variableRows').property('contentY'), 260)
        QTest.keyClick(window, Qt.Key_Space)
        frames.frame(window)
        self.assertEqual(selected[-1]['key'], 'c')
        self.click(window, control)
        self.assertEqual(selected[-1]['key'], 'c')
        view.setProperty('records', self.rows())
        frames.frame(window)
        self.assertEqual(self.item(view, 'variableRows').property('contentY'), 40)
        self.assertTrue(self.item(view, 'item-c').property('activeFocus'))

    def test_large_variable_list_creates_only_visible_rows(self):
        fixture = Path(__file__).parent / 'fixtures/frame_controls/VariableRows.qml'
        rows = [dict(key=str(index), text=str(index), extent=260 if index % 10 == 0 else 40)
            for index in range(10000)]
        window, view = self.create(fixture, dict(records=rows), width=320, height=160)
        self.assertLess(sum(item.objectName().startswith('item-') for item in frames._visual_items(view)), 12)
        self.assertTrue(view.focusListRow('variableRows', 8000, 'item-8000'))
        frames.frame(window)
        self.assertTrue(self.item(view, 'item-8000').property('activeFocus'))
        self.assertLess(sum(item.objectName().startswith('item-') for item in frames._visual_items(view)), 20)
