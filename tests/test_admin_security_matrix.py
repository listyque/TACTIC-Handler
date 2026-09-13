"""Native key semantics, cell-local drafts and multi-group save invariants."""

import ast
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy

from tests.security_matrix_fixture import seed_security
from tests import test_administration_api as native_fixture
from thlib.ui.admin.security import SecurityRulesEditor
from thlib.ui.admin.security_api import security_request
from thlib.ui.admin.security_matrix import compile_group, lookup_keys, resolve


NATIVE = Path(__file__).resolve().parents[1] / '.cache/tactic-source/src/pyasm/security/access_manager.py'


class SecurityMatrixTests(unittest.TestCase):
    def setUp(self):
        self.editor = SecurityRulesEditor(SimpleNamespace(can_administer=True))
        self.addCleanup(self.editor.shutdown)
        seed_security(self.editor)

    def test_duplicate_rules_are_replaced_once_and_extensions_survive(self):
        editor = self.editor
        editor.apply_xml('<rules><!--keep--><rule category="project" code="demo" access="allow"/>'
                         '<rule group="project" code="demo" access="deny"/>'
                         '<rule category="studio" key="x" access="allow" custom="keep"/><extension/></rules>')
        changed = QSignalSpy(editor.matrix.dataChanged)
        editor.matrix.set_allowed(0, 0, False)
        root = ET.fromstring(editor.groupDocument['xml'])
        self.assertEqual(len([rule for rule in root.findall('rule') if rule.get('code') == 'demo']), 1)
        self.assertFalse(editor.matrix.cell_at(0, 0)['checked'])
        self.assertEqual(root.find("rule[@category='studio']").get('custom'), 'keep')
        self.assertIsNotNone(root.find('extension'))
        self.assertIn('<!--keep-->', editor.groupDocument['xml'])
        self.assertEqual(changed.count(), 1)
        self.assertEqual(changed.at(0)[0], editor.matrix.index(0, 0))
        self.assertEqual(editor.matrix.headerData(0, Qt.Horizontal)['identity'], 'G0')

    def test_group_drafts_survive_selection_and_switching_categories(self):
        editor = self.editor
        original = copy.deepcopy(editor.document)
        editor.matrix.set_allowed(1, 1, True)
        editor.select_group('G2')
        editor.add_rule('builtin')
        editor.matrix.filter('link', '', '')
        editor.matrix.set_allowed(0, 1, True)
        self.assertNotEqual(editor.document['groups']['G1'], original['groups']['G1'])
        self.assertNotEqual(editor.document['groups']['G2'], original['groups']['G2'])
        self.assertEqual(editor.document['groups']['G0'], original['groups']['G0'])
        editor.discard()
        self.assertEqual(editor.document, original)

    def test_empty_group_catalog_cannot_create_an_unowned_rule_document(self):
        self.editor._document = {'groups': {}}
        self.editor._metadata['groups'] = []
        self.editor._document_loaded()
        self.editor.apply_xml('<rules/>')
        self.assertEqual(self.editor.document, {'groups': {}})
        self.assertEqual(self.editor.matrix.columnCount(), 0)

    def test_task_wildcard_and_subgroup_grants_cannot_be_overridden_by_fake_denies(self):
        editor = self.editor
        editor.select_group('G1')
        editor.apply_xml('<rules><rule group="process" process="*" pipeline="*" access="allow"/></rules>')
        editor.matrix.filter('tasks', '', '')
        self.assertTrue(editor.matrix.cell_at(0, 1)['locked'])
        self.assertTrue(editor.matrix.cell_at(0, 1)['checked'])
        previous = editor.document['groups']['G1']['xml']
        editor.matrix.set_allowed(0, 1, False)
        self.assertEqual(editor.groupDocument['xml'], previous)
        editor.select_group('G2')
        editor.set_group_field('subGroups', 'Artists 1')
        self.assertTrue(editor.matrix.cell_at(0, 2)['locked'])
        self.assertTrue(editor.matrix.cell_at(0, 2)['checked'])
        editor.set_group_field('subGroups', 'admin')
        editor.matrix.filter('project', '', '')
        self.assertTrue(editor.matrix.cell_at(0, 2)['locked'])
        self.assertTrue(editor.matrix.cell_at(0, 2)['checked'])

    def test_global_defaults_and_project_bound_groups_do_not_leak_between_projects(self):
        editor = self.editor
        editor.select_group('G1')
        editor.set_group_field('accessLevel', 'low')
        self.assertFalse(editor.matrix.cell_at(0, 1)['checked'])
        editor.set_group_field('project', 'demo')
        self.assertTrue(editor.matrix.cell_at(0, 1)['checked'])
        self.assertTrue(editor.matrix.cell_at(0, 1)['locked'])
        editor.set_group_field('project', 'another')
        editor.matrix.filter('link', '', '')
        self.assertFalse(editor.matrix.cell_at(0, 1)['checked'])
        self.assertTrue(editor.matrix.cell_at(0, 1)['locked'])

    @unittest.skipUnless(NATIVE.is_file(), 'Requires the audited TACTIC source checkout')
    def test_projection_agrees_with_actual_native_access_manager(self):
        fixture = native_fixture.AdministrationApiTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.enterContext(patch.object(sys.modules['pyasm.search'], 'SObject', type('SObject', (), {}), create=True))

        class Xml:
            def read_string(self, text):
                self.root = ET.fromstring(text)

            def get_nodes(self, path):
                return self.root.findall(path.removeprefix('rules/'))

            get_attribute = staticmethod(lambda node, name: node.get(name, ''))
            get_attributes = staticmethod(lambda node: node.attrib)

        tree = ast.parse(NATIVE.read_text(encoding='utf-8'))
        body = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'AccessManager']
        namespace = {'Base': object, 'Xml': Xml, 'basestring': str,
                     'Common': SimpleNamespace(get_dict_list=lambda values: sorted(values.items())),
                     'Search': sys.modules['pyasm.search'].Search,
                     'Sudo': SimpleNamespace(is_sudo=lambda: False)}
        exec(compile(ast.Module(body=body, type_ignores=[]), str(NATIVE), 'exec'), namespace)
        native_type = namespace['AccessManager']
        self.editor.apply_xml('''<rules>
            <rule group="project" code="*" access="allow"/>
            <rule group="project" code="demo" access="deny"/>
            <rule group="link" element="*" project="demo" access="allow"/>
            <rule group="link" element="assets" project="demo" access="deny"/>
            <rule group="search_type" code="demo/asset" access="view"/>
            <rule group="search_type" code="demo/asset" project="demo" access="allow"/>
            <rule group="process" process="*" pipeline="*" access="allow"/>
            <rule group="process" process="review" pipeline="demo/tasks" access="deny"/>
            <rule group="gear_menu" submenu="*" label="*" project="demo" access="allow"/>
        </rules>''')
        manager = native_type()
        manager.add_xml_rules(self.editor.groupDocument['xml'])
        compiled = compile_group(self.editor, 'G0')
        for scope, targets in self.editor.metadata['targets'].items():
            if scope == 'search_filter':
                continue
            for target in targets:
                keys = lookup_keys(scope, target['attributes'], 'demo')
                native_keys = [dict(attributes, **({'project': project} if project != '*' else {}))
                               for _, attributes, project in keys]
                native_scope = 'process' if scope == 'tasks' else scope
                expected = manager.get_access(native_scope, native_keys) or 'deny'
                self.assertEqual(resolve(compiled, keys), expected, scope)


class SecurityMatrixApiTests(unittest.TestCase):
    def setUp(self):
        self.fixture = native_fixture.AdministrationApiTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.tables = self.fixture.tables
        self.tables['sthpw/login_group'].append(dict(code='G2', login_group='leads',
            access_level='low', access_rules='<rules/>', sub_groups='', project_code=''))

    def load(self):
        return json.loads(security_request('load', 'demo', 'demo'))

    def test_saves_multiple_group_columns_together_and_rejects_any_stale_revision(self):
        loaded = self.load()
        for data in loaded['document']['groups'].values():
            data['xml'] = '<rules><rule group="project" code="demo" access="allow"/></rules>'
        saved = json.loads(security_request('save', 'demo', 'demo', loaded['document'], loaded['revision']))
        self.assertEqual(saved['document'], loaded['document'])
        self.assertNotEqual(saved['revision'], loaded['revision'])
        before = copy.deepcopy(self.tables)
        with self.assertRaisesRegex(ValueError, 'changed on the server'):
            security_request('save', 'demo', 'demo', loaded['document'], loaded['revision'])
        self.assertEqual(before, self.tables)

    def test_last_invalid_column_prevents_every_group_write(self):
        loaded = self.load()
        loaded['document']['groups']['G1']['xml'] = '<rules><rule group="project" code="demo" access="deny"/></rules>'
        loaded['document']['groups']['G2']['xml'] = '<not-rules/>'
        before = copy.deepcopy(self.tables)
        with self.assertRaisesRegex(ValueError, 'rules root'):
            security_request('save', 'demo', 'demo', loaded['document'], loaded['revision'])
        self.assertEqual(before, self.tables)
        self.assertFalse(any(call[0] == 'commit' for call in self.fixture.calls))

    def test_native_defaults_without_access_are_preserved(self):
        loaded = self.load()
        xml = '<rules><rule group="link" default="allow"/></rules>'
        loaded['document']['groups']['G1']['xml'] = xml
        saved = json.loads(security_request('save', 'demo', 'demo', loaded['document'], loaded['revision']))
        self.assertEqual(saved['document']['groups']['G1']['xml'], xml)

    def test_catalog_uses_native_links_menu_and_distinct_task_pipeline_targets(self):
        configs = {
            'project_view': {'assets': ('Server Assets', 'LinkWdg'), 'folder': ('Work', 'FolderWdg')},
            'folder': {'shots': ('Server Shots', 'LinkWdg'), 'project_view': ('Cycle', 'FolderWdg')},
        }

        def config(_, view):
            values = configs[view]
            return SimpleNamespace(get_element_names=lambda: list(values),
                get_element_attributes=lambda name: {'title': values[name][0]},
                get_display_handler=lambda name: values[name][1], get_display_options=lambda name: {})

        self.enterContext(patch.object(sys.modules['tactic.ui.panel'].SideBarBookmarkMenuWdg, 'get_config', config))
        self.tables['sthpw/pipeline'].append(dict(code='task/asset', search_type='sthpw/task'))
        self.tables['config/process'].extend([
            dict(code='PR2', process='model', pipeline_code='demo/other'),
            dict(code='PR3', process='Review', pipeline_code='task/asset'),
        ])
        targets = self.load()['metadata']['targets']
        self.assertEqual([row['label'] for row in targets['link']], ['', 'Server Assets', 'Work', 'Server Shots', 'Cycle'])
        self.assertEqual(len(targets['process']), 2)
        self.assertEqual(targets['tasks'][1]['attributes'], {'process': 'Review', 'pipeline': 'task/asset'})
        self.assertEqual(targets['gear_menu'][1]['label'], 'Export Selected ...')


if __name__ == '__main__':
    unittest.main()
