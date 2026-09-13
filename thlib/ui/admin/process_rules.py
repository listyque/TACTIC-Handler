"""Modal process-dependency draft, separate from the workflow graph lifecycle."""

from __future__ import annotations

from PySide6.QtCore import Property, Signal, Slot

from .editor import AdminDocumentEditor
from .process_rules_api import process_rules_request


class ProcessRulesEditor(AdminDocumentEditor):
    selectionChanged = Signal()
    WINDOW_ID = 'process_dependencies'

    def __init__(self, application, workflow, parent=None) -> None:
        super().__init__(application, process_rules_request, parent)
        self._workflow = workflow
        self._selected = -1
        self._selected_key = ''
        self.stateChanged.connect(self.selectionChanged.emit)

    @Property('QVariantMap', notify=selectionChanged)
    def selectedRule(self):
        rules = self._document.get('rules', [])
        return rules[self._selected] if 0 <= self._selected < len(rules) else {}

    @Property(int, notify=selectionChanged)
    def selectedIndex(self):
        return self._selected

    def _document_loaded(self) -> None:
        rules = self._document.get('rules', [])
        self._selected = next((index for index, row in enumerate(rules)
                               if self._selected_key and row['key'] == self._selected_key),
                              min(max(0, self._selected), len(rules) - 1))
        self._selected_key = self.selectedRule.get('key', '')
        self.selectionChanged.emit()

    @Slot()
    def open(self) -> None:
        graph = self._workflow
        if self._closed or self.busy or not self._application.can_administer:
            return
        if graph.dirty or graph.busy:
            graph.fail(self.tr('Save the workflow before editing process dependencies'))
            return
        code = graph.metadata.get('processCodes', {}).get(graph.selectedNode)
        if not code:
            graph.fail(self.tr('Save the process before editing its dependencies'))
            return
        windows = self._application.window_model
        if self.dirty:
            windows.show_child_window(self.WINDOW_ID, 'administration')
            return
        self.reset(graph._project)
        windows.show_child_window(self.WINDOW_ID, 'administration')
        self._request('load', code)

    @Slot(int)
    def select_rule(self, index: int) -> None:
        if not self.busy and -1 <= index < len(self._document.get('rules', [])):
            self._selected = index
            self._selected_key = self.selectedRule.get('key', '')
            self.selectionChanged.emit()

    @Slot(str)
    def add_rule(self, kind: str) -> None:
        if self.busy or not self.canWrite or kind not in ('trigger', 'notification'):
            return
        rule = dict(key='', kind=kind, title='', description='', event='change|sthpw/task|status',
                    scope='local', action='notification' if kind == 'notification' else 'task_status',
                    managed=False, srcStatus='', targets=[], outputs=[], column='', targetStatus='',
                    scriptPath='', classPath='', subject='', body='', mailTo='', mailCc='',
                    loginTicket=False, useTemplate=False, mode='same process,same transaction', rules='')
        self._document.setdefault('rules', []).append(rule)
        self._selected = len(self._document['rules']) - 1
        self._selected_key = ''
        self.stateChanged.emit()

    @Slot(str, 'QVariant')
    def set_rule_field(self, key: str, value) -> None:
        rule = self.selectedRule
        if self.busy or not self.canWrite or not rule or rule.get('managed'):
            return
        if key not in rule or key in ('key', 'kind', 'managed'):
            return
        if hasattr(value, 'toVariant'):
            value = value.toVariant()
        if rule[key] != value:
            rule[key] = value
            if key == 'event' and value != 'change|sthpw/task|status':
                rule['srcStatus'] = ''
            self._error = ''
            self.stateChanged.emit()

    @Slot(str, str, bool)
    def set_target(self, process: str, status: str, enabled: bool) -> None:
        targets = [row for row in self.selectedRule.get('targets', []) if row['process'] != process]
        if enabled:
            targets.append({'process': process, 'status': status})
        self.set_rule_field('targets', targets)

    @Slot(str, bool)
    def set_output(self, process: str, enabled: bool) -> None:
        outputs = [name for name in self.selectedRule.get('outputs', []) if name != process]
        if enabled:
            outputs.append(process)
        self.set_rule_field('outputs', outputs)

    @Slot()
    def remove_rule(self) -> None:
        if self.canWrite and not self.busy and self.selectedRule and not self.selectedRule.get('managed'):
            self._document['rules'].pop(self._selected)
            self._document_loaded()
            self.stateChanged.emit()

    @Slot(int)
    def show_item_page(self, offset: int) -> None:
        if not self.busy and not self.dirty and self.identity:
            self._request('load', self.identity, item_offset=max(0, offset))

    @Slot()
    def reload(self) -> None:
        if not self.dirty and not self.busy and self.identity:
            self._request('load', self.identity)

    @Slot(str)
    def open_object(self, key: str) -> None:
        if key in {row['key'] for row in self.metadata.get('items', [])}:
            self._application.open_search_key(key)

    @Slot()
    def request_close(self) -> None:
        if self.busy:
            return
        if self.dirty:
            self.fail(self.tr('Save or discard the process rule changes before closing'))
            return
        self._application.window_model.close_window(self.WINDOW_ID)

    @Slot()
    def cancel(self) -> None:
        if not self.busy:
            self.discard()
            self.request_close()
