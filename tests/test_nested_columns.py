"""The shared table's native columns retain their nested data context."""
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QObject

from tests import test_columns_table_view as columns
from thlib.ui.columns_editor import ColumnsEditorController
from thlib.ui.table.nested_columns import NestedColumnsController


STARTUP_PROBE = r'''
from thlib.ui import application
from thlib.ui.table.nested import NestedTableController

original_build = application.build_application_runtime

def build(*args, **kwargs):
    runtime = original_build(*args, **kwargs)
    try:
        class Context:
            def __init__(self):
                self.values = {}

            def setContextProperty(self, name, value):
                assert name not in self.values, name
                assert value is not None, name
                self.values[name] = value

        context = Context()
        runtime.publish_qml_bindings(context)
        assert context.values['appController'] is runtime.controller
        delivery, editors = runtime.bundles[3:5]
        assert context.values['columnsEditorController'] is delivery.columns_editor
        assert context.values['tableServicesController'] is editors.table_services
        assert context.values['tasksController'] is runtime.bundles[1].tasks
        scope = NestedTableController(editors.table_services, 'startup',
            dict(searchType='demo/asset', view='table'))
        try:
            columns = scope.tableColumns
            assert runtime.controller.columns_editor_controller is delivery.columns_editor
            assert columns._tasks_controller is delivery.columns_editor._tasks_controller
            assert columns._tasks_controller is runtime.bundles[1].tasks
        finally:
            scope.shutdown()
    except BaseException:
        runtime.shutdown()
        raise
    return runtime

application.build_application_runtime = build
assert application.main() == 0
print('NESTED_COLUMNS_STARTUP_OK', flush=True)
'''


class NestedColumnsTests(unittest.TestCase):
    def test_real_application_startup_publishes_nested_columns_owner(self):
        with TemporaryDirectory(prefix='handler-nested-columns-') as directory:
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen',
                QT_QUICK_BACKEND='software', TACTIC_QML_SMOKE_OFFLINE='1',
                TACTIC_QML_SMOKE_WINDOWS='0', TACTIC_QML_SMOKE_EXIT_MS='300',
                TACTIC_QML_TEST_SETTINGS_DIR=directory,
                APPDATA=directory, LOCALAPPDATA=directory)
            completed = subprocess.run([sys.executable, '-c', STARTUP_PROBE],
                cwd=Path(__file__).resolve().parents[1], env=environment,
                capture_output=True, text=True, timeout=35, check=False)
        diagnostic = completed.stdout + completed.stderr
        self.assertEqual(completed.returncode, 0, diagnostic)
        self.assertIn('NESTED_COLUMNS_STARTUP_OK', diagnostic)
        for warning in ('ReferenceError', 'Binding loop', 'TypeError:', 'Traceback'):
            self.assertNotIn(warning, diagnostic)

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
