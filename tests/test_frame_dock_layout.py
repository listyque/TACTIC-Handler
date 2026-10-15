"""Real native input on the shared dock tree, tab order and floating corners."""

import unittest
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QPointF, QUrl, Qt
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QTest
from tests.qt_application import gui_test_application
from tests.profile_ui_responsiveness import frame
import tests.test_sidebar_editor_qml as fixture
from thlib.ui.icon_font import qml_icon_bindings
from thlib.ui.workspace_models.docks import DockPanelModel
from thlib.ui.workspace_models.docks_tree import (
    DockStack,
    serialize_layout,
    stack_for_panel,
)

ROOT = Path(__file__).resolve().parents[1]


class FrameDockLayoutTests(unittest.TestCase):
    def setUp(self):
        self.app = gui_test_application()
        self.engine = QQmlEngine()
        self.model = DockPanelModel({})
        self.warnings = []
        self.engine.warnings.connect(
            lambda errors: self.warnings.extend(error.toString() for error in errors)
        )
        for name, value in dict(
            qml_icon_bindings(ROOT, self.app), dockModel=self.model
        ).items():
            self.engine.rootContext().setContextProperty(name, value)
        self.component = component = QQmlComponent(self.engine)
        source = (
            (ROOT / "tests/fixtures/DockWorkspaceHarness.qml")
            .read_text(encoding="utf-8")
            .replace("__QML_ROOT__", (ROOT / "thlib/ui/qml").as_uri())
        )
        component.setData(source.encode("utf-8"), QUrl())
        self.assertTrue(
            component.isReady(), [error.toString() for error in component.errors()]
        )
        self.window = component.createWithInitialProperties(
            dict(width=1200, height=900)
        )
        self.assertIsNotNone(self.window)
        self.window.requestActivate()
        frame(self.window)

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.assertEqual(self.warnings, [])

    def items(self):
        return list(
            fixture.SidebarEditorQmlTests.descendants(self.window.contentItem())
        )

    def item(self, name):
        return next(
            item
            for item in self.items()
            if item.objectName() == name and item.isVisible()
        )

    def tabs(self):
        configuration = self.model.capture_layout()
        configuration["layout"] = serialize_layout(
            DockStack(("results", "notes", "description", "snapshot"), "notes")
        )
        for panel in configuration["panels"]:
            panel["visible"] = panel["panel_id"] in ("results", "notes", "snapshot")
        self.assertTrue(self.model.apply_layout(configuration))
        frame(self.window)

    def drag_tab(self):
        source = self.item("dockTab_notes_snapshot")
        target = self.item("dockTab_notes_results")
        start = source.mapToScene(
            QPointF(source.width() / 2, source.height() / 2)
        ).toPoint()
        end = target.mapToScene(
            QPointF(target.width() / 2 - 20, target.height() / 2)
        ).toPoint()
        QTest.mousePress(self.window, Qt.LeftButton, pos=start)
        QTest.mouseMove(self.window, start + QPoint(-15, 0))
        QTest.mouseMove(self.window, end)
        frame(self.window)
        return end

    def test_real_tab_reorder_keeps_hidden_slots_and_survives_restore(self):
        self.tabs()
        end = self.drag_tab()
        QTest.mouseRelease(self.window, Qt.LeftButton, pos=end)
        frame(self.window)
        order = stack_for_panel(self.model._layout_root, "results").panel_ids
        self.assertEqual(order, ("snapshot", "results", "description", "notes"))
        restored = DockPanelModel(dict(self.model._settings))
        self.assertEqual(restored.capture_layout(), self.model.capture_layout())

    def test_touch_reorders_tabs_without_triggering_activation(self):
        self.tabs()
        source = self.item("dockTab_notes_snapshot")
        target = self.item("dockTab_notes_results")
        start = source.mapToScene(
            QPointF(source.width() / 2, source.height() / 2)
        ).toPoint()
        end = target.mapToScene(
            QPointF(target.width() / 2 - 20, target.height() / 2)
        ).toPoint()
        device = QTest.createTouchDevice()
        QTest.touchEvent(self.window, device).press(0, start, self.window).commit()
        frame(self.window)
        QTest.touchEvent(self.window, device).move(
            0, start + QPoint(-20, 0), self.window
        ).commit()
        frame(self.window)
        QTest.touchEvent(self.window, device).move(0, end, self.window).commit()
        frame(self.window)
        QTest.touchEvent(self.window, device).release(0, end, self.window).commit()
        frame(self.window)
        self.assertEqual(
            stack_for_panel(self.model._layout_root, "results").panel_ids,
            ("snapshot", "results", "description", "notes"),
        )

        self.assertEqual(
            stack_for_panel(self.model._layout_root, "results").active_panel_id, "notes"
        )

    def test_escape_cancels_tab_reorder_without_saving(self):
        self.tabs()
        before = self.model.capture_layout()
        saves = []
        self.model._save = lambda: saves.append(True)
        end = self.drag_tab()
        self.assertTrue(self.item("dockPanel_notes").property("tabDragging"))
        QTest.keyClick(self.window, Qt.Key_Escape)
        frame(self.window)
        self.assertFalse(self.item("dockPanel_notes").property("tabDragging"))
        QTest.mouseRelease(self.window, Qt.LeftButton, pos=end)
        frame(self.window)
        self.assertEqual(self.model.capture_layout(), before)
        self.assertEqual(saves, [])

    def test_all_eight_floating_handles_keep_minimum_and_opposite_edge(self):
        for edge in [
            "left",
            "right",
            "top",
            "bottom",
            "top_left",
            "top_right",
            "bottom_left",
            "bottom_right",
        ]:
            with self.subTest(edge=edge):
                self.model.float_panel("notes", 0.1, 0.1, 0.6, 0.6)
                frame(self.window)
                panel = self.item("dockPanel_notes")
                before_rect = (panel.x(), panel.y(), panel.width(), panel.height())
                handle = next(
                    item
                    for item in fixture.SidebarEditorQmlTests.descendants(panel)
                    if item.objectName() == "dockResizeEdge_" + edge
                    and item.isVisible()
                )
                start = handle.mapToScene(
                    QPointF(handle.width() / 2, handle.height() / 2)
                ).toPoint()
                delta = QPoint(
                    500 if "left" in edge else -500, 500 if "top" in edge else -500
                )
                end = start + delta
                QTest.mousePress(self.window, Qt.LeftButton, pos=start)
                QTest.mouseMove(self.window, end)
                frame(self.window)
                QTest.mouseRelease(self.window, Qt.LeftButton, pos=end)
                frame(self.window)
                self.assertGreaterEqual(panel.width(), 400)
                self.assertGreaterEqual(panel.height(), 300)
                if "left" in edge:
                    self.assertAlmostEqual(
                        panel.x() + panel.width(),
                        before_rect[0] + before_rect[2],
                        delta=1,
                        msg=str(before_rect),
                    )
                if "top" in edge:
                    self.assertAlmostEqual(
                        panel.y() + panel.height(),
                        before_rect[1] + before_rect[3],
                        delta=1,
                        msg=str(before_rect),
                    )
