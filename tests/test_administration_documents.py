"""Native XML round trips and lifecycle invariants for administration drafts."""

import copy
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

from PySide6.QtCore import QCoreApplication, QObject, Signal

from thlib.ui.admin.documents import GraphDocument, RulesDocument
from thlib.ui.admin.graph_editor import GraphEditor
from thlib.ui.admin.search_types import SearchTypesEditor
from thlib.ui.admin.security import SecurityRulesEditor
from tests.qt_application import gui_test_application


SCHEMA = '''<schema parent="base"><!--keep--><search_type name="demo/asset" xpos="20" ypos="30" custom="yes"/>
<search_type name="demo/shot" xpos="350" ypos="30"/>
<connect from="demo/asset" to="demo/shot" relationship="code" from_col="shot_code" to_col="code" custom="edge"/>
<extension enabled="yes"/></schema>'''
WORKFLOW = '''<pipeline custom="yes"><process name="model" type="manual" xpos="20" ypos="30" color="#6688aa"/>
<process name="review" type="approval" xpos="350" ypos="30"/>
<connect from="model" to="review" from_attr="success" to_attr="input"/></pipeline>'''


class AdministrationDocumentTests(unittest.TestCase):
    def test_graph_roundtrip_keeps_unknown_xml_and_edge_attributes(self):
        graph = GraphDocument('schema', SCHEMA)
        graph.node('demo/asset').set('xpos', '85')
        xml = graph.xml()
        self.assertIn('<!--keep-->', xml)
        self.assertEqual(ET.fromstring(xml).find('extension').get('enabled'), 'yes')
        self.assertEqual(graph.node('demo/asset').get('custom'), 'yes')
        self.assertEqual(graph.edges()[0]['custom'], 'edge')
        self.assertEqual(graph.edges()[0]['from_col'], 'shot_code')

    def test_graph_names_are_identities_not_labels_and_rename_updates_edges(self):
        graph = GraphDocument('workflow', WORKFLOW)
        attrs = dict(graph.node('model').attrib, name='model & lighting')
        graph.set_attributes('model', attrs)
        graph.validate()
        self.assertEqual(graph.edges()[0]['from'], 'model & lighting')
        self.assertIn('model &amp; lighting', graph.xml())
        with self.assertRaises(ValueError):
            graph.add_node('review')

    def test_graph_rejects_incomplete_edges_duplicate_or_nonfinite_nodes(self):
        for xml in ('<pipeline><process name="a"/><process name="a"/></pipeline>',
                    '<pipeline><connect from="missing"/></pipeline>',
                    '<pipeline><process name="a" xpos="nan"/></pipeline>',
                    '<!DOCTYPE pipeline><pipeline/>'):
            with self.subTest(xml=xml), self.assertRaises(ValueError):
                GraphDocument('workflow', xml)

    def test_dangling_workflow_link_loads_losslessly_and_can_be_repaired(self):
        xml = '<pipeline><process name="model"/><connect from="model" to="texture" custom="keep"/></pipeline>'
        graph = GraphDocument('workflow', xml)
        self.assertEqual([row['identity'] for row in graph.nodes()], ['model', 'texture'])
        self.assertTrue(graph.nodes()[1]['referenceOnly'])
        self.assertEqual(graph.nodes()[1]['kind'], 'missing')
        self.assertIsNone(ET.fromstring(graph.xml()).find("process[@name='texture']"))
        self.assertEqual(graph.edges()[0]['custom'], 'keep')
        graph.add_node('texture', 'manual')
        self.assertFalse(graph.nodes()[1]['referenceOnly'])
        self.assertEqual(len(graph.edges()), 1)

    def test_remove_node_removes_only_its_edges(self):
        graph = GraphDocument('workflow', WORKFLOW)
        graph.remove_node('model')
        self.assertEqual([node['identity'] for node in graph.nodes()], ['review'])
        self.assertEqual(graph.edges(), [])
        self.assertEqual(graph.root.get('custom'), 'yes')

    def test_access_rule_edits_preserve_project_default_and_custom_attributes(self):
        rules = RulesDocument('<rules><!--keep--><rule group="process" process="light" '
                              'pipeline="studio/status" project="demo" access="allow" custom="x"/>'
                              '<rule group="sobject" default="true" access="view"/></rules>')
        attrs = {key: value for key, value in rules.records()[0].items() if key != 'ruleIndex'}
        attrs['access'] = 'deny'
        rules.set_rule(0, attrs)
        self.assertEqual(rules.records()[0]['custom'], 'x')
        self.assertEqual(rules.records()[1]['default'], 'true')
        self.assertIn('<!--keep-->', rules.xml())
        with self.assertRaises(ValueError):
            rules.set_rule(0, {'group': 'process', 'access': 'invented'})


class AdministrationLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        self.application = SimpleNamespace(debug_log=None, can_administer=True)
        self.editor = GraphEditor(self.application, 'workflow')
        self.addCleanup(self.editor.shutdown)
        self.editor._can_write = True
        self.editor._project = 'demo'
        self.editor._document = {'xml': WORKFLOW, 'processSettings': {}, 'processDescriptions': {}}
        self.editor._original = copy.deepcopy(self.editor._document)
        self.editor._document_loaded()

    def test_qml_facing_creation_search_type_uses_a_local_notify_signal(self):
        meta_object = self.editor.metaObject()
        property_index = meta_object.indexOfProperty('creationSearchType')
        notify_signal = meta_object.property(property_index).notifySignal()

        self.assertEqual(bytes(notify_signal.methodSignature()), b'selectionChanged()')
        self.assertEqual(notify_signal.enclosingMetaObject().className(), 'GraphEditor')

    def test_pointer_updates_are_local_and_only_committed_on_explicit_save(self):
        with patch('thlib.tactic_classes.execute_procedure_serverside') as rpc:
            self.editor.move_node('model', 123, 89)
            self.editor.select_node('model')
            self.editor.set_process_setting('default', 'script', 'print("hello")')
            self.assertTrue(self.editor.dirty)
            self.assertEqual(self.editor.nodes[0]['nodeX'], 123)
            rpc.assert_not_called()

    def test_multi_selection_moves_and_removes_nodes_atomically(self):
        self.editor.select_nodes(['model', 'review'], 'review')
        self.assertEqual(self.editor.selectedNodes, ['model', 'review'])
        self.assertEqual(self.editor.selectedNode, 'review')
        self.editor.move_nodes([
            {'identity': 'model', 'nodeX': 80, 'nodeY': 90},
            {'identity': 'review', 'nodeX': 410, 'nodeY': 90},
        ])
        self.assertEqual(
            {node['identity']: (node['nodeX'], node['nodeY']) for node in self.editor.nodes},
            {'model': (80.0, 90.0), 'review': (410.0, 90.0)},
        )
        before = self.editor.document['xml']
        self.editor.move_nodes([
            {'identity': 'model', 'nodeX': 100, 'nodeY': 100},
            {'identity': 'missing', 'nodeX': 200, 'nodeY': 200},
        ])
        self.assertEqual(self.editor.document['xml'], before)
        self.editor.clear_selection()
        self.editor.select_nodes(['model', 'review'], 'model')
        self.editor.remove_selected()
        self.assertEqual(self.editor.nodes, [])
        self.assertEqual(self.editor.selectedNodes, [])

    def test_all_automatic_layouts_stage_one_complete_local_change(self):
        for style in ('flow', 'network', 'grid'):
            with self.subTest(style=style):
                self.editor.discard()
                self.editor.arrange_nodes(style)
                positions = {(node['nodeX'], node['nodeY']) for node in self.editor.nodes}
                self.assertEqual(len(positions), 2)
                self.assertTrue(self.editor.dirty)

    def test_add_node_uses_requested_coordinates_and_rejects_invalid_positions_atomically(self):
        original = copy.deepcopy(self.editor.document)
        for x, y in ((float('nan'), 0), (0, float('inf')), (1, None)):
            with self.subTest(x=x, y=y):
                self.editor.add_node('lighting', 'manual', x, y)
                self.assertTrue(self.editor.error)
                self.assertEqual(self.editor.document, original)
        with patch('thlib.tactic_classes.execute_procedure_serverside') as rpc:
            self.editor.add_node('lighting', 'manual', -350.5, 1420.7)
            self.assertEqual(self.editor.error, '')
            self.assertEqual(self.editor.selectedAttributes['xpos'], '-350.5')
            self.assertEqual(self.editor.selectedAttributes['ypos'], '1420.7')
            rpc.assert_not_called()

    def test_process_properties_keep_native_types_and_update_canvas_attributes(self):
        self.editor.select_node('model')
        self.editor.set_process_setting('properties', 'autocreate_task', False)
        self.editor.set_process_setting('properties', 'duration', 3)
        self.editor.set_process_setting('properties', 'color', '#336699')
        self.editor.set_process_setting('properties', 'label', 'Modeling')
        properties = self.editor.processProperties
        self.assertIs(properties['autocreate_task'], False)
        self.assertEqual(properties['duration'], 3)
        self.assertEqual(self.editor.selectedAttributes['color'], '#336699')
        self.assertEqual(self.editor.nodes[0]['label'], 'Modeling')
        self.assertEqual(self.editor.selectedNode, 'model')

    def test_hierarchy_and_status_fields_update_their_native_consumers(self):
        self.editor.select_node('model')
        self.editor.set_attribute('type', 'hierarchy')
        self.editor.set_process_setting('hierarchy', 'subpipeline', 'demo/sub')
        self.assertEqual(self.editor.processSettings['default']['subpipeline_code'], 'demo/sub')
        self.editor.set_attribute('type', 'status')
        self.editor.apply_settings('{"version": 2, "default": {"mapping": "Complete"}, "mapping": "Complete"}')
        self.editor.set_process_setting('default', 'direction', 'output')
        self.editor.set_process_setting('default', 'status', 'review')
        self.assertEqual(self.editor.processSettings['default']['mapping'], '')
        self.assertEqual(self.editor.processSettings['mapping'], '')
        self.assertEqual(self.editor.processSettings['status'], 'review')

    def test_process_code_cannot_be_edited_as_a_regular_attribute(self):
        self.editor.select_node('model')
        self.editor.set_attribute('process_code', 'made_up')
        self.assertNotIn('process_code', self.editor.selectedAttributes)
        self.assertIn('generated by TACTIC', self.editor.error)

    def test_native_node_name_and_nested_settings_are_validated(self):
        self.editor.add_node('  final  ', 'manual')
        self.assertEqual(self.editor.selectedNode, 'final')
        self.assertIn('final', self.editor.document['processSettings'])
        self.editor.apply_settings('{"default":"not an object"}')
        self.assertTrue(self.editor.error)
        self.assertEqual(self.editor.processSettings['node_type'], 'manual')

    def test_invalid_xml_or_attributes_do_not_replace_the_valid_graph(self):
        self.editor.select_node('model')
        previous = self.editor.document['xml']
        self.editor.apply_attributes('{"name":"review"}')
        self.assertTrue(self.editor.error)
        self.assertEqual(self.editor.document['xml'], previous)
        self.editor.apply_xml('<schema/>')
        self.assertEqual(self.editor.document['xml'], previous)

    def test_task_rules_use_native_process_scope_and_preserve_pipeline(self):
        editor = SecurityRulesEditor(self.application)
        self.addCleanup(editor.shutdown)
        editor._project = 'demo'
        editor._can_write = True
        editor._document = {'groups': {'G1': {'xml': '<rules/>', 'accessLevel': 'none', 'project': '', 'subGroups': ''}}}
        editor._document_loaded()
        editor.add_rule('tasks')
        self.assertEqual(editor.rules[0]['group'], 'process')
        self.assertEqual(editor.rules[0]['pipeline'], '*')
        self.assertEqual(editor.rules[0]['project'], 'demo')

    def test_shutdown_disconnects_worker_and_ignores_queued_result(self):
        from thlib.environment import env_inst

        class Worker(QObject):
            result = Signal(object)
            error = Signal(object)
            cancelled = False

            def start(self):
                pass

            def cancel(self):
                self.cancelled = True

        worker = Worker()
        with patch.object(env_inst, 'server_pool', SimpleNamespace(
                is_stopped=False, add_task=lambda *_: worker)):
            self.editor.reload()
        worker.result.emit({'catalog': [{'identity': 'late', 'label': 'Late'}]})
        self.editor.shutdown()
        QCoreApplication.processEvents()
        self.assertTrue(worker.cancelled)
        self.assertEqual(self.editor.catalog, [])
        self.assertIsNone(self.editor._callbacks)

    def test_failed_save_keeps_draft_and_does_not_change_loaded_revision(self):
        self.editor._revision = 'original'
        self.editor.move_node('model', 99, 88)
        self.editor.fail('Server changed')
        self.assertTrue(self.editor.dirty)
        self.assertEqual(self.editor._revision, 'original')
        self.editor.discard()
        self.assertFalse(self.editor.dirty)
        self.assertEqual(self.editor.nodes[0]['nodeX'], 20)

    def test_discarding_a_new_workflow_retains_its_creation_context(self):
        self.editor._loaded = True
        self.editor._document['searchType'] = 'demo/asset'
        self.editor._original = copy.deepcopy(self.editor.document)
        self.editor._document_loaded()
        self.editor.new_document()
        self.assertTrue(self.editor.dirty)

        self.editor.discard()

        self.assertFalse(self.editor.dirty)
        self.assertEqual(self.editor.document, {})
        self.assertEqual(self.editor.creationSearchType, 'demo/asset')
        self.editor.new_document()
        self.assertEqual(self.editor.document['searchType'], 'demo/asset')
        self.assertTrue(self.editor.dirty)
        self.editor.reset('other')
        self.assertEqual(self.editor.creationSearchType, '')

    def test_column_staging_never_drops_existing_columns(self):
        editor = SearchTypesEditor(self.application)
        self.addCleanup(editor.shutdown)
        editor._can_write = True
        editor._document = {'title': 'Assets', 'columns': []}
        editor._metadata = {'columns': {'code': {}}}
        editor.add_column('code', 'text')
        self.assertTrue(editor.error)
        editor.add_column('duration', 'integer')
        self.assertEqual(editor.document['columns'], [{'name': 'duration', 'type': 'integer'}])
        editor.remove_column(0)
        self.assertEqual(editor.metadata['columns'], {'code': {}})

    def test_new_search_type_requires_only_user_facing_details(self):
        editor = SearchTypesEditor(self.application)
        self.addCleanup(editor.shutdown)
        editor._can_write = True
        editor.new_document()
        self.assertNotIn('name', editor.document)
        self.assertFalse(editor.validate_creation_details())
        editor.set_field('title', 'Мои эпизоды')
        self.assertTrue(editor.validate_creation_details())
        self.assertNotIn('name', editor.document)

    def test_refreshing_an_empty_catalog_clears_the_previous_document(self):
        from thlib.environment import env_inst

        class Worker(QObject):
            result = Signal(object)
            error = Signal(object)

            def start(self):
                self.result.emit({'catalog': [], 'canWrite': True})

            def cancel(self):
                pass

        worker = Worker()
        with patch.object(env_inst, 'server_pool', SimpleNamespace(
                is_stopped=False, add_task=lambda *_: worker)):
            self.editor.reload()
            QCoreApplication.processEvents()
        self.assertEqual(self.editor.document, {})
        self.assertEqual(self.editor.nodes, [])
        self.assertEqual(self.editor.identity, '')

    def test_new_workflow_preparation_cannot_survive_reset_failure_or_shutdown(self):
        from thlib.environment import env_inst

        class Worker(QObject):
            result = Signal(object)
            error = Signal(object)
            cancelled = False

            def start(self):
                pass

            def cancel(self):
                self.cancelled = True

        for interruption in ('reset', 'failure', 'shutdown'):
            with self.subTest(interruption=interruption):
                editor = GraphEditor(self.application, 'workflow')
                self.addCleanup(editor.shutdown)
                editor.reset('demo')
                worker = Worker()
                with patch.object(env_inst, 'server_pool', SimpleNamespace(
                        is_stopped=False, add_task=lambda *_: worker)):
                    editor.new_document('demo/asset')
                self.assertTrue(editor.busy)
                if interruption == 'failure':
                    worker.error.emit(({'exception': ValueError('Unavailable')}, worker))
                    QCoreApplication.processEvents()
                    self.assertEqual(editor.error, 'Unavailable')
                else:
                    getattr(editor, interruption)()
                    self.assertTrue(worker.cancelled)
                worker.result.emit(dict(identity='', revision='', document={}, catalog=[],
                                        metadata={'canCreate': True}, canWrite=True))
                QCoreApplication.processEvents()
                self.assertEqual(editor._new_search_type, '')
                self.assertFalse(editor.busy)
                self.assertFalse(editor.dirty)
                self.assertEqual(editor.document, {})

    def test_new_workflow_without_search_type_does_not_start_a_request(self):
        editor = GraphEditor(self.application, 'workflow')
        self.addCleanup(editor.shutdown)
        editor.reset('demo')
        editor._metadata = {'canCreate': True}
        with patch.object(editor, '_request') as request:
            editor.new_document()
            request.assert_not_called()
        self.assertTrue(editor.error)
        self.assertFalse(editor.dirty)
        self.assertEqual(editor.document, {})

    def test_process_rule_queued_results_do_not_survive_parent_reset_or_shutdown(self):
        from thlib.environment import env_inst

        class Worker(QObject):
            result = Signal(object)
            error = Signal(object)
            cancelled = False

            def start(self):
                pass

            def cancel(self):
                self.cancelled = True

        for interruption in ('reset', 'shutdown'):
            with self.subTest(interruption=interruption):
                editor = GraphEditor(self.application, 'workflow')
                self.addCleanup(editor.shutdown)
                editor.reset('demo')
                rules = editor.rulesEditor
                worker = Worker()
                with patch.object(env_inst, 'server_pool', SimpleNamespace(
                        is_stopped=False, add_task=lambda *_: worker)):
                    rules._request('load', 'PR1')
                    worker.result.emit(dict(identity='PR1', revision='old',
                        document={'rules': [{'key': 'old'}]}, canWrite=True))
                    getattr(editor, interruption)()
                    QCoreApplication.processEvents()
                self.assertTrue(worker.cancelled)
                self.assertEqual(rules.document, {})
                self.assertEqual(rules.identity, '')
                self.assertFalse(rules.busy)

    def test_project_metadata_publication_retains_live_stype_and_tabs(self):
        from thlib.environment import env_inst
        from thlib.ui.controllers.connection import ConnectionMixin

        existing = SimpleNamespace(info={'title': 'Old'}, schema='old', pipeline='old')
        project = SimpleNamespace(stypes={'demo/asset': existing})
        existing.project = project
        incoming = SimpleNamespace(info={'title': 'New'}, schema='new', pipeline='new')
        added = SimpleNamespace(info={'title': 'New type'}, schema=None, pipeline=None)
        fresh = SimpleNamespace(get_code=lambda: 'demo', stypes={'demo/asset': incoming, 'demo/new': added},
                                workflow='workflow', views=SimpleNamespace())
        tab = SimpleNamespace(stype=existing, selected_keys=['A'], scroll_y=280)
        application = SimpleNamespace(_current_project_code='demo', navigation_model=Mock(),
                                      workspace_state=Mock(), apply_cache_invalidation=Mock(),
                                      project_state_changed=Mock(), _sessions={'keep': tab})
        with patch.object(env_inst, 'projects', {'demo': project}):
            ConnectionMixin.apply_project_metadata(application, fresh, ['navigation'])
        self.assertIs(project.stypes['demo/asset'], existing)
        self.assertIs(tab.stype, existing)
        self.assertEqual(tab.stype.info['title'], 'New')
        self.assertEqual(tab.selected_keys, ['A'])
        self.assertEqual(tab.scroll_y, 280)
        self.assertIs(added.project, project)
        application.workspace_state.load_project.assert_called_once_with(project)
        application.navigation_model.replace.assert_called_once_with(['navigation'])


if __name__ == '__main__':
    unittest.main()
