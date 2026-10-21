"""Dependency transport; the shared Frame module owns tree state and layout."""
from copy import deepcopy

from PySide6.QtCore import QObject, Signal, Slot, Qt


class DependencyViewerController(QObject):
    received = Signal(str, 'QVariantMap', str)
    fileFailed = Signal(str)

    def __init__(self, services, parent=None):
        super().__init__(parent)
        self.services = services
        self.application = services._application
        self._generation = 0
        self._workers = set()
        self.application.window_model.windowVisibilityChanged.connect(self._visibility_changed)
        self.services.documentChanged.connect(self._document_changed)

    @Slot(str, 'QVariantMap')
    def open(self, node_id: str, cell: dict) -> None:
        node = self.application._node_for_any(node_id)
        if node is None:
            return
        self.shutdown()
        scope = self.services._owner_scope(node_id)
        project = (scope.descriptor.get('projectCode') if scope else '') or self.application._current_project_code
        self.services._document_generation += 1
        self.services._document = dict(kind='dependencies', title='Dependencies', translateTitle=True, nodeId=node_id,
            searchKey=cell.get('targetSearchKey') or node.search_key,
            projectCode=cell.get('projectCode') or project, generation=self._generation)
        self.services.documentChanged.emit()
        self.application.open_window('table_document')

    @Slot('QVariantMap')
    def request(self, request: dict) -> None:
        from thlib import tactic_classes as tc
        from .requests import read_dependency_node

        if self.services.document.get('kind') != 'dependencies':
            return
        project, path = request['projectCode'], request['path']
        arguments = {name: request[name] for name in
            ('search_key', 'offset', 'limit', 'expected_revision', 'file_index') if name in request}
        try:
            server = tc.server_start(project=project)
        except (PermissionError, ValueError) as error:
            self.received.emit(path, {}, str(error))
            return
        self._run(lambda: tc.execute_procedure_serverside(read_dependency_node, arguments,
            project=project, server=server),
            lambda result: self.received.emit(path, result, ''),
            lambda error: self.received.emit(path, {}, str(error)))

    @Slot('QVariantMap')
    def open_file(self, action: dict) -> None:
        from thlib import tactic_classes as tc
        from .requests import read_snapshot_files

        if self.services.document.get('kind') != 'dependencies':
            return
        project = action['projectCode']
        try:
            server = tc.server_start(project=project)
        except (PermissionError, ValueError) as error:
            self.fileFailed.emit(str(error))
            return

        def read():
            data = tc.execute_procedure_serverside(read_snapshot_files,
                dict(search_key=action['snapshotKey'], file_code=action['fileCode'], expected_revision=action['revision']),
                project=project, server=server)
            files = tc.Snapshot(deepcopy(data)).get_files_objects()
            return next(file for file in files if file.get_code() == action['fileCode'])

        self._run(read, self.application.open_file_object, lambda error: self.fileFailed.emit(str(error)))

    def _run(self, operation, accept, reject):
        from thlib.environment import env_inst

        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            reject('Server worker is unavailable')
            return
        generation = self._generation
        self._workers.add(worker)

        def loaded(result):
            if generation == self._generation:
                try:
                    accept(result)
                except (KeyError, TypeError, ValueError, LookupError, OSError) as error:
                    reject(error)

        def failed(payload):
            if generation == self._generation:
                error = payload[0].get('exception') or 'Snapshot is no longer available'
                if self.application.debug_log:
                    self.application.debug_log.raise_error(error,
                        stacktrace=payload[0].get('stacktrace', ''), group='table/dependencies')
                from xmlrpc.client import Fault
                reject(error.faultString if isinstance(error, Fault) else str(error))

        worker.result.connect(loaded, Qt.QueuedConnection)
        worker.error.connect(failed, Qt.QueuedConnection)
        worker.settled.connect(lambda _worker: self._workers.discard(worker), Qt.QueuedConnection)
        worker.start()

    def _visibility_changed(self, window_id, visible):
        if window_id == 'table_document' and not visible:
            self.shutdown()

    def _document_changed(self):
        if self.services.document.get('kind') != 'dependencies':
            self.shutdown()

    @Slot()
    def restart_reads(self) -> None:
        self.shutdown()

    @Slot()
    def shutdown(self) -> None:
        self._generation += 1
        for worker in tuple(self._workers):
            worker.cancel()
