"""Use the ordinary column owner with an explicitly scoped table context."""
from types import SimpleNamespace

from PySide6.QtCore import Slot

from ..columns_editor import ColumnsEditorController


class NestedColumnsController(ColumnsEditorController):
    def __init__(self, scope):
        self.scope = scope
        self.context = SimpleNamespace(
            stype=None, table_view='table', view_mode='nested', sobjects=[])
        super().__init__(
            scope.application,
            scope.application.columns_editor_controller._tasks_controller,
            parent=scope)

    @property
    def _project_code(self):
        return (self.scope.descriptor.get('projectCode')
                or self._application._current_project_code)

    def _current_tab(self):
        return self.context

    def _current_stype(self):
        return self.context.stype

    def _remember_table_view(self, view):
        self.scope.descriptor['view'] = self.context.table_view = self._view = view

    @Slot()
    def begin_session(self):
        if not self.scope._model.get('loaded') and not self.scope._model['busy']:
            self.scope.reload()

    @Slot()
    def reload(self):
        self.scope.reload()

    def accept(self, stype, layout, prepared_rows=None):
        self.context.stype = stype
        self.context.table_view = self.scope.descriptor.get('view') or 'table'
        self.context.sobjects = [
            self.scope._nodes[row['nodeId']].source
            for row in self.scope._model['rows']]
        layout = dict(layout, tableViews=self._table_view_records(
            stype.get_project().get_config_views().config_dict,
            stype.get_code(), self.context.table_view))
        self._loaded((stype, layout), prepared_rows)

    @Slot(int, bool)
    def sort_column(self, row, descending):
        if 0 <= row < len(self.model._records):
            self.scope.activate(dict(
                type='sort', value=self.model._records[row]['name'],
                direction='desc' if descending else 'asc'))

    @Slot(int)
    def group_column(self, row):
        if 0 <= row < len(self.model._records):
            column = self.model._records[row]['name']
            self._publish_group_values(self._cells, column)
            self.scope.set_result_group_mode('column:' + column)

    @Slot(int, str)
    def request_column_focus(self, row, target):
        name = (self.model._records[row]['name']
                if 0 <= row < len(self.model._records) else '')
        self.scope._open_columns(name)

    def _publish_group_values(self, rows, column, rebuild=False):
        # The scoped result model, not the main search, owns these group labels.
        for node in self.scope._nodes.values():
            cell = (rows.get(node.search_key) or {}).get(column) or {}
            if 'text' in cell:
                node.values[column] = str(cell['text'] or '')
