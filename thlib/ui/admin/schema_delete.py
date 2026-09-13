"""A pinned deletion confirmation, separate from removing a canvas node."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Property, Signal, Slot

from .editor import AdminDocumentEditor
from .schema_delete_api import schema_delete_request

if TYPE_CHECKING:
    from .graph_editor import GraphEditor


class SchemaTypeDeletion(AdminDocumentEditor):
    # A newly declared QML property needs its own notify signal here. Using
    # the inherited signal crashes PySide 6.11's QML meta-object lookup.
    deletingChanged = Signal()

    def __init__(self, application, schema: GraphEditor) -> None:
        super().__init__(application, schema_delete_request, schema)
        self._schema = schema
        self._deleting = False
        self.committed.connect(self._deleted)

    @Property(bool, notify=deletingChanged)
    def deleting(self) -> bool:
        return self._deleting

    def _set_deleting(self, value: bool) -> None:
        if self._deleting != value:
            self._deleting = value
            self.deletingChanged.emit()

    def reset(self, project: str = '') -> None:
        self._set_deleting(False)
        super().reset(project)

    @Slot(result=bool)
    def open(self) -> bool:
        graph = self._schema
        identity = graph.selectedNode
        if (self._closed or graph.busy or not graph.canWrite or not identity
                or identity in graph.document.get('newTypes', {})):
            return False
        if graph.dirty:
            graph.fail(self.tr('Save or discard the schema changes before deleting a Search Type'))
            return False
        self.reset(graph._project)
        self._request('load', identity)
        return True

    @Slot()
    def cancel(self) -> None:
        if not self._deleting:
            self.reset(self._project)

    @Slot()
    def save(self) -> None:
        if (not self.canWrite or self.busy or self.document.get('confirmation') != self.identity):
            return
        if self.metadata.get('schemaRevision') != self._schema._revision:
            self.fail(self.tr('Schema changed on the server. Reload before saving.'))
            return
        self._set_deleting(True)
        super().save()

    def fail(self, error: str) -> None:
        self._set_deleting(False)
        super().fail(error)

    def _deleted(self) -> None:
        self._set_deleting(False)
        graph = self._schema
        graph._document = {'xml': self.metadata['schema']['xml']}
        graph._original = dict(graph._document)
        graph._revision = self.metadata['schema']['revision']
        graph._metadata['searchTypes'] = [row for row in graph.metadata.get('searchTypes', [])
                                        if row['identity'] != self.identity]
        graph._document_loaded()
        graph.stateChanged.emit()
        graph.committed.emit()
