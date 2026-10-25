"""Review external-agent drafts inside the ordinary script editor; never execute them here."""
from copy import deepcopy
import json
from uuid import uuid4

from PySide6.QtCore import QObject, Property, Signal, Slot


class AgentDraftsController(QObject):
    changed = Signal()
    activated = Signal()

    def __init__(self, editor):
        super().__init__(editor)
        self._editor = editor
        self._generation = 0
        self._worker = None
        self._pending = None
        self.reset()
        application = editor._application
        if application is not None:
            application.project_changed.connect(self.reset)
            signal = getattr(application, 'authentication_changed', None)
            if signal is not None:
                signal.connect(self.reset)

    @Slot()
    @Slot(str, str)
    def reset(self, *_):
        self._generation += 1
        self._pending = None
        self._model = dict(drafts=[], draft={}, selected='', busy=False, error='', reviewed=False, confirming=False)
        self.changed.emit()

    @Property('QVariantMap', notify=changed)
    def model(self):
        return deepcopy(self._model)

    @Slot()
    def open(self):
        if self._editor.canEdit:
            self._request('refresh')

    @Slot(str, 'QVariant')
    def handle(self, action, value=''):
        if self._model['busy'] or not self._editor.canEdit:
            return
        if action == 'refresh':
            self._request('refresh')
        elif action == 'select':
            self._model['selected'] = str(value)
            self._model.update(draft={}, reviewed=False, confirming=False)
            self._pending = None
            self._request('select')
        elif action == 'reviewed':
            self._model.update(reviewed=bool(value), confirming=False)
            self.changed.emit()
        elif action == 'activate' and not self._model['error'] and self._model['draft'].get('ready') and self._model['reviewed']:
            if not self._model['confirming']:
                self._model['confirming'] = True
                self.changed.emit()
                return
            draft = self._model['draft']
            proposal = dict(draft_id=draft['draft_id'], draft_revision=draft['revision'],
                            expected_revision=draft['dependency_revision'], trial_ids=draft['trial_ids'])
            if self._pending is None or any(self._pending.get(key) != value for key, value in proposal.items()):
                self._pending = dict(proposal, operation_id=str(uuid4()))
            self._request('activate')

    def _request(self, action):
        from thlib.environment import env_inst
        from thlib import tactic_classes as tc
        if self._model['busy']:
            return
        self._generation += 1
        self._model.update(busy=True, error='')
        self.changed.emit()
        pool = env_inst.server_pool
        if pool.is_stopped:
            pool.start()
        try:
            server = tc.server_start(project=self._editor._project_code())
        except Exception as error:
            self._model.update(busy=False, error=str(error))
            self.changed.emit()
            return
        worker = pool.add_task(self._load, server, self._editor._project_code(), action,
            self._model['selected'], deepcopy(self._pending), self._generation)
        worker.result.connect(self._done)
        self._worker = worker
        worker.start()

    @staticmethod
    def _load(server, project, action, selected, pending, generation):
        try:
            def call(action, **values):
                result = server.execute_cmd('tactic.ui.panel.handler_automation_cmd.HandlerAutomationCmd',
                    dict(action=action, project_code=project, **values))
                if not isinstance(result, dict) or result.get('status') != 'OK':
                    raise RuntimeError('Automation request failed')
                return json.loads(result['info']) if isinstance(result['info'], str) else result['info']
            if action == 'activate':
                call('activate', **pending)
            catalog = call('catalog')
            if selected not in {row['draft_id'] for row in catalog['drafts']}:
                selected = catalog['drafts'][0]['draft_id'] if catalog['drafts'] else ''
            draft = call('draft', draft_id=selected) if selected else {}
            return dict(generation=generation, drafts=catalog['drafts'], selected=selected, draft=draft, activated=action == 'activate')
        except Exception as error:
            return dict(generation=generation, error=str(error))

    @Slot(object)
    def _done(self, result):
        if isinstance(result, tuple):
            result = result[0]
        if result['generation'] != self._generation:
            return
        self._worker = None
        self._model.update(busy=False, error=result.get('error', ''))
        if 'error' not in result:
            self._model.update(drafts=result['drafts'], selected=result['selected'], draft=result['draft'], reviewed=False, confirming=False)
            if result['activated']:
                self._pending = None
                self.activated.emit()
        self.changed.emit()
