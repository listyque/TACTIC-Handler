"""Schema connection drafts and the selected endpoints' asynchronous column catalog."""

from __future__ import annotations

import copy
import re
import xml.etree.ElementTree as ET

from PySide6.QtCore import QObject, Property, Qt, Signal, Slot

from .schema_api import schema_columns_request


class SchemaConnectionEditor(QObject):
    changed = Signal()

    def __init__(self, graph) -> None:
        super().__init__(graph)
        self.graph = graph
        self._column_catalog = {}
        self._worker = self._callbacks = None
        self._generation = 0
        self._requested = ()
        self._error = ''
        graph.selectionChanged.connect(self.changed.emit)

    @staticmethod
    def edge_key(edge: dict) -> dict:
        return {key: edge.get(key, '') for key in ('from', 'to', 'path')}

    @Property('QVariantMap', notify=changed)
    def edge(self):
        edge = self.graph.selectedAttributes if self.graph.selectedEdge >= 0 else {}
        if edge and edge.get('relationship', 'code') in ('code', 'id'):
            table = next((row.get('table') for row in self.graph.metadata.get('searchTypes', [])
                          if row['identity'] == edge['to']), None) or edge['to'].split('/')[-1]
            key = edge.get('relationship', 'code')
            edge.setdefault('from_col', table + '_' + key)
            edge.setdefault('to_col', key)
        return edge

    @Property(str, notify=changed)
    def instance(self):
        names = self.graph.document.get('newTypes', {})
        return next((name for name in (self.graph.selectedNode, self.edge.get('from')) if name in names), '')

    @Property('QVariantList', notify=changed)
    def instanceLinks(self):
        return [edge for edge in self.graph.edges if self.instance and edge['from'] == self.instance]

    @Property(bool, notify=changed)
    def createColumns(self):
        return bool(self.edge and self.edge_key(self.edge) in self.graph.document.get('createColumns', []))

    @Property('QVariantMap', notify=changed)
    def columnCatalog(self) -> dict[str, dict[str, object]]:
        return self._column_catalog

    @Property('QVariantMap', notify=changed)
    def columns(self):
        result = {name: row['columns'] for name, row in self._column_catalog.items()}
        for name in self.graph.document.get('newTypes', {}):
            result[name] = [{'name': edge['from_col'], 'type': '', 'pending': True}
                            for edge in self.graph.edges if edge['from'] == name and edge.get('from_col')]
        return result

    @Property(bool, notify=changed)
    def loading(self):
        return self._worker is not None

    @Property(str, notify=changed)
    def error(self):
        return self._error

    @Property(str, notify=changed)
    def saveDetails(self):
        parts = []
        names = list(self.graph.document.get('newTypes', {}))
        if names:
            parts.append(self.tr('New instance Search Types: %s') % ', '.join(names))
        if self.graph.document.get('createColumns') or names:
            parts.append(self.tr('Missing key columns will be created. Existing columns and data will not be deleted.'))
        return '\n'.join(parts)

    def _release(self) -> None:
        if self._worker is not None:
            self._worker.result.disconnect(self._callbacks[0])
            self._worker.error.disconnect(self._callbacks[1])
            self._worker.cancel()
        self._worker = self._callbacks = None

    def reset(self) -> None:
        self._generation += 1
        self._release()
        self._column_catalog = {}
        self._requested = ()
        self._error = ''
        self.changed.emit()

    @Slot()
    def load_columns(self) -> None:
        """Called by the visible inspector, never by node movement or rendering."""
        from thlib import tactic_classes as tc
        from thlib.environment import env_inst

        graph = self.graph
        if graph._closed or not graph._application.can_administer:
            return
        endpoints = tuple(dict.fromkeys(name for name in (self.edge.get('from'), self.edge.get('to'))
                                       if name and name != '*' and name not in graph.document.get('newTypes', {})))
        if endpoints == self._requested:
            return
        self._requested = endpoints
        self._generation += 1
        generation = self._generation
        self._release()
        self._error = ''
        missing = [name for name in endpoints if name not in self._column_catalog]
        if not missing:
            self.changed.emit()
            return
        project = graph._project

        def operation():
            return tc.execute_procedure_serverside(schema_columns_request, {
                'project_code': project, 'search_types': missing}, project=project)

        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            self._error = self.tr('Server worker pool is unavailable')
            self.changed.emit()
            return
        self._worker = worker

        def loaded(result):
            if graph._closed or generation != self._generation:
                return
            self._release()
            self._column_catalog.update(result)
            self.changed.emit()

        def failed(error):
            if graph._closed or generation != self._generation:
                return
            self._release()
            payload, _worker = error
            self._error = str(payload.get('exception') or error)
            self.changed.emit()
            if graph._application.debug_log:
                graph._application.debug_log.raise_error(
                    payload.get('exception') or self._error, stacktrace=payload.get('stacktrace', ''),
                    group='administration/schema_columns')

        self._callbacks = loaded, failed
        worker.result.connect(loaded, Qt.QueuedConnection)
        worker.error.connect(failed, Qt.QueuedConnection)
        self.changed.emit()
        worker.start()

    @Slot()
    def refresh_columns(self) -> None:
        self.reset()
        self.load_columns()

    def _editable(self) -> bool:
        return self.graph.canWrite and not self.graph.busy and self.graph._graph is not None

    @Slot(bool)
    def set_create_columns(self, enabled: bool) -> None:
        if not self._editable() or not self.edge:
            return
        key = self.edge_key(self.edge)
        values = [row for row in self.graph.document.get('createColumns', []) if row != key]
        if enabled:
            values.append(key)
        self.graph.document['createColumns'] = values
        self.graph._changed()

    @Slot(str, str)
    def set_column(self, side: str, name: str) -> None:
        if self._editable() and self.edge and side in ('from_col', 'to_col'):
            edge = self.graph._graph.root.findall('connect')[self.graph.selectedEdge]
            edge.attrib.update({key: self.edge[key] for key in ('from_col', 'to_col')})
            edge.set(side, name.strip())
            self.graph._changed()

    @Slot()
    def reverse(self) -> None:
        if not self._editable() or not self.edge or self.instance:
            return
        edge = self.graph._graph.root.findall('connect')[self.graph.selectedEdge]
        allowed = self.createColumns
        old_key = self.edge_key(edge.attrib)
        source, target = edge.get('from'), edge.get('to')
        left, right = self.edge.get('from_col', ''), self.edge.get('to_col', '')
        edge.attrib.update({'from': target, 'to': source, 'from_col': right, 'to_col': left})
        if allowed:
            self.graph.document['createColumns'] = [self.edge_key(edge.attrib) if row == old_key else row
                                                     for row in self.graph.document['createColumns']]
        self.graph._changed()

    @Slot()
    def make_many_to_many(self) -> None:
        if not self._editable() or not self.edge or self.instance or '*' in (self.edge['from'], self.edge['to']):
            return
        owner = self.graph
        original = self.edge
        create_columns = self.createColumns
        types = {row['identity']: row for row in owner.metadata.get('searchTypes', [])}
        endpoints = [original['from'], original['to']]
        tables = [types.get(name, {}).get('table') or name.split('/')[-1] for name in endpoints]
        base = '_in_'.join(tables)
        name = owner._project + '/' + base
        occupied = set(types) | {node['identity'] for node in owner.nodes}
        suffix = 2
        while name in occupied:
            name = owner._project + '/' + base + '_' + str(suffix)
            suffix += 1
        graph = owner._graph
        graph.remove_edge(owner.selectedEdge)
        graph.add_node(name, 'instance')
        positions = [node for node in owner.nodes if node['identity'] in endpoints]
        graph.node(name).set('xpos', str(sum(row['nodeX'] for row in positions) / len(positions)))
        graph.node(name).set('ypos', str(sum(row['nodeY'] for row in positions) / len(positions) + 110))
        for index, (endpoint, table) in enumerate(zip(endpoints, tables)):
            key = (original.get('to_col') or 'code') if endpoint == original['to'] else 'code'
            foreign_key = table + '_' + key
            if tables[0] == tables[1]:
                foreign_key = table + ('_from_' if index == 0 else '_to_') + key
            graph.root.append(ET.Element('connect', {
                'from': name, 'to': endpoint, 'relationship': 'code', 'type': 'hierarchy',
                'from_col': foreign_key, 'to_col': key}))
        owner.document.setdefault('newTypes', {})[name] = {
            'original': copy.deepcopy(original), 'createColumns': create_columns}
        owner._selected_node, owner._selected_edge = name, -1
        owner._changed()

    @Slot(str)
    def rename_instance(self, table: str) -> None:
        owner = self.graph
        if not self._editable() or not self.instance:
            return
        name = owner._project + '/' + table.strip()
        if not re.fullmatch(r'[a-z][a-z0-9_]*', table.strip()):
            owner.fail(self.tr('Use a lowercase table name with letters, digits and underscores'))
            return
        if name == self.instance:
            return
        if any(row['identity'] == name for row in owner.nodes + owner.metadata.get('searchTypes', [])):
            owner.fail(self.tr('A Search Type with this name already exists'))
            return
        node = owner._graph.node(self.instance)
        owner._graph.set_attributes(self.instance, dict(node.attrib, name=name))
        owner.document['newTypes'][name] = owner.document['newTypes'].pop(self.instance)
        owner._selected_node, owner._selected_edge = name, -1
        owner._changed()

    @Slot()
    def restore_direct(self) -> None:
        if not self._editable() or not self.instance:
            return
        owner = self.graph
        name = self.instance
        draft = owner.document['newTypes'].pop(name)
        original = draft['original']
        if draft.get('createColumns'):
            owner.document.setdefault('createColumns', []).append(self.edge_key(original))
        owner._graph.remove_node(name)
        owner._graph.root.append(ET.Element('connect', original))
        owner._selected_node, owner._selected_edge = '', len(owner._graph.edges()) - 1
        owner._changed()

    def reconcile(self) -> None:
        """Removing XML/nodes cannot leave invisible table-creation side effects."""
        owner = self.graph
        names = {node.get('name') for node in owner._graph.root.findall('search_type')}
        for name in list(owner.document.get('newTypes', {})):
            if name not in names:
                del owner.document['newTypes'][name]
        keys = [self.edge_key(edge.attrib) for edge in owner._graph.root.findall('connect')]
        if 'createColumns' in owner.document:
            owner.document['createColumns'] = [row for row in owner.document['createColumns'] if row in keys]
        for key in ('newTypes', 'createColumns'):
            if not owner.document.get(key):
                owner.document.pop(key, None)
