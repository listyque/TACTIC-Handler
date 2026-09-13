"""Schema-owned type creation through the real native window and worker path."""

import copy
import hashlib
import os
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QObject, QPointF, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QImage
from PySide6.QtTest import QTest

from thlib.environment import env_inst
from thlib.ui.admin.documents import GraphDocument
from tests import test_administration_qml as admin_fixture
from tests.profile_ui_responsiveness import frame


class SchemaTypeCreationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        admin_fixture.AdministrationQmlTests.setUpClass()

    def setUp(self):
        self.ui = admin_fixture.AdministrationQmlTests()
        self.ui.setUp()
        self.addCleanup(self.ui.doCleanups)
        self.admin = self.ui.admin
        self.editor = self.admin.schemaEditor
        self.creator = self.admin.schemaTypeEditor
        self.editor._revision = hashlib.sha256(self.editor.document['xml'].encode()).hexdigest()
        self.ui.window.resize(1400, 940)
        self.ui.click('adminSection_schema')
        self.windows = self.ui.fixture.application.window_model
        self.addCleanup(self.windows.close_window, 'schema_search_type')
        self.enterContext(patch.object(self.admin, '_refresh_pending_metadata'))
        self.checkin = Mock()
        self.creator.attach_checkin_controller(self.checkin)

    def select_preview(self):
        from thlib.environment import env_mode
        path = Path(env_mode.current_path) / 'new_type_preview.png'
        image = QImage(120, 80, QImage.Format_RGB32)
        image.fill(QColor('#54a878'))
        self.assertTrue(image.save(str(path)))
        self.assertTrue(self.item('adminSearchTypeChoosePreview').isVisible())
        preview = self.item('adminSearchTypePreview')
        owner = preview.parentItem()
        while owner is not None and owner.findChild(QObject, 'adminSearchTypePreviewDialog') is None:
            owner = owner.parentItem()
        dialog = owner.findChild(QObject, 'adminSearchTypePreviewDialog')
        dialog.setProperty('selectedFile', QUrl.fromLocalFile(str(path)))
        dialog.accepted.emit()
        frame(self.window)
        self.assertEqual(Path(self.creator.document['previewPath']), path)
        self.checkin.prepare_external_checkin.assert_not_called()
        return path

    def open_creator(self, keyboard=False):
        if keyboard:
            self.ui.item('adminCreateSchemaType').forceActiveFocus()
            QTest.keyClick(self.ui.window, Qt.Key_Space)
            frame(self.ui.window)
        else:
            self.ui.click('adminCreateSchemaType')
        self.window = self.ui.fixture.window('schema_search_type')
        frame(self.window)
        return self.window

    def item(self, name):
        return self.ui.fixture.item(self.window, name)

    def click(self, name):
        item = self.item(name)
        point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
        QTest.mouseClick(self.window, Qt.LeftButton, pos=point)
        frame(self.ui.window if name in ('adminConfirmSave', 'adminDiscardDocument') else self.window)

    def type_text(self, name, text):
        self.click(name)
        QTest.keyClick(self.window, Qt.Key_A, Qt.ControlModifier)
        for character in text:
            QTest.keyClick(self.window, character)
        frame(self.window)

    def response(self):
        server = GraphDocument('schema', self.editor._original['xml'])
        server.add_node('demo/episodes')
        server.node('demo/episodes').set('xpos', '0')
        server.node('demo/episodes').set('ypos', '0')
        xml = server.xml()
        return {
            'identity': 'demo/episodes', 'revision': 'type-revision', 'canWrite': True,
            'document': {'title': 'Episodes', 'description': '', 'color': '#6699aa', 'columns': []},
            'catalog': self.editor.metadata['searchTypes'] + [
                {'identity': 'demo/episodes', 'label': 'Episodes', 'color': '#6699aa'}],
            'metadata': {'columns': {'code': {'data_type': 'varchar'}},
                         'searchKey': 'sthpw/search_object?code=demo/episodes',
                         'schema': {'xml': xml, 'revision': hashlib.sha256(xml.encode()).hexdigest()}},
        }

    def worker(self, execute=False):
        class Worker(QObject):
            result = Signal(object)
            error = Signal(object)
            cancelled = False

            def start(self):
                if execute:
                    self.result.emit(self.operation())

            def cancel(self):
                self.cancelled = True

        worker = Worker()

        def add_task(operation):
            worker.operation = operation
            return worker

        self.enterContext(patch.object(env_inst.server_pool, 'add_task', side_effect=add_task))
        return worker

    def test_keyboard_opens_owned_modal_without_query_and_cancel_keeps_both_drafts(self):
        self.editor.move_node('demo/asset', -90, 155)
        self.admin.typesEditor.set_field('description', 'Another unsaved type')
        original_graph = copy.deepcopy(self.editor.document)
        original_type = copy.deepcopy(self.admin.typesEditor.document)
        with patch('thlib.tactic_classes.execute_procedure_serverside') as rpc:
            self.open_creator(keyboard=True)
            self.assertEqual(self.window.modality(), Qt.WindowModal)
            self.assertEqual(self.window.transientParent(), self.ui.window)
            self.assertTrue(self.admin.projectLocked)
            self.type_text('adminSearchTypeTitle', 'Unsaved type')
            self.assertEqual(self.creator.document['title'], 'Unsaved type')
            self.click('adminDiscardDocument')
            frame(self.ui.window)
            rpc.assert_not_called()
        self.assertFalse(self.windows.is_window_visible('schema_search_type'))
        self.assertEqual(self.editor.document, original_graph)
        self.assertEqual(self.admin.typesEditor.document, original_type)
        self.assertEqual(self.creator.document, {})
        self.assertEqual(self.ui.fixture.warnings, [])

    def test_confirmed_creation_keeps_unsaved_graph_and_updates_revision_once(self):
        self.editor.move_node('demo/asset', -90, 155)
        self.editor.select_edge(0)
        self.editor.set_attribute('path', 'draft_path')
        canvas = self.ui.item('adminGraphCanvas')
        canvas.setProperty('contentX', 310)
        frame(self.ui.window)
        origin = (canvas.property('contentX'), canvas.property('contentY'))
        old_revision = self.editor._revision
        self.open_creator()
        self.type_text('adminSearchTypeTitle', 'Episodes')
        path = self.select_preview()
        response = self.response()
        callbacks = []

        class Worker(QObject):
            result = Signal(object)
            error = Signal(object)

            def start(self):
                self.result.emit(callbacks[0]())

            def cancel(self):
                pass

        worker = Worker()

        def create_task(operation):
            callbacks.append(operation)
            return worker

        with patch.object(env_inst.server_pool, 'add_task', side_effect=create_task), \
                patch('thlib.tactic_classes.execute_procedure_serverside', return_value=response) as rpc, \
                patch('thlib.server_cache.invalidate_domains') as invalidate:
            self.click('adminTypeWizardNext')
            self.click('adminTypeWizardNext')
            self.click('adminSaveDocument')
            self.assertEqual(callbacks, [])
            self.click('adminConfirmSave')
            frame(self.ui.window)
        self.assertEqual(rpc.call_count, 1)
        self.assertEqual(rpc.call_args.args[1]['schema_revision'], old_revision)
        self.assertNotIn('name', rpc.call_args.args[1]['document'])
        self.assertNotIn('previewPath', rpc.call_args.args[1]['document'])
        self.checkin.prepare_external_checkin.assert_called_once()
        queued = self.checkin.prepare_external_checkin.call_args.kwargs
        self.assertEqual(queued['search_key'], response['metadata']['searchKey'])
        self.assertEqual(queued['context'], 'icon')
        self.assertEqual([Path(value) for value in queued['paths']], [path])
        self.assertEqual(invalidate.call_count, 2)
        self.assertFalse(self.windows.is_window_visible('schema_search_type'))
        self.assertEqual(self.editor._revision, response['metadata']['schema']['revision'])
        self.assertEqual(self.editor.selectedNode, 'demo/episodes')
        self.assertTrue(self.editor.dirty)
        graph = GraphDocument('schema', self.editor.document['xml'])
        self.assertEqual(graph.node('demo/asset').get('xpos'), '-90')
        self.assertEqual(graph.edges()[0]['path'], 'draft_path')
        self.assertIn('<!--keep-->', graph.xml())
        self.assertIsNotNone(graph.root.find('extension'))
        self.assertEqual((canvas.property('contentX'), canvas.property('contentY')), origin)
        node = self.ui.item('graphNode_demo/episodes')
        center = canvas.mapFromItem(node, QPointF(node.width() / 2, node.height() / 2))
        self.assertAlmostEqual(center.x(), canvas.width() / 2, delta=1)
        self.assertAlmostEqual(center.y(), canvas.height() / 2, delta=1)
        self.assertTrue(any(row['identity'] == 'demo/episodes' for row in self.admin.typesEditor.catalog))
        self.editor.discard()
        self.assertFalse(self.editor.dirty)
        self.assertIn('demo/episodes', self.editor.document['xml'])
        self.assertNotIn('draft_path', self.editor.document['xml'])
        self.assertEqual(self.ui.fixture.warnings, [])

    def test_failure_keeps_creation_form_and_busy_close_waits_for_result(self):
        self.open_creator()
        self.creator.set_field('title', 'Episodes')
        path = self.select_preview()
        before = copy.deepcopy(self.editor.document)
        worker = self.worker()
        self.creator.save()
        self.assertTrue(self.creator.busy)
        self.window.close()
        frame(self.window)
        self.assertTrue(self.windows.is_window_visible('schema_search_type'))
        worker.error.emit(({'exception': ValueError('Schema changed on the server.'),
                            'stacktrace': 'test conflict'}, worker))
        frame(self.window)
        self.assertFalse(self.creator.busy)
        self.assertIn('Schema changed', self.creator.error)
        self.assertEqual(self.creator.document['title'], 'Episodes')
        self.assertEqual(Path(self.creator.document['previewPath']), path)
        self.checkin.prepare_external_checkin.assert_not_called()
        self.assertEqual(self.editor.document, before)
        self.assertTrue(self.item('adminDocumentError').isVisible())
        self.assertEqual(self.ui.fixture.warnings, [])

    def test_preview_queue_failure_keeps_created_type_open_and_retry_does_not_recreate_node(self):
        self.open_creator()
        self.creator.set_field('title', 'Episodes')
        path = self.select_preview()
        created = self.response()
        saved = copy.deepcopy(created)
        del saved['metadata']['schema']
        self.checkin.prepare_external_checkin.side_effect = [ValueError('Repository unavailable'), None]
        self.worker(execute=True)
        with patch('thlib.tactic_classes.execute_procedure_serverside', side_effect=[created, saved]) as rpc, \
                patch('thlib.server_cache.invalidate_domains'), \
                patch.object(self.editor, 'accept_created_type', wraps=self.editor.accept_created_type) as accept:
            self.creator.save()
            frame(self.ui.window)
            self.assertTrue(self.windows.is_window_visible('schema_search_type'))
            self.assertEqual(self.creator.identity, 'demo/episodes')
            self.assertTrue(self.creator.dirty)
            self.assertEqual(Path(self.creator.document['previewPath']), path)
            self.assertIn('Repository unavailable', self.creator.error)
            self.assertIsNotNone(GraphDocument('schema', self.editor.document['xml']).node('demo/episodes'))
            self.creator.save()
            frame(self.ui.window)
        self.assertEqual(rpc.call_count, 2)
        self.assertEqual(rpc.call_args_list[0].args[1]['identity'], '')
        self.assertIn('schema_revision', rpc.call_args_list[0].args[1])
        self.assertEqual(rpc.call_args_list[1].args[1]['identity'], 'demo/episodes')
        self.assertNotIn('schema_revision', rpc.call_args_list[1].args[1])
        accept.assert_called_once()
        self.assertEqual(self.checkin.prepare_external_checkin.call_count, 2)
        self.assertFalse(self.windows.is_window_visible('schema_search_type'))
        self.assertEqual(self.creator.document, {})
        self.assertEqual(self.ui.fixture.warnings, [])

    def test_server_change_cancels_creation_and_ignores_late_completion(self):
        self.open_creator()
        response = self.response()
        worker = self.worker()
        self.creator.save()
        self.ui.fixture.application._server_url = 'http://another.example'
        self.admin._server_key = ('different', 'user')
        self.admin._server_changed()
        worker.result.emit(response)
        frame(self.ui.window)
        self.assertTrue(worker.cancelled)
        self.assertFalse(self.windows.is_window_visible('schema_search_type'))
        self.assertEqual(self.creator.document, {})
        self.assertEqual(self.editor.nodes, [])

    def test_readonly_schema_cannot_create_type(self):
        self.editor._can_write = False
        self.editor.stateChanged.emit()
        frame(self.ui.window)
        self.assertFalse(self.ui.item('adminCreateSchemaType').isEnabled())
        self.creator.open(10, 20)
        self.assertFalse(self.windows.is_window_visible('schema_search_type'))

    def test_touch_creates_one_modal_and_new_type_window_is_not_restored_open(self):
        point = self.ui.item('adminCreateSchemaType')
        device = QTest.createTouchDevice()
        center = point.mapToScene(QPointF(point.width() / 2, point.height() / 2)).toPoint()
        QTest.touchEvent(self.ui.window, device).press(0, center, self.ui.window).commit()
        QTest.touchEvent(self.ui.window, device).release(0, center, self.ui.window).commit()
        frame(self.ui.window)
        self.window = self.ui.fixture.window('schema_search_type')
        self.creator.set_field('title', 'Keep current draft')
        self.creator.open(200, 300)
        self.assertEqual(self.creator.document['title'], 'Keep current draft')
        self.assertEqual(sum(window.isVisible() and window.property('kind') == 'schema_search_type'
                             for window in self.ui.fixture.app.allWindows()), 1)
        from thlib.ui.workspace_models.windows import FloatingWindowModel
        restored = FloatingWindowModel(dict(self.windows._settings))
        self.assertFalse(restored.is_window_visible('schema_search_type'))
        self.assertEqual(self.ui.fixture.warnings, [])

    def test_narrow_and_wide_form_keeps_fields_and_save_inside_gutters(self):
        self.open_creator()
        self.creator.set_field('title', 'Episodes')
        self.select_preview()
        for width, height in ((600, 560), (980, 800)):
            self.window.resize(width, height)
            frame(self.window)
            viewport = self.item('adminSearchTypeForm')
            viewport.setProperty('contentY', 0)
            field = self.item('adminSearchTypeTitle')
            self.assertTrue(field.isEnabled())
            self.assertGreaterEqual(field.mapToScene(QPointF()).x(), 14)
            self.assertLess(field.mapToScene(QPointF(field.width(), 0)).x(), width - 14)
            save = self.item('adminSaveDocument')
            self.assertLessEqual(save.mapToScene(QPointF(save.width(), save.height())).y(), height - 14)
            self.click('segmentedButtonSegment_entity_fields')
            frame(self.window)
            self.assertTrue(viewport.property('clip'))
            defaults = self.item('adminAutomaticFieldNames')
            self.assertTrue(defaults.isVisible())
            self.assertIn('relative_dir', defaults.property('text'))
            self.assertEqual(self.creator.document['columns'], [])
            self.assertGreaterEqual(defaults.height(), defaults.property('contentHeight'))
            output = os.environ.get('SCHEMA_TYPE_SCREENSHOTS')
            if output:
                Path(output).mkdir(parents=True, exist_ok=True)
                self.window.grabWindow().save(str(Path(output) / ('default_fields_%s.png' % width)))
            self.click('segmentedButtonSegment_entity_details')
            viewport.setProperty('contentY', max(0, viewport.property('contentHeight') - viewport.height()))
            frame(self.window)
            for name in ('adminSearchTypePreview', 'adminSearchTypeChoosePreview',
                         'adminSearchTypeCancelPreview'):
                control = self.item(name)
                top = control.mapToScene(QPointF())
                self.assertGreaterEqual(top.x(), 14)
                self.assertLess(top.x() + control.width(), width - 14)
                self.assertGreaterEqual(top.y(), viewport.mapToScene(QPointF()).y())
                self.assertLessEqual(top.y() + control.height(),
                                     viewport.mapToScene(QPointF(0, viewport.height())).y())
            output = os.environ.get('SCHEMA_TYPE_SCREENSHOTS')
            if output:
                Path(output).mkdir(parents=True, exist_ok=True)
                self.window.grabWindow().save(str(Path(output) / ('create_type_%s.png' % width)))
        self.assertEqual(self.ui.fixture.warnings, [])

    def test_wizard_validates_steps_preserves_fields_and_reviews_the_actual_draft(self):
        self.open_creator()
        self.assertFalse(self.item('adminSaveDocument').isEnabled())
        back = self.window.contentItem().findChild(QObject, 'adminTypeWizardBack')
        self.assertFalse(back.isVisible())
        self.click('adminTypeWizardNext')
        self.assertTrue(self.creator.error)
        self.assertTrue(self.item('adminSearchTypeTitle').isVisible())
        self.type_text('adminSearchTypeTitle', 'Episodes')
        self.type_text('adminSearchTypeDescription', 'Animated episodes for the show')
        self.creator.set_field('color', '#c95873')
        self.select_preview()
        self.item('adminTypeWizardNext').forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Space)
        frame(self.window)
        self.assertTrue(self.item('adminAutomaticFieldNames').isVisible())
        self.assertTrue(self.creator.add_column('duration_minutes', 'integer'))
        self.click('adminTypeWizardNext')
        self.assertEqual(self.item('adminSearchTypeCreationTitle').property('text'), 'Episodes')
        self.assertEqual(self.item('adminSearchTypeCreationTitle').property('color').name(), '#c95873')
        self.assertEqual(self.item('adminSearchTypeCreationDescription').property('text'),
                         'Animated episodes for the show')
        self.assertEqual(self.item('adminSearchTypeCreationPreview').property('source').toString(),
                         self.creator.previewUrl)
        self.assertIn('duration_minutes (integer)',
                      self.item('adminSearchTypeCreationAdditionalFields').property('description'))
        self.assertIn('relative_dir',
                      self.item('adminSearchTypeCreationStandardFields').property('description'))
        self.assertTrue(self.item('adminSaveDocument').isEnabled())
        next_action = self.window.contentItem().findChild(QObject, 'adminTypeWizardNext')
        self.assertFalse(next_action.isVisible())
        for width, height in ((600, 560), (980, 800)):
            self.window.resize(width, height)
            frame(self.window)
            for name in ('adminTypeWizardBack', 'adminSaveDocument'):
                control = self.item(name)
                bottom = control.mapToScene(QPointF(control.width(), control.height()))
                self.assertLessEqual(bottom.x(), width - 14)
                self.assertLessEqual(bottom.y(), height - 14)
            output = os.environ.get('SCHEMA_TYPE_SCREENSHOTS')
            if output:
                Path(output).mkdir(parents=True, exist_ok=True)
                self.assertTrue(self.window.grabWindow().save(str(Path(output) / ('review_%s.png' % width))))
        self.click('adminTypeWizardBack')
        self.assertEqual(self.creator.document['columns'], [{'name': 'duration_minutes', 'type': 'integer'}])
        self.assertFalse(self.item('adminSaveDocument').isEnabled())
        self.assertEqual(self.ui.fixture.warnings, [])


if __name__ == '__main__':
    unittest.main()
