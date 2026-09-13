"""Real mouse/keyboard/touch paths for schema actions, without a live server."""

import copy
import hashlib
import os
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QObject, QPointF, Qt, Signal
from PySide6.QtTest import QTest

from thlib.environment import env_inst
from tests import test_admin_graph_forms as graph_fixture
from tests.profile_ui_responsiveness import frame


class SchemaNodeActionsQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        graph_fixture.AdminGraphFormsTests.setUpClass()

    def setUp(self):
        self.ui = graph_fixture.AdminGraphFormsTests()
        self.ui.setUp()
        self.addCleanup(self.ui.doCleanups)
        self.admin = self.ui.admin
        self.graph = self.admin.schemaEditor
        self.window = self.ui.window
        self.graph._revision = hashlib.sha256(self.graph.document['xml'].encode()).hexdigest()
        self.ui.click('adminSection_schema')
        self.ui.click('graphNode_demo/asset')
        self.enterContext(patch.object(self.admin, '_refresh_pending_metadata'))
        self.workers = []
        self.auto_execute = False

        class Worker(QObject):
            result = Signal(object)
            error = Signal(object)
            cancelled = False

            def start(worker):
                if self.auto_execute:
                    worker.result.emit(worker.operation())

            def cancel(worker):
                worker.cancelled = True

        def add_task(operation):
            worker = Worker()
            worker.operation = operation
            self.workers.append(worker)
            return worker

        self.enterContext(patch.object(env_inst.server_pool, 'add_task', side_effect=add_task))

    def review(self, allowed=True):
        return {'identity': 'demo/asset', 'revision': 'review-revision',
                'document': {'confirmation': ''}, 'canWrite': allowed,
                'metadata': {'title': 'Assets', 'table': 'asset', 'project': 'demo',
                             'objects': 0 if allowed else 7, 'pipelines': [],
                             'aliases': [], 'references': [], 'otherSchemas': [],
                             'sharedRegistration': True, 'schemaRevision': self.graph._revision}}

    def respond(self, payload):
        self.workers[-1].result.emit(payload)
        frame(self.window)

    def screenshot(self, name):
        output = os.environ.get('SCHEMA_ACTION_SCREENSHOTS')
        if output:
            Path(output).mkdir(parents=True, exist_ok=True)
            self.assertTrue(self.window.grabWindow().save(str(Path(output) / (name + '.png'))))

    def test_workflow_shortcut_resolves_exact_type_and_preserves_canvas_draft(self):
        self.graph.move_node('demo/asset', 24, 35)
        before = copy.deepcopy(self.graph.document)
        workflow = self.admin.workflowEditor
        metadata = copy.deepcopy(workflow.metadata)
        metadata['pipelines'].insert(0, {'identity': 'demo/other', 'searchType': 'demo/shot', 'label': 'Other'})
        result = {'canWrite': True, 'identity': '', 'revision': '', 'document': {}, 'metadata': metadata}
        loaded = dict(result, identity='demo/assets', revision='new-revision', document=copy.deepcopy(workflow.document))
        self.auto_execute = True
        with patch('thlib.tactic_classes.execute_procedure_serverside', side_effect=[result, loaded]) as rpc:
            self.ui.item('adminSchemaNodeWorkflows').forceActiveFocus()
            QTest.keyClick(self.window, Qt.Key_Space)
            frame(self.window)
            frame(self.window)
        self.assertEqual(self.admin.section, 'workflow')
        self.assertEqual(workflow.identity, 'demo/assets')
        self.assertEqual([call.args[1]['identity'] for call in rpc.call_args_list], ['demo/asset', 'demo/assets'])
        self.assertEqual(workflow.document['searchType'], 'demo/asset')
        self.assertEqual(self.graph.document, before)
        self.ui.click('adminSection_schema')
        self.assertEqual(self.graph.selectedNode, 'demo/asset')
        self.assertEqual(self.ui.fixture.fixture.warnings, [])

    def test_no_pipeline_opens_a_type_bound_draft_and_dirty_workflow_blocks_navigation(self):
        workflow = self.admin.workflowEditor
        workflow.set_field('name', 'Keep edits')
        self.ui.click('adminSchemaNodeWorkflows')
        self.assertEqual(self.admin.section, 'schema')
        self.assertEqual(self.workers, [])
        workflow.discard()
        metadata = dict(workflow.metadata, pipelines=[])
        self.ui.click('adminSchemaNodeWorkflows')
        self.respond({'identity': '', 'revision': '', 'document': {}, 'metadata': metadata, 'canWrite': True})
        self.assertEqual(self.admin.section, 'workflow')
        self.assertTrue(workflow.dirty)
        self.assertEqual(workflow.document['searchType'], 'demo/asset')
        self.assertEqual(self.ui.fixture.fixture.warnings, [])

    def test_remove_from_canvas_is_local_confirmed_and_undoable_by_discard(self):
        before = copy.deepcopy(self.graph.document)
        self.ui.click('adminRemoveGraphSelection')
        self.ui.click('adminCancelRemoveGraph')
        self.assertEqual(self.graph.document, before)
        self.ui.click('adminRemoveGraphSelection')
        self.ui.click('adminConfirmRemoveGraph')
        self.assertNotIn('demo/asset', self.graph.document['xml'])
        self.assertEqual(self.workers, [])
        self.graph.discard()
        self.assertEqual(self.graph.document, before)

    def test_delete_confirmation_blocks_used_types_then_confirms_one_pinned_target(self):
        before = copy.deepcopy(self.graph.document)
        before_pixel = self.window.grabWindow().pixelColor(10, 10)
        self.ui.click('adminDeleteSchemaSearchType')
        self.assertTrue(self.graph.busy)
        self.assertLess(self.window.grabWindow().pixelColor(10, 10).lightnessF(), before_pixel.lightnessF())
        self.respond(self.review(allowed=False))
        self.assertFalse(self.ui.item('adminConfirmDeleteSearchType').isEnabled())
        self.assertTrue(self.ui.item('adminDeleteSearchTypeBlocks').isVisible())
        self.ui.click('adminCancelDeleteSearchType')
        self.assertEqual(self.graph.document, before)
        self.ui.click('adminDeleteSchemaSearchType')
        review = self.review()
        self.respond(review)
        for width, height in ((900, 620), (1400, 940)):
            self.window.resize(width, height)
            frame(self.window)
            self.ui.assert_inside('adminConfirmDeleteSearchType')
            self.ui.assert_inside('adminCancelDeleteSearchType')
            viewport = self.ui.item('adminDeleteSearchTypeViewport')
            self.assertGreater(viewport.width(), 250)
            self.assertGreater(viewport.height(), 100)
            self.screenshot('delete_' + str(width))
        self.ui.enter('adminDeleteSearchTypeName', 'demo/asset')
        self.assertTrue(self.ui.item('adminConfirmDeleteSearchType').isEnabled())
        self.ui.click('adminConfirmDeleteSearchType')
        self.assertEqual(len(self.workers), 3)
        self.assertTrue(self.graph.busy)
        self.assertTrue(self.graph.deletionEditor.deleting)
        self.assertFalse(self.ui.item('adminConfirmDeleteSearchType').isEnabled())
        self.assertFalse(self.ui.item('adminCancelDeleteSearchType').isEnabled())
        QTest.keyClick(self.window, Qt.Key_Escape)
        frame(self.window)
        self.assertTrue(self.ui.item('adminConfirmDeleteSearchType').isVisible())
        old = self.graph._revision
        result = copy.deepcopy(review)
        result['metadata']['schema'] = {'xml': '<schema><search_type name="demo/shot"/></schema>', 'revision': 'deleted'}
        self.respond(result)
        self.assertNotEqual(self.graph._revision, old)
        self.assertFalse(self.graph.dirty)
        self.assertFalse(self.graph.busy)
        self.assertFalse(self.graph.deletionEditor.deleting)
        self.assertNotIn('demo/asset', self.graph.document['xml'])
        self.assertEqual(self.ui.fixture.fixture.warnings, [])

    def test_cancel_discards_late_review_and_a_failed_delete_can_be_closed(self):
        self.ui.click('adminDeleteSchemaSearchType')
        worker = self.workers[-1]
        late = self.graph.deletionEditor._callbacks[0]
        self.assertTrue(self.ui.item('adminCancelDeleteSearchType').isEnabled())
        QTest.keyClick(self.window, Qt.Key_Escape)
        frame(self.window)
        self.assertTrue(worker.cancelled)
        self.assertFalse(self.graph.busy)
        late(self.review())
        self.assertEqual(self.graph.deletionEditor.document, {})
        self.ui.click('adminDeleteSchemaSearchType')
        self.respond(self.review())
        self.ui.enter('adminDeleteSearchTypeName', 'demo/asset')
        self.ui.click('adminConfirmDeleteSearchType')
        worker = self.workers[-1]
        worker.error.emit(({'exception': ValueError('Deletion details changed'), 'stacktrace': 'test conflict'}, worker))
        frame(self.window)
        self.assertFalse(self.graph.deletionEditor.deleting)
        self.assertTrue(self.ui.item('adminCancelDeleteSearchType').isEnabled())
        self.assertIn('Deletion details changed', self.graph.deletionEditor.error)
        self.assertIn('demo/asset', self.graph.document['xml'])
        self.ui.click('adminCancelDeleteSearchType')
        self.assertEqual(self.ui.fixture.fixture.warnings, [])

    def test_pending_type_and_workflow_edits_block_the_destructive_action(self):
        self.admin.typesEditor.set_field('description', 'Unfinished type edit')
        self.ui.click('adminDeleteSchemaSearchType')
        self.assertEqual(self.workers, [])
        self.assertTrue(self.admin.typesEditor.dirty)
        self.admin.typesEditor.discard()
        self.admin.workflowEditor.set_field('name', 'Unfinished workflow')
        self.ui.click('adminDeleteSchemaSearchType')
        self.assertEqual(self.workers, [])
        self.assertTrue(self.admin.workflowEditor.dirty)
        self.assertEqual(self.ui.fixture.fixture.warnings, [])

    def test_delete_does_not_destroy_pending_edits_and_reset_ignores_late_review(self):
        self.graph.move_node('demo/asset', 25, 50)
        self.ui.click('adminDeleteSchemaSearchType')
        self.assertEqual(self.workers, [])
        self.assertTrue(self.graph.dirty)
        self.graph.discard()
        self.graph.select_node('demo/asset')
        self.ui.click('adminDeleteSchemaSearchType')
        worker = self.workers[-1]
        late = self.graph.deletionEditor._callbacks[0]
        review = self.review()
        self.graph.reset('other')
        late(review)
        self.assertTrue(worker.cancelled)
        self.assertEqual(self.graph.deletionEditor.document, {})
        self.assertEqual(self.graph.nodes, [])

    def test_inspector_add_button_reuses_native_creation_wizard(self):
        self.ui.click('segmentedButtonSegment_add_node')
        button = self.ui.item('adminCreateSchemaTypeFromInspector')
        device = QTest.createTouchDevice()
        point = button.mapToScene(QPointF(button.width() / 2, button.height() / 2)).toPoint()
        QTest.touchEvent(self.window, device).press(0, point, self.window).commit()
        QTest.touchEvent(self.window, device).release(0, point, self.window).commit()
        frame(self.window)
        creator_window = self.ui.fixture.fixture.window('schema_search_type')
        self.assertEqual(creator_window.transientParent(), self.window)
        self.assertEqual(creator_window.modality(), Qt.WindowModal)
        self.assertEqual(self.workers, [])
        self.admin.schemaTypeEditor.discard()
