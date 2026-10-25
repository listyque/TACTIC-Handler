"""Native agent requests with captured context and background transport."""
from copy import deepcopy
import json
import base64
import mimetypes
from pathlib import Path
import tempfile
from uuid import uuid4

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot, QUrl, QBuffer, QIODevice, QCoreApplication

COMMAND = 'tactic.ui.panel.agent_request_cmd.AgentRequestCmd'


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
        self._timer = QTimer(self)
        self._timer.setInterval(2500)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(lambda: self._request('poll'))
        self._model = self.initial()
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().dataChanged.connect(self.clipboardChanged)
        application._registry.register('open_agent_request', self.open)
        application.authentication_changed.connect(self.reset)
        application.signing_out.connect(self.reset)
        application.window_model.windowVisibilityChanged.connect(self.visibility)

    @staticmethod
    def initial(context=None):
        return dict(context=context or {}, prompt='', allowChanges=False, hosts=[], requests=[], selected='',
                    request={}, busy=False, error='', pending=None, attachments=[], uploading=False, model='', contextExpanded=False, previews={})

    @Property('QVariantMap', notify=changed)
    def model(self):
        return deepcopy(self._model)

    def capture(self):
        app = self.application
        section, tab = app._current_section(), app._current_tab()
        shelf = app.script_shelf_context()
        return dict(client='TH', project=app.current_project_code or '', page=section.entry_key if section else '',
                    title=section.title if section else '', search_type=section.search_type if section else '',
                    view=tab.table_view if tab else '', search_keys=shelf.get('search_keys', []))

    @Slot()
    def reset(self):
        self._generation += 1
        self._in_flight = False
        self._queued_action = ''
        self._timer.stop()
        self._server = None
        self._model = self.initial()
        self.application.window_model.close_window('agent_request')
        self.changed.emit()

    @Slot()
    def open(self):
        if not self.application.can_administer:
            return
        if not self._model['selected'] and not self._model['prompt']:
            self._model = self.initial(self.capture())
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
        if self._model['busy']:
            return
        if action in ('prompt', 'changes'):
            if self._model['pending'] or (action == 'changes' and self._model['selected']):
                return
            self._model['prompt' if action == 'prompt' else 'allowChanges'] = str(value) if action == 'prompt' else bool(value)
            self.changed.emit()
        elif action == 'select':
            if self._model['uploading']:
                return
            self._generation += 1
            self._in_flight = False
            if not value:
                self._model = self.initial(self.capture())
                self._capture_session()
                self.changed.emit()
            else:
                self._model.update(selected=str(value), request={}, pending=None, prompt='', attachments=[], model='')
            self.refresh()
        elif action == 'send':
            allowed = self._model['request'].get('document', {}).get('allow_changes', self._model['allowChanges'])
            hosts = [host for host in self._model['hosts'] if not allowed or host['capabilities']['changes']]
            hosts.sort(key=lambda host: host['host_id'] != self._model['request'].get('host_id'))
            if self._model['prompt'].strip() and hosts and not self._model['uploading']:
                files = [file['attachment_id'] for file in self._model['attachments']]
                self._model['pending'] = self._model['pending'] or (dict(message_id=str(uuid4()), host_id=hosts[0]['host_id'], text=self._model['prompt'],
                    attachments=files, model=self._model['model'] or self._model['request'].get('model', '')) if self._model['selected'] else
                    dict(request_id=str(uuid4()), host_id=hosts[0]['host_id'], document=dict(prompt=self._model['prompt'],
                        context=deepcopy(self._model['context']), allow_changes=self._model['allowChanges'], attachments=files, model=self._model['model'])))
                self._request('send')
        elif action == 'model':
            self._model['model'] = str(value)
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
            action, self._model['selected'], deepcopy(self._model['pending']), self._generation)
        self._worker.result.connect(self._done)
        self._worker.start()

    @staticmethod
    def _load(server, project, action, selected, pending, generation):
        try:
            def call(action, **values):
                result = server.execute_cmd(COMMAND, dict(action=action, project_code=project, **values))
                if not isinstance(result, dict) or result.get('status') != 'OK':
                    raise RuntimeError('Agent request failed')
                return json.loads(result['info']) if isinstance(result['info'], str) else result['info']
            if action == 'send':
                selected = (call('message', request_id=selected, **pending) if selected else call('submit', **pending))['request_id']
            elif action == 'cancel':
                call('cancel', request_id=selected)
            elif action == 'undo':
                call('undo', request_id=selected, **pending)
            state = call('state')
            current = call('read', request_id=selected) if selected else {}
            return dict(generation=generation, selected=selected, request=current, action=action, **state)
        except Exception as error:
            return dict(generation=generation, error=str(error))

    @Slot(object)
    def _done(self, result):
        if isinstance(result, tuple):
            result = result[0]
        if result['generation'] != self._generation:
            return
        self._worker = None
        self._in_flight = False
        self._model['busy'] = False
        if 'error' in result:
            self._model['error'] = result['error']
        if 'error' not in result:
            was_active = self._model['request'].get('status') in ('queued', 'running', 'cancelling')
            self._model.update({key: result[key] for key in ('selected', 'request', 'hosts', 'requests')})
            if was_active and result['request'].get('status') not in ('queued', 'running', 'cancelling'):
                terminal = result['request']
                source = ({'completed': 'Task completed', 'blocked': 'Task blocked — see the answer', 'needs_input': 'Waiting for your reply'}.get(
                    terminal.get('outcome'), 'Agent finished — review the answer') if terminal['status'] == 'completed' else
                    {'cancelled': 'Request cancelled', 'failed': 'Request failed', 'interrupted': 'Request interrupted'}.get(terminal['status'], 'Agent finished — review the answer'))
                self.application.notification_changed.emit(QCoreApplication.translate('AgentRequestView', source))
            if result.get('action') in ('send', 'undo'):
                self._model['pending'] = None
            if result.get('action') == 'send':
                self._model['prompt'] = ''
                self._model['attachments'] = []
        self.changed.emit()
        if self._queued_action:
            action, self._queued_action = self._queued_action, ''
            self._request(action)
            return
        if self.application.window_model.is_window_visible('agent_request') or self._model['request'].get('status') in ('queued', 'running', 'cancelling'):
            self._timer.start()
