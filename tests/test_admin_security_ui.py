"""Exercise the real object-by-group matrix, not source-string snapshots."""

import json
import os
import time
from pathlib import Path
import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QSignalSpy, QTest

import tests.test_editor_windows_qml as windows_fixture
from tests.profile_ui_responsiveness import frame
from tests.security_matrix_fixture import RULES, seed_security


class AdminSecurityUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        windows_fixture.EditorWindowQmlTests.setUpClass()

    def setUp(self):
        self.fixture = windows_fixture.EditorWindowQmlTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.admin = self.fixture.admin
        self.admin._project = 'demo'
        self.editor = self.admin.securityEditor
        seed_security(self.editor)
        self.admin.select_section('rules')
        self.admin.open()
        self.window = self.fixture.window('administration')
        self.window.resize(1100, 800)
        frame(self.window)

    def items(self):
        return windows_fixture.SidebarEditorQmlTests.descendants(self.window.contentItem())

    def item(self, name):
        return next(item for item in self.items() if item.objectName() == name and item.isVisible())

    def click(self, name):
        self.fixture.click(self.window, self.item(name))
        frame(self.window)

    def test_all_six_scopes_are_matrices_with_group_columns(self):
        for scope in ('project', 'link', 'gear_menu', 'search_type', 'process', 'tasks'):
            self.click('adminSecurityTab_' + scope)
            self.assertEqual(self.editor.matrix.scope, scope)
            self.assertEqual(self.item('adminSecurityMatrix').property('columns'), 3)
            self.assertFalse(any(item.objectName() == 'adminSecurityAdvancedGroup'
                                 and item.isVisible() for item in self.items()))
        self.assertEqual(self.editor.groupDocument['xml'], RULES)
        self.assertFalse(self.editor.dirty)
        self.assertEqual(self.fixture.warnings, [])

    def test_mouse_keyboard_and_touch_update_only_one_cell_without_rpc_or_reset(self):
        resets = QSignalSpy(self.editor.matrix.modelReset)
        with patch('thlib.tactic_classes.execute_procedure_serverside') as rpc:
            self.click('adminSecurityCell_0_1')
            self.assertTrue(self.editor.matrix.cell_at(0, 1)['checked'])
            self.assertEqual(self.editor.groupDocument['xml'], RULES)
            self.item('adminSecurityCell_0_1').forceActiveFocus()
            QTest.keyClick(self.window, Qt.Key_Space)
            frame(self.window)
            self.assertFalse(self.editor.matrix.cell_at(0, 1)['checked'])
            cell = self.item('adminSecurityCell_1_1')
            point = cell.mapToScene(QPointF(cell.width() / 2, cell.height() / 2)).toPoint()
            device = QTest.createTouchDevice()
            QTest.touchEvent(self.window, device).press(0, point, self.window).commit()
            QTest.touchEvent(self.window, device).release(0, point, self.window).commit()
            frame(self.window)
            self.assertTrue(self.editor.matrix.cell_at(1, 1)['checked'])
            rpc.assert_not_called()
        self.assertEqual(resets.count(), 0)
        self.assertEqual(self.fixture.warnings, [])

    def test_inherited_grants_and_custom_levels_are_not_silently_replaced(self):
        self.click('adminSecurityTab_process')
        self.assertFalse(self.item('adminSecurityCell_0_0').isEnabled())
        self.assertEqual(self.editor.rules[2]['access'], 'view')
        self.click('adminSecurityTab_technical')
        self.click('adminGroupAccessLevel_high')
        self.click('adminSecurityTab_project')
        # A specific project deny can override the wildcard: only the wildcard
        # grant itself is controlled by this group's high access level.
        self.assertTrue(self.item('adminSecurityCell_1_0').property('checked'))
        self.assertEqual(self.editor.groupDocument['xml'], RULES)

    def test_inherit_and_discard_keep_all_group_drafts(self):
        self.click('adminSecurityCell_1_1')
        self.click('adminSecurityInherit')
        self.assertFalse(self.editor.matrix.cell_at(1, 1)['explicit'])
        self.click('adminSecurityCell_1_1')
        self.click('adminSecurityTab_link')
        self.click('adminSecurityCell_0_1')
        self.assertTrue(self.editor.dirty)
        self.click('adminDiscardDocument')
        self.assertFalse(self.editor.dirty)
        self.assertFalse(self.editor.matrix.cell_at(0, 1)['checked'])
        self.assertEqual(self.editor.groupDocument['xml'], RULES)

    def test_advanced_search_rules_and_custom_xml_remain_available(self):
        self.click('adminSecurityTab_search_filter')
        self.click('adminAddAccessRule')
        self.assertEqual(self.editor.selectedAttributes['group'], 'search_filter')
        self.assertNotIn('access', self.editor.selectedAttributes)
        self.click('adminDiscardDocument')
        self.click('adminSecurityTab_technical')
        self.click('adminCustomAccessRule_5')
        self.assertEqual(json.loads(self.item('adminNativeDocumentText').property('text'))['extra'], 'keep')
        self.editor.apply_rule(self.editor.ruleText.replace('"keep"', '"updated"'))
        self.assertIn('<!--preserve-->', self.editor.groupDocument['xml'])
        self.assertIn('<extension name="unchanged"', self.editor.groupDocument['xml'])
        self.assertEqual(self.fixture.warnings, [])

    def test_narrow_wide_virtualization_and_scroll_gutters(self):
        seed_security(self.editor, group_count=40, row_count=100)
        frame(self.window)
        for width, height in ((900, 700), (1400, 940)):
            self.window.resize(width, height)
            frame(self.window)
            grid = self.item('adminSecurityMatrix')
            self.assertGreater(grid.height(), 100)
            for suffix in ('Vertical', 'Horizontal'):
                bar = self.item('adminSecurityMatrix' + suffix + 'Bar')
                self.assertTrue(bar.property('hasOverflow'))
                pos = bar.mapToItem(grid, QPointF())
                if suffix == 'Vertical':
                    self.assertGreaterEqual(pos.x(), grid.width())
                else:
                    self.assertGreaterEqual(pos.y(), grid.height())
            cells = [item for item in self.items() if item.objectName().startswith('adminSecurityCell_')]
            self.assertLess(len(cells), 200)
            grid.setProperty('contentY', 600)
            grid.setProperty('contentX', 400)
            frame(self.window)
            x, y = grid.property('contentX'), grid.property('contentY')
            self.editor.matrix.set_allowed(15, 4, True)
            frame(self.window)
            self.assertEqual((grid.property('contentX'), grid.property('contentY')), (x, y))
            self.assertEqual(self.fixture.warnings, [])
            output = os.environ.get('ADMIN_SECURITY_SCREENSHOTS')
            if output:
                Path(output).mkdir(parents=True, exist_ok=True)
                self.window.grabWindow().save(str(Path(output) / ('matrix_%s.png' % width)))

    def test_search_filters_labels_and_groups_without_server_requests(self):
        with patch('thlib.tactic_classes.execute_procedure_serverside') as rpc:
            field = self.item('adminSecurityGroupSearch')
            field.forceActiveFocus()
            for char in 'Artists 1':
                QTest.keyClick(self.window, char)
            frame(self.window)
            self.assertEqual(self.editor.matrix.columnCount(), 1)
            self.assertEqual(self.editor.matrix.groups[0]['identity'], 'G1')
            rpc.assert_not_called()

    def test_keyboard_arrows_and_real_wheel_keep_headers_synchronized(self):
        seed_security(self.editor, group_count=30, row_count=100)
        frame(self.window)
        self.click('adminSecurityCell_0_1')
        self.item('adminSecurityCell_0_1').forceActiveFocus()
        self.assertTrue(self.item('adminSecurityCell_0_1').property('activeFocus'))
        QTest.keyClick(self.window, Qt.Key_Down)
        frame(self.window)
        self.assertTrue(self.item('adminSecurityCell_1_1').property('activeFocus'), self.fixture.warnings)
        QTest.keyClick(self.window, Qt.Key_Right)
        frame(self.window)
        self.assertTrue(self.item('adminSecurityCell_1_2').property('activeFocus'),
                        (self.fixture.warnings, [item.objectName() for item in self.items()
                                                 if item.property('activeFocus')]))
        grid = self.item('adminSecurityMatrix')
        for _ in range(8):
            QTest.keyClick(self.window, Qt.Key_Right)
            frame(self.window)
        self.assertGreater(grid.property('contentX'), 0)
        point = grid.mapToScene(QPointF(grid.width() / 2, grid.height() / 2))
        QTest.mouseMove(self.window, point.toPoint())
        stopped = QSignalSpy(grid.movementEnded)
        event = QWheelEvent(point, QPointF(self.window.mapToGlobal(point.toPoint())),
                            QPoint(), QPoint(0, -720), Qt.NoButton, Qt.NoModifier,
                            Qt.NoScrollPhase, False)
        event.setTimestamp(time.monotonic_ns() // 1_000_000)
        QCoreApplication.sendEvent(self.window, event)
        if grid.property('moving'):
            self.assertTrue(stopped.wait(2000))
        frame(self.window)
        self.assertGreater(grid.property('contentY'), 0)
        self.assertAlmostEqual(self.item('adminSecurityRowHeaders').property('contentY'), grid.property('contentY'))
        self.assertAlmostEqual(self.item('adminSecurityColumnHeaders').property('contentX'), grid.property('contentX'))
        self.assertEqual(self.fixture.warnings, [])

    def test_save_read_only_busy_and_error_states(self):
        self.assertFalse(self.item('adminSaveDocument').isEnabled())
        self.click('adminSecurityCell_1_1')
        self.assertTrue(self.item('adminSaveDocument').isEnabled())
        self.assertFalse(self.item('adminReloadDocument').isEnabled())
        self.editor._can_write = False
        self.editor.stateChanged.emit()
        frame(self.window)
        self.assertFalse(self.item('adminSecurityCell_1_1').isEnabled())
        self.assertFalse(self.item('adminSaveDocument').isEnabled())
        with patch.object(self.editor, '_worker', object()):
            self.editor.stateChanged.emit()
            frame(self.window)
            self.assertFalse(self.item('adminDiscardDocument').isEnabled())
        self.editor.fail('Server rejected this draft')
        frame(self.window)
        self.assertEqual(self.item('adminDocumentError').property('text'), 'Server rejected this draft')
        self.click('adminDiscardDocument')
        self.assertFalse(self.editor.dirty)
        self.assertEqual(self.editor.error, '')
        self.assertEqual(self.fixture.warnings, [])


if __name__ == '__main__':
    unittest.main()
