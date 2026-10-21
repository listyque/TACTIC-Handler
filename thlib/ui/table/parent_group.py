"""Parent chooser transport and existing record-form entry points."""
from copy import deepcopy
from xmlrpc.client import Fault

from PySide6.QtCore import QObject, Property, Signal, Slot, Qt


class ParentGroupController(QObject):
    seedChanged = Signal()
    openChanged = Signal()
    opened = Signal(QObject)
    closed = Signal()
    received = Signal(str, 'QVariantMap', str, bool)

    def __init__(self, services, parent=None):
        super().__init__(parent)
        self.services = services
        self.application = services._application
        self._seed = {}
        self._open = False
        self._generation = 0
        self._workers = set()
        self._tab = None
        self.application.results_view_changed.connect(self._context_changed)

    @Property('QVariantMap', notify=seedChanged)
    def seed(self) -> dict:
        return dict(self._seed)

    @Property(bool, notify=openChanged)
    def isOpen(self) -> bool:
        return self._open

    @Slot(QObject, str, 'QVariantMap', str)
    def open(self, anchor: QObject, node_id: str, cell: dict, dropped_key: str = '') -> None:
        if self._open:
            return
        node = self.application._node_for_any(node_id)
        if node is None or node.source is None or node.search_key != cell.get('targetSearchKey') or not cell.get('parentEditable'):
            self.services.report_error(self.tr('The configured table target is unavailable'))
            return
        if not self.application.can_manage_tools:
            return
        self.shutdown()
        scope = self.services._owner_scope(node_id)
        project = (scope.descriptor.get('projectCode') if scope else '') or self.application._current_project_code
        self._seed = dict(targetSearchKey=node.search_key, sourceId=cell.get('sourceId'),
            projectCode=cell.get('projectCode') or project, sourceTitle=node.title,
            tableView=cell['tableView'], columnName=cell['columnName'],
            sourceRevision=cell['sourceRevision'], dropParentKey=dropped_key)
        self._tab = self.application._current_tab()
        self._open = True
        self.seedChanged.emit()
        self.openChanged.emit()
        self.opened.emit(anchor)

    @Slot('QVariantMap')
    def request(self, request: dict) -> None:
        from thlib import tactic_classes as tc
        from .requests import edit_parent_group
        if not self._open or any(request.get(name) != self._seed[seed] for name, seed in
                (('search_key', 'targetSearchKey'), ('view', 'tableView'), ('column', 'columnName'))):
            return
        arguments = dict(request)
        arguments.pop('projectCode', None)
        operation = arguments['action']
        project = self._seed['projectCode']
        try:
            server = tc.server_start(project=project)
        except (ValueError, PermissionError) as error:
            self.received.emit(operation, {}, str(error), False)
            return
        from thlib.environment import env_inst
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(lambda: tc.execute_procedure_serverside(
            edit_parent_group, arguments, project=project, server=server))
        if worker is None:
            self.received.emit(operation, {}, 'Server worker is unavailable', False)
            return
        generation = self._generation
        self._workers.add(worker)

        def current():
            return generation == self._generation and self._open and self._tab is self.application._current_tab()

        def loaded(result):
            if not current():
                return
            if not isinstance(result, dict):
                self.received.emit(operation, {}, 'Invalid parent response', operation == 'save')
            else:
                self.received.emit(operation, result, '', False)

        def failed(payload):
            if not current():
                return
            error = payload[0].get('exception') or RuntimeError('Invalid parent response')
            if self.application.debug_log:
                self.application.debug_log.raise_error(error,
                    stacktrace=payload[0].get('stacktrace', ''), group='table/parent')
            message = error.faultString if isinstance(error, Fault) else str(error)
            uncertain = operation == 'save' and not isinstance(error, (Fault, ValueError, PermissionError))
            self.received.emit(operation, {}, message, uncertain)

        worker.result.connect(loaded, Qt.QueuedConnection)
        worker.error.connect(failed, Qt.QueuedConnection)
        worker.settled.connect(lambda _worker: self._workers.discard(worker), Qt.QueuedConnection)
        worker.start()

    @Slot(bool)
    def finish(self, saved: bool = False) -> None:
        key = self._seed.get('targetSearchKey')
        self.shutdown()
        if saved and key:
            self.services.completed.emit(key)

    @Slot('QVariantMap')
    def create_child(self, cell: dict) -> None:
        if not self.application.can_manage_tools or not cell.get('parent') or cell['parent'].get('retired'):
            return
        from thlib import tactic_classes as tc
        from thlib.environment import env_inst
        project = cell.get('projectCode') or self.application._current_project_code
        search_type = cell['targetSearchKey'].split('?')[0]
        stype = env_inst.get_stype_by_code(search_type, project_code=project)
        if stype is None:
            self.services.report_error(self.tr('Search Type is not available for this editor'))
            return
        self.application._sobject_editor_request = dict(mode='insert', view='insert', stype=stype,
            sobject=None, parent_sobject=tc.SObject(deepcopy(cell['parent']['record']), project), _prepared=True)
        self.application.open_window('add_sobject')

    def _context_changed(self):
        if self._open and self._tab is not self.application._current_tab():
            self.shutdown()

    @Slot()
    def shutdown(self) -> None:
        self._generation += 1
        for worker in tuple(self._workers):
            worker.cancel()
        was_open = self._open
        self._open = False
        self._seed = {}
        self.seedChanged.emit()
        if was_open:
            self.openChanged.emit()
            self.closed.emit()
