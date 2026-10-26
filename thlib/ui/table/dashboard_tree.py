"""Native transport and lifecycle for the portable configured hierarchy."""
from pathlib import Path
from copy import copy
from PySide6.QtCore import QObject, Property, Signal, Slot, Qt
from PySide6.QtQml import QJSEngine


class DashboardTreeController(QObject):
    changed = Signal()

    def __init__(self, owner, tree: dict):
        super().__init__(owner)
        self.owner = owner
        self.project = owner.context['project']
        self.engine = QJSEngine(self)
        self.module = self.engine.importModule(str(Path(__file__).parents[1] / 'qml/tactic_frame/features/table/tree.ui.mjs'))
        if self.module.isError():
            raise RuntimeError(self.module.toString())
        self._model = self.call('initial', tree)
        self._generation = 0
        self._workers = set()

    def call(self, name: str, *values) -> dict:
        result = self.module.property(name).call([self.engine.toScriptValue(value) for value in values])
        if result.isError():
            raise RuntimeError(result.toString())
        return result.toVariant()

    @Property('QVariantMap', notify=changed)
    def model(self) -> dict:
        return self._model

    @Slot('QVariantMap')
    def activate(self, action: dict) -> None:
        if action.get('type') == 'inspect':
            self.owner.services._application.open_rich_link('skey://' + action['key'])
            return
        change = self.call('change', self._model, action)
        self._model = change['model']
        self.changed.emit()
        if change.get('request'):
            self.read(change['request'])

    def read(self, request: dict) -> None:
        from thlib import tactic_classes as tc
        from thlib.environment import env_inst
        generation = self._generation
        def settled(result=None, error=''):
            if generation == self._generation:
                self._model = self.call('accept', self._model, request, result, error)
                self.changed.emit()
        try:
            server = copy(tc.server_start(project=self.project))
            server.set_project(self.project)
        except PermissionError as error:
            settled(error=str(error))
            return
        values = {key: request[key] for key in ('tree', 'branch_path', 'parent_key', 'offset', 'limit')}
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(lambda: server.execute_cmd(
            'tactic.ui.panel.dashboard_cmd.DashboardCmd', dict(action='tree',project_code=self.project,**values))['info'])
        if worker is None:
            settled(error=self.tr('Server worker is unavailable'))
            return
        self._workers.add(worker)
        worker.result.connect(settled, Qt.QueuedConnection)
        def failed(error):
            payload=error[0]
            logger=getattr(self.owner.services._application,'debug_log',None)
            if generation==self._generation and logger:
                logger.raise_error(payload.get('exception') or error,
                    stacktrace=payload.get('stacktrace',''),group='dashboard/tree')
            settled(error=str(payload.get('exception') or error))
        worker.error.connect(failed, Qt.QueuedConnection)
        worker.finished.connect(lambda:self._workers.discard(worker))
        worker.start()

    def shutdown(self) -> None:
        self._generation += 1
        for worker in tuple(self._workers):
            worker.cancel()
