"""Real schema connection inspector input, draft preview and bounded layout."""

import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from PySide6.QtCore import QObject, QPointF, Qt, Signal
from PySide6.QtTest import QTest
from PySide6.QtGui import QGuiApplication

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

    def options(self, name):
        rows = self.ui.item(name).property('model')
        return rows.toVariant() if hasattr(rows, 'toVariant') else rows

    def test_real_column_choices_keyboard_touch_and_reversal(self):
        self.assertEqual(self.ui.item('adminSchema_from_col').property('text'), 'shot_code')
        self.assertEqual(self.ui.item('adminSchema_to_col').property('text'), 'code')
        with patch.object(self.editor, '_request') as save:
            self.ui.enter('adminSchema_from_col', 'shot_id')
            self.ui.choose('adminSchemaChoose_to_col', 'id')
            self.assertEqual(self.editor.selectedAttributes['from_col'], 'shot_id')
            self.assertEqual(self.editor.selectedAttributes['to_col'], 'id')
            self.ui.click('adminSchemaCreateColumns')
            self.assertTrue(self.editor.connectionEditor.createColumns)
            self.ui.click('adminSchemaReverse')
            self.assertEqual(self.editor.selectedAttributes['from'], 'demo/shot')
            self.assertEqual(self.editor.selectedAttributes['from_col'], 'id')
            self.assertTrue(self.editor.connectionEditor.createColumns)
            chooser = self.ui.reveal('adminSchemaChoose_from_col')
            point = chooser.mapToScene(QPointF(chooser.width() / 2, chooser.height() / 2)).toPoint()
            device = QTest.createTouchDevice()
            sequence = QTest.touchEvent(self.window, device, autoCommit=False)
            sequence.press(0, point, self.window).commit()
            QTest.qWait(20)
            sequence.release(0, point, self.window).commit()
            QTest.qWait(80)
            popup_window = next(window for window in QGuiApplication.allWindows() if window.isVisible()
                                and any(item.objectName() == 'comboBoxPopupList' and item.isVisible()
                                        for item in graph_fixture.sidebar_fixture.SidebarEditorQmlTests.descendants(window.contentItem())))
            popup_list = next(item for item in graph_fixture.sidebar_fixture.SidebarEditorQmlTests.descendants(popup_window.contentItem())
                              if item.objectName() == 'comboBoxPopupList' and item.isVisible())
            popup_window.requestActivate()
            popup_list.forceActiveFocus()
            QTest.keyClick(popup_window, Qt.Key_Up)
            frame(popup_window)
            QTest.keyClick(popup_window, Qt.Key_Return)
            frame(self.window)
            self.assertEqual(self.editor.selectedAttributes['from_col'], 'code')
            save.assert_not_called()
        self.assertEqual(self.ui.fixture.fixture.warnings, [])

    def test_many_to_many_preview_and_confirmation_do_not_create_before_save(self):
        with patch.object(self.editor, '_request') as request:
            self.ui.choose('adminSchemaRelationship', 'many_to_many')
            identity = self.editor.selectedNode
            self.assertEqual(identity, 'demo/asset_in_shot')
            self.assertTrue(self.ui.item('graphNode_' + identity).isVisible())
            self.assertEqual(len(self.editor.nodes), 3)
            viewport = self.ui.item('adminGraphPropertiesScroll')
            attributes = self.ui.reveal('graph_attributesEditor')
            self.assertLessEqual(attributes.mapToItem(viewport, QPointF(0, attributes.height())).y(), viewport.height())
            output = os.environ.get('SCHEMA_CONNECTION_SCREENSHOTS')
            if output:
                path = Path(output)
                path.mkdir(parents=True, exist_ok=True)
                self.window.grabWindow().save(str(path / 'instance.png'))
            self.ui.click('schemaInstanceLink_1')
            self.ui.choose('adminSchemaChoose_to_col', 'id')
            self.assertEqual(self.editor.selectedAttributes['to_col'], 'id')
            self.ui.enter('adminSchemaInstanceName', 'asset_shots')
            QTest.keyClick(self.window, Qt.Key_Tab)
            frame(self.window)
            self.ui.click('adminSaveDocument')
            self.assertIn('demo/asset_shots', self.ui.item('adminConfirmationDetails').property('text'))
            request.assert_not_called()
            self.ui.click('adminCancelSave')
            request.assert_not_called()
            self.ui.click('adminSchemaRestoreDirect')
            self.assertEqual(len(self.editor.nodes), 2)
            self.assertEqual(self.editor.edges[0]['custom'], 'edge')
            self.ui.choose('adminSchemaRelationship', 'many_to_many')
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
        self.ui.enter('adminSchema_from_col', 'new_shot_key')
        self.ui.click('adminSchemaCreateColumns')
        with patch.object(env_inst.server_pool, 'add_task', return_value=worker) as add_task:
            self.ui.click('adminSchemaRefreshColumns')
            self.assertTrue(self.editor.connectionEditor.loading)
            self.assertFalse(self.ui.item('adminSchemaRefreshColumns').isEnabled())
            worker.result.emit({
                'demo/asset': {'table': 'asset', 'database': 'demo', 'tableAvailable': True,
                               'columns': [{'name': 'code', 'type': 'varchar'}, {'name': 'shot_code', 'type': 'varchar'}]},
                'demo/shot': {'table': 'shot', 'database': 'demo', 'tableAvailable': True,
                              'columns': [{'name': 'code', 'type': 'varchar'}, {'name': 'id', 'type': 'integer'}]}})
            frame(self.window)
            add_task.assert_called_once()
        self.assertFalse(self.editor.connectionEditor.loading)
        self.assertEqual(self.ui.item('adminSchema_from_col').property('text'), 'new_shot_key')
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
            for name in ('adminSchemaRelationship', 'adminSchemaCreateColumns', 'adminSchema_from_col', 'adminSchema_to_col'):
                self.ui.reveal(name)
                self.ui.assert_inside(name)
            for side in ('from_col', 'to_col'):
                chooser = self.ui.reveal('adminSchemaChoose_' + side)
                options = chooser.property('model')
                options = options.toVariant() if hasattr(options, 'toVariant') else options
                self.assertGreater(len(options), 40)
                self.ui.choose('adminSchemaChoose_' + side, 'attribute_39')
                self.assertEqual(self.editor.selectedAttributes[side], 'attribute_39')
                self.assertLessEqual(chooser.width(), self.ui.item('adminGraphPropertiesScroll').width() - 16)
            self.ui.item('adminGraphPropertiesScroll').setProperty('contentY', 0)
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
            self.ui.click('adminSchemaRefreshColumns')
            frame(self.window)
            self.assertFalse(self.editor.connectionEditor.loading)
            self.assertEqual(self.editor.connectionEditor.error, '')
            self.assertIn('id', [row['value'] for row in self.options('adminSchemaChoose_to_col')])
            for width, height in ((900, 620), (1400, 940)):
                with self.subTest(width=width):
                    self.window.resize(width, height)
                    frame(self.window)
                    notice = self.ui.reveal('schemaAbsent_from_colDescription')
                    self.assertEqual(self.editor.connectionEditor.columnCatalog['demo/asset']['table'], 'asset')
                    self.assertIn('отсутствует', notice.property('text'))
                    self.assertGreater(notice.height(), 0)
                    self.ui.assert_inside('schemaAbsent_from_colDescription')
                    viewport = self.ui.item('adminGraphPropertiesScroll')
                    self.assertLessEqual(notice.mapToItem(viewport, QPointF(notice.width(), 0)).x(),
                                         self.ui.item('adminGraphPropertiesScrollBar').mapToItem(viewport, QPointF()).x())
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
            self.assertTrue(self.ui.item('schemaAbsent_from_colDescription').isVisible())
            requests.assert_called_once()
            api.fixture.tables['demo/asset'] = []
            self.ui.click('adminSchemaRefreshColumns')
            frame(self.window)
            self.assertIn('code', [row['value'] for row in self.options('adminSchemaChoose_from_col')])
            self.assertTrue(self.editor.connectionEditor.columnCatalog['demo/asset']['tableAvailable'])
            with self.assertRaises(StopIteration):
                self.ui.item('schemaAbsent_from_colDescription')
            self.assertEqual(requests.call_count, 2)
        self.assertEqual(self.ui.fixture.fixture.warnings, [])


if __name__ == '__main__':
    unittest.main()
