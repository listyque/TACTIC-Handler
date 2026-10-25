"""Native agent requests with captured context and background transport."""
from copy import deepcopy
import json
from uuid import uuid4

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot

COMMAND = 'tactic.ui.panel.agent_request_cmd.AgentRequestCmd'


class AgentRequestController(QObject):
    changed = Signal()

    def __init__(self, application, server_pool):
        super().__init__(application)
        self.application = application
        self._pool = server_pool
        self._generation = 0
        self._server = None
        self._worker = None
        self._in_flight = False
        self._timer = QTimer(self)
        self._timer.setInterval(2500)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(lambda: self._request('poll'))
        self._model = self.initial()
        application._registry.register('open_agent_request', self.open)
        application.authentication_changed.connect(self.reset)
        application.signing_out.connect(self.reset)
        application.window_model.windowVisibilityChanged.connect(self.visibility)

    @staticmethod
    def initial(context=None):
        return dict(context=context or {}, prompt='', allowChanges=False, hosts=[], requests=[], selected='',
                    request={}, busy=False, error='', pending=None)

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
                self._timer.stop()

    @Slot()
    def refresh(self):
        self._request('refresh')

    @Slot(str, 'QVariant')
    def handle(self, action, value=''):
        if self._model['busy']:
            return
        if action in ('prompt', 'changes'):
            if self._model['selected'] or self._model['pending']:
                return
            self._model['prompt' if action == 'prompt' else 'allowChanges'] = str(value) if action == 'prompt' else bool(value)
            self.changed.emit()
        elif action == 'select':
            self._generation += 1
            self._in_flight = False
            if not value:
                self._model = self.initial(self.capture())
                self._capture_session()
                self.changed.emit()
            else:
                self._model.update(selected=str(value), request={}, pending=None)
            self.refresh()
        elif action == 'send':
            hosts = [host for host in self._model['hosts'] if not self._model['allowChanges'] or host['capabilities']['changes']]
            if not self._model['selected'] and self._model['prompt'].strip() and hosts:
                self._model['pending'] = self._model['pending'] or dict(request_id=str(uuid4()), host_id=hosts[0]['host_id'],
                    document=dict(prompt=self._model['prompt'], context=deepcopy(self._model['context']), allow_changes=self._model['allowChanges']))
                self._request('send')
        elif action in ('refresh', 'cancel'):
            self._request(action)

    def _request(self, action):
        if self._in_flight or self._server is None:
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
                selected = call('submit', **pending)['request_id']
            elif action == 'cancel':
                call('cancel', request_id=selected)
            state = call('state')
            current = call('read', request_id=selected) if selected else {}
            return dict(generation=generation, selected=selected, request=current, **state)
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
            self._model.update({key: result[key] for key in ('selected', 'request', 'hosts', 'requests')})
            if result['selected']:
                self._model['pending'] = None
        self.changed.emit()
        if self.application.window_model.is_window_visible('agent_request'):
            self._timer.start()
