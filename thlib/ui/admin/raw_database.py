"""Raw physical-table drafts on the existing asynchronous admin lifecycle."""
from __future__ import annotations

import copy
import json
import os
import tempfile
from pathlib import Path

from PySide6.QtCore import QObject, Property, Signal, Slot, QUrl

from .editor import AdminDocumentEditor
from ..frame_models import FrameTableModel
from .raw_database_api import raw_database_request


from .raw_cell_values import cell_text, cell_value


class RawDatabaseEditor(AdminDocumentEditor):
    rowsChanged = Signal()
    cellChanged = Signal()
    statusChanged = Signal()

    def __init__(self, application, parent=None) -> None:
        super().__init__(application, raw_database_request, parent)
        self._write_pending = False
        self._uncertain = False
        self._cell = {}
        self._cell_sequence = 0
        self._table_model = FrameTableModel(lambda: self.rows, lambda: len(self.metadata.get('columns', [])), self)
        self.stateChanged.connect(self._table_model.refresh)
        self.stateChanged.connect(self.statusChanged.emit)
        application.window_model.windowVisibilityChanged.connect(self._cell_visibility_changed)

    @Property(QObject, constant=True)
    def tableModel(self):
        return self._table_model

    @Property(bool, notify=statusChanged)
    def uncertain(self):
        return self._uncertain or self.writeUncertain

    @Slot()
    @Slot(bool)
    def reload(self, force=False):
        if not self.busy and (force or not self.dirty):
            self.cancel_cell()
            self._request('list')

    @Property(bool, notify=AdminDocumentEditor.stateChanged)
    def dirty(self):
        return self._uncertain or self._document != self._original

    @Property(bool, notify=AdminDocumentEditor.stateChanged)
    def canWrite(self):
        return bool(self._identity) and self._can_write and not self._uncertain

    def fail(self, error: str) -> None:
        if self._write_pending:
            self._uncertain = True
            self._write_pending = False
        super().fail(error)

    @Slot()
    def discard(self) -> None:
        if self._uncertain and not self.busy:
            self._request('list')
        else:
            super().discard()

    @Property('QVariantList', notify=rowsChanged)
    def rows(self):
        return self._document.get('rows', [])

    def _document_loaded(self) -> None:
        self.cancel_cell()
        self._write_pending = self._uncertain = False
        for row in self.rows:
            row['texts'] = {name: cell_text(value) for name, value in row.get('values', {}).items()}
            row['modes'] = {name: 'null' if value is None else 'value' for name, value in row.get('values', {}).items()}
            row['deleted'] = False
        self._original = copy.deepcopy(self._document)
        self.rowsChanged.emit()

    @Slot(int, str, result=str)
    def cell_text(self, index: int, name: str) -> str:
        if not 0 <= index < len(self.rows):
            return ''
        row = self.rows[index]
        mode = row['modes'].get(name, 'default' if row['key'] is None else 'value')
        return 'NULL' if mode == 'null' else 'DEFAULT' if mode == 'default' else row['texts'].get(name, '')

    @Slot(int, str, str)
    def set_cell(self, index: int, name: str, text: str) -> None:
        if self.busy or not self.canWrite or not 0 <= index < len(self.rows):
            return
        column = next((column for column in self._metadata.get('columns', [])
                       if column['name'] == name), None)
        if column and not column['readonly'] and name not in self.rows[index].get('readonly', []):
            self.rows[index]['texts'][name] = text
            self.rows[index]['modes'][name] = 'value'
            self.stateChanged.emit()

    @Property('QVariantMap', notify=cellChanged)
    def cell(self):
        return self._cell

    @Slot(int, str)
    def open_cell(self, index: int, name: str) -> None:
        if self.busy or not 0 <= index < len(self.rows) or self.rows[index]['deleted']:
            return
        column = next((item for item in self.metadata['columns'] if item['name'] == name), None)
        if column is None:
            return
        row = self.rows[index]
        self._cell_sequence += 1
        mode = row['modes'].get(name, 'default' if row['key'] is None else 'value')
        value = row['texts'].get(name, '')
        self._cell = dict(index=index, name=name, type=column['type'], text=value, mode=mode,
                          newRow=row['key'] is None, rowNumber=self.metadata['offset'] + index + 1,
                          readonly=not self.canWrite or column['readonly'] or name in row.get('readonly', []),
                          identity=self.identity, generation=self._generation, session=self._cell_sequence, error='')
        self.cellChanged.emit()
        self._application.window_model.show_child_window('raw_cell', 'administration')

    @Slot(str, str, result=bool)
    def apply_cell(self, mode: str, text: str) -> bool:
        cell = self._cell
        if (not cell or cell['readonly'] or self.busy or not self.canWrite
                or cell['identity'] != self.identity or cell['generation'] != self._generation
                or not 0 <= cell['index'] < len(self.rows) or self.rows[cell['index']]['deleted']):
            return False
        try:
            if mode == 'default':
                if not cell['newRow']:
                    raise ValueError('Default requires a new row')
            else:
                cell_value(text, cell['type'], mode)
        except (ValueError, TypeError):
            self._cell['error'] = self.tr('Enter a valid value for the column type.')
            self.cellChanged.emit()
            return False
        row = self.rows[cell['index']]
        row['texts'][cell['name']] = text if mode == 'value' else ''
        row['modes'][cell['name']] = mode
        self.rowsChanged.emit()
        self.stateChanged.emit()
        self.cancel_cell()
        return True

    @Slot()
    def cancel_cell(self) -> None:
        self._application.window_model.close_window('raw_cell')

    @Slot(str, bool)
    def _cell_visibility_changed(self, window_id: str, visible: bool) -> None:
        if window_id == 'raw_cell' and not visible:
            self._cell = {}
            self.cellChanged.emit()

    @Slot(int)
    def toggle_delete(self, index: int) -> None:
        if not self.busy and self.canWrite and 0 <= index < len(self.rows):
            self.rows[index]['deleted'] = not self.rows[index]['deleted']
            self.rowsChanged.emit()
            self.stateChanged.emit()

    @Slot()
    def new_document(self) -> None:
        if self.canWrite and self.identity and not self.busy and len(self.rows) < 200:
            self.rows.append(dict(key=None, texts={}, modes={}, deleted=False))
            self.rowsChanged.emit()
            self.stateChanged.emit()

    @Slot(int)
    def page(self, offset: int) -> None:
        if not self.busy and not self.dirty and self.identity and offset >= 0:
            self._request('load', self.identity, item_offset=offset)

    @Slot()
    def save(self) -> None:
        if not self.canWrite or not self.dirty or self.busy:
            return
        try:
            rows = []
            baseline = self._original.get('rows', [])
            for index, row in enumerate(self.rows):
                original = baseline[index] if index < len(baseline) else {}
                values = {}
                for column in self._metadata['columns']:
                    name = column['name']
                    text = row['texts'].get(name, '')
                    mode = row['modes'].get(name, 'default' if row['key'] is None else 'value')
                    if column['readonly'] or name in row.get('readonly', []) or mode == 'default':
                        continue
                    if row['key'] is not None and not row['deleted'] and text == original.get('texts', {}).get(name) and mode == original.get('modes', {}).get(name):
                        continue
                    values[name] = None if row['deleted'] else cell_value(text, column['type'], mode)
                if row['key'] is not None and not row['deleted'] and not values:
                    continue
                rows.append(dict(key=row['key'], revision=row.get('revision'),
                                 deleted=row['deleted'], values=values))
        except (ValueError, TypeError):
            self.fail(self.tr('Enter a valid value for the column type.'))
            return
        self._write_pending = True
        self._request('save', self.identity,
                      document=dict(rows=rows, offset=self._metadata['offset']))

    @Slot(str)
    def drop_table(self, confirmation: str) -> None:
        if not self.busy and not self.dirty and self.identity and self.canWrite:
            self._write_pending = True
            self._request('drop', self.identity, confirmation=confirmation)

    @Slot(QUrl)
    def export_csv(self, url: QUrl) -> None:
        if not self.busy and not self.dirty and self.identity and url.isLocalFile():
            self._request('export', self.identity, export_path=url.toLocalFile())

    def _execute_request(self, arguments: dict, project: str, original: dict) -> dict:
        from thlib import server_cache, tactic_classes as tc
        export_path = arguments.pop('export_path', '')
        result = tc.execute_procedure_serverside(self._endpoint, arguments, project=project)
        if arguments['action'] in ('save', 'drop'):
            target_project = json.loads(arguments['identity'])[0]
            server_cache.invalidate_domains(('reference', 'search', 'relations', 'tasks'), target_project)
            server_cache.invalidate_domains(('reference',), 'sthpw')
        if export_path:
            path = Path(export_path)
            descriptor, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
            try:
                with os.fdopen(descriptor, 'w', encoding='utf-8-sig', newline='') as output:
                    output.write(result['metadata'].pop('csv'))
                os.replace(temporary, path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        return result
