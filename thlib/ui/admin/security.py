"""Access rule drafts. Scope keys follow the native AccessManager contract."""

import json
import xml.etree.ElementTree as ET

from PySide6.QtCore import QObject, Property, Signal, Slot

from .documents import RulesDocument
from .editor import AdminDocumentEditor
from .security_api import security_request
from .security_matrix import SecurityMatrixModel


class SecurityRulesEditor(AdminDocumentEditor):
    rulesChanged = Signal()

    def __init__(self, application, parent=None):
        self._rules = None
        self._records = []
        self._selected = -1
        self._group_rules = {}
        self._selected_group = ''
        self._requested_group = ''
        self._message = ''
        super().__init__(application, security_request, parent)
        self._matrix = SecurityMatrixModel(self)
        self.committed.connect(self._saved)
        self.stateChanged.connect(self.rulesChanged.emit)
        self._matrix.modelReset.connect(self.rulesChanged.emit)

    @Property(str, notify=rulesChanged)
    def message(self):
        return self._message

    @Slot()
    def _saved(self):
        self._message = 'Access rules saved on server'
        self.stateChanged.emit()

    def _request(self, *args, **parameters):
        self._message = ''
        super()._request(*args, **parameters)

    @Property(QObject, constant=True)
    def matrix(self):
        return self._matrix

    @Property('QVariantList', notify=rulesChanged)
    def groupCatalog(self):
        return self._metadata.get('groups', [])

    @Property(str, notify=rulesChanged)
    def selectedGroup(self):
        return self._selected_group

    @Property('QVariantMap', notify=rulesChanged)
    def groupDocument(self):
        return self._document.get('groups', {}).get(self._selected_group, {})

    @Property('QVariantList', notify=rulesChanged)
    def matrixTargets(self):
        return self._matrix.targets

    @Property('QVariantList', notify=rulesChanged)
    def matrixGroups(self):
        return self._matrix.groups

    @Slot()
    @Slot(bool)
    def reload(self, force=False):
        if not self.busy and (force or not self.dirty):
            self._request('load', self._project)

    @Slot(str)
    def fail(self, error: str) -> None:
        super().fail(self.tr(str(error)))

    @Slot(str)
    def focus_group(self, identity: str) -> None:
        if self.dirty or self.writeUncertain:
            return
        self._requested_group = str(identity)
        if identity in self._group_rules:
            self.select_group(identity)
            self._requested_group = ''

    @Slot(str)
    def select_group(self, identity: str) -> None:
        if identity in self._group_rules:
            self._selected_group = identity
            self._select_group_rules()
            self.rulesChanged.emit()

    def _select_group_rules(self):
        self._rules = self._group_rules.get(self._selected_group)
        self._records = self._rules.records() if self._rules else []
        self._selected = 0 if self._records else -1

    @Slot(str, 'QVariant')
    def set_group_field(self, name: str, value) -> None:
        if not self.busy and self.canWrite and name in self.groupDocument and name != 'xml':
            self._message = ''
            self.groupDocument[name] = value
            self._matrix.refresh()
            self.stateChanged.emit()

    @Property('QVariantList', notify=rulesChanged)
    def rules(self):
        return self._records

    @Property(int, notify=rulesChanged)
    def selectedRule(self):
        return self._selected

    @Property(str, notify=rulesChanged)
    def ruleText(self):
        record = self._records[self._selected] if 0 <= self._selected < len(self._records) else {}
        return json.dumps({key: value for key, value in record.items() if key != 'ruleIndex'},
                          ensure_ascii=False, indent=2)

    @Property('QVariantMap', notify=rulesChanged)
    def selectedAttributes(self):
        return json.loads(self.ruleText)

    def _document_loaded(self):
        self._message = ''
        self._rules, self._records, self._selected = None, [], -1
        self._group_rules = {}
        try:
            self._group_rules = {code: RulesDocument(data['xml'])
                                 for code, data in self._document.get('groups', {}).items()}
        except (ET.ParseError, ValueError) as error:
            self.fail(str(error))
        if self._requested_group in self._group_rules:
            self._selected_group = self._requested_group
            self._requested_group = ''
        elif self._requested_group and self._group_rules:
            self.fail(self.tr('Group is no longer available'))
            self._requested_group = ''
        if self._selected_group not in self._group_rules:
            self._selected_group = next(iter(self._group_rules), '')
        self._select_group_rules()
        self._matrix.refresh(reset=True)

    def _changed(self):
        self._message = ''
        self._group_rules[self._selected_group] = self._rules
        self.group_rules_changed(self._selected_group)

    def group_rules_changed(self, identity: str) -> None:
        self._message = ''
        xml = self._group_rules[identity].xml()
        original = self._original.get('groups', {}).get(identity, {}).get('xml')
        if original and RulesDocument(original).xml() == xml:
            xml = original
        self._document['groups'][identity]['xml'] = xml
        if identity == self._selected_group:
            self._records = self._rules.records()
        self._matrix.refresh()
        self._error = ''
        self.stateChanged.emit()

    @Slot(int)
    def select_rule(self, index: int):
        if 0 <= index < len(self._records):
            self._selected = index
            self.stateChanged.emit()

    @Slot(str)
    def add_rule(self, scope: str):
        if self.busy or not self.canWrite or not self._rules:
            return
        # Tasks use the native process scope with a task pipeline, not a
        # fictional "task" rule. Server-configured identities are user data.
        keys = {'project': {'code': '*'}, 'search_type': {'code': '*'},
                'process': {'process': '*', 'pipeline': '*'},
                'tasks': {'process': '*', 'pipeline': '*'},
                'link': {'element': '*'}, 'builtin': {'key': 'view_side_bar'},
                'sobject': {'key': '*'},
                'sobject_column': {'search_type': '*', 'column': '*'},
                'gear_menu': {'submenu': '*', 'label': '*'},
                'search_filter': {'search_type': '', 'column': '', 'op': '=', 'value': ''}}
        attributes = {'group': 'process' if scope == 'tasks' else scope, 'access': 'deny',
                      **keys.get(scope, {'key': '*'})}
        if scope not in ('project', 'builtin') and self._project:
            attributes['project'] = self._project
        if scope == 'search_filter':
            attributes.pop('access')
        self._rules.set_rule(-1, attributes)
        self._selected = len(self._rules.records()) - 1
        self._changed()

    @Slot(str)
    def apply_rule(self, text: str):
        if self.busy or not self.canWrite or not self._rules:
            return
        try:
            values = json.loads(text)
            if not isinstance(values, dict) or any(not isinstance(value, str) for value in values.values()):
                raise ValueError(self.tr('Attributes must be a JSON object with string values'))
            self._rules.set_rule(self._selected, values)
            self._changed()
        except ValueError as error:
            self.fail(str(error))

    @Slot(str, str)
    def set_attribute(self, name: str, value: str):
        values = self.selectedAttributes
        values[name] = value
        self.apply_rule(json.dumps(values))

    @Slot(int, str)
    def set_rule_access(self, index: int, access: str) -> None:
        """Change one table row without publishing an intermediate selection."""
        if self.busy or not self.canWrite or not 0 <= index < len(self._records):
            return
        if 'access' not in self._records[index]:
            return
        self._selected = index
        self.set_attribute('access', access)

    @Slot('QVariantMap')
    def set_target(self, attributes: dict):
        values = self.selectedAttributes
        values.update(attributes)
        self.apply_rule(json.dumps(values))

    @Slot()
    def remove_rule(self):
        if not self.busy and self.canWrite and self._selected >= 0:
            self._rules.remove(self._selected)
            self._selected = -1
            self._changed()

    @Slot(str)
    def apply_xml(self, text: str):
        if self.busy or not self.canWrite or not self._selected_group:
            return
        try:
            self._rules = RulesDocument(text)
            self._selected = -1
            self._changed()
        except (ET.ParseError, ValueError) as error:
            self.fail(str(error))
