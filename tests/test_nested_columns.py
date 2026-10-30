"""The shared table's native columns retain their nested data context."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QObject

from tests import test_columns_table_view as columns
from thlib.ui.columns_editor import ColumnsEditorController
from thlib.ui.table.nested_columns import NestedColumnsController


class NestedColumnsTests(unittest.TestCase):
    def test_projection_and_commands_keep_the_child_project_and_view(self):
        stype = columns._SType()
        app = columns._Application(stype)
        app.columns_editor_controller = ColumnsEditorController(app)
        scope = QObject()
        scope.application = app
        scope.descriptor = dict(searchType='demo/asset', projectCode='child', view='table')
        scope._model = dict(loaded=True, busy=False, rows=[dict(nodeId='B')])
        scope._nodes = {'B': SimpleNamespace(source=SimpleNamespace(get_search_key=lambda: 'demo/asset?code=B'))}
        scope.reload = Mock()
        scope.activate = Mock()
        scope.set_result_group_mode = Mock()
        scope._open_columns = Mock()
        owner = NestedColumnsController(scope)
        self.addCleanup(owner.shutdown)
        self.addCleanup(app.columns_editor_controller.shutdown)
        owner.accept(stype, columns._layout_payload())
        self.assertEqual([column['name'] for column in owner.visibleColumns], ['code', 'custom'])
        self.assertEqual(owner.row_cells('demo/asset?code=ASSET001')['custom']['text'], 'Oak')
        owner.sort_column(0, True)
        scope.activate.assert_called_once_with(dict(type='sort', value='code', direction='desc'))
        owner.request_column_focus(1, 'definition')
        scope._open_columns.assert_called_once_with('custom')
        owner.set_width(0, 128)
        with patch.object(owner, '_run', return_value=True) as run:
            self.assertTrue(owner.apply())
            with patch('thlib.tactic_classes.save_widget_config') as save:
                run.call_args.args[0]()
                self.assertEqual(save.call_args.kwargs['project_code'], 'child')
        owner._dirty = False
        owner._table_views = [dict(view='table'), dict(view='child')]
        self.assertTrue(owner.select_table_view(1))
        scope.reload.assert_called_once_with()
        self.assertEqual(scope.descriptor['view'], 'child')
        self.assertEqual(app.tab.table_view, 'table')
        self.assertEqual(app._current_project_code, 'demo')

    def test_prepared_cells_are_completed_without_a_second_mapping(self):
        stype = columns._SType()
        app = columns._Application(stype)
        app.columns_editor_controller = ColumnsEditorController(app)
        scope = QObject()
        scope.application = app
        scope.descriptor = dict(projectCode='demo', view='table')
        scope._model = dict(rows=[], loaded=True, busy=False)
        scope._nodes = {}
        owner = NestedColumnsController(scope)
        self.addCleanup(owner.shutdown)
        self.addCleanup(app.columns_editor_controller.shutdown)
        cells = {'A': {'code': {'text': 'Already prepared'}}}
        with patch.object(owner, '_map_rows', side_effect=AssertionError('Cells must be mapped once')):
            owner.accept(stype, columns._layout_payload(), cells)
        self.assertIs(owner._cells['A'], cells['A'])
        self.assertEqual(owner.row_cells('A')['code']['text'], 'Already prepared')
