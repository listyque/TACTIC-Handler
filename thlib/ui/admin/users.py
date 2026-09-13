"""Administrator user drafts; native profile writes and shared user identities."""

import copy

from PySide6.QtCore import QObject, Property, Signal, Slot

from thlib.ui.workspace_models.records import RecordListModel
from thlib.ui.user_identity import user_avatar_color, user_initials
from .editor import AdminDocumentEditor
from .users_api import query_admin_users


class AdminUsersEditor(AdminDocumentEditor):
    profileChanged = Signal()
    FIELDS = ('first_name', 'last_name', 'display_name', 'email', 'phone_number',
              'address', 'department', 'upn', 'namespace', 's_status',
              'project_code', 'license_type', 'hourly_wage')

    def __init__(self, application, users, parent=None):
        super().__init__(application, query_admin_users, parent)
        self.stateChanged.connect(self.profileChanged.emit)
        self._users = users
        self._objects = {}
        self._identities = {}
        self._query = ''
        self._show_retired = False
        self._avatars_dirty = False
        self._model = RecordListModel(('login', 'displayName', 'initials', 'avatarUrl',
                                      'avatarColor', 'email', 'retired'))
        self._groups_model = RecordListModel(('code', 'label', 'description', 'accessLevel',
                                             'projectCode', 'isDefault'))
        users.avatarsChanged.connect(self._avatar_files_changed)
        self.committed.connect(self._publish_saved)

    @Property(QObject, constant=True)
    def usersModel(self):
        return self._model

    @Property(QObject, constant=True)
    def groupsModel(self) -> RecordListModel:
        return self._groups_model

    @Property(bool, notify=profileChanged)
    def showRetired(self):
        return self._show_retired

    @Property('QVariantMap', notify=profileChanged)
    def profile(self):
        record = dict(self._identities.get(self._identity, {}))
        login = str(self._document.get('login') or '')
        name = str(self._document.get('display_name') or '').strip() or ' '.join(
            str(self._document.get(key) or '').strip() for key in ('first_name', 'last_name')).strip() or login
        return {**record, 'login': login, 'displayName': name,
                'initials': user_initials(name, login), 'avatarColor': user_avatar_color(login)}

    @Property('QStringList', notify=profileChanged)
    def groupNames(self):
        return list(self._document.get('groups', []))

    def activate(self, project: str) -> None:
        # Login accounts are server-wide, not owned by the selected project.
        if self._avatars_dirty:
            self._refresh_identities()
        super().activate('sthpw')

    def reset(self, project: str = '') -> None:
        if project and self._project == 'sthpw':
            return
        self._objects.clear()
        self._identities.clear()
        self._model.clear()
        self._groups_model.clear()
        super().reset('sthpw' if project else '')

    def _request(self, action: str, identity: str = '') -> None:
        if action == 'load':
            if self._closed or self.busy or not self._application.can_administer:
                return
            # The directory already carries these small profiles. Row selection
            # never queries TACTIC or changes the profile window/session login.
            row = next((row for row in self._catalog if row['identity'] == identity), None)
            if row is not None:
                self._identity = identity
                self._document = {**copy.deepcopy(row['document']), 'password': '',
                                  'groups': sorted(self._metadata.get('groups', {}).get(identity, []))}
                self._original = copy.deepcopy(self._document)
                self._error = ''
                self.stateChanged.emit()
            return
        super()._request(action, identity)

    def _execute_request(self, arguments: dict, project: str, original: dict) -> dict:
        from thlib import tactic_classes as tc, server_cache
        if arguments['action'] == 'save':
            data = arguments['document']
            identity = arguments['identity']
            values = {key: data[key] for key in self.FIELDS
                      if key in data and (not identity or data[key] != original.get(key))}
            if identity:
                membership = ({'groups': list(data['groups'])}
                              if data['groups'] != original.get('groups', []) else {})
                tc.mutate_user_profile(identity, values=values, password=data.get('password', ''),
                                       require_admin=True, **membership)
            else:
                identity = str(data.get('login') or '').strip()
                tc.create_user_profile(identity, values=values, password=data.get('password', ''),
                                       groups=list(data['groups']), require_admin=True)
            # A failed directory refresh must not leave committed account data
            # hidden behind a valid persistent reference cache.
            server_cache.invalidate_domains(('reference',), 'sthpw')
            result = tc.execute_procedure_serverside(query_admin_users, {}, project='sthpw')
            row = next(row for row in result['catalog'] if row['identity'] == identity)
            return {**result, 'identity': identity, 'revision': '',
                    'document': {**row['document'], 'password': '',
                                 'groups': sorted(result['metadata']['groups'].get(identity, []))}}
        return tc.execute_procedure_serverside(query_admin_users, {}, project='sthpw')

    def _catalog_loaded(self) -> None:
        from thlib.tactic_classes import Login, LoginGroup
        self._objects = {}
        for row in self._catalog:
            login = Login({**row['document'], '__snapshots__': row['snapshots']}, [], [])
            login.init_snapshots(row['snapshots'])
            self._objects[row['identity']] = login
        groups = []
        for info in self._metadata.get('groupCatalog', []):
            group = LoginGroup(info)
            groups.append({
                'code': group.get_login_group(), 'label': group.get_pretty_name(),
                'description': group.get_description() or '',
                'accessLevel': info.get('access_level') or '',
                'projectCode': info.get('project_code') or '',
                'isDefault': bool(info.get('is_default')),
            })
        self._groups_model.replace(sorted(groups, key=lambda row: (row['label'].casefold(), row['code'])))
        self._refresh_identities()

    @Slot(str, bool)
    def set_group(self, code: str, selected: bool) -> None:
        if self.busy or not self.canWrite or not self._application.can_administer or not self._document:
            return
        if not any(row['code'] == code for row in self._groups_model.records()):
            return
        groups = set(self._document['groups'])
        if selected:
            groups.add(code)
        else:
            groups.discard(code)
        super().set_field('groups', sorted(groups))

    @Slot()
    def _avatar_files_changed(self) -> None:
        self._avatars_dirty = True
        if (self.parent().section == 'users'
                and self._application.window_model.is_window_visible('administration')):
            self._refresh_identities()

    @Slot()
    def _refresh_identities(self) -> None:
        if self._closed:
            return
        self._identities = {login: self._users.identity_record(login, obj)
                            for login, obj in self._objects.items()}
        self._avatars_dirty = False
        self._rebuild_model()
        self.stateChanged.emit()

    def _rebuild_model(self) -> None:
        rows = []
        for login, obj in self._objects.items():
            info = obj.get_info()
            retired = info.get('s_status') == 'retired'
            identity = self._identities[login]
            if retired and not self._show_retired:
                continue
            email = str(info.get('email') or '')
            if self._query and self._query not in (
                    login + ' ' + identity['displayName'] + ' ' + email).casefold():
                continue
            rows.append({**identity, 'email': email, 'retired': retired})
        self._model.replace(sorted(rows, key=lambda row: (row['displayName'].casefold(), row['login'])))

    @Slot(str)
    def set_query(self, query: str) -> None:
        self._query = query.strip().casefold()
        self._rebuild_model()

    @Slot(bool)
    def set_show_retired(self, show: bool) -> None:
        self._show_retired = show
        self._rebuild_model()
        self.stateChanged.emit()

    @Slot()
    def new_document(self) -> None:
        if self.busy or self.dirty or not self.canWrite:
            return
        self._identity = ''
        self._document = {key: '' for key in self.FIELDS if key in self._metadata.get('fields', [])}
        self._document.update(login='', password='', groups=[])
        self._original = {}
        self._error = ''
        self.stateChanged.emit()

    @Slot(str, 'QVariant')
    def set_field(self, name: str, value) -> None:
        if name not in (*self.FIELDS, 'password') and not (name == 'login' and not self._identity):
            return
        super().set_field(name, value)

    @Slot()
    def save(self) -> None:
        if not str(self._document.get('login') or '').strip():
            self.fail(self.tr('A login is required'))
            return
        super().save()

    def clear_password(self) -> None:
        if self._document.get('password'):
            self._document['password'] = ''
            self.stateChanged.emit()

    def _publish_saved(self) -> None:
        from thlib.environment import env_inst
        login = self._objects[self._identity]
        existing = next((obj for obj in (env_inst.get_all_logins() or {}).values()
                         if obj.get_login() == self._identity), None)
        if existing is not None:
            existing.info.update(login.info)
            if login.info.get('s_status') == 'retired':
                env_inst.logins.pop(existing.get_code(), None)
        elif login.info.get('s_status') != 'retired':
            current = env_inst.get_current_login_object()
            if current is not None:
                from thlib.tactic_classes import Login
                fresh = Login(dict(login.info), current.login_groups, current.login_in_groups)
                fresh.init_snapshots(login.info.get('__snapshots__', []))
                env_inst.logins[fresh.get_code()] = fresh
        self._users._rebuild()
