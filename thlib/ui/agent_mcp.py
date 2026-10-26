"""Owner-managed project MCP access in an ordinary native functional window."""
from copy import deepcopy
from datetime import datetime
import json
from urllib.parse import urljoin

from PySide6.QtCore import QObject, Property, Signal, Slot

COMMAND = 'tactic.ui.panel.agent_mcp_cmd.AgentMcpCmd'


class AgentMcpController(QObject):
    changed = Signal()

    def __init__(self, application, pool, parent=None):
        super().__init__(parent)
        self.application, self.pool = application, pool
        self._generation, self._server, self._context, self._origin = 0, None, {}, ''
        self._model = self.initial()
        application.authentication_changed.connect(self.reset)
        application.signing_out.connect(self.reset)
        application.project_changed.connect(lambda *_: self.reset())
        application.window_model.windowVisibilityChanged.connect(self.visibility)

    @staticmethod
    def initial():
        return dict(connections=[], tools=[], selected=[], enabled=False, title='', instructions='',
                    minutes='60', busy=False, error='', issued='')

    @Property('QVariantMap', notify=changed)
    def model(self):
        return deepcopy(self._model)

    @Slot('QVariantMap')
    def open(self, context):
        self.reset()
        if not self.application.can_administer or not context.get('project'):
            return
        from thlib import tactic_classes as tc
        from .agent_request import project_server
        try:
            self._server = project_server(tc.server_start(project=context['project']), context['project'])
        except PermissionError as error:
            self.application.notification_changed.emit(str(error))
            return
        self._context = deepcopy(context)
        self._origin = self.application.server_url
        self._model['project'] = context['project']
        self.application.window_model.show_window('agent_mcp')
        self.request('state')

    @Slot()
    def reset(self):
        self._generation += 1
        self._server, self._context, self._origin = None, {}, ''
        self._model = self.initial()
        self.application.window_model.close_window('agent_mcp')
        self.changed.emit()

    @Slot(str, bool)
    def visibility(self, code, visible):
        if code == 'agent_mcp' and not visible:
            self._generation += 1
            self._model['issued'] = ''
            self.changed.emit()

    @Slot('QVariantMap')
    def handle(self, action):
        if self._model['busy']:
            return
        kind = action.get('type')
        if kind == 'field' and action.get('field') in ('title', 'instructions', 'minutes'):
            self._model[action['field']] = action.get('value', '')
        elif kind == 'tool':
            selected = set(self._model['selected'])
            if action.get('value'):
                selected.add(action['name'])
            else:
                selected.discard(action['name'])
            self._model['selected'] = sorted(selected)
        elif kind == 'readonly':
            self._model['selected'] = [tool['name'] for tool in self._model['tools'] if tool['readonly']]
        elif kind == 'clear':
            self._model['selected'] = []
        elif kind == 'refresh':
            self.request('state')
        elif kind in ('revoke', 'reveal'):
            self.request(kind, dict(id=action['id']))
        elif kind == 'copy':
            from PySide6.QtGui import QGuiApplication
            QGuiApplication.clipboard().setText(self._model['issued'])
        elif kind == 'create':
            self.request('create', dict(title=self._model['title'], instructions=self._model['instructions'],
                minutes=int(self._model['minutes']), tools=list(self._model['selected']), context=deepcopy(self._context)))
        self.changed.emit()

    def request(self, action, values=None):
        if not self._server or self._model['busy']:
            return
        self._generation += 1
        self._model.update(busy=True, error='')
        if self.pool.is_stopped:
            self.pool.start()
        worker = self.pool.add_task(self.load, self._server, self._context['project'], action, values or {}, self._generation)
        worker.result.connect(self.done)
        worker.start()
        self.changed.emit()

    @staticmethod
    def load(server, project, action, values, generation):
        try:
            result = server.execute_cmd(COMMAND, dict(action=action, project_code=project, **values))
            if result.get('status') != 'OK':
                raise RuntimeError(result.get('description') or 'MCP connections could not be loaded')
            info = json.loads(result['info']) if isinstance(result['info'], str) else result['info']
            return dict(generation=generation, action=action, info=info)
        except Exception as error:
            return dict(generation=generation, error=str(error))

    @Slot(object)
    def done(self, result):
        if isinstance(result, tuple):
            result = result[0]
        if result['generation'] != self._generation:
            return
        self._model.update(busy=False, error=result.get('error', ''))
        if 'info' in result:
            info = result['info']
            if result['action'] in ('create', 'reveal'):
                self._model['issued'] = json.dumps(dict(url=urljoin(self._origin, info['path']),
                    headers=dict(Authorization='Bearer ' + info['token'])), indent=2)
                self.request('state')
            else:
                now = datetime.now().timestamp()
                self._model.update(info)
                self._model['connections'] = [dict(item, expired=item['expires'] <= now,
                    expiresLabel=datetime.fromtimestamp(item['expires']).strftime('%Y-%m-%d %H:%M')) for item in info['connections']]
        self.changed.emit()
