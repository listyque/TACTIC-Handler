from __future__ import annotations

import os
from pathlib import Path
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QPointF, Property, QUrl, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from thlib.ui.localization import CatalogTranslator
from thlib.ui.matching_templates import MatchingTemplatesController


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib" / "ui" / "qml"


class _CheckinOutController(QObject):
    @Property("QVariantList", constant=True)
    def processes(self):
        return ["publish", "render"]

    @Property("QVariantList", constant=True)
    def contexts(self):
        return ["review", "final"]


class _WindowModel(QObject):
    @Slot(str)
    def close_window(self, _window_id):
        pass


class MatchingTemplatesLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_narrow_and_wide_content_stays_inside_split_panels(self):
        translator = CatalogTranslator(
            QML.parent / "translations" / "ru.json"
        )
        self.app.installTranslator(translator)
        with (
            patch(
                "thlib.ui.matching_templates.env_read_config",
                return_value={},
            ),
            patch("thlib.ui.matching_templates.env_write_config"),
        ):
            controller = MatchingTemplatesController()

        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        checkin_controller = _CheckinOutController(engine)
        window_model = _WindowModel(engine)
        engine.rootContext().setContextProperty(
            "matchingTemplatesController", controller
        )
        engine.rootContext().setContextProperty(
            "matchingTemplatesModel", controller.model
        )
        engine.rootContext().setContextProperty(
            "checkinOutController", checkin_controller
        )
        engine.rootContext().setContextProperty("windowModel", window_model)

        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(QML / "MatchingTemplatesView.qml")),
        )
        view = component.createWithInitialProperties({
            "theme": theme,
            "windowId": "matching_templates",
        })
        self.assertIsNotNone(
            view,
            "\n".join(error.toString() for error in component.errors()),
        )

        window = QQuickWindow()
        view.setParentItem(window.contentItem())
        window.show()
        try:
            for width, height in ((640, 500), (800, 640), (1000, 700)):
                window.resize(width, height)
                view.setWidth(width)
                view.setHeight(height)
                QTest.qWait(30)
                self._assert_layout_is_contained(view, width)
        finally:
            window.close()
            view.deleteLater()
            theme.deleteLater()
            self.app.removeTranslator(translator)

    def _assert_layout_is_contained(self, view, width):
        list_panel = view.findChild(QObject, "matchingTemplatesListPanel")
        editor = view.findChild(QObject, "matchingTemplatesEditorPanel")
        toolbar = view.findChild(QObject, "matchingTemplatesToolbar")
        template_list = view.findChild(QObject, "matchingTemplatesList")
        editor_layout = view.findChild(
            QObject, "matchingTemplatesEditorLayout"
        )
        mapping_grid = view.findChild(
            QObject, "matchingTemplatesMappingGrid"
        )
        overflow = view.findChild(
            QObject, "matchingTemplatesOverflowButton"
        )
        for item in (
            list_panel,
            editor,
            toolbar,
            template_list,
            editor_layout,
            mapping_grid,
            overflow,
        ):
            self.assertIsNotNone(item)

        panel_right = self._right_in(list_panel, view)
        editor_left = editor.mapToItem(view, QPointF()).x()
        self.assertLessEqual(panel_right, editor_left + 0.1)
        self._assert_inside(toolbar, list_panel)
        self._assert_inside(template_list, list_panel)
        self._assert_inside(editor_layout, editor)
        self._assert_inside(mapping_grid, editor)

        delegate = self._visual_child(
            template_list, "matchingTemplateDelegate"
        )
        self.assertIsNotNone(delegate)
        self._assert_inside(delegate, template_list)
        self.assertLessEqual(
            delegate.width(), template_list.property("width") - 9.5
        )

        compact_editor = bool(editor.property("compactFields"))
        self.assertEqual(
            mapping_grid.property("columns"),
            1 if compact_editor else 2,
        )
        self.assertEqual(bool(overflow.property("visible")), width < 1000)

    def _assert_inside(self, item, parent):
        position = item.mapToItem(parent, QPointF())
        self.assertGreaterEqual(position.x(), -0.1, item.objectName())
        self.assertGreaterEqual(position.y(), -0.1, item.objectName())
        self.assertLessEqual(
            position.x() + item.width(),
            parent.property("width") + 0.1,
            item.objectName(),
        )
        self.assertLessEqual(
            position.y() + item.height(),
            parent.property("height") + 0.1,
            item.objectName(),
        )

    @staticmethod
    def _right_in(item, parent):
        position = item.mapToItem(parent, QPointF())
        return position.x() + item.width()

    @classmethod
    def _visual_child(cls, item, object_name):
        if not isinstance(item, QQuickItem):
            return None
        for child in item.childItems():
            if child.objectName() == object_name:
                return child
            found = cls._visual_child(child, object_name)
            if found is not None:
                return found
        return None


if __name__ == "__main__":
    unittest.main()
