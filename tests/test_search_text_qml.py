"""Main Search Enter populates the actual Advanced Search filter cards."""

from copy import deepcopy
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QEvent, QObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, qmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from tests import test_process_menu_latency as menus
from tests.profile_ui_responsiveness import frame
from thlib.ui.filter_editor import FilterEditorController
from thlib.ui.search_suggestion_data import search_suggestion_spec


class SearchTextQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        menus.ProcessMenuLatencyTests.setUpClass()

    def test_enter_uses_suggestion_fields_in_actual_advanced_search_cards(self):
        workspace = menus.ProcessMenuLatencyTests()
        workspace.setUp()
        self.addCleanup(workspace.doCleanups)
        controller = workspace.controller
        stype = SimpleNamespace(
            get_code=lambda: "demo/asset",
            get_columns_info=lambda: {key: {} for key in ("title", "code", "keywords", "description")},
            get_column_data_type=lambda column: "text",
        )
        self.enterContext(patch.object(controller, "_active_stype", return_value=stype))
        requested = []
        self.enterContext(patch.object(
            controller, "_load_tab",
            side_effect=lambda tab, **kwargs: requested.append(deepcopy(tab.extra_filters)),
        ))
        state = controller.workspace_state
        state.filter_column_model.replace([
            {"value": column, "label": column}
            for column in ("title", "code", "keywords", "description")
        ])
        with workspace.scene(animated=False) as (window, view):
            search_input = view.findChild(QQuickItem, "tacticSearchInput")
            self.assertIsNotNone(search_input)
            search_input.forceActiveFocus()
            for character in "needle":
                QTest.keyClick(window, character)
            QTest.keyClick(window, Qt.Key_Return)
            frame(window)
            _title, _columns, suggestion_query = search_suggestion_spec(stype, "needle")
            self.assertEqual(
                [item for item in requested[-1] if isinstance(item, tuple)],
                [item for item in suggestion_query if isinstance(item, tuple)],
            )
            self.assertEqual(
                [row["operator"] for row in state.filter_model._records],
                ["begin", "or", "or"],
            )

            engine = qmlEngine(view)
            filter_editor = FilterEditorController(
                lambda: state.filter_model._records,
                lambda: state.filter_column_model._records,
                controller.search_filter_relations,
                lambda message: self.fail(message),
            )
            for name, value in {
                "filterModel": state.filter_model,
                "filterColumnModel": state.filter_column_model,
                "advancedFilterSuggestionModel": state.advanced_filter_suggestion_model,
                "filterEditorController": filter_editor,
                "filterPresetModel": filter_editor.presets,
            }.items():
                engine.rootContext().setContextProperty(name, value)
            component = QQmlComponent(engine, QUrl.fromLocalFile(str(menus.QML / "AdvancedSearchView.qml")))
            advanced = component.createWithInitialProperties({"theme": view.property("theme")})
            self.assertIsNotNone(advanced, [error.toString() for error in component.errors()])
            try:
                advanced.setParentItem(window.contentItem())
                advanced.setWidth(700)
                advanced.setHeight(600)
                frame(window)
                cards = [item for item in menus.visual_items(advanced)
                         if item.property("isDefault") is not None
                         and item.property("column") is not None]
                self.assertEqual([item.property("column") for item in cards], ["title", "keywords", "description"])
                self.assertEqual([item.property("value") for item in cards], ["needle"] * 3)
            finally:
                advanced.setParentItem(None)
                advanced.deleteLater()
                QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


if __name__ == "__main__":
    unittest.main()
