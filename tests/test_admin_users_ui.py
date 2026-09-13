"""User administration through the real modal window and shared identity UI."""

import copy
import os
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('QT_QUICK_CONTROLS_STYLE', 'Material')

from PySide6.QtCore import QEvent, QCoreApplication, QMetaObject, QObject, QPointF, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QImage
from PySide6.QtQml import QQmlComponent
from PySide6.QtTest import QTest

import tests.test_editor_windows_qml as windows_fixture
from tests.profile_ui_responsiveness import frame
from thlib.ui.user_identity import user_avatar_color


class AdminUsersUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        windows_fixture.EditorWindowQmlTests.setUpClass()

    def setUp(self):
        self.fixture = windows_fixture.EditorWindowQmlTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.admin = self.fixture.admin
        self.editor = self.admin.usersEditor
        self.editor._project = 'sthpw'
        self.editor._loaded = self.editor._can_write = True
        self.editor._metadata = {'groups': {'user_0': ['Artists', 'Lighting']},
                                 'fields': list(self.editor.FIELDS),
                                 'groupCatalog': [
                                     dict(code='GROUP_%s' % n, login_group=name,
                                          description='Team ' + name, project_code='')
                                     for n, name in enumerate(['Artists', 'Lighting', 'Rigging'])]}
        self.editor._catalog = [{
            'identity': 'user_%s' % n,
            'document': {**dict.fromkeys(self.editor.FIELDS, ''),
                         'login': 'user_%s' % n, 'code': 'user_%s' % n,
                         'display_name': 'Participant %02d' % n,
                         's_status': 'retired' if n == 79 else '',
                         'email': 'artist%s@example.test' % n},
            'snapshots': [],
        } for n in range(80)]
        self.editor._catalog_loaded()
        self.editor.select('user_0')
        self.admin.select_section('users')
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

    def test_retired_toggle_and_search_keep_hidden_users_out_until_requested(self):
        self.assertEqual(self.item('adminUsersList').property('count'), 79)
        active_identity = self.item('userIdentityAvatar_user_0').parentItem()
        self.assertEqual(active_identity.opacity(), 1)
        self.click('adminShowRetiredUsers')
        self.assertEqual(self.item('adminUsersList').property('count'), 80)
        self.type_text('adminUserSearch', 'artist79@')
        self.assertEqual(self.item('adminUsersList').property('count'), 1)
        row = self.item('adminUser_user_79')
        self.assertTrue(row.property('retired'))
        retired_identity = self.item('userIdentityAvatar_user_79').parentItem()
        self.assertEqual(retired_identity.opacity(), 0.5)
        self.assertTrue(row.isEnabled())
        row.forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Return)
        frame(self.window)
        self.assertEqual(self.editor.document['login'], 'user_79')
        output = os.environ.get('ADMIN_SCREENSHOTS')
        if output:
            Path(output).mkdir(parents=True, exist_ok=True)
            self.assertTrue(self.window.grabWindow().save(str(Path(output) / 'users_retired.png')))
        self.click('segmentedButtonSegment_account')
        form = self.item('adminUserForm')
        form.setProperty('contentY', form.property('contentHeight') - form.height())
        frame(self.window)
        self.assertTrue(self.item('adminUserRetired').property('checked'))
        self.click('adminUserRetired')
        self.assertEqual(self.editor.document['s_status'], '')
        self.assertTrue(self.editor.dirty)
        self.editor.discard()
        self.click('adminShowRetiredUsers')
        self.assertEqual(self.item('adminUsersList').property('count'), 0)
        self.fixture.fixture.fixture.rpc.assert_not_called()

    def test_mouse_keyboard_edit_keeps_focus_and_does_not_change_session_or_profile(self):
        selected_profile = copy.deepcopy(self.fixture.users.profile)
        login = self.fixture.users.login
        self.click('adminUser_user_1')
        field = self.item('adminUserField_first_name')
        self.type_text('adminUserField_first_name', 'Alex')
        self.assertIs(self.item('adminUserField_first_name'), field)
        self.assertEqual(self.editor.document['first_name'], 'Alex')
        self.assertTrue(field.hasActiveFocus())
        self.assertEqual(self.fixture.users.login, login)
        self.assertEqual(self.fixture.users.profile, selected_profile)
        self.assertFalse(self.item('adminUser_user_0').isEnabled())
        self.click('adminDiscardDocument')
        self.assertEqual(self.editor.document['first_name'], '')
        self.assertFalse(self.editor.dirty)
        self.fixture.fixture.fixture.rpc.assert_not_called()

    def test_new_account_save_requires_confirmation_and_retains_server_error(self):
        self.click('adminCreateDocument')
        self.type_text('adminUserLogin', 'new_artist')
        self.type_text('adminUserField_first_name', 'Alice')
        self.assertTrue(self.editor.dirty)
        with patch.object(self.editor, '_request') as request:
            self.click('adminSaveDocument')
            request.assert_not_called()
            self.click('adminConfirmSave')
            request.assert_called_once_with('save', '')
        self.editor.fail('Test: duplicate login')
        frame(self.window)
        self.assertIn('duplicate', self.item('adminDocumentError').property('text'))
        self.assertEqual(self.editor.document['login'], 'new_artist')

    def test_profile_group_page_and_touch_selection(self):
        row = self.item('adminUser_user_1')
        point = row.mapToScene(QPointF(row.width() / 2, row.height() / 2)).toPoint()
        device = QTest.createTouchDevice()
        sequence = QTest.touchEvent(self.window, device, autoCommit=False)
        sequence.press(0, point, self.window).commit()
        frame(self.window)
        sequence.release(0, point, self.window).commit()
        frame(self.window)
        self.assertEqual(self.editor.identity, 'user_1')
        self.click('adminUserManageGroups')
        self.assertEqual(self.admin.section, 'users')
        self.click('userGroupMembership_Artists')
        self.assertEqual(self.editor.document['groups'], ['Artists'])
        self.assertTrue(self.editor.dirty)
        self.fixture.fixture.fixture.rpc.assert_not_called()

    def test_membership_edit_is_local_reversible_and_does_not_select_another_profile(self):
        selected_profile = copy.deepcopy(self.fixture.users.profile)
        login = self.fixture.users.login
        self.click('adminUserManageGroups')
        self.assertTrue(self.item('userGroupMembership_Artists').property('checked'))
        self.click('userGroupMembership_Artists')
        checkbox = self.item('userGroupMembership_Rigging')
        checkbox.forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Space)
        frame(self.window)
        self.assertEqual(self.editor.document['groups'], ['Lighting', 'Rigging'])
        self.assertFalse(self.item('adminUser_user_1').isEnabled())
        self.assertEqual(self.fixture.users.login, login)
        self.assertEqual(self.fixture.users.profile, selected_profile)
        self.click('adminDiscardDocument')
        self.assertEqual(self.editor.document['groups'], ['Artists', 'Lighting'])
        self.assertTrue(self.item('userGroupMembership_Artists').property('checked'))
        self.assertFalse(self.item('userGroupMembership_Rigging').property('checked'))
        self.fixture.fixture.fixture.rpc.assert_not_called()

    def test_narrow_wide_forms_have_avatars_gutters_and_visible_save_actions(self):
        for width, height in ((900, 620), (1400, 940)):
            frame(self.window, lambda: self.window.resize(width, height))
            frame(self.window)
            for name in ('adminUserEditorTabs', 'adminSaveDocument', 'adminShowRetiredUsers'):
                item = self.item(name)
                point = item.mapToScene(QPointF())
                self.assertGreaterEqual(point.x(), 0)
                self.assertLessEqual(point.x() + item.width(), self.window.width())
                self.assertLessEqual(point.y() + item.height(), self.window.height())
            avatar = self.item('userIdentityAvatar_user_0')
            self.assertGreaterEqual(avatar.width(), 40)
            self.assertEqual(avatar.property('accent').name(), user_avatar_color('user_0'))
            self.assertFalse(avatar.property('animateAppearance'))
            for list_name, bar_name in (('adminUsersList', 'adminUsersScrollBar'),
                                        ('adminUserForm', 'adminUserFormScrollBar')):
                view = self.item(list_name)
                if view.property('contentHeight') > view.height():
                    bar = self.item(bar_name)
                    self.assertGreater(bar.property('reservedExtent'), 0)
            output = os.environ.get('ADMIN_SCREENSHOTS')
            if output:
                Path(output).mkdir(parents=True, exist_ok=True)
                self.window.grabWindow().save(str(Path(output) / ('users_%s.png' % width)))
        self.assertEqual(self.fixture.warnings, [])

    def test_password_is_cleared_on_close_and_read_only_state_disables_fields(self):
        self.editor.set_field('password', 'test-only-secret')
        self.admin._visibility_changed('administration', False)
        self.assertEqual(self.editor.document['password'], '')
        self.editor._can_write = False
        self.editor.stateChanged.emit()
        frame(self.window)
        self.assertFalse(self.item('adminUserField_first_name').isEnabled())
        self.assertFalse(self.item('adminSaveDocument').isEnabled())

    def test_groups_and_directory_render_the_same_native_avatar_without_animation(self):
        from thlib.environment import env_mode
        image_path = Path(env_mode.current_path) / 'fixture_avatar.png'
        image = QImage(64, 64, QImage.Format_RGB32)
        image.fill(QColor('steelblue'))
        self.assertTrue(image.save(str(image_path)))
        avatar_url = QUrl.fromLocalFile(str(image_path)).toString()
        file_object = SimpleNamespace(get_full_abs_path=lambda: str(image_path), is_local_current=lambda: True)
        with patch('thlib.ui.user.user_avatar_file_candidates',
                   side_effect=lambda obj: [file_object] if obj.get_login() == 'user_0' else []):
            self.editor._refresh_identities()
        self.fixture.users.users.replace([self.editor._identities['user_0']])
        frame(self.window)
        self.assertEqual(self.item('userIdentityAvatar_user_0').property('source').toString(), avatar_url)
        self.click('adminSection_groups')
        frame(self.window)
        avatar = self.item('userIdentityAvatar_user_0')
        self.assertEqual(avatar.property('source').toString(), avatar_url)
        self.assertEqual(avatar.property('accent').name(), user_avatar_color('user_0'))
        self.assertFalse(avatar.property('animateAppearance'))
        # A hidden Users editor keeps data pending, not re-resolving every avatar.
        with patch.object(self.fixture.users, 'identity_record') as resolve:
            self.fixture.users.avatarsChanged.emit()
            resolve.assert_not_called()
        output = os.environ.get('ADMIN_SCREENSHOTS')
        if output:
            Path(output).mkdir(parents=True, exist_ok=True)
            self.assertTrue(self.window.grabWindow().save(str(Path(output) / 'groups_avatar.png')))

    def test_worker_uses_captured_field_deltas_and_native_profile_write(self):
        from thlib import tactic_classes as tc
        original = copy.deepcopy(self.editor.document)
        draft = {**original, 'first_name': 'Alex'}
        catalog = copy.deepcopy(self.editor._catalog)
        catalog[0]['document']['first_name'] = 'Alex'
        with patch.object(tc, 'execute_procedure_serverside', return_value={
                'catalog': catalog, 'metadata': self.editor.metadata, 'canWrite': True}), patch.object(
                tc, 'mutate_user_profile') as mutate:
            result = self.editor._execute_request({'action': 'save', 'identity': 'user_0',
                                                   'document': draft}, 'sthpw', original)
        mutate.assert_called_once_with('user_0', values={'first_name': 'Alex'},
                                       password='', require_admin=True)
        self.assertEqual(result['document']['password'], '')
        self.assertEqual(result['document']['first_name'], 'Alex')

    def test_membership_save_confirms_captures_login_and_publishes_server_result(self):
        from thlib import tactic_classes as tc
        from thlib.environment import env_inst

        class Worker(QObject):
            result = Signal(object)
            error = Signal(object)

            def start(self):
                pass

        operation = []
        worker = Worker()
        pool = SimpleNamespace(is_stopped=False, add_task=lambda task: operation.append(task) or worker)
        self.click('adminUserManageGroups')
        self.click('userGroupMembership_Artists')
        self.click('userGroupMembership_Rigging')
        self.type_text('adminUserSearch', 'user_0')
        metadata = copy.deepcopy(self.editor.metadata)
        metadata['groups']['user_0'] = ['Lighting', 'Rigging']
        metadata['groups']['user_1'] = ['Artists']
        with patch.object(env_inst, 'server_pool', pool), patch.object(
                tc, 'mutate_user_profile') as mutate, patch.object(
                tc, 'execute_procedure_serverside', return_value={
                    'catalog': self.editor.catalog, 'metadata': metadata, 'canWrite': True}):
            self.click('adminSaveDocument')
            self.assertFalse(operation)
            self.click('adminConfirmSave')
            self.assertTrue(self.editor.busy)
            self.assertFalse(self.item('adminUserManageGroups').isEnabled())
            self.assertFalse(self.item('userGroupMembership_Artists').isEnabled())
            self.editor.select('user_1')
            self.editor.save()
            self.assertEqual(len(operation), 1)
            result = operation[0]()
            worker.result.emit(result)
            frame(self.window)
        mutate.assert_called_once_with('user_0', values={}, password='', require_admin=True,
                                       groups=['Lighting', 'Rigging'])
        self.assertFalse(self.editor.busy)
        self.assertFalse(self.editor.dirty)
        self.assertEqual(self.editor.identity, 'user_0')
        self.assertEqual(self.editor.document['groups'], ['Lighting', 'Rigging'])
        self.assertEqual({row['name']: row['memberCount'] for row in self.admin.groups.records()},
                         {'Artists': 1, 'Lighting': 1, 'Rigging': 1})
        self.editor.select('user_1')
        self.assertEqual(self.editor.document['groups'], ['Artists'])

    def test_new_account_sends_selected_groups_to_native_create(self):
        from thlib import tactic_classes as tc
        self.click('adminCreateDocument')
        self.type_text('adminUserLogin', 'new_artist')
        self.click('adminUserManageGroups')
        self.click('userGroupMembership_Rigging')
        document = copy.deepcopy(self.editor.document)
        with patch.object(tc, 'create_user_profile') as create, patch.object(
                tc, 'execute_procedure_serverside', return_value={
                    'catalog': [{'identity': 'new_artist', 'document': document}],
                    'metadata': {'groups': {'new_artist': ['Rigging']}}, 'canWrite': True}):
            result = self.editor._execute_request(
                {'action': 'save', 'identity': '', 'document': document}, 'sthpw', {})
        self.assertEqual(create.call_args.kwargs['groups'], ['Rigging'])
        self.assertEqual(result['document']['groups'], ['Rigging'])
        self.assertEqual(create.call_args.args, ('new_artist',))

    def test_membership_list_narrow_wide_scrolls_and_read_only_rejects_changes(self):
        self.editor._metadata['groupCatalog'].extend([
            dict(code='EXTRA_%s' % n, login_group='team_%02d' % n,
                 description='Long group description ' * 8, project_code='test_project')
            for n in range(35)])
        self.editor._catalog_loaded()
        self.click('adminUserManageGroups')
        for width, height in ((900, 620), (1400, 940)):
            frame(self.window, lambda: self.window.resize(width, height))
            form = self.item('adminUserForm')
            bar = self.item('adminUserFormScrollBar')
            self.assertGreater(form.property('contentHeight'), form.height())
            self.assertGreater(bar.property('reservedExtent'), 0)
            first = self.item('userGroupMembership_Artists')
            row = first.parentItem().parentItem()
            self.assertLessEqual(row.width(), form.width() - bar.property('reservedExtent') - 4)
            point = bar.mapToScene(QPointF(bar.width() / 2, bar.height() - 8)).toPoint()
            QTest.mouseClick(self.window, Qt.LeftButton, pos=point)
            frame(self.window)
            self.assertGreater(form.property('contentY'), 0)
            form.setProperty('contentY', 0)
            output = os.environ.get('ADMIN_SCREENSHOTS')
            if output:
                Path(output).mkdir(parents=True, exist_ok=True)
                self.assertTrue(self.window.grabWindow().save(str(Path(output) / ('user_groups_%s.png' % width))))
        original = copy.deepcopy(self.editor.document)
        self.editor._can_write = False
        self.editor.stateChanged.emit()
        frame(self.window)
        self.assertFalse(self.item('userGroupMembership_Artists').isEnabled())
        self.assertFalse(self.item('adminUserManageGroups').isEnabled())
        self.editor.set_group('Rigging', True)
        self.assertEqual(self.editor.document, original)
        self.assertEqual(self.fixture.warnings, [])

    def test_user_save_refreshes_both_membership_directions_without_a_groups_page(self):
        from thlib.environment import env_inst
        from thlib.tactic_classes import Login, LoginGroup
        from thlib.ui.administration import AdministrationController
        groups = [LoginGroup(dict(row)) for row in self.editor.metadata['groupCatalog']]
        memberships = [{'login': 'user_0', 'login_group': 'Artists'},
                       {'login': 'user_1', 'login_group': 'Artists'}]
        logins = {row['identity']: Login(dict(row['document']), groups, memberships)
                  for row in self.editor.catalog[:2]}
        self.admin._catalog = {'groups': [], 'memberships': [], 'users': []}
        self.admin.groups.clear()
        self.editor._metadata['groups'] = {'user_0': ['Rigging'], 'user_1': ['Artists']}
        with patch.object(env_inst, 'logins', logins), patch.object(
                self.admin, '_publish_catalog',
                side_effect=lambda: AdministrationController._publish_catalog(self.admin)):
            self.admin._user_document_saved()
        self.assertEqual([group.get_login_group() for group in logins['user_0'].get_login_groups()],
                         ['Rigging'])
        self.assertEqual([group.get_login_group() for group in logins['user_1'].get_login_groups()],
                         ['Artists'])
        by_name = {group.get_login_group(): group for group in logins['user_0'].get_all_login_groups()}
        self.assertEqual([user.get_login() for user in by_name['Rigging'].get_logins()], ['user_0'])
        self.assertEqual([user.get_login() for user in by_name['Artists'].get_logins()], ['user_1'])
        self.assertEqual(self.admin.groups.rowCount(), 0)
        self.admin.select_section('groups')
        self.admin.reload.assert_called()

    def test_removing_last_memberships_keeps_save_enabled_and_rejects_unknown_group(self):
        self.click('adminUserManageGroups')
        self.click('userGroupMembership_Artists')
        self.click('userGroupMembership_Lighting')
        self.editor.set_group('missing', True)
        self.assertEqual(self.editor.document['groups'], [])
        self.assertTrue(self.item('adminSaveDocument').isEnabled())

    def test_profile_editor_uses_same_checkboxes_and_preserves_access_level_edits(self):
        from thlib.ui.workspace_models.records import RecordListModel
        model = RecordListModel(('code', 'label', 'description', 'accessLevel',
                                 'projectCode', 'isDefault', 'member'))
        model.replace([{**row, 'member': row['code'] == 'Artists'}
                       for row in self.editor.groupsModel.records()])
        self.fixture.engine.rootContext().setContextProperty('userGroupModel', model)
        component = QQmlComponent(self.fixture.engine)
        component.setData(b'''
import QtQuick
import "." as App
Item {
    App.Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    QtObject {
        id: controller
        objectName: "profileMembershipTestController"
        property bool canManageUsers: true
        property bool editingBusy: false
        property string editingError: ""
        property var profile: ({login: "viewed_user", displayName: "Viewed User"})
        property var savedGroups: []
        property var savedLevels: ({})
        signal profileSaved()
        function save_group_settings(groups, levels) {
            savedGroups = groups
            savedLevels = levels
            return true
        }
    }
    App.UserProfileEditorDialog {
        id: dialog
        objectName: "profileMembershipTestDialog"
        controller: controller
        theme: theme
    }
}
''', QUrl.fromLocalFile(str(windows_fixture.QML / '_MembershipReuseTest.qml')))
        wrapper = component.create()
        self.assertIsNotNone(wrapper, [error.toString() for error in component.errors()])
        wrapper.setParentItem(self.window.contentItem())
        dialog = wrapper.findChild(QObject, 'profileMembershipTestDialog')
        controller = wrapper.findChild(QObject, 'profileMembershipTestController')
        try:
            self.assertTrue(QMetaObject.invokeMethod(dialog, 'openForGroups'))
            frame(self.window)
            self.assertTrue(self.item('userGroupMembership_Artists').property('checked'))
            self.click('userGroupMembership_Lighting')
            levels = self.item('userGroupAccessLevel_Artists')
            levels.forceActiveFocus()
            QTest.keyClick(self.window, Qt.Key_Down)
            frame(self.window)
            self.click('userProfileEditorSave')
            self.assertEqual(controller.property('savedGroups').toVariant(), ['Artists', 'Lighting'])
            self.assertEqual(controller.property('savedLevels').toVariant()['Artists'], 'high')
            self.assertEqual(self.fixture.warnings, [])
        finally:
            QMetaObject.invokeMethod(dialog, 'close')
            wrapper.setParentItem(None)
            wrapper.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_cancelled_directory_worker_cannot_repopulate_a_new_session(self):
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
        pool = SimpleNamespace(is_stopped=False, add_task=lambda operation: worker)
        with patch.object(env_inst, 'server_pool', pool):
            self.editor.reload()
        loaded = self.editor._callbacks[0]
        self.editor.reset()
        self.assertTrue(worker.cancelled)
        loaded({'catalog': [{'identity': 'stale'}], 'canWrite': True})
        self.assertEqual(self.editor.document, {})
        self.assertEqual(self.editor.usersModel.rowCount(), 0)
