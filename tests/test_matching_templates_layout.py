from __future__ import annotations

import os
from pathlib import Path
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QPointF, Property, Qt, QUrl, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from thlib.ui.localization import CatalogTranslator
from thlib.ui.matching_templates import MatchingTemplatesController
from tests.profile_ui_responsiveness import frame


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
        translator = CatalogTranslator(QML.parent / "translations" / "ru.json")
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
        warnings = []
        engine.warnings.connect(lambda errors: warnings.extend(str(error) for error in errors))
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
        view = component.createWithInitialProperties(
            {
                "theme": theme,
                "windowId": "matching_templates",
            }
        )
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
                frame(window)
                self._assert_layout_is_contained(view, width)
            controller.select_row(2)
            frame(window)
            process = self._visual_child(view, "matching_process")
            self.assertTrue(process.isEnabled())
            point = process.mapToScene(QPointF(20, process.height() / 2)).toPoint()
            QTest.mouseClick(window, Qt.LeftButton, pos=point)
            QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
            for char in "custom":
                QTest.keyClick(window, Qt.Key(ord(char.upper())))
            frame(window)
            self.assertEqual(controller.selectedTemplate["process"], "custom")
            checkbox = self._visual_child(
                view, "matchingEnabled_" + controller.selectedTemplate["templateId"]
            )
            self.assertTrue(checkbox.isEnabled())
            point = checkbox.mapToScene(QPointF(18, checkbox.height() / 2)).toPoint()
            QTest.mouseClick(window, Qt.LeftButton, pos=point)
            frame(window)
            self.assertFalse(controller.selectedTemplate["templateEnabled"])
            selected_id = controller.selectedTemplate["templateId"]
            row = self._visual_child(view, "matchingTemplateSelect_" + selected_id)
            row.forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Down)
            frame(window)
            self.assertEqual(controller.selectedRow, 3)
            QTest.keyClick(window, Qt.Key_End)
            frame(window)
            self.assertEqual(controller.selectedRow, controller.model.count() - 1)
            frame(window)
            self.assertEqual(window.activeFocusItem().objectName(), "matchingTemplateSelect_" + controller.selectedTemplate["templateId"])
            self.assertGreater(self._visual_child(view, "matchingTemplatesList").property("contentY"), 0)


            self.assertEqual(warnings, [])
        finally:
            window.close()
            view.deleteLater()
            theme.deleteLater()
            self.app.removeTranslator(translator)

    def _assert_layout_is_contained(self, view, width):
        list_panel = self._visual_child(view, "matchingTemplatesListPanel")
        editor = self._visual_child(view, "matchingTemplatesEditorPanel")
        template_list = self._visual_child(view, "matchingTemplatesList")
        scroll = self._visual_child(view, "matchingTemplatesEditorScroll")
        for item in (list_panel, editor, template_list, scroll):
            self.assertIsNotNone(item)
        self.assertLessEqual(
            self._right_in(list_panel, view), editor.mapToItem(view, QPointF()).x()
        )
        self.assertLessEqual(self._right_in(editor, view), width)
        self._assert_inside(template_list, list_panel)
        self._assert_inside(scroll, editor)
        for name in ("matchingTemplatesSave", "matchingTemplatesCancel"):
            self._assert_inside(self._visual_child(view, name), editor)
        delegate = self._visual_child(template_list, "matchingTemplateDelegate")
        self.assertIsNotNone(delegate)
        self._assert_inside(delegate, template_list)
        self.assertLessEqual(delegate.width(), template_list.width() - 12)
        for name in (
            "matchingPattern",
            "matching_process",
            "matching_context",
            "matchingExample",
        ):
            field = self._visual_child(view, name)
            self.assertIsNotNone(field)
            point = field.mapToItem(editor, QPointF())
            self.assertGreaterEqual(point.x(), 0, name)
            self.assertLessEqual(point.x() + field.width(), editor.width() - 14, name)
        overflow = self._visual_child(view, "matchingTemplatesOverflowButton")
        self.assertEqual(overflow is not None, width < 1000)

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
