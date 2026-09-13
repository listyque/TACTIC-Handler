"""Administration sections, group drafts and committed project metadata."""

from __future__ import annotations

from collections.abc import Callable
import copy
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Property, Qt, Signal, Slot

from thlib.ui.workspace_models.records import RecordListModel
from .admin.graph_editor import GraphEditor
from .admin.search_types import SearchTypesEditor
from .admin.schema_type import SchemaTypeEditor
from .admin.security import SecurityRulesEditor
from .admin.users import AdminUsersEditor
from .user_identity import user_avatar_color, user_initials

if TYPE_CHECKING:
    from .naming_editor import NamingEditorController


class AdministrationController(QObject):
    stateChanged = Signal()
    groupsChanged = Signal()

    def __init__(self, application, users, *, previews=None) -> None:
        super().__init__()
        self._application = application
        self._users = users
        self._naming_editor = None
        self.groups = RecordListModel(('code', 'name', 'description', 'memberCount'))
        self.members = RecordListModel(('login', 'displayName', 'member', 'initials',
                                        'avatarUrl', 'avatarColor', 'retired'))
        self._catalog = {'groups': [], 'memberships': [], 'users': []}
        self._draft = {}
        self._original = {}
        self._members = set()
        self._original_members = set()
        self._query = ''
        self._error = ''
        self._worker = None
        self._worker_callbacks = None
        self._generation = 0
        self._closed = False
        self._server_key = (application.server_url, application.server_user)
        self._section = 'groups'
        self._project = ''
        self._pending_metadata = set()
        self._types_editor = SearchTypesEditor(application, self, previews=previews)
        self._schema_editor = GraphEditor(application, 'schema', self)
        self._schema_type_editor = SchemaTypeEditor(
            application, self._schema_editor, self, previews=previews)
        self._schema_type_editor.stateChanged.connect(self.stateChanged.emit)
        self._schema_type_editor.created.connect(self._schema_type_created)
        self._workflow_editor = GraphEditor(application, 'workflow', self)
        self._schema_editor.deletionEditor.committed.connect(self._schema_type_deleted)
        self._workflow_editor.rulesEditor.stateChanged.connect(self.stateChanged.emit)
        self._security_editor = SecurityRulesEditor(application, self)
        self._users_editor = AdminUsersEditor(application, users, self)
        self._editors = {'types': self._types_editor, 'schema': self._schema_editor,
                         'workflow': self._workflow_editor, 'rules': self._security_editor,
                         'users': self._users_editor}
        for editor in self._editors.values():
            editor.stateChanged.connect(self.stateChanged.emit)
        for editor in (self._types_editor, self._schema_editor, self._workflow_editor):
            editor.committed.connect(self._project_document_saved)
        self._security_editor.committed.connect(self._security_document_saved)
        self._users_editor.committed.connect(self._user_document_saved)
        users.users.contentReplaced.connect(self._rebuild_members)
        application._registry.register('show_administration', self.open)
        application.window_model.windowVisibilityChanged.connect(self._visibility_changed)
        application.server_state_changed.connect(self._server_changed)
        if hasattr(users, 'stateChanged'):
            users.stateChanged.connect(self.stateChanged.emit)

    @Property(bool, notify=stateChanged)
    def canManage(self) -> bool:
        return self._application.can_administer

    @Property(QObject, constant=True)
    def typesEditor(self):
        return self._types_editor

    def attach_naming_editor(self, editor: NamingEditorController) -> None:
        self._naming_editor = editor
        editor.stateChanged.connect(self.stateChanged.emit)

    @Property(QObject, constant=True)
    def namingEditor(self):
        return self._naming_editor

    @Property(QObject, constant=True)
    def schemaEditor(self):
        return self._schema_editor

    @Property(QObject, constant=True)
    def schemaTypeEditor(self):
        return self._schema_type_editor

    @Property(QObject, constant=True)
    def workflowEditor(self):
        return self._workflow_editor

    @Property(QObject, constant=True)
    def securityEditor(self):
        return self._security_editor

    @Property(QObject, constant=True)
    def usersEditor(self):
        return self._users_editor

    @Property(str, notify=stateChanged)
    def section(self):
        return self._section

    @Property(str, notify=stateChanged)
    def project(self):
        return self._project

    @Property(bool, notify=stateChanged)
    def projectLocked(self):
        has_draft = (
            self.dirty
            or self._schema_type_editor.dirty
            or self._workflow_editor.rulesEditor.dirty
            or (self._naming_editor is not None and self._naming_editor.dirty)
            or any(editor.dirty for editor in self._editors.values())
        )
        if has_draft:
            return True
        active_editor = self._editors.get(self._section)
        if active_editor is not None and active_editor.projectUnavailable:
            # A missing project database is not recoverable from inside its
            # editor. Switching projects is the recovery path; reset() safely
            # cancels any remaining read workers.
            return False
        return (
            self.busy
            or self._schema_type_editor.busy
            or self._workflow_editor.rulesEditor.busy
            or (self._naming_editor is not None and self._naming_editor.busy)
            or any(editor.busy for editor in self._editors.values())
        )

    @Slot(str)
    def select_section(self, section: str) -> None:
        if not self.canManage or section not in {'groups', *self._editors}:
            return
        self._section = section
        if section in self._editors:
            self._editors[section].activate(self._project)
        elif not self.groups.rowCount():
            self.reload()
        self.stateChanged.emit()

    @Slot(str)
    def select_project(self, project: str) -> None:
        if self.canManage and not self.projectLocked and project != self._project:
            self._project = project
            for editor in self._editors.values():
                editor.reset(project)
            self._schema_type_editor.reset(project)
            self.select_section(self._section)

    @Slot(str)
    def open_type_workflow(self, identity: str) -> None:
        if not self.canManage or not any(
                row['identity'] == identity for row in self._types_editor.metadata.get('pipelines', [])):
            return
        editor = self._workflow_editor
        if editor.busy or (editor.dirty and editor.identity != identity):
            self._types_editor.fail(self.tr('Finish the current workflow edit before opening another pipeline'))
            return
        if editor._project != self._project:
            editor.reset(self._project)
        self._section = 'workflow'
        self.stateChanged.emit()
        if not editor._loaded or editor.identity != identity:
            editor._request('load', identity)

    @Slot()
    def open_schema_node_workflows(self) -> None:
        source = self._schema_editor
        identity = source.selectedNode
        if (not self.canManage or source.busy or not identity
                or identity in source.document.get('newTypes', {})
                or not any(row['identity'] == identity
                           for row in source.metadata.get('searchTypes', []))):
            return
        editor = self._workflow_editor
        if editor.busy or editor.dirty or editor.rulesEditor.busy or editor.rulesEditor.dirty:
            source.fail(self.tr('Finish the current workflow edit before opening another pipeline'))
            return
        if editor._project != self._project:
            editor.reset(self._project)
        editor.open_search_type(identity)
        self._section = 'workflow'
        self.stateChanged.emit()

    @Slot(QObject)
    def create_type_workflow(self, source: SearchTypesEditor) -> None:
        if (not self.canManage or source not in (self._types_editor, self._schema_type_editor)
                or source.busy or not source.canWrite or source._project != self._project):
            return
        if not source.identity or (source is self._schema_type_editor and source.dirty):
            source.fail(self.tr('Save the Search Type before creating its workflow'))
            return
        editor = self._workflow_editor
        if editor.busy or editor.dirty:
            source.fail(self.tr('Finish the current workflow edit before creating another pipeline'))
            return
        if editor._project != self._project:
            editor.reset(self._project)
        editor.new_document(source.identity, source.document.get('title') or source.identity)
        self._section = 'workflow'
        self.stateChanged.emit()
        if source is self._schema_type_editor:
            self._application.window_model.close_window(source.WINDOW_ID)

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._worker is not None

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error

    @Property('QVariantMap', notify=stateChanged)
    def draft(self) -> dict:
        return dict(self._draft)

    @Property(bool, notify=stateChanged)
    def dirty(self) -> bool:
        return (self._draft != self._original
                or self._members != self._original_members)

    @Property(int, notify=stateChanged)
    def memberCount(self) -> int:
        return len(self._members)

    @Slot()
    def open(self) -> None:
        if self.canManage:
            self._application.window_model.show_window('administration')
        else:
            self._application._notify(self.tr('Administration requires administrator access'))

    @Slot()
    def show_groups(self) -> None:
        self.select_section('groups')

    @Slot()
    def _user_document_saved(self) -> None:
        document = self._users_editor.document
        login = str(document.get('login') or '')
        row = next((row for row in self._catalog['users'] if row['login'] == login), None)
        if row is None:
            row = {'login': login}
            self._catalog['users'].append(row)
        row.update(displayName=self._users_editor.profile['displayName'],
                   retired=document.get('s_status') == 'retired')
        # The user save re-reads the full native membership catalog. Publish it
        # even when the Groups page has not been opened in this session.
        metadata = self._users_editor.metadata
        self._catalog['groups'] = copy.deepcopy(metadata['groupCatalog'])
        self._catalog['memberships'] = [
            {'login': member, 'login_group': group}
            for member, groups in metadata['groups'].items() for group in groups]
        counts = {}
        for member in self._catalog['memberships']:
            counts[member['login_group']] = counts.get(member['login_group'], 0) + 1
        if self.groups.rowCount():
            self.groups.replace(sorted(({
                'code': str(group['code']), 'name': str(group['login_group']),
                'description': str(group.get('description') or ''),
                'memberCount': counts.get(group['login_group'], 0),
            } for group in self._catalog['groups']), key=lambda group: group['name'].casefold()))
        self._publish_catalog()
        self.groupsChanged.emit()
        if self.dirty:
            self._rebuild_members()
        else:
            self._set_group(str(self._draft.get('code') or ''))

    @Slot()
    def _security_document_saved(self) -> None:
        editor = self._security_editor
        documents = editor.document.get('groups', {})
        for group in self._catalog['groups']:
            document = documents.get(group.get('code'))
            if document is None:
                continue
            # Publish committed permissions without replacing a membership
            # draft or starting a competing catalog read.
            for key, field in (('xml', 'access_rules'), ('accessLevel', 'access_level'),
                               ('project', 'project_code'), ('subGroups', 'sub_groups')):
                group[field] = document.get(key, '')
        self._publish_catalog()
        self.groupsChanged.emit()

    @Slot()
    def _project_document_saved(self) -> None:
        self._pending_metadata.add(self._project)
        self._refresh_pending_metadata()

    @Slot()
    def _schema_type_created(self) -> None:
        if self._types_editor._project == self._project:
            self._types_editor._catalog = copy.deepcopy(self._schema_type_editor.catalog)
            self._types_editor.stateChanged.emit()
        self._project_document_saved()

    @Slot(str, result=bool)
    def prepare_schema_node_deletion(self, identity: str) -> bool:
        if identity != self._schema_editor.selectedNode:
            return False
        types, workflow = self._types_editor, self._workflow_editor
        if (types.busy or (types.identity == identity and types.dirty)
                or workflow.busy or (workflow.document.get('searchType') == identity
                    and (workflow.dirty or workflow.rulesEditor.dirty or workflow.rulesEditor.busy))):
            self._schema_editor.fail(self.tr('Finish the Search Type and workflow edits before deleting this type'))
            return False
        return self._schema_editor.deletionEditor.open()

    @Slot()
    def _schema_type_deleted(self) -> None:
        identity = self._schema_editor.deletionEditor.identity
        types, workflow = self._types_editor, self._workflow_editor
        if types.identity == identity:
            types.reset(self._project)
        else:
            types._loaded = False
        if workflow.document.get('searchType') == identity:
            workflow.reset(self._project)
        else:
            workflow._loaded = False

    def _refresh_pending_metadata(self) -> None:
        if self.busy or self._closed or not self._pending_metadata:
            return
        from thlib import tactic_classes as tc
        from thlib.environment import env_inst

        code = self._pending_metadata.pop()
        project = (env_inst.projects or {}).get(code)
        if project is None:
            return
        info = copy.deepcopy(project.info)
        login = env_inst.get_current_login_object()

        def load_metadata():
            # Build a separate native object off-thread. The live project and
            # its already-open tab references are published on the Qt thread.
            fresh = tc.Project(info)
            if not fresh.query_search_types(force=True):
                raise ValueError('Saved, but project metadata could not be refreshed. Reload the project.')
            entries = self._application.navigation_model.build_project_entries(fresh, login)
            return fresh, entries

        def publish(result):
            fresh, entries = result
            self._application.apply_project_metadata(fresh, entries)

        self._run(load_metadata, publish, 'administration/metadata')

    @Slot(str, bool)
    def _visibility_changed(self, window_id: str, visible: bool) -> None:
        if window_id == 'administration' and not visible:
            self._users_editor.clear_password()
        if window_id == 'administration' and visible:
            if not self.canManage:
                self._application.window_model.close_window('administration')
                return
            if not self._project:
                self._project = getattr(self._application, 'current_project_code', '')
            self.select_section(self._section)

    @Slot()
    def _server_changed(self) -> None:
        key = (self._application.server_url, self._application.server_user)
        if key == self._server_key and self.canManage:
            self.stateChanged.emit()
            return
        self._server_key = key
        if not self.canManage:
            self._application.window_model.close_window('administration')
        self._pending_metadata.clear()
        self._project = ''
        for editor in self._editors.values():
            editor.reset()
        self._schema_type_editor.reset()
        self._application.window_model.close_window(self._schema_type_editor.WINDOW_ID)
        self._generation += 1
        self._release_worker(cancel=True)
        self._catalog = {'groups': [], 'memberships': [], 'users': []}
        self.groups.clear()
        self._set_group('')

    def _release_worker(self, cancel: bool = False) -> None:
        worker = self._worker
        if worker is not None:
            if self._worker_callbacks is not None:
                loaded, failed = self._worker_callbacks
                worker.result.disconnect(loaded)
                worker.error.disconnect(failed)
            if cancel:
                worker.cancel()
        self._worker = None
        self._worker_callbacks = None

    def _run(self, operation: Callable, completed: Callable,
             log_group: str = 'administration/security') -> None:
        from thlib.environment import env_inst
        if self.busy or self._closed or not self.canManage:
            return
        self._generation += 1
        generation = self._generation
        self._error = ''
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            self._error = self.tr('Server worker pool is unavailable')
            self.stateChanged.emit()
            return
        self._worker = worker

        def loaded(payload):
            if self._closed or generation != self._generation:
                return
            self._release_worker()
            completed(payload)
            self.stateChanged.emit()
            self._refresh_pending_metadata()

        def failed(error):
            if self._closed or generation != self._generation:
                return
            self._release_worker()
            payload, _worker = error
            self._error = str(payload.get('exception') or error)
            self.stateChanged.emit()
            if self._application.debug_log:
                self._application.debug_log.raise_error(
                    payload.get('exception') or self._error,
                    stacktrace=payload.get('stacktrace', ''),
                    group=log_group)
            self._refresh_pending_metadata()

        worker.result.connect(loaded, Qt.QueuedConnection)
        worker.error.connect(failed, Qt.QueuedConnection)
        self._worker_callbacks = (loaded, failed)
        self.stateChanged.emit()
        worker.start()

    @Slot()
    def reload(self) -> None:
        if not self.canManage or self.dirty:
            return
        from thlib import tactic_classes as tc
        from .security_store import query_security_groups
        self._run(lambda: tc.execute_procedure_serverside(
            query_security_groups, {}, project='sthpw'), self._loaded)

    def _loaded(self, payload: dict) -> None:
        self._catalog = payload
        counts = {}
        for item in payload['memberships']:
            key = item['login_group']
            counts.setdefault(key, set()).add(item['login'])
        self.groups.replace(sorted(({
            'code': str(row['code']), 'name': str(row['login_group']),
            'description': str(row.get('description') or ''),
            'memberCount': len(counts.get(row['login_group'], ())),
        } for row in payload['groups']), key=lambda row: row['name'].casefold()))
        self._publish_catalog()
        code = str(self._draft.get('code') or '')
        if not any(row['code'] == code for row in self.groups.records()):
            code = self.groups.get(0).get('code', '') if self.groups.rowCount() else ''
        self._set_group(code)
        self.groupsChanged.emit()

    def _publish_catalog(self) -> None:
        """Refresh both native membership directions on the owning UI thread."""
        from thlib.environment import env_inst
        from thlib.tactic_classes import LoginGroup
        groups = [LoginGroup(dict(row)) for row in self._catalog['groups']]
        memberships = [dict(row) for row in self._catalog['memberships']]
        by_name = {group.get_login_group(): group for group in groups}
        for login in (env_inst.get_all_logins() or {}).values():
            login.login_groups = groups
            login.login_in_groups = memberships
            for row in memberships:
                if row['login'] == login.get_login() and row['login_group'] in by_name:
                    by_name[row['login_group']].add_login_to_group(login)
        self._users._rebuild()

    def _set_group(self, code: str) -> None:
        self._draft = next((dict(row) for row in self.groups.records()
                            if row['code'] == code), {})
        self._original = dict(self._draft)
        name = self._draft.get('name')
        self._members = {row['login'] for row in self._catalog['memberships']
                         if row['login_group'] == name}
        self._original_members = set(self._members)
        self._rebuild_members()
        self.stateChanged.emit()

    @Slot(str)
    def select_group(self, code: str) -> None:
        if not self.busy and not self.dirty:
            self._set_group(code)

    @Slot()
    def new_group(self) -> None:
        if not self.canManage or self.busy or self.dirty:
            return
        self._set_group('')
        self._draft = {'code': '', 'name': '', 'description': ''}
        self.stateChanged.emit()

    @Slot(str, str)
    def set_field(self, field: str, value: str) -> None:
        if (self.busy or not self.canManage or field not in {'name', 'description'}
                or (field == 'name' and self._draft.get('code'))):
            return
        self._draft[field] = value
        self.stateChanged.emit()

    @Slot(str)
    def set_user_query(self, value: str) -> None:
        self._query = value.casefold().strip()
        self._rebuild_members()

    def _rebuild_members(self) -> None:
        identities = {row['login']: row for row in self._users.users.records()}
        self.members.replace(sorted(({
            **row, 'member': row['login'] in self._members,
            'initials': user_initials(row['displayName'], row['login']),
            'avatarColor': user_avatar_color(row['login']),
            'avatarUrl': identities.get(row['login'], {}).get('avatarUrl', ''),
            'retired': bool(row.get('retired')),
        } for row in self._catalog['users'] if not self._query
            or self._query in (row['login'] + ' ' + row['displayName']).casefold()),
            key=lambda row: row['displayName'].casefold()))

    @Slot(str, bool)
    def set_member(self, login: str, selected: bool) -> None:
        if self.busy or not self.canManage or not self._draft:
            return
        if login not in {row['login'] for row in self._catalog['users']}:
            return
        if selected:
            self._members.add(login)
        else:
            self._members.discard(login)
        self._rebuild_members()
        self.stateChanged.emit()

    @Slot()
    def discard(self) -> None:
        if not self.busy:
            self._set_group(str(self._original.get('code') or ''))

    @Slot()
    def save(self) -> None:
        if not self.canManage or self.busy or not self.dirty:
            return
        name = str(self._draft.get('name') or '').strip()
        if not name:
            self._error = self.tr('Enter a group identifier')
            self.stateChanged.emit()
            return
        from thlib import tactic_classes as tc, server_cache
        from .security_store import query_security_groups, save_security_group
        arguments = {
            'group_code': self._draft.get('code', ''), 'login_group': name,
            'description': self._draft.get('description', ''),
            'add_members': sorted(self._members - self._original_members),
            'remove_members': sorted(self._original_members - self._members),
        }

        def operation():
            result = tc.execute_procedure_serverside(
                save_security_group, arguments, project='sthpw')
            server_cache.invalidate_domains(('reference',), 'sthpw')
            return result, tc.execute_procedure_serverside(
                query_security_groups, {}, project='sthpw')

        def saved(result):
            identity, catalog = result
            self._draft['code'] = identity['code']
            self._loaded(catalog)

        self._run(operation, saved)

    def shutdown(self) -> None:
        self._closed = True
        self._generation += 1
        self._release_worker(cancel=True)
        for editor in self._editors.values():
            editor.shutdown()
        self._schema_type_editor.shutdown()
