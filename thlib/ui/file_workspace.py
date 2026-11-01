"""Separate file-project workspace; QML never performs disk or server work."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import threading
import time
import traceback
import uuid
from datetime import datetime

from PySide6.QtCore import QTimer, QCoreApplication, QObject, Property, Qt, QUrl, Signal, Slot

from thlib.side.client.tactic_client_lib.file_transfer import FileTransferClient, digest_file
from thlib.side.client.tactic_client_lib.file_workspace import reconcile_workspace, local_page, local_browse


SELECTION_FIELDS=('selected','selection_ids','selection_scope','selection_records','focus_id','anchor_id','context_row','file_focus','files_selection')


VIEW_PRESETS = [
    {'id':'files','title':'Files','kind':'files','source':'selection','icon':'file'},
    {'id':'pending','title':'Pending','kind':'changes','state':'pending','states':['pending','shelved'],'icon':'schedule'},
    {'id':'submitted','title':'Submitted','kind':'changes','state':'submitted','icon':'check-circle'},
    {'id':'history','title':'History','kind':'history','icon':'history'},
    {'id':'shelved','title':'Shelved','kind':'changes','state':'shelved','icon':'archive'},
    {'id':'reverted','title':'Reverted','kind':'changes','state':'reverted','icon':'undo'},
    {'id':'conflicts','title':'Conflicts','kind':'conflicts','icon':'warning'},
    {'id':'tasks','title':'Transfers','kind':'tasks','icon':'cloud-upload'},
    {'id':'workspaces','title':'Workspaces','kind':'catalog','source':'workspaces','icon':'desktop'},
    {'id':'streams','title':'Streams','kind':'catalog','source':'streams','icon':'source-branch'},
    {'id':'depots','title':'Depots','kind':'catalog','source':'depots','icon':'database'},
    {'id':'stream_graph','title':'Stream Graph','kind':'graph','source':'stream_graph','icon':'account-tree'},
    {'id':'storage','title':'Storage administration','kind':'catalog','source':'storage','icon':'database','admin_only':True},
]


def initial_state() -> dict:
    return dict(tabs=deepcopy(VIEW_PRESETS[:4]), active_tab='pending', tree_view='depot',
                catalog_rows=[], catalog_detail={}, catalog_source='', catalog_after=None, catalog_cursor='', administrator=False, graph_nodes=[], graph_edges=[], graph_after=None, graph_heads={}, graph_zoom=1, workspace_tree=[], workspace_tree_root='', files_stream='', files_prefix='', files_source='depot', files_selection=[], stream_editor={}, catalog_capabilities={}, depot_draft={}, depot_original={}, storage_info={}, storage_draft={}, storage_original={},
                workspaces=[], streams=[], depots=[], changes=[], tasks=[], tasks_after=None, task_files=[], task_files_after=None, task_info={}, mapping_preview={}, switch_preview={}, workspace='', stream='', active_revision=0,
                change={}, description='', state='pending', view='change', rows=[], selected=[], locks={}, history=[],
                history_path='', history_stream='', history_preview={}, history_more=False, file_focus={}, local_dirty=False, inspector_tab='details', inspection={}, inspection_error='', inspection_busy=False, comparison={}, review={}, submit_review={}, change_details={}, review_request={}, shelves=[], shelves_after=None, preview='', file_error={}, local_counts={}, recovery={}, connection_state='', conflicts=[], resolved_conflicts=[], conflict_selected=[], conflicts_after=None, progress={}, root='', prefix='',
                cursor='', after=None, cursors=[], changes_after=None, workspaces_after=None, streams_after=None,
                change_tree=[], change_children={}, expanded_changes=[], depot_tree=[], depot_heads={}, tree_selection='', tree_width=320, details_height=220, history_details_height=300, log_height=140, log_visible=True, setup=False, editing_workspace=False, case_sensitive=True, setup_kind='workspace', code='', depot='', mappings='',
                target='', shelf='', source='', error='', busy=False,
                selection_query=None, selection_records={}, selection_ids=[], selection_scope='', anchor_id='', focus_id='', context_row={},
                change_ref='', depot_expanded=[], workspace_expanded=[], targets=[], tab_states={}, name_filter='', status_filter='', sort_column='path', sort_desc=False,
                scroll={}, navigation=[], navigation_index=-1,
                columns=[{'key':key,'width':width,'visible':True} for key,width in
                         [('path',300),('local_status',120),('local_number',84),('server_status',120),('checkout',140),('number',72),('have_number',72),('head_number',72),('size',90),('type',70)]])


from .file_workspace_interaction import FileWorkspaceInteraction
from .file_workspace_reads import FileWorkspaceReads, READ_ACTIONS, READ_FIELDS
from .file_workspace_recovery import cache_directory, RECOVERABLE, operation_context, save_operation, load_operation, resume_operation


class FileWorkspaceController(FileWorkspaceReads, FileWorkspaceInteraction, QObject):
    stateChanged = Signal()
    detailsCommandRequested = Signal(str)
    dropRejected = Signal(str)
    progressReady = Signal(int, object)
    inspectionReady = Signal(int, object)
    localReady = Signal(int, object)

    def __init__(self, application, parent=None) -> None:
        super().__init__(parent)
        self.application = application
        self._project_code=application.current_project_code
        self._layout_key=None
        self._layout_base=None
        self._data = initial_state()
        self._restore_geometry()
        self._write_view_context = None
        self._write_selection = None
        from thlib.ui.workspace_models.records import RecordListModel
        self._depot_model = RecordListModel(('id', 'node'), identity_role='id')
        self._change_model = RecordListModel(('id', 'node'), identity_role='id')
        self._depot_model.setParent(self)
        self._change_model.setParent(self)
        self._workspace_model = RecordListModel(('id','node'), identity_role='id')
        self._workspace_model.setParent(self)
        self._catalog_model=RecordListModel(('id','node'),identity_role='id')
        self._catalog_model.setParent(self)
        self._log_model = RecordListModel(('time', 'level', 'operation', 'message', 'path'))
        self._log_model.setParent(self)
        self._operation = ''
        self._last_log_error = ''
        self._tree_sources = {}
        self.stateChanged.connect(self._sync_trees)
        self.stateChanged.connect(self._log_inline_error)
        self._enabled = False
        self._generation = 0
        self._worker = None
        self._init_reads()
        self._watch = None
        self._watch_key = None
        self._watch_generation = 0
        self._watch_pending = set()
        self._watch_checking = False
        self._watch_timer = QTimer(self)
        self._watch_timer.setInterval(1000)
        self._watch_timer.timeout.connect(self._watch_tick)
        self.stateChanged.connect(self._watch_scope)
        self.localReady.connect(self._local_changed, Qt.ConnectionType.QueuedConnection)
        self._inspection_generation = 0
        self._inspection_active = False
        self._inspection_cancel = threading.Event()
        self._inspection_key = None
        self._inspection_timer = QTimer(self)
        self._inspection_timer.setSingleShot(True)
        self._inspection_timer.setInterval(120)
        self._inspection_timer.timeout.connect(self._inspect_selection)
        self.inspectionReady.connect(self._inspected, Qt.ConnectionType.QueuedConnection)
        self.stateChanged.connect(self._queue_inspection)
        self._cancel = threading.Event()
        self.progressReady.connect(self._progress, Qt.ConnectionType.QueuedConnection)
        application.project_changed.connect(self.project_changed)
        # Connection notifications (including ping) do not change the project mode.
        application.signing_out.connect(self.server_changed)
        application.project_state_changed.connect(self.sync_project_mode)
        if hasattr(application, 'authentication_changed'):
            application.authentication_changed.connect(self.sync_project_mode)
        self.sync_project_mode()

    @Property('QVariantMap', notify=stateChanged)
    def data(self) -> dict:
        return self._data

    @Property('QVariantMap', notify=stateChanged)
    def view_data(self) -> dict:
        # Qt models own tree rows; retained tab snapshots stay in Python.
        hidden={'tab_states','change_children','depot_tree','workspace_tree','change_tree','catalog_rows'}
        return {**{key:value for key,value in self._data.items() if key not in hidden},
                'change_file_count':sum(row.get('kind')=='file' for row in self._data['change_tree'])}

    @Property(str, notify=stateChanged)
    def application_project(self):
        return self._project_code

    @Property('QVariantList', constant=True)
    def view_presets(self):
        return deepcopy(VIEW_PRESETS)

    @Slot()
    def copy_change_code(self):
        from PySide6.QtGui import QGuiApplication
        change=self._data['change']
        if change.get('code'):
            QGuiApplication.clipboard().setText('#'+str(change.get('number') or change['code']))

    @Property(QObject, constant=True)
    def depot_model(self):
        return self._depot_model

    @Property(QObject, constant=True)
    def change_model(self):
        return self._change_model

    @Property(QObject, constant=True)
    def workspace_model(self):
        return self._workspace_model

    @Property(QObject, constant=True)
    def catalog_model(self):
        return self._catalog_model

    @Property(QObject, constant=True)
    def log_model(self):
        return self._log_model

    @Slot()
    def clear_log(self) -> None:
        self._log_model.clear()

    @Slot()
    def open_debug_log(self) -> None:
        self.application.open_window('debug_log')

    @Slot()
    def copy_log(self) -> None:
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().setText('\n'.join(
            ' · '.join(str(row[key]) for key in ('time', 'operation', 'message', 'path') if row[key])
            for row in self._log_model.records()))

    def _log(self, level: str, message: str, path: str = '') -> None:
        from thlib.environment import env_server
        ticket = str(env_server.get_ticket() or '')
        if ticket:
            message, path = message.replace(ticket, '<REDACTED>'), path.replace(ticket, '<REDACTED>')
        # Only operation summaries enter the UI; full diagnostics use Debug Log.
        if self._log_model.rowCount() >= 1000:
            self._log_model.remove(0)
        self._log_model.append_records([dict(time=datetime.now().strftime('%H:%M:%S'),
            level=level, operation=self._operation, message=message, path=path)])

    def _log_inline_error(self) -> None:
        message = self._data.get('error', '')
        if message != self._last_log_error:
            self._last_log_error = message
            last = self._log_model.get(self._log_model.rowCount() - 1)
            if message and last.get('message') != message:
                self._log('WARNING', message)

    def _sync_trees(self) -> None:
        for name, model in (('depot_tree', self._depot_model), ('change_tree', self._change_model), ('workspace_tree',self._workspace_model), ('catalog_rows',self._catalog_model)):
            rows = self._data[name]
            source=(rows,self._data['name_filter'],self._data['status_filter']) if name=='change_tree' else (rows,)
            previous=self._tree_sources.get(name)
            if previous and previous[0] is rows and previous[1:]==source[1:]:
                continue
            from .file_workspace_interaction import row_matches
            if name=='change_tree':rows=[row for row in rows if row.get('kind') in ('change','more') or row_matches(row,self._data)]
            model.replace([{'id':row.get('id',row.get('code')), 'node':row} for row in rows])
            self._tree_sources[name] = source

    @Property(str, notify=stateChanged)
    def current_user(self):
        from thlib.environment import env_server
        return str(env_server.get_user())

    @Property(bool, notify=stateChanged)
    def enabled(self) -> bool:
        return self._enabled

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._data['busy']

    @Slot(result=bool)
    def can_leave(self):
        depot_dirty = self._data['depot_draft'] != self._data['depot_original']
        storage_dirty = bool(self._data['storage_draft']) and self._data['storage_draft']['policy'] != self._data['storage_original']
        if depot_dirty or storage_dirty:
            self._data['error'] = self.tr('Save or reset Depot and Storage changes before leaving this project.')
            self.stateChanged.emit()
            return False
        return not self.enabled or not self.busy

    @Slot()
    def sync_project_mode(self) -> None:
        if not self.application.is_stream_server:
            self.server_changed()
            return
        from thlib.environment import env_inst
        project = (env_inst.projects or {}).get(self.application.current_project_code)
        enabled = bool(self.application.is_stream_server and project and project.get_type() == 'file_project')
        if enabled != self._enabled:
            self._enabled = enabled
            self.stateChanged.emit()

    @Slot(str, str)
    def project_changed(self, code: str, _title: str) -> None:
        from thlib.environment import env_inst, env_read_config, env_mode
        self.shutdown()
        self._project_code=code
        self._log_model.clear()
        self._layout_key=None
        self._layout_key=self._tabs_key()
        self._layout_base=env_mode.current_path
        self._data = initial_state()
        project = env_inst.projects.get(code) if env_inst.projects else None
        self._enabled = bool(self.application.is_stream_server and project and project.get_type() == 'file_project')
        self._restore_geometry()
        if self._enabled:
            saved = env_read_config(unique_id=self._tabs_key(), filename='tabs', long_abs_path=True) or {}
            if isinstance(saved.get('tabs'),list):
                self._data['tabs'] = saved['tabs'][:32]
                self._data['active_tab'] = saved.get('active_tab',saved['tabs'][0]['id'] if saved['tabs'] else '')
            for key in ('files_source','files_prefix','files_stream','file_focus','depot_expanded','workspace_expanded'):
                if key in saved:self._data[key]=saved[key]
            self._data['tree_view']=saved.get('tree_view','depot')
            self._data['tab_states']=saved.get('tab_states',{})
            current=self._data['tab_states'].get(self._data['active_tab'],{})
            self._data.update(deepcopy(current))
            if not any(column['key']=='local_number' for column in self._data['columns']):
                self._data['columns'].insert(next((i for i,column in enumerate(self._data['columns']) if column['key']=='have_number'),len(self._data['columns'])),{'key':'local_number','width':84,'visible':True})
        self.stateChanged.emit()
        if self._enabled:
            self.action('refresh', {})
            self.application.open_window('commit_queue')

    @Slot()
    def server_changed(self) -> None:
        self.shutdown()
        self._enabled = False
        self._log_model.clear()
        self._data = initial_state()
        self.stateChanged.emit()

    @Slot(str, 'QVariant')
    def set_value(self, name: str, value) -> None:
        if name not in {'description', 'root', 'prefix', 'view', 'state', 'stream', 'target', 'shelf', 'source', 'preview',
                        'catalog_detail', 'depot_draft', 'depot_original', 'storage_draft', 'storage_original', 'graph_zoom', 'setup', 'editing_workspace', 'setup_kind', 'code', 'depot', 'mappings', 'case_sensitive', 'mapping_preview', 'tree_width', 'details_height', 'history_details_height', 'log_height', 'log_visible', 'tree_view', 'tree_selection', 'history_path', 'history_stream', 'inspector_tab', 'conflict_selected', 'name_filter', 'status_filter'}:
            return
        from PySide6.QtQml import QJSValue
        if isinstance(value,QJSValue):
            value=value.toVariant()
        active=next((tab for tab in self._data['tabs'] if tab['id']==self._data['active_tab']),{})
        if name in ('history_path','history_stream') and active.get('kind')=='history' and active.get('pinned'):
            return
        if name=='setup':
            if value and not self._data.get('setup_original'):
                self._data['setup_original']={key:self._data[key] for key in ('root','stream','mappings','case_sensitive','code','source','depot')}
            elif not value:
                self._data.update(self._data.pop('setup_original',{}))
        self._data[name] = value
        if name=='tree_view':self._save_tabs()
        if name in {'tree_width', 'details_height', 'history_details_height', 'log_height', 'log_visible'}:
            self._save_geometry()
        self.stateChanged.emit()

    @Slot()
    def open_changelist_details(self) -> None:
        if self._data['change'].get('code') and not self.busy:
            self.application.open_window('file_changelist')

    @Slot(str)
    def details_command(self, command: str) -> None:
        if command in {'submit', 'shelve', 'upload', 'revert'}:
            self.detailsCommandRequested.emit(command)

    @Slot(str, bool)
    def select_file(self, path: str, selected: bool) -> None:
        scope='changes' if self._data['view']=='change' else 'files'
        row=next(((key,row) for key,row in self._scope_rows(scope) if row.get('path')==path
                  and row.get('parent',self._data['change'].get('code'))==self._data['change'].get('code')),None)
        if row and (row[0] in self._data['selection_ids']) != selected:
            self.select_file_row(scope,row[0],selected)
        elif not row:
            paths=set(self._data['selected'])
            paths.add(path) if selected else paths.discard(path)
            self._data['selected']=sorted(paths)
            self.stateChanged.emit()

    @Slot(str)
    def choose_root(self, url: str) -> None:
        self.set_value('root', QUrl(url).toLocalFile().replace('\\', '/'))

    def _watch_scope(self) -> None:
        from thlib.side.client.tactic_client_lib.file_watch import WorkspaceWatch
        local_root=self._data.get('setup_original',{}).get('root',self._data['root'])
        key=(self._project_code,self._data['workspace'],local_root) if self.enabled and local_root else None
        if key==self._watch_key:
            return
        self._stop_reads(dispose=True)
        self._watch_generation+=1
        if self._watch:
            self._watch.stop()
        self._watch_key=key
        self._watch_pending.clear()
        self._watch_checking=False
        self._watch=None
        self._watch_timer.stop()
        if key and os.name=='nt':
            self._watch=WorkspaceWatch(key[2])
            self._watch.start()
            self._watch_timer.start()

    def _watch_tick(self) -> None:
        from thlib.environment import env_inst, env_mode, env_server
        from thlib.side.client.tactic_client_lib.file_workspace import watched_changes
        events=self._watch.take()
        if events['error']:
            self._log('WARNING',self.tr('Workspace monitoring stopped. Use Reconcile.'),self._data['root'])
        if events['overflow']:
            self._data['local_dirty']=True
            self.stateChanged.emit()
        remaining=4096-len(self._watch_pending)
        self._watch_pending.update(events['paths'][:remaining])
        if len(events['paths'])>remaining:
            self._data['local_dirty']=True
        if self.busy or self._watch_checking or not self._watch_pending:
            return
        names=tuple(self._watch_pending)
        self._watch_pending.clear()
        generation=self._watch_generation
        root=self._data.get('setup_original',{}).get('root',self._data['root'])
        server=str(env_server.get_server()).rstrip('/')
        if not server.startswith(('http://','https://')):
            server='http://'+server
        identity=sha256((server+'\0'+str(env_server.get_user())+'\0'+self._project_code+'\0'+self._data['workspace']+'\0'+root).encode()).hexdigest()
        cache=Path(env_mode.current_path)/'cache/file_workspaces'/identity/'local.sqlite'
        self._watch_checking=True
        def execute():
            try:
                changed=watched_changes(cache,root,names)
            except (OSError,ValueError) as error:
                changed={name:'unknown' for name in names}
            if generation==self._watch_generation:
                self.localReady.emit(generation,changed)
        worker=env_inst.local_pool.add_task(execute)
        if worker:
            worker.start()
        else:
            self._watch_checking=False
            self._watch_pending.update(names)

    @Slot(int, object)
    def _local_changed(self,generation,paths) -> None:
        if generation!=self._watch_generation:
            return
        self._watch_checking=False
        if not paths:
            return
        self._data['local_dirty']=True
        rows=list(self._data['rows'])
        rows.extend(row for page in self._data['change_children'].values() for row in page.get('items',[]))
        rows.extend(self._data['selection_records'].values())
        rows.append(self._data['context_row'])
        for row in rows:
            path=row.get('local_path',row.get('path',''))
            status=paths.get(path) or next((value for parent,value in paths.items() if value=='missing' and path.startswith(parent+'/')),None)
            if status:
                if status=='added' and (row.get('base') or row.get('head')):
                    status='modified'
                row['local_status']=status
                row['local_modified']=status in ('modified','added')
                if row.get('action') in ('write','move/add'):
                    row['staged_current']=False
                    row['server_status']='modified_after_upload'
        self._tree(self._data)
        self._sync_trees()
        self._inspection_key=None
        self.stateChanged.emit()

    def _queue_inspection(self) -> None:
        if self._data['setup']:
            return
        active=next((tab for tab in self._data['tabs'] if tab['id']==self._data['active_tab']),{})
        if active.get('kind')!='files':
            self._inspection_generation += 1
            self._inspection_key = None
            self._inspection_timer.stop()
            self._data['inspection_busy'] = False
            return
        focus = self._data['file_focus']
        row = self._data['context_row']
        scope = row.get('parent') if self._data['selection_scope'] == 'changes' else ''
        key = (self._project_code, self._data['workspace'], self._data['root'], focus.get('stream'),
               focus.get('path'), scope, self._data['inspector_tab'])
        if not self.enabled or not focus.get('path'):
            self._inspection_generation += 1
            self._inspection_key = None
            self._inspection_timer.stop()
            self._data.update(inspection={},inspection_error='',inspection_busy=False)
            return
        if key != self._inspection_key:
            self._inspection_key = key
            self._inspection_generation += 1
            self._data.update(inspection={}, inspection_error='', inspection_busy=True)
            self._inspection_timer.start()

    def _inspect_selection(self) -> None:
        if not self.application.is_stream_server:
            return
        from thlib.environment import env_inst, env_server
        from thlib.proxy import UrllibTransport
        from thlib.side.client.tactic_client_lib.file_transfer import local_path
        if self._inspection_active or not self._inspection_key:
            return
        self._inspection_active = True
        self._inspection_cancel = threading.Event()
        cancelled = self._inspection_cancel
        generation = self._inspection_generation
        project, workspace, root, stream, path, scope, tab = self._inspection_key
        server = str(env_server.get_server()).rstrip('/')
        if not server.startswith(('http://', 'https://')):
            server = 'http://' + server
        ticket = str(env_server.get_ticket())
        shelf = self._data['change'].get('state') == 'shelved'
        def execute():
            try:
                if not self.application.is_stream_server:
                    raise InterruptedError('The Stream file workspace session changed')
                client = FileTransferClient(server, ticket, project, opener_factory=UrllibTransport)
                options = dict(stream=stream, path=path)
                if scope:
                    options['shelf' if shelf else 'change'] = scope
                info = client.rpc('file_info', **options, **({'workspace': workspace} if workspace else {}), preview=tab == 'preview')
                if cancelled.is_set():
                    return
                if root and info.get('local_path'):
                    local = local_path(Path(root).resolve(), info['local_path'])
                    info['workspace_location'] = local.as_posix()
                    info['local_exists'] = local.is_file()
                    if info['local_exists']:
                        stat = local.stat()
                        info.update(local_size=stat.st_size, local_modified_ns=stat.st_mtime_ns)
                if not cancelled.is_set():
                    self.inspectionReady.emit(generation, info)
            except Exception as error:
                if not cancelled.is_set():
                    self.inspectionReady.emit(generation, {'error': str(error), 'stacktrace':traceback.format_exc()})
        worker = env_inst.commit_pool.add_task(execute)
        if worker:
            worker.start()
        else:
            self._inspected(generation, {'error': self.tr('File worker pool is unavailable')})

    @Slot(int, object)
    def _inspected(self, generation: int, value: dict) -> None:
        self._inspection_active = False
        if generation != self._inspection_generation:
            if self.enabled and self._inspection_key:
                self._inspection_timer.start()
            return
        if value.get('error') and getattr(self.application, 'debug_log', None):
            self.application.debug_log.log('ERROR', value['error'], group='server/file_workspace', source='File inspector', stacktrace=value.get('stacktrace',''))
        self._data.update(inspection=value if 'error' not in value else {},
                          inspection_error=value.get('error', ''), inspection_busy=False)
        self.stateChanged.emit()

    @Slot()
    def stop(self) -> None:
        self._cancel.set()

    @Slot(str, 'QVariantMap')
    def action(self, action: str, values: dict) -> None:
        if not self.application.is_stream_server or not self.enabled:
            return
        if action in READ_ACTIONS and (action!='transfer_status' or self.busy):
            self._start_read(action,values)
            return
        if self.busy:
            return
        if action in ('preview_workspace_switch', 'choose_workspace'):
            if self._data['description'] != self._data['change'].get('description', ''):
                self._data['error'] = self.tr('Save the changelist description before switching views.')
                self.stateChanged.emit()
                return
            self._stop_reads()
        from thlib.environment import env_inst, env_server, env_mode
        self._generation += 1
        generation = self._generation
        self._cancel = threading.Event()
        cancelled = self._cancel
        if action in ('goto_change','prepare_unshelve'):self._capture_view()
        state = deepcopy({key:value for key,value in self._data.items() if key!='tab_states'})
        self._write_view_context=(state['active_tab'],state['view'],state['prefix'],state['change'].get('code'))
        self._write_selection={key:deepcopy(state[key]) for key in SELECTION_FIELDS}
        state['error'] = ''
        server = str(env_server.get_server()).rstrip('/')
        if not server.startswith(('http://', 'https://')):
            server = 'http://' + server
        project = self.application.current_project_code
        if action == 'drop_files':
            values = {**values, 'project': project}
        ticket = str(env_server.get_ticket())
        cache = cache_directory(env_mode.current_path, server, env_server.get_user(), project, state['workspace'], state['root'])
        labels = {'get_latest':'Get latest workspace', 'sync_selected':'Get latest selected files',
                  'sync_folder':'Get latest', 'get_revision':'Get Revision', 'reconcile':'Reconcile',
                  'resume_upload':'Resume upload',
                  'submit':'Submit', 'checkout':'Checkout', 'shelve':'Shelve',
                  'unshelve_begin':'Unshelve', 'merge_begin':'Merge', 'revert':'Revert',
                  'refresh':'Refresh', 'create_change':'New changelist', 'rename_files':'Rename file',
                  'restore_file':'Restore revision', 'delete_change':'Delete changelists',
                  'revert_unchanged':'Revert unchanged files', 'revert_unchanged_change':'Revert unchanged files',
                  'move_files':'Move files', 'drop_files':'Import files', 'revert':'Revert changelist', 'revert_files':'Revert files'}
        self._operation_action=action
        self._operation = self.tr(labels.get(action, 'File operation'))
        self._log('INFO', self.tr('Started'))
        self._data.update(busy=True, error='')
        self.stateChanged.emit()
        last_progress = [0.0]
        recovery_progress = [{}]
        persisted_progress = [0.0]

        def progress(value):
            if cancelled.is_set():
                raise InterruptedError('Stopped. Uploaded files and server tasks are retained; refresh or resume.')
            now = time.monotonic()
            if action in RECOVERABLE or action == 'resume_operation':
                previous = recovery_progress[0]
                fields = ('task','kind','change','workspace','phase','state','journal','source_journal','path','files_done','files_total','bytes_done','bytes_total','total_known','file_error','error')
                if value.get('journal') and previous.get('journal') != value['journal']:
                    previous = {key:previous[key] for key in ('change','workspace','source_journal') if key in previous}
                updated = {**previous,**{key:value[key] for key in fields if key in value}}
                transition = tuple(updated.get(key) for key in ('task','phase','state','journal')) != tuple(recovery_progress[0].get(key) for key in ('task','phase','state','journal'))
                recovery_progress[0] = updated
                if transition or now - persisted_progress[0] >= 2:
                    save_operation(cache, updated, 'operation_progress')
                    persisted_progress[0] = now
            if now - last_progress[0] >= .1 or value.get('state') in ('error', 'complete', 'ready', 'submitted', 'blocked'):
                last_progress[0] = now
                self.progressReady.emit(generation, dict(value))

        def execute():
            try:
                from thlib.proxy import UrllibTransport
                if not self.application.is_stream_server:
                    raise InterruptedError('The Stream file workspace session changed')
                if action in RECOVERABLE:
                    save_operation(cache, operation_context(state, action, values))
                    save_operation(cache, {}, 'operation_progress')
                client = FileTransferClient(server, ticket, project, progress=progress, opener_factory=UrllibTransport)
                native_call = client.rpc
                def call(operation, **kwargs):
                    if not self.application.is_stream_server:
                        raise InterruptedError('The Stream file workspace session changed')
                    if cancelled.is_set() and operation!='transfer_pause':
                        raise InterruptedError('Stopped. Uploaded files and server tasks are retained; refresh or resume.')
                    return native_call(operation, **kwargs)
                client.rpc = call
                result = self._execute(client, state, cache, action, dict(values), cancelled)
                result.pop('resuming_operation',None)
                if (action in RECOVERABLE or action == 'resume_operation') and not result.get('drop_rejected'):
                    if not result.get('operation_blocked'):
                        save_operation(cache, {})
                        save_operation(cache, {}, 'operation_progress')
                        result['recovery'] = {}
                    else:
                        result['recovery'] = load_operation(cache, result)
                if not result.get('drop_rejected'):result['connection_state']='connected'
                return result
            except Exception as exception:
                # Worker boundary: retain diagnostics without printing or opening a modal.
                return {'operation_error': {'exception': exception, 'stacktrace': traceback.format_exc()}}

        worker = env_inst.commit_pool.add_task(execute)
        if worker is None:
            self._operation_failed({'exception': RuntimeError('File worker pool is unavailable')})
            return
        self._worker = worker
        worker.add_result_data(generation)
        worker.result.connect(self._result, Qt.ConnectionType.QueuedConnection)
        worker.error.connect(self._failed, Qt.ConnectionType.QueuedConnection)
        worker.start()

    @Slot(object)
    def _result(self, envelope) -> None:
        result, generation = envelope
        if generation != self._generation:
            return
        self._worker = None
        if 'operation_error' in result:
            self._operation_failed(result['operation_error'])
            return
        drop_rejected = result.pop('drop_rejected', '')
        notice = result.pop('operation_notice', None)
        if notice:
            self._log(notice['level'], self.tr(notice['message']).replace('%1', notice.get('folder', '')), notice.get('path', ''))
        elif result.pop('operation_blocked', False):
            message = self.tr('Not enough free disk space to download this batch. Free space and retry; existing files and Have were kept.' if result['progress'].get('reason') == 'insufficient_disk_space' else 'Sync stopped: this local file is modified or untracked. It was not overwritten. Reconcile and preserve your changes before syncing again.')
            result['error'] = message
            self._log('WARNING', message, result['progress'].get('path', ''))
        elif result.pop('operation_warning', False):
            self._log('WARNING', self.tr('Files without the requested revision: %1. Their local copies were left unchanged.').replace('%1', str(result['progress']['missing_revisions'])), result['progress'].get('missing_path', ''))
        else:
            self._log('INFO', self.tr('Completed'))
        workspace_changed = self._data['workspace'] != result['workspace']
        tabs_changed=workspace_changed or (self._data['tabs'],self._data['active_tab'])!=(result['tabs'],result['active_tab'])
        if workspace_changed or getattr(self,'_operation_action','') in ('reconcile','get_latest','get_revision','sync_selected','sync_folder'):
            result['local_dirty']=False
        else:
            result['local_dirty']=self._data['local_dirty'] or (getattr(self,'_operation_action','') in ('revert','revert_files') and result.get('local_dirty',False))
        if not workspace_changed and result['file_focus'] == self._data['file_focus']:
            result.update({key:self._data[key] for key in ('inspection','inspection_error','inspection_busy','inspector_tab')})
        context=(self._data['active_tab'],self._data['view'],self._data['prefix'],self._data['change'].get('code'))
        moved=not workspace_changed and self._write_view_context is not None and context!=self._write_view_context
        self._stop_reads()
        if moved:
            updated=result.get('change',{})
            result.update({key:self._data[key] for key in READ_FIELDS})
            result.update({key:self._data[key] for key in ('tabs','active_tab','selected','selection_ids','selection_scope','selection_records','focus_id','context_row','file_focus','files_selection')})
            if result['change'].get('code')==updated.get('code'):
                result['change']=updated
                result['description']=updated.get('description','')
        elif not workspace_changed and self._write_selection is not None and any(self._data[key]!=self._write_selection[key] for key in ('selected','selection_ids')):
            result.update({key:self._data[key] for key in SELECTION_FIELDS})
        if workspace_changed and self._data['active_tab']!=result['active_tab']:
            result['tabs']=deepcopy(self._data['tabs'])
            result['active_tab']=self._data['active_tab']
            moved=True
        if workspace_changed:
            # Keep tab preferences, never rows/selections tied to the previous workspace.
            preferences = ('columns', 'sort_column', 'sort_desc', 'name_filter', 'status_filter')
            from .file_workspace_interaction import VIEW_FIELDS
            defaults = initial_state()
            result['tab_states'] = {identity: {**{key: deepcopy(defaults[key]) for key in VIEW_FIELDS},
                                              **{key: value for key, value in tab.items() if key in preferences}}
                                   for identity, tab in self._data['tab_states'].items()}
        else:
            result['scroll']=deepcopy(self._data['scroll'])
            result['tab_states']=self._data['tab_states']
        result.update({key: self._data[key] for key in ('tree_width', 'details_height', 'history_details_height', 'log_height', 'log_visible')})
        self._data = result
        text=self._data.pop('clipboard_text',None)
        if text is not None:
            from PySide6.QtGui import QGuiApplication
            QGuiApplication.clipboard().setText(text)
        if tabs_changed:self._save_tabs()
        self._data['busy'] = False
        self._inspection_key = None
        self.stateChanged.emit()
        if drop_rejected:self.dropRejected.emit(self.tr(drop_rejected))
        if moved:
            QTimer.singleShot(0,lambda:self.action('activate_tab',{'tab':self._data['active_tab']}))

    @Slot(object)
    def _failed(self, envelope) -> None:
        if self.sender() is not self._worker:
            return
        self._worker = None
        payload = envelope[0] if isinstance(envelope, (tuple, list)) else envelope
        self._operation_failed(payload)

    def _operation_failed(self, payload) -> None:
        exception = payload.get('exception') if isinstance(payload, dict) else payload
        raw = str(exception or 'File operation failed')
        path = str(getattr(exception, 'file_error', {}).get('path', ''))
        self._data['file_error'] = getattr(exception, 'file_error', {})
        if isinstance(exception, InterruptedError):
            message = self.tr('Stopped. Uploaded files and server tasks are retained; refresh or resume.')
            level = 'INFO'
        elif raw.startswith('Local file changed after review; review the changelist again: '):
            message=self.tr('Local file changed after review. Review the changelist again.')
            path=raw.partition(': ')[2]
            level='WARNING'
        elif raw.startswith('Local copy is absent. Get Latest before preparing this changelist: '):
            message=self.tr('Local copy is absent. Get Latest before preparing this changelist.')
            path=raw.partition(': ')[2]
            level='WARNING'
        else:
            message = (self.tr('File operation failed. Open Debug Log for details.')
                       if 'Traceback' in raw or '\n' in raw else QCoreApplication.translate('TacticHandler', raw))
            level = 'ERROR'
        self._log(level, message, path)
        self._data.update(busy=False, error=message)
        if getattr(self,'_operation_action','') in RECOVERABLE or getattr(self,'_operation_action','') == 'resume_operation':
            self._data['recovery']={'available':True}
        self._data['progress'] = {**self._data['progress'],
            'state': 'cancelled' if isinstance(exception, InterruptedError) else 'error', 'error': message, 'path': path}
        from urllib.error import URLError, HTTPError
        if isinstance(exception, (URLError, TimeoutError, ConnectionError)) and not (isinstance(exception, HTTPError) and exception.code < 500):
            self._data['connection_state']='offline'
            self._data['progress']['state']='offline'
            self._data['error']=self.tr('Connection lost; work retained. Reconnect and resume the operation.')
        self.stateChanged.emit()
        debug = getattr(self.application, 'debug_log', None)
        if debug is not None and isinstance(payload, dict):
            debug.log(level if level != 'INFO' else 'LOG', raw, group='server/file_workspace',
                      source='File workspace', stacktrace=str(payload.get('stacktrace') or ''),
                      details=self._operation)

    @Slot(int, object)
    def _progress(self, generation: int, value: dict) -> None:
        if generation == self._generation:
            self._data['progress'] = dict(value)
            if value.get('kind')=='mutation' and value.get('change')==self._data['change'].get('code'):
                if value['state'] in ('queued','running'):
                    self._data['change']['active_bulk']=value['task']
                else:
                    self._data['change'].pop('active_bulk',None)
            self.stateChanged.emit()

    @staticmethod
    def _change_query(state, after=''):
        tab=next((row for row in state['tabs'] if row['id']==state['active_tab']),{})
        options={'states':tab['states']} if tab.get('states') else {}
        options['scope']=tab.get('scope','mine')
        if options['scope']!='workspace':options['workspace']=None
        if options['scope']=='stream':options['stream']=state['stream']
        return {'action':'inspect_change','values':{'change':tab['change']}} if tab.get('change') else {
            'action':'changes','values':dict(state=state['state'],after=after,limit=100,**({'workspace':state['workspace']} if 'workspace' not in options else {}),**options)}

    @staticmethod
    def _changes(client, state, after='', page=None):
        if page is None:
            query=FileWorkspaceController._change_query(state,after)
            page=client.rpc(query['action'],**query['values'])
            if query['action']=='inspect_change':page={'items':[page],'after':None}
        state['changes'], state['changes_after'] = page['items'], page['after']
        codes = {item['code'] for item in page['items']}
        current=next((item for item in page['items'] if item['code']==(state['change'].get('code') or state['change_ref'])),None)
        if current:
            clean=state['description']==state['change'].get('description','')
            state['change']=current
            if clean:state['description']=current.get('description','')
        state['expanded_changes'] = [code for code in state['expanded_changes'] if code in codes]
        state['change_children'] = {code: children for code, children in state['change_children'].items() if code in codes}
        FileWorkspaceController._tree(state)

    @staticmethod
    def _tree(state):
        state['change_tree'] = []
        parents={item['code'] for item in state['changes'] if item['state']!='shelved'}
        ordered=[]
        for item in state['changes']:
            if item['state']=='shelved' and item.get('source_change') in parents:continue
            ordered.append((item,0))
            if item['code'] in state['expanded_changes']:
                ordered.extend((shelf,1) for shelf in state['changes'] if shelf['state']=='shelved' and shelf.get('source_change')==item['code'])
        for item,depth in ordered:
            expanded = item['code'] in state['expanded_changes']
            state['change_tree'].append({**item, 'id': item['code'], 'kind': 'change', 'depth': depth, 'expanded': expanded})
            if expanded:
                page = state['change_children'].get(item['code'], {})
                state['change_tree'].extend({**row, 'id': item['code'] + '/' + row['path'], 'kind': 'file', 'depth': depth+1,
                                            'stream': item['stream'], 'parent': item['code'], 'change_state':item['state'], 'owner':item['owner'], 'workspace':item.get('workspace')} for row in page.get('items', [])
                                            )
                if page.get('after'):
                    state['change_tree'].append({'id': item['code'] + '//more', 'kind': 'more', 'depth': depth+1, 'parent': item['code']})

    @staticmethod
    def _depot_roots(state):
        state['depot_heads'] = {}
        state['workspace_tree_root']=''
        state['workspace_tree']=[{'id':'workspace/'+state['workspace'],'kind':'workspace','name':state['workspace'],'directory':'','depth':0,'expanded':False}] if state['workspace'] else []
        state['depot_tree'] = []
        for depot in state['depots']:
            state['depot_tree'].append({'id': 'depot/' + depot['code'], 'kind': 'depot', 'name': depot['code'], 'depth': 0, 'expanded': True})
            state['depot_tree'].extend({'id': 'stream/' + stream['code'], 'kind': 'stream', 'name': stream['code'], 'depth': 1,
                                        'stream': stream['code'], 'directory': '', 'expanded': False}
                                       for stream in state['streams'] if stream['depot'] == depot['code'])

    @classmethod
    def _depot_branch(cls, client, state, identity, more=False, page=None):
        tree = state['depot_tree']
        index = next(i for i, row in enumerate(tree) if row['id'] == identity)
        node = tree[index]
        end = index + 1
        while end < len(tree) and tree[end]['depth'] > node['depth']:
            end += 1
        if node.get('expanded') and not more:
            del tree[index + 1:end]
            node['expanded'] = False
            return
        if node['kind'] == 'depot':
            children = [{'id': 'stream/' + row['code'], 'kind': 'stream', 'name': row['code'], 'depth': node['depth'] + 1,
                         'stream': row['code'], 'directory': '', 'expanded': False}
                        for row in state['streams'] if row['depot'] == node['name']]
        else:
            options = dict(stream=node['stream'], directory=node['directory'], limit=200)
            if state['depot_heads'].get(node['stream']):
                options['published_change'] = state['depot_heads'][node['stream']]
            if more:
                options['after'] = node['after']
            if page is None:page = client.rpc('browse', **options)
            state['depot_heads'][node['stream']] = page['published_change']
            children = [{**row, 'id': 'path/' + node['stream'] + '/' + row['path'], 'depth': node['depth'] + 1,
                         'stream': node['stream'], 'directory': row['path'] if row['kind'] == 'directory' else '', 'expanded': False}
                        for row in page['items']]
            node['after'] = page['after']
            if page['after']:
                children.append({'id': identity + '//more', 'kind': 'more', 'depth': node['depth'] + 1, 'parent': identity})
        if more:
            # Replace just the load-more row; previously expanded folders stay intact.
            position = next(i for i in range(index + 1, end) if tree[i].get('parent') == identity and tree[i]['kind'] == 'more')
            tree[position:position + 1] = children
        else:
            tree[index + 1:end] = children
        node['expanded'] = True
        from .file_workspace_tree_state import trim_tree
        if trim_tree(tree, identity):
            state['operation_notice']={'level':'INFO','message':'Earlier tree rows released; reopen a folder to reload them.'}

    @classmethod
    def _workspace_branch(cls,client,state,cache,identity,more=False,page=None):
        tree=state['workspace_tree']
        index=next(i for i,row in enumerate(tree) if row['id']==identity)
        node=tree[index];end=index+1
        while end<len(tree) and tree[end]['depth']>node['depth']:end+=1
        if node['expanded'] and not more:
            tree[index+1:end]=[];node['expanded']=False;return
        options={'directory':node['directory'],'limit':200,'after':node.get('after','') if more else ''}
        if (cache/'local.sqlite').is_file():
            page=local_browse(cache/'local.sqlite',**options)
        else:
            if page is None:page=client.rpc('workspace_browse',workspace=state['workspace'],root=state['workspace_tree_root'] or None,**options)
            state['workspace_tree_root']=page['root']
        children=[{**row,'id':'workspace-path/'+row['path'],'directory':row['path'] if row['kind']=='directory' else '',
                   'depth':node['depth']+1,'expanded':False,'workspace':True} for row in page['items']]
        node['after']=page['after'];node['expanded']=True
        if page['after']:children.append({'id':identity+'//more','kind':'more','parent':identity,'depth':node['depth']+1,'workspace':True})
        if more:
            position=next(i for i,row in enumerate(tree) if row.get('parent')==identity and row['kind']=='more')
            tree[position:position+1]=children
        else:tree[index+1:end]=children
        from .file_workspace_tree_state import trim_tree
        if trim_tree(tree, identity):
            state['operation_notice']={'level':'INFO','message':'Earlier tree rows released; reopen a folder to reload them.'}

    @classmethod
    def _change_branch(cls, client, state, code, more=False):
        if code in state['expanded_changes'] and not more:
            state['expanded_changes'].remove(code)
            state['change_children'].pop(code, None)
        else:
            change = next(row for row in state['changes'] if row['code'] == code)
            options = {'shelf' if change['state'] == 'shelved' else 'change': code, 'limit': 200}
            previous = state['change_children'].get(code, {})
            if more:
                options['after'] = previous['after']
                if change['state']=='pending':options['edit_revision']=previous['edit_revision']
            page = client.rpc('read_page',source='inspect_change_files',workspace_context=state['workspace'], **options)
            if page.get('info'):
                change.update(page['info'])
                if state['change'].get('code')==code:
                    clean=state['description']==state['change'].get('description','')
                    state['change']={**state['change'],**page['info']}
                    if clean:state['description']=state['change'].get('description','')
            cls._file_states(client,state,Path(state['local_cache']).parent if state.get('local_cache') else None,page['items'],change['stream'])
            cls._locks(client, state, page['items'], change['stream'])
            if more:
                # shortcut: retain 1000 loaded children; whole queries use server selections.
                page['items'] = (previous['items'] + page['items'])[-1000:]
            state['change_children'][code] = page
            while sum(len(value['items']) for value in state['change_children'].values())>8000:
                released=next(identity for identity in state['expanded_changes'] if identity!=code)
                state['change_children'].pop(released,None)
                state['expanded_changes'].remove(released)
                state['operation_notice']={'level':'INFO','message':'Earlier changelist rows released; expand the change to reload them.'}
            if code not in state['expanded_changes']:
                state['expanded_changes'].append(code)
        cls._tree(state)

    @staticmethod
    def _integration(state):
        change = state['change']
        return dict(change=change['code'], edit_revision=change['edit_revision'], integration=change['integration']['code'])

    @classmethod
    def _files(cls, client, state, cache, after='', page=None):
        options = dict(after=after, limit=200, prefix=state['prefix'])
        change = state['change']
        tab=next((row for row in state['tabs'] if row['id']==state['active_tab']),{})
        folder=tab.get('kind')=='files' and tab.get('source')=='selection'
        if folder:options['folder']=True
        if page is None:
            if state['view'] == 'local':
                if folder:
                    page=local_browse(cache/'local.sqlite',directory=state['prefix'],after=after)
                    page['items']=[row for row in page['items'] if row['kind']=='file']
                else:
                    page = local_page(cache / 'local.sqlite', after, changes_only=False, prefix=state['prefix'],
                        local_changes_only=tab.get('reconcile_only',False))
            elif state['view'] == 'have' and state['workspace']:
                page = client.rpc('read_page',source='have',workspace_context=state['workspace'], workspace=state['workspace'], **options)
            elif state['view'] == 'depot' and state['stream']:
                published = state['depot_heads'].get(state['stream']) or (state.get('published') if after else None)
                if published:
                    options['published_change'] = published
                page = client.rpc('read_page',source='list',workspace_context=state['workspace'], stream=state['stream'], **options)
                state['published'] = page['published_change']
            elif state['view'] == 'change' and change:
                scope = {'shelf' if change['state'] == 'shelved' else 'change': change['code']}
                if change['state'] == 'pending' and after:
                    options['edit_revision'] = change['edit_revision']
                page = client.rpc('read_page',source='inspect_change_files',workspace_context=state['workspace'], **scope, **options)
            else:
                page = {'items': [], 'after': None}
        if state['view']=='change' and page.get('info'):
            clean=state['description']==change.get('description','')
            change.update(page['info'])
            if clean:state['description']=change.get('description','')
            for listed in state['changes']:
                if listed['code']==change['code']:listed.update(page['info'])
        state['rows'], state['after'], state['cursor'] = page['items'], page.get('after'), after
        cls._file_states(client,state,cache,state['rows'],(change.get('stream') if state['view']=='change' else None) or state['stream'])
        cls._sort_rows(state)
        if state['view'] == 'change' and change and change['code'] in {row['code'] for row in state['changes']} and not state['prefix'] and not after:
            state['change_children'][change['code']] = page
            if change['code'] not in state['expanded_changes']:
                state['expanded_changes'].append(change['code'])
        cls._tree(state)
        cls._locks(client, state, page['items'], (change.get('stream') if state['view']=='change' else None) or state['stream'])
        cls._sort_rows(state)

    @staticmethod
    def _file_states(client,state,cache,rows,default_stream):
        from thlib.side.client.tactic_client_lib.file_workspace import inspect_local
        valid=[row for row in rows if row.get('local_status')!='unmapped']
        if not valid or not state['workspace']:return
        states=valid if all('head' in row and 'have' in row for row in valid) else client.rpc('file_states',workspace=state['workspace'],paths=[
            {'stream':row.get('stream') or default_stream,'path':row.get('source_path',row['path'])} for row in valid])['items']
        if cache is not None:inspect_local(cache/'local.sqlite',state['root'],states)
        for row,detail in zip(valid,states):
            row.update({key:value for key,value in detail.items() if key not in ('path','stream')})
            if state['view']=='change' and state['change'].get('state'):row['change_state']=state['change']['state']

    @staticmethod
    def _locks(client, state, items, default_stream):
        streams = {}
        for item in items:
            stream = item.get('stream') or default_stream
            state['locks'][stream + '\0' + item.get('source_path', item['path'])] = []
            if 'holders' in item:
                state['locks'][stream + '\0' + item.get('source_path', item['path'])] = item['holders']
            else:
                streams.setdefault(stream, []).append(item.get('source_path', item['path']))
        for stream, paths in streams.items():
            for row in client.rpc('locks', stream=stream, paths=paths)['items']:
                state['locks'][stream + '\0' + row['path']] = row['holders']

    @classmethod
    def _conflicts(cls, client, state, after=''):
        if not state['change'].get('integration'):
            state['conflicts'], state['conflicts_after'], state['resolved_conflicts'], state['conflict_selected'] = [], None, [], []
            return
        page,resolved=client.rpc('read_batch',requests=[
            {'action':'conflicts','values':{**cls._integration(state),'after':after,'limit':100}},
            {'action':'resolved_files','values':{**cls._integration(state),'limit':200}}])['items']
        state['conflicts'],state['conflicts_after']=page['items'],page['after']
        state['resolved_conflicts']=resolved['items']
        state['conflict_selected'] = [path for path in state['conflict_selected'] if any(row['path']==path for row in state['conflicts'])]

    @classmethod
    def _execute(cls, client, state, cache, action, values, cancelled):
        state['local_cache']=str(cache/'local.sqlite')
        cache.mkdir(parents=True, exist_ok=True)
        for field in ('review_revision','shelf_revision','preview_head_revision','edit_revision'):
            value=values.get(field)
            if isinstance(value,str) and value.isdigit():
                values[field]=int(value)
        if action in ('depot_editor','save_depot'):
            from .file_workspace_catalog import depot_editor
            return depot_editor(client,state,action,values)
        if action == 'storage_admin':
            from .file_workspace_catalog import storage_admin
            return storage_admin(client,state,values,cancelled)
        if action in ('stream_editor','save_stream'):
            from .file_workspace_catalog import edit_stream
            return edit_stream(client,state,action,values)
        if action == 'changelist_details':
            from urllib.error import URLError
            request = values.pop('request')
            previous = state.get('change_details', {})
            try:
                result = client.rpc(action, **values)
                details = {**(previous if previous.get('change') == values['change'] else {}), **result}
                details.update(request=request, error='')
                if state['change'].get('code') == values['change']:
                    if state['description'] == state['change'].get('description', ''):
                        state['description'] = result['info'].get('description', '')
                    state['change'] = result['info']
                state['change_details'] = details
            except (URLError, ValueError, TimeoutError, ConnectionError) as error:
                state['change_details'] = {'change': values['change'], 'request': request, 'error': str(error)}
            return state
        from .file_workspace_submit import execute_submit
        if execute_submit(client,state,action,values):
            return state
        if action == 'catalog_page':
            from .file_workspace_catalog import catalog_page
            catalog_page(client,state,values)
            return state
        if action == 'resume_operation':
            action, values = resume_operation(client, state, cache, cancelled)
        if action=='workspace_preview':
            mappings=json.loads(state['mappings']) if state['mappings'].strip() else [{'stream':state['stream'],'source':'...','target':'...','writable':True}]
            state['mapping_preview']=client.rpc('workspace_preview',stream=state['stream'],mappings=mappings,case_sensitive=state['case_sensitive'],paths=values.get('paths',[]))
            return state
        if action in ('preview_workspace_switch', 'choose_workspace') and state['description'] != state['change'].get('description', ''):
            raise ValueError('Save the changelist description before switching views.')
        if action=='preview_workspace_switch':
            if values['workspace'] == state['workspace']:
                state['switch_preview'] = {}
                return state
            preview=client.rpc('workspace_switch_preview',workspace=values['workspace'])
            if preview['previous'] and (preview['pending_changes'] is None or preview['pending_changes'] or preview['active_transfer'] or preview['active_bulk_tasks']):
                state['switch_preview']=preview
                state['switch_preview']['token']=uuid.uuid4().hex
                return state
            action='choose_workspace'
            values={'workspace':preview['workspace'],'revision':preview['revision']}
        if action in ('bulk_query','bulk_target','bulk_resume'):
            if action=='bulk_resume':
                state['progress']=client.wait_bulk(values['task'])
            else:
                if not state.get('selection_query'):
                    raise ValueError('Select matching server files first.')
                operation=values.get('operation','checkout')
                source=state['change']
                destination=source
                if not client.rpc('capabilities').get('files_service_configured'):
                    raise ValueError('Enable the files service before starting server bulk operations.')
                if action=='bulk_target':
                    if not values.get('target') and not values.get('creating'):
                        raise ValueError('Choose a target changelist or create one explicitly.')
                    destination=client.rpc('status',change=values['target']) if values.get('target') else client.rpc(
                        'create_change',workspace=state['workspace'],stream=source['stream'] if operation=='move_files' else state['stream'],description=values.get('description',''),request_id=uuid.uuid4().hex)
                change=source if operation=='move_files' else destination
                options=dict(change=change['code'],edit_revision=change['edit_revision'],selection=state['selection_query']['selection'],
                             operation=operation,mode=values.get('mode','ordinary'),request_id=uuid.uuid4().hex)
                if operation=='move_files':
                    options.update(target_change=destination['code'],target_edit_revision=destination['edit_revision'])
                state['progress']=client.bulk(**options)
                state['change']=client.rpc('status',change=change['code'])
            state['selection_query']=None
            action='refresh'
        if action=='compare':
            from .file_workspace_compare import compare_files
            compare_files(client,state,cache,values,cancelled)
            return state
        if action=='external_compare':
            from .file_workspace_compare import external_compare
            external_compare(client,state,cache,values,cancelled)
            return state
        if action in ('task_files','next_task_files'):
            task=values.get('task') or state['task_info'].get('task')
            page=client.rpc('transfer_items',task=task,after=state['task_files_after'] if action=='next_task_files' else '',limit=200)
            state.update(task_files=page['items'],task_files_after=page['after'],task_info={key:value for key,value in page.items() if key not in ('items','after')})
            return state
        if action=='clear_completed_tasks':
            state['tasks']=[task for task in state['tasks'] if task['state'] not in ('complete','ready','submitted','error','cancelled','expired')]
            state.update(task_files=[],task_files_after=None,task_info={})
            if state['progress'].get('state') in ('complete','ready','submitted','error','cancelled','expired'):
                state['progress']={}
            return state
        if action in ('shelf_targets','shelf_targets_more'):
            page=client.rpc('changes',stream=state['change']['stream'],scope='stream',state='shelved',limit=200,
                            after=state['shelves_after'] if action=='shelf_targets_more' else '')
            state['shelves']=[{**row,'label':'#'+str(row['number'])+' · '+row.get('description','')+' · '+row['owner']} for row in page['items']]
            state['shelves_after']=page['after']
            return state
        if action=='prepare_unshelve':
            if state['description']!=state['change'].get('description',''):
                raise ValueError('Save the changelist description before switching views.')
            shelf=values.get('shelf') or state['change']['code']
            shelf_info=client.rpc('inspect_change',change=shelf)
            if shelf_info.get('state')!='shelved':
                raise ValueError('Choose a shelved changelist.')
            if not values.get('target') and not values.get('creating'):
                raise ValueError('Choose a target changelist or create one explicitly.')
            destination=client.rpc('status',change=values['target']) if values.get('target') else client.rpc(
                'create_change',workspace=state['workspace'],stream=shelf_info['stream'],description=values.get('description',''),request_id=uuid.uuid4().hex)
            if destination['state']!='pending' or destination['stream']!=shelf_info['stream']:
                raise ValueError('Choose a pending changelist in the shelf stream.')
            state.update(change=destination,description=destination.get('description',''),state='pending',selected=[],selection_ids=[],selection_records={})
            state.update(active_tab='pending',view='change',prefix='',stream=destination['stream'])
            if not any(tab['id']=='pending' for tab in state['tabs']):state['tabs'].append(deepcopy(VIEW_PRESETS[1]))
            cls._changes(client,state);cls._files(client,state,cache)
            values={'operation':'unshelve_begin','shelf':shelf}
            action='review_change'
        if action in ('review_change', 'review_more'):
            if action=='review_change':
                state['review']={}
                state.pop('local_review',None)
                if values.get('operation','submit') in ('submit','shelve','shelve_selected','shelve_revert','update_shelf'):
                    review=cache/('review-'+uuid.uuid4().hex+'.sqlite')
                    state['local_review']=client.prepare_change(state['change']['code'],state['root'],review,
                        paths=set(values['paths']) if values.get('paths') else None,cancelled=cancelled.is_set)
                    state['change']=client.rpc('status',change=state['change']['code'])
                state['review_request']=dict(values)
            request=state['review_request']
            operation=request.get('operation','submit')
            options=dict(change=state['change']['code'],edit_revision=state['change']['edit_revision'],limit=200)
            if action=='review_more':
                options['after']=state['review']['after']
                options['edit_revision']=state['review']['edit_revision']
                options.update({key:state['review'][key] for key in ('preview_head_revision','preview_source_root','shelf_revision') if key in state['review']})
            options.update({key:request[key] for key in ('shelf','source_stream','paths') if request.get(key)})
            if operation in ('rebase_begin','unshelve_begin','merge_begin'):
                options['kind']=operation.removesuffix('_begin')
                state['review']=client.rpc('integration_preview',**options)
                state['review'].update(number=state['change']['number'],editable=True,files_unknown=True)
            elif operation=='compare_shelf':
                state['review']=client.rpc('compare_shelf',**options)
            else:
                state['review']=client.rpc('change_preview',**options)
                if action=='review_change' and operation=='submit':
                    from .file_workspace_submit import load_submit_context
                    load_submit_context(client,state)
            return state
        if action=='delete_shelf_files':
            from .file_workspace_interaction import selected_rows
            selected=selected_rows(state)
            if not selected or any(row.get('kind','file')!='file' or row.get('parent')!=state['change']['code'] for row in selected):
                raise ValueError('Select files from this shelf only.')
            client.rpc('update_shelf',shelf=state['change']['code'],shelf_revision=state['change']['edit_revision'],
                       paths=[row.get('source_path',row['path']) for row in selected],delete=True,request_id=uuid.uuid4().hex)
            state.update(selected=[],selection_ids=[],selection_records={})
            action='refresh'
        if action in ('submit','shelve','shelve_selected','shelve_revert','update_shelf'):
            snapshot=state.get('local_review')
            if not snapshot or snapshot.get('change')!=state['change'].get('code') or snapshot.get('root')!=str(Path(state['root']).resolve()) or snapshot.get('edit_revision')!=state['change'].get('edit_revision'):
                raise ValueError('Review local contents before submitting or shelving.')
            reviewed_revision=values.get('review_revision')
            if reviewed_revision is not None and reviewed_revision!=snapshot['edit_revision']:
                raise ValueError('Changelist changed; review the files again.')
            if action=='submit':
                client.configure_submit_review(snapshot,values.get('submit_options',{}))
            revision=client.upload_prepared_change(snapshot,cancelled=cancelled.is_set)
            from thlib.side.client.tactic_client_lib.file_workspace import cache_prepared_change
            cache_prepared_change(cache/'local.sqlite',snapshot['review'])
            state['change']=client.rpc('status',change=snapshot['change'])
            snapshot['edit_revision']=revision
            if reviewed_revision is not None:values['review_revision']=revision
        if action in ('shelve_selected', 'shelve_revert'):
            options = dict(change=state['change']['code'], edit_revision=values.get('review_revision',state['change']['edit_revision']), request_id=uuid.uuid4().hex)
            if action == 'shelve_selected':
                options['paths'] = values.get('paths') or state['selected']
            else:
                options['revert'] = True
            result = client.rpc('shelve', **options)
            state['shelf'] = result['code']
            if action == 'shelve_revert':
                state.update(state='reverted',active_tab='reverted')
                if not any(tab['id']=='reverted' for tab in state['tabs']):
                    state['tabs'].append(deepcopy(next(tab for tab in VIEW_PRESETS if tab['id']=='reverted')))
            action = 'refresh'
        change = state['change']
        review_revision = values.pop('review_revision', None)
        if review_revision is not None and review_revision != change.get('edit_revision'):
            raise ValueError('Changelist changed; review the files again.')
        if action in ('submit','shelve'):
            values.pop('paths', None)
        args = dict(change=change.get('code'), edit_revision=change.get('edit_revision'), request_id=uuid.uuid4().hex)
        loaded = state['change_children'].get(change.get('code'), {}).get('items', []) if state['view'] == 'change' else state['rows']
        from .file_workspace_interaction import selected_rows
        rows = [row for row in selected_rows(state) if row.get('path') and row.get('kind','file')=='file'] if state['selection_ids'] else [row for row in loaded if row['path'] in state['selected']]
        paths = [row.get('source_path', row['path']) for row in rows]
        if state.get('selection_scope')=='changes' and action in ('checkout','move_files','remove_files'):
            parents={row.get('parent') for row in rows}
            if len(parents)>1:
                raise ValueError('Select files from one changelist.')
        if action in ('revert','revert_files'):
            from .file_workspace_revert import revert_files
            from .file_workspace_refresh import refresh
            revert_files(client,state,cache,action,values,cancelled)
            return refresh(cls,client,state,cache,catalog=False,operation=action)
        from .file_workspace_files import execute_files
        handled=execute_files(client,state,cache,action,values,cancelled)
        if handled:
            if action in ('revert_unchanged', 'revert_unchanged_change'):
                from .file_workspace_refresh import refresh
                return refresh(cls,client,state,cache,catalog=False,operation=action)
            if state.get('drop_rejected'):return state
            if action in ('open_local','reveal_local','delete_local','copy_local_paths','export_query','reveal_tree'):
                return state
            if state['change']:
                state['change']=client.rpc('status',change=state['change']['code'])
                state['description']=state['change'].get('description','')
            cls._changes(client,state)
            cls._files(client,state,cache)
            for code in list(state['expanded_changes']):
                state['expanded_changes'].remove(code)
                state['change_children'].pop(code,None)
                cls._change_branch(client,state,code)
            return state
        if action in ('checkout', 'move_files', 'remove_files') and any(row.get('writable') is False or row.get('stream', change.get('stream')) != change.get('stream') for row in rows):
            raise ValueError('Select writable files from the changelist stream.')
        if action=='select_query':
            if values.get('whole_change'):
                state.update(selection_query={**client.rpc('select_query',source='change',change=change['code']),
                    'name':'','file_action':'','prefix':''},selection_ids=[],selection_records={},selected=[])
                return state
            if state['view'] not in ('depot','have','change'):
                raise ValueError('Select a server file view for a query selection')
            options=dict(source=state['view'],prefix=state['prefix'],name=state['name_filter'])
            if state['view']=='depot':options['stream']=state['stream']
            elif state['view']=='have':options['workspace']=state['workspace']
            else:options['change']=state['change']['code']
            status=state['status_filter']
            if status not in ('','Uploaded','Marked for delete','Checked out'):
                raise ValueError('Query selections use server file actions; inspect local states with Reconcile.')
            options['file_action']={'Uploaded':'write','Marked for delete':'delete','Checked out':'checkout'}.get(status,'')
            state.update(selection_query={**client.rpc('select_query',**options),'name':state['name_filter'],
                                           'file_action':options['file_action'],'prefix':state['prefix']},selection_ids=[],selected=[])
            return state
        if action in ('toggle_workspace_tree','more_workspace_tree'):
            cls._workspace_branch(client,state,cache,values['id'],more=action=='more_workspace_tree')
            return state
        if action in ('toggle_depot', 'more_depot'):
            cls._depot_branch(client, state, values['id'], more=action == 'more_depot')
            return state
        if action in ('toggle_change', 'more_change'):
            cls._change_branch(client, state, values['change'], more=action == 'more_change')
            return state
        if action == 'select_directory':
            state['files_selection']=[]
            state.update(files_stream=values.get('stream',state['stream']),files_prefix=values['directory'],
                         files_source='local' if values.get('workspace') and (cache/'local.sqlite').is_file() else 'have' if values.get('workspace') else 'depot',tree_selection=values['id'])
            tab=next((row for row in state['tabs'] if row['id']==state['active_tab']),{})
            if tab.get('kind')=='files':
                state.update(view=state['files_source'] if tab.get('source')=='selection' else tab.get('source','depot'),stream=state['files_stream'],prefix=(tab.get('prefix') or state['files_prefix']) if tab.get('source')=='selection' else tab.get('prefix',''),cursors=[])
                cls._files(client,state,cache)
            return state
        if action == 'select_tree_files':
            from .file_workspace_selection import selected_tree_files
            selected_tree_files(cls,client,state,cache)
            return state
        if action == 'activate_tab':
            tab=next(row for row in state['tabs'] if row['id']==values['tab'])
            if tab['kind'] in ('catalog','graph'):
                from .file_workspace_catalog import catalog_page
                state['view']=tab['kind']
                catalog_page(client,state,{'source':tab['source']})
                return state
            if tab['kind']=='files':
                if tab.get('source')=='selection' and state['files_selection']:
                    from .file_workspace_selection import selected_tree_files
                    selected_tree_files(cls,client,state,cache)
                    return state
                state.update(view=state['files_source'] if tab.get('source')=='selection' else tab.get('source','depot'),prefix=(tab.get('prefix') or state['files_prefix']) if tab.get('source')=='selection' else tab.get('prefix',''),stream=state['files_stream'] or state['stream'],cursors=[])
                cls._files(client,state,cache)
            elif tab['kind']=='changes':
                if state['change'].get('state') not in tab.get('states',[tab['state']]):
                    state.update(change={},description='',selected=[])
                state.update(view='change',state=tab['state'])
                if state['change']:
                    query=cls._change_query(state)
                    page,files=client.rpc('read_batch',requests=[query,{'action':'read_page','values':{
                        'source':'inspect_change_files','workspace_context':state['workspace'],
                        'shelf' if state['change']['state']=='shelved' else 'change':state['change']['code'],
                        'after':'','prefix':state['prefix'],'limit':200}}])['items']
                    if query['action']=='inspect_change':page={'items':[page],'after':None}
                    cls._changes(client,state,page=page)
                    cls._files(client,state,cache,page=files)
                else:
                    cls._changes(client,state)
            return state
        if action == 'choose_stream':
            state.update(stream=values['stream'], prefix='', cursors=[])
            if state['view'] == 'depot':
                cls._files(client, state, cache)
            return state
        if action == 'refresh':
            from .file_workspace_refresh import refresh
            return refresh(cls,client,state,cache)
        elif action == 'change_state':
            state.update(change={}, description='', history=[], rows=[], prefix='', change_children={}, expanded_changes=[])
        elif action == 'choose_workspace':
            client.rpc('switch_workspace', workspace=values['workspace'], revision=values.get('revision',state['active_revision']), request_id=uuid.uuid4().hex)
            from .file_workspace_interaction import VIEW_FIELDS
            defaults = initial_state()
            preserved = ('view', 'state', 'columns', 'sort_column', 'sort_desc', 'name_filter', 'status_filter')
            fields = VIEW_FIELDS + SELECTION_FIELDS + ('root', 'files_stream', 'files_prefix', 'files_source',
                'workspace_tree_root', 'depot_expanded', 'workspace_expanded', 'tree_selection',
                'inspection', 'inspection_error', 'inspection_busy', 'comparison', 'review', 'review_request',
                'preview', 'conflicts', 'resolved_conflicts', 'conflict_selected', 'conflicts_after',
                'progress', 'task_info', 'task_files', 'task_files_after', 'navigation', 'navigation_index', 'switch_preview')
            state.update({key: deepcopy(defaults[key]) for key in fields if key not in preserved})
            state['workspace'] = values['workspace']
            from .file_workspace_refresh import refresh
            return refresh(cls,client,state,cache,operation='choose_workspace')
        elif action=='goto_change':
            if state['description']!=state['change'].get('description',''):raise ValueError('Save the changelist description before switching views.')
            reference=values['change'].strip()
            if reference.startswith(('http://','https://')):
                from urllib.parse import urlsplit, parse_qs, unquote
                link=urlsplit(reference)
                if link.path!='/projects/'+client.project+'/' and unquote(link.path)!='/projects/'+client.project+'/':
                    raise ValueError('Open a changelist link from the current project.')
                references=parse_qs(link.query).get('changelist',[])
                if len(references)!=1:raise ValueError('Paste a changelist number or link.')
                reference=references[0]
            inspected=client.rpc('inspect_change',change=reference)
            identity='change/'+inspected['code']
            if not any(tab['id']==identity for tab in state['tabs']):
                if len(state['tabs'])>=32:raise ValueError('Close a view tab before opening another.')
                state['tabs'].append({'id':identity,'title':'#'+str(inspected['number']),'kind':'changes','state':inspected['state'],'custom':True,'change':inspected['code'],'scope':'all','icon':'archive'})
            state['active_tab']=identity;state['state']=inspected['state'];state['change']=inspected
            state.update(description=state['change'].get('description',''),view='change',prefix='',cursors=[],changes=[state['change']],expanded_changes=[],selected=[],selection_ids=[],selection_records={},selection_query=None)
            cls._files(client,state,cache)
            return state
        elif action == 'select_change':
            selected_page = state['change_children'].get(values['change'])
            state['change'] = next(item for item in state['changes'] if item['code'] == values['change'])
            state.update(description=state['change'].get('description', ''), view='change', prefix='', cursors=[], history=[], preview='')
        elif action == 'create_change':
            state['change'] = client.rpc(action, workspace=state['workspace'], stream=state['stream'], description='',request_id=values.get('request_id') or uuid.uuid4().hex)
            state.update(description='', state='pending', view='change',active_tab='pending',selected=[],selection_ids=[],selection_records={},selection_query=None,anchor_id='',focus_id='')
            if not any(tab['id']=='pending' for tab in state['tabs']):state['tabs'].append(deepcopy(VIEW_PRESETS[1]))
        elif action == 'edit_workspace':
            state.setdefault('setup_original',{key:state[key] for key in ('root','stream','mappings','case_sensitive','code','source','depot')})
            state['case_sensitive']=next((row.get('case_sensitive',True) for row in state['workspaces'] if row['code']==state['workspace']),True)
            workspace = client.rpc('workspace_status', workspace=state['workspace'])
            state.update(setup=True, editing_workspace=True, setup_kind='workspace', code=state['workspace'],
                         root=workspace['local_root'], stream=workspace['stream'],
                         mappings=json.dumps(workspace.get('mappings', []), ensure_ascii=False, indent=2),
                         workspace_revision=workspace.get('view_revision', 0))
            return state
        elif action in ('create_workspace', 'update_workspace', 'create_stream', 'create_depot'):
            params = dict(code=state['code'])
            if action in ('create_workspace', 'update_workspace'):
                import shutil
                root_path=Path(state['root'])
                if not root_path.is_absolute():raise ValueError('Choose an absolute local workspace root.')
                existing=root_path
                while not existing.exists() and existing!=existing.parent:existing=existing.parent
                if not existing.is_dir():raise ValueError('Local workspace root or its parent is not a directory.')
                if any(parent.is_symlink() for parent in (root_path,*root_path.parents)):
                    raise ValueError('Local workspace root must not follow symlinks.')
                if not shutil.disk_usage(existing).free:raise ValueError('Local workspace disk is full.')
                params.update(stream=state['stream'], local_root=state['root'],case_sensitive=state['case_sensitive'])
                if state['mappings'].strip():
                    params['mappings'] = json.loads(state['mappings'])
                if action == 'update_workspace':
                    params.pop('code')
                    params.update(workspace=state['workspace'], view_revision=state['workspace_revision'], request_id=uuid.uuid4().hex)
            if action == 'create_stream':
                params.update(depot=state['depot'])
                if state['source']:
                    params['parent'] = state['source']
            client.rpc(action, **params)
            state.update(state.pop('setup_original',{}))
            state['setup'] = False
            state['editing_workspace'] = False
        elif action == 'next_changes':
            cls._changes(client, state, state['changes_after'])
            return state
        elif action in ('next_workspaces', 'next_streams', 'next_depots', 'next_tasks'):
            field = action[5:]
            page = client.rpc('transfer_tasks' if field == 'tasks' else field, after=state[field + '_after'], limit=200)
            state[field], state[field + '_after'] = page['items'], page['after']
            if field in ('streams', 'depots'):
                cls._depot_roots(state)
            return state
        elif action in ('files', 'next_files', 'previous_files'):
            cursor = state['after'] if action == 'next_files' else state['cursors'].pop() if action == 'previous_files' else ''
            if action == 'next_files':
                state['cursors'].append(state['cursor'])
                state['cursors']=state['cursors'][-128:]
            elif action == 'files':
                state['cursors'] = []
            cls._files(client, state, cache, cursor)
            return state
        elif action == 'history':
            path, stream = values['path'], values['stream']
            history = client.rpc('history', path=path, stream=stream, limit=1000)
            state.update(history=history['items'],history_more=history.get('more',False))
            state.update(history_path=path,history_stream=stream, preview='')
            return state
        elif action == 'history_preview':
            from urllib.error import URLError
            revision = values.pop('revision')
            try:
                state['history_preview'] = {**client.rpc('file_preview', **values), 'revision':revision}
            except (URLError, ValueError, TimeoutError, ConnectionError) as error:
                state['history_preview'] = {'revision':revision, 'error':str(error)}
            return state
        elif action == 'preview':
            result = client.rpc('file_preview', **values)
            state['preview'] = result.get('text') or result['kind']+' · '+str(result['size'])+' bytes · '+result['sha256']
            return state
        elif action == 'save_revision':
            target = Path(QUrl(values.pop('destination')).toLocalFile())
            descriptor = client.rpc('transfer', **values)
            temporary = target.with_name(target.name + '.tactic-' + uuid.uuid4().hex + '.part')
            digest, size = sha256(), 0
            try:
                with client.open('download', **values) as source, temporary.open('xb') as output:
                    for block in iter(lambda: source.read(4 * 1024 * 1024), b''):
                        if cancelled.is_set():
                            raise InterruptedError('Revision download stopped')
                        output.write(block)
                        digest.update(block)
                        size += len(block)
                    output.flush()
                    os.fsync(output.fileno())
                if size != descriptor['size'] or digest.hexdigest() != descriptor['sha256']:
                    raise ValueError('Downloaded revision checksum mismatch')
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
            state['progress'] = {'state': 'complete', 'path': target.as_posix()}
            return state
        elif action=='index_change':
            while True:
                indexed=client.rpc('index_change',change=change['code'])
                client.progress({'state':'indexing','path':indexed.get('after'),'total_known':False})
                if indexed['complete']:
                    break
        elif action in ('reconcile', 'get_latest', 'sync_selected', 'sync_folder', 'get_revision'):
            status = None
            if action != 'reconcile':
                scope = values.get('scope', 'selection' if action == 'sync_selected' else 'folder' if action == 'sync_folder' else 'workspace')
                if scope not in ('workspace', 'selection', 'folder'):
                    raise ValueError('Choose a workspace, folder or file selection.')
                options = {key: values[key] for key in ('force', 'file_revision', 'revision', 'changelist', 'at_date') if key in values}
                for key in ('file_revision', 'revision'):
                    if key in options and isinstance(options[key], str) and options[key].isdigit():
                        options[key] = int(options[key])
                if any(key in options for key in ('file_revision', 'revision', 'changelist', 'at_date')):
                    if not client.rpc('capabilities')['revision_index_ready']:
                        while True:
                            if cancelled.is_set(): return state
                            indexed = client.rpc('revision_upgrade')
                            client.progress({'state': 'indexing_history', **indexed})
                            if indexed['complete']: break
                if scope == 'selection':
                    history = values.get('history')
                    selected = [history] if history else rows
                    if not selected: raise ValueError('Select files first.')
                    local = not history and (state['selection_scope'] == 'workspace' or state['selection_scope'] == 'files' and state['view'] == 'local')
                    if local:
                        options['paths'] = [row.get('local_path', row['path']) for row in selected]
                    else:
                        mapped = client.rpc('workspace_paths', workspace=state['workspace'], paths=[
                            {'stream': row.get('stream') or change.get('stream') or state['stream'], 'path': row.get('source_path', row['path'])} for row in selected])['items']
                        if any(row.get('excluded') for row in mapped): raise ValueError('Selected files must be mapped to this workspace.')
                        options['paths'] = [row['path'] for row in mapped]
                elif scope == 'folder':
                    context = state['context_row']
                    if context.get('kind') == 'depot':
                        options['source_depot'] = context['name']
                    elif context.get('kind') != 'workspace':
                        prefix = context.get('directory', '')
                        if state['selection_scope'] != 'workspace':
                            options['source_stream'] = context.get('stream') or state['stream']
                            if prefix:
                                mapped = client.rpc('workspace_paths', workspace=state['workspace'], paths=[{'stream': options['source_stream'], 'path': prefix + '__subtree__'}])['items'][0]
                                if mapped.get('excluded'): raise ValueError('Folder subtree is excluded from this workspace.')
                                prefix = mapped['path'].rsplit('/', 1)[0] + '/' if '/' in mapped['path'] else ''
                        options['prefix'] = prefix
                status = client.download(state['workspace'], state['root'], **options)
                if status.get('state') == 'blocked':
                    state['progress'] = status
                    state['operation_blocked'] = True
                    return state
            state['progress'] = reconcile_workspace(client, state['workspace'], state['root'], cache / 'local.sqlite', cancelled=cancelled.is_set)
            if status and status.get('missing_revisions'):
                state['progress'].update(missing_revisions=status['missing_revisions'], missing_path=status.get('missing_path', ''))
                state['operation_warning'] = True
            cls._depot_roots(state)
            if action=='reconcile':
                if not any(tab['id']=='reconcile' for tab in state['tabs']):
                    state['tabs'].append({**deepcopy(VIEW_PRESETS[0]),'id':'reconcile','title':'Reconcile','source':'local','reconcile_only':True})
                state.update(active_tab='reconcile',view='local',prefix='',files_selection=[],selected=[],selection_ids=[],selection_records={},
                    selection_scope='files',name_filter='',status_filter='')
            elif next((tab['kind'] for tab in state['tabs'] if tab['id'] == state['active_tab']), '') == 'files':
                state['view'] = 'local'
        elif action == 'resume_upload':
            next_action,next_values=resume_operation(client,state,cache,cancelled)
            return cls._execute(client,state,cache,next_action,next_values,cancelled)
        elif action in ('rebase_begin', 'unshelve_begin', 'merge_begin', 'continue_integration'):
            if action != 'continue_integration':
                client.rpc(action, **args, **values)
                state['change'] = client.rpc('status', change=change['code'])
            while True:
                result = client.rpc('integration_next', **cls._integration(state), request_id=uuid.uuid4().hex)
                client.progress({'state': 'resolving', 'path': result.get('after'), 'conflicts': result['conflicts']})
                if result['complete']:
                    break
            if not result['conflicts']:
                client.rpc('integration_finish', **cls._integration(state), request_id=uuid.uuid4().hex)
        elif action == 'integration_cancel':
            while not client.rpc(action, **cls._integration(state), request_id=uuid.uuid4().hex)['complete']:
                pass
        elif action == 'next_conflicts':
            cls._conflicts(client, state, state['conflicts_after'])
            return state
        elif action in ('resolve', 'undo_resolve', 'merged_file', 'integration_finish'):
            if action == 'merged_file':
                file = Path(QUrl(values.pop('file')).toLocalFile())
                blob = client.rpc('upload_begin', change=change['code'], size=file.stat().st_size)['code']
                with file.open('rb') as source:
                    offset = 0
                    for block in iter(lambda: source.read(4 * 1024 * 1024), b''):
                        with client.open('upload', data=block, length=len(block), change=change['code'], blob=blob, offset=offset):
                            pass
                        offset += len(block)
                        client.progress({'state': 'uploading', 'path': values['path'], 'bytes_done': offset, 'bytes_total': file.stat().st_size, 'total_known': True})
                client.rpc('upload_finish', change=change['code'], blob=blob, sha256=digest_file(file))
                path=values.pop('path')
                values['resolutions'] = [{'path':path, 'choice':'blob', 'blob':blob}]
                conflict=next(row for row in state['conflicts'] if row['path']==path)
                if conflict.get('rename_partner'):
                    values['resolutions'].append({'path':conflict['rename_partner'],'choice':'ours'})
            client.rpc('resolve' if action == 'merged_file' else action, **cls._integration(state), request_id=uuid.uuid4().hex, **values)
        elif action == 'stage_deletions':
            operations = [{'path': row['source_path'], 'delete': True} for row in rows if row.get('local_status') == 'missing' and row.get('writable') and row.get('stream') == change['stream'] and row.get('head') and not row['head'].get('deleted')]
            if not operations:
                raise ValueError('Select writable missing files from the changelist stream.')
            client.rpc('edit', change=change['code'], edit_revision=change['edit_revision'], chunk=uuid.uuid4().hex, operations=operations)
        elif action in ('transfer_status', 'transfer_cancel'):
            state['progress'] = client.rpc(('bulk_status' if action=='transfer_status' else 'bulk_cancel') if values.pop('bulk',False) else action, task=values['task'])
            if action=='transfer_status':
                state['tasks']=[{**row,**state['progress']} if (row.get('task') or row.get('code'))==values['task'] else row for row in state['tasks']]
                return state
            from .file_workspace_refresh import refresh
            return refresh(cls,client,state,cache,catalog=False,operation=action)
        else:
            if action in ('checkout', 'remove_files', 'move_files'):
                values['paths'] = paths
            if action == 'move_files':
                destination = client.rpc('status', change=state['target'])
                values.update(target_change=state['target'], target_edit_revision=destination['edit_revision'])
            if action == 'update_change':
                values['description'] = state['description']
            if action == 'submit':
                values.setdefault('description',state['description'])
                client.submit(change['code'], edit_revision=args['edit_revision'], **values)
                from urllib.error import URLError
                try:
                    if values.get('task_status_updates',change.get('task_status_updates')):
                        client.rpc('submit_task_status',change=change['code'])
                except (URLError,TimeoutError,ConnectionError) as error:
                    state['operation_notice']={'level':'WARNING','message':'Files submitted; linked task statuses were not updated. Retry from Changelist actions. '+str(error)}
                state['progress']={'state':'submitted','change':change['code'],'files_done':change.get('opened_files') or 0,'files_total':change.get('opened_files') or 0,'total_known':change.get('opened_files') is not None}
            else:
                client.rpc(action, **args, **values)
        from .file_workspace_refresh import refresh
        result=refresh(cls,client,state,cache,
            catalog=action in ('create_workspace','update_workspace','create_stream','create_depot'),operation=action)
        if action == 'select_change' and values.get('selected'):
            page=result['change_children'].get(result['change']['code'],{})
            if selected_page and selected_page['edit_revision']!=result['change']['edit_revision']:
                raise ValueError('Changelist changed; refresh the file list.')
            if selected_page:
                result['change_children'][result['change']['code']]=selected_page
                result['rows']=selected_page['items']
                page=selected_page
                cls._tree(result)
            if not any(row['path']==values['path'] for row in page.get('items',[])):
                raise ValueError('Select a file from the loaded changelist.')
            result['selected']=[values['path']]
        return result

    def shutdown(self) -> None:
        from thlib.environment import env_mode
        if self._layout_key and self._enabled and self._layout_base==env_mode.current_path:
            self._capture_view()
        self._watch_generation+=1
        if self._watch:
            self._watch.stop()
        self._watch=None
        self._watch_key=None
        self._watch_timer.stop()
        self._inspection_generation += 1
        self._inspection_cancel.set()
        self._inspection_active = False
        self._inspection_timer.stop()
        self._generation += 1
        self._cancel.set()
        if self._worker:
            self._worker.result.disconnect(self._result)
            self._worker.error.disconnect(self._failed)
            self._worker.cancel()
            self._worker = None
        self._data['busy'] = False
