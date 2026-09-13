"""Administration RPC boundaries against native-object contract fixtures."""

import copy
import json
import sqlite3
import sys
import textwrap
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from thlib.ui.admin.schema_api import schema_request
from thlib.ui.admin.search_types_api import search_types_request
from thlib.ui.admin.security_api import security_request
from thlib.ui.admin.workflow_api import workflow_request


class AdministrationApiTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.admin = True
        self.project_code = 'demo'
        self.count_queries = []
        self.tables = {
            'demo/asset': [],
            'sthpw/search_object': [dict(code='demo/asset', title='Assets', namespace='demo',
                                        description='', color='', table_name='asset', database='{project}')],
            'sthpw/schema': [dict(code='demo', schema='<schema custom="yes"><search_type name="demo/asset"/></schema>')],
            'sthpw/pipeline': [dict(code='demo/assets', project_code='demo', name='Assets',
                                   description='Keep', color='#667788', search_type='demo/asset',
                                   pipeline='<pipeline><process name="model" type="action"/></pipeline>')],
            'config/process': [dict(code='PR1', pipeline_code='demo/assets', process='model',
                                    description='', workflow={'version': 2, 'node_type': 'action',
                                                              'custom': {'retained': True}})],
            'config/trigger': [], 'config/custom_script': [], 'config/widget_config': [],
            'sthpw/task': [], 'sthpw/snapshot': [],
            'sthpw/login': [dict(login='artist', display_name='Artist')],
            'sthpw/login_group': [dict(code='G1', login_group='artists', access_level='low',
                                       project_code='demo', sub_groups='', access_rules='<rules/>')],
            'sthpw/project': [dict(code='demo', title='Demo')],
        }
        self.columns = {'demo/asset': {'code': {'data_type': 'varchar'}}}
        # TACTIC's postgresql/bootstrap_schema.sql registry columns. In
        # particular, search_object has no s_status column. Prepare real SQL
        # against this contract instead of accepting arbitrary filter names.
        self.registry = sqlite3.connect(':memory:')
        self.addCleanup(self.registry.close)
        self.registry.execute('''CREATE TABLE search_object (
            id integer, code text UNIQUE, search_type text, namespace text,
            description text, "database" text, table_name text, class_name text,
            title text, "schema" text, color text, id_column text, default_layout text
        )''')
        fixture = self

        class NativeObject:
            def __init__(self, table, data, new=False):
                self.table, self.data, self.new = table, data, new

            def get_code(self):
                return self.data.get('code', '')

            def get_value(self, key, **_):
                return self.data.get(key, '')

            def get_data(self):
                return copy.deepcopy(self.data)

            def get_json_value(self, key):
                return copy.deepcopy(self.data.get(key, {}))

            def set_value(self, key, value):
                if self.table == 'sthpw/search_object':
                    fixture.registry.execute(
                        'UPDATE search_object SET "{}" = ? WHERE code = ?'.format(key),
                        (value, self.get_code()))
                self.data[key] = value

            def get_table(self):
                return self.data['table_name']

            def get_search_type_id_col(self):
                return self.data.get('id_column') or 'id'

            def get_relationship_attrs(self, source, target, path=None, cache=True):
                for edge in ET.fromstring(self.data.get('schema') or '<schema/>').findall('connect'):
                    if {edge.get('from'), edge.get('to')} != {source, target}:
                        continue
                    if path and edge.get('path') != path:
                        continue
                    attrs = dict(edge.attrib)
                    kind = attrs.get('relationship', 'code')
                    if kind in ('code', 'id'):
                        table = get_by_code('sthpw/search_object', attrs['to']).get_table()
                        attrs.setdefault('from_col', table + '_' + kind)
                        attrs.setdefault('to_col', kind)
                    return attrs
                parent = self.get_parent_schema()
                return parent.get_relationship_attrs(source, target, path, cache) if parent else {}

            def get_database(self):
                database = self.get_value('database')
                return fixture.project.get_database_name() if database == '{project}' else database

            def get_search_key(self):
                return self.table + '?code=' + self.get_code()

            def get_parent_schema(self):
                parent = ET.fromstring(self.data.get('schema') or '<schema/>').get('parent')
                return get_by_code('sthpw/schema', parent) if parent else None

            sthpw_schema = None

            def set_xml(self, xml):
                self.data['schema'] = xml

            def set_pipeline(self, xml):
                # This is deliberately not persistence: the upstream method
                # only builds/caches an in-memory graph.
                self.cached_xml = xml

            def commit(self):
                if self.new and self.table == 'sthpw/pipeline' and not self.get_code():
                    self.data['code'] = 'PIPELINE{:05d}'.format(
                        len(fixture.tables[self.table]) + 1
                    )
                fixture.calls.append(('commit', self.table, self.get_code()))
                if self.new:
                    fixture.tables[self.table].append(self.data)
                    self.new = False

            def update_dependencies(self):
                fixture.calls.append(('dependencies', self.data['pipeline']))

        class Search:
            def __init__(self, table):
                self.table, self.filters = table, []
                self.show_retired = False

            def set_show_retired(self, value):
                self.show_retired = value

            def add_filter(self, name, value, op='=', **_):
                self.filters.append((name, [value], op))

            def add_filters(self, name, values):
                self.filters.append((name, values, '='))

            def set_limit(self, _):
                pass

            def get_sobjects(self):
                if self.table == 'sthpw/search_object':
                    fixture.registry.execute('DELETE FROM search_object')
                    for row in fixture.tables[self.table]:
                        columns = ', '.join('"{}"'.format(key) for key in row)
                        parameters = ', '.join('?' for _ in row)
                        fixture.registry.execute(
                            'INSERT INTO search_object ({}) VALUES ({})'.format(columns, parameters),
                            list(row.values()))
                    clauses, parameters = [], []
                    for name, values, op in self.filters:
                        clauses.append('search_object."{}" {} ({})'.format(
                            name, 'NOT IN' if op == '!=' else 'IN',
                            ', '.join('?' for _ in values)))
                        parameters.extend(values)
                    query = 'SELECT code FROM search_object'
                    if clauses:
                        query += ' WHERE ' + ' AND '.join(clauses)
                    codes = {row[0] for row in fixture.registry.execute(query, parameters)}
                    return [NativeObject(self.table, row) for row in fixture.tables[self.table]
                            if row['code'] in codes]
                return [NativeObject(self.table, row) for row in fixture.tables[self.table]
                        if (self.show_retired or row.get('s_status') != 'retired')
                        and all((row.get(name) in values) == (op != '!=')
                                for name, values, op in self.filters)]

            def get_sobject(self):
                return next(iter(self.get_sobjects()), None)

            def get_count(self):
                fixture.count_queries.append((self.table, self.show_retired, list(self.filters)))
                return sum(1 for row in fixture.tables[self.table]
                           if (self.show_retired or row.get('s_status') != 'retired')
                           and all((row.get(name) in values) == (op != '!=')
                                   for name, values, op in self.filters))

        def get_by_code(table, code):
            return next((NativeObject(table, row) for row in self.tables[table]
                         if row.get('code') == code), None)

        def create_schema(code, description, xml):
            item = NativeObject('sthpw/schema', dict(code=code, description=description, schema=xml), True)
            item.commit()
            return item

        def create_type(name, title, description, has_pipeline):
            code = 'demo/' + name
            self.calls.append(('create_type', name, has_pipeline))
            self.tables['sthpw/search_object'].append(dict(
                code=code, title=title, description=description, namespace='demo', table_name=name,
                database='{project}'))
            self.columns[code] = {'code': {'data_type': 'varchar'}}
            self.tables[code] = []
            # SearchTypeCreatorCmd also registers a node in the project schema.
            schema = get_by_code('sthpw/schema', 'demo')
            if schema is None:
                schema = create_schema('demo', 'Project schema', '<schema/>')
            root = ET.fromstring(schema.get_value('schema'))
            ET.SubElement(root, 'search_type', name=code, xpos='0', ypos='0')
            schema.set_xml(ET.tostring(root, encoding='unicode'))
            schema.commit()

        def add_column(identity, name, column_type):
            self.calls.append(('column', identity, name, column_type))
            self.columns[identity][name] = {'data_type': column_type}

        class ProcessCommand:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def execute(self):
                fixture.calls.append(('process_command', copy.deepcopy(self.kwargs)))
                for row in fixture.tables['config/process']:
                    if row['process'] == self.kwargs['process']:
                        row['workflow'] = {key: value for key, value in self.kwargs.items()
                                           if key not in ('process', 'pipeline_code', 'description')}

        class AccessManager:
            def add_xml_rules(self, xml, **kwargs):
                ET.fromstring(xml)
                fixture.calls.append(('validate_rules', xml))

        self.security = SimpleNamespace(is_admin=lambda: self.admin, reset_access_manager=lambda: None)
        self.project = SimpleNamespace(
            get_database_name=lambda: 'sthpw' if self.project_code == 'admin' else self.project_code,
            get_search_types=lambda **_: Search('sthpw/search_object').get_sobjects())
        self.local_api = SimpleNamespace(create_search_type=create_type, add_column_to_search_type=add_column,
                                         execute_cmd=lambda *args, **kwargs: None)
        modules = {
            'pyasm.common': SimpleNamespace(Environment=SimpleNamespace(get_security=lambda: self.security)),
            'pyasm.search': SimpleNamespace(Search=Search,
                SearchKey=SimpleNamespace(get_by_sobject=lambda obj, **_: obj.get_search_key()),
                SearchType=SimpleNamespace(
                get=lambda code: get_by_code('sthpw/search_object', code),
                create=lambda table: NativeObject(table, {}, True),
                get_columns=lambda code: list(self.columns[code]),
                get_column_info=lambda code: copy.deepcopy(self.columns[code]),
                build_search_type=lambda code, project: code if code.startswith('sthpw/') else code + '?project=' + project,
                get_sql_by_search_type=lambda code: SimpleNamespace(table_exists=lambda table:
                    table in {key.split('/')[-1] for key in self.tables},
                    get_database_name=lambda: get_by_code('sthpw/search_object', code.split('?')[0]).get_database(),
                    get_column_info=lambda table, use_cache=True: copy.deepcopy(self.columns[code.split('?')[0]])),
                clear_column_cache=lambda code: None)),
            'pyasm.biz': SimpleNamespace(
                Project=SimpleNamespace(get_project_code=lambda: self.project_code, get=lambda: self.project,
                                        get_by_code=lambda code: get_by_code('sthpw/project', code)),
                Schema=SimpleNamespace(get_by_code=lambda code: get_by_code('sthpw/schema', code),
                                       create=create_schema, get=lambda **kwargs: get_by_code(
                                           'sthpw/schema', kwargs.get('project_code', self.project_code))),
                Pipeline=SimpleNamespace(get_by_code=lambda code: get_by_code('sthpw/pipeline', code),
                                         clear_cache=lambda **_: None)),
            'pyasm.security': SimpleNamespace(AccessManager=AccessManager,
                Login=SimpleNamespace(get_default_security_level=lambda: 'low'), LoginGroup=SimpleNamespace(
                ACCESS_DICT={'low': 1, 'high': 2}, get_default_access_rule=lambda *_, **kw: '<rules/>')),
            'tactic_client_lib': SimpleNamespace(TacticServerStub=SimpleNamespace(get=lambda **_: self.local_api)),
            'tactic.ui.tools.pipeline_wdg': SimpleNamespace(NewProcessInfoCmd=ProcessCommand),
            'tactic.ui.panel.security_manager_wdg': SimpleNamespace(permission_list=[{'key': 'edit', 'title': 'Edit'}]),
            'tactic.ui.panel': SimpleNamespace(SideBarBookmarkMenuWdg=SimpleNamespace(
                get_config=lambda *args: SimpleNamespace(get_element_names=lambda: []))),
            'tactic.ui.startup.security_wdg': SimpleNamespace(GearMenuSecurityWdg=SimpleNamespace(
                get_all_menu_names=lambda: [('File', {'label': ['Export Selected ...']})])),
        }
        self.enterContext(patch.dict(sys.modules, modules))

    def test_every_endpoint_authorizes_on_server_before_read_or_write(self):
        self.admin = False
        for endpoint in (search_types_request, schema_request, workflow_request, security_request):
            with self.subTest(endpoint=endpoint.__name__), self.assertRaises(PermissionError):
                endpoint('list', 'demo')
        self.assertEqual(self.calls, [])

    def test_workflow_form_catalogs_use_server_groups_users_and_scoped_pipelines(self):
        self.tables['sthpw/pipeline'].extend([
            dict(code='task', name='Shared statuses', search_type='sthpw/task', project_code=''),
            dict(code='other/tasks', name='Other project', search_type='sthpw/task', project_code='other'),
        ])
        result = json.loads(workflow_request('load', 'demo', 'demo/assets'))
        metadata = result['metadata']
        self.assertEqual(metadata['groups'], [{'identity': 'artists', 'label': 'artists'}])
        self.assertEqual(metadata['users'], [{'identity': 'artist', 'label': 'Artist'}])
        self.assertEqual([row['identity'] for row in metadata['pipelines']
                          if row['searchType'] == 'sthpw/task'], ['task'])
        self.assertEqual(metadata['processes'], [{'identity': 'PR1', 'label': 'model', 'pipeline': 'demo/assets'}])

    def test_workflow_rejects_nonexistent_group_wrong_task_pipeline_and_invented_process_code(self):
        loaded = json.loads(workflow_request('load', 'demo', 'demo/assets'))
        for properties in ({'assigned_group': 'missing'}, {'supervisor_group': 'missing'},
                           {'task_pipeline': 'demo/assets'}):
            with self.subTest(properties=properties):
                document = copy.deepcopy(loaded['document'])
                document['processSettings']['model']['properties'] = properties
                with self.assertRaises(ValueError):
                    workflow_request('save', 'demo', 'demo/assets', document, loaded['revision'])
        document = copy.deepcopy(loaded['document'])
        document['xml'] = '<pipeline><process name="model" type="action" process_code="invented"/></pipeline>'
        with self.assertRaisesRegex(ValueError, 'generated by TACTIC'):
            workflow_request('save', 'demo', 'demo/assets', document, loaded['revision'])
        self.assertEqual(self.calls, [])

    def test_dangling_pipeline_load_is_lossless_but_save_requires_explicit_repair(self):
        xml = '<pipeline><process name="model" type="action"/><connect from="model" to="texture"/></pipeline>'
        self.tables['sthpw/pipeline'][0]['pipeline'] = xml
        loaded = json.loads(workflow_request('load', 'demo', 'demo/assets'))
        self.assertEqual(loaded['document']['xml'], xml)
        self.assertEqual(self.calls, [])
        with self.assertRaisesRegex(ValueError, 'model → texture'):
            workflow_request('save', 'demo', 'demo/assets', loaded['document'], loaded['revision'])
        self.assertEqual(self.calls, [])
        loaded['document']['xml'] = '<pipeline><process name="model" type="action"/></pipeline>'
        saved = json.loads(workflow_request('save', 'demo', 'demo/assets', loaded['document'], loaded['revision']))
        self.assertNotIn('<connect', saved['document']['xml'])

    def test_created_process_uses_native_code_and_refreshes_process_choices(self):
        from pyasm.biz import Pipeline

        loaded = json.loads(workflow_request('load', 'demo', 'demo/assets'))
        loaded['document']['xml'] = (
            '<pipeline><process name="model" type="action"/>'
            '<process name="review" type="approval"/></pipeline>')
        loaded['document']['processSettings']['review'] = {
            'version': 2, 'properties': {'assigned_group': 'artists', 'task_creation': True}}
        generated = dict(code='SERVER-PROCESS-2', pipeline_code='demo/assets',
                         process='review', workflow={}, description='')
        native_type = type(Pipeline.get_by_code('demo/assets'))
        with patch.object(native_type, 'update_dependencies',
                          side_effect=lambda: self.tables['config/process'].append(generated)) as create:
            saved = json.loads(workflow_request('save', 'demo', 'demo/assets',
                                               loaded['document'], loaded['revision']))
        create.assert_called_once_with()
        self.assertEqual(saved['metadata']['processCodes']['review'], 'SERVER-PROCESS-2')
        self.assertIn({'identity': 'SERVER-PROCESS-2', 'label': 'review', 'pipeline': 'demo/assets'},
                      saved['metadata']['processes'])
        command = next(call[1] for call in self.calls if call[0] == 'process_command')
        self.assertNotIn('process_code', command)
        self.assertEqual(command['properties']['assigned_group'], 'artists')
        self.assertIs(command['properties']['task_creation'], True)

    def test_search_type_catalog_uses_native_project_discovery(self):
        with patch.object(self.project, 'get_search_types',
                          wraps=self.project.get_search_types) as discover:
            result = json.loads(search_types_request('list', 'demo'))
        discover.assert_called_once_with(include_multi_project=True, include_sthpw=True, include_config=True)
        self.assertEqual(result, {
            'catalog': [{'identity': 'demo/asset', 'label': 'Assets',
                         'description': '', 'color': '', 'namespace': 'demo',
                         'table': 'asset', 'database': 'demo', 'projectLocal': True,
                         'linkTable': False, 'manyToMany': False, 'relationships': []}], 'canWrite': True})
        self.assertEqual(self.calls, [])

    def test_search_type_create_add_column_and_edit_keep_physical_data(self):
        created = json.loads(search_types_request('save', 'demo', document={
            'title': 'Episodes', 'hasPipeline': True,
            'columns': [{'name': 'duration', 'type': 'integer'}]}))
        self.assertEqual(created['identity'], 'demo/episodes')
        self.assertIn(('create_type', 'episodes', True), self.calls)
        created['document']['title'] = 'Episode library'
        saved = json.loads(search_types_request('save', 'demo', created['identity'],
                                                created['document'], created['revision']))
        self.assertEqual(saved['document']['title'], 'Episode library')
        self.assertNotIn('retired', saved['document'])
        self.assertIn('duration', self.columns['demo/episodes'])
        self.assertIn({'identity': 'demo/episodes', 'label': 'Episode library',
                       'description': '', 'color': '', 'namespace': 'demo',
                       'table': 'episodes', 'database': 'demo', 'projectLocal': True,
                       'linkTable': False, 'manyToMany': False, 'relationships': []}, saved['catalog'])

    def test_search_type_table_name_is_generated_from_the_title(self):
        for title, table in (
                ('3D Assets', 'type_3d_assets'),
                ('Мои Эпизоды', 'moi_epizody'),
                ('Café Props', 'cafe_props'),
                ('Table', 'type_table')):
            with self.subTest(title=title):
                created = json.loads(search_types_request(
                    'save', 'demo', document={'title': title, 'hasPipeline': False}))
                self.assertEqual(created['identity'], 'demo/' + table)
                self.assertIn(('create_type', table, False), self.calls)

    def test_search_type_creation_rejects_a_client_supplied_table_name(self):
        before = copy.deepcopy(self.tables)
        with self.assertRaisesRegex(ValueError, 'Unknown Search Type setting'):
            search_types_request('save', 'demo', document={
                'title': 'Episodes', 'name': 'manual_name'})
        self.assertEqual(self.tables, before)

    def test_schema_type_creation_returns_native_schema_revision(self):
        loaded = json.loads(schema_request('load', 'demo', 'demo'))
        created = json.loads(search_types_request('save', 'demo', document={
            'title': 'Episodes', 'hasPipeline': True,
            'columns': [{'name': 'duration', 'type': 'integer'}]},
            schema_revision=loaded['revision']))
        schema = json.loads(schema_request('load', 'demo', 'demo'))
        self.assertEqual(created['metadata']['schema'], {
            'xml': schema['document']['xml'], 'revision': schema['revision']})
        self.assertNotEqual(loaded['revision'], schema['revision'])
        self.assertIsNotNone(ET.fromstring(schema['document']['xml']).find(
            "search_type[@name='demo/episodes']"))
        root = ET.fromstring(schema['document']['xml'])
        root.find("search_type[@name='demo/episodes']").set('xpos', '-140')
        saved = json.loads(schema_request('save', 'demo', 'demo',
            {'xml': ET.tostring(root, encoding='unicode')},
            created['metadata']['schema']['revision']))
        self.assertEqual(ET.fromstring(saved['document']['xml']).find(
            "search_type[@name='demo/episodes']").get('xpos'), '-140')

    def test_schema_type_creation_rejects_conflict_before_creating_table(self):
        loaded = json.loads(schema_request('load', 'demo', 'demo'))
        self.tables['sthpw/schema'][0]['schema'] = '<schema changed="yes"/>'
        before = copy.deepcopy(self.tables)
        with self.assertRaisesRegex(ValueError, 'Schema changed'):
            search_types_request('save', 'demo', document={
                'title': 'Episodes'}, schema_revision=loaded['revision'])
        self.assertEqual(self.tables, before)
        self.assertEqual(self.calls, [])

    def test_schema_type_creation_bootstraps_missing_schema_through_rpc(self):
        from thlib import tactic_classes as tc

        self.tables['sthpw/schema'] = []
        schema = json.loads(schema_request('load', 'demo', 'demo'))

        def execute(_path, kwargs):
            namespace = {}
            exec('def procedure():\n' + textwrap.indent(kwargs['code'], '    '), namespace)
            return {'info': {'spt_ret_val': namespace['procedure']()}}

        with patch.object(tc, 'server_start', return_value=SimpleNamespace(execute_python_script=execute)):
            created = tc.execute_procedure_serverside(search_types_request, {
                'action': 'save', 'project_code': 'demo', 'schema_revision': schema['revision'],
                'document': {'title': 'Episodes'}}, project='demo')
        self.assertEqual(created['identity'], 'demo/episodes')
        self.assertEqual(len(self.tables['sthpw/schema']), 1)
        self.assertEqual(created['metadata']['schema']['xml'], self.tables['sthpw/schema'][0]['schema'])

    def test_schema_type_creation_rejects_existing_document_and_permission(self):
        schema = json.loads(schema_request('load', 'demo', 'demo'))
        with self.assertRaisesRegex(ValueError, 'only valid when creating'):
            search_types_request('save', 'demo', 'demo/asset', {'title': 'Changed'},
                                 schema_revision=schema['revision'])
        self.admin = False
        with self.assertRaises(PermissionError):
            search_types_request('save', 'demo', document={'title': 'New'},
                                 schema_revision=schema['revision'])
        self.assertEqual(self.calls, [])

    def test_search_type_retirement_is_rejected_before_any_write(self):
        loaded = json.loads(search_types_request('load', 'demo', 'demo/asset'))
        before = copy.deepcopy(self.tables)
        loaded['document']['retired'] = True
        with self.assertRaisesRegex(ValueError, 'Unknown Search Type setting'):
            search_types_request('save', 'demo', 'demo/asset',
                                 loaded['document'], loaded['revision'])
        self.assertEqual(self.tables, before)
        self.assertEqual(self.calls, [])

    def test_search_type_requests_execute_through_rpc_serializer(self):
        from thlib import tactic_classes as tc

        def execute(_path, kwargs):
            namespace = {}
            exec('def procedure():\n' + textwrap.indent(kwargs['code'], '    '), namespace)
            return {'info': {'spt_ret_val': namespace['procedure']()}}

        with patch.object(tc, 'server_start', return_value=SimpleNamespace(execute_python_script=execute)):
            catalog = tc.execute_procedure_serverside(search_types_request, {
                'action': 'list', 'project_code': 'demo'}, project='demo')
            loaded = tc.execute_procedure_serverside(search_types_request, {
                'action': 'load', 'project_code': 'demo', 'identity': 'demo/asset'}, project='demo')
            loaded['document']['description'] = 'Updated through RPC'
            saved = tc.execute_procedure_serverside(search_types_request, {
                'action': 'save', 'project_code': 'demo', 'identity': 'demo/asset',
                'document': loaded['document'], 'expected_revision': loaded['revision']}, project='demo')
        expected_catalog = copy.deepcopy(catalog['catalog'])
        expected_catalog[0]['description'] = 'Updated through RPC'
        self.assertEqual(expected_catalog, saved['catalog'])
        self.assertEqual(saved['document']['description'], 'Updated through RPC')
        self.assertNotEqual(loaded['revision'], saved['revision'])

    def test_column_validation_happens_before_any_registry_write(self):
        before = copy.deepcopy(self.tables)
        with self.assertRaises(ValueError):
            search_types_request('save', 'demo', document={'title': 'Bad',
                                  'columns': [{'name': 'evil;drop', 'type': 'text'}]})
        self.assertEqual(self.tables, before)
        self.assertEqual(self.calls, [])

    def test_search_type_color_is_native_metadata_and_invalid_color_is_rejected(self):
        loaded = json.loads(search_types_request('load', 'demo', 'demo/asset'))
        loaded['document']['color'] = '#336699'
        saved = json.loads(search_types_request('save', 'demo', 'demo/asset',
                                               loaded['document'], loaded['revision']))
        schema = json.loads(schema_request('load', 'demo', 'demo'))
        self.assertEqual(schema['metadata']['searchTypes'][0]['color'], '#336699')
        self.assertEqual(saved['catalog'][0]['color'], '#336699')
        saved['document']['color'] = 'invalid'
        self.calls.clear()
        with self.assertRaisesRegex(ValueError, '#RRGGBB'):
            search_types_request('save', 'demo', 'demo/asset', saved['document'], saved['revision'])
        self.assertEqual(self.calls, [])

    def test_pipeline_xml_is_persisted_not_only_assigned_to_cached_graph(self):
        loaded = json.loads(workflow_request('load', 'demo', 'demo/assets'))
        loaded['document']['xml'] = '<pipeline description="A &amp; B"><process name="model" type="action" xpos="150"/></pipeline>'
        saved = json.loads(workflow_request('save', 'demo', 'demo/assets',
                                           loaded['document'], loaded['revision']))
        xml = self.tables['sthpw/pipeline'][0]['pipeline']
        self.assertEqual(ET.fromstring(xml).get('description'), 'A & B')
        self.assertEqual(saved['document']['xml'], xml)
        self.assertIn(('dependencies', xml), self.calls)
        self.assertFalse(any(call[0] == 'process_command' for call in self.calls))

    def test_graph_save_keeps_negative_native_positions(self):
        for request, identity, tag in ((workflow_request, 'demo/assets', 'process'),
                                       (schema_request, 'demo', 'search_type')):
            with self.subTest(identity=identity):
                loaded = json.loads(request('load', 'demo', identity))
                root = ET.fromstring(loaded['document']['xml'])
                node = root.find(tag)
                node.set('xpos', '-125.5')
                node.set('ypos', '-70')
                loaded['document']['xml'] = ET.tostring(root, encoding='unicode')
                saved = json.loads(request('save', 'demo', identity,
                                           loaded['document'], loaded['revision']))
                saved_node = ET.fromstring(saved['document']['xml']).find(tag)
                self.assertEqual(saved_node.get('xpos'), '-125.5')
                self.assertEqual(saved_node.get('ypos'), '-70')

    def test_action_code_is_loaded_from_native_script_and_conflicts_are_detected(self):
        self.tables['config/trigger'].append(dict(
            code='TR1', process='PR1', event='process|action', script_path='folder/action', mode='blocking'))
        self.tables['config/custom_script'].append(dict(
            code='SC1', folder='folder', title='action', script='print("native")', language='python'))
        loaded = json.loads(workflow_request('load', 'demo', 'demo/assets'))
        settings = loaded['document']['processSettings']['model']['default']
        self.assertEqual(settings['script'], 'print("native")')
        loaded['document']['processDescriptions']['model'] = 'Updated description'
        workflow_request('save', 'demo', 'demo/assets', loaded['document'], loaded['revision'])
        call = next(call[1] for call in self.calls if call[0] == 'process_command')
        self.assertEqual(call['default']['script_path'], 'folder/action')
        self.assertEqual(call['default']['script'], 'print("native")')
        refreshed = json.loads(workflow_request('load', 'demo', 'demo/assets'))
        self.tables['config/custom_script'][0]['script'] = 'print("another administrator")'
        self.calls.clear()
        with self.assertRaisesRegex(ValueError, 'changed on the server'):
            workflow_request('save', 'demo', 'demo/assets', refreshed['document'], refreshed['revision'])
        self.assertEqual(self.calls, [])

    def test_changing_node_type_invokes_native_process_lifecycle(self):
        loaded = json.loads(workflow_request('load', 'demo', 'demo/assets'))
        loaded['document']['xml'] = '<pipeline><process name="model" type="approval"/></pipeline>'
        workflow_request('save', 'demo', 'demo/assets', loaded['document'], loaded['revision'])
        call = next(call[1] for call in self.calls if call[0] == 'process_command')
        self.assertEqual(call['node_type'], 'approval')

    def test_shared_pipeline_can_be_inspected_but_not_overwritten(self):
        self.tables['sthpw/pipeline'][0]['project_code'] = ''
        loaded = json.loads(workflow_request('load', 'demo', 'demo/assets'))
        self.assertFalse(loaded['canWrite'])
        self.assertTrue(loaded['metadata']['canCreate'])
        self.assertTrue(loaded['catalog'][0]['shared'])
        with self.assertRaises(PermissionError):
            workflow_request('save', 'demo', 'demo/assets', loaded['document'], loaded['revision'])
        self.assertEqual(self.calls, [])

    def test_changed_process_settings_use_native_command_and_preserve_custom_fields(self):
        loaded = json.loads(workflow_request('load', 'demo', 'demo/assets'))
        loaded['document']['processSettings']['model']['default'] = {
            'action': 'create_new', 'language': 'python', 'script': 'print("saved, not run")'}
        workflow_request('save', 'demo', 'demo/assets', loaded['document'], loaded['revision'])
        command = next(call[1] for call in self.calls if call[0] == 'process_command')
        self.assertEqual(command['custom'], {'retained': True})
        self.assertEqual(command['pipeline_code'], 'demo/assets')
        self.assertEqual(command['default']['script'], 'print("saved, not run")')

    def test_concurrent_process_or_trigger_change_rejects_save_before_writes(self):
        loaded = json.loads(workflow_request('load', 'demo', 'demo/assets'))
        self.tables['config/trigger'].append(dict(code='TR1', process='PR1', event='process|action'))
        before = copy.deepcopy(self.tables)
        with self.assertRaises(ValueError):
            workflow_request('save', 'demo', 'demo/assets', loaded['document'], loaded['revision'])
        self.assertEqual(self.tables, before)
        self.assertEqual(self.calls, [])

    def test_used_process_cannot_be_removed_by_xml_editor(self):
        loaded = json.loads(workflow_request('load', 'demo', 'demo/assets'))
        self.tables['sthpw/task'].append(dict(project_code='demo', process='model', search_type='demo/asset'))
        loaded['document']['xml'] = '<pipeline/>'
        with self.assertRaises(ValueError):
            workflow_request('save', 'demo', 'demo/assets', loaded['document'], loaded['revision'])
        self.assertEqual(self.calls, [])

    def test_schema_columns_checked_and_unknown_attributes_survive_save(self):
        loaded = json.loads(schema_request('load', 'demo', 'demo'))
        loaded['document']['xml'] = '<schema custom="yes"><search_type name="demo/asset" xpos="22"/></schema>'
        saved = json.loads(schema_request('save', 'demo', 'demo', loaded['document'], loaded['revision']))
        self.assertEqual(ET.fromstring(saved['document']['xml']).get('custom'), 'yes')
        self.assertNotEqual(saved['revision'], loaded['revision'])
        with self.assertRaises(ValueError):
            schema_request('save', 'demo', 'demo', loaded['document'], loaded['revision'])

    def test_workflow_creation_prepares_catalogs_without_writing_a_pipeline(self):
        before = copy.deepcopy(self.tables)
        result = json.loads(workflow_request('new', 'demo', 'demo/asset'))
        self.assertEqual(result['identity'], '')
        self.assertEqual(result['document'], {})
        self.assertTrue(result['canWrite'])
        self.assertTrue(result['metadata']['canCreate'])
        self.assertIn('demo/asset', [row['identity'] for row in result['metadata']['searchTypes']])
        self.assertEqual(self.tables, before)
        self.assertEqual(self.calls, [])
        with self.assertRaisesRegex(ValueError, 'registered Search Type'):
            workflow_request('new', 'demo', 'demo/missing')

    def test_new_workflow_uses_the_code_generated_by_tactic_on_commit(self):
        document = {
            'name': 'Animation',
            'description': 'Animation workflow',
            'color': '#667788',
            'searchType': 'demo/asset',
            'xml': '<pipeline/>',
            'processSettings': {},
            'processDescriptions': {},
        }

        saved = json.loads(workflow_request(
            'save', 'demo', document=document,
        ))

        self.assertTrue(saved['identity'])
        self.assertEqual(saved['identity'], self.tables['sthpw/pipeline'][-1]['code'])
        self.assertNotIn('pipelineCode', document)
        self.assertEqual(saved['document']['name'], 'Animation')

    def test_workflow_cannot_rebind_its_search_type_or_be_created_without_one(self):
        loaded = json.loads(workflow_request('load', 'demo', 'demo/assets'))
        before = copy.deepcopy(self.tables)
        loaded['document']['searchType'] = 'sthpw/task'
        with self.assertRaisesRegex(ValueError, 'Search Type'):
            workflow_request('save', 'demo', 'demo/assets', loaded['document'], loaded['revision'])
        document = dict(name='Unbound', searchType='', xml='<pipeline/>')
        with self.assertRaisesRegex(ValueError, 'Search Type'):
            workflow_request('save', 'demo', document=document)
        self.assertEqual(self.tables, before)
        self.assertEqual(self.calls, [])

    def test_unbound_native_pipeline_remains_inspectable_but_cannot_be_reassigned(self):
        self.tables['sthpw/pipeline'][0]['search_type'] = ''
        before = copy.deepcopy(self.tables)
        loaded = json.loads(workflow_request('load', 'demo', 'demo/assets'))
        self.assertFalse(loaded['canWrite'])
        self.assertEqual(loaded['document']['searchType'], '')
        self.assertIn('model', loaded['document']['processSettings'])
        loaded['document']['searchType'] = 'demo/asset'
        with self.assertRaisesRegex(ValueError, 'Search Type'):
            workflow_request('save', 'demo', 'demo/assets', loaded['document'], loaded['revision'])
        self.assertEqual(self.tables, before)
        self.assertEqual(self.calls, [])

    def test_process_task_workflows_roundtrip_independently_of_parent_type(self):
        for code in ('demo/model_tasks', 'demo/review_tasks'):
            self.tables['sthpw/pipeline'].append(dict(
                code=code, project_code='demo', search_type='sthpw/task', pipeline='<pipeline/>'))
        self.tables['sthpw/pipeline'][0]['pipeline'] = (
            '<pipeline><process name="model" type="action"/>'
            '<process name="review" type="approval"/></pipeline>')
        self.tables['config/process'].append(dict(
            code='PR2', pipeline_code='demo/assets', process='review', description='',
            workflow={'version': 2, 'node_type': 'approval'}))
        loaded = json.loads(workflow_request('load', 'demo', 'demo/assets'))
        for name in ('model', 'review'):
            loaded['document']['processSettings'][name]['properties'] = {
                'task_pipeline': 'demo/' + name + '_tasks'}
        workflow_request('save', 'demo', 'demo/assets', loaded['document'], loaded['revision'])
        refreshed = json.loads(workflow_request('load', 'demo', 'demo/assets'))
        self.assertEqual(refreshed['document']['searchType'], 'demo/asset')
        for name in ('model', 'review'):
            self.assertEqual(refreshed['document']['processSettings'][name]['properties']['task_pipeline'],
                             'demo/' + name + '_tasks')
        calls = [call[1] for call in self.calls if call[0] == 'process_command']
        self.assertEqual({call['process'] for call in calls}, {'model', 'review'})
        self.assertTrue(all(call['pipeline_code'] == 'demo/assets' for call in calls))

        before = copy.deepcopy(self.tables)
        self.calls.clear()
        refreshed['document']['processSettings']['model']['properties']['task_pipeline'] = 'demo/assets'
        with self.assertRaisesRegex(ValueError, 'task pipeline'):
            workflow_request('save', 'demo', 'demo/assets', refreshed['document'], refreshed['revision'])
        self.assertEqual(self.tables, before)
        self.assertEqual(self.calls, [])

    def test_schema_catalog_contains_only_current_project_and_preserves_inheritance(self):
        original = '<schema parent="base"><search_type name="demo/asset"/></schema>'
        parent = dict(code='base', schema='<schema custom="parent"/>')
        self.tables['sthpw/schema'][0]['schema'] = original
        self.tables['sthpw/schema'].append(copy.deepcopy(parent))
        catalog = [{'identity': 'demo', 'label': 'demo'}]

        listed = json.loads(schema_request('list', 'demo'))
        self.assertEqual(listed['catalog'], catalog)
        loaded = json.loads(schema_request('load', 'demo'))
        self.assertEqual(loaded['identity'], 'demo')
        self.assertEqual(loaded['catalog'], catalog)
        self.assertEqual(loaded['document']['xml'], original)
        loaded['document']['xml'] = original.replace('name="demo/asset"', 'name="demo/asset" xpos="22"')
        saved = json.loads(schema_request('save', 'demo', 'demo', loaded['document'], loaded['revision']))
        self.assertEqual(saved['catalog'], catalog)
        self.assertEqual(ET.fromstring(saved['document']['xml']).get('parent'), 'base')
        self.assertEqual(self.tables['sthpw/schema'][1], parent)

    def test_schema_cannot_select_parent_or_other_project(self):
        self.tables['sthpw/schema'][0]['schema'] = '<schema parent="base"/>'
        self.tables['sthpw/schema'].extend([
            dict(code='base', schema='<schema/>'), dict(code='other', schema='<schema/>')])
        before = copy.deepcopy(self.tables)
        for identity in ('base', 'other'):
            for action in ('load', 'save'):
                with self.subTest(identity=identity, action=action):
                    with self.assertRaisesRegex(ValueError, 'selected project'):
                        schema_request(action, 'demo', identity)
        self.assertEqual(self.tables, before)
        self.assertEqual(self.calls, [])

    def test_security_native_search_filter_without_access_is_valid(self):
        loaded = json.loads(security_request('load', 'demo', 'demo'))
        loaded['document']['groups']['G1']['xml'] = '<rules><rule group="search_filter" search_type="demo/asset" column="code" value="A"/><rule group="process" pipeline="demo/assets" process="model" access="deny" custom="keep"/></rules>'
        saved = json.loads(security_request('save', 'demo', 'demo', loaded['document'], loaded['revision']))
        self.assertIn('custom="keep"', saved['document']['groups']['G1']['xml'])
        self.assertTrue(any(call[0] == 'validate_rules' for call in self.calls))

    def test_security_rejects_cycles_and_concurrent_rules(self):
        self.tables['sthpw/login_group'].append(dict(code='G2', login_group='leads', sub_groups='artists'))
        loaded = json.loads(security_request('load', 'demo', 'demo'))
        loaded['document']['groups']['G1']['subGroups'] = 'leads'
        with self.assertRaises(ValueError):
            security_request('save', 'demo', 'demo', loaded['document'], loaded['revision'])
        self.assertFalse(any(call[0] == 'commit' for call in self.calls))
        self.tables['sthpw/login_group'][0]['access_rules'] = '<rules><rule group="builtin" key="edit" access="deny"/></rules>'
        with self.assertRaises(ValueError):
            security_request('save', 'demo', 'demo', loaded['document'], loaded['revision'])

    def test_rpc_envelopes_keep_identifiers_out_of_reserved_code_argument(self):
        from thlib import tactic_classes as tc
        scripts = []

        def execute(_path, kwargs):
            script = kwargs['code']
            scripts.append(script)
            compile('def procedure():\n' + textwrap.indent(script, '    '),
                    '<administration-procedure>', 'exec')
            return {'info': {'spt_ret_val': '{"ok": true}'}}

        for endpoint in (search_types_request, schema_request, workflow_request, security_request):
            with patch.object(tc, 'server_start', return_value=SimpleNamespace(execute_python_script=execute)):
                result = tc.execute_procedure_serverside(endpoint, {
                    'action': 'load', 'project_code': 'demo', 'identity': 'demo/example'}, project='demo')
            self.assertTrue(result['ok'])
            self.assertTrue(scripts[-1].startswith('def '))
            self.assertIn("identity='demo/example'", scripts[-1])


if __name__ == '__main__':
    unittest.main()
