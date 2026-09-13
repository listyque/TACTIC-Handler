"""Registry entries are not proof of physical TACTIC tables."""

import json
import os
from pathlib import Path
import sqlite3
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from thlib.ui.admin.search_types_api import search_types_request
from tests import test_administration_api as api_fixture
from tests import test_admin_search_types as ui_fixture
from tests.profile_ui_responsiveness import frame


class SearchTypeAvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.api = api_fixture.AdministrationApiTests()
        self.api.setUp()
        self.addCleanup(self.api.doCleanups)
        self.api.project_code = 'sthpw'
        self.api.tables['sthpw/search_object'].append(dict(
            code='sthpw/command', title='Commands', namespace='sthpw',
            database='sthpw', table_name='command'))
        self.database = sqlite3.connect(':memory:')
        self.addCleanup(self.database.close)
        self.database.execute('CREATE TABLE command_log (code TEXT)')
        self.sql = SimpleNamespace(table_exists=lambda table: bool(self.database.execute(
            "SELECT 1 FROM sqlite_master WHERE name = ? AND type IN ('table', 'view')", (table,)).fetchone()))

    def test_registered_missing_table_loads_readonly_without_probing_columns_or_rows(self):
        from pyasm.search import SearchType

        with patch.object(SearchType, 'get_sql_by_search_type', return_value=self.sql, create=True) as resource, \
                patch.object(SearchType, 'get_column_info', side_effect=AssertionError(
                    'A missing table must not reach SELECT LIMIT 0')):
            result = json.loads(search_types_request('load', 'sthpw', 'sthpw/command'))
        resource.assert_called_once_with('sthpw/command')
        self.assertEqual(result['identity'], 'sthpw/command')
        self.assertEqual(result['document']['title'], 'Commands')
        self.assertFalse(result['canWrite'])
        self.assertFalse(result['metadata']['tableAvailable'])
        self.assertEqual(result['metadata']['columns'], {})
        self.assertNotIn('total', result['metadata']['summary'])
        self.assertIn('sthpw/command', {row['identity'] for row in result['catalog']})
        self.assertEqual(self.api.calls, [])
        self.assertEqual(self.api.count_queries, [])

    def test_disappeared_table_blocks_save_before_introspection_or_writes(self):
        from pyasm.search import SearchType

        with patch.object(SearchType, 'get_sql_by_search_type', return_value=self.sql, create=True), \
                patch.object(SearchType, 'get_column_info', side_effect=AssertionError('Unsafe probe')), \
                patch.object(self.api.local_api, 'execute_cmd') as command:
            with self.assertRaisesRegex(ValueError, 'command.*absent'):
                search_types_request('save', 'sthpw', 'sthpw/command',
                                     document={'title': 'Commands', 'removedColumns': ['notes']})
        command.assert_not_called()
        self.assertEqual(self.api.calls, [])

    def test_real_system_table_is_not_hidden_or_blocked_by_its_name(self):
        from pyasm.search import SearchType

        self.database.execute('CREATE TABLE command (code TEXT)')
        self.api.tables['sthpw/command'] = [{'code': 'C1'}]
        self.api.columns['sthpw/command'] = {'code': {'data_type': 'text'}}
        with patch.object(SearchType, 'get_sql_by_search_type', return_value=self.sql, create=True):
            result = json.loads(search_types_request('load', 'sthpw', 'sthpw/command'))
        self.assertTrue(result['canWrite'])
        self.assertTrue(result['metadata']['tableAvailable'])
        self.assertEqual(result['metadata']['summary']['total'], 1)

    def test_database_catalog_failure_stays_an_error(self):
        from pyasm.search import SearchType

        with patch.object(SearchType, 'get_sql_by_search_type', side_effect=RuntimeError(
                'Database connection failed'), create=True):
            with self.assertRaisesRegex(RuntimeError, 'connection failed'):
                search_types_request('load', 'sthpw', 'sthpw/command')

    def test_listing_keeps_registry_entries_without_individual_column_probes(self):
        from pyasm.search import SearchType

        with patch.object(SearchType, 'get_column_info', side_effect=AssertionError('Unneeded column query')), \
                patch.object(SearchType, 'get_sql_by_search_type', side_effect=AssertionError('Unneeded probe')):
            result = json.loads(search_types_request('list', 'sthpw'))
        self.assertIn('sthpw/command', {row['identity'] for row in result['catalog']})

    def test_existing_database_view_is_available(self):
        from pyasm.search import SearchType

        self.database.execute('CREATE VIEW command AS SELECT code FROM command_log')
        self.api.tables['sthpw/command'] = []
        self.api.columns['sthpw/command'] = {'code': {'data_type': 'text'}}
        with patch.object(SearchType, 'get_sql_by_search_type', return_value=self.sql):
            result = json.loads(search_types_request('load', 'sthpw', 'sthpw/command'))
        self.assertTrue(result['metadata']['tableAvailable'])
        self.assertEqual(result['metadata']['summary']['total'], 0)


class SearchTypeAvailabilityQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ui_fixture.AdminSearchTypeEditorTests.setUpClass()

    def setUp(self):
        self.api = api_fixture.AdministrationApiTests()
        self.api.setUp()
        self.addCleanup(self.api.doCleanups)
        self.api.project_code = 'sthpw'
        self.api.tables['sthpw/search_object'].append(dict(
            code='sthpw/command', title='Commands', namespace='sthpw', database='sthpw', table_name='command'))
        self.ui = ui_fixture.AdminSearchTypeEditorTests()
        self.ui.setUp()
        self.addCleanup(self.ui.doCleanups)
        self.editor = self.ui.editor
        self.editor._project = 'sthpw'
        self.editor._catalog = json.loads(search_types_request('list', 'sthpw'))['catalog']
        self.editor.stateChanged.emit()
        self.workers = []

        def task(operation):
            worker = self.ui.worker(operation)
            self.workers.append(worker)
            return worker

        from thlib.environment import env_inst

        self.enterContext(patch.object(env_inst.server_pool, 'add_task', side_effect=task))
        self.rpc = self.enterContext(patch('thlib.tactic_classes.execute_procedure_serverside',
            side_effect=lambda endpoint, arguments, **kwargs: json.loads(endpoint(**arguments))))

    def test_selecting_registry_only_type_explains_state_and_recovers_on_next_selection(self):
        from PySide6.QtCore import QPointF

        self.ui.click('adminSearchType_sthpw/command')
        frame(self.ui.window)
        self.assertEqual(self.editor.identity, 'sthpw/command')
        self.assertFalse(self.editor.busy)
        self.assertEqual(self.editor.error, '')
        self.assertFalse(self.ui.item('adminSaveDocument').isEnabled())
        self.assertEqual(self.ui.item('adminSearchTypeCount_total').property('text'), '—')
        for width, height in ((900, 620), (1400, 940)):
            with self.subTest(width=width):
                self.ui.window.resize(width, height)
                frame(self.ui.window)
                notice = self.ui.reveal('adminSearchTypeMissingTable')
                viewport = self.ui.item('adminSearchTypeForm')
                self.assertIn('sthpw.command', notice.property('text'))
                self.assertIn('отсутствует', notice.property('text'))
                self.assertGreaterEqual(notice.mapToItem(viewport, QPointF()).x(), 0)
                self.assertLessEqual(notice.mapToItem(viewport, QPointF(notice.width(), 0)).x(),
                                     viewport.width() - 16)
                self.assertGreater(notice.height(), 0)
                output = os.environ.get('SEARCH_TYPE_SCREENSHOTS')
                if output:
                    Path(output).mkdir(parents=True, exist_ok=True)
                    self.ui.window.grabWindow().save(str(Path(output) / ('missing_table_%s.png' % width)))
        self.ui.click('segmentedButtonSegment_entity_details')
        self.assertFalse(self.ui.item('adminSearchTypeTitle').isEnabled())
        self.editor.set_field('title', 'Changed')
        self.assertEqual(self.editor.document['title'], 'Commands')
        self.ui.click('adminSearchType_demo/asset')
        frame(self.ui.window)
        self.assertTrue(self.editor.canWrite)
        self.assertTrue(self.ui.item('adminSearchTypeTitle').isEnabled())
        self.assertEqual(self.editor.error, '')
        self.assertTrue(self.editor.metadata['tableAvailable'])
        with self.assertRaises(StopIteration):
            self.ui.item('adminSearchTypeMissingTable')
        self.assertEqual(self.rpc.call_count, 2)
        self.assertEqual(self.api.calls, [])
        self.assertEqual(self.ui.ui.fixture.warnings, [])
