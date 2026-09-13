"""Schema relationship drafts and native save boundaries (no live server)."""

import copy
import json
import sqlite3
import tempfile
import textwrap
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

from thlib import tactic_classes as tc
from thlib.ui.admin.graph_editor import GraphEditor
from thlib.ui.admin.schema_api import schema_request
from thlib.ui.admin.schema_api import schema_columns_request
from PySide6.QtCore import QCoreApplication, QObject, Signal
import tests.test_administration_api as native_fixture
from tests.test_administration_documents import SCHEMA
from tests.qt_application import gui_test_application


class SchemaConnectionDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        from thlib.environment import env_mode
        self.directory = self.enterContext(tempfile.TemporaryDirectory(prefix='schema-connections-'))
        self.enterContext(patch.object(env_mode, 'current_path', self.directory))
        self.enterContext(patch('socket.create_connection', side_effect=AssertionError('Schema tests must run offline')))
        self.editor = GraphEditor(SimpleNamespace(can_administer=True, debug_log=None), 'schema')
        self.addCleanup(self.editor.shutdown)
        self.editor._project = 'demo'
        self.editor._can_write = True
        self.editor._document = {'xml': SCHEMA}
        self.editor._original = copy.deepcopy(self.editor.document)
        self.editor._metadata = {'searchTypes': [
            {'identity': 'demo/asset', 'label': 'Assets', 'table': 'asset'},
            {'identity': 'demo/shot', 'label': 'Shots', 'table': 'shot'}]}
        self.editor._document_loaded()

    def test_many_to_many_is_a_local_instance_node_and_two_code_links(self):
        self.editor.select_edge(0)
        self.editor.connectionEditor.make_many_to_many()
        instance = self.editor.selectedNode
        self.assertEqual(instance, 'demo/asset_in_shot')
        self.assertEqual(self.editor.selectedAttributes['type'], 'instance')
        self.assertTrue(next(node for node in self.editor.nodes if node['identity'] == instance)['pendingCreation'])
        self.assertEqual([(edge['from'], edge['to'], edge['from_col'], edge['to_col'])
                          for edge in self.editor.edges], [
            (instance, 'demo/asset', 'asset_code', 'code'),
            (instance, 'demo/shot', 'shot_code', 'code')])
        self.assertTrue(all(edge['relationship'] == 'code' for edge in self.editor.edges))
        self.assertIn('<!--keep-->', self.editor.document['xml'])
        self.assertIn('extension', self.editor.document['xml'])
        self.editor.connectionEditor.restore_direct()
        self.assertEqual(self.editor.edges[0]['custom'], 'edge')
        self.assertFalse(self.editor.document.get('newTypes'))

    def test_discard_or_remove_instance_does_not_leave_a_table_creation_request(self):
        self.editor.select_edge(0)
        self.editor.connectionEditor.make_many_to_many()
        self.editor.remove_selected()
        self.assertFalse(self.editor.document.get('newTypes'))
        self.editor.discard()
        self.assertFalse(self.editor.dirty)
        self.assertEqual(self.editor.document, {'xml': SCHEMA})

    def test_raw_xml_removal_and_rename_keep_creation_plan_owned_by_the_draft(self):
        self.editor.select_edge(0)
        self.editor.connectionEditor.set_create_columns(True)
        self.editor.connectionEditor.make_many_to_many()
        self.editor.connectionEditor.rename_instance('asset_shots')
        self.assertEqual(set(self.editor.document['newTypes']), {'demo/asset_shots'})
        self.assertTrue(all(edge['from'] == 'demo/asset_shots' for edge in self.editor.edges))
        self.editor.connectionEditor.restore_direct()
        self.assertTrue(self.editor.connectionEditor.createColumns)
        self.editor.connectionEditor.make_many_to_many()
        self.editor.apply_xml('<schema/>')
        self.assertEqual(self.editor.document, {'xml': '<schema />'})

    def test_reverse_materializes_implicit_native_keys_in_the_correct_direction(self):
        self.editor.apply_xml(SCHEMA.replace(' from_col="shot_code" to_col="code"', ''))
        self.editor.select_edge(0)
        self.editor.connectionEditor.reverse()
        self.assertEqual(self.editor.selectedAttributes['from_col'], 'code')
        self.assertEqual(self.editor.selectedAttributes['to_col'], 'shot_code')

    def test_column_requests_are_bounded_cached_and_cancelled_on_selection_or_reset(self):
        from thlib.environment import env_inst

        class Worker(QObject):
            result = Signal(object)
            error = Signal(object)
            cancelled = False

            def start(self):
                pass

            def cancel(self):
                self.cancelled = True

        workers = []

        def add_task(operation):
            worker = Worker()
            worker.operation = operation
            workers.append(worker)
            return worker

        self.enterContext(patch.object(env_inst, 'server_pool', SimpleNamespace(
            is_stopped=False, add_task=add_task)))
        connection = self.editor.connectionEditor
        self.editor.select_edge(0)
        connection.load_columns()
        self.assertTrue(connection.loading)
        stale_callback = connection._callbacks[0]
        self.editor.select_node('demo/asset')
        connection.load_columns()
        self.assertTrue(workers[0].cancelled)
        stale_callback({'demo/asset': [{'name': 'stale', 'type': 'text'}]})
        self.assertEqual(connection.columns, {})
        self.editor.select_edge(0)
        connection.load_columns()
        payload = {
            'demo/asset': {'table': 'asset', 'database': 'demo', 'tableAvailable': False, 'columns': []},
            'demo/shot': {'table': 'shot', 'database': 'demo', 'tableAvailable': True,
                          'columns': [{'name': 'id', 'type': 'integer'}]},
        }
        with patch.object(tc, 'execute_procedure_serverside', return_value=payload) as rpc:
            result = workers[-1].operation()
            rpc.assert_called_once_with(schema_columns_request, {
                'project_code': 'demo', 'search_types': ['demo/asset', 'demo/shot']}, project='demo')
        workers[-1].result.emit(result)
        QCoreApplication.processEvents()
        self.assertEqual(connection.columnCatalog, payload)
        self.assertEqual(connection.columns, {name: row['columns'] for name, row in payload.items()})
        self.assertEqual(connection.error, '')
        self.editor.select_node('demo/asset')
        connection.load_columns()
        self.editor.select_edge(0)
        connection.load_columns()
        self.editor.move_node('demo/asset', 66, 44)
        connection.load_columns()
        self.assertEqual(len(workers), 2)
        connection.refresh_columns()
        self.assertEqual(len(workers), 3)
        workers[-1].error.emit(({'exception': ValueError('Column query failed')}, workers[-1]))
        QCoreApplication.processEvents()
        self.assertEqual(connection.error, 'Column query failed')
        connection.load_columns()
        self.assertEqual(len(workers), 3, 'Errors do not cause a binding-driven retry loop')
        connection.refresh_columns()
        stale_callback = connection._callbacks[0]
        self.editor.reset('another')
        stale_callback(payload)
        self.assertTrue(workers[-1].cancelled)
        self.assertEqual(connection.columns, {})
        self.assertEqual(connection.columnCatalog, {})


class SchemaConnectionApiTests(unittest.TestCase):
    def setUp(self):
        self.fixture = native_fixture.AdministrationApiTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        fixture = self.fixture
        fixture.tables['sthpw/search_object'].append(dict(
            code='demo/shot', title='Shots', namespace='demo', table_name='shot', database='{project}'))
        fixture.columns['demo/shot'] = {'code': {'data_type': 'varchar'}, 'id': {'data_type': 'integer'}}
        fixture.tables['demo/shot'] = []
        fixture.tables['sthpw/schema'][0]['schema'] = SCHEMA
        fixture.columns['demo/asset']['shot_code'] = {'data_type': 'varchar'}
        fixture.project.get_sql = lambda: SimpleNamespace(table_exists=lambda name: 'demo/' + name in fixture.tables)
        self.loaded = json.loads(schema_request('load', 'demo', 'demo'))

    def save(self, document):
        return json.loads(schema_request('save', 'demo', 'demo', document, self.loaded['revision']))

    def instance_document(self):
        return {'xml': '''<schema parent="base"><!--keep-->
            <search_type name="demo/asset"/><search_type name="demo/shot"/>
            <search_type name="demo/asset_in_shot" type="instance" xpos="180" ypos="80"/>
            <connect from="demo/asset_in_shot" to="demo/asset" relationship="code" from_col="asset_code" to_col="code"/>
            <connect from="demo/asset_in_shot" to="demo/shot" relationship="code" from_col="shot_id" to_col="id"/>
            </schema>''', 'newTypes': {'demo/asset_in_shot': {'original': {}}}}

    def test_save_creates_instance_and_typed_keys_only_after_all_validation(self):
        result = self.save(self.instance_document())
        self.assertIn(('create_type', 'asset_in_shot', False), self.fixture.calls)
        self.assertEqual(self.fixture.columns['demo/asset_in_shot']['shot_id']['data_type'], 'integer')
        self.assertIn('<!--keep-->', result['document']['xml'])
        self.assertEqual(set(result['document']), {'xml'})
        self.assertIn('demo/asset_in_shot', [row['identity'] for row in result['metadata']['searchTypes']])

    def test_missing_keys_require_explicit_create_columns_and_use_opposite_type(self):
        root = ET.fromstring(SCHEMA)
        edge = root.find('connect')
        edge.set('from_col', 'shot_id')
        edge.set('to_col', 'id')
        document = {'xml': ET.tostring(root, encoding='unicode')}
        with self.assertRaisesRegex(ValueError, 'shot_id'):
            self.save(document)
        self.assertEqual(self.fixture.calls, [])
        document['createColumns'] = [{'from': 'demo/asset', 'to': 'demo/shot', 'path': ''}]
        self.save(document)
        self.assertIn(('column', 'demo/asset', 'shot_id', 'integer'), self.fixture.calls)

    def test_conflicts_or_invalid_last_edge_never_create_a_partial_instance(self):
        for failure in ('column', 'existing_table', 'revision', 'orphan'):
            with self.subTest(failure=failure):
                document = self.instance_document()
                if failure == 'column':
                    document['xml'] = document['xml'].replace('to_col="id"', 'to_col="absent"')
                elif failure == 'existing_table':
                    self.fixture.tables['demo/asset_in_shot'] = []
                elif failure == 'revision':
                    self.fixture.tables['sthpw/schema'][0]['schema'] = '<schema changed="yes"/>'
                else:
                    document['xml'] = '<schema/>'
                with self.assertRaises(ValueError):
                    self.save(document)
                self.assertEqual(self.fixture.calls, [])
                self.fixture.tables.pop('demo/asset_in_shot', None)
                self.fixture.tables['sthpw/schema'][0]['schema'] = SCHEMA

    def test_catalog_reads_only_selected_columns_and_save_preserves_native_key_length(self):
        self.fixture.columns['demo/asset']['code']['size'] = 1024
        columns = json.loads(schema_columns_request('demo', ['demo/asset', 'demo/shot']))
        self.assertEqual(set(columns), {'demo/asset', 'demo/shot'})
        self.assertIn({'name': 'id', 'type': 'integer'}, columns['demo/shot']['columns'])
        self.assertEqual(self.fixture.calls, [])
        result = self.save(self.instance_document())
        self.assertEqual(self.fixture.columns['demo/asset_in_shot']['asset_code']['data_type'], 'varchar(1024)')
        # Repeating an uncertain save must conflict, never create another table.
        calls = list(self.fixture.calls)
        with self.assertRaisesRegex(ValueError, 'Schema changed'):
            self.save(self.instance_document())
        self.assertEqual(self.fixture.calls, calls)
        self.assertNotIn('newTypes', result['document'])

    def test_column_catalog_authorization_precedes_table_discovery(self):
        self.fixture.admin = False
        with self.assertRaises(PermissionError):
            schema_columns_request('demo', ['demo/asset'])
        self.assertEqual(self.fixture.calls, [])

    def test_missing_endpoint_keeps_other_columns_and_reports_physical_table(self):
        from pyasm.search import SearchType

        database = sqlite3.connect(':memory:')
        self.addCleanup(database.close)
        database.execute('CREATE TABLE shot (code TEXT, id INTEGER)')

        def column_info(table, **_):
            self.assertEqual(table, 'shot', 'Missing tables must not be probed')
            return {row[1]: {'data_type': row[2].lower()}
                    for row in database.execute('PRAGMA table_info(shot)')}

        sql = SimpleNamespace(
            get_database_name=lambda: 'demo',
            table_exists=lambda table: bool(database.execute(
                'SELECT 1 FROM sqlite_master WHERE name = ?', (table,)).fetchone()),
            get_column_info=Mock(side_effect=column_info))
        with patch.object(SearchType, 'get_sql_by_search_type', return_value=sql):
            result = json.loads(schema_columns_request('demo', ['demo/asset', 'demo/shot']))

        self.assertEqual(result['demo/asset'], {
            'table': 'asset', 'database': 'demo', 'tableAvailable': False, 'columns': []})
        self.assertTrue(result['demo/shot']['tableAvailable'])
        self.assertIn({'name': 'id', 'type': 'integer'}, result['demo/shot']['columns'])
        sql.get_column_info.assert_called_once_with('shot', use_cache=False)
        self.assertEqual(self.fixture.calls, [])

    def test_column_catalog_respects_native_fixed_and_project_database_resolution(self):
        from pyasm.search import SearchType

        self.fixture.tables['sthpw/search_object'][0]['database'] = 'shared_assets'
        resolutions = []

        def resource(search_type):
            # This is Project.get_database_by_search_type's contract: an
            # explicit ?project overrides the Search Type's registry database.
            name, _, query = search_type.partition('?project=')
            database = query or SearchType.get(name).get_database()
            resolutions.append((name, database))
            return SimpleNamespace(
                get_database_name=lambda: database,
                table_exists=lambda table: (database, table) in (
                    ('shared_assets', 'asset'), ('demo', 'shot')),
                get_column_info=lambda table, **_: self.fixture.columns[name])

        with patch.object(SearchType, 'get_sql_by_search_type', side_effect=resource):
            result = json.loads(schema_columns_request('demo', ['demo/asset', 'demo/shot']))
            self.save({'xml': SCHEMA.replace('shot_code', 'code')})
        self.assertTrue(all(row['tableAvailable'] for row in result.values()))
        self.assertEqual(resolutions, [('demo/asset', 'shared_assets'), ('demo/shot', 'demo')] * 2)

    def test_column_catalog_database_failure_is_not_a_missing_table(self):
        from pyasm.search import SearchType

        sql = SimpleNamespace(table_exists=Mock(side_effect=RuntimeError('Database connection failed')),
                              get_database_name=lambda: 'demo')
        with patch.object(SearchType, 'get_sql_by_search_type', return_value=sql):
            with self.assertRaisesRegex(RuntimeError, 'Database connection failed'):
                schema_columns_request('demo', ['demo/asset'])
        self.assertEqual(self.fixture.calls, [])

    def test_save_still_rejects_missing_table_before_any_schema_or_column_write(self):
        self.fixture.tables.pop('demo/asset')
        document = self.instance_document()
        with self.assertRaisesRegex(ValueError, 'demo/asset.*absent'):
            self.save(document)
        self.assertEqual(self.fixture.calls, [])

    def test_both_procedures_execute_through_the_actual_rpc_source_envelope(self):
        def execute_script(path, kwargs):
            self.assertEqual(path, '')
            scope = {}
            exec('def procedure():\n' + textwrap.indent(kwargs['code'], '    '), scope)
            return {'info': {'spt_ret_val': scope['procedure']()}}

        server = SimpleNamespace(execute_python_script=execute_script)
        columns = tc.execute_procedure_serverside(schema_columns_request, {
            'project_code': 'demo', 'search_types': ['demo/shot']}, project='demo', server=server)
        self.assertEqual(columns['demo/shot']['columns'][1]['name'], 'id')
        result = tc.execute_procedure_serverside(schema_request, {
            'action': 'save', 'project_code': 'demo', 'identity': 'demo',
            'document': self.instance_document(), 'expected_revision': self.loaded['revision']},
            project='demo', server=server)
        self.assertIn('demo/asset_in_shot', result['document']['xml'])
        self.assertEqual(sum(call[0] == 'create_type' for call in self.fixture.calls), 1)


if __name__ == '__main__':
    unittest.main()
