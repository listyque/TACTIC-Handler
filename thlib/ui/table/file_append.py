"""One captured snapshot attachment session; file and server work stays off the UI thread."""
from pathlib import Path
import os
import tempfile
import threading
import uuid

from PySide6.QtCore import QObject, Property, Signal, Slot, Qt, QUrl, QEvent

from thlib.ui.workspace_models.records import RecordListModel


class SnapshotAppendController(QObject):
    changed = Signal()
    completed = Signal(str)

    def __init__(self, application, parent=None):
        super().__init__(parent)
        self._application = application
        self._generation = 0
        self._workers = set()
        self._cancel = threading.Event()
        self._open = False
        self._server = None
        self._scope = {}
        self._source_key = ''
        self._input_window = None
        self._temporary_files = set()
        self.files = RecordListModel(('key', 'index', 'path', 'title', 'size', 'canRemove'))
        self.files.setParent(self)
        self._model = self._empty_model()

    @staticmethod
    def _empty_model() -> dict:
        return dict(append=True, ready=False, busy=False, appendUncertain=False, error='', count=0,
                    process='', context='', processes=[], fileType='attachment', keepFileName=False,
                    discard=False, title='', version=0)

    @Property(bool, notify=changed)
    def isOpen(self) -> bool:
        return self._open

    @Property(bool, notify=changed)
    def busy(self) -> bool:
        return self._model['busy']

    @Property('QVariantMap', notify=changed)
    def model(self) -> dict:
        return dict(self._model, count=self.files.rowCount(), error=self.tr(self._model['error']))

    @Property(QObject, constant=True)
    def fileModel(self) -> QObject:
        return self.files

    @Slot(QObject)
    def attach_window(self, window: QObject) -> None:
        if window is None or window is self._input_window:
            return
        self._detach_input_window()
        self._input_window = window
        window.installEventFilter(self)
        window.destroyed.connect(self._input_window_destroyed)

    @Slot()
    def _input_window_destroyed(self) -> None:
        self._input_window = None

    def _detach_input_window(self) -> None:
        window, self._input_window = self._input_window, None
        if window is not None:
            window.removeEventFilter(self)
            window.destroyed.disconnect(self._input_window_destroyed)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        from PySide6.QtGui import QGuiApplication, QKeySequence
        if (watched is self._input_window and event.type() == QEvent.KeyPress
                and event.matches(QKeySequence.Paste) and self._open
                and self._model['ready'] and not self.busy and not self._model['appendUncertain']):
            mime = QGuiApplication.clipboard().mimeData()
            if mime and mime.hasImage():
                self.activate(dict(type='clipboard'))
                return True
        return False

    def open(self, search_key: str, project: str) -> None:
        from thlib import tactic_classes as tc
        from .requests import append_snapshot_files
        if self._open:
            if search_key != self._source_key:
                self._model['error'] = self.tr('Close the current attachment session before selecting another snapshot')
                self.changed.emit()
            return
        try:
            server = tc.server_start(project=project)
        except PermissionError as error:
            self._application._notify(str(error))
            return
        self._generation += 1
        self._cancel = threading.Event()
        self._open = True
        self._source_key = search_key
        self._server = server
        self._model = self._empty_model()
        self.files.clear()

        def loaded(result):
            self._scope = dict(result)
            self._model.update(ready=True, process=result['process'], context=result['context'],
                processes=[dict(value=result['process'], label=result['process'])],
                title=result['ownerTitle'], version=result['version'])

        self._application.window_model.show_window('snapshot_append')
        self._run(lambda: tc.execute_procedure_serverside(append_snapshot_files,
            dict(search_key=search_key), project=project, server=server), loaded)

    @staticmethod
    def _file_records(values: list) -> list[dict]:
        records, seen = [], set()
        for value in values:
            url = value if isinstance(value, QUrl) else QUrl(str(value))
            if url.isLocalFile():
                source = url.toLocalFile()
            elif url.scheme() and len(url.scheme()) != 1:
                raise ValueError('Choose local files for attachment')
            else:
                source = str(value)
            path = Path(source).resolve(strict=True)
            if not path.is_file():
                raise ValueError('Choose files, not directories')
            key = os.path.normcase(str(path))
            if key in seen:
                continue
            seen.add(key)
            records.append(dict(key=key, path=str(path), title=path.name,
                                size=path.stat().st_size, canRemove=True))
        return records

    def _add_records(self, records: list[dict]) -> None:
        current = self.files.records()
        keys = {os.path.normcase(row['path']) for row in current}
        current.extend(row for row in records if os.path.normcase(row['path']) not in keys)
        if len(current) > 50:
            raise ValueError('Choose between one and 50 files')
        for index, row in enumerate(current):
            row.update(index=index, key=str(index), canRemove=True)
        self.files.replace(current)

    @Slot('QVariantList')
    def add_files(self, values: list) -> None:
        if self.busy or not self._open or not self._model['ready'] or self._model['appendUncertain']:
            return
        captured = list(values)
        self._run(lambda: self._file_records(captured), self._add_records, local=True)

    @Slot('QVariantMap', 'QVariant')
    def activate(self, action: dict, value=None) -> None:
        kind = action.get('type')
        if kind == 'close':
            self.request_close()
        elif kind == 'discard' and not self.busy:
            self.shutdown()
        elif not self.busy:
            if kind == 'continue':
                self._model['discard'] = False
            elif kind == 'field' and action.get('field') in ('fileType', 'keepFileName'):
                self._model[action['field']] = action.get('value')
            elif kind == 'removeFile':
                index = int(action.get('index', -1))
                records = self.files.records()
                if 0 <= index < len(records) and records[index]['path'] == action.get('path'):
                    del records[index]
                    for row_index, row in enumerate(records):
                        row.update(index=row_index, key=str(row_index))
                    self.files.replace(records)
            elif kind == 'clipboard' and self._model['ready'] and not self._model['appendUncertain']:
                self._paste_image()
            elif kind == 'submit':
                self._save()
            self.changed.emit()

    def _paste_image(self):
        from PySide6.QtGui import QGuiApplication
        image = QGuiApplication.clipboard().image().copy()
        if image.isNull():
            self._model['error'] = self.tr('The clipboard does not contain an image')
            return
        def save():
            directory = Path(tempfile.gettempdir()) / 'th_append_clipboard'
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / ('clipboard-' + str(uuid.uuid4()) + '.png')
            try:
                if not image.save(str(path), 'PNG'):
                    raise OSError('Could not save the clipboard image')
                return self._file_records([str(path)])
            except (OSError, ValueError):
                path.unlink(missing_ok=True)
                raise
        def loaded(records):
            self._temporary_files.update(row['path'] for row in records)
            self._add_records(records)
        # Generated images belong only to this draft, including a cancelled late result.
        self._run(save, loaded, local=True, stale=lambda records: self._remove_temporary(row['path'] for row in records))

    @staticmethod
    def _remove_temporary(paths):
        directory = (Path(tempfile.gettempdir()) / 'th_append_clipboard').resolve()
        for value in paths:
            path = Path(value).resolve()
            if path.parent == directory:
                path.unlink(missing_ok=True)

    def _save(self):
        from thlib import tactic_classes as tc
        from .requests import append_snapshot_files
        if not self._model['ready'] or self._model['appendUncertain'] or not self.files.rowCount():
            return
        rows = self.files.records()
        names = [row['title'] for row in rows]
        if len({name.casefold() for name in names}) != len(names) or any(
                name.casefold() in {value.casefold() for value in self._scope['existingNames']} for name in names):
            self._model['error'] = self.tr('Choose file names that are not already in the snapshot')
            return
        server, scope = self._server, dict(self._scope)
        file_type = str(self._model['fileType']).strip()
        keep_name = bool(self._model['keepFileName'])
        if not file_type or len(file_type) > 128 or any(ord(character) < 32 for character in file_type):
            self._model['error'] = self.tr('Choose a valid file type')
            return
        cancel = self._cancel
        write_started = threading.Event()
        def save():
            for row in rows:
                if cancel.is_set():
                    raise InterruptedError('Attachment upload cancelled')
                server.upload_file(row['path'], upload_subdir=scope['uploadDirectory'])
            if cancel.is_set():
                raise InterruptedError('Attachment upload cancelled')
            write_started.set()
            return tc.execute_procedure_serverside(append_snapshot_files,
                dict(search_key=scope['searchKey'], action='save', expected_revision=scope['expectedRevision'],
                     filenames=names, file_type=file_type, keep_file_name=keep_name,
                     upload_directory=scope['uploadDirectory']),
                project=server.get_project(), server=server)
        def saved(result):
            if result.get('state') != 'saved' or result.get('searchKey') != scope['searchKey']:
                raise ValueError('The attachment result is unknown. Close this window and refresh the snapshot before retrying.')
            keys = dict.fromkeys([result['searchKey'], self._source_key or result['searchKey']])
            self.shutdown()
            for key in keys:
                self.completed.emit(key)
            self._application.refresh_snapshot_browser()
        self._run(save, saved, write_started=write_started)

    @Slot()
    def request_close(self) -> None:
        if not self._open:
            self._application.window_model.close_window('snapshot_append')
            return
        if self.busy and self._model['ready']:
            return
        if self.files.rowCount():
            self._model['discard'] = True
            self.changed.emit()
        else:
            self.shutdown()

    def _run(self, operation, accept, *, local=False, write_started=None, stale=None):
        from thlib.environment import env_inst
        pool = env_inst.local_pool if local else env_inst.server_pool
        if pool.is_stopped:
            pool.start()
        outcome = {}
        def perform():
            result = operation()
            outcome['result'] = result
            return result
        worker = pool.add_task(perform)
        if worker is None:
            self._model['error'] = self.tr('Server worker is unavailable')
            self.changed.emit()
            return
        generation = self._generation
        self._model.update(busy=True, error='')
        self.files.replace([dict(row, canRemove=False) for row in self.files.records()])
        self._workers.add(worker)
        def finish():
            self._model['busy'] = False
            self.files.replace([dict(row, canRemove=True) for row in self.files.records()])
        def loaded(result):
            if generation != self._generation:
                return
            finish()
            try:
                accept(result)
            except (KeyError, TypeError, ValueError) as error:
                self._model.update(error=str(error), appendUncertain=bool(write_started and write_started.is_set()))
            self.changed.emit()
        def failed(error):
            if generation != self._generation:
                return
            finish()
            payload = error[0]
            exception = payload.get('exception') or error
            self._model.update(error=str(exception), appendUncertain=bool(write_started and write_started.is_set()))
            if self._application.debug_log:
                self._application.debug_log.raise_error(exception,
                    stacktrace=payload.get('stacktrace', ''), group='table/append')
            self.changed.emit()
        def settled(_worker):
            self._workers.discard(worker)
            if stale and generation != self._generation and 'result' in outcome:
                cleanup = env_inst.local_pool.add_task(lambda: stale(outcome['result']))
                if cleanup:
                    cleanup.start()
        worker.result.connect(loaded, Qt.QueuedConnection)
        worker.error.connect(failed, Qt.QueuedConnection)
        worker.settled.connect(settled, Qt.QueuedConnection)
        self.changed.emit()
        worker.start()

    @Slot()
    def shutdown(self) -> None:
        from thlib.environment import env_inst
        self._generation += 1
        self._cancel.set()
        was_open = self._open
        self._open = False
        self._server = None
        self._scope = {}
        self._detach_input_window()
        self._model = self._empty_model()
        self.files.clear()
        if was_open:
            self._application.window_model.close_window('snapshot_append')
        for worker in tuple(self._workers):
            worker.cancel()
        paths, self._temporary_files = tuple(self._temporary_files), set()
        if paths:
            pool = env_inst.local_pool
            if pool.is_stopped:
                pool.start()
            cleanup = pool.add_task(lambda: self._remove_temporary(paths))
            if cleanup:
                cleanup.start()
        self.changed.emit()
