"""Raw table controller and actual Administration QML input."""
import copy
import json
import unittest
from unittest.mock import patch

from PySide6.QtCore import QPointF, Qt
from PySide6.QtTest import QTest
from PySide6.QtQml import QQmlProperty

import tests.test_administration_qml as admin_fixture
from tests.profile_ui_responsiveness import frame


class RawDatabaseQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        admin_fixture.AdministrationQmlTests.setUpClass()

    def setUp(self):
        self.fixture = admin_fixture.AdministrationQmlTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.editor = self.fixture.admin.rawEditor
        self.editor._identity = json.dumps(['sthpw', 'raw_browser'])
        self.editor._catalog = [dict(identity=self.editor.identity, label='sthpw / raw_browser')]
        self.editor._metadata = dict(columns=[dict(name='id', type='INTEGER', readonly=False),
                                              dict(name='value', type='TEXT', readonly=False),
                                              dict(name='number', type='INTEGER', readonly=False),
                                              dict(name='password', type='TEXT', readonly=True)],
                                     total=1, offset=0, label='sthpw / raw_browser')
        self.editor._document = dict(offset=0, rows=[dict(key=[1], revision='row-revision',
                                                        values=dict(id=1, value='old', number=7, password='[redacted]'))])
        self.editor._document_loaded()
        self.editor.stateChanged.emit()
        self.fixture.click('adminSection_raw')
        frame(self.fixture.window)

    def cell_window(self):
        window = self.fixture.fixture.window('raw_cell')
        frame(window)
        return window

    def cell_item(self, name):
        window = self.cell_window()
        return next(item for item in admin_fixture.windows_fixture.SidebarEditorQmlTests.descendants(window.contentItem())
                    if item.objectName() == name and item.isVisible())

    def edit_cell(self, index, name, value):
        self.fixture.click('rawCell_' + str(index) + '_' + name)
        window = self.cell_window()
        field = self.cell_item('rawCellValue')
        self.fixture.fixture.click(window, field)
        QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
        for character in value:
            QTest.keyClick(window, Qt.Key_Return if character == '\n' else character)
        button = self.cell_item('rawCellApply')
        from PySide6.QtCore import QPointF
        point = button.mapToScene(QPointF(button.width() / 2, button.height() / 2)).toPoint()
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point)
        frame(self.fixture.window)

    def test_loaded_table_opens_and_survives_responsive_scene_replacement(self):
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlComponent
        from pathlib import Path
        host = self.fixture.fixture
        theme = self.fixture.item('rawDatabasePage').property('theme')
        component = QQmlComponent(host.engine)
        component.setData(b"""import QtQuick
import "." as TH
Window {
    id: root
    required property var theme
    width: 1100; height: 740; visible: true
    TH.AdminRawDatabaseView {anchors.fill: parent; theme: root.theme; controller: administrationController.rawEditor}
}""", QUrl.fromLocalFile(str(Path(__file__).resolve().parents[1] / 'thlib/ui/qml/RawViewportTest.qml')))
        self.assertTrue(component.isReady(), [error.toString() for error in component.errors()])
        window = component.createWithInitialProperties({'theme': theme})
        self.assertIsNotNone(window)
        try:
            frame(window)
            window.resize(360, 320)
            window.resize(1100, 740)
            frame(window)
            fields = [item for item in admin_fixture.windows_fixture.SidebarEditorQmlTests.descendants(window.contentItem())
                      if item.objectName() == 'rawCell_0_id' and item.isVisible()]
            self.assertEqual(len(fields), 1, [(item.objectName(), item.width(), item.height(), item.isVisible()) for item in admin_fixture.windows_fixture.SidebarEditorQmlTests.descendants(window.contentItem()) if item.objectName()])
            self.assertEqual(fields[0].property('text'), '1')
            self.assertEqual(host.warnings, [])
        finally:
            window.close()
            window.deleteLater()
            frame(self.fixture.window)

    def test_first_async_page_reserves_header_above_rows(self):
        from PySide6.QtCore import QPointF
        identity = self.editor.identity
        catalog = copy.deepcopy(self.editor.catalog)
        metadata = copy.deepcopy(self.editor.metadata)
        document = copy.deepcopy(self.editor._document)
        document['rows'] = [dict(key=[index + 1], revision=str(index),
            values=dict(id=index + 1, value=str(index), number=7, password='[redacted]')) for index in range(50)]
        metadata['total'] = 50
        self.fixture.window.resize(1400, 940)
        loader = self.fixture.item('rawDatabasePage').parentItem()
        loader.setProperty('active', False)
        self.editor.reset('demo')
        loader.setProperty('active', True)
        frame(self.fixture.window)
        self.editor._identity = identity
        self.editor._catalog = catalog
        self.editor._can_write = True
        self.editor._metadata = metadata
        self.editor._document = document
        self.editor._document_loaded()
        self.editor.stateChanged.emit()
        frame(self.fixture.window)
        viewport = self.fixture.item('rawTableViewport')
        heading = self.fixture.item('rawTableHeadings')
        cell = self.fixture.item('rawCell_0_value')
        top = cell.mapToItem(viewport, QPointF()).y()
        bottom = heading.mapToItem(viewport, QPointF()).y() + heading.height()
        self.assertGreaterEqual(top, bottom - 1)
        import os
        output = os.environ.get('RAW_HEADER_SCREENSHOT')
        if output:
            self.fixture.window.grabWindow().save(output)
        theme = self.fixture.item('rawDatabasePage').property('theme')
        # Compare rendered pixels: fixed headings must hide text, hover and delete icons below.
        for width, height in ((1400, 940), (900, 620)):
            self.fixture.window.resize(width, height)
            for dark in (True, False):
                theme.setProperty('dark', dark)
                for horizontal in (0, 120):
                    viewport.setProperty('contentX', horizontal)
                    viewport.setProperty('contentY', viewport.property('originY'))
                    frame(self.fixture.window)
                    def header_image():
                        point = viewport.mapToScene(QPointF(2, 2))
                        image = self.fixture.window.grabWindow()
                        scale = image.devicePixelRatio()
                        return image.copy(round(point.x() * scale), round(point.y() * scale),
                                          round((viewport.width() - 22) * scale), round(36 * scale))
                    baseline = header_image()
                    for vertical in (100, 493):
                        viewport.setProperty('contentY', vertical)
                        frame(self.fixture.window)
                        self.assertAlmostEqual(heading.mapToItem(viewport, QPointF()).y(), 0, delta=1)
                        self.assertEqual(header_image(), baseline,
                                         (width, dark, horizontal, vertical))
        viewport.setProperty('contentY', viewport.property('originY'))
        frame(self.fixture.window)
        cell = self.fixture.item('rawCell_0_value')
        self.assertGreaterEqual(cell.mapToItem(viewport, QPointF()).y(), heading.height() - 1)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_edit_delete_discard_and_narrow_wide_layout(self):
        fixture = self.fixture
        for width, height in ((900, 620), (1400, 940)):
            fixture.window.resize(width, height)
            frame(fixture.window)
            viewport = fixture.item('rawTableViewport')
            self.assertGreater(viewport.width(), 200)
            self.assertGreater(viewport.height(), 80)
            self.assertEqual(fixture.fixture.warnings, [])
        cell = fixture.item('rawCell_0_value')
        background = cell.property('background')
        self.assertEqual(background.property('radius'), 0)
        self.assertEqual(background.property('color').alpha(), 0)
        self.assertEqual(QQmlProperty.read(background, 'border.width'), 0)
        self.assertEqual(cell.width(), 229)
        self.assertTrue(cell.property('readOnly'))
        self.edit_cell(0, 'value', 'new')
        background = self.fixture.item('rawCell_0_value').property('background')
        self.assertEqual(background.property('radius'), 0)
        self.assertEqual(self.editor.rows[0]['texts']['value'], 'new')
        self.assertTrue(self.editor.dirty)
        self.assertTrue(fixture.admin.projectLocked)
        fixture.click('adminSection_schema'); fixture.click('adminSection_raw')
        self.assertEqual(fixture.item('rawCell_0_value').property('text'), 'new')
        self.editor.toggle_delete(0)
        self.assertTrue(self.editor.rows[0]['deleted'])
        self.editor.discard(); frame(fixture.window)
        self.assertFalse(self.editor.dirty)
        self.assertFalse(self.editor.rows[0]['deleted'])
        self.assertEqual(fixture.item('rawCell_0_value').property('text'), 'old')

    def test_square_cells_in_new_deleted_and_disabled_rows(self):
        def check_cells():
            frame(self.fixture.window)
            for item in admin_fixture.windows_fixture.SidebarEditorQmlTests.descendants(self.fixture.window.contentItem()):
                if item.objectName().startswith('rawCell_') and item.isVisible():
                    self.assertTrue(item.property('tableCell'))
                    self.assertEqual(item.property('background').property('radius'), 0)
        check_cells()
        self.editor.new_document()
        check_cells()
        self.editor.toggle_delete(0)
        check_cells()
        self.editor._can_write = False
        self.editor.stateChanged.emit()
        check_cells()

    def test_toolbar_filter_grid_and_page_range_match_stream(self):
        fixture = self.fixture
        self.assertEqual(fixture.item('rawPageRange').property('text'), '1–1 / 1')
        for width, height in [(1400, 940), (900, 620)]:
            fixture.window.resize(width, height)
            frame(fixture.window)
            cell = fixture.item('rawCell_0_value')
            self.assertEqual(cell.width(), 229)
            self.assertEqual(cell.height(), 36)
            actions = fixture.item('rawRowActions')
            selector = fixture.item('rawTableSelector')
            if width == 1400:
                self.assertAlmostEqual(actions.mapToScene(QPointF()).y(), selector.mapToScene(QPointF()).y(), delta=1)
            else:
                self.assertGreater(actions.mapToScene(QPointF()).y(), selector.mapToScene(QPointF()).y())
            self.assertEqual(fixture.fixture.warnings, [])
        fixture.click('rawTableFilter')
        for character in 'not-a-table':
            QTest.keyClick(fixture.window, character)
        frame(fixture.window)
        # A filter keeps the selected table's real label in both clients.
        self.assertEqual(fixture.item('rawTableSelector').property('count'), 1)
        self.assertEqual(fixture.item('rawTableSelector').property('currentIndex'), 0)
        self.assertEqual(fixture.item('rawTableSelector').property('currentText'), 'sthpw / raw_browser')

    def test_cell_geometry_matches_stream_in_all_themes(self):
        theme = self.fixture.item('rawDatabasePage').property('theme')
        for style, height in [('md3', 36), ('material5', 38), ('fluent', 34)]:
            theme.setProperty('styleName', style)
            frame(self.fixture.window)
            cell = self.fixture.item('rawCell_0_value')
            self.assertEqual(cell.height(), height)
            tile = cell.parentItem()
            while tile.property('row') is None or tile.property('column') is None:
                tile = tile.parentItem()
            self.assertEqual(tile.height(), height + 1)
            self.assertEqual(tile.width(), 230)
            self.assertEqual(self.fixture.item('rawTableHeadings').height(), 40)
            self.assertEqual(self.fixture.item('rawCell_0_password').property('readOnly'), True)
            self.assertEqual(self.fixture.fixture.warnings, [])

    def test_inline_discard_drop_and_confirmed_save_match_stream(self):
        fixture = self.fixture
        fixture.click('rawNewRow')
        self.assertEqual(len(self.editor.rows), 2)
        with patch.object(self.editor, '_request') as request:
            fixture.click('adminSaveDocument')
            request.assert_not_called()
            fixture.click('adminConfirmSave')
            self.assertEqual(request.call_args.args[:2], ('save', self.editor.identity))
        self.editor._write_pending = False
        fixture.click('adminDiscardDocument')
        frame(fixture.window)
        self.assertTrue(self.editor.dirty)
        self.assertTrue(fixture.item('adminDocumentConfirmation').isVisible())
        fixture.click('adminConfirmSave')
        frame(fixture.window)
        self.assertFalse(self.editor.dirty)
        self.assertEqual(len(self.editor.rows), 1)
        fixture.click('rawDropTable')
        frame(fixture.window)
        self.assertFalse(fixture.item('rawConfirmChanges').isEnabled())
        fixture.click('rawDropName')
        for character in 'sthpw / raw_browser':
            QTest.keyClick(fixture.window, character)
        frame(fixture.window)
        self.assertTrue(fixture.item('rawConfirmChanges').isEnabled())
        with patch.object(self.editor, '_request') as request:
            fixture.click('rawConfirmChanges')
            self.assertEqual(request.call_args.args[:2], ('drop', self.editor.identity))
            self.assertEqual(request.call_args.kwargs['confirmation'], 'sthpw / raw_browser')

    def test_read_only_cells_remain_selectable_and_json_is_compact(self):
        self.editor._metadata['columns'][1]['readonly'] = True
        self.editor.rows[0]['values']['value'] = {'label': 'kept', 'flag': True}
        self.editor._document_loaded(); self.editor.stateChanged.emit()
        frame(self.fixture.window)
        cell = self.fixture.item('rawCell_0_value')
        self.assertTrue(cell.isEnabled())
        self.assertTrue(cell.property('readOnly'))
        self.assertEqual(cell.property('text'), '{"label":"kept","flag":true}')

    def test_cell_context_menus_are_lazy_reused_and_keep_selection(self):
        from PySide6.QtCore import QPointF, QMetaObject, Q_ARG
        field = self.fixture.item('rawCell_0_value')
        other = self.fixture.item('rawCell_0_number')
        self.assertIsNone(field.property('contextMenu'))
        self.assertIsNone(other.property('contextMenu'))
        field.forceActiveFocus()
        QTest.keyClick(self.fixture.window, Qt.Key_A, Qt.ControlModifier)
        selection = field.property('selectedText')
        point = field.mapToScene(QPointF(8, field.height() / 2)).toPoint()
        QTest.mouseClick(self.fixture.window, Qt.RightButton, Qt.NoModifier, point)
        QTest.qWait(100)
        menu = field.property('contextMenu')
        self.assertIsNotNone(menu)
        self.assertTrue(menu.property('visible'))
        self.assertEqual(field.property('selectedText'), selection)
        self.assertIsNone(other.property('contextMenu'))
        self.assertTrue(menu.property('readOnly'))
        QMetaObject.invokeMethod(menu, 'close')
        QTest.qWait(100)
        QTest.mouseClick(self.fixture.window, Qt.RightButton, Qt.NoModifier, point)
        QTest.qWait(100)
        self.assertEqual(field.property('contextMenu'), menu)
        QMetaObject.invokeMethod(menu, 'trigger', Q_ARG(str, 'select_all'))
        QTest.qWait(150)
        self.assertEqual(field.property('selectedText'), field.property('text'))
        viewport = self.fixture.item('rawTableViewport')
        viewport.setProperty('contentX', max(0, viewport.property('contentWidth') - viewport.width()))
        frame(self.fixture.window)
        readonly = self.fixture.item('rawCell_0_password')
        point = readonly.mapToScene(QPointF(8, readonly.height() / 2)).toPoint()
        QTest.mouseClick(self.fixture.window, Qt.RightButton, Qt.NoModifier, point)
        QTest.qWait(100)
        readonly_menu = readonly.property('contextMenu')
        self.assertIsNotNone(readonly_menu)
        self.assertTrue(readonly_menu.property('readOnly'))
        QMetaObject.invokeMethod(readonly_menu, 'close')
        QTest.qWait(100)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_invalid_typed_numbers_never_reach_server(self):
        for value in ['NaN', 'Infinity', '1e400', '{"value":1e400}']:
            self.editor.set_cell(0, 'number', value)
            with patch.object(self.editor, '_request') as request:
                self.editor.save()
                request.assert_not_called()
            self.assertTrue(self.editor.canWrite)
            self.assertTrue(self.editor.error)
        self.editor.discard()
        self.assertEqual(self.editor.error, '')

    def test_full_pages_create_only_visible_rows_and_keep_offscreen_drafts(self):
        from PySide6.QtCore import QPointF
        descendants = admin_fixture.windows_fixture.SidebarEditorQmlTests.descendants
        self.editor._document = dict(offset=0, rows=[dict(key=[index], revision=str(index),
            values=dict(id=index, value=str(index), number=7, password='[redacted]')) for index in range(50)])
        self.editor._metadata.update(total=100, offset=0)
        self.editor._document_loaded()
        self.editor.stateChanged.emit()
        frame(self.fixture.window)
        viewport = self.fixture.item('rawTableViewport')
        def cells():
            return [item for item in descendants(self.fixture.window.contentItem())
                    if item.objectName().startswith('rawCell_')]
        self.assertLess(len(cells()), 4 * 50)
        viewport.setProperty('contentY', viewport.property('contentHeight') - viewport.height())
        frame(self.fixture.window)
        self.edit_cell(49, 'value', 'last row')
        self.assertEqual(self.editor.rows[49]['texts']['value'], 'last row')
        viewport.setProperty('contentY', viewport.property('originY'))
        frame(self.fixture.window)
        self.assertLess(len(cells()), 4 * 50)
        viewport.setProperty('contentY', viewport.property('contentHeight') - viewport.height())
        frame(self.fixture.window)
        self.assertEqual(self.fixture.item('rawCell_49_value').property('text'), 'last row')
        heading = self.fixture.item('rawTableHeadings')
        self.assertAlmostEqual(heading.mapToItem(viewport, QPointF(0, 0)).y(), 0, delta=1)
        self.editor.discard()
        with patch.object(self.editor, '_request') as request:
            self.fixture.click('rawNextPage')
            request.assert_called_once_with('load', self.editor.identity, item_offset=50)
        self.editor._metadata['offset'] = 50
        self.editor._document = dict(offset=50, rows=[dict(key=[index], revision=str(index),
            values=dict(id=index, value=str(index), number=7, password='[redacted]')) for index in range(50, 100)])
        self.editor._document_loaded()
        self.editor.stateChanged.emit()
        frame(self.fixture.window)
        self.assertEqual(self.fixture.item('rawPageRange').property('text'), '51–100 / 100')
        self.assertLess(len(cells()), 4 * 50)
        with patch.object(self.editor, '_request') as request:
            self.fixture.click('rawPreviousPage')
            request.assert_called_once_with('load', self.editor.identity, item_offset=0)

    def test_save_sends_only_changed_rows_and_cells(self):
        self.editor._document['rows'].append(dict(key=[2], revision='second-revision',
                                                  values=dict(id=2, value='background', number=8,
                                                              password='[redacted]')))
        self.editor._document_loaded()
        self.editor.stateChanged.emit()
        frame(self.fixture.window)
        self.edit_cell(0, 'value', 'edited')
        with patch.object(self.editor, '_request') as request:
            self.fixture.click('adminSaveDocument')
            self.fixture.click('adminConfirmSave')
        draft = request.call_args.kwargs['document']
        self.assertEqual(draft, dict(offset=0, rows=[dict(key=[1], revision='row-revision',
                                                       deleted=False, values={'value': 'edited'})]))
        self.editor._write_pending = False
        self.editor.discard()
        self.editor.toggle_delete(1)
        self.editor.new_document()
        self.editor.set_cell(2, 'value', 'new')
        with patch.object(self.editor, '_request') as request:
            self.editor.save()
        rows = request.call_args.kwargs['document']['rows']
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['key'], [2])
        self.assertEqual(rows[0]['revision'], 'second-revision')
        self.assertTrue(rows[0]['deleted'])
        self.assertIsNone(rows[1]['key'])
        self.assertEqual(rows[1]['values'], {'value': 'new'})
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_native_cell_editor_cancel_null_empty_literal_and_validation(self):
        self.assertEqual(self.fixture.item('rawCell_0_value').property('text'), 'old')
        self.fixture.click('rawCell_0_value')
        window = self.cell_window()
        self.assertEqual(window.property('kind'), 'raw_cell')
        self.assertEqual(window.transientParent(), self.fixture.window)
        self.assertEqual(window.modality(), Qt.WindowModal)
        self.assertEqual(self.cell_item('rawCellValue').property('text'), 'old')
        self.cell_item('rawCellValue').setProperty('text', 'cancelled')
        QTest.keyClick(window, Qt.Key_Escape)
        frame(self.fixture.window)
        self.assertFalse(self.editor.dirty)
        self.edit_cell(0, 'value', 'line one\nline two')
        self.assertEqual(self.editor.rows[0]['texts']['value'], 'line one\nline two')
        self.editor.open_cell(0, 'value')
        self.assertTrue(self.editor.apply_cell('null', ''))
        self.assertEqual(self.editor.cell_text(0, 'value'), 'NULL')
        self.editor.open_cell(0, 'value')
        self.assertTrue(self.editor.apply_cell('value', ''))
        with patch.object(self.editor, '_request') as request:
            self.editor.save()
        self.assertEqual(request.call_args.kwargs['document']['rows'][0]['values'], {'value': ''})
        self.editor._write_pending = False
        self.editor.open_cell(0, 'value')
        self.assertTrue(self.editor.apply_cell('value', 'NULL'))
        with patch.object(self.editor, '_request') as request:
            self.editor.save()
        self.assertEqual(request.call_args.kwargs['document']['rows'][0]['values'], {'value': 'NULL'})
        self.editor._write_pending = False
        self.editor.open_cell(0, 'number')
        self.assertFalse(self.editor.apply_cell('value', 'not a number'))
        self.assertTrue(self.editor.cell['error'])
        self.assertTrue(window.isVisible())
        self.assertTrue(self.editor.apply_cell('value', '9223372036854775807'))
        with patch.object(self.editor, '_request') as request:
            self.editor.save()
        self.assertEqual(request.call_args.kwargs['document']['rows'][0]['values']['number'], '9223372036854775807')
        self.editor._write_pending = False
        self.editor.open_cell(0, 'password')
        self.assertTrue(self.editor.cell['readonly'])
        self.assertFalse(self.editor.apply_cell('value', 'private overwrite'))
        self.editor.cancel_cell()
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_cell_editor_localized_layout_keyboard_and_default_mode(self):
        import os
        from pathlib import Path
        host = self.fixture.fixture
        report = Path(os.environ['RAW_CELL_REPORT_DIR']) if os.environ.get('RAW_CELL_REPORT_DIR') else None
        if report:
            report.mkdir(parents=True, exist_ok=True)
        measurements = []
        theme = self.fixture.item('rawDatabasePage').property('theme')
        for language in ('en', 'ru'):
            if language == 'en':
                host.app.removeTranslator(host.translator)
            else:
                host.app.installTranslator(host.translator)
            host.engine.retranslate()
            for width in (640, 480):
                for dark in (True, False):
                    theme.setProperty('dark', dark)
                    self.fixture.window.requestActivate()
                    frame(self.fixture.window)
                    cell = self.fixture.item('rawCell_0_value')
                    cell.forceActiveFocus()
                    QTest.keyClick(self.fixture.window, Qt.Key_F2)
                    window = self.cell_window()
                    window.resize(width, 440)
                    frame(window)
                    field = self.cell_item('rawCellValue')
                    combo = self.cell_item('rawCellMode')
                    self.assertGreaterEqual(field.height(), 100)
                    self.assertEqual(combo.width(), width - 28)
                    self.assertEqual(field.width(), width - 28)
                    self.assertEqual(window.title(), 'Cell editor' if language == 'en' else 'Редактор ячейки')
                    self.assertFalse(any(
                        item.objectName() == 'rawCellTitle'
                        for item in admin_fixture.windows_fixture.SidebarEditorQmlTests.descendants(window.contentItem())
                    ))
                    for name in ('rawCellApply', 'rawCellCancel'):
                        action = self.cell_item(name)
                        bottom = action.mapToScene(QPointF(0, action.height())).y()
                        self.assertLessEqual(bottom, window.height() - 8)

                    measurements.append(dict(language=language, width=width, dark=dark,
                                             fieldWidth=field.width(), fieldHeight=field.height(),
                                             comboWidth=combo.width(), comboHeight=combo.height()))
                    if report:
                        window.grabWindow().save(str(report / ('handler-%s-%s-%s.png' % (language, width, 'dark' if dark else 'light'))))
                    QTest.keyClick(window, Qt.Key_Escape)
                    frame(self.fixture.window)
                    self.assertFalse(self.editor.dirty)
        self.editor.new_document()
        self.editor.open_cell(1, 'value')
        window = self.cell_window()
        combo = self.cell_item('rawCellMode')
        self.assertEqual(combo.property('currentValue'), 'default')
        host.choose_combo_option(window, combo, 0)
        field = self.cell_item('rawCellValue')
        field.setProperty('text', '')
        field.forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Return, Qt.ControlModifier)
        frame(self.fixture.window)
        with patch.object(self.editor, '_request') as request:
            self.editor.save()
        self.assertEqual(request.call_args.kwargs['document']['rows'][0]['values'], {'value': ''})
        if report:
            (report / 'handler-measurements.json').write_text(json.dumps(measurements, indent=2), encoding='utf-8')
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_json_defaults_save_and_unknown_write_guard(self):
        self.editor.new_document()
        self.editor.open_cell(1, 'value')
        self.assertTrue(self.editor.apply_cell('null', ''))
        with patch.object(self.editor, '_request') as request:
            self.editor.save()
            draft = request.call_args.kwargs['document']
            self.assertEqual(draft['rows'][0]['values'], {'value': None})
            self.assertIsNone(draft['rows'][0]['key'])
        self.editor.fail('transport failure')
        self.assertTrue(self.editor.dirty)
        self.assertFalse(self.editor.canWrite)
        with patch.object(self.editor, '_request') as request:
            self.editor.discard()
            request.assert_called_once_with('list')


if __name__ == '__main__':
    unittest.main()
