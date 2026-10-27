"""A configured native document owns its embedded tables and script lifetime."""

from PySide6.QtCore import QObject, Slot, QTimer, Signal, Property


class CustomLayoutController(QObject):
    changed = Signal()

    def __init__(self, services, *, workspace=False):
        super().__init__(services)
        self.services = services
        self.scopes = {}
        self.runner = None
        self.tab = None
        self.context = {}
        self.generation = 0
        self._detail_generation = 0
        self.pages = {}
        self.current = ''
        self.workspace = workspace
        self._workspace_document = {}
        self._focus_active = False
        self._previous_maximized = ''
        self._view = self._title = self._target = ''
        self._report_models = {}
        if workspace:
            services._application.results_view_changed.connect(self.changed)
            services._application.selected_node_changed.connect(self.select_detail)
        else:
            services.documentChanged.connect(self.changed)

    @property
    def document_data(self):
        return self._workspace_document if self.workspace else self.services._document

    @document_data.setter
    def document_data(self, value):
        if self.workspace:
            self._workspace_document = value
        else:
            self.services._document = value

    @property
    def document_generation(self):
        return self.generation if self.workspace else self.services._document_generation

    @document_generation.setter
    def document_generation(self, value):
        if self.workspace:
            self.generation = value
        else:
            self.services._document_generation = value

    @Property('QVariantMap', notify=changed)
    def document(self):
        return self.document_data

    @Property(bool, notify=changed)
    def active(self):
        return bool(self.workspace and self.current and self.tab is self.services._application._current_tab()
                    and getattr(self.tab, 'layout_view', ''))

    def notify_document(self):
        if self.workspace:
            self.changed.emit()
        else:
            self.services.documentChanged.emit()

    def focus_workspace(self):
        dock = getattr(self.services._application, 'dock_model', None)
        if not self.workspace or dock is None or self._focus_active:
            return
        self._focus_active = True
        self._previous_maximized = dock.maximizedPanelId
        if dock.maximizedPanelId != 'results':
            dock.maximize_panel('results')

    def leave_workspace(self):
        dock = getattr(self.services._application, 'dock_model', None)
        if self._focus_active and dock is not None and dock.maximizedPanelId == 'results':
            dock.maximize_panel('results')
            if self._previous_maximized:
                dock.maximize_panel(self._previous_maximized)
        self._focus_active = False
        self.changed.emit()

    @Slot()
    def refresh(self):
        self.open_view(self._view, self._title, self.current, search_key=self._target, force=True,
                       filter_values=self.document_data.get('layoutFilterValues'))

    @Slot('QVariantMap')
    def apply_filters(self, values):
        if not self.workspace or self.document_data.get('layoutBusy'):
            return
        self.open_view(self._view, self._title, self.current, search_key=self._target,
                       force=True, filter_values=values)

    @Slot(str)
    def filter_error(self, message):
        self.document_data['layoutError'] = message
        self.notify_document()

    @Slot(QObject, 'QVariantMap')
    def format_document(self, document, style):
        from ..rich_text_document import format_readonly_document
        format_readonly_document(document, style)

    def close(self):
        self.generation += 1
        self._detail_generation += 1
        if self.runner:
            self.runner.cancel()
            self.runner = None
        for key, scope in tuple(self.services._nested_scopes.items()):
            if getattr(scope, 'layout_owner', None) is not self:
                continue
            self.services._nested_scopes.pop(key, None)
            scope.shutdown()
            scope.deleteLater()
        self.scopes.clear()
        for model in self._report_models.values():
            model.deleteLater()
        self._report_models.clear()
        self.pages.clear()
        self.current = ''
        self.services._nested_changed()
        self.context = {}
        self.tab = None
        if self.workspace:
            self.leave_workspace()

    def open(self, tab, context, tab_key=''):
        if not tab_key or (not self.workspace and self.tab is not None and self.tab is not tab):
            self.close()
        elif tab_key in self.pages:
            self.select_page(tab_key)
            return
        for scope in self.scopes.values():
            scope.open = False
            scope.suspend()
        self.scopes = {}
        self.tab, self.context = tab, dict(context)
        document = self.document_data
        self.current = tab_key
        document['layoutState'] = dict(
            form=document.get('layoutForm') or '',
            root={},
            controls=document.get('layoutControls') or [],
        )

        self._open_tables(document.get('layoutNodes') or [])
        self._open_reports()
        if tab_key:
            self.pages[tab_key] = dict(
                document=document, scopes=self.scopes, context=self.context, tab=tab
            )
        self._tabs()
        self.changed.emit()
        source = '\n'.join(
            item['javascript'] for item in document.get('layoutLoad') or []
        )
        generation = self.generation
        if source:
            QTimer.singleShot(
                0, lambda: self.run(source) if generation == self.generation else None
            )

    def _open_reports(self):
        from ..frame_models import FrameTableModel
        reports = {}
        def walk(nodes, prefix):
            for index, item in enumerate(nodes):
                key = prefix + '_' + str(index)
                if item['kind'] == 'summary':
                    reports[key] = item['report']
                walk(item.get('children') or [], key)
        walk(self.document_data.get('layoutNodes') or [], 'customLayout')
        walk((self.document_data.get('layoutDetail') or {}).get('layoutNodes') or [], 'customLayoutDetails')
        for key in tuple(self._report_models):
            if key not in reports:
                self._report_models.pop(key).deleteLater()
        for key, report in reports.items():
            old = self._report_models.get(key)
            if old is not None and old.report == report:
                continue
            if old is not None:
                old.deleteLater()
            model = FrameTableModel(lambda report=report: report['rows'],
                                    lambda report=report: len(report['columns']), self)
            model.report = report
            self._report_models[key] = model

    def _open_tables(self, items, prefix='customLayout'):
        from .nested import NestedTableController
        document, services = self.document_data, self.services
        tab_key = self.current

        def tables(items, prefix):
            for index, item in enumerate(items):
                key = prefix + '_' + str(index)
                if item['kind'] == 'table':
                    scope = NestedTableController(
                        self.services, document['nodeId'], item['table']
                    )
                    scope.document_generation = self.document_generation
                    scope.layout_page = tab_key
                    scope.layout_owner = self
                    scope.open = True
                    scope.changed.connect(self.changed)
                    self.scopes[key] = scope
                    self.services._nested_scopes[('workspace:' if self.workspace else '') + tab_key + ':' + key] = scope
                    scope.reload()
                else:
                    tables(item.get('children') or [], key)

        tables(items, prefix)

    def select_detail(self):
        from thlib import tactic_classes as tc
        app, document = self.services._application, self.document_data
        def has_details(nodes):
            return any(item['kind'] == 'details' or has_details(item.get('children') or []) for item in nodes)
        if not self.active or not document.get('layoutItems') or not has_details(document.get('layoutNodes') or []):
            return
        node = app.workspace_model.node_for(app.selected_node_id)
        if node is not None and node.node_type in ('process','relation'):
            return
        key = node.search_key if node is not None else ''
        if key and document.get('layoutDetail',{}).get('targetSearchKey') == key:
            return
        self._detail_generation += 1
        request, generation = self._detail_generation, self.document_generation
        for name in tuple(self.scopes):
            if not name.startswith('customLayoutDetails_'):
                continue
            scope = self.scopes.pop(name)
            self.services._nested_scopes.pop('workspace:' + self.current + ':' + name,None)
            scope.shutdown()
            scope.deleteLater()
        document['layoutDetail'] = dict(busy=bool(key),targetSearchKey=key)
        self._open_reports()
        self.notify_document()
        if not key:
            return
        try:
            server = tc.server_start(project=self.context['project'])
        except PermissionError as error:
            document['layoutDetail'] = dict(error=str(error))
            self.notify_document()
            return
        def current():
            return request == self._detail_generation and generation == self.document_generation and self.active
        def loaded(result):
            if current():
                document['layoutDetail'] = result['info']
                self._open_reports()
                self._open_tables(result['info']['layoutNodes'], 'customLayoutDetails')
                self.notify_document()
        def settled():
            if current() and document.get('layoutDetail',{}).get('busy'):
                document['layoutDetail'] = dict(error=self.services.error)
                self.notify_document()
        self.services._run(lambda:server.execute_cmd('tactic.ui.table.CustomLayoutReadCmd',dict(
            view=document['layoutView'],search_key=document['targetSearchKey'],detail_key=key,
            filter_values=document.get('layoutFilterValues'))),loaded,settled=settled)

    def _tabs(self):
        self.document_data['layoutTabs'] = [] if self.workspace else [
            dict(key=key, title=page['document']['title'])
            for key, page in self.pages.items()
        ]
        self.document_data['layoutTabKey'] = self.current

    @Slot(str, 'QVariantMap')
    def open_cell(self, node_id, cell):
        services, app = self.services, self.services._application
        node = app._node_for_any(node_id)
        if node is None or not cell.get('layoutNodes'):
            return
        self.document_generation += 1
        self.document_data = dict(
            cell, nodeId=node_id, title=cell.get('layoutView') or 'Custom Layout'
        )
        scope = services.scope_for(node_id)
        project = (
            scope.descriptor.get('projectCode') if scope else ''
        ) or app._current_project_code
        self.open(
            app._current_tab(),
            dict(
                project=project,
                searchKey=cell.get('targetSearchKey') or node.search_key,
                record=cell.get('layoutRecord') or {},
            ),
        )
        self.notify_document()
        app.open_window('table_document')

    def open_view(self, view, title, key, *, search_key='', force=False, filter_values=None):
        from thlib import tactic_classes as tc
        from .requests import read_custom_layout

        services, app = self.services, self.services._application
        tab, project = app._current_tab(), app._current_project_code
        if self.workspace:
            self.focus_workspace()
            self._view, self._title, self._target = view, title, search_key
            if (not force and key in self.pages
                    and self.pages[key]['document'].get('layoutView') == view
                    and self.pages[key].get('target', '') == search_key):
                self.select_page(key)
                return
        try:
            server = tc.server_start(project=project)
        except PermissionError as error:
            services.report_error(str(error))
            if self.workspace:
                self.tab, self.current = tab, key
                self.document_data = dict(title=title, layoutBusy=False, layoutError=str(error))
                self.notify_document()
            return
        self.document_generation += 1
        generation = self.document_generation
        if self.workspace:
            self.tab, self.current = tab, key
            if self.document_data.get('layoutView') == view:
                self.document_data.update(layoutBusy=True, layoutError='')
            else:
                self.document_data = dict(title=title, layoutBusy=True, layoutError='')
            self.notify_document()

        def loaded(result):
            if (
                generation != self.document_generation
                or tab is not app._current_tab()
                or project != app._current_project_code
            ):
                return
            self.open_result(result, title, key)

        def settled():
            if self.workspace and generation == self.document_generation:
                self.document_data.update(layoutBusy=False, layoutError=services.error)
                self.notify_document()

        services._run(
            lambda: tc.execute_procedure_serverside(
                read_custom_layout, dict(view=view, search_key=search_key,filter_values=filter_values), project=project, server=server
            ),
            loaded,
            settled=settled,
        )

    def open_result(self, result, title, key):
        services, app = self.services, self.services._application
        if self.workspace:
            self._view, self._title = result.get('layoutView') or self._view, title
        self.document_generation += 1
        if self.workspace and key in self.pages:
            self.drop_page(key)
        self.document_data = dict(result, title=title, nodeId='', translateTitle=False)
        self.open(app._current_tab(), dict(project=app._current_project_code,
            searchKey=result['targetSearchKey'], record=result['layoutRecord']), key)
        if self.workspace:
            self.pages[key]['target'] = self._target
            if result.get('layoutItems'):
                self.show_items(force=True)
            else:
                self.tab.loaded = True
        self.notify_document()
        if not self.workspace:
            app.open_window('table_document')

    @Slot(str)
    def select_page(self, key):
        if key not in self.pages or self.runner:
            return
        self.generation += 1
        for scope in self.scopes.values():
            scope.open = False
            scope.suspend()
        page = self.pages[key]
        self.tab = page.get('tab', self.tab)
        self.current, self.scopes, self.context = key, page['scopes'], page['context']
        self.document_data = page['document']
        self._open_reports()
        for scope in self.scopes.values():
            scope.document_generation = self.document_generation
            scope.open = True
        self._tabs()
        self.services._nested_changed()
        self.notify_document()
        self.changed.emit()

        self.show_items()

    def show_items(self, *, force=False):
        """Use the current native search tab; never create another result tree."""
        app = self.services._application
        scope = self.document_data.get('layoutItems')
        if not self.workspace or not scope or self.tab is not app._current_tab():
            return
        from ..search_contract import records_from_filters
        section = app._current_section()
        section.search_type = scope['searchType']
        section.base_filters = ()
        self.tab.table_view = scope['view']
        self.tab.view_mode = 'continious'
        reload = force or self.tab.extra_filters != scope['filters']
        if reload:
            self.tab.sort_mode = 'column:' + scope['orderBy'] + ':asc'
            self.tab.extra_filters = list(scope['filters'])
            self.tab.filter_records = records_from_filters(scope['filters'])
            self.tab.limit = scope['initialLimit']
            self.tab.offset = self.tab.next_offset = 0
            self.tab.failure_count = 0
            self.tab.loaded = False
        if reload:
            app.refresh_current()
        else:
            app._show_or_load_tab(self.tab, content_only=True)

    @Slot()
    def reload_item_results(self):
        self.show_items(force=True)

    @Slot()
    def load_item_page(self):
        app = self.services._application
        if self.tab is app._current_tab() and app.has_more and not self.tab.loading:
            app._load_tab(self.tab, append=True)

    @Property('QVariantMap', notify=changed)
    def tableModels(self):
        return {**{key: scope.model for key, scope in self.scopes.items()}, **self._report_models}

    @Slot(str)
    def close_page(self, key):
        if key not in self.pages or self.runner:
            return
        self.drop_page(key)
        if self.pages:
            self.select_page(next(reversed(self.pages)))
        elif not self.workspace:
            self.services._application.window_model.close_window('table_document')

    def drop_page(self, key):
        page = self.pages.pop(key)
        for name, scope in page['scopes'].items():
            self.services._nested_scopes.pop(('workspace:' if self.workspace else '') + key + ':' + name, None)
            scope.shutdown()
            scope.deleteLater()

    @Slot(str, int, result=QObject)
    def table(self, key, revision=0):
        return self.scopes.get(key)

    @Slot('QVariantMap')
    def set_state(self, state):
        if not self.runner:
            self.document_data['layoutState'] = dict(state)
            self.notify_document()

    @Slot('QVariantMap')
    def activate(self, action):
        if action.get('name') == 'script':
            self.run(action.get('javascript') or '', action.get('selector') or '')
        elif action.get('name') == 'layout-link':
            self.services._application.open_rich_link(action.get('href') or '')
        else:
            document = self.document_data
            self.services._application.invoke_table_widget_action(
                action.get('name') or '', document.get('nodeId') or '', document
            )

    def run(self, source, selector=''):
        from thlib import tactic_classes as tc
        from .scripts import TableScriptRunner

        services, app = self.services, self.services._application
        if (
            not source
            or self.runner
            or services._busy
            or self.tab is not app._current_tab()
        ):
            return
        document = self.document_data
        context = dict(
            self.context,
            searchKey=document['targetSearchKey'],
            searchType=document['targetSearchKey'].split('?')[0],
            view=document['layoutView'],
            layoutState=document['layoutState'],
            layoutUser=document.get('layoutUser'),
            layoutTrigger=selector,
        )
        try:
            server = tc.server_start(project=context['project'])
        except PermissionError as error:
            services.report_error(str(error))
            return
        runner = TableScriptRunner(server, context, services.scriptProgress.emit)
        self.runner = runner
        generation = self.generation
        document.update(layoutBusy=True, layoutError='')
        self.notify_document()

        def settled():
            if generation != self.generation:
                return
            self.runner = None
            self.document_data.update(layoutBusy=False, layoutError=services.error)
            self.notify_document()

        def loaded(result):
            if generation != self.generation or self.tab is not app._current_tab():
                return
            if result.get('confirmation'):
                raise ValueError(
                    'This layout action requires an explicit confirmation control'
                )
            close = False
            for command in result['commands']:
                kind = command['type']
                if kind == 'layout-state':
                    document['layoutState'] = command['state']
                elif kind in ('message', 'log'):
                    app._notify(command['text'])
                elif kind == 'close-layout':
                    close = True
                    services.completed.emit(document['targetSearchKey'])
                    app.refresh_current()
                elif kind == 'print-layout':
                    QTimer.singleShot(
                        0,
                        lambda: (
                            self.print_report()
                            if generation == self.generation
                            else None
                        ),
                    )
                elif kind == 'refresh':
                    for scope in self.scopes.values():
                        scope.reload()
                else:
                    raise ValueError('Unsupported layout command: ' + kind)
            if close:
                if self.workspace:
                    app.close_section(app._current_section_key)
                else:
                    app.window_model.close_window('table_document')

        services._run(lambda: runner.run(source), loaded, settled)

    def print_report(self):
        from thlib import tactic_classes as tc
        from .report import print_report

        generation = self.generation
        document = dict(self.document_data)
        try:
            server = tc.server_start(project=self.context['project'])
        except PermissionError as error:
            self.services.report_error(str(error))
            self.document_data['layoutError'] = str(error)
            self.notify_document()
            return
        self.document_data.update(layoutBusy=True, layoutError='')
        self.notify_document()

        def settled():
            if generation == self.generation:
                self.document_data.update(
                    layoutBusy=False, layoutError=self.services.error
                )
                self.notify_document()

        def loaded(result):
            if (
                generation == self.generation
                and self.tab is self.services._application._current_tab()
            ):
                print_report(result['info'])

        self.services._run(
            lambda: server.execute_cmd(
                'tactic.ui.table.CustomLayoutReportCmd',
                dict(
                    search_key=document['targetSearchKey'], view=document['layoutView']
                ),
            ),
            loaded,
            settled,
        )
