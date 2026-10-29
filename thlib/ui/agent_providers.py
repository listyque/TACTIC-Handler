"""Native provider profile editor; its model never contains stored credentials."""
from copy import deepcopy
import json

from PySide6.QtCore import QObject, Property, Signal, Slot, QTimer

COMMAND = 'tactic.ui.panel.agent_provider_cmd.AgentProviderCmd'


class AgentProvidersController(QObject):
    changed = Signal()

    def __init__(self, application, pool, parent=None):
        super().__init__(parent)
        self.application, self.pool = application, pool
        self._generation, self._server, self._project, self._worker = 0, None, '', None
        self._model = self.initial()
        self._embedded_active = False
        self._timer = QTimer(self)
        self._timer.setInterval(2000)
        self._timer.timeout.connect(self._poll)
        application._registry.register('open_agent_providers', self.open)
        application.authentication_changed.connect(self.reset)
        application.signing_out.connect(self.reset)
        application.window_model.windowVisibilityChanged.connect(self.visibility)

    @staticmethod
    def initial():
        return dict(profiles=[], kinds=[], default='codex', revision='', selected='codex', draft={}, baseline={}, busy=False, error='', notice='')

    @Property('QVariantMap', notify=changed)
    def model(self):
        return deepcopy(self._model)

    def dirty(self):
        return self._model['draft'] != self._model['baseline']

    def select(self, code):
        row = next((row for row in self._model['profiles'] if row['id']==code), {})
        draft = dict(name=row.get('name',''),kind=row.get('kind','compatible'),url=row.get('url',''),secret='',
            secret_env=row.get('secret_env',''),clear_secret=False,enabled=row.get('enabled',True),
            default_model=row.get('default_model',''),default=code==self._model['default'])
        self._model.update(selected=code,draft=draft,baseline=deepcopy(draft),error='',notice='')

    @Slot()
    def open(self):
        if self.activate():
            self.application.window_model.show_window('agent_providers')

    def activate(self):
        if not self.application.can_administer:
            self._model['error'] = 'Administrator access required'
            self.changed.emit()
            return False
        project = self.application.current_project_code
        if not project:
            self.application.notification_changed.emit('Select a project before configuring the agent')
            return False
        if not self._server:
            from thlib import tactic_classes as tc
            try:
                self._server = tc.server_start(project=project)
                self._project = project
            except PermissionError as error:
                self._model['error'] = str(error)
                self.changed.emit()
        if not self._model['busy'] and (not self.dirty() or not self._model['revision']):
            self.request('state')
        return True

    @Slot(bool)
    def set_embedded_active(self, active):
        self._embedded_active = active
        if active:
            self.activate()
        elif not self.application.window_model.is_window_visible('agent_providers'):
            self._timer.stop()

    @Slot()
    def reset(self):
        self._generation += 1
        self._timer.stop()
        self._embedded_active = False
        self._server, self._project = None, ''
        self._model = self.initial()
        self.application.window_model.close_window('agent_providers')
        self.changed.emit()

    @Slot(str, bool)
    def visibility(self, code, visible):
        if code=='agent_providers' and not visible and not self._embedded_active:
            self._timer.stop()

    @Slot('QVariantMap')
    def handle(self, action):
        if self._model['busy']:
            return
        kind = action.get('type')
        if kind=='field':
            field, value = action['field'], action.get('value')
            if field not in self._model['draft']:
                return
            self._model['draft'][field] = value
            if field=='kind':
                self._model['draft']['url'] = next((row['url'] for row in self._model['kinds'] if row['value']==value),'')
            self._model.update(error='',notice='')
        elif kind in ('select','new') and not self.dirty():
            self.select(action.get('value','') if kind=='select' else '')
        elif kind=='reset':
            self.select(self._model['selected'])
        elif kind=='refresh' and not self.dirty():
            self.request('state')
        elif kind in ('save','check','remove'):
            values = dict(provider=self._model['selected'],expected_revision=self._model['revision'])
            if kind=='save':
                values['document'] = deepcopy(self._model['draft'])
            self.request(kind, values)
        self.changed.emit()

    def request(self, action, values=None):
        if not self._server or self._model['busy']:
            return
        self._generation += 1
        self._model.update(busy=True,error='')
        self._timer.stop()
        if self.pool.is_stopped:
            self.pool.start()
        self._worker = self.pool.add_task(self.load,self._server,self._project,action,values or {},self._generation)
        self._worker.result.connect(self.done)
        self._worker.start()
        self.changed.emit()

    @staticmethod
    def load(server,project,action,values,generation):
        try:
            result = server.execute_cmd(COMMAND,dict(action=action,project_code=project,**values))
            if result.get('status')!='OK':
                raise RuntimeError(result.get('description') or 'Provider settings could not be loaded')
            info = json.loads(result['info']) if isinstance(result['info'],str) else result['info']
            return dict(generation=generation,action=action,info=info)
        except Exception as error:
            return dict(generation=generation,error=str(error))

    @Slot(object)
    def done(self,result):
        if isinstance(result,tuple):
            result=result[0]
        if result['generation']!=self._generation:
            return
        self._worker=None
        self._model.update(busy=False,error=result.get('error',''))
        if 'info' in result:
            old = {row['id'] for row in self._model['profiles']}
            selected = self._model['selected']
            info = result['info']
            if result['action']=='save' and not selected:
                selected=next((row['id'] for row in info['profiles'] if row['id'] not in old),info['default'])
            self._model.update(info)
            self.select(selected if any(row['id']==selected for row in info['profiles']) else info['default'])
            if result['action']=='check':
                self._model['notice']='Waiting for the external host'
            if (self._embedded_active or self.application.window_model.is_window_visible('agent_providers')) and any(row['status']=='waiting' for row in info['profiles']):
                self._timer.start()
        self.changed.emit()

    def _poll(self):
        if not self.dirty():
            self.request('state')
