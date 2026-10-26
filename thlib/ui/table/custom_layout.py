"""A configured native document owns its embedded tables and script lifetime."""

from PySide6.QtCore import QObject, Slot, QTimer, Signal, Property


class CustomLayoutController(QObject):
    changed = Signal()

    def __init__(self, services):
        super().__init__(services)
        self.services = services
        self.scopes = {}
        self.runner = None
        self.tab = None
        self.context = {}
        self.generation = 0
        self.pages = {}
        self.current = ''

    @Slot(QObject, 'QVariantMap')
    def format_document(self, document, style):
        from ..rich_text_document import format_readonly_document
        format_readonly_document(document, style)

    def close(self):
        self.generation += 1
        if self.runner:
            self.runner.cancel()
            self.runner = None
        for key, scope in tuple(self.services._nested_scopes.items()):
            if not hasattr(scope, 'layout_page'):
                continue
            self.services._nested_scopes.pop(key, None)
            scope.shutdown()
            scope.deleteLater()
        self.scopes.clear()
        self.pages.clear()
        self.current = ''
        self.services._nested_changed()
        self.context = {}
        self.tab = None

    def open(self, tab, context, tab_key=''):
        from .nested import NestedTableController

        if not tab_key or (self.tab is not None and self.tab is not tab):
            self.close()
        elif tab_key in self.pages:
            self.select_page(tab_key)
            return
        for scope in self.scopes.values():
            scope.open = False
            scope.suspend()
        self.scopes = {}
        self.tab, self.context = tab, dict(context)
        document = self.services._document
        self.current = tab_key
        document['layoutState'] = dict(
            form=document.get('layoutForm') or '',
            root={},
            controls=document.get('layoutControls') or [],
        )

        def tables(items, prefix='customLayout'):
            for index, item in enumerate(items):
                key = prefix + '_' + str(index)
                if item['kind'] == 'table':
                    scope = NestedTableController(
                        self.services, document['nodeId'], item['table']
                    )
                    scope.document_generation = self.services._document_generation
                    scope.layout_page = tab_key
                    scope.open = True
                    scope.changed.connect(self.changed)
                    self.scopes[key] = scope
                    self.services._nested_scopes[tab_key + ':' + key] = scope
                    scope.reload()
                else:
                    tables(item.get('children') or [], key)

        tables(document.get('layoutNodes') or [])
        if tab_key:
            self.pages[tab_key] = dict(
                document=document, scopes=self.scopes, context=self.context
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

    def _tabs(self):
        self.services._document['layoutTabs'] = [
            dict(key=key, title=page['document']['title'])
            for key, page in self.pages.items()
        ]
        self.services._document['layoutTabKey'] = self.current

    @Slot(str, 'QVariantMap')
    def open_cell(self, node_id, cell):
        services, app = self.services, self.services._application
        node = app._node_for_any(node_id)
        if node is None or not cell.get('layoutNodes'):
            return
        services._document_generation += 1
        services._document = dict(
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
        services.documentChanged.emit()
        app.open_window('table_document')

    def open_view(self, view, title, key):
        from thlib import tactic_classes as tc
        from .requests import read_custom_layout

        services, app = self.services, self.services._application
        tab, project = app._current_tab(), app._current_project_code
        try:
            server = tc.server_start(project=project)
        except PermissionError as error:
            services.report_error(str(error))
            return
        services._document_generation += 1
        generation = services._document_generation

        def loaded(result):
            if (
                generation != services._document_generation
                or tab is not app._current_tab()
                or project != app._current_project_code
            ):
                return
            self.open_result(result, title, key)

        services._run(
            lambda: tc.execute_procedure_serverside(
                read_custom_layout, dict(view=view), project=project, server=server
            ),
            loaded,
        )

    def open_result(self, result, title, key):
        services, app = self.services, self.services._application
        services._document_generation += 1
        services._document = dict(result, title=title, nodeId='', translateTitle=False)
        self.open(app._current_tab(), dict(project=app._current_project_code,
            searchKey=result['targetSearchKey'], record=result['layoutRecord']), key)
        services.documentChanged.emit()
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
        self.current, self.scopes, self.context = key, page['scopes'], page['context']
        self.services._document = page['document']
        for scope in self.scopes.values():
            scope.document_generation = self.services._document_generation
            scope.open = True
        self._tabs()
        self.services._nested_changed()
        self.services.documentChanged.emit()
        self.changed.emit()

    @Property('QVariantMap', notify=changed)
    def tableModels(self):
        return {key: scope.model for key, scope in self.scopes.items()}

    @Slot(str)
    def close_page(self, key):
        if key not in self.pages or self.runner:
            return
        page = self.pages.pop(key)
        for name, scope in page['scopes'].items():
            self.services._nested_scopes.pop(key + ':' + name, None)
            scope.shutdown()
            scope.deleteLater()
        if self.pages:
            self.select_page(next(reversed(self.pages)))
        else:
            self.services._application.window_model.close_window('table_document')

    @Slot(str, int, result=QObject)
    def table(self, key, revision=0):
        return self.scopes.get(key)

    @Slot('QVariantMap')
    def set_state(self, state):
        if not self.runner:
            self.services._document['layoutState'] = dict(state)
            self.services.documentChanged.emit()

    @Slot('QVariantMap')
    def activate(self, action):
        if action.get('name') == 'script':
            self.run(action.get('javascript') or '', action.get('selector') or '')
        elif action.get('name') == 'layout-link':
            self.services._application.open_rich_link(action.get('href') or '')
        else:
            document = self.services._document
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
        document = services._document
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
        services.documentChanged.emit()

        def settled():
            if generation != self.generation:
                return
            self.runner = None
            services._document.update(layoutBusy=False, layoutError=services.error)
            services.documentChanged.emit()

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
                app.window_model.close_window('table_document')

        services._run(lambda: runner.run(source), loaded, settled)

    def print_report(self):
        from thlib import tactic_classes as tc
        from .report import print_report

        generation = self.generation
        document = dict(self.services._document)
        try:
            server = tc.server_start(project=self.context['project'])
        except PermissionError as error:
            self.services.report_error(str(error))
            self.services._document['layoutError'] = str(error)
            self.services.documentChanged.emit()
            return
        self.services._document.update(layoutBusy=True, layoutError='')
        self.services.documentChanged.emit()

        def settled():
            if generation == self.generation:
                self.services._document.update(
                    layoutBusy=False, layoutError=self.services.error
                )
                self.services.documentChanged.emit()

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
