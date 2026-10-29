"""Definition refresh must not blank cells before the row response arrives."""
from copy import deepcopy
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tests.test_columns_table_view import _Application, _SType, _Pool, _layout_payload
from tests.qt_application import gui_test_application
from thlib.ui.columns_editor import ColumnsEditorController


class TableRefreshPresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def test_definition_refresh_retains_cells_until_row_response(self):
        from thlib.environment import env_inst
        application = _Application(_SType())
        payload = _layout_payload()
        key = next(iter(payload['rows']))
        application.tab.sobjects = [SimpleNamespace(get_search_key=lambda: key)]
        controller = ColumnsEditorController(application)
        with patch('thlib.tactic_classes.get_table_layout', return_value=payload), \
                patch.object(env_inst, 'server_pool', _Pool()):
            controller.reload()
        key = next(iter(controller._cells))
        original = deepcopy(controller.row_cells(key))
        published = []
        controller.cellRevisionChanged.connect(lambda: published.append(controller.row_cells(key)))
        definition = dict(payload, rows={})
        with patch('thlib.tactic_classes.get_table_layout', return_value=definition), \
                patch.object(env_inst, 'server_pool', _Pool()), \
                patch.object(controller, '_sync_table_rows') as sync:
            controller.reload()
        self.assertEqual(published, [original])
        self.assertIn(key, controller._changed_row_keys)
        sync.assert_called_once()
        refreshed = deepcopy(payload)
        refreshed['rows'][key]['custom']['text'] = 'Pine'
        controller._table_rows_loaded(controller._row_request_id, refreshed)
        self.assertEqual(controller.row_cells(key)['custom']['text'], 'Pine')
        controller._table_rows_loaded(controller._row_request_id - 1, payload)
        self.assertEqual(controller.row_cells(key)['custom']['text'], 'Pine')

        # A different project must never borrow this project's presentation.
        application._current_project_code = 'other'
        with patch('thlib.tactic_classes.get_table_layout', return_value=definition), \
                patch.object(env_inst, 'server_pool', _Pool()), \
                patch.object(controller, '_sync_table_rows'):
            controller.reload()
        self.assertEqual(controller.row_cells(key), {})

        controller._loading_context = ('demo', application.stype.get_code(), 'table')
        controller._loaded((application.stype, payload))
        self.assertEqual(controller.row_cells(key), {})
        self.assertTrue(controller._reload_pending)
