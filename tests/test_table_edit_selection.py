"""Real table double-click editing preserves checkbox selection."""

import time
import unittest

from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest

from tests import test_frame_table as frames
from tests.test_columns_table_view import _TableColumns, _TableController, _visual_items
from thlib.ui.workspace_models.records import RecordListModel
from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.results_types import WorkspaceNode


class TableEditSelectionTests(unittest.TestCase):
    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close

    @classmethod
    def setUpClass(cls):
        frames.FrameTableTests.setUpClass.__func__(cls)

    def test_double_click_focuses_and_edits_without_changing_checkboxes(self):
        for selected in ([], ["other"], ["asset", "other"]):
            with self.subTest(selected=selected):
                model = WorkspaceItemModel()
                model.replace_nodes([WorkspaceNode(
                    node_id=identity, node_type="sobject", search_key=identity,
                    code=identity, title=title, values={"name": title},
                ) for identity, title in (("asset", "Oak"), ("other", "Pine"))])
                columns, controller = _TableColumns(), _TableController()
                columns._columns = [column for column in columns._columns
                                    if column["name"] == "name"]
                controller._selected = list(selected)
                users = RecordListModel(("login", "displayName", "initials", "avatarUrl"))
                window, view = self.create("SearchResultTable.qml", dict(
                    controller=controller, columnsController=columns, resultModel=model,
                    userModel=users, presentationActive=True,
                ), width=800, height=300)
                deadline = time.monotonic() + 1
                while (time.monotonic() < deadline and not any(
                    item.objectName() == "tableCellEditArea_name"
                    for item in _visual_items(view)
                )):
                    QTest.qWait(5)
                row = next(item for item in _visual_items(view)
                           if item.objectName() == "searchResultTableRow" and item.property("nodeId") == "asset")
                named = {item.objectName(): item for item in _visual_items(row) if item.objectName()}
                area = named["tableCellEditArea_name"]
                point = area.mapToScene(QPointF(area.width() / 2, area.height() / 2)).toPoint()
                QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point)
                self.assertEqual(controller.selected_node_id, "asset")
                self.assertEqual(controller.selected_result_node_ids, selected)
                QTest.mouseDClick(window, Qt.LeftButton, Qt.NoModifier, point)
                QTest.qWait(20)
                self.assertEqual(columns.editor_requests[-1], ("asset", "name"))
                self.assertEqual(controller.selected_node_id, "asset")
                self.assertEqual(controller.selected_result_node_ids, selected)
                self.assertEqual(named["tableSelection_asset"].property("checked"),
                                 "asset" in selected)
                self.assertEqual(view.findChild(QObject, "tableSelectionActions").property("active"),
                                 bool(selected))
                loader = named["tableCellEditor_name"]
                self.assertTrue(loader.property("active"))
                self.assertTrue(any(item.objectName() == "tableInlineValue"
                                    for item in _visual_items(loader.property("item"))))
                QTest.keyClick(window, Qt.Key_Escape)
                QTest.qWait(10)
                self.assertFalse(loader.property("active"))
                self.assertEqual(controller.selected_result_node_ids, selected)
                self.assertEqual(controller.field_updates, [])
                self.assertEqual(controller.double_clicks, [])


if __name__ == "__main__":
    unittest.main()
