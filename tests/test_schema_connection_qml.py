"""Real schema connection inspector input, draft preview and bounded layout."""

import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from PySide6.QtCore import QObject, QPointF, Qt, Signal
from PySide6.QtTest import QTest

import tests.test_admin_graph_forms as graph_fixture
import tests.test_schema_connections as api_fixture
from tests.profile_ui_responsiveness import frame


class SchemaConnectionQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        graph_fixture.AdminGraphFormsTests.setUpClass()

    def setUp(self):
        self.ui = graph_fixture.AdminGraphFormsTests()
        self.ui.setUp()
        self.addCleanup(self.ui.doCleanups)
        self.window = self.ui.window
        self.editor = self.ui.admin.schemaEditor
        self.ui.click('adminSection_schema')
        self.ui.click('graphEdge_0')

    def test_real_column_choices_keyboard_touch_and_reversal(self):
        self.assertEqual(self.ui.item('schemaColumn_from').property('text'), 'shot_code')
        self.assertEqual(self.ui.item('schemaColumn_to').property('text'), 'code')
        with patch.object(self.editor, '_request') as save:
            self.ui.enter('schemaColumn_from', 'shot_id')
            parent_id = self.ui.reveal('schemaColumnChoice_to_id')
            parent_id.forceActiveFocus()
            QTest.keyClick(self.window, Qt.Key_Space)
            frame(self.window)
            self.assertEqual(self.editor.selectedAttributes['from_col'], 'shot_id')
            self.assertEqual(self.editor.selectedAttributes['to_col'], 'id')
            self.ui.click('schemaCreateColumns')
            self.assertTrue(self.editor.connectionEditor.createColumns)
            self.ui.click('schemaReverseConnection')
            self.assertEqual(self.editor.selectedAttributes['from'], 'demo/shot')
            self.assertEqual(self.editor.selectedAttributes['from_col'], 'id')
            self.assertTrue(self.editor.connectionEditor.createColumns)
            row = self.ui.reveal('schemaColumnChoice_from_code')
            point = row.mapToScene(QPointF(row.width() / 2, row.height() / 2)).toPoint()
            device = QTest.createTouchDevice()
            sequence = QTest.touchEvent(self.window, device, autoCommit=False)
            sequence.press(0, point, self.window).commit()
            frame(self.window)
            sequence.release(0, point, self.window).commit()
            frame(self.window)
            self.assertEqual(self.editor.selectedAttributes['from_col'], 'code')
            save.assert_not_called()
        self.assertEqual(self.ui.fixture.fixture.warnings, [])

    def test_many_to_many_preview_and_confirmation_do_not_create_before_save(self):
        with patch.object(self.editor, '_request') as request:
            self.ui.click('segmentedButtonSegment_many_to_many')
            identity = self.editor.selectedNode
            self.assertEqual(identity, 'demo/asset_in_shot')
            self.assertTrue(self.ui.item('graphNode_' + identity).isVisible())
            self.assertEqual(len(self.editor.nodes), 3)
            viewport = self.ui.item('adminGraphPropertiesViewport')
            attributes = self.ui.item('adminSelectionAttributesEditor')
            self.assertLess(attributes.mapToItem(viewport, QPointF()).y(), viewport.height() - 50,
                            'Empty endpoint lists must not leave blank space above the instance JSON')
            output = os.environ.get('SCHEMA_CONNECTION_SCREENSHOTS')
            if output:
                path = Path(output)
                path.mkdir(parents=True, exist_ok=True)
                self.window.grabWindow().save(str(path / 'instance.png'))
            self.ui.click('schemaInstanceLink_demo/shot')
            self.ui.click('schemaColumnChoice_to_id')
            self.assertEqual(self.editor.selectedAttributes['to_col'], 'id')
            self.ui.enter('schemaInstanceTableName', 'asset_shots')
            self.ui.click('adminSaveDocument')
            self.assertIn('demo/asset_shots', self.ui.item('adminConfirmationText').property('text'))
            request.assert_not_called()
            self.ui.click('adminCancelSave')
            request.assert_not_called()
            self.ui.click('schemaRestoreDirect')
            self.assertEqual(len(self.editor.nodes), 2)
            self.assertEqual(self.editor.edges[0]['custom'], 'edge')
            self.ui.click('segmentedButtonSegment_many_to_many')
            self.ui.click('adminSaveDocument')
            self.ui.click('adminConfirmSave')
            request.assert_called_once_with('save', 'demo')
        self.assertEqual(self.ui.fixture.fixture.warnings, [])

    def test_visible_refresh_loads_once_and_keeps_unsaved_column_edits(self):
        from thlib.environment import env_inst

        class Worker(QObject):
            result = Signal(object)
            error = Signal(object)

            def start(self):
                pass

            def cancel(self):
                pass

        worker = Worker()
        self.ui.enter('schemaColumn_from', 'new_shot_key')
        self.ui.click('schemaCreateColumns')
        with patch.object(env_inst.server_pool, 'add_task', return_value=worker) as add_task:
            self.ui.click('schemaRefreshColumns')
            self.assertTrue(self.editor.connectionEditor.loading)
            self.assertFalse(self.ui.item('schemaRefreshColumns').isEnabled())
            worker.result.emit({
                'demo/asset': {'table': 'asset', 'database': 'demo', 'tableAvailable': True,
                               'columns': [{'name': 'code', 'type': 'varchar'}, {'name': 'shot_code', 'type': 'varchar'}]},
                'demo/shot': {'table': 'shot', 'database': 'demo', 'tableAvailable': True,
                              'columns': [{'name': 'code', 'type': 'varchar'}, {'name': 'id', 'type': 'integer'}]}})
            frame(self.window)
            add_task.assert_called_once()
        self.assertFalse(self.editor.connectionEditor.loading)
        self.assertEqual(self.ui.item('schemaColumn_from').property('text'), 'new_shot_key')
        self.assertTrue(self.editor.connectionEditor.createColumns)
        self.assertEqual(self.ui.fixture.fixture.warnings, [])

    def test_localized_inspector_fits_and_all_long_lists_have_scrollbar_gutters(self):
        catalog = self.editor.connectionEditor._column_catalog
        for name in catalog:
            catalog[name]['columns'] += [{'name': 'attribute_%02d' % index, 'type': 'varchar'} for index in range(40)]
        self.editor.connectionEditor.changed.emit()
        for width, height in ((900, 620), (1400, 940)):
            self.window.resize(width, height)
            frame(self.window)
            for name in ('schemaRelationshipType', 'schemaCreateColumns', 'schemaColumn_from', 'schemaColumn_to'):
                self.ui.reveal(name)
                self.ui.assert_inside(name)
            for side in ('from', 'to'):
                viewport = self.ui.reveal('schemaColumnList_' + side)
                self.assertLessEqual(viewport.height(), 180)
                self.assertGreater(viewport.property('contentHeight'), viewport.height())
                row = self.ui.item('schemaColumnChoice_' + side + '_code')
                self.assertLessEqual(row.width(), viewport.width() - 16)
                bar = next(item for item in graph_fixture.sidebar_fixture.SidebarEditorQmlTests.descendants(viewport)
                           if item.inherits('QQuickScrollBar'))
                self.assertTrue(bar.isVisible())
            self.ui.item('adminGraphPropertiesViewport').setProperty('contentY', 0)
            frame(self.window)
            output = os.environ.get('SCHEMA_CONNECTION_SCREENSHOTS')
            if output:
                path = Path(output)
                path.mkdir(parents=True, exist_ok=True)
                self.window.grabWindow().save(str(path / ('connection_%s.png' % width)))
            self.assertEqual(self.ui.fixture.fixture.warnings, [])

    def test_missing_table_is_explained_without_losing_other_endpoint_and_refresh_recovers(self):
        from thlib.environment import env_inst

        api = api_fixture.SchemaConnectionApiTests()
        api.setUp()
        self.addCleanup(api.doCleanups)
        api.fixture.tables.pop('demo/asset')
        original = self.editor.document['xml']

        class Worker(QObject):
            result = Signal(object)
            error = Signal(object)

            def __init__(self, operation):
                super().__init__()
                self.operation = operation

            def start(self):
                self.result.emit(self.operation())

            def cancel(self):
                pass

        with patch.object(env_inst.server_pool, 'add_task', side_effect=Worker) as requests, \
                patch('thlib.tactic_classes.execute_procedure_serverside', side_effect=lambda endpoint, args, **_:
                      json.loads(endpoint(**args))):
            self.ui.click('schemaRefreshColumns')
            frame(self.window)
            self.assertFalse(self.editor.connectionEditor.loading)
            self.assertEqual(self.editor.connectionEditor.error, '')
            self.assertTrue(self.ui.item('schemaColumnChoice_to_id').isVisible())
            for width, height in ((900, 620), (1400, 940)):
                with self.subTest(width=width):
                    self.window.resize(width, height)
                    frame(self.window)
                    notice = self.ui.reveal('schemaMissingTable_from')
                    self.assertIn('demo.asset', notice.property('text'))
                    self.assertIn('отсутствует', notice.property('text'))
                    self.assertGreater(notice.height(), 0)
                    self.ui.assert_inside('schemaMissingTable_from')
                    viewport = self.ui.item('adminGraphPropertiesViewport')
                    self.assertLessEqual(notice.mapToItem(viewport, QPointF(notice.width(), 0)).x(),
                                         viewport.width() - 16)
                    output = os.environ.get('SCHEMA_CONNECTION_SCREENSHOTS')
                    if output:
                        path = Path(output)
                        path.mkdir(parents=True, exist_ok=True)
                        self.window.grabWindow().save(str(path / ('missing_table_%s.png' % width)))
            self.assertEqual(self.editor.document['xml'], original)
            self.assertFalse(self.editor.dirty)
            self.assertEqual(api.fixture.calls, [])
            self.ui.click('graphNode_demo/shot')
            self.ui.click('graphEdge_0')
            self.assertTrue(self.ui.item('schemaMissingTable_from').isVisible())
            requests.assert_called_once()
            api.fixture.tables['demo/asset'] = []
            self.ui.click('schemaRefreshColumns')
            frame(self.window)
            self.assertTrue(self.ui.item('schemaColumnChoice_from_code').isVisible())
            self.assertTrue(self.editor.connectionEditor.columnCatalog['demo/asset']['tableAvailable'])
            with self.assertRaises(StopIteration):
                self.ui.item('schemaMissingTable_from')
            self.assertEqual(requests.call_count, 2)
        self.assertEqual(self.ui.fixture.fixture.warnings, [])


if __name__ == '__main__':
    unittest.main()
