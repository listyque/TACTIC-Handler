from __future__ import annotations

import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QSignalSpy, QTest

from thlib.ui.workspace_models.sections import SectionTab, SectionTabModel


class SectionTabRailQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QGuiApplication.instance() or QGuiApplication([])
        cls.qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"

    @staticmethod
    def _visual_children(item, object_name):
        found = []
        for child in item.childItems():
            if child.objectName() == object_name:
                found.append(child)
            found.extend(
                SectionTabRailQmlTests._visual_children(child, object_name)
            )
        return found

    def _create_rail(self):
        engine = QQmlEngine()
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        model = SectionTabModel()
        model.replace([
            SectionTab(
                entry_key="assets", title="Assets", accent="#6f9fc1",
                current=True, glyph="assets",
            ),
            SectionTab(
                entry_key="shots", title="Shots", accent="#9f80c1",
                current=False, glyph="movie",
            ),
        ])
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(self.qml_dir / "SectionTabRail.qml")),
        )
        rail = component.createWithInitialProperties({
            "theme": theme,
            "model": model,
        })
        self.assertIsNotNone(
            rail,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(900, 520)
        rail.setParent(window.contentItem())
        rail.setParentItem(window.contentItem())
        rail.setHeight(520)
        window.show()
        QTest.mouseMove(window, QPoint(860, 490))
        QTest.qWait(450)
        return engine, theme, model, component, rail, window

    def test_hover_expands_only_the_pointed_tab(self):
        engine, theme, model, component, rail, window = self._create_rail()
        try:
            panel = rail.findChild(QObject, "sectionTabPanelBackground")
            tab_list = rail.findChild(QObject, "sectionTabList")
            tabs = self._visual_children(rail, "sectionTabDelegate")
            icons = self._visual_children(rail, "sectionTabIcon")
            surfaces = self._visual_children(rail, "sectionTabSurface")
            self.assertEqual(rail.property("reservedWidth"), 48.0)
            self.assertEqual(rail.property("width"), 320.0)
            self.assertEqual(tab_list.property("width"), 320.0)
            self.assertEqual(panel.property("width"), 48.0)
            self.assertEqual(panel.property("x"), 0.0)
            self.assertEqual(panel.property("y"), 0.0)
            self.assertEqual(panel.property("height"), 515.0)
            self.assertEqual(panel.property("radius"), 0.0)
            self.assertGreater(panel.property("bottomRightRadius"), 4.0)
            self.assertEqual(len(tabs), 2)
            self.assertEqual(len(surfaces), 2)
            self.assertEqual(
                {icon.property("name") for icon in icons},
                {"assets", "movie"},
            )
            QTest.mouseMove(window, QPoint(5, 70))
            QTest.qWait(60)

            self.assertGreater(tabs[1].property("width"), 48.0)
            self.assertLess(tabs[1].property("width"), 260.0)
            self.assertEqual(panel.property("width"), 48.0)
            self.assertEqual(panel.property("x"), 0.0)

            QTest.qWait(240)

            self.assertEqual(panel.property("width"), 48.0)
            self.assertEqual(panel.property("x"), 0.0)
            self.assertEqual(tabs[0].property("width"), 48.0)
            self.assertGreaterEqual(tabs[1].property("width"), 260.0)
            self.assertEqual(surfaces[0].property("width"), 40.0)
            self.assertGreaterEqual(surfaces[1].property("width"), 256.0)
        finally:
            window.close()
            window.deleteLater()
            del model, engine

    def test_current_switch_updates_roles_without_resetting_the_rail(self):
        model = SectionTabModel()
        model.replace([
            SectionTab("assets", "Assets", "#6f9fc1", True, "assets"),
            SectionTab("shots", "Shots", "#9f80c1", False, "movie"),
        ])
        resets = []
        changes = []
        model.modelReset.connect(lambda: resets.append(True))
        model.dataChanged.connect(
            lambda first, last, roles: changes.append((
                first.row(), last.row(), list(roles)
            ))
        )

        model.replace([
            SectionTab("assets", "Assets", "#6f9fc1", False, "assets"),
            SectionTab("shots", "Shots", "#9f80c1", True, "movie"),
        ])

        self.assertEqual(resets, [])
        self.assertEqual([change[:2] for change in changes], [(0, 0), (1, 1)])
        self.assertTrue(all(
            model.CurrentRole in change[2] for change in changes
        ))

    def test_collapsed_rail_does_not_block_workspace_actions(self):
        engine, theme, model, component, rail, window = self._create_rail()
        probe_component = QQmlComponent(engine)
        probe_component.setData(
            b'''import QtQuick
Item {
    id: root
    signal clicked()
    width: 900
    height: 520
    MouseArea {
        anchors.fill: parent
        onClicked: root.clicked()
    }
}
''',
            QUrl.fromLocalFile(str(self.qml_dir / "_RailUnderlayProbe.qml")),
        )
        probe = probe_component.create()
        self.assertIsNotNone(
            probe,
            "\n".join(error.toString() for error in probe_component.errors()),
        )
        probe.setParent(window.contentItem())
        probe.setParentItem(window.contentItem())
        probe.setZ(0)
        rail.setZ(30)
        meta = probe.metaObject()
        clicked_spy = QSignalSpy(
            probe, meta.method(meta.indexOfSignal("clicked()"))
        )
        try:
            QTest.mouseMove(window, QPoint(860, 490))
            QTest.qWait(450)
            QTest.mouseClick(
                window, Qt.LeftButton, Qt.NoModifier, QPoint(68, 70)
            )
            QTest.mouseClick(
                window, Qt.LeftButton, Qt.NoModifier, QPoint(110, 70)
            )
            QTest.qWait(30)
            self.assertEqual(clicked_spy.count(), 2)
        finally:
            window.close()
            window.deleteLater()
            probe.deleteLater()
            del model, engine

    def test_close_button_closes_without_selecting_the_tab(self):
        engine, theme, model, component, rail, window = self._create_rail()
        meta = rail.metaObject()
        selected_spy = QSignalSpy(
            rail, meta.method(meta.indexOfSignal("selected(QString)"))
        )
        closed_spy = QSignalSpy(
            rail, meta.method(meta.indexOfSignal("closed(QString)"))
        )
        try:
            QTest.mouseMove(window, QPoint(5, 70))
            QTest.qWait(300)
            buttons = self._visual_children(rail, "sectionTabCloseButton")
            self.assertEqual(len(buttons), 2)
            visible_buttons = [button for button in buttons
                               if button.property("visible")]
            self.assertEqual(len(visible_buttons), 1)
            button = visible_buttons[0]
            self.assertIsInstance(button, QQuickItem)
            scene_pos = button.mapToScene(
                QPointF(button.width() / 2, button.height() / 2)
            )
            QTest.mouseMove(
                window, QPoint(round(scene_pos.x()), round(scene_pos.y()))
            )
            QTest.qWait(60)
            self.assertTrue(button.property("pointerHovered"))
            self.assertTrue(button.property("visible"))
            QTest.mouseClick(
                window,
                Qt.LeftButton,
                Qt.NoModifier,
                QPoint(round(scene_pos.x()), round(scene_pos.y())),
            )
            QTest.qWait(40)

            self.assertEqual(closed_spy.count(), 1)
            self.assertIn(closed_spy.at(0), (["assets"], ["shots"]))
            self.assertEqual(selected_spy.count(), 0)
        finally:
            window.close()
            window.deleteLater()
            del model, engine


if __name__ == "__main__":
    unittest.main()
