"""Counted custom-card actions paint native badges and preserve their input path."""

import math
from pathlib import Path
import unittest

from PySide6.QtCore import QObject, Slot, Qt
from PySide6.QtTest import QTest

from tests import test_frame_table as frames
from tests.test_columns_table_view import _visual_items
from tests.qt_application import run_native_windows_test
from thlib.ui.icon_font import qml_icon_bindings

ROOT = Path(__file__).resolve().parents[1]


class Actions(QObject):
    def __init__(self):
        super().__init__()
        self.calls = []

    @Slot(str, str)
    def invoke_item_action(self, action: str, node_id: str) -> None:
        self.calls.append((action, node_id))


class ItemActionBadgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()

    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close
    item = frames.FrameTableTests.item
    click = frames.FrameTableTests.click

    def test_task_and_note_badges_paint_counts_and_follow_updates(self):
        if run_native_windows_test(self):
            return
        actions = Actions()
        layout = dict(flow="grid", collection="tree", columns=12, gap=4,
                      elements=[dict(name=name, kind="button", row=1,
                                     column=column, span=6, rows=1, height=40,
                                     parent="", variant="all",
                                     options=dict(action=name, icon=icon,
                                                  badge="node." + field))
                                for name, icon, column, field in (
                                    ("tasks", "task", 1, "task_count"),
                                    ("notes", "comment", 7, "note_count"))])
        def record(count):
            return dict(kind="object", record={},
                        task_count=count, note_count=count)
        window, view = self.create(
            "features/search/ConfiguredItem.qml",
            dict(controller=actions, nodeId="demo/record?code=P1",
                 layout=layout, record=record(5)), width=360, height=120,
            context=qml_icon_bindings(ROOT, self.app),
        )
        window.setColor(view.property("theme").property("workspace"))
        buttons = {name: self.item(view, "itemComposition_" + name + "Button")
                   for name in ("tasks", "notes")}
        for count in (5, 1, 12, 99, 100, 0, 5):
            view.setProperty("record", record(count))
            frames.frame(window)
            image = window.grabWindow()
            scale = image.width() / window.width()
            for name, button in buttons.items():
                self.assertIs(self.item(view, "itemComposition_" + name + "Button"), button)
                self.assertEqual(button.property("toolTip"),
                                 name.title() + (f" · {count}" if count else ""))
                text = "99+" if count > 99 else str(count)
                labels = [item for item in _visual_items(button)
                          if item.property("text") == text and item.isVisible()]
                if count == 0:
                    self.assertEqual(labels, [])
                    continue
                self.assertEqual(len(labels), 1, f"{name} badge {text} is missing")
                label = labels[0]
                self.assertGreater(label.width(), 3)
                point = label.mapToScene(label.boundingRect().topLeft())
                bounds = (math.floor(point.x() * scale), math.floor(point.y() * scale),
                          math.ceil((point.x() + label.width()) * scale),
                          math.ceil((point.y() + label.height()) * scale))
                light_pixels = sum(
                    min(image.pixelColor(x, y).red(), image.pixelColor(x, y).green(),
                        image.pixelColor(x, y).blue()) > 200
                    for x in range(max(0, bounds[0]), min(image.width(), bounds[2]))
                    for y in range(max(0, bounds[1]), min(image.height(), bounds[3]))
                )
                self.assertGreater(light_pixels, 2, f"{name} badge text is not painted")
        self.click(window, buttons["tasks"])
        self.click(window, buttons["notes"])
        self.assertEqual(actions.calls, [("tasks", "demo/record?code=P1"),
                                        ("notes", "demo/record?code=P1")])
        buttons["tasks"].forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Space)
        self.assertEqual(actions.calls[-1], ("tasks", "demo/record?code=P1"))
        self.assertEqual(len(actions.calls), 3)


if __name__ == "__main__":
    unittest.main()
