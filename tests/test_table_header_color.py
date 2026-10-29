"""Real native table headers use the shared independent surface role."""

import json
import os
from pathlib import Path
import unittest
from PySide6.QtQuick import QQuickItem
import tests.test_frame_table as frames
from tests.test_columns_table_view import _TableColumns, _TableController
from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.results_types import WorkspaceNode
from thlib.ui.icon_font import qml_icon_bindings


class TableHeaderColorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()

    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close
    item = frames.FrameTableTests.item

    def test_header_is_distinct_with_readable_grouped_labels(self):
        captures = []
        for dark in (True, False):
            for grouped in (False, True):
                columns = _TableColumns()
                columns._columns = columns._columns[1:3]
                controller = _TableController()
                if grouped:
                    controller.set_result_group_mode("column:code")
                model = WorkspaceItemModel()
                model.replace_nodes(
                    [
                        WorkspaceNode(
                            node_id="A",
                            node_type="sobject",
                            search_key="demo/asset?code=A",
                            code="A",
                            title="Workshop",
                        )
                    ]
                )
                window, table = self.create(
                    "SearchResultTable.qml",
                    dict(
                        controller=controller,
                        columnsController=columns,
                        resultModel=model,
                    ),
                    width=600,
                    height=160,
                    context=qml_icon_bindings(
                        Path(__file__).resolve().parents[1], self.app
                    ),
                )
                theme = table.property("theme")
                theme.setProperty("dark", dark)
                window.setColor(theme.property("workspace"))
                frames.frame(window)
                surface = table.findChild(QQuickItem, "tableHeaderSurface")
                color = surface.property("color")
                self.assertEqual(color, theme.property("tableHeader"))
                for role in ("toolBar", "surfaceContainerLow", "surfaceContainerHigh"):
                    other = theme.property(role)
                    self.assertGreaterEqual(
                        max(
                            abs(color.red() - other.red()),
                            abs(color.green() - other.green()),
                            abs(color.blue() - other.blue()),
                        ),
                        16,
                    )
                label = self.item(table, "tableColumnHeaderLabel_code")
                self.assertEqual(label.property("color"), theme.property("primaryText"))
                output = os.environ.get("TABLE_HEADER_OUTPUT")
                name = f"{str(dark).lower()}-{str(grouped).lower()}"
                if output:
                    target = Path(output)
                    target.mkdir(parents=True, exist_ok=True)
                    window.grabWindow().save(str(target / f"native-{name}.png"))
                captures.append(
                    dict(
                        name=name, background=[color.red(), color.green(), color.blue()]
                    )
                )
                self.doCleanups()
        if os.environ.get("TABLE_HEADER_OUTPUT"):
            (Path(os.environ["TABLE_HEADER_OUTPUT"]) / "native.json").write_text(
                json.dumps(captures), encoding="utf-8"
            )


if __name__ == "__main__":
    unittest.main()
