"""Destructive Search Type edits: draft ownership, native commands and confirmation."""

import copy
import json
import os
from pathlib import Path
import sqlite3
import time
import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QSignalSpy, QTest

from thlib.environment import env_inst
from thlib.ui.admin.search_types_api import search_types_request
from tests import test_administration_api as api_fixture
from tests import test_admin_search_types as ui_fixture
from tests.profile_ui_responsiveness import frame


class ColumnRemovalApiTests(unittest.TestCase):
    def setUp(self):
        self.api = api_fixture.AdministrationApiTests()
        self.api.setUp()
        self.addCleanup(self.api.doCleanups)
        self.api.columns['demo/asset'].update({
            name: {'data_type': 'text'} for name in ('id', 's_status', 'pipeline_code', 'brief', 'notes')})

    def load(self):
        return json.loads(search_types_request('load', 'demo', 'demo/asset'))

    def save(self, loaded, removed):
        document = dict(loaded['document'], removedColumns=removed)
        return json.loads(search_types_request('save', 'demo', 'demo/asset', document, loaded['revision']))

    def test_remove_uses_native_command_and_refreshes_columns_without_touching_other_values(self):
        database = sqlite3.connect(':memory:')
        self.addCleanup(database.close)
        database.execute('CREATE TABLE asset (code TEXT PRIMARY KEY, brief TEXT, notes TEXT)')
        database.execute("INSERT INTO asset VALUES ('A1', 'discard', 'keep')")
        loaded = self.load()

        def remove(class_name, args, values):
            self.assertEqual(class_name, 'tactic.ui.panel.AlterSearchTypeCbk')
            self.assertEqual(args, {'alter_mode': 'Remove Column'})
            self.assertEqual(values['target_search_type'], 'demo/asset?project=demo')
            self.assertEqual(values['column_name'], 'brief')
            self.assertEqual(values['config_constraint'], '')
            database.execute('ALTER TABLE asset DROP COLUMN brief')
            del self.api.columns['demo/asset']['brief']

        with patch.object(self.api.local_api, 'execute_cmd', side_effect=remove) as command:
            saved = self.save(loaded, ['brief'])
        command.assert_called_once()
        self.assertNotIn('brief', saved['metadata']['columns'])
        self.assertIn('notes', saved['metadata']['columns'])
        self.assertEqual(saved['document']['removedColumns'], [])
        self.assertNotEqual(saved['revision'], loaded['revision'])
        self.assertEqual(database.execute('SELECT code, notes FROM asset').fetchall(), [('A1', 'keep')])

    def test_invalid_missing_duplicate_and_protected_columns_reject_whole_draft_before_writes(self):
        loaded = self.load()
        for removed in (['brief', 'id'], ['code'], ['s_status'], ['pipeline_code'], ['missing'],
                        ['brief', 'brief'], ['brief"; DROP TABLE asset'], 'brief', [None], [{}]):
            with self.subTest(removed=removed), patch.object(self.api.local_api, 'execute_cmd') as command:
                with self.assertRaises(ValueError):
                    self.save(loaded, removed)
                command.assert_not_called()
                self.assertEqual(self.api.calls, [])

    def test_schema_key_added_after_load_blocks_deletion_with_current_server_metadata(self):
        from pyasm.biz import Schema

        loaded = self.load()
        self.api.tables['sthpw/schema'][0]['schema'] = (
            '<schema><connect from="demo/asset" to="demo/asset" relationship="code" '
            'from_col="brief" to_col="code"/></schema>')
        with patch.object(Schema, 'get', wraps=Schema.get) as get_schema, \
                patch.object(self.api.local_api, 'execute_cmd') as command:
            with self.assertRaisesRegex(ValueError, 'brief'):
                self.save(loaded, ['brief'])
            get_schema.assert_any_call(reset_cache=True, project_code='demo')
        command.assert_not_called()
        self.assertEqual(self.api.calls, [])

    def test_revision_conflict_and_new_type_removal_do_not_write(self):
        loaded = self.load()
        self.api.columns['demo/asset']['another'] = {'data_type': 'integer'}
        with patch.object(self.api.local_api, 'execute_cmd') as command:
            with self.assertRaisesRegex(ValueError, 'changed'):
                self.save(loaded, ['brief'])
            with self.assertRaises(ValueError):
                search_types_request('save', 'demo', document={
                    'name': 'new_type', 'title': 'New', 'removedColumns': ['description']})
        command.assert_not_called()
        self.assertEqual(self.api.calls, [])

    def test_native_identity_and_inherited_implicit_schema_keys_are_protected(self):
        self.api.tables['sthpw/search_object'][0]['id_column'] = 'native_id'
        self.api.columns['demo/asset'].update({
            name: {'data_type': 'text'} for name in ('native_id', 'asset_code', 'description')})
        self.api.tables['sthpw/schema'][0]['schema'] = '<schema parent="base"/>'
        self.api.tables['sthpw/schema'].append(dict(code='base', schema=(
            '<schema><connect from="demo/asset" to="demo/asset" relationship="code"/></schema>')))
        loaded = self.load()
        blocks = loaded['metadata']['columnRemovalBlocks']
        self.assertEqual(blocks['native_id'], 'identity')
        self.assertEqual(blocks['asset_code'], 'schema')
        self.assertNotIn('description', blocks)
        with patch.object(self.api.local_api, 'execute_cmd') as command:
            for name in ('native_id', 'asset_code'):
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, name):
                    self.save(loaded, [name])
        command.assert_not_called()

    def test_system_and_config_columns_cannot_be_deleted(self):
        for namespace in ('sthpw', 'config'):
            identity = namespace + '/example'
            self.api.tables['sthpw/search_object'].append(dict(
                code=identity, title='Example', namespace=namespace, table_name='example', database='{project}'))
            self.api.columns[identity] = {'custom': {'data_type': 'text'}}
            self.api.tables[identity] = []
            loaded = json.loads(search_types_request('load', 'demo', identity))
            self.assertEqual(loaded['metadata']['columnRemovalBlocks'], {'custom': 'system_type'})
            with patch.object(self.api.local_api, 'execute_cmd') as command, self.assertRaisesRegex(
                    ValueError, 'protected'):
                search_types_request('save', 'demo', identity,
                                     dict(loaded['document'], removedColumns=['custom']), loaded['revision'])
            command.assert_not_called()

    def test_native_dependency_error_is_not_swallowed_or_followed_by_metadata_writes(self):
        loaded = self.load()
        with patch.object(self.api.local_api, 'execute_cmd', side_effect=RuntimeError(
                'Cannot drop brief: a database view depends on it')) as command:
            with self.assertRaisesRegex(RuntimeError, 'database view'):
                self.save(loaded, ['brief', 'notes'])
        command.assert_called_once()
        self.assertEqual(self.api.calls, [])
        self.assertIn('brief', self.api.columns['demo/asset'])


class ColumnRemovalQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ui_fixture.AdminSearchTypeEditorTests.setUpClass()

    def setUp(self):
        self.ui = ui_fixture.AdminSearchTypeEditorTests()
        self.ui.setUp()
        self.addCleanup(self.ui.doCleanups)
        self.editor = self.ui.editor
        self.window = self.ui.window
        self.editor._document['removedColumns'] = []
        self.editor._original = copy.deepcopy(self.editor.document)
        self.editor._metadata.update(
            columns={name: {'data_type': 'text'} for name in ('code', 'brief', 'notes')},
            columnRemovalBlocks={'code': 'identity'})
        self.editor.stateChanged.emit()
        self.ui.click('segmentedButtonSegment_entity_fields')

    def test_mark_restore_discard_and_protected_field_use_local_draft_only(self):
        with patch('thlib.tactic_classes.execute_procedure_serverside') as rpc:
            self.assertFalse(self.ui.item('adminDeleteColumn_code').isEnabled())
            self.ui.click('adminDeleteColumn_brief')
            self.assertEqual(self.editor.document['removedColumns'], ['brief'])
            self.assertTrue(self.editor.dirty)
            self.assertIn('удаление', self.ui.item('adminExistingField_brief').property('description'))
            undo = self.ui.reveal('adminDeleteColumn_brief')
            undo.forceActiveFocus()
            QTest.keyClick(self.window, Qt.Key_Space)
            frame(self.window)
            self.assertFalse(self.editor.dirty)
            self.ui.click('adminDeleteColumn_notes')
            self.ui.click('adminDiscardDocument')
            self.assertEqual(self.editor.document['removedColumns'], [])
            self.assertIn('notes', self.editor.metadata['columns'])
            rpc.assert_not_called()
        self.assertEqual(self.ui.ui.fixture.warnings, [])

    def test_cancel_then_confirm_sends_removal_and_keeps_preview_workflow(self):
        self.ui.click('adminDeleteColumn_brief')
        response = dict(identity=self.editor.identity, revision='saved', canWrite=True,
                        catalog=self.editor.catalog, document=dict(self.editor.document, removedColumns=[]),
                        metadata=copy.deepcopy(self.editor.metadata))
        del response['metadata']['columns']['brief']
        workers = []

        def task(operation):
            worker = self.ui.worker(operation)
            workers.append(worker)
            return worker

        with patch('thlib.tactic_classes.execute_procedure_serverside', return_value=response) as rpc, \
                patch.object(env_inst.server_pool, 'add_task', side_effect=task), \
                patch('thlib.server_cache.invalidate_domains'):
            self.ui.click('adminSaveDocument')
            message = self.ui.item('adminConfirmationText').property('text')
            self.assertIn('demo/asset', message)
            self.assertIn('brief', message)
            self.assertIn('данные', message)
            self.ui.click('adminCancelSave')
            rpc.assert_not_called()
            self.assertEqual(self.editor.document['removedColumns'], ['brief'])
            self.ui.click('adminSaveDocument')
            self.ui.click('adminConfirmSave')
            frame(self.window)
        rpc.assert_called_once()
        self.assertEqual(rpc.call_args.args[1]['document']['removedColumns'], ['brief'])
        self.assertNotIn('brief', self.editor.metadata['columns'])
        self.assertFalse(self.editor.dirty)
        self.ui.checkin.prepare_external_checkin.assert_not_called()
        self.assertEqual(self.ui.ui.fixture.warnings, [])

    def test_readonly_busy_and_protected_staging_do_not_mutate_draft(self):
        original = copy.deepcopy(self.editor.document)
        self.editor._can_write = False
        self.editor.stateChanged.emit()
        self.assertFalse(self.ui.item('adminDeleteColumn_brief').isEnabled())
        self.editor.set_column_removed('brief', True)
        self.assertEqual(self.editor.document, original)
        self.editor._can_write = True
        self.editor._worker = self.ui.worker(lambda: None)
        self.editor.stateChanged.emit()
        self.assertFalse(self.ui.item('adminDeleteColumn_brief').isEnabled())
        self.editor.set_column_removed('brief', True)
        self.assertEqual(self.editor.document, original)
        self.editor._worker = None
        self.editor.set_column_removed('code', True)
        self.assertTrue(self.editor.error)
        self.assertEqual(self.editor.document, original)
        self.editor.set_column_removed('gone', True)
        self.assertEqual(self.editor.document, original)

    def test_touch_deletion_and_save_error_preserve_draft(self):
        button = self.ui.reveal('adminDeleteColumn_notes')
        point = button.mapToScene(QPointF(button.width() / 2, button.height() / 2)).toPoint()
        device = QTest.createTouchDevice()
        QTest.touchEvent(self.window, device).press(0, point, self.window).commit()
        QTest.touchEvent(self.window, device).release(0, point, self.window).commit()
        frame(self.window)
        self.assertEqual(self.editor.document['removedColumns'], ['notes'])
        pending = []

        def task(operation):
            worker = self.ui.worker(operation)
            pending.append(worker)
            return worker

        with patch('thlib.tactic_classes.execute_procedure_serverside', side_effect=RuntimeError(
                'Cannot drop notes: a database view depends on it')), \
                patch.object(env_inst.server_pool, 'add_task', side_effect=task):
            self.ui.click('adminSaveDocument')
            self.ui.click('adminConfirmSave')
            frame(self.window)
        self.assertTrue(self.editor.dirty)
        self.assertFalse(self.editor.busy)
        self.assertIn('database view', self.editor.error)
        self.assertEqual(self.editor.document['removedColumns'], ['notes'])
        self.assertIn('notes', self.editor.metadata['columns'])
        self.assertTrue(self.ui.item('adminSaveDocument').isEnabled())
        self.assertEqual(self.ui.ui.fixture.warnings, [])

    def test_long_confirmation_scrolls_inside_dialog_and_keeps_actions_visible(self):
        names = ['extra_field_%02d' % index for index in range(50)]
        self.editor._metadata['columns'].update({name: {'data_type': 'text'} for name in names})
        for name in names:
            self.editor.set_column_removed(name, True)
        for width, height in ((900, 620), (1400, 940)):
            with self.subTest(width=width):
                self.window.resize(width, height)
                frame(self.window)
                self.ui.click('adminSaveDocument')
                viewport = self.ui.item('adminConfirmationScroll')
                self.assertEqual(viewport.property('contentY'), 0)
                label = self.ui.item('adminConfirmationText')
                bar = self.ui.item('adminConfirmationScrollBar')
                self.assertGreater(viewport.property('contentHeight'), viewport.height())
                self.assertTrue(bar.isVisible())
                self.assertLessEqual(label.width() + bar.property('reservedExtent'), viewport.width())
                for name in ('adminCancelSave', 'adminConfirmSave'):
                    button = self.ui.item(name)
                    self.assertGreaterEqual(button.mapToScene(QPointF()).y(), 0)
                    self.assertLessEqual(button.mapToScene(QPointF(button.width(), button.height())).y(), height)
                self.assertTrue(self.ui.item('adminCancelSave').hasActiveFocus())
                QTest.keyClick(self.window, Qt.Key_Tab)
                self.assertTrue(self.ui.item('adminConfirmSave').hasActiveFocus())
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
                output = os.environ.get('SEARCH_TYPE_SCREENSHOTS')
                if output:
                    Path(output).mkdir(parents=True, exist_ok=True)
                    self.window.grabWindow().save(str(Path(output) / ('delete_columns_%s.png' % width)))
                QTest.keyClick(self.window, Qt.Key_Escape)
                frame(self.window)
                self.assertEqual(self.editor.document['removedColumns'], names)
        self.assertEqual(self.ui.ui.fixture.warnings, [])

    def test_existing_field_actions_fit_narrow_and_wide_editor(self):
        self.ui.click('adminDeleteColumn_brief')
        viewport = self.ui.item('adminSearchTypeForm')
        for width, height in ((900, 620), (1400, 940)):
            with self.subTest(width=width):
                self.window.resize(width, height)
                frame(self.window)
                for name in ('code', 'brief', 'notes'):
                    button = self.ui.reveal('adminDeleteColumn_' + name)
                    row = self.ui.item('adminExistingField_' + name)
                    origin = button.mapToItem(row, QPointF())
                    self.assertGreaterEqual(origin.x(), 0)
                    self.assertGreaterEqual(origin.y(), 0)
                    self.assertLessEqual(origin.x() + button.width(), row.width())
                    self.assertLessEqual(origin.y() + button.height(), row.height())
                    self.assertLessEqual(button.mapToItem(viewport, QPointF(button.width(), 0)).x(),
                                         viewport.width() - 16)
                output = os.environ.get('SEARCH_TYPE_SCREENSHOTS')
                if output:
                    Path(output).mkdir(parents=True, exist_ok=True)
                    self.window.grabWindow().save(str(Path(output) / ('field_actions_%s.png' % width)))
        self.assertEqual(self.ui.ui.fixture.warnings, [])
