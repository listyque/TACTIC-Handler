"""Real search header input and the existing quick-filter selection owner."""
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
import tests.test_process_menu_latency as fixture
from tests.test_quick_filters import _Stype
from thlib.ui.quick_filter_editor import QuickFilterEditorController
from thlib.ui.localization import CatalogTranslator


class SearchInlineFilterTests(unittest.TestCase):
    setUpClass = classmethod(fixture.ProcessMenuLatencyTests.setUpClass.__func__)
    setUp = fixture.ProcessMenuLatencyTests.setUp
    scene = fixture.ProcessMenuLatencyTests.scene

    def click(self, window, item):
        point = item.mapToScene(QPointF(item.width()/2, item.height()/2)).toPoint()
        QTest.mouseClick(item.window(), Qt.LeftButton, Qt.NoModifier, point)
        fixture.frame(window)

    def test_scoped_groups_use_existing_selection_and_resize_fallback(self):
        controller = self.controller
        tab = controller._current_tab()
        tab.search_text = 'hero'
        tab.stype = _Stype()
        tab.quick_filter_tasks = {"any": [{"status": "Review", "process": "model", "assigned": "artist"}]}
        tab.quick_filter_layout = [{"key": key} for key in ("status", "assigned", "column:category")]
        tab.quick_filter_layout.append({"key": "process", "enabled": False})
        controller.workspace_model.replace_nodes([])
        facets = [{"key": "column:category", "title": "Category", "source": "column", "accent": "#607d8b", "options": [{"key": "Props", "title": "Props"}]}]
        self.enterContext(patch.object(controller, "_active_quick_filter_facets", return_value=facets))
        self.enterContext(patch.object(controller, "_request_quick_filter_catalog"))
        self.enterContext(patch.object(controller, "_request_quick_filter_tasks"))
        loader = self.enterContext(patch.object(controller, "_load_tab"))
        self.enterContext(patch.object(QuickFilterEditorController, "_run"))
        shelf = QObject()
        with self.scene(width=1460, animated=False, shelf=shelf) as (window, view):
            popup = view.findChild(QObject, "searchQuickFilterPopup")
            editor = popup.property("editorController")
            key = editor._key(editor._context(include_groups=False))
            editor._context_key = key
            editor._loaded[key] = {"groups": [], "defaultSelections": {}}
            status = fixture.visual_control(view, "searchQuickGroup_status")
            self.assertIsNotNone(status)
            self.assertTrue(status.isVisible())
            self.assertEqual(status.property('background').property('cornerRadius'), view.property('theme').property('fieldRadius'))
            self.assertEqual(fixture.visual_control(status, 'searchQuickGroup_statusIcon').property('name'), 'status')
            self.assertIsNone(fixture.visual_control(view, "searchQuickGroup_process"))
            self.click(window, status)
            self.assertTrue(popup.property("opened"))
            self.assertEqual(popup.property("groupKey"), "status")
            groups = popup.property("groups").toVariant()
            self.assertEqual([group["key"] for group in groups], ["status"])
            # Actual chip activation, not direct controller invocation.
            target = next(item for item in fixture.visual_items(popup.property("contentItem"))
                if item.property("text") == "Review" and item.property("maximumChipWidth") is not None and item.isVisible())
            self.click(window, target)
            self.assertIn("Review", tab.quick_filters["status"])
            loader.assert_called()
            self.assertEqual(status.property("text"), "Status · 1")
            assigned = fixture.visual_control(view, "searchQuickGroup_assigned")
            self.click(window, assigned)
            self.assertTrue(popup.property("opened"))
            self.assertEqual(popup.property("groupKey"), "assigned")
            self.assertEqual([group["key"] for group in popup.property("groups").toVariant()], ["assigned"])
            mine = next(item for item in fixture.visual_items(popup.property("contentItem"))
                if item.property("text") == "MY TASKS" and item.property("maximumChipWidth") is not None and item.isVisible())
            self.click(window, mine)
            self.assertIn('__current_login__', tab.quick_filters['assigned'])
            QTest.keyClick(window, Qt.Key_Escape)
            fixture.frame(window)
            self.assertFalse(popup.property("opened"))
            # Full menu remains available with every enabled group.
            full = fixture.visual_control(view, "searchQuickFilterButton")
            cursor = full.findChild(QObject, "compactIconButtonCursorArea")
            cursor.setProperty("lastActivationAt", -1000.0)
            self.click(window, full)
            self.assertEqual(len(popup.property("groups").toVariant()), 3)
            QTest.keyClick(window, Qt.Key_Escape)
            tab.loading = True
            controller.search_state_changed.emit()
            fixture.frame(window)
            self.assertFalse(status.isEnabled())
            tab.loading = False
            controller.search_state_changed.emit()
            fixture.frame(window)
            status.forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Space)
            fixture.frame(window)
            self.assertTrue(popup.property("opened"))
            window.resize(900, 650)
            view.setWidth(900)
            fixture.frame(window)
            self.assertFalse(popup.property("opened"))
            self.assertIsNone(fixture.visual_control(view, "searchQuickGroup_status"))
            window.resize(1460, 650)
            view.setWidth(1460)
            fixture.frame(window)
            self.assertIn("Review", tab.quick_filters["status"])
            output = os.environ.get("SEARCH_INLINE_OUTPUT")
            if output:
                Path(output).mkdir(parents=True, exist_ok=True)
                for dark in (True, False):
                    view.property("theme").setProperty("dark", dark)
                    fixture.frame(window)
                    window.grabWindow().copy(0, 0, 1460, 48).save(str(Path(output)/("native-en-" + ("dark" if dark else "light") + ".png")))

    def test_russian_labels_fit_without_clipping(self):
        translator = CatalogTranslator(fixture.QML.parent / 'translations/ru.json')
        self.app.installTranslator(translator)
        self.addCleanup(self.app.removeTranslator, translator)
        tab = self.controller._current_tab()
        tab.search_text = 'hero'
        tab.quick_filters = {'status': {'Review'}, 'assigned': {'artist'}}
        tab.quick_filter_layout = [{'key': key} for key in ('status', 'assigned', 'column:category')]
        tab.quick_filter_layout.append({'key': 'process', 'enabled': False})
        facets = [{'key': 'column:category', 'title': 'Category', 'source': 'column', 'accent': '#607d8b', 'options': [{'key': 'Props', 'title': 'Props'}]}]
        self.enterContext(patch.object(self.controller, '_active_quick_filter_facets', return_value=facets))
        self.controller.workspace_model.replace_nodes([])
        self.enterContext(patch.object(QuickFilterEditorController, '_run'))
        shelf = QObject()
        with self.scene(width=1460, animated=False, shelf=shelf) as (window, view):
            for key in ('status', 'assigned'):
                item = fixture.visual_control(view, 'searchQuickGroup_' + key)
                self.assertIsNotNone(item)
                label = next(child for child in fixture.visual_items(item) if child.isVisible() and child.property('lineCount') is not None and child.property('text') == item.property('text'))
                self.assertLessEqual(label.implicitWidth(), label.width())
                self.assertEqual(label.property('font').weight(), 400)
            output = os.environ.get('SEARCH_INLINE_OUTPUT')
            if output:
                Path(output).mkdir(parents=True, exist_ok=True)
                for dark in (True, False):
                    view.property('theme').setProperty('dark', dark)
                    fixture.frame(window)
                    window.grabWindow().copy(0, 0, 1460, 48).save(str(Path(output)/('native-ru-' + ('dark' if dark else 'light') + '.png')))


if __name__ == "__main__":
    unittest.main()
