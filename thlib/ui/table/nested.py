"""An expanded table owns its records, selection and request generation."""
import json
import uuid
from PySide6.QtCore import QObject, Property, Signal, Slot, Qt, QTimer


class NestedTableController(QObject):
    changed = Signal()
    search_text_changed = Signal()

    def __init__(self, services, node_id, descriptor, column: str = ''):
        super().__init__(services)
        self.services = services
        self.application = services._application
        self.open = False
        self.owner_node_id = node_id
        self.descriptor = dict(descriptor)
        self.column = column
        self.tab = self.application._current_tab()
        self._generation = 0
        self._workers = set()
        self._nodes = {}
        from ..workspace_models.results import WorkspaceItemModel
        self._table_model = WorkspaceItemModel()
        self._table_model.setParent(self)
        self._columns = None
        self._layout = None
        self._focused = ''
        self._anchor = ''
        self._group = 'none'
        self._pending_reload = False
        from ..workspace_models.records import RecordListModel
        from ..search_suggestion_data import SEARCH_SUGGESTION_ROLES
        self._suggestions = RecordListModel(SEARCH_SUGGESTION_ROLES)
        self._suggestions.setParent(self)
        self._suggestion_generation = 0
        self._suggestion_worker = None
        self._pending_suggestion = ''
        self._search_text = ''
        self._keyword = ''
        self._keyword_relation = 'EQI'
        self._reload_timer = QTimer(self)
        self._reload_timer.setSingleShot(True)
        self._reload_timer.timeout.connect(self.reload)
        self._identity = 'nested:' + uuid.uuid4().hex + ':'
        self._model = dict(searchType=descriptor.get('searchType') or '', embedded=descriptor.get('embedded', False), columns=[], rows=[], selected=[], offset=0, filter='', filterField='code',
                           gallery=descriptor.get('gallery'), refresh=descriptor.get('refresh', True),
                           insert=False, gear=False, selection=descriptor.get('selection', True), shelf=descriptor.get('shelf', True),
                           search=descriptor.get('search', True), searchLimit=descriptor.get('searchLimit', True), busy=False, error='')
        self.services.nestedChanged.connect(self.changed)
        self.services.completed.connect(self._record_saved)
        self.application.item_fields_updated.connect(self._records_saved)

    @Property('QVariantMap', notify=changed)
    def expansionState(self) -> dict:
        return dict(open=self.open, busy=self._model['busy'], column=self.column, scope=self.descriptor)

    @Property('QVariantMap', notify=changed)
    def model(self):
        model = dict(self._model)
        model['dirtyTaskCount'] = self._columns.dirtyTaskCount if self._columns is not None else 0
        model['children'] = {}
        for row in model['rows']:
            child = self.services.nested_row(row['nodeId']) if row.get('nodeId') else None
            if child:
                model['children'][row['key']] = dict(open=True, model=child.model)
        return model

    @Property(QObject, constant=True)
    def searchSuggestions(self):
        return self._suggestions

    @Property(str, notify=search_text_changed)
    def current_search_text(self):
        return self._search_text

    @Slot(str)
    def update_search_text(self, value):
        self._search_text = value
        self._model['filter'] = value

    @Slot()
    def clear_search_suggestions(self):
        self._suggestion_generation += 1
        self._pending_suggestion = ''
        if self._suggestion_worker is not None:
            self._suggestion_worker.cancel()
        self._suggestions.clear()

    @Slot(str)
    def request_search_suggestions(self, value):
        from thlib import tactic_classes as tc
        from thlib.environment import env_inst
        from ..search_suggestion_data import search_suggestion_records
        from .requests import read_nested_scope
        self.clear_search_suggestions()
        if not value.strip() or not self.services.scope_visible(self):
            return
        if self._suggestion_worker is not None:
            self._pending_suggestion = value
            return
        generation = self._suggestion_generation
        project = self.descriptor.get('projectCode') or self.application._current_project_code
        try:
            server = tc.server_start(project=project)
            descriptor = self.descriptor
            arguments = dict(parent_key=descriptor['parentKey'], search_type=descriptor['searchType'],
                view=descriptor.get('view') or 'table', expression=descriptor.get('expression') or '',
                search_view=descriptor.get('searchView') or '', project_scope=descriptor.get('projectScope', False),
                simple_view=descriptor.get('simpleSearchView') or '', simple_values=dict(self._model.get('simpleValues') or {}),
                filters=list(descriptor.get('filters') or []), keyword=value, limit=50)
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            worker = env_inst.server_pool.add_task(lambda: tc.execute_procedure_serverside(
                read_nested_scope, arguments, project=project, server=server))
            if worker is None:
                raise RuntimeError(self.tr('Server worker is unavailable'))
        except (PermissionError, RuntimeError) as error:
            self._model['error'] = str(error)
            self.changed.emit()
            return
        self._workers.add(worker)
        self._suggestion_worker = worker
        def loaded(result):
            if generation != self._suggestion_generation or not self.services.scope_visible(self):
                return
            result = json.loads(result) if isinstance(result, str) else result
            self._suggestions.replace(search_suggestion_records(result['records'], value, result['searchColumn']))
        def failed(error):
            if generation == self._suggestion_generation and self.services.scope_visible(self):
                self._model['error'] = str(error[0].get('exception') or error)
                self.changed.emit()
        worker.result.connect(loaded, Qt.QueuedConnection)
        worker.error.connect(failed, Qt.QueuedConnection)
        worker.settled.connect(self._suggestions_settled, Qt.QueuedConnection)
        worker.start()

    @Slot(object)
    def _suggestions_settled(self, worker):
        self._workers.discard(worker)
        if self._suggestion_worker is not worker:
            return
        self._suggestion_worker = None
        pending, self._pending_suggestion = self._pending_suggestion, ''
        if pending:
            self.request_search_suggestions(pending)

    @Slot(str)
    def search(self, value):
        self._keyword = self._search_text = value
        self._keyword_relation = 'EQI'
        self._model['offset'] = 0
        self.clear_search_suggestions()
        self.search_text_changed.emit()
        self.reload()

    @Slot(int)
    def accept_search_suggestion(self, row):
        if not 0 <= row < self._suggestions.count():
            return
        self._keyword = self._search_text = self._suggestions._records[row]['title']
        self._keyword_relation = '='
        self._model['offset'] = 0
        self.clear_search_suggestions()
        self.search_text_changed.emit()
        self.reload()

    @Slot(int)
    def open_search_suggestion_in_new_tab(self, row):
        # Embedded results must keep their mandatory parent/page scope.
        self.accept_search_suggestion(row)

    @Property('QVariantList', notify=changed)
    def selected_result_node_ids(self):
        selected = set(self._model['selected'])
        return [identity for identity, node in self._nodes.items() if node.search_key in selected]

    @Property(str, notify=changed)
    def selected_node_id(self):
        return self._focused

    @Property(QObject, constant=True)
    def tableModel(self):
        return self._table_model

    @Property(QObject, constant=True)
    def tableColumns(self):
        if self._columns is None:
            from .nested_columns import NestedColumnsController
            self._columns = NestedColumnsController(self)
            self._columns.stateChanged.connect(self.changed)
            if self._layout is not None:
                self._accept_columns()
        return self._columns

    def _accept_columns(self):
        from thlib.environment import env_inst
        stype = env_inst.get_stype_by_code(self.descriptor['searchType'],
            project_code=self.descriptor.get('projectCode') or self.application._current_project_code)
        self._columns.accept(stype, self._layout, {
            row['key']: row['cells'] for row in self._model['rows']})

    @Property(str, notify=changed)
    def result_group_mode(self):
        return self._group

    @Property(str, notify=changed)
    def result_sort_mode(self):
        order = self._model.get('order', '').split()
        return 'column:' + ':'.join(order) if order else ''

    @Slot(float)
    def set_table_row_height(self, height):
        if height > 0 and self._model.get('rowHeight') != height:
            self._model['rowHeight'] = height
            self.changed.emit()

    @Slot(str)
    def set_result_group_mode(self, mode):
        self._group = mode
        self._table_model.set_organization(group_mode=mode)
        self.changed.emit()

    @Slot(str)
    def toggle_result_node(self, identity):
        self._table_model.toggle_node(identity)

    @Slot()
    def clear_result_selection(self):
        self.activate(dict(type='clear-selection'))

    @Slot()
    def select_all_result_siblings(self):
        if self._model['selection'] is not False:
            self._model['selected'] = [row['key'] for row in self._model['rows']][:500]
            self.changed.emit()

    @Slot(str, str, str, int, bool)
    def select_result_node(self, identity, search_key, node_type, modifiers, preserve):
        node = self.node_for(identity)
        if node is None:
            return
        self._focused = identity
        if not preserve and self._model['selection'] is not False:
            keys = [row['key'] for row in self._model['rows']]
            shift = modifiers & Qt.ShiftModifier.value
            if shift and self._anchor in keys and node.search_key in keys:
                start, end = sorted((keys.index(self._anchor), keys.index(node.search_key)))
                self._model['selected'] = keys[start:end + 1][:500]
            elif modifiers & Qt.ControlModifier.value:
                self.activate(dict(type='select', key=node.search_key))
            else:
                self._model['selected'] = [node.search_key]
        if not modifiers & Qt.ShiftModifier.value:
            self._anchor = node.search_key
        self.changed.emit()

    def node_for(self, identity):
        return self._nodes.get(identity)

    def _records_saved(self, project, search_keys):
        if project == (self.descriptor.get('projectCode') or self.application._current_project_code):
            for search_key in search_keys:
                self._record_saved(search_key)

    def _record_saved(self, search_key):
        if search_key in {self.descriptor.get('parentKey'), *self._model['selected'], *(row['key'] for row in self._model['rows'])}:
            self._reload_timer.start(0)

    @Slot()
    def reload(self):
        self.clear_search_suggestions()
        from thlib import tactic_classes as tc, tactic_query as tq
        from thlib.environment import env_inst
        from .requests import read_nested_scope
        if not self.services.scope_visible(self) or self._model['busy']:
            self._pending_reload = True
            return
        self._pending_reload = False
        try:
            project_code = self.descriptor.get('projectCode') or self.application._current_project_code
            server = tc.server_start(project=project_code)
        except PermissionError as error:
            self._model.update(error=str(error), busy=False)
            self.changed.emit()
            return
        self._generation += 1
        generation = self._generation
        descriptor, state = dict(self.descriptor), dict(self._model)
        arguments = dict(parent_key=descriptor['parentKey'], search_type=descriptor['searchType'],
            view=descriptor.get('view') or 'table', expression=descriptor.get('expression') or '',
            search_view=descriptor.get('searchView') or '',
            project_scope=descriptor.get('projectScope', False),
            simple_view=descriptor.get('simpleSearchView') or '', simple_values=state.get('simpleValues') or {},
            offset=state['offset'], limit=int(descriptor.get('initialLimit') or 50), order_by=[state['order']] if state.get('order') else [], filters=list(descriptor.get('filters') or []))
        arguments.update(keyword=self._keyword, keyword_relation=self._keyword_relation)
        def read():
            scope = tc.execute_procedure_serverside(read_nested_scope, arguments, project=project_code, server=server)
            if isinstance(scope, str):
                scope = json.loads(scope)
            layout = tc.execute_procedure_serverside(tq.query_table_layout,
                dict(search_type=scope['searchType'], view=scope['view'], project_code=project_code,
                     search_keys=[row['__search_key__'] for row in scope['records']]),
                project=project_code, server=server)
            scope['layout'] = json.loads(layout) if isinstance(layout, str) else layout
            return scope
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(read)
        if worker is None:
            self._model.update(error=self.tr('Server worker is unavailable'), busy=False)
            self.changed.emit()
            return
        self._workers.add(worker)
        self._model.update(busy=True, error='')
        def loaded(result):
            if generation != self._generation:
                return
            if not self.services.scope_visible(self):
                self._model['busy'] = False
                self._pending_reload = True
                return
            self._accept(result)
        def failed(error):
            if generation != self._generation:
                return
            payload = error[0]
            self._model.update(busy=False, error=str(payload.get('exception') or error))
            if self.application.debug_log:
                self.application.debug_log.raise_error(payload.get('exception') or error,
                    stacktrace=payload.get('stacktrace', ''), group='table/nested')
            self.changed.emit()
        worker.result.connect(loaded, Qt.QueuedConnection)
        worker.error.connect(failed, Qt.QueuedConnection)
        worker.finished.connect(lambda: self._workers.discard(worker))
        self.changed.emit()
        worker.start()

    def _accept(self, result):
        from thlib import tactic_classes as tc, tactic_table_widgets as widgets
        from thlib.environment import env_inst
        from thlib.ui.workspace_models.results_types import WorkspaceNode
        layout = result['layout']
        columns = []
        adapters = {}
        for index, source in enumerate(layout['columns']):
            adapter = widgets.create_widget(source)
            adapters[source['name']] = adapter
            kind = adapter.get_cell_kind(source.get('dataType'))
            first = next(iter(layout['rows'].values()), {})
            column_width = source.get('width') or (first.get(source['name']) or {}).get('widthHint')
            columns.append(dict(source, width=column_width, title=source.get('title') or source['name'], index=index,
                field=source['name'], supported=kind != 'unsupported', cell=dict(kind=kind)))
        nodes = {identity: node for identity, node in self._nodes.items() if node.search_key in self._model['selected']}
        rows = []
        project = env_inst.projects[self.descriptor.get('projectCode') or self.application._current_project_code]
        for record in result['records']:
            key = record['__search_key__']
            identity = self._identity + key
            source = tc.SObject(record, project)
            nodes[identity] = WorkspaceNode(node_id=identity,
                node_type='snapshot' if result['searchType'] == 'sthpw/snapshot' else 'sobject',
                search_key=key, code=str(record.get('code') or ''),
                title=str(record.get('name') or record.get('title') or record.get('code') or record.get('id')),
                source=source, values=record)
            cells = {column['name']: adapters[column['name']].map_cell(
                (layout['rows'].get(key) or {}).get(column['name']) or {}, column.get('dataType')) for column in columns}
            nodes[identity].preview_url = next((cell['image'] for cell in cells.values() if cell.get('image')), '')
            nodes[identity].preview_requested = True
            nodes[identity].preview_revealed = True
            rows.append(dict(key=key, nodeId=identity, record=record, cells=cells))
        self._nodes = nodes
        self._layout = layout
        self._model.update(columns=columns, rows=rows, hasNext=result['hasNext'], simpleFilters=result.get('simpleFilters') or [], busy=False, loaded=True,
            insert=bool(self.descriptor.get('insert', True) and self.application.can_manage_tools),
            gear=bool(self.descriptor.get('gear', True) and self.application.can_manage_tools),
            filterField=next((name for name in ('name', 'title', 'file_name', 'code') if any(column['name'] == name for column in columns)), 'id'))
        if self._columns is not None:
            self._accept_columns()
        self._table_model.replace_nodes([nodes[row['nodeId']] for row in rows])
        self.changed.emit()
        self.services._nested_changed()
        if self._pending_reload:
            self._reload_timer.start(0)

    @Slot('QVariantMap', 'QVariant')
    def activate(self, action, value=None):
        kind = action.get('type')
        if kind == 'gallery-open':
            node = next((node for node in self._nodes.values()
                         if node.search_key == action.get('key')), None)
            if (node is not None and self.descriptor.get('gallery')
                    and self.services.scope_visible(self)):
                self.services.open_checkout(node.node_id, dict(
                    targetSearchKey=node.search_key,
                    projectCode=self.descriptor.get('projectCode')
                    or self.application._current_project_code))
            return
        if kind == 'filter':
            self._model['filter'] = str(action.get('value') or '')
            return
        if kind == 'clear-selection':
            self._model['selected'] = []
            keys = {row['key'] for row in self._model['rows']}
            self._nodes = {identity:node for identity,node in self._nodes.items() if node.search_key in keys}
            self.changed.emit()
        elif kind == 'select':
            selected = self._model['selected']
            key = action['key']
            if key not in selected and len(selected) >= 500:
                self._model['error'] = self.tr('Choose at most 500 table records')
                self.changed.emit()
                return
            self._model['selected'] = [item for item in selected if item != key] if key in selected else [*selected, key]
            self.changed.emit()
        elif kind in ('edit', 'create'):
            self._edit(action.get('key') if kind == 'edit' else None)
        elif kind == 'columns':
            self._open_columns(action.get('column') or '')
        elif not self._model['busy']:
            if kind == 'page':
                self._model['offset'] = max(0, self._model['offset'] + int(action['value']) * int(self.descriptor.get('initialLimit') or 50))
            else:
                self._model['offset'] = 0
                if kind == 'simple-filter':
                    self._model.setdefault('simpleValues', {})[action['field']] = action['value']
                if kind == 'sort':
                    name = action['value']
                    self._model['order'] = name + ' ' + (action.get('direction') or ('desc' if self._model.get('order') == name + ' asc' else 'asc'))
            self.reload()

    def _edit(self, key, view_override='', operation=''):
        from thlib.environment import env_inst
        app = self.application
        if self.tab is not app._current_tab() or not app.can_manage_tools:
            return
        node = next((node for node in self._nodes.values() if node.search_key == key), None)
        if key and node is None:
            return
        stype = env_inst.get_stype_by_code(self.descriptor['searchType'], project_code=self.descriptor.get('projectCode') or app._current_project_code)
        if stype is None:
            self._model['error'] = self.tr('Search Type is not available for this editor')
            self.changed.emit()
            return
        owner = app._node_for_any(self.owner_node_id)
        parent = owner.source if not key and not self.descriptor.get('projectScope') and owner and owner.source and owner.search_key.split('?')[0] != self.descriptor['searchType'] else None
        from thlib.ui.sobject_editor import open_sobject_editor
        view = view_override or ((self.descriptor.get('editView') or 'edit') if key else (self.descriptor.get('insertView') or 'insert'))
        open_sobject_editor(app, dict(mode='edit' if key else 'insert', view=view,
            stype=stype, operation=operation, sobject=node.source if node else None, parent_sobject=parent, _prepared=True),
            refresh=lambda: (app.refresh_current(), self.services.completed.emit(self.descriptor['parentKey'])))

    def _open_columns(self, column=''):
        app = self.application
        if self.tab is not app._current_tab() or not app.can_manage_tools:
            return
        app.columns_editor_controller.open_scoped_definition(
            self.descriptor['searchType'],
            self.descriptor.get('view') or 'table',
            self.descriptor.get('projectCode') or app._current_project_code,
            column,
        )
        self._pending_reload = True
        app.open_columns_editor()

    def suspend(self):
        self.clear_search_suggestions()
        self._reload_timer.stop()
        if self._model['busy']:
            self._pending_reload = True
            self._generation += 1
            self._model['busy'] = False
            for worker in tuple(self._workers):
                worker.cancel()

    @Slot()
    def request_close(self):
        self.open = False
        self.suspend()
        self.services._nested_changed()

    def shutdown(self):
        self.clear_search_suggestions()
        self._reload_timer.stop()
        self._pending_reload = False
        self._generation += 1
        self._nodes = {}
        if self._columns is not None:
            self._columns.shutdown()
        self._model.update(busy=False)
        for worker in tuple(self._workers):
            worker.cancel()
