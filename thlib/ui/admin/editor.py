"""Async native-document lifecycle shared by the administration editors."""

from __future__ import annotations

import copy
from collections.abc import Callable

from PySide6.QtCore import QObject, Property, Qt, Signal, Slot


class AdminDocumentEditor(QObject):
    stateChanged = Signal()
    committed = Signal()

    def __init__(self, application, endpoint: Callable, parent=None) -> None:
        super().__init__(parent)
        self._application = application
        self._endpoint = endpoint
        self._project = ''
        self._catalog = []
        self._metadata = {}
        self._identity = ''
        self._document = {}
        self._original = {}
        self._revision = ''
        self._error = ''
        self._project_unavailable = False
        self._can_write = False
        self._loaded = False
        self._worker = None
        self._callbacks = None
        self._generation = 0
        self._closed = False

    @Property('QVariantList', notify=stateChanged)
    def catalog(self):
        return self._catalog

    @Property('QVariantMap', notify=stateChanged)
    def document(self):
        return self._document

    @Property('QVariantMap', notify=stateChanged)
    def metadata(self):
        return self._metadata

    @Property(str, notify=stateChanged)
    def identity(self):
        return self._identity

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Property(bool, notify=stateChanged)
    def projectUnavailable(self):
        return self._project_unavailable

    @Property(bool, notify=stateChanged)
    def dirty(self):
        return self._document != self._original

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._worker is not None

    @Property(bool, notify=stateChanged)
    def canWrite(self):
        return self._can_write

    def activate(self, project: str) -> None:
        if project != self._project:
            self.reset(project)
        if not self._loaded and project and not self.busy:
            self.reload()

    def reset(self, project: str = '') -> None:
        self._generation += 1
        self._release(cancel=True)
        self._project = project
        self._loaded = False
        self._catalog = []
        self._metadata = {}
        self._identity = ''
        self._document = self._original = {}
        self._revision = ''
        self._can_write = False
        self._error = ''
        self._project_unavailable = False
        self._document_loaded()
        self.stateChanged.emit()

    def _release(self, cancel=False):
        if self._worker:
            if self._callbacks:
                self._worker.result.disconnect(self._callbacks[0])
                self._worker.error.disconnect(self._callbacks[1])
            if cancel:
                self._worker.cancel()
        self._worker = self._callbacks = None

    def _execute_request(self, arguments: dict, project: str, original: dict) -> dict:
        from thlib import tactic_classes as tc
        return tc.execute_procedure_serverside(self._endpoint, arguments, project=project)

    def _catalog_loaded(self) -> None:
        """Publish a domain catalog after a successful worker response."""

    def _request(self, action: str, identity: str = '', **parameters) -> None:
        from thlib import server_cache
        from thlib.environment import env_inst
        if self.busy or self._closed:
            return
        if not self._application.can_administer:
            self.fail(self.tr('Administration requires administrator access'))
            return
        self._generation += 1
        generation = self._generation
        project = self._project
        endpoint = self._endpoint
        args = {'action': action, 'project_code': project, 'identity': identity,
                'document': copy.deepcopy(self._document) if action == 'save' else None,
                'expected_revision': self._revision, **copy.deepcopy(parameters)}
        original = copy.deepcopy(self._original)
        self._error = ''
        self._project_unavailable = False

        def operation():
            result = self._execute_request(args, project, original)
            if action == 'save':
                server_cache.invalidate_domains(('reference', 'search', 'relations', 'tasks'), project)
                server_cache.invalidate_domains(('reference',), 'sthpw')
            return result

        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            self.fail(self.tr('Server worker pool is unavailable'))
            return
        self._worker = worker

        def loaded(result):
            if self._closed or generation != self._generation:
                return
            self._release()
            self._loaded = True
            self._catalog = result.get('catalog', self._catalog)
            self._metadata = result.get('metadata', {})
            self._can_write = bool(result.get('canWrite'))
            self._catalog_loaded()
            if action == 'list':
                if not self._catalog:
                    self._identity = self._revision = ''
                    self._document = {}
                    self._original = {}
                    self._document_loaded()
                self.stateChanged.emit()
                if self._catalog:
                    selected = self._identity if any(
                        row['identity'] == self._identity for row in self._catalog) else self._catalog[0]['identity']
                    self._request('load', selected)
                return
            self._identity = result['identity']
            self._revision = result['revision']
            self._document = copy.deepcopy(result['document'])
            self._original = copy.deepcopy(self._document)
            self._document_loaded()
            self.stateChanged.emit()
            if action == 'save':
                self.committed.emit()

        def failed(error):
            if self._closed or generation != self._generation:
                return
            self._release()
            payload, _worker = error
            exception = payload.get('exception') or error
            detail = str(exception)
            folded = detail.casefold()
            self._project_unavailable = (
                'database [' in folded and '] does not exist' in folded
            )
            if self._project_unavailable:
                self.fail(self.tr(
                    'Project "%s" is unavailable because its database no longer exists. '
                    'Choose another project.') % self._project)
            else:
                self.fail(detail)
            if self._application.debug_log:
                self._application.debug_log.raise_error(
                    exception,
                    stacktrace=payload.get('stacktrace', ''),
                    group='administration/' + endpoint.__name__)

        self._callbacks = loaded, failed
        worker.result.connect(loaded, Qt.QueuedConnection)
        worker.error.connect(failed, Qt.QueuedConnection)
        self.stateChanged.emit()
        worker.start()

    def fail(self, error: str) -> None:
        self._error = str(error)
        self.stateChanged.emit()

    def _document_loaded(self) -> None:
        """Domain editors rebuild their projection after load or discard."""

    @Slot(str)
    def select(self, identity: str) -> None:
        if not self.busy and not self.dirty and identity != self._identity:
            self._request('load', identity)

    @Slot()
    def reload(self) -> None:
        if not self.busy and not self.dirty:
            self._request('list')

    @Slot()
    def discard(self) -> None:
        if not self.busy:
            self._document = copy.deepcopy(self._original)
            self._error = ''
            self._document_loaded()
            self.stateChanged.emit()

    @Slot(str, 'QVariant')
    def set_field(self, name: str, value) -> None:
        if not self.busy and self._can_write and name in self._document:
            self._document[name] = value
            self.stateChanged.emit()

    @Slot()
    def save(self) -> None:
        if self._can_write and self.dirty and not self.busy:
            self._request('save', self._identity)

    def shutdown(self) -> None:
        self._closed = True
        self._generation += 1
        self._release(cancel=True)
