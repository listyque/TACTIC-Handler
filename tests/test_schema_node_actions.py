"""Schema node deletion boundaries and the original native command contract."""

import copy
import json
import sys
import textwrap
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from thlib.ui.admin.schema_delete_api import schema_delete_request
from tests import test_administration_api as native_fixture


class SchemaDeletionApiTests(unittest.TestCase):
    def setUp(self):
        self.fixture = native_fixture.AdministrationApiTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.tables['sthpw/pipeline'][0]['pipeline'] = '<pipeline/>'
        self.fixture.tables['config/process'] = []
        native = sys.modules['pyasm.search']
        self.native = native
        search_class = native.Search

        class Search(search_class):
            def __init__(self, table):
                super().__init__(table.split('?')[0])

        self.enterContext(patch.object(native, 'Search', Search))
        self.locks = []
        self.sql = SimpleNamespace(
            table_exists=lambda table: 'demo/' + table in self.fixture.tables,
            get_database_type=lambda: 'PostgreSQL',
            is_in_transaction=lambda: True,
            do_update=self.locks.append, clear_table_cache=Mock(),
            get_column_info=lambda table, **_: self.fixture.columns['demo/' + table])
        self.enterContext(patch.object(native.SearchType, 'get_sql_by_search_type', return_value=self.sql))
        obj_class = type(native.SearchType.get('demo/asset'))

        def delete(obj):
            self.fixture.calls.append(('delete', obj.table, obj.get_code()))
            self.fixture.tables[obj.table].remove(obj.data)

        self.enterContext(patch.object(obj_class, 'delete', delete, create=True))

        def execute(command, arguments):
            self.assertEqual(command, 'tactic.ui.tools.DeleteSearchTypeCmd')
            self.assertEqual(arguments, {'search_type': 'demo/asset', 'values': {'related_types': []}})
            self.fixture.tables.pop('demo/asset')
            obj = native.SearchType.get('demo/asset')
            if obj.get_value('database') != '{project}':
                obj.delete()

        self.native_delete = Mock(side_effect=execute)
        self.fixture.local_api.execute_cmd = self.native_delete

    def request(self, action='load', **kwargs):
        return json.loads(schema_delete_request(action, 'demo', 'demo/asset', **kwargs))

    def save(self, payload):
        return self.request('save', document={'confirmation': 'demo/asset'},
                            expected_revision=payload['revision'])

    def test_read_only_review_then_native_delete_preserves_shared_registration(self):
        review = self.request()
        self.assertTrue(review['canWrite'])
        self.assertTrue(review['metadata']['sharedRegistration'])
        self.assertEqual(self.locks, [])
        self.native_delete.assert_not_called()
        result = self.save(review)
        self.native_delete.assert_called_once()
        self.assertIn('LOCK TABLE "asset" IN ACCESS EXCLUSIVE MODE', self.locks)
        self.assertNotIn('demo/asset', self.fixture.tables)
        self.assertIsNotNone(self.native.SearchType.get('demo/asset'))
        self.assertEqual(self.fixture.tables['sthpw/pipeline'], [])
        self.assertNotIn('search_type', result['metadata']['schema']['xml'])
        self.assertIn('custom="yes"', result['metadata']['schema']['xml'])
        self.sql.clear_table_cache.assert_called_once()

    def test_used_types_retired_objects_aliases_and_active_processes_are_not_deleted(self):
        for kind in ('objects', 'retired', 'alias', 'pipeline', 'process'):
            with self.subTest(kind=kind):
                before = copy.deepcopy(self.fixture.tables)
                if kind in ('objects', 'retired'):
                    self.fixture.tables['demo/asset'] = [{'code': 'A1', 's_status': 'retired' if kind == 'retired' else ''}]
                elif kind == 'alias':
                    self.fixture.tables['sthpw/search_object'].append(dict(
                        self.fixture.tables['sthpw/search_object'][0], code='demo/alias'))
                elif kind == 'pipeline':
                    self.fixture.tables['sthpw/pipeline'][0]['pipeline'] = '<pipeline><process name="model"/></pipeline>'
                else:
                    self.fixture.tables['config/process'] = [{'pipeline_code': 'demo/assets'}]
                review = self.request()
                self.assertFalse(review['canWrite'])
                with self.assertRaisesRegex(ValueError, 'in use'):
                    self.save(review)
                self.native_delete.assert_not_called()
                self.fixture.tables = before

    def test_rechecks_after_lock_and_rejects_a_new_object(self):
        review = self.request()

        def lock(statement):
            self.locks.append(statement)
            if statement.startswith('LOCK TABLE'):
                self.fixture.tables['demo/asset'].append({'code': 'NEW'})

        self.sql.do_update = lock
        with self.assertRaisesRegex(ValueError, 'in use'):
            self.save(review)
        self.native_delete.assert_not_called()

    def test_bad_confirmation_stale_schema_and_lost_admin_do_not_write(self):
        review = self.request()
        with self.assertRaisesRegex(ValueError, 'identifier'):
            self.request('save', document={'confirmation': 'asset'}, expected_revision=review['revision'])
        self.fixture.tables['sthpw/schema'][0]['schema'] = '<schema><search_type name="demo/asset" xpos="20"/></schema>'
        with self.assertRaisesRegex(ValueError, 'changed'):
            self.save(review)
        self.fixture.admin = False
        with self.assertRaises(PermissionError):
            self.save(review)
        self.native_delete.assert_not_called()

    def test_system_types_and_other_databases_are_rejected(self):
        row = self.fixture.tables['sthpw/search_object'][0]
        for namespace in ('sthpw', 'config'):
            row['namespace'] = namespace
            with self.assertRaisesRegex(ValueError, 'System'):
                self.request()
        row.update(namespace='demo', database='another')
        with self.assertRaisesRegex(ValueError, 'another database'):
            self.request()
        self.native_delete.assert_not_called()

    def test_native_swallowed_failure_does_not_commit_schema_or_pipeline_deletion(self):
        review = self.request()
        self.native_delete.side_effect = None
        with self.assertRaisesRegex(RuntimeError, 'did not delete'):
            self.save(review)
        self.assertEqual(self.fixture.calls, [])
        self.assertIn('demo/asset', self.fixture.tables['sthpw/schema'][0]['schema'])

    def test_deletion_outside_a_native_transaction_is_rejected(self):
        review = self.request()
        self.sql.is_in_transaction = lambda: False
        with self.assertRaisesRegex(RuntimeError, 'TACTIC transaction'):
            self.save(review)
        self.native_delete.assert_not_called()
        self.assertEqual(self.locks, [])

    def test_project_owned_registration_is_removed_but_external_schema_blocks_it(self):
        self.fixture.tables['sthpw/search_object'][0]['database'] = 'demo'
        self.fixture.tables['sthpw/schema'].append({'code': 'other', 'schema': '<schema><search_type name="demo/asset"/></schema>'})
        review = self.request()
        self.assertFalse(review['canWrite'])
        self.assertEqual(review['metadata']['otherSchemas'], ['other'])
        self.fixture.tables['sthpw/schema'].pop()
        self.save(self.request())
        self.assertIsNone(self.native.SearchType.get('demo/asset'))

    def test_delete_executes_through_the_actual_rpc_source_envelope(self):
        from thlib import tactic_classes as tc

        def execute_script(path, kwargs):
            self.assertEqual(path, '')
            scope = {}
            exec('def procedure():\n' + textwrap.indent(kwargs['code'], '    '), scope)
            return {'info': {'spt_ret_val': scope['procedure']()}}

        server = SimpleNamespace(execute_python_script=execute_script)
        arguments = {'project_code': 'demo', 'identity': 'demo/asset'}
        review = tc.execute_procedure_serverside(
            schema_delete_request, dict(arguments, action='load'), project='demo', server=server)
        self.native_delete.assert_not_called()
        result = tc.execute_procedure_serverside(schema_delete_request, dict(
            arguments, action='save', document={'confirmation': 'demo/asset'},
            expected_revision=review['revision']), project='demo', server=server)
        self.assertIn('schema', result['metadata'])
        self.native_delete.assert_called_once()
