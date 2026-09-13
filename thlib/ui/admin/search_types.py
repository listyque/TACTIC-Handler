"""Search Type metadata, previews and staged column changes."""

from pathlib import Path
import re

from PySide6.QtCore import Property, QUrl, Signal, Slot

from .editor import AdminDocumentEditor
from .search_types_api import search_types_request


def build_local_relationship_graph(
        identity: str, catalog: list[dict], relationships: list[dict]) -> dict:
    """Project the selected Search Type and its immediate schema neighborhood."""
    if not identity:
        return {'center': '', 'nodes': [], 'edges': []}

    catalog_by_identity = {
        row.get('identity'): row for row in catalog if row.get('identity')
    }
    nodes: dict[str, dict] = {}
    ranks: dict[str, int] = {}
    edge_labels: dict[tuple[str, str], set[str]] = {}

    def add_node(node_identity: str, rank: int, *, link_table: bool = False) -> None:
        if not node_identity:
            return
        row = catalog_by_identity.get(node_identity, {})
        is_link_table = link_table or bool(row.get('linkTable'))
        nodes.setdefault(node_identity, {
            'identity': node_identity,
            'label': row.get('label') or node_identity,
            'kind': 'instance' if is_link_table else row.get('table') or node_identity,
            'color': row.get('color') or '',
            'referenceOnly': True,
        })
        if node_identity == identity:
            ranks[node_identity] = 0
        elif node_identity not in ranks or abs(rank) < abs(ranks[node_identity]):
            ranks[node_identity] = rank

    def add_edge(source: str, target: str, label: str) -> None:
        if not source or not target or source == target:
            return
        edge_labels.setdefault((source, target), set()).add(label)

    add_node(identity, 0)
    ordered_relations = sorted(
        relationships or [],
        key=lambda edge: (
            str(edge.get('from') or ''), str(edge.get('to') or ''),
            str(edge.get('instanceType') or ''), str(edge.get('schema') or ''),
        ),
    )
    for relationship in ordered_relations:
        source = str(relationship.get('from') or '')
        target = str(relationship.get('to') or '')
        instance = str(relationship.get('instanceType') or '')
        many_to_many = bool(relationship.get('manyToMany'))
        chain = [source, target]
        if many_to_many and instance:
            chain = [source, instance, target]
        # Some native schemas use an endpoint itself as instance_type. Collapse
        # it so the read-only projection never draws a meaningless self-edge.
        chain = [node for index, node in enumerate(chain)
                 if node and node not in chain[:index]]
        if identity not in chain:
            continue
        center_index = chain.index(identity)
        relation_kind = str(
            relationship.get('relationship') or relationship.get('type') or 'code'
        )
        label = ('M:N · ' if many_to_many else '') + relation_kind
        for index, node_identity in enumerate(chain):
            add_node(
                node_identity,
                index - center_index,
                link_table=many_to_many and node_identity == instance,
            )
        for source_identity, target_identity in zip(chain, chain[1:]):
            add_edge(source_identity, target_identity, label)

    ranks.setdefault(identity, 0)
    columns: dict[int, list[dict]] = {}
    for node_identity, node in nodes.items():
        columns.setdefault(ranks.get(node_identity, 0), []).append(node)
    for column in columns.values():
        column.sort(key=lambda node: (str(node['label']).casefold(), node['identity']))

    column_gap, row_gap, top = 320, 116, 32
    left_rank = min(columns)
    maximum_height = max((len(column) - 1) * row_gap for column in columns.values())
    projected_nodes = []
    for rank in sorted(columns):
        column = columns[rank]
        column_height = (len(column) - 1) * row_gap
        offset = top + (maximum_height - column_height) / 2
        for index, node in enumerate(column):
            projected_nodes.append(dict(
                node,
                nodeX=40 + (rank - left_rank) * column_gap,
                nodeY=offset + index * row_gap,
            ))

    projected_edges = [
        {'from': source, 'to': target, 'edgeIndex': index,
         'label': ' · '.join(sorted(labels))}
        for index, ((source, target), labels) in enumerate(edge_labels.items())
    ]
    return {'center': identity, 'nodes': projected_nodes, 'edges': projected_edges}


class SearchTypesEditor(AdminDocumentEditor):
    previewChanged = Signal()
    relationshipGraphChanged = Signal()

    def __init__(self, application, parent=None, *, previews=None):
        super().__init__(application, search_types_request, parent)
        self._previews = previews
        self._checkin = None
        self._commit_queue = None
        self._preview_url = ''
        self._preview_identity = ''
        self._queued_preview = ''
        self._presentation_visible = False
        self._relationship_graph = {'center': '', 'nodes': [], 'edges': []}
        self.stateChanged.connect(self.previewChanged.emit)
        self.committed.connect(self._queue_preview)
        if previews is not None:
            previews.previewReady.connect(self._preview_ready)
            previews.previewsReady.connect(self._previews_ready)

    def attach_checkin_controller(self, checkin, commit_queue=None) -> None:
        if self._commit_queue is not None:
            self._commit_queue.operationCompleted.disconnect(self._preview_committed)
        self._checkin = checkin
        self._commit_queue = commit_queue
        if commit_queue is not None:
            commit_queue.operationCompleted.connect(self._preview_committed)

    @Property(str, notify=previewChanged)
    def previewUrl(self) -> str:
        path = self._document.get('previewPath', '') or self._queued_preview
        return QUrl.fromLocalFile(path).toString() if path else self._preview_url

    @Property(bool, notify=previewChanged)
    def previewQueued(self) -> bool:
        return bool(self._queued_preview)

    @Property('QVariantMap', notify=relationshipGraphChanged)
    def relationshipGraph(self) -> dict:
        return self._relationship_graph

    @Slot(bool)
    def set_presentation_visible(self, visible: bool) -> None:
        self._presentation_visible = visible
        if visible:
            self._read_preview()

    def _document_loaded(self) -> None:
        self._update_relationship_graph()
        identity = self._metadata.get('searchKey', '')
        if identity != self._preview_identity:
            self._queued_preview = ''
        self._preview_identity = identity
        self._preview_url = ''
        self._read_preview()

    def _catalog_loaded(self) -> None:
        self._update_relationship_graph()

    def _update_relationship_graph(self) -> None:
        graph = build_local_relationship_graph(
            self._identity, self._catalog, self._metadata.get('relationships', []))
        if graph != self._relationship_graph:
            self._relationship_graph = graph
            self.relationshipGraphChanged.emit()

    def _read_preview(self) -> None:
        key = self._metadata.get('searchKey')
        if self._closed or not self._presentation_visible or not self._previews or not key:
            return
        records = self._previews.records_for_text('skey://' + key)
        url = str(records[0].get('previewUrl') or '') if records else ''
        if self._preview_url != url:
            self._preview_url = url
            self.previewChanged.emit()

    @Slot(str, object)
    def _preview_ready(self, key, _record) -> None:
        if key == 'skey://' + self._metadata.get('searchKey', ''):
            # Read the resolver's current server/login cache, not a late
            # descriptor emitted by a worker from the previous connection.
            self._read_preview()

    @Slot(object)
    def _previews_ready(self, records) -> None:
        if any(row.get('searchKey') == 'skey://' + self._metadata.get('searchKey', '')
               for row in records):
            self._read_preview()

    @Slot()
    def reload(self) -> None:
        if self.busy or self.dirty:
            return
        if self._previews and self._metadata.get('searchKey'):
            self._previews.retry(self._metadata['searchKey'])
        self._queued_preview = ''
        super().reload()

    @Slot('QVariant')
    def set_preview_path(self, value) -> None:
        if self.busy or not self.canWrite or not self._document:
            return
        url = value if isinstance(value, QUrl) else QUrl(str(value or ''))
        if not url.isEmpty() and not url.isLocalFile():
            self.fail(self.tr('Choose a local image file'))
            return
        self._document['previewPath'] = url.toLocalFile()
        if self._identity:
            self._original.setdefault('previewPath', '')
        self._error = ''
        self.stateChanged.emit()

    def _execute_request(self, arguments: dict, project: str, original: dict) -> dict:
        arguments = dict(arguments)
        path = ''
        if arguments.get('document') is not None:
            arguments['document'] = dict(arguments['document'])
            path = arguments['document'].pop('previewPath', '')
        if path:
            from PySide6.QtGui import QImageReader
            if not Path(path).is_file() or not QImageReader(path).canRead():
                raise ValueError(self.tr('The selected preview is not a readable image'))
            if self._checkin is None:
                raise ValueError(self.tr('Commit Queue is unavailable'))
        result = super()._execute_request(arguments, project, original)
        if 'document' in result:
            result['document']['previewPath'] = path
        return result

    @Slot()
    def _queue_preview(self) -> None:
        path = self._document.get('previewPath')
        if not path:
            return
        from thlib.tactic_classes import SObject
        key = self._metadata['searchKey']
        source = SObject({'__search_key__': key, 'code': self.identity,
                          'title': self.document['title']})
        try:
            self._checkin.prepare_external_checkin(
                search_key=key, source=source, project_code='sthpw',
                title=self.document['title'], code=self.identity,
                context='icon', description='Search Type preview', paths=[path],
                update_versionless=True, queue_when_ready=True)
        except (OSError, TypeError, ValueError) as error:
            self._original['previewPath'] = ''
            self.fail(self.tr('Search Type saved, but its preview could not be queued: %1')
                      .replace('%1', str(error)))
            return
        self._document['previewPath'] = self._original['previewPath'] = ''
        self._queued_preview = path
        self.stateChanged.emit()
        self._application.notify(self.tr('Search Type preview added to Commit Queue'))

    @Slot('QVariantMap')
    def _preview_committed(self, payload: dict) -> None:
        if (self._closed or payload.get('context') != 'icon'
                or str(payload.get('searchKey') or '').removeprefix('skey://')
                != self._metadata.get('searchKey')):
            return
        self._queued_preview = ''
        if self._previews is not None:
            self._previews.retry(self._metadata['searchKey'])
        self.previewChanged.emit()

    def shutdown(self) -> None:
        if self._commit_queue is not None:
            self._commit_queue.operationCompleted.disconnect(self._preview_committed)
        if self._previews is not None:
            self._previews.previewReady.disconnect(self._preview_ready)
            self._previews.previewsReady.disconnect(self._previews_ready)
        super().shutdown()

    @Slot()
    def new_document(self):
        if self.busy or self.dirty or not self.canWrite:
            return
        self._identity, self._revision = '', ''
        self._original = {}
        self._document = {'title': '', 'description': '', 'color': '',
                          'hasPipeline': True, 'columns': []}
        self._metadata = {}
        self._document_loaded()
        self.stateChanged.emit()

    @Slot(result=bool)
    def validate_creation_details(self) -> bool:
        if self.busy or not self.canWrite:
            return False
        if not str(self._document.get('title', '')).strip():
            self.fail(self.tr('Enter a Search Type title'))
            return False
        self._error = ''
        self.stateChanged.emit()
        return True

    @Slot(str, str, result=bool)
    def add_column(self, name: str, column_type: str) -> bool:
        if self.busy or not self.canWrite or not self._document:
            return False
        name = name.strip()
        if not name:
            self.fail(self.tr('Enter a column name'))
            return False
        if not re.fullmatch(r'[a-z][a-z0-9_]*', name):
            self.fail(self.tr('Use lowercase Latin letters, numbers and underscores; start with a letter. Example: duration_minutes.'))
            return False
        if column_type not in ('varchar(256)', 'text', 'integer', 'numeric', 'boolean', 'timestamp'):
            self.fail(self.tr('Choose a field type from the list'))
            return False
        if name in self._metadata.get('columns', {}) or any(
                row['name'] == name for row in self._document.get('columns', [])):
            self.fail(self.tr('A column with this name already exists'))
            return False
        self._document.setdefault('columns', []).append({'name': name, 'type': column_type})
        self._error = ''
        self.stateChanged.emit()
        return True

    @Slot(int)
    def remove_column(self, index: int):
        columns = self._document.get('columns', [])
        if not self.busy and self.canWrite and 0 <= index < len(columns):
            columns.pop(index)
            self.stateChanged.emit()

    @Slot(str, bool)
    def set_column_removed(self, name: str, removed: bool) -> None:
        if self.busy or not self.canWrite or not self._identity:
            return
        if name not in self._metadata.get('columns', {}):
            self.fail(self.tr('This field is no longer available. Reload the Search Type.'))
            return
        if removed and name in self._metadata.get('columnRemovalBlocks', {}):
            self.fail(self.tr('This field is required by TACTIC or the project schema and cannot be deleted.'))
            return
        columns = self._document['removedColumns']
        if removed and name not in columns:
            columns.append(name)
        elif not removed and name in columns:
            columns.remove(name)
        self._error = ''
        self.stateChanged.emit()
