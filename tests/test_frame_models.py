"""Editing a Frame row keeps the native table and its viewport intact."""
import unittest
from PySide6.QtCore import QModelIndex
from PySide6.QtTest import QSignalSpy
from thlib.ui.frame_models import FrameTableModel


class FrameTableModelTests(unittest.TestCase):
    def test_edits_publish_data_without_reset_and_shape_changes_reset(self):
        rows = [{'value': 'old'}]
        columns = [3]
        model = FrameTableModel(lambda: rows, lambda: columns[0])
        changed, reset = QSignalSpy(model.dataChanged), QSignalSpy(model.modelReset)
        self.assertEqual((model.rowCount(), model.columnCount()), (1, 3))
        rows[0]['value'] = 'edited'
        model.refresh()
        self.assertEqual(model.data(model.index(0, 2), model.CELL), {'value': 'edited'})
        self.assertEqual((changed.count(), reset.count()), (1, 0))
        rows.append({'value': 'new'})
        model.refresh()
        self.assertEqual((model.rowCount(), reset.count()), (2, 1))
        columns[0] = 1
        model.refresh()
        self.assertEqual((model.columnCount(), reset.count()), (1, 2))
        previous = model.index(1, 0)
        rows.pop()
        self.assertEqual(model.data(previous, model.CELL), {'value': 'new'}, 'old indices remain valid until model reset')
        model.refresh()
        self.assertEqual(model.rowCount(), 1)
        self.assertIsNone(model.data(previous, model.CELL))
        self.assertIsNone(model.data(QModelIndex(), model.CELL))
        self.assertIsNone(model.data(model.index(0, 0)))
