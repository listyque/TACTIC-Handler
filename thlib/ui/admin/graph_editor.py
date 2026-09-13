"""Project schema/workflow canvas drafts; no server work during pointer input."""

from __future__ import annotations

import copy
import json
import math
import xml.etree.ElementTree as ET

from PySide6.QtCore import QObject, Property, Signal, Slot

from .documents import GraphDocument
from .editor import AdminDocumentEditor
from .graph_layout import layout_graph
from .schema_api import schema_request
from .schema_connections import SchemaConnectionEditor
from .schema_delete import SchemaTypeDeletion
from .workflow_api import workflow_request
from .process_rules import ProcessRulesEditor


class GraphEditor(AdminDocumentEditor):
    graphChanged = Signal()
    selectionChanged = Signal()
    catalogChanged = Signal()
    PROCESS_PROPERTIES = ('label', 'group', 'color', 'completion', 'task_pipeline',
                          'assigned_group', 'supervisor_group', 'duration',
                          'bid_duration', 'task_creation', 'autocreate_task')

    def __init__(self, application, mode: str, parent=None) -> None:
        self._mode = mode
        self._graph = None
        self._nodes = []
        self._edges = []
        self._selected_node = ''
        self._selected_nodes = []
        self._selected_edge = -1
        self._new_search_type = ''
        self._opening_search_type = ''
        self._creation_search_type = ''
        super().__init__(application, schema_request if mode == 'schema' else workflow_request, parent)
        self._rules_editor = ProcessRulesEditor(application, self, self) if mode == 'workflow' else None
        self._connection_editor = SchemaConnectionEditor(self) if mode == 'schema' else None
        self._deletion_editor = SchemaTypeDeletion(application, self) if mode == 'schema' else None
        if self._deletion_editor is not None:
            self._deletion_editor.stateChanged.connect(self.stateChanged.emit)
        self.stateChanged.connect(self.selectionChanged.emit)

    @Property(QObject, constant=True)
    def connectionEditor(self):
        return self._connection_editor

    @Property(QObject, constant=True)
    def deletionEditor(self):
        return self._deletion_editor

    @Property(bool, notify=AdminDocumentEditor.stateChanged)
    def busy(self):
        return self._worker is not None or bool(self._deletion_editor and self._deletion_editor.busy)

    @Property(QObject, constant=True)
    def rulesEditor(self):
        return self._rules_editor

    @Property(str, constant=True)
    def mode(self):
        return self._mode

    @Property('QVariantList', notify=graphChanged)
    def nodes(self):
        return self._nodes

    @Property('QVariantList', notify=graphChanged)
    def edges(self):
        return self._edges

    @Property(str, notify=selectionChanged)
    def selectedNode(self):
        return self._selected_node

    @Property('QStringList', notify=selectionChanged)
    def selectedNodes(self):
        return list(self._selected_nodes)

    @Property(int, notify=selectionChanged)
    def selectedEdge(self):
        return self._selected_edge

    @Property('QVariantMap', notify=selectionChanged)
    def selectedAttributes(self):
        if self._selected_node and self._graph:
            return next((dict(row['attributes']) for row in self._nodes
                         if row['identity'] == self._selected_node), {})
        if 0 <= self._selected_edge < len(self._edges):
            return {key: value for key, value in self._edges[self._selected_edge].items()
                    if key != 'edgeIndex'}
        return {}

    @Property(str, notify=selectionChanged)
    def attributesText(self):
        return json.dumps(self.selectedAttributes, ensure_ascii=False, indent=2)

    @Property(str, notify=selectionChanged)
    def settingsText(self):
        return json.dumps(self._document.get('processSettings', {}).get(self._selected_node, {}),
                          ensure_ascii=False, indent=2)

    @Property('QVariantMap', notify=selectionChanged)
    def processSettings(self):
        return self._document.get('processSettings', {}).get(self._selected_node, {})

    @Property(str, notify=selectionChanged)
    def processKind(self):
        if self._mode == 'workflow' and self._document.get('searchType') == 'sthpw/task':
            return 'status'
        return self.selectedAttributes.get('type') or 'manual'

    @Property('QVariantMap', notify=selectionChanged)
    def processProperties(self):
        # XML is still a native presentation input (color, label, completion).
        # Workflow properties are the engine's authoritative task settings.
        return {**{key: value for key, value in self.selectedAttributes.items()
                   if key in self.PROCESS_PROPERTIES},
                **(self.processSettings.get('properties') or {})}

    @Property('QVariantMap', notify=catalogChanged)
    def processCatalog(self):
        return self._metadata

    # PySide 6.11 must receive a signal declared on this subclass here. Passing
    # AdminDocumentEditor.stateChanged builds an apparently valid meta-object
    # that access-violates when QML first wraps a GraphEditor.
    @Property(str, notify=selectionChanged)
    def creationSearchType(self):
        """Search Type retained for creating another workflow after discard."""
        if self._mode != 'workflow':
            return ''
        return self._document.get('searchType') or self._creation_search_type

    def _catalog_loaded(self) -> None:
        self.catalogChanged.emit()

    @Slot(str, str, 'QVariant')
    def set_process_setting(self, section: str, key: str, value) -> None:
        if self.busy or not self.canWrite or not self._selected_node or self.selectedReference:
            return
        if key in ('duration', 'bid_duration', 'completion', 'task_number') and isinstance(value, (int, float)):
            # QML numbers arrive through QVariant as doubles. Native task
            # generation parses XML estimates as integer strings, not "3.0".
            if not math.isfinite(value) or value != int(value):
                self.fail(self.tr('Enter a whole number'))
                return
            value = int(value)
        settings = self._document.setdefault('processSettings', {}).setdefault(self._selected_node, {})
        if section in settings and not isinstance(settings[section], dict):
            self.fail(self.tr('Process setting sections must be JSON objects'))
            return
        settings.setdefault('version', 2)
        if section:
            settings.setdefault(section, {})[key] = value
        else:
            settings[key] = value
        kind = self.processKind
        if kind == 'status':
            self._graph.node(self._selected_node).set('type', 'status')
            self._document['xml'] = self._graph.xml()
        if section == 'hierarchy' and key == 'subpipeline':
            # Native task generation reads default.subpipeline_code, while
            # NewProcessInfoCmd owns the process table's subpipeline reference.
            settings.setdefault('default', {})['subpipeline_code'] = value
        if kind == 'status' and section == 'default' and key in ('mapping', 'direction', 'status'):
            settings[key] = value
            cleared = ('direction', 'status') if key == 'mapping' else ('mapping',)
            if value:
                for other in cleared:
                    settings['default'][other] = settings[other] = ''
        if section == 'properties' and key in self.PROCESS_PROPERTIES:
            if kind == 'status' and key == 'color':
                settings.setdefault('default', {})['color'] = value
            self._graph.node(self._selected_node).set(
                key, str(value).lower() if isinstance(value, bool) else str(value))
            self._changed()
            return
        if key == 'related_search_type':
            settings[section].update(related_pipeline_code='', related_process='')
        elif key == 'related_pipeline_code':
            settings[section]['related_process'] = ''
        if kind == 'status':
            self._changed()
            return
        self._error = ''
        self.stateChanged.emit()

    @Property(str, notify=selectionChanged)
    def processDescription(self):
        return self._document.get('processDescriptions', {}).get(self._selected_node, '')

    @Property(bool, notify=selectionChanged)
    def selectedReference(self):
        return any(row['identity'] == self._selected_node and row.get('referenceOnly')
                   for row in self._nodes)

    def _document_loaded(self) -> None:
        if self._mode == 'workflow' and self._document.get('searchType'):
            self._creation_search_type = self._document['searchType']
        if self._opening_search_type:
            search_type, self._opening_search_type = self._opening_search_type, ''
            pipelines = [row for row in self._metadata.get('pipelines', [])
                         if row.get('searchType') == search_type]
            if pipelines:
                self._request('load', pipelines[0]['identity'])
            else:
                self.new_document(search_type)
            return
        if self._new_search_type:
            search_type, self._new_search_type = self._new_search_type, ''
            self.new_document(search_type)
            return
        self.catalogChanged.emit()
        self._selected_node, self._selected_nodes, self._selected_edge = '', [], -1
        if self._connection_editor is not None:
            self._connection_editor.reset()
        self._graph = None
        self._nodes, self._edges = [], []
        if self._document.get('xml'):
            try:
                self._graph = GraphDocument(self._mode, self._document['xml'])
                self._project_graph()
            except (ET.ParseError, ValueError) as error:
                self.fail(str(error))
        self.graphChanged.emit()

    def _project_graph(self) -> None:
        self._nodes, self._edges = self._graph.nodes(), self._graph.edges()
        types = {row['identity']: row for row in self._metadata.get('searchTypes', [])}
        for node in self._nodes:
            node['pendingCreation'] = node['identity'] in self._document.get('newTypes', {})
            if self._mode == 'workflow' and self._document.get('searchType') == 'sthpw/task' and not node.get('referenceOnly'):
                node['kind'] = 'status'
            type_data = types.get(node['identity'], {}) if self._mode == 'schema' else {}
            node['label'] = type_data.get('label') or node['attributes'].get('label') or node['identity']
            if not node['color']:
                node['color'] = type_data.get('color', '')
        self.graphChanged.emit()

    def _changed(self) -> None:
        if self._connection_editor is not None:
            self._connection_editor.reconcile()
        self._document['xml'] = self._graph.xml()
        self._project_graph()
        self._error = ''
        self.stateChanged.emit()

    def accept_created_type(self, identity: str, catalog: list[dict],
                            schema: dict, x: float, y: float) -> None:
        """Rebase only the native creator's node; retain all local graph edits."""
        server_graph = GraphDocument('schema', schema['xml'])
        node = copy.deepcopy(server_graph.node(identity))
        node.set('xpos', str(round(x, 1)))
        node.set('ypos', str(round(y, 1)))
        # An unregistered node may already exist in an imported schema XML.
        # Registration must not duplicate it or replace its authored attributes.
        if not any(row.get('name') == identity for row in self._graph.root.findall('search_type')):
            self._graph.root.append(node)
        types = {row['identity']: row for row in self._metadata.get('searchTypes', [])}
        types.update({row['identity']: row for row in catalog})
        self._metadata['searchTypes'] = list(types.values())
        self._original = {'xml': server_graph.xml()}
        self._revision = schema['revision']
        self._selected_node, self._selected_nodes, self._selected_edge = identity, [identity], -1
        self._changed()

    @Slot(str)
    def select_node(self, identity: str) -> None:
        if any(node['identity'] == identity for node in self._nodes):
            self._selected_node, self._selected_nodes, self._selected_edge = identity, [identity], -1
            self.selectionChanged.emit()

    @Slot('QVariantList', str)
    def select_nodes(self, identities: list, primary: str = '') -> None:
        available = {node['identity'] for node in self._nodes}
        selected = []
        for identity in identities:
            identity = str(identity)
            if identity in available and identity not in selected:
                selected.append(identity)
        primary = str(primary or '')
        if primary not in selected:
            primary = selected[-1] if selected else ''
        self._selected_node, self._selected_nodes = primary, selected
        self._selected_edge = -1
        self.selectionChanged.emit()

    @Slot(int)
    def select_edge(self, index: int) -> None:
        if 0 <= index < len(self._edges):
            self._selected_node, self._selected_nodes, self._selected_edge = '', [], index
            self.selectionChanged.emit()

    @Slot()
    def clear_selection(self) -> None:
        self._selected_node, self._selected_nodes, self._selected_edge = '', [], -1
        self.selectionChanged.emit()

    @Slot()
    def open_task_workflow(self) -> None:
        identity = self.processProperties.get('task_pipeline')
        if not identity or self.busy:
            return
        if self.dirty:
            self.fail(self.tr('Save the workflow before opening its task status workflow'))
            return
        if any(row['identity'] == identity and row.get('searchType') == 'sthpw/task'
               for row in self._metadata.get('pipelines', [])):
            self.select(identity)

    @Slot(str, 'QVariant')
    def set_field(self, name: str, value) -> None:
        if self._mode == 'workflow' and name == 'searchType':
            if value != self._document.get('searchType'):
                self.fail(self.tr('A pipeline belongs to its original Search Type. Create a workflow from the required Search Type instead.'))
            return
        super().set_field(name, value)

    @Slot(str, float, float)
    def move_node(self, name: str, x: float, y: float) -> None:
        self.move_nodes([{'identity': name, 'nodeX': x, 'nodeY': y}])

    @Slot('QVariantList')
    def move_nodes(self, positions: list) -> None:
        if self.busy or not self.canWrite or not self._graph:
            return
        try:
            graph = GraphDocument(self._mode, self._graph.xml())
            available = {row['identity']: row for row in self._nodes}
            seen = set()
            for position in positions:
                if not isinstance(position, dict):
                    raise ValueError(self.tr('Node positions must be records'))
                identity = str(position.get('identity') or '')
                x, y = position.get('nodeX'), position.get('nodeY')
                if (identity in seen or identity not in available
                        or available[identity].get('referenceOnly')):
                    raise ValueError(self.tr('Choose movable nodes on this canvas'))
                if not isinstance(x, (int, float)) or not isinstance(y, (int, float)) \
                        or not math.isfinite(x) or not math.isfinite(y):
                    raise ValueError(self.tr('Node positions must be finite'))
                seen.add(identity)
                node = graph.node(identity)
                node.set('xpos', str(round(x, 1)))
                node.set('ypos', str(round(y, 1)))
            if not seen:
                return
            self._graph = graph
            self._changed()
        except ValueError as error:
            self.fail(str(error))

    @Slot(str)
    def arrange_nodes(self, style: str) -> None:
        if self.busy or not self.canWrite or not self._graph:
            return
        try:
            self.move_nodes(layout_graph(self._nodes, self._edges, style))
        except ValueError as error:
            self.fail(str(error))

    @Slot(str, str)
    @Slot(str, str, float, float)
    def add_node(self, name: str, kind: str, x: float | None = None,
                 y: float | None = None) -> None:
        if self.busy or not self.canWrite or not self._graph:
            return
        try:
            name = name.strip()
            if self._mode == 'schema' and name not in {
                    row['identity'] for row in self._metadata.get('searchTypes', [])}:
                raise ValueError(self.tr('Choose a registered Search Type'))
            if not name:
                raise ValueError(self.tr('Enter a process name'))
            if (x is None) != (y is None) or (x is not None and not (
                    math.isfinite(x) and math.isfinite(y))):
                raise ValueError(self.tr('Node positions must be finite'))
            if any(node['identity'] == name and not node.get('referenceOnly') for node in self._nodes):
                if self._mode == 'schema':
                    self._error = ''
                    self.select_node(name)
                    return
                raise ValueError(self.tr('A process with this name is already on the canvas. Enter a different name.'))
            self._graph.add_node(name, kind if self._mode == 'workflow' else '')
            if x is not None:
                node = self._graph.node(name)
                node.set('xpos', str(round(x, 1)))
                node.set('ypos', str(round(y, 1)))
            if self._mode == 'workflow':
                if self._document.get('searchType') == 'sthpw/task':
                    kind = 'status'
                    self._graph.node(name).set('type', kind)
                self._document.setdefault('processSettings', {})[name] = {'version': 2, 'node_type': kind}
            self._selected_node, self._selected_nodes, self._selected_edge = name, [name], -1
            self._changed()
        except ValueError as error:
            self.fail(str(error))

    @Slot(str, str)
    def connect_nodes(self, source: str, target: str) -> None:
        if self.busy or not self.canWrite or not self._graph:
            return
        try:
            self._graph.connect(source, target)
            self._selected_node, self._selected_nodes = '', []
            self._selected_edge = len(self._graph.edges()) - 1
            self._changed()
        except ValueError as error:
            self.fail(str(error))

    @Slot()
    def remove_selected(self) -> None:
        if self.busy or not self.canWrite or not self._graph or self.selectedReference:
            return
        if self._selected_nodes:
            references = {row['identity'] for row in self._nodes if row.get('referenceOnly')}
            for identity in self._selected_nodes:
                if identity in references:
                    continue
                self._graph.remove_node(identity)
                for key in ('processSettings', 'processDescriptions'):
                    self._document.get(key, {}).pop(identity, None)
        elif self._selected_edge >= 0:
            self._graph.remove_edge(self._selected_edge)
        self._selected_node, self._selected_nodes, self._selected_edge = '', [], -1
        self._changed()

    @Slot(str)
    def apply_attributes(self, text: str) -> None:
        if self.busy or not self.canWrite or not self._graph or self.selectedReference:
            return
        try:
            attributes = json.loads(text)
            if not isinstance(attributes, dict) or any(
                    not isinstance(value, str) for value in attributes.values()):
                raise ValueError(self.tr('Attributes must be a JSON object with string values'))
            graph = GraphDocument(self._mode, self._graph.xml())
            previous_name = self._selected_node
            if previous_name:
                code = attributes.get('process_code')
                if code and code != self.selectedAttributes.get('process_code'):
                    raise ValueError(self.tr('Process codes are generated by TACTIC and cannot be edited'))
                graph.set_attributes(previous_name, attributes)
                if previous_name in self._document.get('newTypes', {}) and attributes.get('name') != previous_name:
                    raise ValueError(self.tr('Rename the instance using its table name field'))
            elif self._selected_edge >= 0:
                edge = graph.root.findall('connect')[self._selected_edge]
                edge.attrib.clear()
                edge.attrib.update(attributes)
            graph.validate()
            if previous_name:
                self._selected_node = attributes.get('name', previous_name)
                if self._selected_node != previous_name:
                    for key in ('processSettings', 'processDescriptions'):
                        values = self._document.get(key, {})
                        if previous_name in values:
                            values[self._selected_node] = values.pop(previous_name)
                self._selected_nodes = [
                    self._selected_node if identity == previous_name else identity
                    for identity in self._selected_nodes
                ]
            self._graph = graph
            self._changed()
        except (ValueError, ET.ParseError) as error:
            self.fail(str(error))

    @Slot(str, str)
    def set_attribute(self, key: str, value: str) -> None:
        if key == 'process_code':
            self.fail(self.tr('Process codes are generated by TACTIC and cannot be edited'))
            return
        if self._mode == 'workflow' and self._selected_node and key in self.PROCESS_PROPERTIES:
            self.set_process_setting('properties', key, value)
            return
        attributes = self.selectedAttributes
        attributes[key] = value
        self.apply_attributes(json.dumps(attributes))

    @Slot(str)
    def apply_settings(self, text: str) -> None:
        if self.busy or not self.canWrite or not self._selected_node:
            return
        try:
            settings = json.loads(text)
            if not isinstance(settings, dict):
                raise ValueError(self.tr('Process settings must be a JSON object'))
            if any(key in settings and not isinstance(settings[key], dict)
                   for key in ('properties', 'default', 'hierarchy', 'progress')):
                raise ValueError(self.tr('Process setting sections must be JSON objects'))
            self._document.setdefault('processSettings', {})[self._selected_node] = settings
            for key, value in (settings.get('properties') or {}).items():
                if key in self.PROCESS_PROPERTIES:
                    self._graph.node(self._selected_node).set(
                        key, str(value).lower() if isinstance(value, bool) else str(value))
            self._changed()
        except ValueError as error:
            self.fail(str(error))

    @Slot(str)
    def set_process_description(self, text: str) -> None:
        if self.canWrite and not self.busy and self._selected_node:
            self._document.setdefault('processDescriptions', {})[self._selected_node] = text
            self.stateChanged.emit()

    @Slot(str)
    def apply_xml(self, text: str) -> None:
        if self.busy or not self.canWrite:
            return
        try:
            graph = GraphDocument(self._mode, text)
            self._graph = graph
            self._selected_node, self._selected_nodes, self._selected_edge = '', [], -1
            self._changed()
        except (ValueError, ET.ParseError) as error:
            self.fail(str(error))

    def reset(self, project: str = '') -> None:
        if self._rules_editor is not None:
            self._rules_editor.reset(project)
        if self._deletion_editor is not None:
            self._deletion_editor.reset(project)
        self._new_search_type = ''
        self._opening_search_type = ''
        self._creation_search_type = ''
        super().reset(project)

    def fail(self, error: str) -> None:
        self._new_search_type = ''
        self._opening_search_type = ''
        super().fail(error)

    def shutdown(self) -> None:
        if self._rules_editor is not None:
            self._rules_editor.shutdown()
        if self._deletion_editor is not None:
            self._deletion_editor.shutdown()
        self._new_search_type = ''
        self._opening_search_type = ''
        self._creation_search_type = ''
        super().shutdown()
        if self._connection_editor is not None:
            self._connection_editor.reset()

    @Slot()
    def save(self) -> None:
        missing = [node['identity'] for node in self._nodes if node.get('referenceOnly')]
        if self._mode == 'workflow' and missing:
            self.fail(self.tr('Add missing processes or remove their connections before saving: %s') % ', '.join(missing))
            return
        super().save()

    def open_search_type(self, search_type: str) -> None:
        """Resolve this type's pipelines, including ones just created by TACTIC."""
        if self._mode != 'workflow' or self._closed or self.busy or self.dirty:
            return
        self._opening_search_type = search_type
        self._request('new', search_type)

    @Slot()
    @Slot(str)
    @Slot(str, str)
    def new_document(self, search_type: str = '', search_type_label: str = '') -> None:
        if self._mode != 'workflow' or self._closed or self.busy or self.dirty:
            return
        search_type = (search_type or self._document.get('searchType', '')
                       or self._creation_search_type)
        if not search_type:
            self.fail(self.tr('Create a workflow from a saved Search Type.'))
            return
        if search_type and not self._loaded:
            self._new_search_type = search_type
            self._request('new', search_type)
            return
        if not (self.canWrite or self._metadata.get('canCreate')):
            return
        if search_type and not any(
                row['identity'] == search_type for row in self._metadata.get('searchTypes', [])):
            # A freshly saved type may not be in this retained catalog yet.
            self._metadata.setdefault('searchTypes', []).append({
                'identity': search_type, 'label': search_type_label or search_type})
        self._can_write = True
        self._error = ''
        self._metadata['shared'] = False
        self._creation_search_type = search_type
        self._identity, self._revision = '', ''
        self._original = {}
        self._document = {'name': '', 'description': '', 'color': '',
                          'searchType': search_type, 'xml': '<pipeline/>',
                          'processSettings': {}, 'processDescriptions': {}}
        self._document_loaded()
        self.stateChanged.emit()
