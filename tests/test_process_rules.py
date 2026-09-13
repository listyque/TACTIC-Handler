"""Native trigger callbacks, context isolation and process dependency drafts."""

import ast
import copy
import json
from pathlib import Path
import sys
import textwrap
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from tests import test_administration_api as native_fixture
from thlib.ui.admin.process_rules_api import process_rules_request


NATIVE_SOURCE = Path(__file__).resolve().parents[1] / '.cache/tactic-source/src/tactic/ui/tools/trigger_wdg.py'


@unittest.skipUnless(NATIVE_SOURCE.is_file(), 'Requires the audited TACTIC source checkout')
class ProcessRulesApiTests(unittest.TestCase):
    def setUp(self):
        self.fixture = native_fixture.AdministrationApiTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.tables = self.fixture.tables
        self.tables.update({'config/naming': [], 'sthpw/notification': []})
        self.tables['sthpw/pipeline'][0]['pipeline'] = (
            '<pipeline><process name="model"/><process name="review"/>'
            '<connect from="model" to="review"/></pipeline>')
        self.tables['sthpw/pipeline'].append(dict(code='task', project_code='', search_type='sthpw/task',
            pipeline='<pipeline><process name="Work"/><process name="Done"/><process name="O\'Brien &amp; Co"/></pipeline>'))
        self.tables['config/process'][0]['workflow'] = {}
        self.tables['config/process'].append(dict(code='PR2', pipeline_code='demo/assets', process='review', workflow={}))
        search_module, biz = sys.modules['pyasm.search'], sys.modules['pyasm.biz']
        Search = search_module.Search
        Native = type(biz.Pipeline.get_by_code('task'))
        fixture = self.fixture
        original_commit = Native.commit

        def commit(row):
            if not row.get_code():
                row.data['code'] = 'generated-' + str(len(fixture.tables[row.table]) + 1)
            original_commit(row)

        def json_value(row, key):
            value = row.data.get(key) or {}
            return json.loads(value) if isinstance(value, str) else copy.deepcopy(value)

        def processes(row):
            return [SimpleNamespace(get_name=lambda node=node: node.get('name'), get_task_pipeline=lambda: 'task')
                    for node in ET.fromstring(row.get_value('pipeline') or '<pipeline/>').findall('process')]

        self.enterContext(patch.object(Native, 'get_json_value', json_value))
        self.enterContext(patch.object(Native, 'set_json_value', lambda row, key, value: row.set_value(key, copy.deepcopy(value)), create=True))
        self.enterContext(patch.object(Native, 'get_base_search_type', lambda row: row.table, create=True))
        self.enterContext(patch.object(Native, 'get_display_value', lambda row: row.get_value('name'), create=True))
        self.enterContext(patch.object(Native, 'commit', commit))
        self.enterContext(patch.object(Native, 'delete', lambda row: fixture.tables[row.table].remove(row.data), create=True))
        self.enterContext(patch.object(Native, 'get_processes', processes, create=True))
        self.enterContext(patch.object(Native, 'get_output_processes', lambda row, name: [
            node for node in processes(row) if node.get_name() in [edge.get('to') for edge in
            ET.fromstring(row.get_value('pipeline')).findall('connect') if edge.get('from') == name]], create=True))
        self.enterContext(patch.object(search_module.SearchType, 'column_exists', lambda table, column: table == 'demo/asset', create=True))
        self.enterContext(patch.object(Search, 'get_by_search_key', staticmethod(lambda key: next(
            (Native(table, data) for table, rows in self.tables.items() for data in rows
             if table + '?code=' + data.get('code', '') == key), None)), create=True))
        unpaged = Search.get_sobjects
        self.enterContext(patch.object(Search, 'set_offset', lambda row, value: setattr(row, 'offset', value), create=True))
        self.enterContext(patch.object(Search, 'add_column', lambda row, column: None, create=True))
        self.enterContext(patch.object(Search, 'set_limit', lambda row, value: setattr(row, 'limit', value)))
        self.enterContext(patch.object(Search, 'get_sobjects', lambda row: unpaged(row)[
            getattr(row, 'offset', 0):getattr(row, 'offset', 0) + getattr(row, 'limit', 100000)]))

        class Command:
            def __init__(self, **kwargs):
                self.kwargs, self.info = kwargs, {}

        # Execute the ACTUAL audited callback class bodies, not imitations of
        # their save contracts. Widget imports/initialization are unnecessary.
        names = {'BaseTriggerEditCbk', 'StatusTriggerEditCbk', 'TriggerParentStatusEditCbk',
                 'TriggerCreateCbk', 'TriggerDateCbk', 'PythonScriptTriggerEditCbk',
                 'PythonClassTriggerEditCbk', 'NotificationTriggerEditCbk'}
        tree = ast.parse(NATIVE_SOURCE.read_text(encoding='utf-8'))
        classes = ast.Module(body=[node for node in tree.body if isinstance(node, ast.ClassDef) and node.name in names], type_ignores=[])
        namespace = dict(Command=Command, Search=Search, SearchType=search_module.SearchType,
                         SearchKey=search_module.SearchKey, Project=biz.Project, Notification=Native,
                         jsondumps=json.dumps, jsonloads=json.loads)
        exec(compile(classes, str(NATIVE_SOURCE), 'exec'), namespace)
        callbacks = SimpleNamespace(**{name: namespace[name] for name in names})
        self.enterContext(patch.dict(sys.modules, {'tactic.ui.tools': SimpleNamespace(trigger_wdg=callbacks)}))

    def load(self, **kwargs):
        return json.loads(process_rules_request('load', 'demo', 'PR1', **kwargs))

    def save(self, loaded):
        return json.loads(process_rules_request('save', 'demo', 'PR1', loaded['document'], loaded['revision']))

    def rule(self, action='task_status', **changes):
        from thlib.ui.admin.process_rules import ProcessRulesEditor
        editor = ProcessRulesEditor(SimpleNamespace(), None)
        editor._can_write = True
        editor.add_rule('notification' if action == 'notification' else 'trigger')
        return dict(editor.selectedRule, title='Test rule', action=action, **changes)

    def test_native_callbacks_create_each_action_without_executing_it(self):
        cases = [
            ('task_status', dict(targets=[{'process': 'review', 'status': 'Done'}], srcStatus='Work')),
            ('parent_status', dict(targetStatus='Done')),
            ('task_create', dict(outputs=['review'])),
            ('task_date', dict(column='actual_start_date')),
            ('custom_script', dict(scriptPath='workflow/test')),
            ('python_class', dict(classPath='test.NeverExecuteThis')),
            ('notification', dict(subject='Subject', body='Hello', mailTo='{$LOGIN}', loginTicket=True)),
        ]
        loaded = self.load()
        for action, values in cases:
            with self.subTest(action=action):
                loaded['document']['rules'].append(self.rule(action, **values))
                loaded = self.save(loaded)
                row = loaded['document']['rules'][-1]
                self.assertEqual(row['action'], action)
                self.assertEqual(row['scope'], 'local')
                self.assertTrue(row['key'])
                self.assertEqual(self.fixture.calls[-1][0], 'commit')
        self.assertEqual(len(self.tables['config/trigger']), 6)
        self.assertEqual(len(self.tables['sthpw/notification']), 1)

    def test_global_scope_and_unrelated_records_are_not_overwritten(self):
        self.tables['config/trigger'].append(dict(code='foreign', process='unrelated', event='custom'))
        loaded = self.load()
        loaded['document']['rules'].append(self.rule('task_date', column='actual_end_date', scope='global'))
        saved = self.save(loaded)
        self.assertEqual(self.tables['config/trigger'][-1]['process'], 'model')
        saved['document']['rules'] = []
        self.save(saved)
        self.assertEqual([row['code'] for row in self.tables['config/trigger']], ['foreign'])

    def test_notification_status_is_xml_safe_and_can_be_cleared(self):
        loaded = self.load()
        loaded['document']['rules'].append(self.rule('notification', srcStatus="O'Brien & Co", body='unchanged'))
        loaded = self.save(loaded)
        row = self.tables['sthpw/notification'][0]
        self.assertIn("O'Brien", ET.fromstring(row['rules']).find('rule').text)
        loaded['document']['rules'][0]['srcStatus'] = ''
        loaded = self.save(loaded)
        self.assertEqual(row['rules'], '')
        self.assertNotIn('src_status', row['data'])
        self.assertEqual(row['message'], 'unchanged')

    def test_clearing_status_keeps_authored_notification_conditions(self):
        loaded = self.load()
        loaded['document']['rules'].append(self.rule('notification', srcStatus='Done', rules=
            '<rules><rule>@GET(.priority) == 3</rule></rules>'))
        loaded = self.save(loaded)
        loaded['document']['rules'][0]['srcStatus'] = ''
        self.save(loaded)
        rules = ET.fromstring(self.tables['sthpw/notification'][0]['rules'])
        self.assertEqual([row.text for row in rules.findall('rule')], ['@GET(.priority) == 3'])

    def test_explicit_approval_task_workflow_supplies_its_statuses(self):
        self.tables['sthpw/pipeline'].append(dict(code='demo/approval', search_type='sthpw/task',
            project_code='demo', pipeline='<pipeline><process name="Accepted"/></pipeline>'))
        self.tables['config/process'][1]['workflow'] = {'properties': {'task_pipeline': 'demo/approval'}}
        loaded = self.load()
        self.assertEqual(loaded['metadata']['processes'][1]['statuses'], ['Accepted'])

    def test_validation_and_revision_conflicts_precede_all_mutations(self):
        loaded = self.load()
        loaded['document']['rules'].append(self.rule('task_date', column='actual_end_date'))
        loaded['document']['rules'].append(self.rule('task_status', targets=[{'process': 'review', 'status': 'Invalid'}]))
        with self.assertRaisesRegex(ValueError, 'destination task workflow'):
            self.save(loaded)
        self.assertEqual(self.fixture.calls, [])
        loaded['document']['rules'].pop()
        self.tables['config/process'][0]['description'] = 'Changed remotely'
        with self.assertRaisesRegex(ValueError, 'changed on the server'):
            self.save(loaded)
        self.assertEqual(self.fixture.calls, [])

    def test_generated_action_trigger_has_one_owner(self):
        self.tables['config/trigger'].append(dict(code='native', process='PR1', event='process|action', data={}))
        loaded = self.load()
        self.assertTrue(loaded['document']['rules'][0]['managed'])
        loaded['document']['rules'] = []
        with self.assertRaisesRegex(ValueError, 'node parameters'):
            self.save(loaded)
        self.assertEqual(self.fixture.calls, [])

    def test_objects_are_counted_for_pipeline_and_paged(self):
        self.tables['demo/asset'] = [dict(code=str(index), name='Object ' + str(index), pipeline_code='demo/assets')
                                     for index in range(121)]
        first, second = self.load(), self.load(item_offset=50)
        self.assertEqual(first['metadata']['itemCount'], 121)
        self.assertEqual(len(first['metadata']['items']), 50)
        self.assertEqual(second['metadata']['items'][0]['label'], 'Object 50')
        self.assertEqual(first['revision'], second['revision'])

    def test_permission_and_shared_pipeline_are_enforced_server_side(self):
        self.fixture.admin = False
        with self.assertRaises(PermissionError):
            self.load()
        self.fixture.admin = True
        self.tables['sthpw/pipeline'][0]['project_code'] = ''
        loaded = self.load()
        self.assertFalse(loaded['canWrite'])
        with self.assertRaises(PermissionError):
            self.save(loaded)
        self.assertEqual(self.fixture.calls, [])

    def test_rpc_serialization_uses_native_modules_only(self):
        from thlib import tactic_classes as tc

        def execute(_path, kwargs):
            script = kwargs['code']
            compile('def procedure():\n' + textwrap.indent(script, '    '), '<process-dependencies>', 'exec')
            self.assertNotIn('from thlib', script)
            self.assertIn("identity='PR1'", script)
            return {'info': {'spt_ret_val': '{"ok": true}'}}

        with patch.object(tc, 'server_start', return_value=SimpleNamespace(execute_python_script=execute)):
            result = tc.execute_procedure_serverside(process_rules_request, {
                'action': 'load', 'project_code': 'demo', 'identity': 'PR1'}, project='demo')
        self.assertTrue(result['ok'])

    def test_graph_revision_ignores_ordinary_rules_but_tracks_generated_triggers(self):
        from thlib.ui.admin.workflow_api import workflow_request

        def graph_revision():
            return json.loads(workflow_request('load', 'demo', 'demo/assets'))['revision']

        before = graph_revision()
        self.tables['config/trigger'].append(dict(code='ordinary', process='PR1',
            event='change|sthpw/task|status', data={}))
        self.assertEqual(graph_revision(), before)
        self.tables['config/trigger'].append(dict(code='generated', process='PR1',
            event='process|action', data={}))
        self.assertNotEqual(graph_revision(), before)
