"""First table activation must bootstrap columns without a previous layout."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('QSG_RENDER_LOOP', 'basic')
from PySide6.QtCore import QPointF
from tests import test_columns_table_view as fixture
from tests import test_frame_table as native
from tests.profile_ui_responsiveness import frame
from tests.qt_application import gui_test_application
from thlib.environment import env_inst
from thlib.ui.columns_editor import ColumnsEditorController
from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.results_types import WorkspaceNode


class FirstTableOpenTests(unittest.TestCase):
    create = native.FrameTableTests.create
    close = native.FrameTableTests.close
    item = native.FrameTableTests.item

    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        self.application = fixture._Application(fixture._SType())
        self.tab = self.application.tab
        self.application.tab = None
        self.application.dock_model.is_panel_presented = lambda panel: panel == 'results'
        self.controller = ColumnsEditorController(self.application)
        self.addCleanup(self.controller.shutdown)
        self.pool = fixture._Pool()
        self.enterContext(patch.object(env_inst, 'server_pool', self.pool))
        self.read = self.enterContext(patch(
            'thlib.tactic_classes.get_table_layout',
            return_value=fixture._layout_payload(),
        ))

    def test_first_activation_loads_definition_when_initial_session_has_no_tab(self):
        self.controller.begin_session()
        self.read.assert_not_called()
        self.assertEqual(self.controller.visibleColumns, [])
        self.application.tab = self.tab
        self.application.results_view_changed.emit()
        self.read.assert_called_once()
        self.assertEqual(
            [column['name'] for column in self.controller.visibleColumns],
            ['code', 'custom'],
        )
        self.assertFalse(self.controller.busy)
        self.assertEqual(self.controller.error, '')

    def test_first_definition_arrives_in_the_already_visible_native_table(self):
        model = WorkspaceItemModel()
        model.replace_nodes([WorkspaceNode(
            node_id='asset', node_type='sobject',
            search_key='demo/asset?code=ASSET001', code='ASSET001', title='Oak',
        )])
        window, table = self.create(
            'SearchResultTable.qml',
            dict(controller=fixture._TableController(), resultModel=model,
                 columnsController=self.controller, presentationActive=True),
            width=900, height=400,
        )
        self.assertTrue(self.item(table, 'tableColumnsEmptyState').isVisible())
        self.read.assert_not_called()
        self.application.tab = self.tab
        self.application.results_view_changed.emit()
        frame(window)
        self.read.assert_called_once()
        self.assertFalse(self.item(table, 'tableColumnsEmptyState').isVisible())
        header = self.item(table, 'tableColumnHeaderLabel_code')
        self.assertTrue(header.isVisible())
        self.assertEqual(header.property('text'), 'CODE')
        self.assertGreater(header.mapToItem(table, QPointF()).x(), 0)
        self.assertEqual(
            self.controller.row_cells('demo/asset?code=ASSET001')['custom']['text'],
            'Oak',
        )

    def test_first_activation_reuses_the_same_inflight_definition(self):
        self.controller.begin_session()
        self.application.tab = self.tab
        with (
            patch.object(self.pool, 'add_task', wraps=self.pool.add_task) as add,
            patch.object(fixture._Worker, 'start'),
        ):
            self.application.results_view_changed.emit()
            self.application.results_view_changed.emit()
            add.assert_called_once()
            self.assertTrue(self.controller.busy)
            self.assertFalse(self.controller._reload_pending)
            worker = next(iter(self.controller._workers))
        fixture._Worker.start(worker)
        self.read.assert_called_once()
        self.assertFalse(self.controller.busy)
        self.assertEqual(len(self.controller.visibleColumns), 2)

    def test_non_table_activation_does_not_bootstrap_a_table(self):
        self.tab.view_mode = 'tiles'
        self.application.tab = self.tab
        self.application.results_view_changed.emit()
        self.read.assert_not_called()

    def test_unpresented_workspace_does_not_bootstrap_from_admin_signals(self):
        self.application.tab = self.tab
        self.application.dock_model.is_panel_presented = lambda _panel: False
        self.application.results_view_changed.emit()
        self.read.assert_not_called()


if __name__ == '__main__':
    unittest.main()
