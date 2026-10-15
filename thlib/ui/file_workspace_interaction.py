"""Desktop file-view selection, view persistence and filesystem interaction."""
from copy import deepcopy
import json
from hashlib import sha256
import uuid
from pathlib import Path

from PySide6.QtCore import QUrl, Slot


VIEW_FIELDS = ('view', 'state', 'stream', 'prefix', 'cursor', 'after', 'cursors',
               'change', 'change_ref', 'description', 'rows', 'selected', 'selection_ids',
               'selection_scope', 'selection_query', 'selection_records', 'anchor_id', 'focus_id', 'changes', 'changes_after',
               'expanded_changes', 'change_children', 'change_tree', 'history',
               'history_path', 'history_stream', 'history_more', 'columns', 'sort_column', 'sort_desc',
               'name_filter', 'status_filter', 'scroll', 'catalog_source', 'catalog_rows', 'catalog_after', 'catalog_cursor', 'catalog_detail', 'graph_nodes', 'graph_edges', 'graph_after', 'graph_heads', 'graph_zoom')


def file_identity(row, state):
    return json.dumps([state['workspace'], row.get('stream') or state.get('stream'),
                       row.get('parent', ''), row.get('source_path', row.get('path', ''))],
                      ensure_ascii=False, separators=(',', ':'))


def row_matches(row,state):
    if row.get('kind')=='change':return True
    query=state['name_filter'].lower()
    status=state['status_filter']
    states={'Modified':('local_status','modified'),'Added':('local_status','added'),
            'Missing':('local_status','missing'),'Uploaded':('action','write'),
            'Marked for delete':('action','delete'),'Checked out':('action','checkout')}
    if status=='Uploaded' and row.get('change_state') in ('submitted','shelved'):return False
    field,value=states.get(status,('',None))
    return (not query or query in row.get('path','').lower()) and (not status or row.get(field)==value)


def selected_rows(state):
    """Keep at most one native command's explicit selection across loaded pages."""
    return [state.get('selection_records', {}).get(key, {}) for key in state['selection_ids']]


class FileWorkspaceInteraction:
    def _scope_rows(self, scope):
        fields = {'changes': 'change_tree', 'files': 'rows', 'depot': 'depot_tree',
                  'workspace': 'workspace_tree', 'history': 'history'}
        rows = self._data.get(fields.get(scope), [])
        if scope in ('files','changes'):
            rows=[row for row in rows if row_matches(row,self._data)]
        result = []
        for row in rows:
            if row.get('kind') == 'more':
                continue
            identity = (file_identity(row, self._data) if scope == 'files' else
                        str(row.get('id') or row.get('code') or row.get('version')))
            result.append((identity, row))
        return result

    @Slot(str, str, int)
    @Slot(str, str, int, bool)
    def select_row(self, scope, identity, modifiers=0, menu=False):
        rows = self._scope_rows(scope)
        keys = [key for key, _ in rows]
        if identity not in keys:
            return
        state = self._data
        previous_focus=dict(state['file_focus'])
        if scope=='files' and state['selection_scope'] in ('depot','workspace'):
            selected_keys={file_identity(item,state) for item in state['files_selection']}
            records={key:deepcopy(item) for key,item in rows if key in selected_keys}
            anchor=next((key for key,item in rows if item.get('source_path',item['path'])==previous_focus.get('path')), '')
            state.update(selection_scope='files',selection_ids=list(records),selection_records=records,
                         anchor_id=anchor,focus_id=anchor)

        row=next(row for key,row in rows if key==identity)
        if scope=='changes' and state['description']!=state['change'].get('description','') and (row.get('parent') or row.get('code'))!=state['change'].get('code'):
            state['error']=self.tr('Save the changelist description before switching views.')
            self.stateChanged.emit()
            return
        selected = set(state['selection_ids']) if state['selection_scope'] == scope else set()
        if not (menu and identity in selected):
            if modifiers & 0x02000000 and state['anchor_id'] in keys:
                first, last = sorted((keys.index(state['anchor_id']), keys.index(identity)))
                span = set(keys[first:last + 1])
                selected = selected | span if modifiers & 0x04000000 else span
            elif modifiers & 0x04000000:
                selected.symmetric_difference_update({identity})
                state['anchor_id'] = identity
            else:
                selected = {identity}
                state['anchor_id'] = identity
        if len(selected) > 1000:
            state['error']=self.tr('Select at most 1000 loaded items, or use a server query selection.')
            self.stateChanged.emit()
            return
        records=state.get('selection_records',{}) if state['selection_scope']==scope else {}
        records.update({key:deepcopy(value) for key,value in rows if key in selected})
        state.update(selection_records={key:records[key] for key in selected if key in records})
        state.update(selection_query=None,selection_scope=scope, selection_ids=[key for key in dict.fromkeys(state["selection_ids"]+keys) if key in selected],
                     focus_id=identity)
        row = next(row for key, row in rows if key == identity)
        state['context_row'] = deepcopy(row)
        if row.get('path') and row.get('kind','file')=='file' and scope!='history':
            state['file_focus']={'path':row.get('source_path',row['path']),'stream':row.get('stream') or state['stream']}
        if scope in ('depot', 'workspace'):
            state['tree_selection'] = identity
            state['files_selection']=[deepcopy(item) for item in selected_rows(state) if item.get('kind')=='file'] if row.get('kind')=='file' else []
            if row.get('kind')!='file':
                state.update(file_focus={},inspection={},inspection_error='',inspection_busy=False)
            state.update(files_source=('local' if Path(state.get('local_cache','')).is_file() else 'have') if scope=='workspace' else 'depot',files_stream=row.get('stream') or state['stream'],
                files_prefix=row.get('directory','') if row.get('kind')!='file' else (row.get('path','').rsplit('/',1)[0]+'/' if '/' in row.get('path','') else ''))
        if scope == 'changes':
            code = row.get('parent') if row.get('kind') == 'file' else row.get('code')
            change = next((item for item in state['changes'] if item['code'] == code), None)
            if change and state['description'] == state['change'].get('description', ''):
                state['change'] = deepcopy(change)
                state['description'] = change.get('description', '')
                state['rows'] = state['change_children'].get(code, {}).get('items', [])
        state['selected'] = [row['path'] for row in selected_rows(state)
                             if row.get('path') and row.get('kind') not in
                             ('change', 'directory', 'depot', 'stream', 'workspace')]
        self.stateChanged.emit()
        tab=next((tab for tab in state['tabs'] if tab['id']==state['active_tab']),{})
        if state['file_focus']!=previous_focus and scope!='history' and row.get('path') and row.get('kind','file')=='file' and tab.get('kind')=='history' and not tab.get('pinned'):
            self._load_history(state['file_focus'])
        if scope in ('depot','workspace') and tab.get('kind')=='files' and tab.get('source')=='selection':
            if state['files_selection']:
                state.update(name_filter='',status_filter='')
                self.stateChanged.emit()
                same_folder=(state['view']==state['files_source'] and state['stream']==state['files_stream']
                             and state['prefix']==state['files_prefix'])
                if (not same_folder or self._read_worker is not None or
                        not any(item['path']==row['path'] for item in state['rows'])):
                    self.action('select_tree_files',{})
            elif row.get('kind') in ('directory','stream','workspace'):
                self.action('select_directory',{'id':identity,'stream':state['files_stream'],'directory':state['files_prefix'],'workspace':scope=='workspace'})

    def _load_history(self, focus):
        if not focus:
            return
        self._data.update(history=[],history_more=False,preview='',history_path=focus['path'],history_stream=focus['stream'])
        self.stateChanged.emit()
        self.action('history',dict(focus))

    @Slot(str, str, bool)
    def select_file_row(self, scope: str, identity: str, selected: bool) -> None:
        if (self._data['selection_scope']==scope and identity in self._data['selection_ids'])==selected:
            return
        files_only=self._data['selection_scope']==scope and all(row.get('kind','file')=='file' for row in selected_rows(self._data))
        self.select_row(scope,identity,0x04000000 if files_only else 0)

    @Slot(str, bool)
    def select_loaded(self, scope, selected=True):
        rows = self._scope_rows(scope)
        self._data.update(selection_query=None,selection_records={key:deepcopy(row) for key,row in rows[:1000]} if selected else {},selection_scope=scope, selection_ids=[key for key, _ in rows[:1000]] if selected else [],
                          selected=[row['path'] for _, row in rows[:1000] if row.get('path') and
                                    row.get('kind', 'file') == 'file'] if selected else [])
        self.stateChanged.emit()

    @Slot(str, int, int)
    def step_selection(self, scope, direction, modifiers):
        rows = self._scope_rows(scope)
        keys = [key for key, _ in rows]
        if not keys:
            return
        focus=self._data['focus_id']
        if scope=='files' and self._data['selection_scope'] in ('depot','workspace'):
            focus=next((key for key,row in rows if row.get('source_path',row['path'])==self._data['file_focus'].get('path')),focus)
        index = keys.index(focus) if focus in keys else -1
        self.select_row(scope, keys[max(0, min(len(keys) - 1, index + direction))], modifiers)

    @Slot('QVariantMap', result=str)
    def row_identity(self, row):
        return file_identity(row, self._data)

    @Slot()
    def copy_change_link(self):
        from PySide6.QtGui import QGuiApplication
        from urllib.parse import urlencode, quote
        from thlib.environment import env_server
        if self._data['change'].get('code'):
            server=str(env_server.get_server()).rstrip('/')
            if not server.startswith(('http://','https://')):server='http://'+server
            QGuiApplication.clipboard().setText(server+'/projects/'+quote(self._project_code,safe='')+'/?'+urlencode({'changelist':self._data['change']['code']}))

    @Slot(str)
    def copy_selection(self, kind):
        if kind=='local':
            self.action('copy_local_paths',{})
            return
        from PySide6.QtGui import QGuiApplication
        rows = selected_rows(self._data)
        values = []
        for row in rows:
            path = row.get('source_path', row.get('path', row.get('directory','')))
            if kind == 'number' and row.get('number'):
                values.append('#' + str(row['number']))
            elif kind == 'local' and path:
                from thlib.side.client.tactic_client_lib.file_transfer import local_path
                values.append(str(local_path(self._data['root'], row.get('local_path', row.get('path', path)))))
            elif kind == 'depot' and path:
                values.append('//' + (row.get('stream') or self._data['stream']) + '/' + path)
            elif path:
                values.append(path)
        QGuiApplication.clipboard().setText('\n'.join(values))

    @Slot(str, str, result='QVariantMap')
    def drag_payload(self, scope, identity):
        self.select_row(scope, identity, 0, True)
        rows = selected_rows(self._data)
        return {'application/x-tactic-file-workspace': json.dumps({
            'project': self.application.current_project_code, 'workspace': self._data['workspace'],
            'scope': scope, 'source':self._data['view'] if scope=='files' else scope, 'rows': rows}, ensure_ascii=False)}

    def _capture_view(self):
        identity = self._data['active_tab']
        if identity and any(tab['id']==identity for tab in self._data['tabs']):
            self._data['tab_states'][identity] = deepcopy({key: self._data[key] for key in VIEW_FIELDS})
        self._save_tabs()

    @Slot(str, float)
    def remember_scroll(self, scope, position):
        self._data['scroll'][scope] = max(0, position)

    @Slot(str)
    def sort_files(self, column):
        if column not in ('path', 'local_status', 'server_status', 'number', 'local_number', 'have_number', 'head_number', 'size', 'type', 'checkout'):
            return
        self._data['sort_desc'] = column == self._data['sort_column'] and not self._data['sort_desc']
        self._data['sort_column'] = column
        self._sort_rows(self._data)
        self._capture_view()
        self.stateChanged.emit()

    @staticmethod
    def _sort_rows(state):
        column = state['sort_column']
        def key(row):
            if column=='checkout':
                holders=state['locks'].get((row.get('stream') or state['stream'])+'\0'+row.get('source_path',row.get('path','')),[])
                return ','.join(holder['owner']+' '+holder['mode'] for holder in holders).casefold()
            if column in ('have_number','head_number'):
                return (row.get('have' if column=='have_number' else 'head') or {}).get('number',0)
            if column in ('number', 'size'):
                return (row.get('file') or row.get('head') or row.get('have') or row).get(column, 0) or 0
            if column == 'type':
                return Path(row.get('path', '')).suffix.casefold()
            return str(row.get(column, '')).casefold()
        state['rows'] = sorted(state['rows'], key=key, reverse=state['sort_desc'])

    @Slot(str, int, bool)
    def configure_column(self, key, width, visible):
        for column in self._data['columns']:
            if column['key'] == key:
                column.update(width=max(48, min(900, width)), visible=visible or key == 'path')
        self._capture_view()
        self.stateChanged.emit()

    @Slot(str, int)
    def move_column(self, key, direction):
        columns = self._data['columns']
        index = next((i for i, column in enumerate(columns) if column['key'] == key), -1)
        target = index + direction
        if index >= 0 and 0 <= target < len(columns):
            columns[index], columns[target] = columns[target], columns[index]
            self._capture_view()
            self.stateChanged.emit()

    def _restore_geometry(self):
        from thlib.environment import env_read_config
        geometry = env_read_config(unique_id='ui_file_workspace', filename='geometry', long_abs_path=True) or {}
        for key, default, minimum in [('tree_width', 280, 220), ('details_height', 220, 140), ('history_details_height', 300, 110), ('log_height', 140, 80)]:
            self._data[key] = max(minimum, min(600, geometry.get(key, default)))
        self._data['log_visible'] = geometry.get('log_visible', True) is not False

    def _save_geometry(self):
        from thlib.environment import env_write_config
        env_write_config({key: self._data[key] for key in ('tree_width', 'details_height', 'history_details_height', 'log_height', 'log_visible')},
                         unique_id='ui_file_workspace', filename='geometry', long_abs_path=True)

    def _tabs_key(self):
        if self._layout_key:
            return self._layout_key
        from thlib.environment import env_server
        key = str(env_server.get_server()) + '\0' + str(env_server.get_user()) + '\0' + self._project_code
        return 'ui_file_workspace/' + sha256(key.encode()).hexdigest()

    def _save_tabs(self):
        from thlib.environment import env_write_config
        saved={key:self._data[key] for key in ('tabs','active_tab','tree_view','files_source','files_prefix','files_stream','file_focus')}
        saved['depot_expanded']=[row['id'] for row in self._data['depot_tree'] if row.get('expanded')] if self._data['depot_tree'] else self._data['depot_expanded']
        saved['workspace_expanded']=[row['id'] for row in self._data['workspace_tree'] if row.get('expanded')] if self._data['workspace_tree'] else self._data['workspace_expanded']
        fields=('selection_ids','selection_scope','selection_records','anchor_id','focus_id','selected','expanded_changes',
                'history_path','history_stream','change_ref','prefix','stream','view','state','columns','sort_column','sort_desc','name_filter','status_filter','scroll','graph_zoom','catalog_source')
        saved['tab_states']={identity:{**{key:value for key,value in values.items() if key in fields},'change_ref':values.get('change',{}).get('code',values.get('change_ref',''))}
                             for identity,values in self._data['tab_states'].items()}
        references=('id','path','source_path','local_path','stream','parent','kind','workspace','code','change','number','deleted')
        for values in saved['tab_states'].values():
            values['selection_records']={identity:{key:value for key,value in row.items() if key in references} for identity,row in values.get('selection_records',{}).items()}
        env_write_config(saved, unique_id=self._tabs_key(), filename='tabs',long_abs_path=True)

    @Slot(str)
    def open_view(self, identity):
        preset = next((row for row in self.view_presets if row['id']==identity),None)
        if not preset:
            return
        if not any(row['id']==identity for row in self._data['tabs']):
            self._data['tabs'].append(deepcopy(preset))
        self.activate_tab(identity)

    @Slot(str)
    def activate_tab(self, identity):
        if not any(row['id']==identity for row in self._data['tabs']):
            return
        if self._data['description'] != self._data['change'].get('description',''):
            self._data['error']=self.tr('Save the changelist description before switching views.');self.stateChanged.emit();return
        self._capture_view()
        restored=self._data['tab_states'].get(identity)
        self._data['active_tab']=identity
        if restored:
            restored=deepcopy(restored)
            tab=next(row for row in self._data['tabs'] if row['id']==identity)
            current=(self._data['change'] if tab['kind']=='conflicts' or (tab['kind']=='files' and not restored.get('change')) or
                     self._data['change'].get('code')==restored.get('change',{}).get('code') else
                     next((change for change in self._data['changes'] if change['code']==restored.get('change',{}).get('code')),None))
            if current:
                restored['change']=deepcopy(current)
                restored['description']=current.get('description','')
            self._data.update(restored)
        else:
            self._data.update(selected=[],selection_ids=[],selection_records={},selection_query=None,selection_scope='',focus_id='',anchor_id='',scroll={})
        self._save_tabs()
        tab=next(row for row in self._data['tabs'] if row['id']==identity)
        if tab['kind']=='history':
            focus=({'path':self._data['history_path'],'stream':self._data['history_stream']} if tab.get('pinned') and self._data['history_path'] else self._data['file_focus'])
            self._load_history(focus)
        if tab['kind'] in ('files','changes','catalog','graph'):
            self.action('activate_tab',{'tab':identity})
        else:self.stateChanged.emit()

    @Slot(str)
    def close_tab(self, identity):
        if self.busy:
            return
        active=self._data['active_tab']==identity
        if active and self._data['description']!=self._data['change'].get('description',''):
            self._data['error']=self.tr('Save the changelist description before switching views.');self.stateChanged.emit();return
        self._capture_view()
        self._data['tab_states'].pop(identity,None)
        self._data['tabs']=[row for row in self._data['tabs'] if row['id']!=identity]
        if active:
            self._data['active_tab']=''
        self._save_tabs()
        self.stateChanged.emit()
        if active and self._data['tabs']:
            self.activate_tab(self._data['tabs'][0]['id'])

    @Slot(int)
    def move_tab(self, direction):
        if self.busy:
            return
        tabs=self._data['tabs']
        index=next((i for i,row in enumerate(tabs) if row['id']==self._data['active_tab']),-1)
        target=index+direction
        if index < 0 or direction not in (-1,1) or not 0 <= target < len(tabs):
            return
        tabs[index],tabs[target]=tabs[target],tabs[index]
        self._save_tabs();self.stateChanged.emit()

    @Slot('QVariantMap')
    def configure_tab(self, values):
        if self.busy or not str(values.get('title','')).strip():
            return
        preset=next((row for row in self.view_presets if row['id']==values.get('preset')),None)
        if not preset or len(self._data['tabs']) >= 32 and not values.get('id'):
            return
        identity=values.get('id') or uuid.uuid4().hex
        row={**preset,'id':identity,'title':str(values['title']).strip()[:120],'custom':True}
        row['prefix']=str(values.get('prefix',''))
        row['pinned']=bool(values.get('pinned',False))
        row['scope']=values.get('scope','mine') if values.get('scope','mine') in ('mine','workspace','stream','all') else 'mine'
        if row['kind']=='files':
            row['source']=values.get('source') if values.get('source') in ('selection','depot','have','local','change') else 'depot'
        existing=next((i for i,tab in enumerate(self._data['tabs']) if tab['id']==identity),None)
        if existing is None:self._data['tabs'].append(row)
        else:self._data['tabs'][existing]=row
        self.activate_tab(identity)

    @Slot(int)
    def set_navigation(self, direction):
        index=self._data['navigation_index']+direction
        if 0<=index<len(self._data['navigation']):
            self._data['navigation_index']=index
            self.action('navigate',{'path':self._data['navigation'][index],'restore':True})
