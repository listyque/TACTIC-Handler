"""Native agent requests with captured context and background transport."""
from copy import copy, deepcopy
import json
import base64
import mimetypes
from pathlib import Path
import tempfile
from uuid import uuid4

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot, QUrl, QBuffer, QIODevice, QCoreApplication

COMMAND = 'tactic.ui.panel.agent_request_cmd.AgentRequestCmd'


def project_server(server, project):
    if server.get_project() == project:
        return server
    client = copy(server)
    client.set_project(project)
    return client


class AgentRequestController(QObject):
    changed = Signal()
    clipboardChanged = Signal()

    def __init__(self, application, server_pool):
        super().__init__(application)
        self.application = application
        self._pool = server_pool
        self._generation = 0
        self._server = None
        self._worker = None
        self._in_flight = False
        self._queued_action = ''
        self._library_operation = None
        self._history_timer = QTimer(self)
        self._history_timer.setSingleShot(True)
        self._history_timer.setInterval(300)
        self._history_timer.timeout.connect(self.refresh)
        self._timer = QTimer(self)
        self._timer.setInterval(2500)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(lambda: self._request('poll'))
        self._model = self.new_model()
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().dataChanged.connect(self.clipboardChanged)
        application._registry.register('open_agent_request', self.open)
        application.agentRequestRequested.connect(self.open_for_item)
        application.authentication_changed.connect(self.reset)
        application.signing_out.connect(self.reset)
        application.window_model.windowVisibilityChanged.connect(self.visibility)

    @staticmethod
    def initial(context=None):
        return dict(context=context or {}, prompt='', allowChanges=False, allowWeb=False, hosts=[], executor={}, executorTarget=None, requests=[], selected='',
                    request={}, busy=False, error='', refreshError='', pending=None, attachments=[], uploading=False, model=None, effort=None, provider=None, contextExpanded=False, previews={},
                    history=dict(visible=None,mobile=False,width=280,query='',project='',searchOpen=False,grouping='time',archived=False,collapsed={},edit=None),
                    groups=[],groups_revision='',group_revisions={},projects=[],unavailable_projects=[],total=0,next_offset=None,drafts={})

    @staticmethod
    def saved_choices():
        from thlib.environment import env_read_config
        stored = env_read_config(filename='ui_agent_chat', unique_id='ui_main', long_abs_path=True) or {}
        if not isinstance(stored, dict):
            return {}
        return {key: value for key, value in stored.items()
                if (key in ('provider', 'model', 'effort') and isinstance(value, str) and len(value) <= 512)
                or (key in ('allowChanges', 'allowWeb') and type(value) is bool)}

    def new_model(self, context=None):
        return dict(self.initial(context), **self.saved_choices())

    def remember_choices(self, fields):
        from thlib.environment import env_write_config
        try:
            env_write_config(dict(self.saved_choices(), **fields), filename='ui_agent_chat', unique_id='ui_main', long_abs_path=True)
        except OSError as error:
            self._model['error'] = str(error)

    @Slot('QVariantMap')
    def set_history(self, value):
        before = self._model['history']
        self._model['history'] = deepcopy(value)
        if any(before.get(key) != value.get(key) for key in ('query','archived','project')):
            self._history_timer.start()
        self.changed.emit()

    def _draft(self):
        return {key:deepcopy(self._model[key]) for key in ('prompt','attachments','model','provider','effort','allowChanges','allowWeb')}

    def _restore_draft(self, code, fresh=False):
        values = dict(prompt='',attachments=[],model=None,provider=None,effort=None,allowChanges=False,allowWeb=False)
        if fresh or not code:
            values.update(self.saved_choices())
        values.update(deepcopy(self._model['drafts'].get(self._draft_key(code), {})))
        self._model.update(values)

    def _draft_key(self, code):
        return self._model['context']['project']+':'+code

    @Property('QVariantMap', notify=changed)
    def model(self):
        return deepcopy(self._model)

    def capture(self):
        app = self.application
        section, tab = app._current_section(), app._current_tab()
        shelf = app.script_shelf_context()
        return dict(client='TH', project=app.current_project_code or '', page=section.entry_key if section else '',
                    title=section.title if section else '', search_type=section.search_type if section else '',
                    view=(getattr(tab,'layout_view','') or tab.table_view) if tab else '', search_keys=shelf.get('search_keys', []))

    @Slot(str)
    def open_for_item(self, node_id):
        app = self.application
        node = app._node_for_any(node_id)
        if not app.can_administer or node is None or node.node_type not in ('sobject', 'snapshot') or not node.search_key:
            return
        if self._model['prompt'].strip() or self._model['attachments'] or self._model['pending'] or self._model['uploading']:
            self.open()
            app.notification_changed.emit('Send or clear the current draft before opening another object')
            return
        context = self.capture()
        tab = app._current_tab()
        ids = list(tab.selected_node_ids) if tab and node_id in tab.selected_node_ids else [node_id]
        nodes = [app._node_for_any(identity) for identity in ids]
        context.update(search_type=node.search_key.split('?')[0], search_keys=list(dict.fromkeys(
            item.search_key for item in nodes if item and item.node_type in ('sobject', 'snapshot') and item.search_key)))
        self._generation += 1
        self._in_flight = False
        self._queued_action = ''
        self._timer.stop()
        self._model = dict(self.new_model(context), history=self._model['history'], drafts=self._model['drafts'])
        self._capture_session()
        self.open(context)

    @Slot()
    def reset(self):
        self._generation += 1
        self._in_flight = False
        self._queued_action = ''
        self._timer.stop()
        self._history_timer.stop()
        self._server = None
        self._model = self.new_model()
        self.application.window_model.close_window('agent_request')
        self.changed.emit()

    @Slot()
    def open(self, context=None):
        if not self.application.can_administer:
            return
        if not self._model['selected'] and not self._model['prompt'] and not self._model['attachments'] and not self._model['pending'] and not self._model['uploading']:
            self._model = dict(self.new_model(context or self.capture()), history=self._model['history'], drafts=self._model['drafts'])
        if self._model['context'].get('project') and self._server is None:
            self._capture_session()
        self.application.window_model.show_window('agent_request')
        if self._server is None:
            self._model['error'] = self._model['error'] or 'Select a project before contacting the agent'
            self.changed.emit()
        else:
            self.refresh()

    def _capture_session(self):
        from thlib import tactic_classes as tc
        self._server = None
        if self._model['context'].get('project'):
            try:
                self._server = tc.server_start(project=self._model['context']['project'])
            except PermissionError as error:
                self._model['error'] = str(error)

    @Slot(str, bool)
    def visibility(self, window_id, visible):
        if window_id == 'agent_request':
            if visible:
                self.refresh()
            else:
                if self._model['request'].get('status') in ('queued', 'running', 'cancelling'):
                    self._timer.start()
                else:
                    self._timer.stop()

    @Slot()
    def refresh(self):
        self._request('refresh')

    @Slot(str, 'QVariant')
    def handle(self, action, value=''):
        if hasattr(value,'toVariant'):
            value=value.toVariant()
        if self._model['busy']:
            return
        if action == 'executorTarget':
            self._model['executorTarget'] = value
            self.changed.emit()
            return
        if action == 'executor' and isinstance(value, dict) and value.get('action') in ('start', 'stop'):
            if getattr(self.application, 'agent_desktop', None):
                self.application.agent_desktop.stop_local(self._model['context']['project'], value)
            self._request('executor_' + value['action'] + ':' + value['target'])
            return
        if action in ('historyNew','historyEdit'):
            if self._model['pending'] or self._model['uploading']:
                return
            if not self._model['selected'] and action == 'historyNew' and (self._model['prompt'].strip() or self._model['attachments']):
                self._model['error']='Send or clear the current draft before opening another object'
                self.changed.emit()
                return
            context=deepcopy(self._model['context']) if action=='historyEdit' else self.capture()
            project=self._model['history'].get('project') or context['project']
            if action!='historyEdit' and project!=context['project']:
                context=dict(client='TH',project=project,page='',title='',search_type='',view='',search_keys=[])
            self._library_operation=dict(action='draft',edit=action=='historyEdit',values=dict(request_id=str(uuid4()),context=context))
            self._request('library')
            return
        if action in ('historySave','historyArchive','historyGroupRemove'):
            edit=self._model['history']['edit']
            if not edit:
                return
            if edit['kind']=='group':
                self._library_operation=dict(action='group_remove' if action=='historyGroupRemove' else 'group_save', values=dict(group=edit['id'],name=edit['name'],expected_revision=edit['revision']))
            else:
                values={key:edit[key] for key in ('title','group','pinned','archived')}
                if action=='historyArchive':values['archived']=not values['archived']
                self._library_operation=dict(action='organize',values=dict(request_id=edit['id'],expected_revision=edit['revision'],document=values))
            self._library_operation['project']=edit.get('project') or self._model['context']['project']
            self._request('library')
            return
        if action=='historyMore':
            self._request('historyMore')
            return
        if action=='historyUseContext':
            source=self._model['history']['edit']
            if not source or not self._model['selected'] or self._model['request'].get('status') in ('queued','running','cancelling'):
                return
            self._library_operation=dict(action='link_source',values=dict(request_id=self._model['selected'],
                source_project=source['project'],source_request=source['id']))
            self._request('library')
            return
        if action in ('prompt', 'changes', 'web'):
            if self._model['pending'] or (action in ('changes', 'web') and self._model['selected'] and self._model['request'].get('status')!='draft'):
                return
            self._model[{'prompt': 'prompt', 'changes': 'allowChanges', 'web': 'allowWeb'}[action]] = str(value) if action == 'prompt' else bool(value)
            if action in ('changes', 'web'):
                field = 'allowChanges' if action == 'changes' else 'allowWeb'
                self.remember_choices({field: self._model[field]})
            self.changed.emit()
        elif action == 'select':
            if self._model['uploading'] or self._model['pending']:
                return
            if not self._model['selected'] and (self._model['prompt'].strip() or self._model['attachments']):
                self._model['error']='Send or clear the current draft before opening another object'
                self.changed.emit()
                return
            code=value.get('request_id') if isinstance(value,dict) else str(value)
            project=value.get('project') if isinstance(value,dict) else None
            selected=next((row for row in self._model['requests'] if row['request_id']==code
                           and (not project or row.get('project')==project)),None)
            if selected is None:
                return
            self._model['drafts'][self._draft_key(self._model['selected'])]=self._draft()
            project=selected.get('project') or self._model['context']['project']
            if project!=self._model['context']['project']:
                self._model['context']=dict(client='TH',project=project,page='',title='',search_type='',view='',search_keys=[])
                self._model['previews']={}
            self._generation += 1
            self._in_flight = False
            self._model.update(selected=code, request={}, pending=None)
            self._restore_draft(code, fresh=selected.get('status') == 'draft')
            self._model['history']['edit']=None
            self.refresh()
        elif action == 'send':
            if self._model.get('executor', {}).get('state') in ('preparing', 'starting', 'stopping', 'failed'):
                return
            started=bool(self._model['selected']) and self._model['request'].get('status')!='draft'
            allowed = self._model['request'].get('document', {}).get('allow_changes', False) if started else self._model['allowChanges']
            hosts = [host for host in self._model['hosts'] if not allowed or host['capabilities']['changes']]
            hosts.sort(key=lambda host: host['host_id'] != self._model['request'].get('host_id'))
            if (self._model['prompt'].strip() or self._model['attachments']) and hosts and not self._model['uploading']:
                files = [file['attachment_id'] for file in self._model['attachments']]
                model = self._model['model'] if self._model['model'] is not None else self._model['request'].get('model', '')
                effort = self._model['effort'] if self._model['effort'] is not None else self._model['request'].get('effort', '')
                provider = self._model.get('provider')
                if provider is None:
                    provider = self._model['request'].get('provider','codex') if started else hosts[0]['capabilities'].get('default_provider','codex')
                self._model['pending'] = self._model['pending'] or (dict(message_id=str(uuid4()), host_id=hosts[0]['host_id'], text=self._model['prompt'],
                    attachments=files, model=model, effort=effort, provider=provider) if started else
                    dict(request_id=self._model['selected'] or str(uuid4()), host_id=hosts[0]['host_id'], document=dict(prompt=self._model['prompt'],
                        context=deepcopy(self._model['request'].get('document',{}).get('context',self._model['context'])), allow_changes=self._model['allowChanges'], allow_web=self._model['allowWeb'], attachments=files, model=model, effort=effort, provider=provider)))
                self._request('send')
        elif action in ('model', 'effort', 'provider'):
            if self._model['pending'] or self._model['request'].get('status') in ('queued', 'running', 'cancelling'):
                return
            self._model[action] = str(value)
            if action == 'provider':
                self._model['model'] = ''
            if action in ('model', 'provider'):
                self._model['effort'] = ''
            provider = self._model['provider'] or self._model['request'].get('provider') or next(
                (host['capabilities'].get('default_provider', 'codex') for host in self._model['hosts']), 'codex')
            self.remember_choices(dict(provider=provider,
                model=self._model['model'] if self._model['model'] is not None else self._model['request'].get('model', ''),
                effort=self._model['effort'] or ''))
            self.changed.emit()
        elif action == 'context':
            self._model['contextExpanded'] = not self._model['contextExpanded']
            self.changed.emit()
        elif action == 'remove' and not self._model['pending']:
            self._model['attachments'] = [file for file in self._model['attachments'] if file['attachment_id'] != value]
            self.changed.emit()
        elif action == 'paste':
            self.paste_attachment()
        elif action == 'download':
            self._download(str(value))
        elif action in ('refresh', 'cancel', 'undo'):
            if action == 'undo':
                self._model['pending'] = dict(operation_id=self._model['request']['undo_operation'])
            self._request(action)

    @Property(bool, notify=clipboardChanged)
    def clipboard_has_attachment(self):
        from PySide6.QtGui import QGuiApplication
        data = QGuiApplication.clipboard().mimeData()
        return bool(data and (data.hasUrls() or data.hasImage()))

    @Slot(result=bool)
    def paste_attachment(self):
        from PySide6.QtGui import QGuiApplication
        data = QGuiApplication.clipboard().mimeData()
        if data is None:
            return False
        if data.hasUrls():
            self.add_files(data.urls())
            return True
        if data.hasImage():
            self._start_files([], QGuiApplication.clipboard().image().copy())
            return True
        return False

    @Slot('QVariantList')
    def add_files(self, urls):
        self._start_files([QUrl(url).toLocalFile() for url in urls if QUrl(url).isLocalFile()])

    def _start_files(self, paths, image=None):
        if self._in_flight or self._server is None or self._model['pending'] or self._model['uploading']:
            return
        if len(paths) + len(self._model['attachments']) + (image is not None) > 20:
            self._model['error'] = 'Attach at most 20 files'
            self.changed.emit()
            return
        self._timer.stop()
        self._generation += 1
        self._in_flight = True
        self._model.update(uploading=True, error='')
        self.changed.emit()
        if self._pool.is_stopped:
            self._pool.start()
        self._worker = self._pool.add_task(self._upload, self._server, self._model['context']['project'], paths, image, self._generation)
        self._worker.result.connect(self._files_done)
        self._worker.start()

    @staticmethod
    def _upload(server, project, paths, image, generation):
        files, previews = [], {}
        try:
            server = project_server(server, project)
            def call(action, **values):
                result = server.execute_cmd('tactic.ui.panel.agent_attachment_cmd.AgentAttachmentCmd', dict(action=action, project_code=project, **values))
                if result.get('status') != 'OK':
                    raise RuntimeError('Attachment upload failed')
                return json.loads(result['info']) if isinstance(result['info'], str) else result['info']
            with tempfile.TemporaryDirectory(prefix='tactic-agent-input-') as directory:
                if image is not None:
                    path = Path(directory) / 'clipboard.png'
                    if not image.save(str(path)):
                        raise RuntimeError('Clipboard image could not be saved')
                    paths = [*paths, str(path)]
                for value in paths:
                    path = Path(value)
                    size = path.stat().st_size
                    if not path.is_file() or size > 64 * 1024 * 1024:
                        raise ValueError('Each attachment must be at most 64 MB')
                    code = str(uuid4())
                    call('start', attachment_id=code, name=path.name, size=size, media_type=mimetypes.guess_type(path.name)[0] or '')
                    with path.open('rb') as source:
                        offset = 0
                        while chunk := source.read(384 * 1024):
                            call('append', attachment_id=code, offset=offset, data=base64.b64encode(chunk).decode())
                            offset += len(chunk)
                    files.append(call('finish', attachment_id=code))
                    if image is not None and path.name == 'clipboard.png':
                        buffer = QBuffer(); buffer.open(QIODevice.WriteOnly)
                        image.scaledToWidth(160).save(buffer, 'PNG')
                        previews[code] = 'data:image/png;base64,' + bytes(buffer.data().toBase64()).decode()
                    elif files[-1]['media_type'].startswith('image/'):
                        previews[code] = QUrl.fromLocalFile(str(path)).toString()
            return dict(generation=generation, files=files, previews=previews)
        except Exception as error:
            return dict(generation=generation, files=files, previews=previews, error=str(error))

    @Slot(object)
    def _files_done(self, result):
        if isinstance(result, tuple):
            result = result[0]
        if result['generation'] != self._generation:
            return
        self._worker = None
        self._in_flight = False
        self._model['uploading'] = False
        self._model['attachments'].extend(result['files'])
        self._model['previews'].update(result['previews'])
        self._model['error'] = result.get('error', '')
        self._model['busy'] = False
        self.changed.emit()
        if self._queued_action:
            action, self._queued_action = self._queued_action, ''
            self._request(action)
            return
        self._timer.start()

    def _download(self, code):
        if self._in_flight or self._server is None:
            return
        self._generation += 1
        self._in_flight = True
        self._model['busy'] = True
        self.changed.emit()
        if self._pool.is_stopped:
            self._pool.start()
        self._worker = self._pool.add_task(self._download_file, self._server,
            self._model['context']['project'], code, self._generation)
        self._worker.result.connect(self._download_done)
        self._worker.start()

    @staticmethod
    def _download_file(server, project, code, generation):
        try:
            server = project_server(server, project)
            directory = Path(tempfile.mkdtemp(prefix='tactic-agent-download-'))
            offset = 0
            while True:
                result = server.execute_cmd('tactic.ui.panel.agent_attachment_cmd.AgentAttachmentCmd',
                    dict(action='read', project_code=project, attachment_id=code, offset=offset))
                if result.get('status') != 'OK':
                    raise RuntimeError('Attachment download failed')
                result = json.loads(result['info']) if isinstance(result['info'], str) else result['info']
                name = Path(result['name']).name
                with (directory / name).open('wb' if offset == 0 else 'ab') as output:
                    output.write(base64.b64decode(result['data'], validate=True))
                offset = result['next_offset']
                if offset is None:
                    break
            return dict(generation=generation, directory=str(directory))
        except Exception as error:
            return dict(generation=generation, error=str(error))

    @Slot(object)
    def _download_done(self, result):
        from PySide6.QtGui import QDesktopServices
        if isinstance(result, tuple):
            result = result[0]
        if result['generation'] != self._generation:
            return
        self._in_flight = False
        self._worker = None
        self._model.update(busy=False, error=result.get('error', ''))
        if 'directory' in result:
            QDesktopServices.openUrl(QUrl.fromLocalFile(result['directory']))
        self.changed.emit()
        self._timer.start()

    def _request(self, action):
        if self._in_flight:
            if action != 'poll' and not self._model['busy']:
                self._queued_action = action
                self._model['busy'] = True
                self.changed.emit()
            return
        if self._server is None:
            return
        if self._pool is None:
            self._model['error'] = 'Agent request worker is unavailable'
            self.changed.emit()
            return
        self._generation += 1
        self._in_flight = True
        self._model['busy'] = action != 'poll'
        if action != 'poll':
            self._model['error'] = ''
        self.changed.emit()
        pool = self._pool
        if pool.is_stopped:
            pool.start()
        self._worker = pool.add_task(self._load, self._server, self._model['context']['project'],
            action, self._model['selected'], deepcopy(self._model['pending']), self._generation, set(self._model['previews']),
            dict(query=self._model['history']['query'],archived=self._model['history']['archived'],project_filter=self._model['history'].get('project',''),
                **(dict(offset=self._model['next_offset']) if action=='historyMore' else {})),
            deepcopy(self._library_operation),deepcopy(self._model['attachments']))
        self._worker.result.connect(self._done)
        self._worker.start()

    @staticmethod
    def _load(server, project, action, selected, pending, generation, cached_previews=(), history_filter=None, library_operation=None, draft_attachments=()):
        reading=False
        try:
            if action=='library' and library_operation['action']=='draft':
                project=library_operation['values']['context']['project']
            history_filter=dict(history_filter or dict(query='',archived=False))
            def call(action, target=None, **values):
                target=target or project
                result = project_server(server,target).execute_cmd(COMMAND, dict(action=action, project_code=target, **values))
                if not isinstance(result, dict):
                    raise RuntimeError('Agent request failed')
                if result.get('status') != 'OK':
                    raise RuntimeError(result.get('description') or 'Agent request failed')
                return json.loads(result['info']) if isinstance(result['info'], str) else result['info']
            if action.startswith('executor_'):
                result = project_server(server, project).execute_cmd('tactic.ui.panel.agent_executor_cmd.AgentExecutorCmd',
                    dict(action=action.split(':')[0].removeprefix('executor_'), target=action.split(':')[1], project_code=project))
                if result.get('status') != 'OK':
                    raise RuntimeError(result.get('description') or 'Agent connection failed')
            if action == 'send':
                selected = (call('submit', **pending) if 'document' in pending else call('message', request_id=selected, **pending))['request_id']
            elif action == 'cancel':
                call('cancel', request_id=selected)
            elif action == 'undo':
                call('undo', request_id=selected, **pending)
            elif action=='library':
                saved=call(library_operation['action'],target=library_operation.get('project'),**library_operation['values'])
                if library_operation['action']=='draft':
                    selected=saved['request_id']
                    history_filter=dict(query='',archived=False,project_filter=history_filter.get('project_filter',''))
            reading=True
            state = call('state')
            state.update(call('library',**history_filter))
            current = call('read', request_id=selected) if selected else {}
            previews = {}
            for message in [*current.get('messages', []),dict(attachments=draft_attachments)]:
                for file in message.get('attachments', []):
                    code = file['attachment_id']
                    if not file['media_type'].startswith('image/') or code in cached_previews:
                        continue
                    try:
                        result = project_server(server,project).execute_cmd('tactic.ui.panel.agent_attachment_cmd.AgentAttachmentCmd',
                            dict(action='preview', project_code=project, attachment_id=code))
                        value = json.loads(result['info']) if isinstance(result['info'], str) else result['info']
                        previews[code] = value['url']
                    except Exception:
                        previews[code] = ''
            return dict(generation=generation, selected=selected, request=current, action=action, previews=previews,
                history_filter=history_filter,library_operation=library_operation, **state)
        except Exception as error:
            return dict(generation=generation, error=str(error), refresh_error=reading)

    @Slot(object)
    def _done(self, result):
        if isinstance(result, tuple):
            result = result[0]
        if result['generation'] != self._generation:
            return
        self._worker = None
        self._in_flight = False
        self._model['busy'] = False
        history_filter=result.get('history_filter',{})
        if 'error' not in result and result.get('action')!='library' and any(
                history_filter.get(field,self._model['history'].get(key,''))!=self._model['history'].get(key,'')
                for field,key in (('query','query'),('archived','archived'),('project_filter','project'))):
            self._queued_action=''
            self.changed.emit()
            self._request('refresh')
            return
        if 'error' in result:
            self._model['refreshError' if result.get('refresh_error') else 'error'] = result['error']
        if 'error' not in result:
            self._model['refreshError']=''
            was_active = self._model['request'].get('status') in ('queued', 'running', 'cancelling') and self._model['request'].get('request_id')==result['request'].get('request_id')
            if result.get('action') in ('poll','historyMore'):
                records={row.get('key',row.get('project','')+':'+row['request_id']):row for row in [*self._model['requests'],*result['requests']]}
                result['requests']=list(records.values())
                if result['action']=='poll' and self._model['requests']:
                    result['next_offset']=self._model['next_offset']
            if result.get('action')=='library':
                operation=result['library_operation']
                if operation['action']=='draft':
                    self._model['drafts'][self._draft_key(self._model['selected'])]=self._draft()
                    if self._model['context']['project']!=result['request']['document']['context']['project']:
                        self._model['previews']={}
                    self._model['context']=result['request']['document']['context']
                    if not operation.get('edit'):
                        self._restore_draft(result['selected'], fresh=True)
                    self._model['history'].update(query='',archived=False)
                self._model['history']['edit']=None
            self._model.update({key: result[key] for key in ('selected', 'request', 'hosts', 'requests')})
            self._model['executor'] = result.get('executor', {})
            if getattr(self.application, 'agent_desktop', None):
                self._model['executor'] = self.application.agent_desktop.decorate(self._model['executor'])
            self._model.update({key:result[key] for key in ('groups','groups_revision','group_revisions','projects','unavailable_projects','total','next_offset') if key in result})
            if result['request']:
                self._model['context']=result['request']['document']['context']
            if result.get('action')=='library' and result['library_operation'].get('edit'):
                row=self._model['request']['library_summary']
                self._model['history'].update(visible=True,edit=dict(kind='chat',id=row['request_id'],project=self._model['context']['project'],title='' if row.get('default_title') else row['title'],
                    group=row['group'],pinned=row['pinned'],archived=row['archived'],revision=row['library_revision'],status=row['status']))
            self._model['previews'].update(result.get('previews', {}))
            if was_active and result['request'].get('status') not in ('queued', 'running', 'cancelling'):
                terminal = result['request']
                source = ({'completed': 'Task completed', 'blocked': 'Task blocked — see the answer', 'needs_input': 'Waiting for your reply'}.get(
                    terminal.get('outcome'), 'Agent finished — review the answer') if terminal['status'] == 'completed' else
                    {'cancelled': 'Request cancelled', 'failed': 'Request failed', 'interrupted': 'Request interrupted'}.get(terminal['status'], 'Agent finished — review the answer'))
                self.application.notification_changed.emit(QCoreApplication.translate('AgentRequestView', source))
            if result.get('action') in ('send', 'undo'):
                self._model['pending'] = None
            if result.get('action') == 'send':
                self._model['drafts'].pop(self._draft_key(self._model['selected']),None)
                self._model['prompt'] = ''
                self._model['attachments'] = []
        self.changed.emit()
        if self._queued_action:
            action, self._queued_action = self._queued_action, ''
            self._request(action)
            return
        if self.application.window_model.is_window_visible('agent_request') or self._model['request'].get('status') in ('queued', 'running', 'cancelling'):
            self._timer.start()
