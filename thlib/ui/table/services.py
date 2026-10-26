"""Table service actions keep captured sessions and existing command owners."""

from PySide6.QtCore import QObject, Property, Signal, Slot, Qt


def preference_request(key, value=None, expected_revision=None, action='save'):
    import hashlib
    import json
    from pyasm.biz import PrefSetting
    from pyasm.command import Command
    from pyasm.search import Search
    from tactic.ui.table import SetPreferenceCmd

    record = PrefSetting.get_by_key(key, use_cache=False)
    current = record.get_value('value') if record else ''
    revision = hashlib.sha256(json.dumps(record.get_data() if record else None,
                              sort_keys=True, default=str).encode()).hexdigest()
    if action == 'check':
        return {'state': 'saved' if current == value else 'unchanged' if revision == expected_revision else 'conflict'}
    if action != 'save' or not expected_revision:
        raise ValueError('Reload the preference before saving')
    sql = Search('sthpw/pref_setting').get_sql()
    lock = getattr(sql.get_database_impl(), 'lock_collection_table', None)
    if lock:
        lock(sql, 'pref_setting')
    elif sql.get_database_type() == 'PostgreSQL':
        sql.do_update('LOCK TABLE "pref_setting" IN EXCLUSIVE MODE')
    else:
        raise ValueError('Preference revisions require a transactional database lock')
    record = PrefSetting.get_by_key(key, use_cache=False)
    revision = hashlib.sha256(json.dumps(record.get_data() if record else None,
                              sort_keys=True, default=str).encode()).hexdigest()
    if revision != expected_revision:
        raise ValueError('Preference changed. Reload before saving.')
    Command.execute_cmd(SetPreferenceCmd(key=key, value=value))
    return {'state': 'saved'}


def object_status_request(search_key, action, expected_revision):
    import hashlib
    import json
    from pyasm.search import Search
    if action not in ('retire', 'reactivate'):
        raise ValueError('Invalid object action')
    obj = Search.get_by_search_key(search_key)
    if obj is None:
        raise LookupError('Object is no longer available')
    sql = obj.get_sql()
    lock = getattr(sql.get_database_impl(), 'lock_collection_table', None)
    if lock:
        lock(sql, obj.get_table())
    elif sql.get_database_type() == 'PostgreSQL':
        sql.do_update('LOCK TABLE "%s" IN EXCLUSIVE MODE' % obj.get_table().replace('"', '""'))
    else:
        raise ValueError('Object revisions require a transactional database lock')
    obj = Search.get_by_search_key(search_key)
    revision = hashlib.sha256(json.dumps(obj.get_data(), sort_keys=True, default=str).encode()).hexdigest()
    if revision != expected_revision:
        raise ValueError('Object changed. Reload before saving.')
    if action == 'retire':
        obj.retire()
    else:
        obj.reactivate()
    return {'search_key': search_key}


class TableServicesController(QObject):
    stateChanged = Signal()
    documentChanged = Signal()
    preferenceOpened = Signal(QObject)
    preferenceClosed = Signal()
    completed = Signal(str)
    templateOpened = Signal(str)
    objectActionOpened = Signal(str, 'QVariantMap')
    scriptConfirmation = Signal(str)
    scriptCommands = Signal('QVariantList')
    scriptProgress = Signal(str, str)

    connectionRemovalOpened = Signal()
    connectionRemovalClosed = Signal()
    nestedChanged = Signal()

    def __init__(self, application, parent=None, *, administration=None, tasks=None, scripts=None, links=None):
        super().__init__(parent)
        self._application = application
        self._administration, self._tasks, self._scripts = administration, tasks, scripts
        self._generation = 0
        self._workers = set()
        self._busy = False
        self._error = ''
        self._uncertain = False
        self._preference = {}
        self._connection_removal = None
        self._server = None
        self._script_session = None
        self._links = links
        self._document = {}
        self._document_generation = 0
        application.window_model.windowVisibilityChanged.connect(self._document_visibility)
        self._nested_scopes = {}
        self._nested_revision = 0
        from .custom_layout import CustomLayoutController
        self._layout = CustomLayoutController(self)
        self._workspace_layout = CustomLayoutController(self, workspace=True)
        from .file_append import SnapshotAppendController
        self._append = SnapshotAppendController(application, self)
        self._append.changed.connect(self.stateChanged)
        self._append.completed.connect(self.completed)
        from .file_checkout import SnapshotCheckoutController
        self._checkout = SnapshotCheckoutController(application, self)
        self._checkout.changed.connect(self.stateChanged)
        from .dependencies import DependencyViewerController
        self._dependencies = DependencyViewerController(self, self)
        from .parent_group import ParentGroupController
        self._parent_groups = ParentGroupController(self, self)
        application.results_view_changed.connect(self._prune_nested)
        from thlib.ui.source_editor import SourceEditorService
        self._source_editor = SourceEditorService(self)
        self.scriptProgress.connect(self._script_progress, Qt.QueuedConnection)
        application.signing_out.connect(self.shutdown)
        application.project_changed.connect(self.shutdown)

    def _document_visibility(self, window_id, visible):
        if window_id == 'table_document' and not visible:
            self._document_generation += 1
            self._layout.close()

    @Property(QObject, constant=True)
    def customLayout(self):
        return self._layout

    @Property(QObject, constant=True)
    def workspaceLayout(self):
        return self._workspace_layout

    @Property(QObject, constant=True)
    def dependencyViewer(self):
        return self._dependencies

    @Property(QObject, constant=True)
    def parentGroups(self):
        return self._parent_groups

    @Property(QObject, constant=True)
    def appendEditor(self):
        return self._append

    @Slot(str, 'QVariantMap')
    def open_append(self, node_id, cell):
        node = self._application._node_for_any(node_id)
        if node is not None:
            self._append.open(str(cell.get('targetSearchKey') or node.search_key),
                str(cell.get('projectCode') or self._application._current_project_code))

    @Property(QObject, constant=True)
    def checkoutEditor(self):
        return self._checkout

    @Slot(str, 'QVariantMap')
    def open_checkout(self, node_id, cell):
        node = self._application._node_for_any(node_id)
        if node is not None:
            self._checkout.open(str(cell.get('targetSearchKey') or node.search_key),
                str(cell.get('projectCode') or self._application._current_project_code))

    @Slot(str, 'QVariantMap')
    @Slot(str, 'QVariantMap', 'QVariantList')
    def open_ingest(self, node_id, cell, values=None):
        if self.busy or not self._application.can_manage_tools:
            return
        node = self._application._node_for_any(node_id)
        if node is None:
            return
        from pathlib import Path
        import uuid
        from PySide6.QtCore import QUrl
        from PySide6.QtWidgets import QFileDialog
        from thlib import tactic_classes as tc
        from .requests import ingest_drop_files
        raw_values = list(values or [])
        if not raw_values:
            raw_values, _ = QFileDialog.getOpenFileNames(None, self.tr('Choose files'))
        if not raw_values:
            return
        target_key = str(cell.get('targetSearchKey') or node.search_key)
        project = str(cell.get('projectCode') or self._application._current_project_code)
        try:
            server = tc.server_start(project=project)
        except PermissionError as error:
            self.report_error(str(error))
            return
        upload_dir = 'ingest_' + uuid.uuid4().hex
        def operation():
            names = []
            for item in raw_values:
                url = item if isinstance(item, QUrl) else QUrl(str(item))
                source = url.toLocalFile() if url.isLocalFile() else str(item)
                path = Path(source).resolve(strict=True)
                if not path.is_file():
                    raise ValueError('Choose files, not directories')
                server.upload_file(str(path), upload_subdir=upload_dir)
                names.append(path.name)
            return tc.execute_procedure_serverside(ingest_drop_files, dict(
                search_key=target_key,
                files=names,
                upload_directory=upload_dir,
                transfer_mode=str(cell.get('transferMode') or 'free_copy'),
                checkin_mode=str(cell.get('checkinMode') or 'default'),
                context=str(cell.get('context') or 'publish'),
                subcontext_mode=str(cell.get('subcontextMode') or '{none}'),
                subcontext=str(cell.get('subcontext') or ''),
            ), project=project, server=server)
        def saved(result):
            self._application._notify(f"Ingested {result.get('file_count', 0)} file(s) into [{result.get('code', '')}]")
            self.completed.emit(target_key)
        self._run(operation, saved)

    @Property(int, notify=nestedChanged)
    def nestedRevision(self):
        return self._nested_revision

    def _prune_nested(self):
        tabs = {id(tab) for section in self._application._sessions.values() for tab in section.tabs}
        for key, page in tuple(self._workspace_layout.pages.items()):
            if id(page['tab']) not in tabs:
                self._workspace_layout.drop_page(key)
        if not self._workspace_layout.pages and id(self._workspace_layout.tab) not in tabs:
            self._workspace_layout.close()
        if self._document.get('layoutNodes') is not None and (
                id(self._layout.tab) not in tabs or self._layout.tab is not self._application._current_tab()):
            self._layout.close()
            self._document_generation += 1
            self._document = {}
            self.documentChanged.emit()
            self._application.window_model.close_window('table_document')
        for key, scope in tuple(self._nested_scopes.items()):
            if id(scope.tab) not in tabs:
                scope.shutdown()
                scope.deleteLater()
                del self._nested_scopes[key]
            elif self.scope_visible(scope) and scope._pending_reload:
                scope._reload_timer.start(0)
        self._nested_revision += 1
        self.nestedChanged.emit()

    def refresh_time_cells(self):
        for scope in self._nested_scopes.values():
            if any(cell.get('timeDays') for row in scope.model['rows'] for cell in row['cells'].values()):
                scope._pending_reload = True
                if scope.open and scope.tab is self._application._current_tab():
                    scope._reload_timer.start(0)

    def _owner_scope(self, identity):
        return next((scope for scope in self._nested_scopes.values()
            if scope.tab is self._application._current_tab() and scope.node_for(identity)), None)

    def scope_visible(self, scope):
        seen = set()
        while scope is not None:
            if id(scope) in seen or not scope.open or scope.tab is not self._application._current_tab():
                return False
            layout_owner = getattr(scope, 'layout_owner', None)
            generation = layout_owner.document_generation if layout_owner else self._document_generation
            if getattr(scope, 'document_generation', generation) != generation:
                return False
            seen.add(id(scope))
            owner = self._owner_scope(scope.owner_node_id)
            if owner is None and scope.owner_node_id.startswith('nested:'):
                return False
            scope = owner
        return True

    def scope_for(self, identity):
        scope = self._owner_scope(identity)
        return scope if scope and self.scope_visible(scope) else None

    def node_for(self, identity):
        scope = self.scope_for(identity)
        return scope.node_for(identity) if scope else None

    @Slot(str, int, result=QObject)
    def nested_row(self, node_id, revision=0):
        return next((scope for scope in self._nested_scopes.values()
            if scope.owner_node_id == node_id and self.scope_visible(scope)), None)

    def _nested_changed(self):
        for scope in self._nested_scopes.values():
            if not self.scope_visible(scope):
                scope.suspend()
            elif scope._pending_reload:
                scope._reload_timer.start(0)
        self._nested_revision += 1
        self.nestedChanged.emit()

    @Slot(str, 'QVariantMap')
    def toggle_nested(self, node_id, cell):
        from .nested import NestedTableController
        if not isinstance(cell.get('nestedTable'), dict):
            return
        descriptor = cell['nestedTable']
        ancestor = self.scope_for(node_id)
        def identity(value):
            return (value.get('projectCode') or self._application._current_project_code,
                value.get('searchType') or '', value.get('view') or 'table',
                value.get('parentKey') or '', value.get('expression') or '')
        while ancestor is not None:
            if identity(ancestor.descriptor) == identity(descriptor):
                self.report_error(self.tr('This nested table would repeat an ancestor scope'))
                return
            ancestor = self._owner_scope(ancestor.owner_node_id)
        tab = self._application._current_tab()
        key = (id(tab), node_id, str(cell.get('columnName') or ''))
        scope = self._nested_scopes.get(key)
        if scope and scope.descriptor != descriptor:
            scope.shutdown()
            scope.deleteLater()
            del self._nested_scopes[key]
            scope = None
        if scope is None:
            scope = NestedTableController(self, node_id, descriptor)
            scope.open = False
            self._nested_scopes[key] = scope
        opening = not scope.open
        for sibling in self._nested_scopes.values():
            if sibling.tab is tab and sibling.owner_node_id == node_id:
                sibling.open = False
        scope.open = opening
        self._nested_changed()
        if opening and (not scope.model.get('loaded') or scope._pending_reload):
            scope.reload()

    @Slot(QObject)
    def close_nested(self, scope):
        if scope in self._nested_scopes.values():
            scope.open = False
            self._nested_changed()

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._busy or self._script_session is not None or self._append.busy or self._checkout.busy

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Property(bool, notify=stateChanged)
    def uncertain(self):
        return self._uncertain

    @Property(QObject, constant=True)
    def sourceEditor(self):
        return self._source_editor

    @Property('QVariantMap', notify=documentChanged)
    def document(self):
        return dict(self._document)

    @Property('QVariantMap', notify=stateChanged)
    def preference(self):
        return dict(self._preference)

    @Slot(QObject, 'QVariantMap')
    def open_preference(self, anchor, cell):
        if self._busy or self._preference:
            return
        from thlib import tactic_classes as tc
        if not cell.get('preferenceKey') or not cell.get('expectedRevision'):
            return
        try:
            self._server = tc.server_start(project=self._application._current_project_code)
        except PermissionError as error:
            self._application._notify(str(error))
            return
        self._preference = dict(cell)
        self._uncertain, self._error = False, ''
        self.stateChanged.emit()
        self.preferenceOpened.emit(anchor)

    @Slot()
    def cancel_preference(self):
        if self._busy:
            return
        self._preference = {}
        self._error, self._uncertain = '', False
        self._server = None
        self.stateChanged.emit()
        self.preferenceClosed.emit()

    @Slot(str)
    @Slot(str, bool)
    def save_preference(self, value, check=False):
        if not self._preference or self._busy or self._uncertain and not check:
            return
        from thlib import tactic_classes as tc
        cell, server = dict(self._preference), self._server
        def operation():
            return tc.execute_procedure_serverside(preference_request,
                dict(key=cell['preferenceKey'], value=value, expected_revision=cell['expectedRevision'],
                     action='check' if check else 'save'), project=server.get_project(), server=server)
        def saved(result):
            if result.get('state') != 'saved':
                self._uncertain = True
                self._error = self.tr('Preference changed. Reload before saving.')
            else:
                self.cancel_preference()
                self.completed.emit(str(cell.get('targetSearchKey') or ''))
        self._run(operation, saved)

    @Slot(str, 'QVariantMap')
    def request_connection_removal(self, node_id: str, cell: dict) -> None:
        if self.busy or not self._application.can_manage_tools:
            return
        node = self._application._node_for_any(node_id)
        if node is None:
            return
        from thlib import tactic_classes as tc
        try:
            scope = self.scope_for(node_id)
            project = (scope.descriptor.get('projectCode') if scope else '') or self._application._current_project_code
            server = tc.server_start(project=project)
        except PermissionError as error:
            self.report_error(str(error))
            return
        self._connection_removal = dict(server=server, tab=self._application._current_tab(),
            values=dict(parent_key=cell.get('targetSearchKey') or node.search_key,
                connection_key=cell.get('connectionKey'), expected_revision=cell.get('expectedRevision'),
                direction=cell.get('direction') or 'dst'))
        self.connectionRemovalOpened.emit()

    @Slot(bool)
    def confirm_connection_removal(self, accepted: bool) -> None:
        if self.busy:
            return
        request, self._connection_removal = self._connection_removal, None
        self.connectionRemovalClosed.emit()
        if not accepted or request is None:
            return
        if request['tab'] is not self._application._current_tab():
            self.report_error(self.tr('The source tab changed. Table action results were not opened.'))
            return
        from thlib import tactic_classes as tc
        from .requests import remove_connection
        server, values = request['server'], request['values']
        def removed(result):
            if result.get('state') != 'removed':
                raise ValueError('Could not confirm removal of the connection')
        self._run(lambda: tc.execute_procedure_serverside(remove_connection, values,
            project=server.get_project(), server=server), removed,
            settled=lambda: self.completed.emit(str(values['parent_key'])))

    @Slot(str, 'QVariantMap')
    def request_object_action(self, action, cell):
        if not self._busy and action in ('retire', 'reactivate'):
            self.objectActionOpened.emit(action, dict(cell))

    @Slot(str, 'QVariantMap')
    def change_object_status(self, action, cell):
        if self._busy or action not in ('retire', 'reactivate'):
            return
        from thlib import tactic_classes as tc
        try:
            server = tc.server_start(project=self._application._current_project_code)
        except PermissionError as error:
            self.report_error(str(error))
            return
        values = dict(search_key=cell['targetSearchKey'], action=action,
                      expected_revision=cell['expectedRevision'])
        self._run(lambda: tc.execute_procedure_serverside(object_status_request, values,
                  project=server.get_project(), server=server),
                  lambda result: self.completed.emit(str(result['search_key'])))

    @Slot(str)
    def request_template(self, project_code):
        if not self._busy and self._application.can_manage_tools:
            self.templateOpened.emit(project_code)

    @Slot(str)
    def export_template(self, project_code):
        if self._busy or not self._application.can_manage_tools:
            return
        from thlib import tactic_classes as tc
        try:
            server = tc.server_start(project='admin')
        except PermissionError as error:
            self.report_error(str(error))
            return
        self._run(lambda: server.execute_cmd('tactic.command.ProjectTemplateCreatorCmd',
                  args={'project_code': project_code}),
                  lambda result: self._application._notify(self.tr('Template archive created')))

    @Slot(str)
    def test_notification(self, search_key):
        if self._busy or not self._application.can_manage_tools:
            return
        from thlib import tactic_classes as tc
        try:
            server = tc.server_start(project=self._application._current_project_code)
        except PermissionError as error:
            self.report_error(str(error))
            return
        def operation():
            record = server.get_by_search_key(search_key)
            return server.execute_cmd('tactic.command.NotificationTestCmd', args={'sobject_dict': record})
        self._run(operation, lambda result: self._application._notify(str(result.get('description') or '')))

    @Slot(str, 'QVariantMap', 'QVariantList')
    def open_links(self, node_id, cell, keys):
        if self.busy or self._links is None:
            return
        if self._links._dirty or self._links._busy or self._links._uncertain:
            self.report_error(self.tr('Apply or discard unsaved changes first'))
            return
        from thlib.environment import env_inst
        node = self._application._node_for_any(node_id)
        project = self._application._current_project_code
        if node is None or node.source is None or node.search_key != cell.get('targetSearchKey'):
            self.report_error(self.tr('The configured table target is unavailable'))
            return
        stype = env_inst.get_stype_by_code(str(cell.get('acceptedType') or ''),project_code=project)
        if stype is None:
            self.report_error(self.tr('Search Type is not available for this editor'))
            return
        self._application._sobject_link_request = dict(_prepared=True,stype=stype,parent_sobject=node.source,
            project_code=project,relation=cell['relation'],table_drop=dict(search_type=node.search_key.split('?')[0],
            view=cell['tableView'],column=cell['columnName'],parent_key=node.search_key,
            expected_revision=cell['expectedRevision'],links=cell['links']))
        self._application.open_window('link_sobjects')
        if keys:
            token = self._links._session_token
            def stage():
                if self._links._busy:
                    return
                self._links.stateChanged.disconnect(stage)
                if token == self._links._session_token:
                    self._links.stage_dropped(keys)
            self._links.stateChanged.connect(stage)
            stage()

    @Slot(str, str, 'QVariantMap')
    def open_task_action(self, action, node_id, cell):
        if self.busy or self._tasks is None:
            return
        if action == 'table-schedule':
            login = str(cell.get('actionLogin') or cell.get('login') or '')
            if login:
                self._tasks.open_for_user(login)
                self._tasks.set_view_mode('gantt')
                return
            if str(cell.get('actionScope') or cell.get('scope') or '') == 'project':
                self._tasks.use_project()
                self._tasks._show_workspace_surface('browser')
                self._tasks.set_view_mode('gantt')
                return
            parent_keys = [str(item) for item in (cell.get('actionParentKeys') or []) if item]
            if len(parent_keys) > 1:
                self._tasks.use_related_objects(parent_keys)
                self._tasks._show_workspace_surface('browser')
                self._tasks.set_view_mode('gantt')
                return
        key = str(cell.get('targetSearchKey') or '')
        if not key:
            return
        process = str(cell.get('actionProcess') or cell.get('process') or '')
        code = str(cell.get('actionTaskCode') or cell.get('taskCode') or '')
        if not code and str(cell.get('actionTaskKey') or '').startswith('sthpw/task?'):
            from urllib.parse import urlsplit, parse_qs
            code = parse_qs(urlsplit(cell['actionTaskKey']).query).get('code', [''])[0]
        self._tasks.open_object_context(key, code, process)
        if action == 'table-schedule':
            self._tasks.set_view_mode('gantt')
        if action == 'work':
            self._application.invoke_table_widget_action('checkin', node_id, cell)
        elif action == 'add-task':
            generation = self._generation
            def create():
                if self._tasks.advancedBusy:
                    return
                self._tasks.advancedChanged.disconnect(create)
                if generation == self._generation and self._tasks._advanced_target_key == key:
                    self._tasks.create_advanced_task_draft()
            self._tasks.advancedChanged.connect(create)
            create()

    @Slot(str)
    @Slot(str, str)
    def insert_record(self, view, operation=''):
        app = self._application
        if self.busy or not app.can_manage_tools:
            return
        stype = app._active_stype()
        if stype is None:
            return
        from thlib.ui.sobject_editor import open_sobject_editor
        open_sobject_editor(app, dict(mode='insert', view=view or 'insert', operation=operation,
            stype=stype, sobject=None, parent_sobject=None, _prepared=True))

    @Slot(str, 'QVariantMap')
    def run_script(self, node_id, cell):
        if self.busy or self._preference:
            return
        from thlib import tactic_classes as tc
        from .scripts import TableScriptRunner
        application = self._application
        node = application._node_for_any(node_id)
        tab = application._current_tab()
        if node is None or node.source is None or tab is None:
            return
        options = dict(cell.get('displayOptions') or {})
        scope = self.scope_for(node_id)
        selected_ids = [identity for identity, item in scope._nodes.items() if item.search_key in scope.model['selected']] if scope else application.selected_result_node_ids
        source_key = node.search_key
        target_key = str(cell.get('targetSearchKey') or source_key)
        context = dict(searchKey=target_key, searchType=target_key.split('?')[0],
                       record=dict(node.source.get_info()), project=(scope.descriptor.get('projectCode') if scope else '') or application._current_project_code,
                       records={selected.search_key: {'code': selected.source.get_value('code')}
                                for identity in selected_ids
                                if (selected := application._node_for_any(identity)) is not None and selected.source is not None},
                       column=cell.get('columnName') or '', view=cell.get('layoutView') or (scope.descriptor.get('view') if scope else tab.table_view),
                       searchKeys=[selected.search_key for identity in selected_ids
                                   if (selected := application._node_for_any(identity)) is not None and selected.source is not None])
        try:
            server = tc.server_start(project=context['project'])
        except PermissionError as error:
            self.report_error(str(error))
            return
        runner = TableScriptRunner(server, context, self.scriptProgress.emit)
        session = dict(runner=runner, source=None, tab=tab, node_id=node_id)
        self._script_session = session
        def operation():
            if target_key != source_key:
                record = server.get_by_search_key(target_key)
                if not record:
                    raise ValueError('The configured table target is unavailable')
                runner.context['record'] = record
            source = options.get('cbjs_action') or options.get('javascript')
            if not source and cell.get('scriptKey'):
                record = server.get_by_search_key(cell['scriptKey'])
                if not record:
                    raise ValueError('Script is no longer available')
                language = str(record.get('language') or 'javascript').lower()
                if language not in ('javascript', 'js'):
                    raise ValueError('Table button scripts must use JavaScript')
                source = record.get('script')
            if not source:
                raise ValueError('No script defined for this button')
            session['source'] = str(source)
            return runner.run(session['source'])
        self._run(operation, self._script_result)

    @Slot(bool)
    def confirm_script(self, accepted):
        session = self._script_session
        if not session or self._busy or not session.get('confirmation'):
            return
        confirmation = dict(message=session.pop('confirmation'), accepted=accepted)
        self._run(lambda: session['runner'].run(session['source'], confirmation), self._script_result)

    def _script_result(self, result):
        session = self._script_session
        if not session:
            return
        if session['tab'] is not self._application._current_tab():
            self.cancel_script()
            self._application._notify(self.tr('The source tab changed. Table action results were not opened.'))
            return
        if not isinstance(result, dict) or not isinstance(result.get('calls'), int):
            raise ValueError('Invalid table action result')
        if 'confirmation' in result:
            if result['calls'] or session.get('confirmed'):
                raise ValueError('A table action cannot replay server calls for confirmation')
            session['confirmation'] = str(result['confirmation'])
            session['confirmed'] = True
            self.scriptConfirmation.emit(session['confirmation'])
            return
        commands = result.get('commands')
        if not isinstance(commands, list):
            raise ValueError('Invalid table action commands')
        self.scriptCommands.emit(commands)
        self._script_session = None

    @Slot(str, str)
    def _script_progress(self, title, detail):
        if self._script_session:
            self._application._notify(' '.join(part for part in (title, detail) if part))

    @Slot()
    def cancel_script(self):
        if self._script_session:
            self._script_session['runner'].cancel()
            self._script_session = None
        self.stateChanged.emit()

    @Slot('QVariantMap')
    def open_port(self, command):
        try:
            self._open_port(dict(command))
        except (ValueError, KeyError, TypeError, PermissionError) as error:
            self.report_error(str(error))

    def _open_port(self, command):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        app = self._application
        session = self._script_session
        if not session or session['tab'] is not app._current_tab():
            raise ValueError('The source tab changed. Table action results were not opened.')
        kind = command['type']
        options = command.get('options') or {}
        if kind == 'refresh':
            app.refresh_current()
        elif kind in ('message', 'log'):
            app._notify(str(command.get('text') or ''))
        elif kind == 'url':
            url = QUrl(str(command.get('url') or ''))
            if url.isRelative():
                url = QUrl(app.server_url).resolved(url)
            if url.scheme().lower() not in ('http', 'https', 'mailto'):
                raise ValueError('Unsupported table link')
            if not QDesktopServices.openUrl(url):
                raise ValueError('Could not open table link')
        elif kind == 'schedule':
            self._tasks.open_for_user(str(options.get('login') or ''))
        elif kind == 'notes':
            self._tasks.open_notes(str(options.get('search_key') or ''),
                                   str(options.get('process') or options.get('context') or 'publish'))
        elif kind in ('security-summary','custom-layout'):
            from thlib import tactic_classes as tc
            from thlib.ui.table.requests import read_group_summary, read_custom_layout
            server = tc.server_start(project=session['runner'].context['project'])
            self._document_generation += 1
            document_generation = self._document_generation
            def show_document(result):
                if session['tab'] is not app._current_tab() or document_generation != self._document_generation:
                    return
                self._document = dict(result, title=command.get('title') or result.get('title') or 'Custom Layout',
                    translateTitle=not bool(command.get('title')), nodeId=session['node_id'])
                if result.get('layoutNodes') is not None:
                    self._layout.open(session['tab'], session['runner'].context, command.get('tabKey') or '')
                else:
                    self._layout.close()
                self.documentChanged.emit()
                self.stateChanged.emit()
                app.open_window('table_document')
            procedure = read_group_summary if kind == 'security-summary' else read_custom_layout
            arguments = dict(search_key=options.get('search_key') or session['runner'].context['searchKey'])
            if kind == 'custom-layout':
                arguments['view'] = options.get('view') or ''
            self._run(lambda: tc.execute_procedure_serverside(procedure,arguments,
                project=server.get_project(),server=server),show_document)
        elif kind == 'edit':
            from thlib.environment import env_inst
            node = app._node_for_any(session['node_id'])
            key = str(options.get('search_key') or '')
            search_type = str(options.get('search_type') or key.split('?')[0])
            stype = env_inst.get_stype_by_code(search_type, project_code=session['runner'].context['project'])
            if stype is None:
                raise ValueError('Search Type is not available for this editor')
            def open_editor(source):
                if session['tab'] is not app._current_tab():
                    return
                from thlib.ui.sobject_editor import open_sobject_editor
                open_sobject_editor(app, dict(mode='edit' if key else 'insert',
                    view=options.get('view') or ('edit' if key else 'insert'),
                    ignore=options.get('ignore') or '', stype=stype,
                    sobject=source, parent_sobject=None, _prepared=True))
            if key and (node is None or node.search_key != key):
                from thlib import tactic_classes as tc
                server = tc.server_start(project=session['runner'].context['project'])
                project = env_inst.projects[session['runner'].context['project']]
                def loaded(record):
                    if not record:
                        raise ValueError('The configured table target is unavailable')
                    open_editor(tc.SObject(record, project))
                self._run(lambda: server.get_by_search_key(key),loaded)
            else:
                open_editor(node.source if key else None)
        elif kind in ('users', 'groups', 'workflow', 'schema'):
            if self._administration is None or self._administration.projectLocked:
                raise ValueError('Apply or discard unsaved changes first')
            node = app._node_for_any(session['node_id'])
            identity = ''
            if kind in ('users', 'groups', 'workflow'):
                if node is None or node.source is None or options.get('search_key') != node.search_key:
                    raise ValueError('The configured table target is unavailable')
                identity = node.source.get_value('login' if kind == 'users' else 'code')
            self._administration.select_section(kind)
            self._administration.open()
            if identity:
                if kind == 'groups':
                    self._administration.focus_group(identity)
                else:
                    editor = self._administration.usersEditor if kind == 'users' else self._administration.workflowEditor
                    editor.focus(identity)
        elif kind == 'script':
            path = str(options.get('script_path') or '').strip('/')
            if not path or self._scripts is None:
                raise ValueError('Script is no longer available')
            app.open_window('script_editor')
            generation = self._generation
            def select():
                if generation != self._generation:
                    self._scripts.stateChanged.disconnect(select)
                    return
                if not self._scripts.loaded:
                    return
                self._scripts.stateChanged.disconnect(select)
                record = next((row for row in self._scripts._scripts
                    if ('%s/%s' % (row.get('folder') or '', row.get('title') or '')).strip('/') == path), None)
                if record:
                    self._scripts.script(record['token'])
                else:
                    self.report_error('Script is no longer available')
            self._scripts.stateChanged.connect(select)
            if self._scripts.loaded:
                select()
            else:
                self._scripts.load()
        else:
            raise ValueError('Unsupported table window: ' + kind)

    @Slot(str)
    def open_link(self, href):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        url = QUrl(str(href))
        if url.isRelative():
            url = QUrl(self._application.server_url).resolved(url)
        if url.scheme().lower() not in ('http','https','mailto') or not QDesktopServices.openUrl(url):
            self.report_error(self.tr('Could not open table link'))

    @Slot(str)
    def report_error(self, message):
        self._error = str(message)
        self._application._notify(self._error)
        self.stateChanged.emit()

    def _run(self, operation, accept, *, settled=None):
        from thlib.environment import env_inst
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            self._error = self.tr('Server worker is unavailable')
            self.cancel_script()
            self.stateChanged.emit()
            return
        generation = self._generation
        self._workers.add(worker)
        self._busy, self._error = True, ''
        def loaded(result):
            if generation != self._generation:
                return
            self._busy = False
            try:
                accept(result)
            except (ValueError, TypeError, KeyError, PermissionError) as error:
                self.cancel_script()
                self.report_error(str(error))
            if settled:
                settled()
            self.stateChanged.emit()
        def failed(error):
            if generation != self._generation:
                return
            self._busy = False
            self._uncertain = bool(self._preference)
            self.cancel_script()
            payload = error[0]
            if self._application.debug_log:
                self._application.debug_log.raise_error(payload.get('exception') or error,
                    stacktrace=payload.get('stacktrace', ''), group='table/actions')
            self._error = str(payload.get('exception') or error)
            self._application._notify(self._error)
            if settled:
                settled()
            self.stateChanged.emit()
        worker.result.connect(loaded, Qt.QueuedConnection)
        worker.error.connect(failed, Qt.QueuedConnection)
        worker.finished.connect(lambda: self._workers.discard(worker))
        self.stateChanged.emit()
        worker.start()

    @Slot()
    def shutdown(self):
        self._layout.close()
        self._workspace_layout.close()
        self._connection_removal = None
        self.connectionRemovalClosed.emit()
        self._append.shutdown()
        self._checkout.shutdown()
        self._dependencies.shutdown()
        self._parent_groups.shutdown()
        for scope in self._nested_scopes.values():
            scope.shutdown()
            scope.deleteLater()
        self._nested_scopes.clear()
        self._nested_revision += 1
        self.nestedChanged.emit()
        self._generation += 1
        self._document = {}
        self.documentChanged.emit()
        self._application.window_model.close_window('table_document')
        self.cancel_script()
        for worker in self._workers:
            worker.cancel()
        self._busy = False
        self.cancel_preference()
