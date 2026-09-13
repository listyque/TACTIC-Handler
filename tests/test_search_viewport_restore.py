"""Search viewport persistence through real QML teardown and lazy restoration."""

import os
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent

from thlib.environment import env_mode
from thlib.ui.controller import ApplicationController
from thlib.ui.controllers.types import SearchTabSession, SectionSession
from thlib.ui.workspace_models.results_types import WorkspaceNode
from tests.test_process_menu_latency import ProcessMenuLatencyTests, visual_items
from tests.test_result_tree_state import _loaded_tree
from tests.test_search_pagination_qml import SearchPaginationQmlTests


class SearchViewportRestoreTests(unittest.TestCase):
    scene = ProcessMenuLatencyTests.scene
    wait_frame = SearchPaginationQmlTests.wait_frame

    @classmethod
    def setUpClass(cls):
        ProcessMenuLatencyTests.setUpClass.__func__(cls)

    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        self.enterContext(patch.object(env_mode, "current_path", directory))
        self.rpc = self.enterContext(patch(
            "thlib.tactic_classes.execute_procedure_serverside",
            side_effect=AssertionError("Viewport state must not query TACTIC"),
        ))
        self.controllers = []
        self.addCleanup(self.shutdown_controllers)

    def shutdown_controllers(self):
        for controller in self.controllers:
            controller.shutdown()

    def controller_for(self, mode="continious", restored=False):
        controller = ApplicationController()
        self.controllers.append(controller)
        controller._current_project_code = "demo"
        section = SectionSession(
            entry_key="demo/asset", title="Assets", accent="#987654",
            search_type="demo/asset",
        )
        if restored:
            controller._restore_section_tabs(
                section, controller._load_search_cache("demo")[section.entry_key],
            )
        else:
            section.tabs = [SearchTabSession(
                tab_id="assets", title="Assets", loaded=True, view_mode=mode,
                loaded_page_offsets=[0, 25, 50], next_offset=80, total=80,
            )]
            section.current_tab_id = "assets"
        controller._sessions = {section.entry_key: section}
        controller._current_section_key = section.entry_key
        controller._sync_search_tabs()
        self.controller = controller
        return controller, controller._current_tab()

    @staticmethod
    def roots():
        roots = [WorkspaceNode(
            node_id=f"asset-{index}", node_type="sobject",
            search_key=f"demo/asset?code=ASSET{index:03d}",
            code=f"ASSET{index:03d}", title=f"Asset {index:03d}",
            preview_requested=True, card_preview_requested=True, loaded=True,
        ) for index in range(80)]
        branch = _loaded_tree()
        branch.preview_requested = True
        branch.card_preview_requested = True
        roots.insert(40, branch)
        return roots

    def results_view(self, view, name="searchResultsListView"):
        return next(item for item in visual_items(view) if item.objectName() == name)

    def test_hidden_view_captures_last_scroll_before_qml_is_destroyed(self):
        for mode in ("continious", "compact", "tiles"):
            with self.subTest(mode=mode):
                controller, tab = self.controller_for(mode)
                controller.workspace_model.replace_nodes(self.roots())
                tab.selected_node_id = "asset"
                with self.scene(animated=False) as (window, view):
                    name = (
                        "searchResultsGridView" if mode == "tiles"
                        else "searchResultsListView"
                    )
                    results = self.results_view(view, name)
                    position = results.mapToScene(QPointF(100, 100))
                    wheel = QWheelEvent(
                        position, QPointF(window.mapToGlobal(position.toPoint())),
                        QPoint(), QPoint(0, -1200), Qt.NoButton, Qt.NoModifier,
                        Qt.NoScrollPhase, False,
                    )
                    self.app.sendEvent(window, wheel)
                    self.wait_frame(window, lambda: results.property("contentY") > 100)
                    expected = results.property("contentY")
                    # Closing a window or hiding its dock precedes QML teardown.
                    window.contentItem().setVisible(False)
                    self.assertFalse(view.property("presentationActive"))
                    controller._capture_current_tree_state()
                    actual = tab.tile_content_y if mode == "tiles" else tab.list_content_y
                    self.assertAlmostEqual(actual, expected)
                # Shutdown still persists after the engine/views are gone.
                controller.shutdown()
                self.controllers.remove(controller)
                restored, saved_tab = self.controller_for(restored=True)
                self.assertEqual(saved_tab.loaded_page_offsets, [0, 25, 50])
                self.assertEqual(saved_tab.selected_node_id, "asset")
                actual = (
                    saved_tab.tile_content_y if mode == "tiles"
                    else saved_tab.list_content_y
                )
                self.assertAlmostEqual(actual, expected)
                saved_tab.loaded = True
                restored.workspace_model.replace_nodes(self.roots())
                with self.scene(animated=False) as (window, view):
                    restored._restore_result_viewport(saved_tab)
                    results = self.results_view(view, name)
                    self.wait_frame(window, lambda: abs(
                        results.property("contentY") - expected,
                    ) < 1)

    def test_autosave_during_tree_restore_does_not_overwrite_saved_viewport(self):
        controller, tab = self.controller_for()
        tab.list_content_y = 1900.5
        tab.list_content_y_valid = True
        tab.viewport_restore_pending = True
        controller.workspace_model.replace_nodes(self.roots())
        with self.scene(animated=False) as (window, view):
            self.assertEqual(view.property("activeResultSurface").property("listContentY"), 0)
            controller._write_search_cache()
            self.assertEqual(tab.list_content_y, 1900.5)
            cached = controller._search_cache["demo"]["sections"][0]["tabs"][0]
            self.assertEqual(cached["list_content_y"], 1900.5)
            controller._restore_viewport_if_tree_idle(tab.tab_id)
            results = self.results_view(view)
            self.wait_frame(window, lambda: results.property("contentY") == 1900.5)

    def test_restore_request_survives_initial_empty_layout(self):
        controller, tab = self.controller_for()
        tab.list_content_y = 900.5
        tab.list_content_y_valid = True
        with self.scene(animated=False) as (window, view):
            controller._restore_result_viewport(tab)
            controller._write_search_cache()
            self.assertEqual(tab.list_content_y, 900.5)
            controller.workspace_model.replace_nodes(self.roots())
            results = self.results_view(view)
            self.wait_frame(window, lambda: results.property("contentY") == 900.5)

    def test_view_created_after_cached_result_restores_its_position(self):
        controller, tab = self.controller_for()
        tab.list_content_y = 900.5
        tab.list_content_y_valid = True
        controller.workspace_model.replace_nodes(self.roots())
        controller._restore_result_viewport(tab)
        with self.scene(animated=False) as (window, view):
            results = self.results_view(view)
            self.wait_frame(window, lambda: results.property("contentY") == 900.5)


if __name__ == "__main__":
    unittest.main()
