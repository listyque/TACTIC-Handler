"""Search-Type-first naming, using the existing editor inside Administration."""

import os
from pathlib import Path
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QCoreApplication, QObject, QPoint, QPointF, Qt, Signal
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QSignalSpy, QTest

from tests.qt_application import gui_test_application
from tests import test_administration_qml as ui_fixture
from tests.profile_ui_responsiveness import frame
from thlib.ui.naming_editor import NamingEditorController


class AdministrationNamingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        self.application = SimpleNamespace(
            can_administer=True, debug_log=None, window_model=Mock(),
            _notify=Mock(), server_url='server', server_user='admin')
        self.checkin = SimpleNamespace(currentObject={}, process='publish', context='publish',
                                       processes=[], contexts=[])
        self.queue = SimpleNamespace(operation=lambda _identity: None)
        self.editor = NamingEditorController(self.application, self.checkin, self.queue)
        self.addCleanup(self.editor.shutdown)
        self.rules = [dict(code='N1', search_type='demo/asset', context='model',
                           dir_naming='{project.code}/{search_type.table_name}',
                           file_naming='{sobject.name}_v{version}.{ext}',
                           __search_key__='config/naming?project=demo&code=N1')]
        self.server = Mock()
        self.server.query.side_effect = self.query
        self.server_start = self.enterContext(patch('thlib.tactic_classes.server_start', return_value=self.server))
        self.enterContext(patch.object(self.editor, '_start_worker',
                                      side_effect=lambda work, done: done(work())))

    def query(self, search_type, filters, **_kwargs):
        if search_type == 'config/naming':
            self.assertEqual(filters, [('search_type', 'demo/asset')])
            return self.rules
        if search_type == 'sthpw/project':
            return {'code': 'demo', 'title': 'Demo project'}
        raise AssertionError('Type naming must not fetch an arbitrary Search Object')

    def begin_type(self):
        self.assertTrue(self.editor.begin_search_type('demo', 'demo/asset', 'Assets'))

    def test_type_is_the_owner_not_an_existing_rule_or_workspace_object(self):
        self.begin_type()
        self.application.window_model.show_child_window.assert_not_called()
        self.application.window_model.show_window.assert_not_called()
        self.assertTrue(self.editor.typeMode)
        self.assertEqual(self.editor.currentObject, {
            'projectCode': 'demo', 'searchType': 'demo/asset', 'title': 'Assets'})
        self.assertEqual(self.editor.rulesModel.rowCount(), 1)
        self.assertEqual(self.editor.previewDirectory, 'demo/asset')

    def test_type_with_no_rules_can_create_its_first_rule(self):
        self.rules.clear()
        self.begin_type()
        self.assertEqual(self.editor.rulesModel.rowCount(), 0)
        self.editor.create_rule()
        self.assertEqual(self.editor.selectedRule['search_type'], 'demo/asset')
        self.editor.set_field('search_type', 'demo/shot')
        self.assertEqual(self.editor.selectedRule['search_type'], 'demo/asset')
        self.server.insert.return_value = {'code': 'N2'}
        self.server_start.reset_mock()
        self.assertTrue(self.editor.save())
        args, options = self.server.insert.call_args
        self.assertEqual(args[0], 'config/naming')
        self.assertEqual(args[1]['search_type'], 'demo/asset')
        self.assertTrue(options['triggers'])
        self.assertEqual(self.server_start.call_args_list[0].kwargs, {'project': 'demo'})

    def test_existing_rule_updates_native_identity_in_the_captured_project(self):
        self.begin_type()
        self.editor.set_field('file_naming', 'updated.{ext}')
        self.server_start.reset_mock()
        self.server.insert_update.return_value = {'code': 'N1'}
        self.assertTrue(self.editor.save())
        args, options = self.server.insert_update.call_args
        self.assertEqual(args[0], 'config/naming?project=demo&code=N1')
        self.assertEqual(args[1]['file_naming'], 'updated.{ext}')
        self.assertTrue(options['triggers'])
        self.assertEqual(self.server_start.call_args_list[0].kwargs, {'project': 'demo'})

    def test_reopening_same_type_keeps_draft_without_loading_again(self):
        self.begin_type()
        self.editor.set_field('file_naming', 'draft.{ext}')
        self.server.query.reset_mock()
        self.begin_type()
        self.assertEqual(self.editor.selectedRule['file_naming'], 'draft.{ext}')
        self.server.query.assert_not_called()
        self.assertFalse(self.editor.begin_search_type('other', 'demo/shot', 'Shots'))
        self.assertEqual(self.editor.currentObject['searchType'], 'demo/asset')

    def test_non_admin_cannot_enter_type_naming(self):
        self.application.can_administer = False
        self.assertFalse(self.editor.begin_search_type('demo', 'demo/asset', 'Assets'))
        self.server.query.assert_not_called()

    def test_reset_discards_first_local_rule(self):
        self.rules.clear()
        self.begin_type()
        self.editor.create_rule()
        self.editor.reset()
        self.assertFalse(self.editor.dirty)
        self.assertFalse(self.editor.isNew)
        self.assertEqual(self.editor.selectedRule, {})

    def test_queue_entry_still_loads_object_scoped_rules_after_type_edit(self):
        self.begin_type()
        self.queue.operation = lambda _identity: {
            'searchKey': 'skey://shots_project/demo/shot?code=S1',
            'objectTitle': 'Shot one', 'context': 'render/review',
            'process': 'render', 'files': [{'path': 'shot.ma'}], 'version': 3}
        self.server.query.side_effect = None
        self.server.query.return_value = {}
        self.server.split_search_key.return_value = ('demo/shot?project=shots_project', 'S1')
        self.editor.prepare_operation('OP1')
        self.editor.begin()
        self.assertFalse(self.editor.typeMode)
        self.assertEqual(self.editor.currentObject['projectCode'], 'shots_project')
        self.assertEqual(self.editor.sampleFile, 'shot.ma')
        self.assertEqual(self.editor.sampleVersion, 3)
        self.assertEqual(self.editor.previewContext, 'render/review')
        self.server.query.assert_any_call('config/naming', [('search_type', 'demo/shot')],
                                          order_bys=['context', 'code'])

    def test_server_change_disconnects_requests_and_rejects_queued_results_and_errors(self):
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
        self.editor._generation = 1
        with patch.object(env_inst, 'server_pool', SimpleNamespace(is_stopped=False, add_task=lambda _work: worker)):
            NamingEditorController._start_worker(self.editor, lambda: None, self.editor._rules_loaded)
        worker.result.emit({'generation': 1, 'records': self.rules})
        worker.error.emit(ValueError('stale error'))
        self.application.server_url = 'other server'
        self.editor.server_changed()
        QCoreApplication.processEvents()
        self.assertTrue(worker.cancelled)
        self.assertIsNone(self.editor._worker_callbacks)
        self.assertEqual(self.editor.rulesModel.rowCount(), 0)
        self.assertEqual(self.editor.currentObject, {})
        self.assertEqual(self.editor.error, '')


class AdministrationNamingQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ui_fixture.AdministrationQmlTests.setUpClass()

    def setUp(self):
        self.ui = ui_fixture.AdministrationQmlTests()
        self.ui.setUp()
        self.addCleanup(self.ui.doCleanups)
        self.fixture = self.ui.fixture
        self.editor = NamingEditorController(
            self.fixture.application,
            SimpleNamespace(currentObject={}, process='publish', context='publish', processes=[], contexts=[]),
            SimpleNamespace(operation=lambda _identity: None))
        self.addCleanup(self.editor.shutdown)
        self.ui.admin.attach_naming_editor(self.editor)
        context = self.fixture.engine.rootContext()
        context.setContextProperty('namingEditorController', self.editor)
        context.setContextProperty('namingEditorModel', self.editor.model)
        self.server = Mock()
        self.rules = []
        self.server.query.side_effect = lambda table, *args, **kw: (
            self.rules if table == 'config/naming' else {'code': 'demo', 'title': 'Demo project'})
        self.enterContext(patch('thlib.tactic_classes.server_start', return_value=self.server))
        self.enterContext(patch.object(self.editor, '_start_worker',
                                      side_effect=lambda work, done: done(work())))
        self.window = self.ui.window
        self.ui.click('adminSection_types')
        self.ui.click('segmentedButtonSegment_entity_naming')
        frame(self.window)

    def item(self, name):
        return self.ui.item(name)

    def click(self, name):
        self.ui.click(name)

    def test_type_tab_embeds_existing_editor_without_a_native_child_window(self):
        self.assertFalse(self.fixture.application.window_model.is_window_visible('naming_editor'))
        self.assertEqual(self.editor.currentObject['searchType'], 'demo/asset')
        self.assertEqual(self.item('namingTargetTitle').property('text'), 'Assets')
        self.assertEqual(self.server.query.call_count, 2)
        self.server.query.assert_any_call('config/naming', [('search_type', 'demo/asset')],
                                          order_bys=['context', 'code'])
        self.click('namingCreate')
        self.editor.set_field('file_naming', 'draft.{ext}')
        self.click('segmentedButtonSegment_entity_details')
        self.click('segmentedButtonSegment_entity_naming')
        self.assertEqual(self.editor.selectedRule['file_naming'], 'draft.{ext}')
        self.assertEqual(self.server.query.call_count, 2)
        self.assertTrue(self.ui.admin.projectLocked)

    def test_first_rule_is_created_for_selected_type_and_saved_by_existing_editor(self):
        self.assertEqual(self.editor.rulesModel.rowCount(), 0)
        self.assertTrue(self.item('namingCreate').isEnabled())
        self.click('namingCreate')
        self.assertEqual(self.editor.selectedRule['search_type'], 'demo/asset')
        self.assertTrue(self.item('namingSearchType').property('readOnly'))
        self.server.insert.return_value = {'code': 'N1'}
        self.window.requestActivate()
        save = self.item('namingSave')
        save.forceActiveFocus()
        frame(self.window)
        QTest.keyClick(self.window, Qt.Key_Space)
        frame(self.window)
        self.assertEqual(self.server.insert.call_count, 1)
        self.assertEqual(self.server.insert.call_args.args[1]['search_type'], 'demo/asset')
        self.assertFalse(self.editor.dirty)
        self.assertFalse(self.fixture.application.window_model.is_window_visible('naming_editor'))

    def test_selecting_another_type_without_rules_changes_the_owner(self):
        self.click('segmentedButtonSegment_entity_summary')
        types = self.ui.admin.typesEditor
        types._catalog.append({'identity': 'demo/shot', 'label': 'Shots', 'projectLocal': True})
        types.stateChanged.emit()

        def loaded(_action, identity):
            self.ui.seed(types, identity, {'title': 'Shots', 'description': '', 'columns': [], 'color': ''}, {})

        with patch.object(types, '_request', side_effect=loaded):
            self.click('adminSearchType_demo/shot')
        self.click('segmentedButtonSegment_entity_naming')
        self.assertEqual(self.editor.currentObject['searchType'], 'demo/shot')
        self.assertEqual(self.item('namingTargetTitle').property('text'), 'Shots')
        self.assertEqual(self.editor.rulesModel.rowCount(), 0)
        self.click('namingCreate')
        self.assertEqual(self.editor.selectedRule['search_type'], 'demo/shot')
        self.server.query.assert_any_call('config/naming', [('search_type', 'demo/shot')],
                                          order_bys=['context', 'code'])

    def test_inline_layout_at_narrow_wide_sizes_and_scrolling(self):
        self.click('namingCreate')
        for width, height in ((900, 620), (1500, 940)):
            self.window.resize(width, height)
            frame(self.window)
            for name in ('namingCreate', 'namingReload', 'namingSave', 'namingReset', 'namingFieldsScroll'):
                item = self.item(name)
                point = item.mapToScene(QPointF())
                self.assertGreaterEqual(point.x(), 0, name)
                self.assertGreaterEqual(point.y(), 0, name)
                self.assertLessEqual(point.x() + item.width(), self.window.width(), name)
                self.assertLessEqual(point.y() + item.height(), self.window.height(), name)
            scroll = self.item('namingFieldsScroll')
            scroll.setProperty('contentY', 0)
            frame(self.window)
            output = os.environ.get('NAMING_SCREENSHOTS')
            if output:
                Path(output).mkdir(parents=True, exist_ok=True)
                self.window.grabWindow().save(str(Path(output) / ('inline_naming_' + str(width) + '.png')))
            point = scroll.mapToScene(QPointF(scroll.width() / 2, scroll.height() / 2))
            stopped = QSignalSpy(scroll.movementEnded)
            event = QWheelEvent(point, self.window.mapToGlobal(point.toPoint()), QPoint(), QPoint(0, -12000),
                                Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False)
            event.setTimestamp(time.monotonic_ns() // 1_000_000)
            QCoreApplication.sendEvent(self.window, event)
            if scroll.property('moving'):
                self.assertTrue(stopped.wait(2000))
            frame(self.window)
            bar = self.fixture.item(self.window, 'namingFieldsBar')
            self.assertEqual(bar.isVisible(), scroll.property('contentHeight') > scroll.height())
            if scroll.property('contentHeight') > scroll.height():
                self.assertGreater(scroll.property('contentY'), 0)
            field = self.item('namingSearchType')
            self.assertLessEqual(field.mapToScene(QPointF()).x() + field.width(),
                                 bar.mapToScene(QPointF()).x())
