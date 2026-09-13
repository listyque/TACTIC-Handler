"""Owned Search Type creation from a schema, preserving the canvas draft."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PySide6.QtCore import Signal, Slot

from .search_types import SearchTypesEditor

if TYPE_CHECKING:
    from .graph_editor import GraphEditor


class SchemaTypeEditor(SearchTypesEditor):
    created = Signal()
    WINDOW_ID = 'schema_search_type'

    def __init__(self, application, schema: GraphEditor, parent=None, *, previews=None) -> None:
        super().__init__(application, parent, previews=previews)
        self._schema = schema
        self._position = (0.0, 0.0)
        self.committed.connect(self._created)
        application.window_model.windowVisibilityChanged.connect(self._visibility_changed)

    @Slot(float, float)
    def open(self, x: float, y: float) -> None:
        if (not self._application.can_administer or self._closed or self.busy
                or self._schema.busy or not self._schema.canWrite
                or self._schema.identity != self._schema._project
                or not all(math.isfinite(value) for value in (x, y))):
            return
        if self._application.window_model.is_window_visible(self.WINDOW_ID):
            self._application.window_model.raise_window(self.WINDOW_ID)
            return
        self.reset(self._schema._project)
        self._position = (x, y)
        self._can_write = self._loaded = True
        self.new_document()
        # AdminDocumentEditor snapshots original before dispatching the worker.
        self._original = {'schemaRevision': self._schema._revision}
        self._application.window_model.show_child_window(self.WINDOW_ID, 'administration')

    def _execute_request(self, arguments: dict, project: str, original: dict) -> dict:
        if not arguments.get('identity'):
            arguments = dict(arguments, schema_revision=original['schemaRevision'])
        return super()._execute_request(arguments, project, original)

    @Slot()
    def _created(self) -> None:
        if 'schema' in self.metadata:
            self._schema.accept_created_type(
                self.identity, self.catalog, self.metadata['schema'], *self._position)
            self.created.emit()
        # A failed preview preparation retains the saved type and image for
        # retry. The next save updates that type, without creating another node.
        if not self.dirty:
            self._application.window_model.close_window(self.WINDOW_ID)

    @Slot()
    def discard(self) -> None:
        if not self.busy:
            self._application.window_model.close_window(self.WINDOW_ID)

    @Slot(str, bool)
    def _visibility_changed(self, window_id: str, visible: bool) -> None:
        if window_id == self.WINDOW_ID and not visible and not self.busy:
            self.reset()
