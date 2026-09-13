"""Search Type summaries, native destinations and real editor interaction."""

import copy
import json
import os
import time
import traceback
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QCoreApplication, QObject, QPoint, QPointF, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QImage, QWheelEvent
from PySide6.QtTest import QSignalSpy, QTest

from thlib.environment import env_inst
from thlib.ui.admin.search_types import build_local_relationship_graph
from thlib.ui.admin.search_types_api import search_types_request
from tests import test_administration_api as api_fixture
from tests import test_administration_qml as ui_fixture
from tests import test_sidebar_editor_qml as sidebar_fixture
from tests.profile_ui_responsiveness import frame


class SearchTypeSummaryApiTests(unittest.TestCase):
    def setUp(self):
        self.api = api_fixture.AdministrationApiTests()
        self.api.setUp()
        self.addCleanup(self.api.doCleanups)

    def test_project_membership_uses_native_database_not_namespace(self):
        self.api.tables['sthpw/search_object'] += [
            dict(code='library/prop', title='Props', namespace='library', table_name='prop',
                 database='{project}'),
            dict(code='demo/shared', title='Shared', namespace='demo', table_name='shared',
                 database='sthpw'),
            dict(code='config/naming', title='Naming', namespace='config', table_name='naming',
                 database='{project}'),
            dict(code='library/local', title='Local', namespace='library', table_name='local',
                 database='demo'),
        ]
        rows = json.loads(search_types_request('list', 'demo'))['catalog']
        self.assertEqual({row['identity'] for row in rows if row['projectLocal']},
                         {'demo/asset', 'library/prop', 'config/naming', 'library/local'})
        self.assertEqual(self.api.count_queries, [])
        self.api.project_code = 'admin'
        rows = json.loads(search_types_request('list', 'admin'))['catalog']
        self.assertTrue(next(row for row in rows if row['identity'] == 'demo/shared')['projectLocal'])
        self.assertFalse(next(row for row in rows if row['identity'] == 'library/local')['projectLocal'])
        self.assertEqual(self.api.calls, [])

    def test_schema_distinguishes_many_to_many_endpoints_and_link_table_without_name_guesses(self):
        self.api.tables['sthpw/search_object'] += [
            dict(code=code, title=code, namespace='demo', table_name=code.split('/')[1],
                 database='{project}')
            for code in ('demo/shot', 'demo/association', 'demo/fake_in_shot')]
        self.api.tables['sthpw/schema'][0]['schema'] = '''<schema parent="base">
            <search_type name="demo/asset"/><search_type name="demo/shot"/>
            <connect from="demo/asset" to="demo/shot" relationship="instance"
                     instance_type="demo/association"/>
        </schema>'''
        self.api.tables['sthpw/schema'].append(dict(code='base', schema='''<schema>
            <connect from="demo/shot" to="demo/asset" type="hierarchy" relationship="code"
                     from_col="asset_code" to_col="code"/>
        </schema>'''))
        rows = {row['identity']: row for row in json.loads(search_types_request('list', 'demo'))['catalog']}
        self.assertTrue(rows['demo/asset']['manyToMany'])
        self.assertFalse(rows['demo/asset']['linkTable'])
        self.assertTrue(rows['demo/association']['linkTable'])
        self.assertFalse(rows['demo/fake_in_shot']['linkTable'])
        self.assertEqual(rows['demo/fake_in_shot']['relationships'], [])
        self.assertEqual({row['schema'] for row in rows['demo/asset']['relationships']}, {'demo', 'base'})
        loaded = json.loads(search_types_request('load', 'demo', 'demo/asset'))
        self.assertEqual(loaded['metadata']['relationships'], rows['demo/asset']['relationships'])
        self.assertEqual(self.api.calls, [])

    def test_schema_native_many_to_many_attribute_variants_and_node_marker(self):
        for attributes in ('relationship="many_to_many" instance_type="demo/asset"',
                           'type="many_to_many" instance_type="demo/asset"',
                           'relationship="instance" path="demo/asset"'):
            with self.subTest(attributes=attributes):
                self.api.tables['sthpw/schema'][0]['schema'] = (
                    '<schema><connect from="demo/a" to="demo/b" ' + attributes + '/></schema>')
                row = json.loads(search_types_request('list', 'demo'))['catalog'][0]
                self.assertTrue(row['linkTable'])
                self.assertTrue(row['manyToMany'])
        self.api.tables['sthpw/schema'][0]['schema'] = (
            '<schema><search_type name="demo/asset" type="instance"/></schema>')
        row = json.loads(search_types_request('list', 'demo'))['catalog'][0]
        self.assertTrue(row['linkTable'])

    def test_summary_counts_all_objects_and_only_related_project_or_shared_pipelines(self):
        self.api.tables['demo/asset'] = [
            {'code': 'A1'}, {'code': 'A2', 's_status': ''}, {'code': 'A3', 's_status': 'retired'}]
        self.api.columns['demo/asset'].update(
            s_status={'data_type': 'text'}, pipeline_code={'data_type': 'text'})
        self.api.tables['sthpw/pipeline'] += [
            dict(code='shared', name='Shared', search_type='demo/asset',
                 pipeline='<pipeline><process name="review"/><process name="done"/></pipeline>'),
            dict(code='foreign', search_type='demo/asset', project_code='elsewhere'),
            dict(code='other', search_type='demo/shot', project_code='demo'),
        ]
        result = json.loads(search_types_request('load', 'demo', 'demo/asset'))
        self.assertEqual(result['metadata']['summary'], {
            'total': 3, 'active': 2, 'retired': 1, 'fields': 3, 'pipelines': 2, 'processes': 3})
        self.assertTrue(result['metadata']['hasPipeline'])
        self.assertEqual([row['identity'] for row in result['metadata']['pipelines']],
                         ['demo/assets', 'shared'])
        self.assertTrue(result['metadata']['pipelines'][1]['shared'])
        self.assertEqual(self.api.count_queries, [
            ('demo/asset', True, []), ('demo/asset', True, [('s_status', ['retired'], '=')])])
        self.assertEqual(result['metadata']['searchKey'], 'sthpw/search_object?code=demo/asset')
        self.assertEqual(self.api.calls, [])

    def test_system_projects_include_system_and_config_types_and_count_without_retirement_column(self):
        from pyasm.search import Search

        registry = self.api.tables['sthpw/search_object']
        for code, title in (('sthpw/search_object', 'Search Types'), ('config/process', 'Processes')):
            namespace, table = code.split('/')
            registry.append(dict(code=code, title=title, namespace=namespace, table_name=table))
            self.api.columns[code] = {'code': {'data_type': 'text'}}

        def discover(**options):
            # The native Project method excludes these namespaces unless the
            # caller enables them, even in admin/sthpw projects.
            return [row for row in Search('sthpw/search_object').get_sobjects()
                    if options.get('include_' + row.get_value('namespace'), False)]

        with patch.object(self.api.project, 'get_search_types', side_effect=discover):
            for project in ('admin', 'sthpw'):
                self.api.project_code = project
                result = json.loads(search_types_request('list', project))
                self.assertEqual({row['identity'] for row in result['catalog']},
                                 {'sthpw/search_object', 'config/process'})
                loaded = json.loads(search_types_request('load', project, 'sthpw/search_object'))
                self.assertEqual(loaded['metadata']['summary']['total'], len(registry))
                self.assertEqual(loaded['metadata']['summary']['retired'], 0)
                self.assertFalse(loaded['metadata']['hasPipeline'])
        self.assertTrue(all(not filters for _, _, filters in self.api.count_queries))


class SearchTypeRelationshipGraphTests(unittest.TestCase):
    def setUp(self):
        self.catalog = [
            {'identity': 'demo/asset', 'label': 'Assets', 'table': 'asset',
             'color': '#44aacc', 'linkTable': False},
            {'identity': 'demo/shot', 'label': 'Shots', 'table': 'shot',
             'color': '#cc8844', 'linkTable': False},
            {'identity': 'demo/association', 'label': 'Asset shots',
             'table': 'asset_shot', 'color': '', 'linkTable': True},
            {'identity': 'demo/unrelated', 'label': 'Unrelated', 'table': 'unrelated',
             'color': '', 'linkTable': False},
        ]

    def test_endpoint_projection_contains_only_its_local_many_to_many_chain(self):
        graph = build_local_relationship_graph('demo/asset', self.catalog, [
            {'from': 'demo/asset', 'to': 'demo/shot', 'relationship': 'instance',
             'instanceType': 'demo/association', 'manyToMany': True, 'schema': 'demo'},
            {'from': 'demo/unrelated', 'to': 'demo/shot', 'relationship': 'code',
             'instanceType': '', 'manyToMany': False, 'schema': 'demo'},
        ])

        nodes = {node['identity']: node for node in graph['nodes']}
        self.assertEqual(graph['center'], 'demo/asset')
        self.assertEqual(set(nodes), {'demo/asset', 'demo/association', 'demo/shot'})
        self.assertEqual(nodes['demo/asset']['label'], 'Assets')
        self.assertEqual(nodes['demo/asset']['color'], '#44aacc')
        self.assertEqual(nodes['demo/association']['kind'], 'instance')
        self.assertLess(nodes['demo/asset']['nodeX'], nodes['demo/association']['nodeX'])
        self.assertLess(nodes['demo/association']['nodeX'], nodes['demo/shot']['nodeX'])
        self.assertEqual(
            [(edge['from'], edge['to']) for edge in graph['edges']],
            [('demo/asset', 'demo/association'), ('demo/association', 'demo/shot')],
        )

    def test_link_table_is_centered_between_endpoints_and_duplicate_edges_collapse(self):
        relationship = {
            'from': 'demo/asset', 'to': 'demo/shot', 'relationship': 'instance',
            'instanceType': 'demo/association', 'manyToMany': True, 'schema': 'demo',
        }
        inherited = dict(relationship, schema='base')
        graph = build_local_relationship_graph(
            'demo/association', self.catalog, [relationship, inherited])

        nodes = {node['identity']: node for node in graph['nodes']}
        self.assertLess(nodes['demo/asset']['nodeX'], nodes['demo/association']['nodeX'])
        self.assertLess(nodes['demo/association']['nodeX'], nodes['demo/shot']['nodeX'])
        self.assertEqual(len(graph['edges']), 2)
        self.assertTrue(all(edge['label'].startswith('M:N') for edge in graph['edges']))


class AdminSearchTypeEditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ui_fixture.AdministrationQmlTests.setUpClass()

    def setUp(self):
        self.ui = ui_fixture.AdministrationQmlTests()
        self.ui.setUp()
        self.addCleanup(self.ui.doCleanups)
        self.window = self.ui.window
        self.admin = self.ui.admin
        self.editor = self.admin.typesEditor
        self.editor._metadata.update(
            searchKey='sthpw/search_object?code=demo/asset',
            summary=dict(total=230, active=215, retired=15, fields=24, pipelines=1, processes=8),
            hasPipeline=True, pipelines=[dict(identity='demo/assets', label='Asset workflow',
                description='Model and review', shared=False, color='#54a878', processCount=8)])
        self.editor._document['previewPath'] = ''
        self.editor._original = copy.deepcopy(self.editor.document)
        self.editor.stateChanged.emit()
        self.window.resize(1400, 940)
        self.ui.click('adminSection_types')
        self.enterContext(patch.object(self.admin, '_refresh_pending_metadata'))
        self.checkin = Mock()
        self.editor.attach_checkin_controller(self.checkin)

    def item(self, name):
        return self.ui.item(name)

    def reveal(self, name):
        item = self.item(name)
        parent = item.parentItem()
        while parent is not None:
            if parent.inherits('QQuickFlickable'):
                top = item.mapToItem(parent, QPointF()).y()
                if top < 0 or top + item.height() > parent.height():
                    parent.setProperty('contentY', max(0, min(
                        parent.property('contentHeight') - parent.height(),
                        parent.property('contentY') + top - 8)))
                    frame(self.window)
            parent = parent.parentItem()
        return item

    def click(self, name):
        self.reveal(name)
        self.ui.click(name)

    def image(self):
        from thlib.environment import env_mode
        path = Path(env_mode.current_path) / 'search_type_preview.png'
        image = QImage(120, 80, QImage.Format_RGB32)
        image.fill(QColor('#54a878'))
        self.assertTrue(image.save(str(path)))
        return path

    def worker(self, function):
        class Worker(QObject):
            result = Signal(object)
            error = Signal(object)
            cancelled = False

            def start(inner):
                try:
                    result = function()
                except Exception as error:
                    inner.error.emit(({'exception': error, 'stacktrace': traceback.format_exc()}, inner))
                else:
                    inner.result.emit(result)

            def cancel(inner):
                inner.cancelled = True

        return Worker()

    def test_field_staging_validates_name_and_type_before_changing_draft(self):
        for name, kind in (('Wrong Name', 'text'), ('1name', 'text'),
                           ('code ', 'text'), ('valid', 'made_up'), ('', 'text')):
            with self.subTest(name=name, kind=kind):
                self.assertFalse(self.editor.add_column(name, kind))
                self.assertEqual(self.editor.document['columns'], [])
                self.assertTrue(self.editor.error)
        self.assertTrue(self.editor.add_column(' duration_minutes ', 'integer'))
        self.assertEqual(self.editor.document['columns'], [{'name': 'duration_minutes', 'type': 'integer'}])
        self.assertFalse(self.editor.add_column('duration_minutes ', 'text'))
        self.assertEqual(len(self.editor.document['columns']), 1)

    def test_creation_explains_automatic_fields_separately_from_additions(self):
        self.click('adminCreateDocument')
        self.click('segmentedButtonSegment_entity_fields')
        defaults = self.item('adminAutomaticFieldNames')
        self.assertEqual(defaults.property('text').split(', '), [
            'id', 'code', 'name', 'description', 'keywords', 'login',
            'timestamp', 'data', 's_status', 'relative_dir'])
        self.assertIn('автоматически', self.item('adminAutomaticFields').property('description'))
        self.assertEqual(self.editor.document['columns'], [])
        self.assertFalse(any(item.objectName() == 'adminExistingFieldsFilter' and item.isVisible()
                             for item in sidebar_fixture.SidebarEditorQmlTests.descendants(
                                 self.window.contentItem())))
        pipeline = self.item('adminAutomaticPipelineField')
        self.assertEqual(pipeline.property('text'), self.editor.tr(
            'pipeline_code will also be created: pipeline support is enabled.'))
        with patch('thlib.tactic_classes.execute_procedure_serverside') as rpc:
            self.click('segmentedButtonSegment_entity_details')
            self.click('adminSearchTypeHasPipeline')
            self.click('segmentedButtonSegment_entity_fields')
            self.assertEqual(pipeline.property('text'), self.editor.tr(
                'pipeline_code will not be created: pipeline support is disabled.'))
            self.click('segmentedButtonSegment_entity_details')
            checkbox = self.reveal('adminSearchTypeHasPipeline')
            checkbox.forceActiveFocus()
            QTest.keyClick(self.window, Qt.Key_Space)
            frame(self.window)
            self.click('segmentedButtonSegment_entity_fields')
            self.assertEqual(pipeline.property('text'), self.editor.tr(
                'pipeline_code will also be created: pipeline support is enabled.'))
            rpc.assert_not_called()
        for width, height in ((900, 620), (1400, 940)):
            self.window.resize(width, height)
            frame(self.window)
            viewport = self.item('adminSearchTypeForm')
            viewport.setProperty('contentY', 0)
            frame(self.window)
            for name in ('adminAutomaticFieldNames', 'adminAutomaticPipelineField'):
                label = self.item(name)
                self.assertGreaterEqual(label.mapToItem(viewport, QPointF()).x(), 0)
                self.assertLessEqual(label.mapToItem(viewport, QPointF(label.width(), 0)).x(),
                                     viewport.width() - 16)
                self.assertGreaterEqual(label.height(), label.property('contentHeight'))
            output = os.environ.get('SEARCH_TYPE_SCREENSHOTS')
            if output:
                Path(output).mkdir(parents=True, exist_ok=True)
                self.window.grabWindow().save(str(Path(output) / ('default_fields_%s.png' % width)))
        self.assertEqual(self.editor.document['columns'], [])
        self.assertEqual(self.ui.fixture.warnings, [])

    def test_project_checkbox_filters_locally_and_retains_draft(self):
        self.editor._catalog = [
            dict(identity='library/asset', label='Assets', namespace='library', projectLocal=True,
                 table='asset', manyToMany=True, linkTable=False, relationships=[]),
            dict(identity='demo/link', label='Associations', namespace='demo', projectLocal=True,
                 table='link', manyToMany=True, linkTable=True, relationships=[]),
            dict(identity='sthpw/login', label='Users', namespace='sthpw', projectLocal=False,
                 table='login', manyToMany=False, linkTable=False, relationships=[]),
        ]
        self.editor.stateChanged.emit()
        frame(self.window)
        catalog = self.item('adminSearchTypesList')
        self.assertEqual(catalog.property('count'), 2)
        self.editor.set_field('description', 'Keep this draft')
        with patch.object(self.editor, '_request') as request:
            self.click('adminSearchTypesProjectOnly')
            self.assertEqual(catalog.property('count'), 3)
            checkbox = self.item('adminSearchTypesProjectOnly')
            checkbox.forceActiveFocus()
            frame(self.window)
            QTest.keyClick(self.window, Qt.Key_Space)
            frame(self.window)
            self.assertEqual(catalog.property('count'), 2)
            self.window.resize(900, 620)
            frame(self.window)
            point = checkbox.mapToScene(QPointF(12, checkbox.height() / 2)).toPoint()
            device = QTest.createTouchDevice()
            QTest.touchEvent(self.window, device).press(0, point, self.window).commit()
            QTest.touchEvent(self.window, device).release(0, point, self.window).commit()
            frame(self.window)
            self.assertEqual(catalog.property('count'), 3)
            request.assert_not_called()
        self.assertEqual(self.editor.document['description'], 'Keep this draft')
        self.assertIn('M:N', self.item('adminSearchTypeRole_library/asset').property('text'))
        self.assertIn('M:N', self.item('adminSearchTypeRole_demo/link').property('text'))
        self.assertEqual(self.ui.fixture.warnings, [])

    def test_config_filter_combines_with_project_and_text_without_reloading(self):
        self.editor._catalog = [
            dict(identity='demo/asset', label='Assets', namespace='demo', projectLocal=True),
            dict(identity='demo/configuration', label='Configuration objects', namespace='demo', projectLocal=True),
            dict(identity='config/naming', label='Naming', namespace='config', projectLocal=True),
            dict(identity='sthpw/login', label='Users', namespace='sthpw', projectLocal=False),
        ]
        self.editor.stateChanged.emit()
        frame(self.window)
        catalog = self.item('adminSearchTypesList')
        self.assertTrue(self.item('adminSearchTypesProjectOnly').property('checked'))
        self.assertTrue(self.item('adminSearchTypesHideConfig').property('checked'))
        self.assertEqual(catalog.property('count'), 2)
        self.editor.set_field('description', 'Keep this draft')
        with patch.object(self.editor, '_request') as request:
            self.click('adminSearchTypesHideConfig')
            self.assertEqual(catalog.property('count'), 3)
            self.click('adminSearchTypesProjectOnly')
            self.assertEqual(catalog.property('count'), 4)
            self.editor.stateChanged.emit()
            frame(self.window)
            self.assertEqual(catalog.property('count'), 4)
            self.click('adminSearchTypesHideConfig')
            self.click('adminSearchTypesProjectOnly')
            self.assertEqual(catalog.property('count'), 2)
            checkbox = self.item('adminSearchTypesHideConfig')
            for width, height in ((900, 620), (1400, 940)):
                self.window.resize(width, height)
                frame(self.window)
                point = checkbox.mapToScene(QPointF())
                self.assertGreaterEqual(point.x(), 0)
                self.assertLessEqual(point.x() + checkbox.width(), width)
                self.assertLessEqual(point.y() + checkbox.height(), height)
                checkbox.forceActiveFocus()
                frame(self.window)
                QTest.keyClick(self.window, Qt.Key_Space)
                frame(self.window)
                self.assertEqual(catalog.property('count'), 3)
                device = QTest.createTouchDevice()
                center = checkbox.mapToScene(QPointF(12, checkbox.height() / 2)).toPoint()
                QTest.touchEvent(self.window, device).press(0, center, self.window).commit()
                QTest.touchEvent(self.window, device).release(0, center, self.window).commit()
                frame(self.window)
                self.assertEqual(catalog.property('count'), 2)
            self.click('adminSearchTypeFilter')
            for character in 'configuration':
                QTest.keyClick(self.window, character)
            frame(self.window)
            self.assertEqual(catalog.property('count'), 1)
            self.assertTrue(self.item('adminSearchType_demo/configuration').isVisible())
            request.assert_not_called()
        self.assertEqual(self.editor.identity, 'demo/asset')
        self.assertEqual(self.editor.document['description'], 'Keep this draft')
        self.assertEqual(self.ui.fixture.warnings, [])

    def test_field_form_localized_examples_search_and_scrollbar_gutter_narrow_wide(self):
        self.editor._metadata['columns'] = {
            'code': {'data_type': 'character varying', 'character_maximum_length': 256,
                     'is_nullable': 'NO'},
            'duration_minutes': {'data_type': 'integer'},
            **{'extra_%s' % n: {'data_type': 'text'} for n in range(35)},
        }
        self.editor.stateChanged.emit()
        self.click('segmentedButtonSegment_entity_fields')
        viewport = self.item('adminSearchTypeForm')
        for width, height in ((900, 620), (1400, 940)):
            with self.subTest(width=width):
                self.window.resize(width, height)
                viewport.setProperty('contentY', 0)
                frame(self.window)
                self.assertGreater(viewport.property('contentHeight'), viewport.height())
                for name in ('adminNewColumnName', 'adminNewColumnType', 'adminStageColumn',
                             'adminNewColumnExample'):
                    item = self.reveal(name)
                    left = item.mapToItem(viewport, QPointF()).x()
                    right = item.mapToItem(viewport, QPointF(item.width(), 0)).x()
                    self.assertGreaterEqual(left, 0)
                    self.assertLessEqual(right, viewport.width() - 16)
                combo = self.reveal('adminNewColumnType')
                for index, example in ((0, 'Пожарная машина'), (1, 'Опишите сцену'),
                                       (2, '3'), (3, '12.5'), (4, 'Да / Нет'), (5, 'Сегодня')):
                    self.ui.fixture.choose_combo_option(self.window, combo, index)
                    self.assertIn(example, self.item('adminNewColumnExample').property('text'))
                viewport.setProperty('contentY', 0)
                frame(self.window)
                output = os.environ.get('SEARCH_TYPE_SCREENSHOTS')
                if output:
                    Path(output).mkdir(parents=True, exist_ok=True)
                    self.window.grabWindow().save(str(Path(output) / ('fields_%s.png' % width)))
        self.window.requestActivate()
        frame(self.window)
        self.click('adminExistingFieldsFilter')
        self.assertTrue(self.item('adminExistingFieldsFilter').hasActiveFocus())
        for character in 'duration':
            QTest.keyClick(self.window, character)
        frame(self.window)
        self.assertEqual(self.item('adminExistingFieldsFilter').property('text'), 'duration')
        self.assertIn('Целое число', self.item('adminExistingField_duration_minutes').property('description'))
        visible_names = {item.objectName() for item in sidebar_fixture.SidebarEditorQmlTests.descendants(
            viewport) if item.isVisible() and item.objectName().startswith('adminExistingField_')}
        self.assertEqual(visible_names, {'adminExistingField_duration_minutes'})
        self.window.resize(900, 620)
        viewport.setProperty('contentY', 0)
        frame(self.window)
        self.assertGreater(viewport.property('contentHeight'), viewport.height())
        point = viewport.mapToScene(QPointF(viewport.width() / 2, viewport.height() / 2))
        stopped = QSignalSpy(viewport.movementEnded)
        event = QWheelEvent(point, self.window.mapToGlobal(point.toPoint()), QPoint(), QPoint(0, -1200),
                            Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False)
        event.setTimestamp(time.monotonic_ns() // 1_000_000)
        QCoreApplication.sendEvent(self.window, event)
        if viewport.property('moving'):
            self.assertTrue(stopped.wait(2000))
        frame(self.window)
        self.assertGreater(viewport.property('contentY'), 0)
        self.assertEqual(self.ui.fixture.warnings, [])

    def test_summary_explains_native_relationship_and_link_table(self):
        self.editor._metadata.update(
            database='demo', projectLocal=True, linkTable=True, manyToMany=True,
            relationships=[dict(schema='demo', manyToMany=True, relationship='instance',
                instanceType='demo/association', **{'from': 'demo/asset', 'to': 'demo/shot'})])
        self.editor._update_relationship_graph()
        self.editor.stateChanged.emit()
        frame(self.window)
        relation = self.reveal('adminSearchTypeRelation_0')
        self.assertIn('M:N', relation.property('description'))
        self.assertIn('Связующая таблица: demo/association', relation.property('description'))
        self.assertIn('Схема: demo', relation.property('description'))
        graph = self.item('adminSearchTypeRelationshipGraph')
        nodes = graph.property('nodes')
        nodes = nodes.toVariant() if hasattr(nodes, 'toVariant') else nodes
        self.assertEqual(
            {node['identity'] for node in nodes},
            {'demo/asset', 'demo/association', 'demo/shot'},
        )
        self.assertTrue(graph.property('readOnly'))
        self.assertFalse(graph.property('selectionEnabled'))
        self.assertEqual(self.ui.fixture.warnings, [])

    def test_fields_real_input_examples_and_invalid_name_retention(self):
        self.click('segmentedButtonSegment_entity_fields')
        field = self.reveal('adminNewColumnName')
        self.ui.fixture.click(self.window, field)
        for character in 'Wrong Name':
            QTest.keyClick(self.window, character)
        self.click('adminStageColumn')
        self.assertEqual(field.property('text'), 'Wrong Name')
        self.assertTrue(self.editor.error)
        self.assertEqual(self.editor.document['columns'], [])
        self.ui.fixture.click(self.window, self.reveal('adminNewColumnName'))
        QTest.keyClick(self.window, Qt.Key_A, Qt.ControlModifier)
        for character in 'duration_minutes':
            QTest.keyClick(self.window, character)
        combo = self.reveal('adminNewColumnType')
        self.ui.fixture.choose_combo_option(self.window, combo, 2)
        self.assertEqual(combo.property('currentValue'), 'integer')
        self.assertIn('duration_minutes', self.item('adminNewColumnExample').property('text'))
        self.click('adminStageColumn')
        self.assertEqual(field.property('text'), '')
        self.assertEqual(self.editor.document['columns'], [{'name': 'duration_minutes', 'type': 'integer'}])
        self.click('adminRemoveColumn_duration_minutes')
        self.assertEqual(self.editor.document['columns'], [])
        self.assertEqual(self.ui.fixture.warnings, [])

    def test_color_picker_mouse_keyboard_reset_and_draft_retention(self):
        self.click('segmentedButtonSegment_entity_details')
        self.click('adminSearchTypeColor_choose')
        field = self.item('adminSearchTypeColor')
        dialog = field.findChild(QObject, 'adminSearchTypeColor_dialog')
        self.assertTrue(dialog.property('visible'))
        self.click('adminSearchTypeColor_dialog_hex')
        QTest.keyClick(self.window, Qt.Key_A, Qt.ControlModifier)
        for character in '#c95873':
            QTest.keyClick(self.window, character)
        label = QCoreApplication.translate('QQuickDialogButtonBox', 'OK')
        button = next(item for item in sidebar_fixture.SidebarEditorQmlTests.descendants(self.window.contentItem())
                      if item.isVisible() and item.inherits('QQuickAbstractButton')
                      and item.property('text') == label)
        self.ui.fixture.click(self.window, button)
        self.assertEqual(self.editor.document['color'], '#c95873')
        self.click('adminSection_schema')
        self.click('adminSection_types')
        self.assertEqual(self.item('adminSearchTypeColor').property('value'), '#c95873')
        button = self.reveal('adminSearchTypeResetColor')
        button.forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Space)
        frame(self.window)
        self.assertEqual(self.editor.document['color'], '')
        self.assertEqual(self.ui.fixture.warnings, [])

    def test_summary_and_workflow_real_touch_navigation_preserve_type_draft(self):
        self.assertEqual(self.item('adminSearchTypeCount_total').property('text'), '230')
        self.assertEqual(self.item('adminSearchTypeCount_retired').property('text'), '15')
        self.editor.set_field('description', 'Pending type description')
        self.click('segmentedButtonSegment_entity_workflows')
        button = self.reveal('adminSearchTypeWorkflow_demo/assets')
        point = button.mapToScene(QPointF(button.width() / 2, button.height() / 2)).toPoint()
        device = QTest.createTouchDevice()
        sequence = QTest.touchEvent(self.window, device, autoCommit=False)
        sequence.press(0, point, self.window).commit()
        frame(self.window)
        sequence.release(0, point, self.window).commit()
        frame(self.window)
        self.assertEqual(self.admin.section, 'workflow')
        self.assertEqual(self.admin.workflowEditor.identity, 'demo/assets')
        self.assertEqual(self.editor.document['description'], 'Pending type description')
        self.assertTrue(self.editor.dirty)
        self.assertEqual(self.ui.fixture.warnings, [])

    def test_workflow_navigation_loads_exact_pipeline_and_does_not_discard_another_draft(self):
        workflow = self.admin.workflowEditor
        workflow._identity = 'demo/other'
        workflow.set_field('name', 'Pending workflow')
        self.admin.open_type_workflow('demo/assets')
        self.assertEqual(self.admin.section, 'types')
        self.assertTrue(self.editor.error)
        workflow.discard()
        with patch.object(workflow, '_request') as request:
            self.admin.open_type_workflow('demo/assets')
        request.assert_called_once_with('load', 'demo/assets')
        self.assertEqual(self.admin.section, 'workflow')

    def test_create_workflow_button_presets_type_and_keeps_unsaved_type_edits(self):
        self.editor.set_field('description', 'Keep this draft')
        self.click('segmentedButtonSegment_entity_details')
        self.assertFalse(any(
            item.objectName() == 'adminCreateTypeWorkflow' and item.isVisible()
            for item in sidebar_fixture.SidebarEditorQmlTests.descendants(
                self.window.contentItem()
            )
        ))
        self.click('segmentedButtonSegment_entity_workflows')
        with patch.object(self.admin.workflowEditor, '_request') as request:
            self.click('adminCreateTypeWorkflow')
        request.assert_not_called()
        self.assertEqual(self.admin.section, 'workflow')
        workflow = self.admin.workflowEditor
        self.assertEqual(workflow.identity, '')
        self.assertEqual(workflow.document['searchType'], 'demo/asset')
        self.assertEqual(workflow.document['xml'], '<pipeline/>')
        self.assertTrue(workflow.dirty)
        self.assertTrue(self.item('adminWorkflowDraft').isVisible())
        self.assertEqual(self.editor.document['description'], 'Keep this draft')
        self.assertTrue(self.editor.dirty)
        self.assertEqual(self.ui.fixture.warnings, [])

    def test_new_type_explains_why_workflow_needs_a_saved_type(self):
        self.editor.new_document()
        frame(self.window)
        self.assertFalse(any(
            item.objectName() == 'adminCreateTypeWorkflow' and item.isVisible()
            for item in sidebar_fixture.SidebarEditorQmlTests.descendants(
                self.window.contentItem()
            )
        ))
        self.admin.create_type_workflow(self.editor)
        self.assertEqual(self.admin.section, 'types')
        self.assertEqual(self.admin.workflowEditor.identity, 'demo/assets')

    def test_create_workflow_does_not_replace_an_existing_workflow_draft(self):
        workflow = self.admin.workflowEditor
        workflow.set_field('name', 'Keep current workflow')
        before = copy.deepcopy(workflow.document)
        self.click('segmentedButtonSegment_entity_workflows')
        self.click('adminCreateTypeWorkflow')
        self.assertEqual(self.admin.section, 'types')
        self.assertEqual(workflow.document, before)
        self.assertTrue(self.editor.error)

    def test_create_workflow_first_use_fetches_catalogs_without_loading_another_pipeline(self):
        api = api_fixture.AdministrationApiTests()
        api.setUp()
        self.addCleanup(api.doCleanups)
        workflow = self.admin.workflowEditor
        workers = []

        def add_task(operation):
            worker = self.worker(operation)
            workers.append(worker)
            return worker

        def execute(endpoint, arguments, **_):
            return json.loads(endpoint(**arguments))

        for empty_catalog in (False, True):
            with self.subTest(empty_catalog=empty_catalog):
                if empty_catalog:
                    api.tables['sthpw/pipeline'] = []
                before = copy.deepcopy(api.tables)
                workflow.reset('demo')
                self.ui.click('adminSection_types')
                self.click('segmentedButtonSegment_entity_workflows')
                with patch('thlib.tactic_classes.execute_procedure_serverside', side_effect=execute) as rpc, \
                        patch.object(env_inst.server_pool, 'add_task', side_effect=add_task):
                    self.click('adminCreateTypeWorkflow')
                    frame(self.window)
                self.assertEqual(rpc.call_count, 1)
                self.assertEqual(rpc.call_args.args[1]['action'], 'new')
                self.assertEqual(workflow.document['searchType'], 'demo/asset')
                self.assertEqual(workflow.nodes, [])
                self.assertEqual(workflow.error, '')
                self.assertTrue(workflow.dirty)
                self.assertFalse(workflow.busy)
                self.assertEqual(api.tables, before)
                self.assertEqual(api.calls, [])
                self.assertEqual(self.ui.fixture.warnings, [])

    def test_create_workflow_button_layout_and_keyboard_touch_input(self):
        for width, height in ((900, 620), (1400, 940)):
            self.window.resize(width, height)
            self.ui.click('adminSection_types')
            self.click('segmentedButtonSegment_entity_workflows')
            frame(self.window)
            button = self.reveal('adminCreateTypeWorkflow')
            top_left = button.mapToScene(QPointF())
            self.assertGreaterEqual(top_left.x(), 0)
            self.assertLessEqual(top_left.x() + button.width(), width)
            self.assertLessEqual(top_left.y() + button.height(), height)
            self.assertEqual(button.property('text'), 'Создать воркфлоу')
            output = os.environ.get('ADMIN_TYPE_WORKFLOW_SCREENSHOTS')
            if output:
                Path(output).mkdir(parents=True, exist_ok=True)
                self.window.grabWindow().save(str(Path(output) / ('type_' + str(width) + '.png')))
            if width == 900:
                button.forceActiveFocus()
                QTest.keyClick(self.window, Qt.Key_Space)
            else:
                device = QTest.createTouchDevice()
                point = button.mapToScene(QPointF(button.width() / 2, button.height() / 2)).toPoint()
                sequence = QTest.touchEvent(self.window, device, autoCommit=False)
                sequence.press(0, point, self.window).commit()
                frame(self.window)
                sequence.release(0, point, self.window).commit()
            frame(self.window)
            self.assertEqual(self.admin.section, 'workflow')
            self.assertEqual(self.admin.workflowEditor.document['searchType'], 'demo/asset')
            self.admin.workflowEditor.discard()
            self.assertEqual(self.ui.fixture.warnings, [])

    def test_file_selection_can_be_undone_without_saving_or_uploading(self):
        self.click('segmentedButtonSegment_entity_details')
        path = self.image()
        # Exercise the FileDialog's accepted route without displaying a native
        # OS chooser from an offscreen test process.
        field = self.item('adminSearchTypePreview')
        owner = field.parentItem()
        while owner is not None and owner.findChild(QObject, 'adminSearchTypePreviewDialog') is None:
            owner = owner.parentItem()
        dialog = owner.findChild(QObject, 'adminSearchTypePreviewDialog')
        dialog.setProperty('selectedFile', QUrl.fromLocalFile(str(path)))
        dialog.accepted.emit()
        frame(self.window)
        self.assertEqual(self.editor.previewUrl, QUrl.fromLocalFile(str(path)).toString())
        self.assertTrue(self.editor.dirty)
        self.checkin.prepare_external_checkin.assert_not_called()
        self.click('adminSearchTypeCancelPreview')
        self.assertFalse(self.editor.dirty)
        self.assertEqual(self.editor.document['previewPath'], '')
        self.assertEqual(self.ui.fixture.warnings, [])

    def test_selected_image_is_painted_in_software_backend(self):
        self.click('segmentedButtonSegment_entity_details')
        preview = self.reveal('adminSearchTypePreview')
        ready = QSignalSpy(preview.imageReady)
        self.editor.set_preview_path(QUrl.fromLocalFile(str(self.image())))
        self.assertTrue(ready.wait(2000))
        frame(self.window)
        center = preview.mapToScene(QPointF(preview.width() / 2, preview.height() / 2))
        screenshot = self.window.grabWindow()
        scale_x = screenshot.width() / self.window.width()
        scale_y = screenshot.height() / self.window.height()
        self.assertEqual(screenshot.pixelColor(round(center.x() * scale_x), round(center.y() * scale_y)),
                         QColor('#54a878'))

    def test_save_queues_icon_of_search_type_registry_record_not_an_instance(self):
        path = self.image()
        self.editor.set_preview_path(QUrl.fromLocalFile(str(path)))
        response = dict(identity='demo/asset', revision='saved', canWrite=True,
                        catalog=self.editor.catalog, metadata=self.editor.metadata,
                        document={key: value for key, value in self.editor.document.items() if key != 'previewPath'})
        workers = []

        def add_task(operation):
            worker = self.worker(operation)
            workers.append(worker)
            return worker

        with patch('thlib.tactic_classes.execute_procedure_serverside', return_value=response) as rpc, \
                patch.object(env_inst.server_pool, 'add_task', side_effect=add_task), \
                patch('thlib.server_cache.invalidate_domains'):
            self.click('adminSaveDocument')
            self.click('adminConfirmSave')
            frame(self.window)
        request = rpc.call_args.args[1]
        self.assertNotIn('previewPath', request['document'])
        self.assertEqual(request['identity'], 'demo/asset')
        args = self.checkin.prepare_external_checkin.call_args.kwargs
        self.assertEqual(args['search_key'], 'sthpw/search_object?code=demo/asset')
        self.assertEqual(args['source'].get_search_key(), args['search_key'])
        self.assertEqual(args['context'], 'icon')
        self.assertEqual(args['project_code'], 'sthpw')
        self.assertEqual([Path(value) for value in args['paths']], [path])
        self.assertTrue(args['queue_when_ready'])
        self.assertFalse(self.editor.dirty)
        self.assertFalse(self.editor.busy)
        self.assertEqual(self.ui.fixture.warnings, [])

    def test_creation_form_stages_preview_and_queues_it_only_after_type_is_created(self):
        self.click('adminCreateDocument')
        path = self.image()
        for width, height in ((900, 620), (1400, 940)):
            self.window.resize(width, height)
            frame(self.window)
            choose = self.reveal('adminSearchTypeChoosePreview')
            self.assertTrue(choose.isEnabled())
            self.assertGreaterEqual(choose.mapToScene(QPointF()).x(), 14)
            self.assertLess(choose.mapToScene(QPointF(choose.width(), 0)).x(), width - 14)
        owner = self.item('adminSearchTypePreview').parentItem()
        while owner is not None and owner.findChild(QObject, 'adminSearchTypePreviewDialog') is None:
            owner = owner.parentItem()
        dialog = owner.findChild(QObject, 'adminSearchTypePreviewDialog')
        dialog.setProperty('selectedFile', QUrl.fromLocalFile(str(path)))
        dialog.accepted.emit()
        frame(self.window)
        self.assertEqual(Path(self.editor.document['previewPath']), path)
        self.assertEqual(self.editor.identity, '')
        self.checkin.prepare_external_checkin.assert_not_called()
        self.click('adminSearchTypeCancelPreview')
        self.assertEqual(self.editor.document['previewPath'], '')
        dialog.accepted.emit()
        self.editor.set_field('title', 'Episodes')
        response = dict(
            identity='demo/episodes', revision='created', canWrite=True,
            catalog=self.editor.catalog,
            metadata={'searchKey': 'sthpw/search_object?code=demo/episodes'},
            document=dict(title='Episodes', description='', color='', columns=[]))
        workers = []

        def add_task(operation):
            worker = self.worker(operation)
            workers.append(worker)
            return worker

        with patch('thlib.tactic_classes.execute_procedure_serverside', return_value=response) as rpc, \
                patch.object(env_inst.server_pool, 'add_task', side_effect=add_task), \
                patch('thlib.server_cache.invalidate_domains'):
            self.click('adminSaveDocument')
            rpc.assert_not_called()
            self.checkin.prepare_external_checkin.assert_not_called()
            self.click('adminConfirmSave')
            frame(self.window)
        rpc.assert_called_once()
        request = rpc.call_args.args[1]
        self.assertEqual(request['identity'], '')
        self.assertNotIn('name', request['document'])
        self.assertNotIn('previewPath', request['document'])
        self.checkin.prepare_external_checkin.assert_called_once()
        queued = self.checkin.prepare_external_checkin.call_args.kwargs
        self.assertEqual(queued['search_key'], 'sthpw/search_object?code=demo/episodes')
        self.assertEqual(queued['source'].get_search_key(), queued['search_key'])
        self.assertEqual(queued['context'], 'icon')
        self.assertEqual([Path(value) for value in queued['paths']], [path])
        self.assertTrue(self.editor.previewQueued)
        self.assertFalse(self.editor.dirty)
        self.click('segmentedButtonSegment_entity_workflows')
        self.assertTrue(self.reveal('adminCreateTypeWorkflow').isEnabled())
        self.click('adminCreateTypeWorkflow')
        self.assertEqual(self.admin.section, 'workflow')
        self.assertEqual(self.admin.workflowEditor.document['searchType'], 'demo/episodes')
        self.assertIn('demo/episodes', [row['identity'] for row in self.admin.workflowEditor.metadata['searchTypes']])
        self.assertEqual(self.ui.fixture.warnings, [])

    def test_discard_new_type_with_preview_leaves_no_draft_or_upload(self):
        self.click('adminCreateDocument')
        self.editor.set_preview_path(QUrl.fromLocalFile(str(self.image())))
        self.assertTrue(self.editor.document.get('previewPath'))
        self.click('adminDiscardDocument')
        self.assertEqual(self.editor.document, {})
        self.assertFalse(self.editor.dirty)
        self.assertEqual(self.editor.previewUrl, '')
        self.checkin.prepare_external_checkin.assert_not_called()

    def test_invalid_image_rejected_before_rpc_and_queue_failure_keeps_image_for_retry(self):
        with patch('thlib.tactic_classes.execute_procedure_serverside') as rpc:
            with self.assertRaises(ValueError) as caught:
                self.editor._execute_request(dict(action='save', document={'previewPath': 'missing.png'}),
                                             'demo', {})
        self.assertEqual(str(caught.exception), self.editor.tr('The selected preview is not a readable image'))
        rpc.assert_not_called()
        path = self.image()
        self.editor.set_preview_path(QUrl.fromLocalFile(str(path)))
        self.editor._original = copy.deepcopy(self.editor.document)
        self.checkin.prepare_external_checkin.side_effect = ValueError('Repository unavailable')
        self.editor.committed.emit()
        self.assertTrue(self.editor.dirty)
        self.assertIn('Repository unavailable', self.editor.error)
        self.assertEqual(Path(self.editor.document['previewPath']), path)

    def test_registry_preview_enters_the_real_checkin_preparation_path(self):
        from thlib.ui.checkin_out import CheckinOutController
        checkin = CheckinOutController(self.ui.fixture.application)
        self.addCleanup(checkin.deleteLater)
        self.editor.attach_checkin_controller(checkin)
        self.editor.set_preview_path(QUrl.fromLocalFile(str(self.image())))
        with patch.object(checkin, '_schedule_naming'):
            self.editor.committed.emit()
        payload = checkin.operation_payload()
        self.assertEqual(checkin.files.rowCount(), 1)
        self.assertEqual(payload['searchKey'], 'sthpw/search_object?code=demo/asset')
        self.assertEqual(payload['context'], 'icon')
        self.assertTrue(payload['updateVersionless'])
        self.assertTrue(checkin._queue_after_naming)
        self.assertFalse(self.editor.dirty)

    def test_current_preview_uses_native_file_and_scoped_cache_without_hidden_work(self):
        from thlib.ui.skey_previews import SearchKeyPreviewResolver
        from thlib.ui.admin.search_types import SearchTypesEditor
        resolver = SearchKeyPreviewResolver(self.ui.fixture.application)
        editor = SearchTypesEditor(self.ui.fixture.application, previews=resolver)
        self.addCleanup(editor.shutdown)
        key = 'skey://sthpw/search_object?code=demo/asset'
        path = self.image()
        native_file = SimpleNamespace(is_local_current=lambda: True, get_full_abs_path=lambda: str(path))
        descriptor = {'searchKey': key, 'status': 'ready', 'kind': 'sobject', '_previewFile': native_file}
        resolver._resolved(resolver._scope(), [descriptor])
        editor._metadata = dict(searchKey=key.removeprefix('skey://'))
        editor._document_loaded()
        self.assertEqual(editor.previewUrl, '')
        with patch.object(resolver, 'request_many') as requests:
            editor.set_presentation_visible(True)
            self.assertEqual(editor.previewUrl, QUrl.fromLocalFile(str(path)).toString())
            self.assertEqual(requests.call_args.args[0], [])
            editor.set_presentation_visible(False)
            requests.reset_mock()
            resolver.previewReady.emit(key, {'previewUrl': 'not from this server'})
            requests.assert_not_called()
            editor.set_presentation_visible(True)
            resolver._resolved(('previous server', 'previous login'), [
                {'searchKey': key, 'status': 'ready', 'kind': 'sobject', 'previewUrl': 'other.png'}])
            self.assertEqual(editor.previewUrl, QUrl.fromLocalFile(str(path)).toString())
        editor.reset()
        resolver.previewReady.emit(key, {'previewUrl': 'late.png'})
        self.assertEqual(editor.previewUrl, '')

    def test_queue_completion_refreshes_only_matching_preview_without_losing_draft(self):
        class Queue(QObject):
            operationCompleted = Signal('QVariantMap')

        queue = Queue()
        self.editor.attach_checkin_controller(self.checkin, queue)
        path = self.image()
        self.editor.set_preview_path(QUrl.fromLocalFile(str(path)))
        self.editor.committed.emit()
        self.assertTrue(self.editor.previewQueued)
        self.editor._preview_url = 'previous-image.png'
        self.assertEqual(self.editor.previewUrl, QUrl.fromLocalFile(str(path)).toString())
        self.editor.set_field('description', 'Keep pending description')
        queue.operationCompleted.emit({'searchKey': 'demo/asset?code=A1', 'context': 'icon'})
        self.assertTrue(self.editor.previewQueued)
        queue.operationCompleted.emit({'searchKey': self.editor.metadata['searchKey'], 'context': 'icon'})
        self.assertFalse(self.editor.previewQueued)
        self.assertEqual(self.editor.document['description'], 'Keep pending description')
        self.assertTrue(self.editor.dirty)

    def test_hidden_native_window_disables_preview_presentation(self):
        self.assertTrue(self.editor._presentation_visible)
        self.ui.fixture.application.window_model.close_window('administration')
        QCoreApplication.processEvents()
        self.assertFalse(self.editor._presentation_visible)

    def test_preview_settings_belong_to_details_and_keep_selection_across_pages(self):
        def visible_choices():
            return [item for item in sidebar_fixture.SidebarEditorQmlTests.descendants(
                self.window.contentItem()) if item.objectName() == 'adminSearchTypeChoosePreview'
                and item.isVisible()]

        self.assertEqual(visible_choices(), [])
        self.assertTrue(self.item('adminSearchTypeCount_total').isVisible())
        self.click('segmentedButtonSegment_entity_details')
        self.assertEqual(len(visible_choices()), 1)
        path = self.image()
        self.editor.set_preview_path(QUrl.fromLocalFile(str(path)))
        self.click('segmentedButtonSegment_entity_summary')
        self.assertEqual(visible_choices(), [])
        self.click('segmentedButtonSegment_entity_details')
        self.assertEqual(Path(self.editor.document['previewPath']), path)
        self.assertTrue(self.item('adminSearchTypeCancelPreview').isVisible())
        self.checkin.prepare_external_checkin.assert_not_called()
        self.assertEqual(self.ui.fixture.warnings, [])

    def test_details_preview_and_scrollbar_layout_narrow_wide_and_wheel(self):
        self.editor.set_preview_path(QUrl.fromLocalFile(str(self.image())))
        for width, height in ((900, 620), (1400, 940)):
            self.window.resize(width, height)
            self.click('segmentedButtonSegment_entity_details')
            for name in ('adminSearchTypeTitle', 'adminSearchTypeChoosePreview',
                         'adminSearchTypeCancelPreview', 'adminSaveDocument'):
                item = self.reveal(name)
                origin = item.mapToScene(QPointF())
                self.assertGreaterEqual(origin.x(), 0)
                self.assertLessEqual(origin.x() + item.width(), width + 1)
                self.assertLessEqual(origin.y() + item.height(), height + 1)
            scroll = self.item('adminSearchTypeForm')
            if width == 900:
                scroll.setProperty('contentY', 0)
                frame(self.window)
                point = scroll.mapToScene(QPointF(scroll.width() / 2, scroll.height() / 2))
                stopped = QSignalSpy(scroll.movementEnded)
                event = QWheelEvent(point, self.window.mapToGlobal(point.toPoint()), QPoint(), QPoint(0, -12000),
                                    Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False)
                event.setTimestamp(time.monotonic_ns() // 1_000_000)
                QCoreApplication.sendEvent(self.window, event)
                if scroll.property('moving'):
                    self.assertTrue(stopped.wait(2000))
                frame(self.window)
                self.assertGreater(scroll.property('contentY'), 0)
            output = os.environ.get('SEARCH_TYPE_SCREENSHOTS')
            if output:
                Path(output).mkdir(parents=True, exist_ok=True)
                scroll.setProperty('contentY', 0)
                frame(self.window)
                self.window.grabWindow().save(str(Path(output) / ('details_%s.png' % width)))
            self.assertEqual(self.ui.fixture.warnings, [])
