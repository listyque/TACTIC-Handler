"""Actual input/layout for the administration graph's form and technical tabs."""

import copy
import json
import os
from pathlib import Path
import time
import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtTest import QSignalSpy, QTest

import tests.test_administration_qml as administration_fixture
import tests.test_sidebar_editor_qml as sidebar_fixture
from tests.profile_ui_responsiveness import frame


class AdminGraphFormsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        administration_fixture.AdministrationQmlTests.setUpClass()

    def setUp(self):
        self.fixture = administration_fixture.AdministrationQmlTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.admin = self.fixture.admin
        self.window = self.fixture.window
        self.window.resize(1400, 940)
        self.click('adminSection_workflow')

    def item(self, name):
        if isinstance(name, tuple):
            panel, child = name
            return next(item for item in sidebar_fixture.SidebarEditorQmlTests.descendants(self.item(panel))
                        if item.objectName() == child and item.isVisible())
        return self.fixture.item(name)

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
        self.fixture.fixture.click(self.window, self.reveal(name))

    def choose(self, name, value):
        combo = self.reveal(name)
        combo.forceActiveFocus()
        model = combo.property('model')
        if hasattr(model, 'toVariant'):
            model = model.toVariant()
        index = next(index for index, row in enumerate(model) if row['identity'] == value)
        QTest.keyClick(self.window, Qt.Key_Home)
        for _ in range(index):
            QTest.keyClick(self.window, Qt.Key_Down)
        frame(self.window)
        self.assertEqual(combo.property('currentValue'), value)

    def color_dialog_button(self, label):
        label = QCoreApplication.translate('QQuickDialogButtonBox', label)
        for window in QGuiApplication.allWindows():
            if not window.isVisible():
                continue
            for item in sidebar_fixture.SidebarEditorQmlTests.descendants(window.contentItem()):
                if item.isVisible() and item.inherits('QQuickAbstractButton') and item.property('text') == label:
                    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
                    QTest.mouseClick(window, Qt.LeftButton, pos=point)
                    frame(self.window)
                    return
        self.fail('Color dialog button not found: ' + label)

    def enter(self, name, text):
        self.click(name)
        QTest.keyClick(self.window, Qt.Key_A, Qt.ControlModifier)
        for character in text:
            QTest.keyClick(self.window, character)
        frame(self.window)

    def assert_inside(self, name):
        item = self.item(name)
        origin = item.mapToScene(QPointF())
        self.assertGreaterEqual(origin.x(), 0, name)
        self.assertGreaterEqual(origin.y(), 0, name)
        self.assertLessEqual(origin.x() + item.width(), self.window.width() + 1, name)
        self.assertLessEqual(origin.y() + item.height(), self.window.height() + 1, name)

    def test_process_and_pipeline_settings_share_the_right_inspector(self):
        for width, height in ((900, 620), (1400, 940)):
            with self.subTest(width=width):
                self.window.resize(width, height)
                frame(self.window)
                self.click('graphNode_model')
                canvas = self.item('adminGraphCanvas')
                inspector = self.item('adminProcessSettingsViewport')
                self.assertGreater(inspector.mapToScene(QPointF()).x(),
                                   canvas.mapToScene(QPointF()).x() + canvas.width())
                self.assertEqual(self.item('adminGraphPages').property('currentValue'), 'canvas')
                self.assertEqual([row['value'] for row in self.item('adminGraphPages').property('model').toVariant()],
                                 ['canvas', 'technical'])
                self.enter('adminProcessDescription', 'Only model')
                self.assertEqual(self.admin.workflowEditor.processDescription, 'Only model')
                self.click('adminEditPipeline')
                self.assertEqual(self.admin.workflowEditor.selectedNode, '')
                self.enter('adminPipelineTitle', 'Asset workflow')
                self.assertEqual(self.admin.workflowEditor.document['searchType'], 'demo/asset')
                self.assertIn('Assets', self.item('adminWorkflowSearchType').property('text'))
                self.assertTrue(canvas.isVisible())
                self.assertEqual(self.fixture.fixture.warnings, [])

    def test_pipeline_settings_share_the_canvas_toolbar(self):
        for width, height in ((900, 620), (1400, 940)):
            with self.subTest(width=width):
                self.window.resize(width, height)
                frame(self.window)
                self.click('graphNode_model')
                tabs = self.item('adminGraphPages')
                settings = self.item('adminEditPipeline')
                self.assertAlmostEqual(
                    tabs.mapToScene(QPointF(0, tabs.height() / 2)).y(),
                    settings.mapToScene(QPointF(0, settings.height() / 2)).y(),
                    delta=1)
                for name in ('adminGraphPages', 'adminEditPipeline'):
                    self.assert_inside(name)
                self.assertGreaterEqual(
                    settings.mapToScene(QPointF()).x(),
                    tabs.mapToScene(QPointF()).x() + tabs.width() + 6)
                self.click('adminEditPipeline')
                self.assertEqual(self.admin.workflowEditor.selectedNode, '')
                self.assertTrue(self.item('adminPipelineTitle').isVisible())
                self.assertEqual(self.fixture.fixture.warnings, [])

    def test_task_workflow_picker_and_edit_action_have_a_gap(self):
        for width, height in ((900, 620), (1400, 940)):
            with self.subTest(width=width):
                self.window.resize(width, height)
                frame(self.window)
                self.click('graphNode_model')
                self.choose('adminProcessField_task_pipeline', 'demo/tasks')
                action = self.reveal('adminEditTaskWorkflow')
                picker = self.item('adminProcessField_task_pipeline')
                self.assertGreaterEqual(
                    action.mapToScene(QPointF()).y()
                    - picker.mapToScene(QPointF(0, picker.height())).y(), 8)
                self.assertAlmostEqual(action.width(), picker.width(), delta=1)
                self.assert_inside('adminEditTaskWorkflow')
                editor = self.admin.workflowEditor
                editor._original = copy.deepcopy(editor.document)
                with patch.object(editor, '_request') as request:
                    self.click('adminEditTaskWorkflow')
                    request.assert_called_once_with('load', 'demo/tasks')
                self.assertEqual(self.fixture.fixture.warnings, [])

    def test_graph_subpages_are_visible_tabs_and_remain_bounded_when_narrow(self):
        self.click('graphNode_model')
        for width, height in ((900, 620), (1400, 940)):
            self.window.resize(width, height)
            for page in ('canvas', 'technical'):
                with self.subTest(width=width, page=page):
                    self.click('segmentedButtonSegment_' + page)
                    self.assert_inside('adminGraphPages')
                    self.assert_inside('adminSaveDocument')
                    if page == 'canvas':
                        canvas = self.item('adminGraphCanvas')
                        self.assertGreaterEqual(canvas.width(), 180)
                        self.assertGreaterEqual(canvas.height(), 120)
                    if page == 'technical':
                        self.assert_inside('adminNativeDocumentViewport')
                        self.assertGreater(self.item('adminNativeDocumentViewport').height(), 90)
                    output = os.environ.get('ADMIN_GRAPH_FORM_SCREENSHOTS')
                    if output:
                        path = Path(output)
                        path.mkdir(parents=True, exist_ok=True)
                        self.window.grabWindow().save(str(path / (page + '_' + str(width) + '.png')))
                    self.assertEqual(self.fixture.fixture.warnings, [])

    def test_process_creation_uses_visible_native_type_choices(self):
        self.click('adminAddProcess')
        self.enter('adminNewProcessName', 'lighting')
        self.click('adminNewNodeType_action')
        self.click('adminAddGraphNode')
        editor = self.admin.workflowEditor
        self.assertEqual(editor.selectedNode, 'lighting')
        self.assertEqual(editor.selectedAttributes['type'], 'action')
        self.assertTrue(editor.dirty)
        self.assertTrue(self.item('adminProcessSettingsViewport').isVisible())
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_node_specific_forms_and_progress_circle(self):
        editor = self.admin.workflowEditor
        editor.add_node('assets', 'progress', 40, 210)
        frame(self.window)
        self.click('graphNode_assets')
        circle = self.item('graphNode_assets')
        self.assertEqual(circle.width(), circle.height())
        self.assertTrue(self.item('adminProcessField_related_search_type').isVisible())
        self.assertFalse(any(item.isVisible() and item.objectName() == 'adminProcessField_assigned_group'
                             for item in sidebar_fixture.SidebarEditorQmlTests.descendants(self.window.contentItem())))
        self.click('graphOutput_assets')
        preview = self.item('graphPendingConnection')
        self.assertAlmostEqual(preview.property('startX'), circle.x() + circle.width())
        self.click('graphInput_review')
        self.assertEqual(editor.edges[-1]['from'], 'assets')
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_workflows_are_grouped_by_type_and_statuses_have_a_separate_group(self):
        editor = self.admin.workflowEditor
        with patch.object(editor, '_request') as request:
            listing = self.item('adminWorkflowList')
            rows = listing.property('model')
            self.assertEqual([row['identity'] for row in rows if row['header']], ['demo/asset', 'sthpw/task'])
            self.assertTrue(self.item('adminWorkflow_demo/assets').property('selected'))
            self.assertEqual(self.item('adminWorkflow_demo/assets').property('accent').name(), '#6688aa')
            self.click('adminWorkflowGroup_demo/asset')
            rows = listing.property('model')
            self.assertNotIn('demo/assets', [row['identity'] for row in rows])
            request.assert_not_called()
            self.click('adminWorkflow_demo/tasks')
            request.assert_called_once_with('load', 'demo/tasks')
            request.reset_mock()
            self.click('adminCreateWorkflow_sthpw/task')
            self.assertEqual(editor.document['searchType'], 'sthpw/task')
            self.assertTrue(editor.dirty)
            request.assert_not_called()
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_missing_process_opens_as_warning_without_creating_or_dropping_xml(self):
        editor = self.admin.workflowEditor
        xml = '<pipeline><process name="model"/><connect from="model" to="texture"/></pipeline>'
        editor._document['xml'] = xml
        editor._original = copy.deepcopy(editor.document)
        editor._document_loaded()
        editor.stateChanged.emit()
        frame(self.window)
        self.assertEqual(editor.error, '')
        self.assertFalse(editor.dirty)
        self.assertIn('texture', self.item('adminMissingProcesses').property('text'))
        self.click('graphNode_texture')
        self.assertTrue(self.item('adminMissingProcessDetails').isVisible())
        self.assertEqual(editor.document['xml'], xml)
        with patch.object(editor, '_request') as request:
            editor.set_field('name', 'Edited pipeline')
            editor.save()
            request.assert_not_called()
            self.assertIn('texture', editor.error)
        self.click('adminAddProcess')
        self.enter('adminNewProcessName', 'texture')
        self.click('adminAddGraphNode')
        self.assertFalse(editor.selectedReference)
        self.assertEqual(editor.error, '')
        self.assertEqual(len(editor.edges), 1)
        self.assertFalse(any(node['referenceOnly'] for node in editor.nodes))
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_task_pipeline_nodes_use_status_form_even_without_xml_type(self):
        editor = self.admin.workflowEditor
        editor._document['searchType'] = 'sthpw/task'
        editor.apply_xml('<pipeline><process name="Review"/></pipeline>')
        frame(self.window)
        self.click('graphNode_Review')
        self.choose('adminProcessField_mapping', 'Complete')
        self.assertEqual(editor.processSettings['mapping'], 'Complete')
        self.assertEqual(editor.selectedAttributes['type'], 'status')
        self.assertFalse(any(item.isVisible() and item.objectName() == 'adminProcessField_duration'
                             for item in sidebar_fixture.SidebarEditorQmlTests.descendants(self.window.contentItem())))
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_task_workflow_edit_link_keeps_unsaved_parent_changes(self):
        self.click('graphNode_model')
        self.choose('adminProcessField_task_pipeline', 'demo/tasks')
        editor = self.admin.workflowEditor
        with patch.object(editor, '_request') as request:
            self.click('adminEditTaskWorkflow')
            self.assertFalse(request.called)
            self.assertTrue(editor.dirty)
            self.assertTrue(editor.error)
            editor._original = dict(editor.document)
            editor.open_task_workflow()
            request.assert_called_once_with('load', 'demo/tasks')

    def test_dependencies_button_opens_saved_process_in_native_modal(self):
        editor = self.admin.workflowEditor
        editor._metadata['processCodes'] = {'model': 'PR1'}
        self.click('graphNode_model')
        with patch.object(editor.rulesEditor, '_request') as request:
            self.click('adminOpenProcessDependencies')
            request.assert_called_once_with('load', 'PR1')
            child = self.fixture.fixture.window('process_dependencies')
            self.assertEqual(child.modality(), Qt.WindowModal)
            self.fixture.fixture.application.window_model.close_window('process_dependencies')
            editor.set_process_description('Unsaved')
            request.reset_mock()
            editor.rulesEditor.open()
            request.assert_not_called()
            self.assertTrue(editor.error)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_new_pipeline_opens_its_details_without_hiding_the_canvas_tabs(self):
        self.click('adminCreateDocument')
        self.assert_inside('adminPipelineTitle')
        self.assertTrue(self.item('adminWorkflowDraft').property('selected'))
        self.assertEqual(
            self.item('adminWorkflowDraft').property('description'),
            self.admin.workflowEditor.tr('Draft · not saved yet'),
        )
        for width, height in ((900, 620), (1400, 940)):
            self.window.resize(width, height)
            frame(self.window)
            self.assert_inside('adminWorkflowDraft')
            self.assert_inside('adminPipelineTitle')
        self.enter('adminPipelineTitle', 'New pipeline')
        self.assertEqual(self.item('adminWorkflowDraft').property('text'), 'New pipeline')
        self.assertNotIn('pipelineCode', self.admin.workflowEditor.document)
        self.click('segmentedButtonSegment_canvas')
        self.assert_inside('adminGraphCanvas')
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_discarded_pipeline_keeps_the_create_action_available(self):
        editor = self.admin.workflowEditor
        self.click('adminCreateDocument')
        self.assertTrue(editor.dirty)

        self.click('adminDiscardDocument')

        create = self.item('adminCreateDocument')
        self.assertTrue(create.isEnabled())
        self.click('adminCreateDocument')
        self.assertEqual(editor.document['searchType'], 'demo/asset')
        self.assertTrue(editor.dirty)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_schema_creation_is_the_top_left_document_action(self):
        self.click('adminSection_schema')
        toolbar = self.item('adminDocumentToolbar')
        create = self.item('adminCreateSchemaType')
        reload_action = self.item('adminReloadDocument')
        self.assertLess(create.mapToScene(QPointF()).x(),
                        reload_action.mapToScene(QPointF()).x())
        self.assertGreaterEqual(create.mapToScene(QPointF()).x(),
                                toolbar.mapToScene(QPointF()).x())
        self.assertAlmostEqual(create.mapToScene(QPointF()).y(),
                               reload_action.mapToScene(QPointF()).y(), delta=1)

        self.click('adminCreateSchemaType')

        creator = self.fixture.fixture.window('schema_search_type')
        self.assertEqual(creator.transientParent(), self.window)
        self.admin.schemaTypeEditor.discard()
        self.fixture.fixture.application.window_model.close_window('schema_search_type')
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_search_type_context_is_readonly_and_new_pipelines_inherit_it(self):
        editor = self.admin.workflowEditor
        editor.set_field('searchType', 'demo/shot')
        frame(self.window)
        self.assertEqual(editor.document['searchType'], 'demo/asset')
        self.assertFalse(editor.dirty)
        self.assertTrue(editor.error)
        self.assertIn('Assets', self.item('adminWorkflowSearchType').property('text'))
        self.click('adminCreateDocument')
        self.assertEqual(editor.document['searchType'], 'demo/asset')
        self.assertEqual(self.item('adminGraphPages').property('currentValue'), 'canvas')
        self.assertEqual(editor.error, '')
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_schema_type_row_accepts_touch_then_adds_only_one_native_node(self):
        editor = self.admin.schemaEditor
        editor._metadata['searchTypes'].append({
            'identity': 'demo/sequence', 'label': 'Sequences', 'color': '#8877aa'})
        editor.stateChanged.emit()
        self.click('adminSection_schema')
        self.click('segmentedButtonSegment_add_node')
        self.enter('adminGraphTypeFilter', 'Sequences')
        row = self.item('adminGraphType_demo/sequence')
        point = row.mapToScene(QPointF(row.width() / 2, row.height() / 2)).toPoint()
        device = QTest.createTouchDevice()
        sequence = QTest.touchEvent(self.window, device, autoCommit=False)
        sequence.press(0, point, self.window).commit()
        frame(self.window)
        sequence.release(0, point, self.window).commit()
        frame(self.window)
        self.assertTrue(row.property('selected'))
        self.click('adminAddGraphNode')
        self.assertEqual(editor.selectedNode, 'demo/sequence')
        self.assertEqual(sum(node['identity'] == 'demo/sequence' for node in editor.nodes), 1)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_adding_a_schema_type_places_it_in_the_current_canvas_view(self):
        editor = self.admin.schemaEditor
        editor._metadata['searchTypes'].append({'identity': 'demo/sequence', 'label': 'Sequences'})
        editor.stateChanged.emit()
        self.click('adminSection_schema')
        canvas = self.item('adminGraphCanvas')
        original_nodes = editor.nodes
        center = canvas.mapToScene(QPointF(canvas.width() / 2, canvas.height() / 2)).toPoint()
        for _ in range(3):
            QTest.mousePress(self.window, Qt.MiddleButton, pos=center)
            QTest.mouseMove(self.window, center - QPoint(125, 90))
            QTest.mouseMove(self.window, center - QPoint(250, 180))
            QTest.mouseRelease(self.window, Qt.MiddleButton, pos=center - QPoint(250, 180))
            frame(self.window)
        self.click('segmentedButtonSegment_add_node')
        self.click('adminGraphType_demo/sequence')
        self.click('adminAddGraphNode')
        node = self.item('graphNode_demo/sequence')
        position = node.mapToItem(canvas, QPointF(node.width() / 2, node.height() / 2))
        self.assertGreaterEqual(position.x(), 0)
        self.assertGreaterEqual(position.y(), 0)
        self.assertLessEqual(position.x(), canvas.width())
        self.assertLessEqual(position.y(), canvas.height())
        self.assertEqual(editor.selectedNode, 'demo/sequence')
        self.assertEqual(editor.nodes[:len(original_nodes)], original_nodes)
        self.assertTrue(editor.dirty)
        self.assertEqual(editor.error, '')
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_adding_a_schema_type_already_on_the_canvas_reveals_it_without_a_duplicate(self):
        self.click('adminSection_schema')
        editor = self.admin.schemaEditor
        self.fixture.seed(editor, 'demo', {'xml': editor.document['xml'].replace(
            'xpos="20" ypos="30"', 'xpos="1500" ypos="1200"')}, editor.metadata)
        frame(self.window)
        original = editor.document['xml']
        self.click('segmentedButtonSegment_add_node')
        self.click('adminGraphType_demo/asset')
        self.assertEqual(self.item('adminAddGraphNode').property('text'), 'Показать на схеме')
        self.assertIn('Уже на схеме', self.item('adminGraphType_demo/asset').property('description'))
        self.click('adminAddGraphNode')
        self.assertEqual(editor.error, '')
        self.assertEqual(editor.selectedNode, 'demo/asset')
        self.assertEqual(editor.document['xml'], original)
        self.assertFalse(editor.dirty)
        self.assertEqual(sum(node['identity'] == 'demo/asset' for node in editor.nodes), 1)
        canvas = self.item('adminGraphCanvas')
        node = self.item('graphNode_demo/asset')
        center = node.mapToItem(canvas, QPointF(node.width() / 2, node.height() / 2))
        self.assertAlmostEqual(center.x(), canvas.width() / 2, delta=1)
        self.assertAlmostEqual(center.y(), canvas.height() / 2, delta=1)
        self.assertEqual(self.item('adminGraphInspectorPages').property('currentValue'), 'selection')
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_reference_type_can_be_added_locally_without_losing_its_connection(self):
        self.click('adminSection_schema')
        editor = self.admin.schemaEditor
        editor.apply_xml('<schema><search_type name="demo/asset"/>'
                         '<connect from="demo/asset" to="demo/shot" relationship="code" custom="keep"/></schema>')
        frame(self.window)
        original_edges = editor.edges
        self.assertTrue(next(node for node in editor.nodes if node['identity'] == 'demo/shot')['referenceOnly'])
        self.click('segmentedButtonSegment_add_node')
        self.click('adminGraphType_demo/shot')
        self.assertFalse(self.item('adminAddGraphNode').property('revealExisting'))
        self.click('adminAddGraphNode')
        self.assertEqual(editor.selectedNode, 'demo/shot')
        self.assertFalse(editor.selectedReference)
        self.assertEqual(editor.edges, original_edges)
        self.assertEqual(sum(node['identity'] == 'demo/shot' for node in editor.nodes), 1)
        self.assertEqual(editor.error, '')
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_duplicate_process_name_is_localized_and_can_be_corrected(self):
        original = self.admin.workflowEditor.document['xml']
        self.window.resize(900, 620)
        frame(self.window)
        self.click('adminAddProcess')
        self.enter('adminNewProcessName', 'model')
        self.click('adminAddGraphNode')
        self.assertEqual(self.admin.workflowEditor.error,
                         'Процесс с таким именем уже есть на схеме. Введите другое имя.')
        self.assertEqual(self.admin.workflowEditor.document['xml'], original)
        self.assertEqual(self.item('adminNewProcessName').property('text'), 'model')
        self.enter('adminNewProcessName', 'lighting')
        self.click('adminAddGraphNode')
        self.assertEqual(self.admin.workflowEditor.selectedNode, 'lighting')
        self.assertEqual(self.admin.workflowEditor.error, '')
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_node_add_action_stays_visible_outside_the_scrollable_form(self):
        self.click('adminSection_schema')
        for size in ((900, 620), (1400, 940)):
            with self.subTest(size=size):
                self.window.resize(*size)
                frame(self.window)
                self.click('segmentedButtonSegment_add_node')
                self.click('adminGraphType_demo/asset')
                viewport = self.item('adminGraphPropertiesViewport')
                button = self.item('adminAddGraphNode')
                position = button.mapToScene(QPointF())
                self.assertGreaterEqual(position.y(), viewport.mapToScene(QPointF()).y() + viewport.height())
                self.assert_inside('adminAddGraphNode')
                viewport.setProperty('contentY', max(0, viewport.property('contentHeight') - viewport.height()))
                frame(self.window)
                self.assertEqual(button.mapToScene(QPointF()), position)
                output = os.environ.get('ADMIN_GRAPH_FORM_SCREENSHOTS')
                if output:
                    path = Path(output)
                    path.mkdir(parents=True, exist_ok=True)
                    self.window.grabWindow().save(str(path / ('add_type_' + str(size[0]) + '.png')))
                self.fixture.click('adminAddGraphNode')
                self.assertEqual(self.admin.schemaEditor.selectedNode, 'demo/asset')
                self.assertEqual(self.admin.schemaEditor.error, '')
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_process_action_and_native_json_use_same_draft(self):
        editor = self.admin.workflowEditor
        editor.select_node('model')
        editor.set_attribute('type', 'action')
        frame(self.window)
        self.enter('adminProcessDescription', 'Prepare rendering')
        self.click('segmentedButtonSegment_command')
        self.enter('adminProcessCommandClass', 'project.pipeline.RenderCmd')
        self.click('segmentedButtonSegment_native_json')
        value = json.loads(self.item('adminNativeDocumentText').property('text'))
        self.assertEqual(value['default']['action'], 'command')
        self.assertEqual(value['default']['on_action_class'], 'project.pipeline.RenderCmd')
        self.assertEqual(editor.processDescription, 'Prepare rendering')
        value['custom_handler'] = {'enabled': True}
        self.enter('adminNativeDocumentText', json.dumps(value))
        self.click('adminApplyNativeDocument')
        self.assertEqual(editor.processSettings['custom_handler'], {'enabled': True})
        self.assertFalse(self.item('adminApplyNativeDocument').isEnabled())
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_canvas_attributes_keep_native_values(self):
        self.click('graphNode_model')
        self.click('segmentedButtonSegment_native_json')
        self.assertEqual(self.item('adminGraphPages').property('currentValue'), 'canvas')
        value = json.loads(self.item(('adminSelectionAttributesEditor', 'adminNativeDocumentText')).property('text'))
        value['custom'] = 'kept as data'
        self.enter(('adminSelectionAttributesEditor', 'adminNativeDocumentText'), json.dumps(value))
        self.click(('adminSelectionAttributesEditor', 'adminApplyNativeDocument'))
        self.assertEqual(self.admin.workflowEditor.selectedAttributes['custom'], 'kept as data')
        self.click('segmentedButtonSegment_technical')
        field = self.item('adminNativeDocumentText')
        self.assertIn('kept as data', field.property('text'))
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_schema_node_and_connection_show_json_without_leaving_canvas(self):
        self.click('adminSection_schema')
        editor = self.admin.schemaEditor
        editor.select_node('demo/asset')
        frame(self.window)
        self.assertEqual(json.loads(self.item('adminNativeDocumentText').property('text')),
                         editor.selectedAttributes)
        self.assertEqual(editor.selectedAttributes['custom'], 'yes')

        self.click('segmentedButtonSegment_add_node')
        self.click('graphNode_demo/asset')
        self.assertEqual(self.item('adminGraphInspectorPages').property('currentValue'), 'selection')
        self.assertEqual(json.loads(self.item('adminNativeDocumentText').property('text'))['name'],
                         'demo/asset')

        self.click('graphEdge_0')
        attributes = json.loads(self.item('adminNativeDocumentText').property('text'))
        self.assertEqual(attributes, editor.selectedAttributes)
        self.assertEqual(attributes['custom'], 'edge')
        attributes['custom'] = 'edited connection'
        self.enter('adminNativeDocumentText', json.dumps(attributes))
        self.click('adminApplyNativeDocument')
        self.assertEqual(editor.selectedAttributes['custom'], 'edited connection')
        self.assertEqual(self.item('adminGraphPages').property('currentValue'), 'canvas')
        self.click('graphNode_demo/shot')
        self.assertEqual(json.loads(self.item('adminNativeDocumentText').property('text'))['name'],
                         'demo/shot')
        self.assertEqual(self.item('adminGraphPropertiesViewport').property('contentY'), 0)
        self.assertFalse(self.item('adminApplyNativeDocument').isEnabled())
        self.click('segmentedButtonSegment_technical')
        with self.assertRaises(StopIteration):
            self.item('adminGraphTechnicalPages')
        self.assertTrue(self.item('adminNativeDocumentText').property('text').startswith('<schema'))
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_selection_json_is_immediately_visible_and_bounded_when_narrow(self):
        self.click('adminSection_schema')
        self.click('graphNode_demo/asset')
        for width, height in ((900, 620), (1400, 940)):
            with self.subTest(width=width):
                self.window.resize(width, height)
                frame(self.window)
                viewport = self.item('adminGraphPropertiesViewport')
                viewport.setProperty('contentY', 0)
                frame(self.window)
                panel = self.item('adminSelectionAttributesEditor')
                field = self.item('adminNativeDocumentText')
                json_viewport = self.item('adminNativeDocumentViewport')
                self.assertEqual(panel.property('title'), 'Атрибуты (JSON)')
                self.assertGreater(json_viewport.height(), 90)
                self.assertGreaterEqual(field.mapToItem(viewport, QPointF()).y(), 0)
                self.assertLess(field.mapToItem(viewport, QPointF()).y(), viewport.height() - 50)
                self.assertLessEqual(field.width(), json_viewport.width() - 12)
                self.assertLessEqual(panel.width(), viewport.width() - 12)
                output = os.environ.get('ADMIN_GRAPH_FORM_SCREENSHOTS')
                if output:
                    path = Path(output)
                    path.mkdir(parents=True, exist_ok=True)
                    self.window.grabWindow().save(str(path / ('schema_json_' + str(width) + '.png')))
                self.click('adminApplyNativeDocument')
                self.assert_inside('adminApplyNativeDocument')
                button = self.item('adminApplyNativeDocument')
                point = button.mapToItem(panel, QPointF())
                self.assertLessEqual(point.x() + button.width(), panel.width())
                self.assertLessEqual(point.y() + button.height(), panel.height())
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_selection_json_keeps_validation_and_readonly_guards(self):
        self.click('graphNode_model')
        self.click('segmentedButtonSegment_native_json')
        editor = self.admin.workflowEditor
        original = editor.document['xml']
        self.enter(('adminSelectionAttributesEditor', 'adminNativeDocumentText'), '{"name":12}')
        self.click(('adminSelectionAttributesEditor', 'adminApplyNativeDocument'))
        self.assertTrue(editor.error)
        self.assertEqual(editor.document['xml'], original)
        self.assertFalse(editor.dirty)
        self.assertEqual(self.item(('adminSelectionAttributesEditor', 'adminNativeDocumentText')).property('text'), '{"name":12}')
        self.click('graphNode_review')
        self.click('segmentedButtonSegment_native_json')
        editor._can_write = False
        editor.stateChanged.emit()
        frame(self.window)
        field = self.item(('adminSelectionAttributesEditor', 'adminNativeDocumentText'))
        self.assertTrue(field.property('readOnly'))
        field.forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_A, Qt.ControlModifier)
        QTest.keyClick(self.window, 'x')
        self.assertEqual(json.loads(field.property('text')), editor.selectedAttributes)
        with self.assertRaises(StopIteration):
            self.item(('adminSelectionAttributesEditor', 'adminApplyNativeDocument'))
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_native_editor_scrolls_with_wheel_and_keeps_a_scrollbar_gutter(self):
        editor = self.admin.workflowEditor
        editor.select_node('model')
        values = {'key_%s' % index: 'Native value %s' % index for index in range(100)}
        editor.apply_settings(json.dumps({'custom': values}))
        editor.apply_attributes(json.dumps(dict(editor.selectedAttributes, **values)))
        self.window.resize(900, 620)
        frame(self.window)
        self.click('segmentedButtonSegment_native_json')
        for panel in ('adminProcessNativeSettingsEditor', 'adminSelectionAttributesEditor'):
            with self.subTest(panel=panel):
                self.reveal((panel, 'adminNativeDocumentViewport'))
                viewport = self.item((panel, 'adminNativeDocumentViewport'))
                field = self.item((panel, 'adminNativeDocumentText'))
                self.assertGreater(viewport.property('contentHeight'), viewport.height())
                self.assertLessEqual(field.width(), viewport.width() - 12)
                scrollbar = next(item for item in sidebar_fixture.SidebarEditorQmlTests.descendants(viewport)
                                 if item.inherits('QQuickScrollBar'))
                self.assertTrue(scrollbar.isVisible())
                point = viewport.mapToScene(QPointF(viewport.width() / 2, viewport.height() / 2))
                stopped = QSignalSpy(viewport.movementEnded)
                event = QWheelEvent(point, QPointF(self.window.mapToGlobal(point.toPoint())),
                                    QPoint(), QPoint(0, -12000), Qt.NoButton, Qt.NoModifier,
                                    Qt.NoScrollPhase, False)
                event.setTimestamp(time.monotonic_ns() // 1_000_000)
                QCoreApplication.sendEvent(self.window, event)
                if viewport.property('moving'):
                    self.assertTrue(stopped.wait(2000))
                frame(self.window)
                self.assertGreater(viewport.property('contentY'), 0)
                self.click((panel, 'adminApplyNativeDocument'))
                self.assert_inside((panel, 'adminApplyNativeDocument'))
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_process_catalog_fields_store_native_values_and_boolean_types(self):
        self.click('graphNode_model')
        self.choose('adminProcessField_assigned_group', 'artists')
        self.choose('adminProcessField_supervisor_group', 'leads')
        self.choose('adminProcessField_task_pipeline', 'demo/tasks')
        self.click('adminProcessField_autocreate_task')
        self.enter('adminProcessField_duration', '3')
        QTest.keyClick(self.window, Qt.Key_Tab)
        frame(self.window)
        properties = self.admin.workflowEditor.processProperties
        self.assertEqual(properties['assigned_group'], 'artists')
        self.assertEqual(properties['supervisor_group'], 'leads')
        self.assertEqual(properties['task_pipeline'], 'demo/tasks')
        self.assertIs(properties['autocreate_task'], True)
        self.assertEqual(properties['duration'], 3)
        self.assertIs(type(properties['duration']), int)
        self.assertEqual(self.admin.workflowEditor.selectedAttributes['duration'], '3')
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_each_process_has_its_own_task_status_workflow_without_requests(self):
        editor = self.admin.workflowEditor
        editor._metadata['pipelines'].append({
            'identity': 'demo/review_tasks', 'label': 'Review statuses', 'searchType': 'sthpw/task'})
        editor.catalogChanged.emit()
        with patch.object(editor, '_request') as request:
            self.click('graphNode_model')
            self.choose('adminProcessField_task_pipeline', 'demo/tasks')
            combo = self.item('adminProcessField_task_pipeline')
            choices = combo.property('model')
            if hasattr(choices, 'toVariant'):
                choices = choices.toVariant()
            self.assertEqual([row['identity'] for row in choices],
                             ['', 'demo/tasks', 'demo/review_tasks'])
            self.click('graphNode_review')
            self.assertEqual(editor.processProperties.get('task_pipeline', ''), '')
            self.choose('adminProcessField_task_pipeline', 'demo/review_tasks')
            self.click('graphNode_model')
            self.assertEqual(self.item('adminProcessField_task_pipeline').property('currentValue'),
                             'demo/tasks')
            self.click('graphNode_review')
            self.choose('adminProcessField_task_pipeline', '')
            self.assertEqual(editor.document['processSettings']['model']['properties']['task_pipeline'],
                             'demo/tasks')
            self.assertEqual(editor.document['searchType'], 'demo/asset')
            self.click('adminEditPipeline')
            self.assertTrue(editor.dirty)
            request.assert_not_called()
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_status_workflow_does_not_offer_another_task_status_workflow(self):
        editor = self.admin.workflowEditor
        self.fixture.seed(editor, 'demo/tasks', {
            'xml': '<pipeline><process name="Done" type="status"/></pipeline>',
            'searchType': 'sthpw/task', 'processSettings': {}, 'processDescriptions': {}}, editor.metadata)
        frame(self.window)
        self.click('graphNode_Done')
        self.assertIn('sthpw/task', self.item('adminWorkflowSearchType').property('text'))
        self.assertTrue(self.item('adminProcessField_mapping').isVisible())
        with self.assertRaises(StopIteration):
            self.item('adminProcessField_task_pipeline')
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_leaving_process_inspector_commits_the_field_to_its_original_node(self):
        editor = self.admin.workflowEditor
        self.click('graphNode_model')
        self.enter('adminProcessField_duration', '8')
        self.click('graphNode_review')
        self.assertEqual(editor.document['processSettings']['model']['properties']['duration'], 8)
        self.assertNotIn('duration', editor.processProperties)
        self.enter('adminProcessField_duration', '5')
        self.click('adminAddProcess')
        self.assertEqual(editor.document['processSettings']['review']['properties']['duration'], 5)
        self.click('graphNode_review')
        self.enter('adminProcessField_duration', '7')
        self.click('adminEditPipeline')
        self.assertEqual(editor.document['processSettings']['review']['properties']['duration'], 7)
        self.assertEqual(editor.selectedNode, '')
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_dependency_and_progress_select_catalog_process_names_or_codes(self):
        editor = self.admin.workflowEditor
        editor.select_node('model')
        for kind, section, process_value in (('dependency', 'default', 'review'), ('progress', 'progress', 'PR2')):
            editor.set_attribute('type', kind)
            frame(self.window)
            self.choose('adminProcessField_related_search_type', 'demo/asset')
            self.choose('adminProcessField_related_pipeline_code', 'demo/sub')
            self.choose('adminProcessField_related_process', process_value)
            self.assertEqual(editor.processSettings[section]['related_process'], process_value)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_optional_estimate_can_be_cleared_with_the_keyboard(self):
        self.click('graphNode_model')
        self.enter('adminProcessField_duration', '3')
        QTest.keyClick(self.window, Qt.Key_Tab)
        frame(self.window)
        self.click('adminProcessField_duration')
        QTest.keyClick(self.window, Qt.Key_A, Qt.ControlModifier)
        QTest.keyClick(self.window, Qt.Key_Backspace)
        QTest.keyClick(self.window, Qt.Key_Tab)
        frame(self.window)
        self.assertEqual(self.admin.workflowEditor.processProperties['duration'], '')
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_color_picker_cancels_without_editing_and_accepts_into_the_native_draft(self):
        self.click('graphNode_model')
        editor = self.admin.workflowEditor
        field = self.item('adminProcessField_color')
        self.assertIsNone(field.findChild(QObject, 'adminProcessField_color_dialog'))
        self.click('adminProcessField_color_choose')
        frame(self.window)
        picker = field.findChild(QObject, 'adminProcessField_color_dialog')
        self.assertTrue(picker.property('visible'))
        output = os.environ.get('ADMIN_GRAPH_FORM_SCREENSHOTS')
        if output:
            path = Path(output)
            path.mkdir(parents=True, exist_ok=True)
            self.window.grabWindow().save(str(path / 'color_picker.png'))
        self.enter('adminProcessField_color_dialog_hex', '#b85435')
        QTest.keyClick(self.window, Qt.Key_Tab)
        self.color_dialog_button('Cancel')
        frame(self.window)
        self.assertFalse(editor.dirty)
        self.window.requestActivate()
        self.assertTrue(QTest.qWaitForWindowActive(self.window, 1000))
        button = self.item('adminProcessField_color_choose')
        button.forceActiveFocus()
        frame(self.window)
        QTest.keyClick(self.window, Qt.Key_Space)
        frame(self.window)
        self.assertTrue(picker.property('visible'))
        self.enter('adminProcessField_color_dialog_hex', '#356eb8')
        QTest.keyClick(self.window, Qt.Key_Tab)
        self.color_dialog_button('OK')
        frame(self.window)
        self.assertEqual(editor.processProperties['color'], '#356eb8')
        self.assertEqual(editor.selectedAttributes['color'], '#356eb8')
        with self.assertRaises(StopIteration):
            self.item('adminGraphAttribute_process_code')
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_color_picker_supports_pointer_keyboard_and_drag(self):
        self.click('graphNode_model')
        self.click('adminProcessField_color_choose')
        plane = self.item('adminProcessField_color_dialog_plane')
        field = self.item('adminProcessField_color')
        picker = field.findChild(QObject, 'adminProcessField_color_dialog')
        center = plane.mapToScene(QPointF(plane.width() / 2, plane.height() / 2)).toPoint()
        QTest.mouseClick(self.window, Qt.LeftButton, pos=center)
        frame(self.window)
        self.assertAlmostEqual(picker.property('saturation'), 0.5, delta=0.01)
        QTest.keyClick(self.window, Qt.Key_Left)
        frame(self.window)
        self.assertAlmostEqual(picker.property('saturation'), 0.49, delta=0.01)
        end = center + QPoint(55, 25)
        QTest.mousePress(self.window, Qt.LeftButton, pos=center)
        QTest.mouseMove(self.window, center + QPoint(25, 10))
        QTest.mouseMove(self.window, end)
        frame(self.window)
        self.assertGreater(picker.property('saturation'), 0.6)
        self.assertLess(picker.property('brightness'), 0.5)
        QTest.mouseRelease(self.window, Qt.LeftButton, pos=end)
        hue = self.item('adminProcessField_color_dialog_hue')
        hue.forceActiveFocus()
        previous_hue = picker.property('hue')
        QTest.keyClick(self.window, Qt.Key_Right)
        frame(self.window)
        self.assertAlmostEqual(picker.property('hue'), previous_hue + 0.005)
        QTest.keyClick(self.window, Qt.Key_Escape)
        frame(self.window)
        self.assertFalse(picker.property('visible'))
        self.assertFalse(self.admin.workflowEditor.dirty)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_color_picker_supports_touch(self):
        self.click('graphNode_model')
        self.click('adminProcessField_color_choose')
        field = self.item('adminProcessField_color')
        picker = field.findChild(QObject, 'adminProcessField_color_dialog')
        plane = self.item('adminProcessField_color_dialog_plane')
        point = plane.mapToScene(QPointF(plane.width() / 4, plane.height() / 4)).toPoint()
        device = QTest.createTouchDevice()
        sequence = QTest.touchEvent(self.window, device, autoCommit=False)
        sequence.press(0, point, self.window).commit()
        frame(self.window)
        sequence.release(0, point, self.window).commit()
        frame(self.window)
        self.assertAlmostEqual(picker.property('saturation'), 0.25, delta=0.01)
        self.assertAlmostEqual(picker.property('brightness'), 0.75, delta=0.01)
        self.color_dialog_button('Cancel')
        self.assertFalse(self.admin.workflowEditor.dirty)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_color_picker_fits_narrow_and_wide_windows_and_does_not_whiten_the_background(self):
        self.click('graphNode_model')
        field = self.item('adminProcessField_color')
        theme = field.property('theme')
        for dark in (True, False):
            theme.setProperty('dark', dark)
            for size in ((900, 620), (1400, 940)):
                self.window.resize(*size)
                frame(self.window)
                before = self.window.grabWindow().pixelColor(10, 10).lightnessF()
                self.click('adminProcessField_color_choose')
                frame(self.window)
                picker = field.findChild(QObject, 'adminProcessField_color_dialog')
                self.assertLessEqual(self.window.grabWindow().pixelColor(10, 10).lightnessF(), before)
                hex_field = self.item('adminProcessField_color_dialog_hex')
                self.assert_inside('adminProcessField_color_dialog_hex')
                viewport = hex_field.parentItem()
                while viewport is not None and not viewport.inherits('QQuickFlickable'):
                    viewport = viewport.parentItem()
                self.assertIsNotNone(viewport)
                self.assertLessEqual(viewport.property('contentHeight'), viewport.height() + 1)
                self.color_dialog_button('Cancel')
                self.assertFalse(picker.property('visible'))
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_forms_keep_page_and_node_type_tabs_while_catalogs_use_comboboxes(self):
        self.click('graphNode_model')
        for page in ('canvas', 'technical'):
            self.click('segmentedButtonSegment_' + page)
            selectors = [item for item in sidebar_fixture.SidebarEditorQmlTests.descendants(self.window.contentItem())
                         if item.isVisible() and item.inherits('QQuickComboBox')]
            expected = {'administrationProjectSelector'}
            if page == 'canvas':
                expected.update('adminProcessField_' + field for field in (
                    'assigned_group', 'supervisor_group', 'task_pipeline'))
            self.assertEqual({item.objectName() for item in selectors}, expected)


if __name__ == '__main__':
    unittest.main()
