"""Real group-editor cards, tabs, membership input and scrollable layouts."""

import os
from pathlib import Path
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QUICK_CONTROLS_STYLE', 'Material')

import tests.test_editor_windows_qml as windows_fixture
from tests.profile_ui_responsiveness import frame

from PySide6.QtCore import QPointF, Qt
from PySide6.QtTest import QTest


class AdminGroupsUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        windows_fixture.EditorWindowQmlTests.setUpClass()

    def setUp(self):
        self.fixture = windows_fixture.EditorWindowQmlTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.admin = self.fixture.admin
        self.admin.show_groups()
        self.admin.open()
        self.window = self.fixture.window('administration')
        frame(self.window)

    def item(self, name):
        return next(item for item in windows_fixture.SidebarEditorQmlTests.descendants(
            self.window.contentItem()) if item.objectName() == name and item.isVisible())

    def click(self, name):
        self.fixture.click(self.window, self.item(name))

    def type_text(self, name, text):
        self.click(name)
        QTest.keyClick(self.window, Qt.Key_A, Qt.ControlModifier)
        for character in text:
            QTest.keyClick(self.window, character)
        frame(self.window)

    def assert_inside_window(self, item):
        point = item.mapToScene(QPointF())
        self.assertGreaterEqual(point.x(), 0)
        self.assertGreaterEqual(point.y(), 0)
        self.assertLessEqual(point.x() + item.width(), self.window.width())
        self.assertLessEqual(point.y() + item.height(), self.window.height())

    def test_member_cards_and_group_list_keep_their_space_at_both_sizes(self):
        for width, height in ((900, 620), (1400, 940)):
            with self.subTest(width=width):
                frame(self.window, lambda: self.window.resize(width, height))
                frame(self.window)
                groups = self.item('securityGroupsList')
                members = self.item('securityMembersList')
                toolbar = self.item('administrationHeaderSaveBar')
                group_panel = groups.parentItem().parentItem().parentItem()
                toolbar_bottom = toolbar.mapToScene(QPointF(0, toolbar.height())).y()
                self.assertGreater(group_panel.mapToScene(QPointF()).y(), toolbar_bottom)
                self.assertFalse(any(
                    item.objectName() == 'adminGroupToolbar' and item.isVisible()
                    for item in windows_fixture.SidebarEditorQmlTests.descendants(
                        self.window.contentItem()
                    )
                ))
                self.assertGreater(groups.height(), self.window.height() * .5)
                self.assertGreater(members.height(), 160)
                self.assertEqual(members.property('count'), 80)
                self.assertEqual(groups.property('count'), 40)
                for name in ('securityGroupEditorTabs', 'securityMemberSearch',
                             'createSecurityGroup', 'saveSecurityGroup'):
                    self.assert_inside_window(self.item(name))
                for row_name, bar_name in (
                    ('securityGroup_G0', 'securityGroupsScrollBar'),
                    ('securityMember_user_0', 'securityMembersScrollBar'),
                ):
                    row = self.item(row_name)
                    bar = self.item(bar_name)
                    self.assertGreater(bar.property('reservedExtent'), 0)
                    row_edge = row.mapToScene(QPointF(row.width(), 0)).x()
                    self.assertLess(row_edge, bar.mapToScene(QPointF()).x())
                self.assertEqual(self.item('securityGroup_G0').property('description'), 'Team 0')
                self.assertTrue(self.item('securityMember_user_0').property('checked'))
                output = os.environ.get('ADMIN_SCREENSHOTS')
                if output:
                    Path(output).mkdir(parents=True, exist_ok=True)
                    self.window.grabWindow().save(str(Path(output) / ('groups_%s.png' % width)))
                self.assertEqual(self.fixture.warnings, [])

    def test_member_content_has_no_style_insets_and_fits_the_row(self):
        for display_name in ('Participant 00', 'user_0'):
            self.admin._catalog['users'][0]['displayName'] = display_name
            self.admin.set_user_query('user_0')
            frame(self.window)
            row = self.item('securityMember_user_0')
            content = row.property('contentItem')
            self.assertEqual((content.x(), content.y(), content.width(), content.height()),
                             (0, 0, row.width(), row.height()))
            avatar = self.item('userIdentityAvatar_user_0')
            offset = avatar.mapToItem(row, QPointF())
            self.assertEqual((offset.x(), offset.y(), avatar.width(), avatar.height()), (38, 7, 40, 40))
            self.assertAlmostEqual(offset.y() + avatar.height() / 2, row.height() / 2)
            title = self.item('memberTitle_user_0')
            position = title.mapToItem(row, QPointF())
            self.assertGreaterEqual(position.y(), 0)
            self.assertLessEqual(position.y() + title.height(), row.height())
            if display_name == 'user_0':
                self.assertEqual(position.y() + title.height() / 2, row.height() / 2)
            self.admin.set_user_query('no-matching-user')
            frame(self.window)
        self.assertEqual(self.fixture.warnings, [])

    def test_creation_edits_details_and_members_before_one_explicit_save(self):
        writes = []
        self.enterContext(patch.object(self.admin, '_run', side_effect=lambda *args: writes.append(args)))
        self.window.resize(900, 620)
        frame(self.window)
        self.click('createSecurityGroup')
        self.assertEqual(self.item('segmentedButtonSegment_details').property('checked'), True)
        self.assertFalse(self.item('securityGroupName').property('readOnly'))
        self.type_text('securityGroupName', 'lighting_team')
        self.type_text('securityGroupDescription', 'Lighting and look development')
        self.assertEqual(self.admin.draft['name'], 'lighting_team')
        self.assertEqual(self.admin.draft['description'], 'Lighting and look development')
        self.click('segmentedButtonSegment_members')
        self.type_text('securityMemberSearch', 'Participant 01')
        self.assertEqual(self.admin.members.rowCount(), 1)
        self.click('securityMember_user_1')
        self.assertEqual(self.admin.memberCount, 1)
        self.assertTrue(self.admin.dirty)
        self.assertFalse(self.item('securityGroup_G0').isEnabled())
        self.assertEqual(writes, [])
        self.click('saveSecurityGroup')
        self.assertEqual(len(writes), 1)
        self.fixture.fixture.fixture.rpc.assert_not_called()

    def test_keyboard_selects_groups_and_membership_is_discardable(self):
        group = self.item('securityGroup_G1')
        group.forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Return)
        frame(self.window)
        self.assertEqual(self.admin.draft['code'], 'G1')
        self.assertTrue(self.item('securityGroup_G1').property('selected'))
        self.type_text('securityMemberSearch', 'user_3')
        member = self.item('securityMember_user_3')
        member.forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Space)
        frame(self.window)
        self.assertEqual(self.admin.memberCount, 1)
        self.click('adminDiscardDocument')
        self.assertTrue(self.admin.dirty)
        self.click('confirmDiscardSecurityGroup')
        self.assertEqual(self.admin.memberCount, 0)
        self.assertFalse(self.admin.dirty)
        self.assertFalse(self.item('securityMember_user_3').property('checked'))

    def test_retired_member_is_dimmed_but_can_still_be_unlinked(self):
        self.admin._catalog['users'][0]['retired'] = True
        self.admin._rebuild_members()
        frame(self.window)
        output = os.environ.get('ADMIN_SCREENSHOTS')
        if output:
            Path(output).mkdir(parents=True, exist_ok=True)
            self.assertTrue(self.window.grabWindow().save(str(Path(output) / 'groups_retired.png')))
        self.type_text('securityMemberSearch', 'user_0')
        member = self.item('securityMember_user_0')
        identity = self.item('userIdentityAvatar_user_0').parentItem()
        self.assertEqual(identity.opacity(), 0.5)
        self.assertTrue(member.isEnabled())
        self.assertTrue(member.property('checked'))
        self.click('securityMember_user_0')
        self.assertFalse(member.property('checked'))
        self.assertTrue(self.admin.dirty)
        self.fixture.fixture.fixture.rpc.assert_not_called()

    def test_arrow_keys_move_the_tab_and_keyboard_focus_together(self):
        self.item('segmentedButtonSegment_members').forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Right)
        frame(self.window)
        self.assertTrue(self.item('segmentedButtonSegment_details').property('checked'))
        self.assertEqual(self.window.activeFocusItem().objectName(), 'segmentedButtonSegment_details')
        QTest.keyClick(self.window, Qt.Key_Left)
        frame(self.window)
        self.assertTrue(self.item('segmentedButtonSegment_members').property('checked'))
        self.assertEqual(self.window.activeFocusItem().objectName(), 'segmentedButtonSegment_members')

    def test_unknown_write_requires_confirmed_reload_before_another_save(self):
        from types import SimpleNamespace
        from PySide6.QtCore import QObject, Signal
        from thlib.environment import env_inst

        class Worker(QObject):
            result = Signal(object)
            error = Signal(object)
            def start(self):
                pass
            def cancel(self):
                pass

        worker = Worker()
        self.admin.reload.side_effect = lambda force=False: type(self.admin).reload(self.admin, force)
        from unittest.mock import Mock
        submit = Mock(return_value=worker)
        pool = SimpleNamespace(is_stopped=False, add_task=submit)
        self.enterContext(patch.object(env_inst, 'server_pool', pool))
        self.admin.set_member('user_1', True)
        self.click('saveSecurityGroup')
        self.assertTrue(self.admin.busy)
        worker.error.emit(({'exception': ConnectionError('response lost')}, worker))
        frame(self.window)
        self.assertTrue(self.admin.groupUncertain)
        self.assertTrue(self.admin.projectLocked)
        self.assertFalse(self.item('saveSecurityGroup').isEnabled())
        self.admin.save()
        self.assertEqual(submit.call_count, 1)
        self.click('adminReloadDocument')
        self.assertEqual(submit.call_count, 1)
        self.click('keepSecurityGroup')
        self.assertTrue(self.admin.dirty)
        self.click('adminReloadDocument')
        self.click('confirmDiscardSecurityGroup')
        self.assertEqual(submit.call_count, 2)
        worker.result.emit(self.admin._catalog)
        frame(self.window)
        self.assertFalse(self.admin.groupUncertain)
        self.assertFalse(self.admin.dirty)
        self.assertEqual(self.admin.memberCount, 1)

    def test_touch_changes_one_membership_only_once(self):
        self.type_text('securityMemberSearch', 'Participant 01')
        member = self.item('securityMember_user_1')
        point = member.mapToScene(QPointF(member.width() / 2, member.height() / 2)).toPoint()
        device = QTest.createTouchDevice()
        sequence = QTest.touchEvent(self.window, device, autoCommit=False)
        with patch.object(self.admin, 'set_member', wraps=self.admin.set_member) as update:
            sequence.press(0, point, self.window).commit()
            frame(self.window)
            sequence.release(0, point, self.window).commit()
            frame(self.window)
        update.assert_called_once_with('user_1', True)
        self.assertEqual(self.admin.memberCount, 2)

    def test_existing_identifier_is_read_only_and_details_have_a_shared_scrollbar(self):
        self.admin._catalog['groups'][0]['description'] = (
            'Production group: lighting, rendering and look development.\n' * 18)
        self.admin._loaded(self.admin._catalog)
        self.window.resize(900, 500)
        frame(self.window)
        self.click('segmentedButtonSegment_details')
        self.assertTrue(self.item('securityGroupName').property('readOnly'))
        details = self.item('securityGroupDetails')
        bar = self.item('securityDetailsScrollBar')
        self.assertGreater(details.property('contentHeight'), details.height())
        self.assertGreater(bar.property('reservedExtent'), 0)
        # Thumb input scrolls the form, while the selected group remains intact.
        point = bar.mapToScene(QPointF(bar.width() / 2, bar.height() - 3))
        QTest.mouseClick(self.window, Qt.LeftButton, pos=point.toPoint())
        frame(self.window)
        self.assertGreater(details.property('contentY'), 0)
        self.assertEqual(self.admin.draft['code'], 'G0')
        self.assertFalse(self.admin.dirty)
        self.assert_inside_window(self.item('saveSecurityGroup'))


if __name__ == '__main__':
    unittest.main()
