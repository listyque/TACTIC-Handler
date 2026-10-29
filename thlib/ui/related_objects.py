"""A native related-object window over the existing scoped table controller."""
from PySide6.QtCore import QObject, Property, Signal, Slot

from .table.nested import NestedTableController


def read_related_types(parent_key: str) -> list[dict]:
    """Original-server schema catalogue; no project relationship is invented locally."""
    from pyasm.biz import Project
    from pyasm.common import Environment
    from pyasm.search import Search, SearchKey, SearchType
    security = Environment.get_security()
    if not security.is_admin() and (not security.is_logged_in() or security.get_user_name() == 'admin'
            or not (Project.get_project_code() in ('admin', 'sthpw') or security.check_access(
                'project', [{'code': '*'}, {'code': Project.get_project_code()}], 'allow', default='deny'))):
        raise PermissionError('Administration requires administrator access')
    if SearchKey.extract_project(parent_key) not in (None, '', Project.get_project_code(), 'sthpw', 'admin'):
        raise ValueError('The configured table target belongs to another project')
    parent = Search.get_by_search_key(parent_key)
    if parent is None:
        raise LookupError('Object is no longer available')
    base, schema = parent.get_base_search_type(), parent.get_schema()
    result = []
    for code in dict.fromkeys(SearchType.get_related_types(base)):
        child = SearchType.get(code)
        attrs = schema.get_relationship_attrs(code, base)
        available = bool(attrs) and not attrs.get('disabled') and not attrs.get('prefix') and code != base
        available = available and attrs.get('from') == code and attrs.get('to') in (base, '*')
        available = available and attrs.get('relationship') in ('code', 'id', 'search_type', 'search_code', 'search_id')
        if available:
            result.append(dict(title=child.get_value('title') or code, command='related:child:' + code,
                               expression='', canCreate=code not in ('sthpw/file', 'sthpw/snapshot')))
    return result


class RelatedObjectsController(QObject):
    changed = Signal()

    def __init__(self, application, services):
        super().__init__(application)
        self.application = application
        self.services = services
        self._node = None
        self._relations = []
        self._selected = ''
        self._error = ''
        self._scope = None
        self._generation = 0
        self._worker = None
        application.window_model.windowVisibilityChanged.connect(self._visibility)
        application.project_changed.connect(self.close)
        application.signing_out.connect(self.close)
        application.results_view_changed.connect(self._context_changed)

    @Property('QVariantMap', notify=changed)
    def model(self):
        return dict(parentTitle=self._node.title if self._node else '',
                    relations=[dict(value=r['command'], label=r['title'] + ' · ' + r['command'].split(':', 2)[2]) for r in self._relations],
                    selectedType=self._selected, busy=bool(self._scope and self._scope.model.get('busy')), error=self._error,
                    canCreate=bool(self._scope and self._selected.startswith('related:child:') and self.application.can_manage_tools
                                   and next((r.get('canCreate', False) for r in self._relations if r['command'] == self._selected), False)))

    @Property(QObject, notify=changed)
    def scope(self):
        return self._scope

    def open(self, node_id: str, direction: str = '', search_type: str = '') -> None:
        node = self.application._node_for_any(node_id)
        if node is None or node.node_type != 'sobject' or node.source is None:
            return
        self._release_scope()
        self._node = node
        self._relations = [r for r in self.application.relation_menu_actions(node_id)
                           if str(r.get('command') or '').startswith('related:')]
        desired = 'related:' + direction + ':' + search_type if search_type else ''
        selected = next((r['command'] for r in self._relations if r['command'] == desired),
                        self._relations[0]['command'] if self._relations else '')
        self._selected = ''
        self._error = ''
        self.application.open_window('related_objects')
        if selected:
            self.select_relation(selected)
        else:
            self._error = 'No related objects'
            self.changed.emit()
        self._load_relations()

    def _load_relations(self):
        import json
        from PySide6.QtCore import Qt
        from thlib import tactic_classes as tc
        from thlib.environment import env_inst
        self._generation += 1
        generation, key, project = self._generation, self._node.search_key, self.application._current_project_code
        if self._worker is not None:
            self._worker.cancel()
        try:
            server = tc.server_start(project=project)
        except PermissionError as error:
            self._error = str(error)
            self.changed.emit()
            return
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(lambda: tc.execute_procedure_serverside(
            read_related_types, dict(parent_key=key), project=project, server=server))
        if worker is None:
            self._error = 'Server worker is unavailable'
            self.changed.emit()
            return
        self._worker = worker
        def loaded(result):
            if generation != self._generation or self._node is None:
                return
            items = json.loads(result) if isinstance(result, str) else result
            merged = {item['command']: item for item in self._relations}
            for item in merged.values():
                item['canCreate'] = False
            for item in items:
                if item['command'] in merged:
                    merged[item['command']]['canCreate'] = item['canCreate']
                else:
                    merged[item['command']] = item
            self._relations = list(merged.values())
            self.changed.emit()
            if not self._selected and self._relations:
                self.select_relation(self._relations[0]['command'])
        def failed(error):
            if generation == self._generation:
                self._error = str(error[0].get('exception') or error)
                self.changed.emit()
        worker.result.connect(loaded, Qt.QueuedConnection)
        worker.error.connect(failed, Qt.QueuedConnection)
        worker.start()

    @Slot(str)
    def select_relation(self, value: str) -> None:
        if not self._node or value not in {r['command'] for r in self._relations}:
            return
        self._release_scope()
        self._selected = value
        self._error = ''
        _, direction, code = value.split(':', 2)
        source = self._node.source
        owner = source.get_stype()
        selected = next(r for r in self._relations if r['command'] == value)
        target = owner.get_project().stypes.get(code)
        if target is None and 'expression' not in selected:
            self._error = 'Search Type is not available for this editor'
            self.changed.emit()
            return
        try:
            expression = selected['expression'] if 'expression' in selected else source.get_related_sobjects_tel_string(
                child_stype=owner if direction == 'parent' else target,
                parent_stype=target if direction == 'parent' else owner,
                path=direction)
        except (ValueError, KeyError, TypeError) as error:
            self._error = str(error)
            self.changed.emit()
            return
        descriptor = dict(parentKey=self._node.search_key, searchType=code, view='table',
                          projectCode=self.application._current_project_code,
                          expression=expression, selection=False, insert=False,
                          embedded=True, search=True, shelf=True, gear=True, searchLimit=True)
        self._scope = NestedTableController(self.services, self._node.node_id, descriptor)
        self._scope._model['rowActions'] = True
        self._scope.window_id = 'related_objects'
        self._scope.open = True
        self.services._nested_scopes[('related_objects', id(self))] = self._scope
        self._scope.changed.connect(self.changed)
        self.changed.emit()
        self._scope.reload()

    @Slot('QVariantMap', 'QVariant')
    def activate(self, action: dict, value=None) -> None:
        if action.get('type') == 'relation':
            self.select_relation(str(action.get('value') or ''))
        elif action.get('type') == 'create' and self.model['canCreate']:
            self._scope.activate(dict(type='create'))

    def _release_scope(self):
        if self._scope is None:
            return
        removed = {self._scope}
        while True:
            descendants = {scope for scope in self.services._nested_scopes.values()
                           if any(owner.node_for(scope.owner_node_id) is not None for owner in removed)}
            if descendants <= removed:
                break
            removed.update(descendants)
        for key, scope in tuple(self.services._nested_scopes.items()):
            if scope in removed:
                del self.services._nested_scopes[key]
                scope.open = False
                scope.shutdown()
                scope.deleteLater()
        self._scope = None
        self.services._nested_changed()

    def _visibility(self, window_id, visible):
        if window_id == 'related_objects' and not visible:
            self._generation += 1
            if self._worker is not None:
                self._worker.cancel()
            self._worker = None
            self._release_scope()
            self._node = None
            self._relations = []
            self.changed.emit()

    def _context_changed(self):
        if self._scope and self._scope.tab is not self.application._current_tab():
            self.close()

    @Slot()
    def close(self) -> None:
        self._generation += 1
        if self._worker is not None:
            self._worker.cancel()
        self._worker = None
        self.application.window_model.close_window('related_objects')
        self._release_scope()

    def shutdown(self) -> None:
        self.close()
        self._node = None
