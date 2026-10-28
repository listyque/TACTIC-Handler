"""Native layout authoring; Frame owns the UI and all structural XML edits."""
from __future__ import annotations

import copy
import re
from urllib.parse import quote, urlencode, urlsplit
from xml.dom import minidom

from PySide6.QtCore import QObject, Property, Qt, Signal, Slot, QUrl, QTimer
from PySide6.QtGui import QDesktopServices

from .admin.layout_editor_api import layout_editor_request
from .server_address import normalize_tactic_server_url, is_valid_tactic_server_url
from .source_editor import SourceEditorService


def layout_tree(source):
    if not isinstance(source, str) or not source.strip():
        raise ValueError('Select a SObject layout configuration')
    if len(source.encode('utf8')) > 512 * 1024:
        raise ValueError('Invalid configuration XML')
    if re.search(r'<!DOCTYPE|<!ENTITY', source, re.I):
        raise ValueError('Document types and XML entities are not supported')
    document = minidom.parseString(source)
    if document.documentElement.tagName != 'config':
        raise ValueError('Invalid configuration XML')

    def convert(node):
        if node.nodeType == 1:
            return dict(type=1, name=node.tagName,
                        attributes=[[name, node.getAttribute(name)] for name in node.attributes.keys()],
                        children=[convert(child) for child in node.childNodes])
        if node.nodeType == 9:
            return dict(type=9, children=[convert(child) for child in node.childNodes])
        if node.nodeType in (3, 4, 7, 8):
            value = dict(type=node.nodeType, text=node.data)
            if node.nodeType == 7:
                value['name'] = node.target
            return value
        raise ValueError('Unsupported XML node')

    try:
        return convert(document)
    finally:
        document.unlink()


class LayoutEditorHost(QObject):
    stateChanged = Signal()
    committed = Signal()

    def __init__(self, application, parent=None, *, previews=None):
        super().__init__(parent)
        self._application = application
        self._previews = previews
        self._source_editor = SourceEditorService(self)
        self._project = ''
        self._generation = 0
        self._worker = self._callbacks = None
        self._closed = False
        from .workspace_models.results import WorkspaceItemModel
        self._preview_model = WorkspaceItemModel()
        self._preview_model.setParent(self)
        self._preview_workers = set()
        self._draft_serial = 0
        self._sample_generation = 0
        self._sample_filters = None
        self._draft_worker = None
        self._draft_timer = QTimer(self)
        self._draft_timer.setSingleShot(True)
        self._draft_timer.setInterval(250)
        self._draft_timer.timeout.connect(self._resolve_draft)
        self._reset_state()
        if previews is not None:
            previews.previewReady.connect(self._preview_ready)
            previews.previewsReady.connect(self._previews_ready)

    def _reset_state(self):
        self._pending_reference = None
        self._loaded = False
        self._loaded_scope = None
        self._types = []
        self._search_type = self._preferred_type = ''
        self._view = 'continuous_example'
        self._configuration = None
        self._source = ''
        self._xml = self._baseline = ''
        self._tree = None
        self._parse_error = ''
        self._templates = []
        self._sample_items = []
        self._sample_error = ''
        self._draft_error = ''
        self._preview = None
        self._live_interface = None
        self._checked = self._diff = self._error = self._message = ''
        self._uncertain = self._presentation_dirty = self._project_unavailable = False
        self._pending_template = None

    @Property(QObject, constant=True)
    def sourceEditor(self):
        return self._source_editor

    @Property(QObject, constant=True)
    def previewModel(self):
        return self._preview_model

    @Property(QObject, constant=True)
    def application(self):
        return self._application if isinstance(self._application, QObject) else None

    @Property(bool, notify=stateChanged)
    def dirty(self):
        return self._xml != self._baseline or self._presentation_dirty or self._uncertain

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._worker is not None

    @Property(bool, notify=stateChanged)
    def projectUnavailable(self):
        return self._project_unavailable

    @Property(bool, notify=stateChanged)
    def canWrite(self):
        return bool(self._application.can_manage_tools and self._configuration and self._loaded_scope == (self._project, self._search_type, self._view))

    @Property(bool, notify=stateChanged)
    def writeUncertain(self):
        return self._uncertain

    @Property('QVariantMap', notify=stateChanged)
    def model(self):
        from thlib.environment import env_server
        base = normalize_tactic_server_url(env_server.get_server())
        parts = urlsplit(base)
        return dict(project=self._project, searchTypes=copy.deepcopy(self._types),
                    searchType=self._search_type, view=self._view, configuration=copy.deepcopy(self._configuration),
                    source=self._source, xml=self._xml, tree=copy.deepcopy(self._tree), parseError=self._parse_error,
                    templates=copy.deepcopy(self._templates), sampleItems=copy.deepcopy(self._sample_items),
                    sampleError=self._sample_error, previewError=self._draft_error, preview=copy.deepcopy(self._preview),
                    liveInterface=copy.deepcopy(self._live_interface), checked=self._checked,
                    diff=self._diff, error=self._error or self._draft_error, message=self._message, busy=self.busy,
                    dirty=self.dirty, uncertain=self._uncertain, canWrite=self.canWrite,
                    canLoad=bool(self._application.can_manage_tools and self._project),
                    assetBase=parts.scheme + '://' + parts.netloc if parts.netloc else '')

    def activate(self, project):
        if project != self._project:
            self.reset(project)
        if not self._loaded and not self.busy and project:
            self._request('catalog')

    def preview_scope(self, project, search_type, view, filters=None):
        self.reset(project)
        self._preferred_type, self._view = search_type, view
        self._sample_filters = copy.deepcopy(filters or [])
        self._request('catalog')

    def reset(self, project=''):
        self._sample_filters = None
        self._generation += 1
        self._sample_generation += 1
        self._draft_serial += 1
        self._draft_timer.stop()
        self._preview_model.replace_nodes([])
        self._release(cancel=True)
        self._project = project
        self._reset_state()
        if project and self._application.can_manage_tools:
            tab = self._application._current_tab()
            self._preferred_type = tab.stype.get_code() if tab and tab.stype else ''
            self._select_type()
        self.stateChanged.emit()

    def _select_type(self):
        self._search_type = self._preferred_type if self._preferred_type in {row['value'] for row in self._types} else (self._types[0]['value'] if self._types else '')

    def _release(self, cancel=False):
        if self._worker:
            if self._callbacks:
                self._worker.result.disconnect(self._callbacks[0])
                self._worker.error.disconnect(self._callbacks[1])
            if cancel:
                self._worker.cancel()
        self._worker = self._callbacks = None

    def _parse(self):
        self._tree = None
        self._parse_error = ''
        try:
            self._tree = layout_tree(self._xml)
        except Exception as error:
            self._parse_error = str(error)

    @Slot(str)
    def set_xml(self, text):
        if self.busy or self._uncertain or not self._configuration or not self._application.can_manage_tools or self._loaded_scope != (self._project, self._search_type, self._view) or text == self._xml:
            return
        self._xml = text
        self._checked = self._diff = self._error = self._message = ''
        self._preview = None
        self._parse()
        self._schedule_preview()
        self.stateChanged.emit()

    @Slot(str)
    def initialize_xml(self, text):
        if self._configuration and not self.busy and not self._xml and not self._baseline and self._loaded_scope == (self._project, self._search_type, self._view):
            self._xml = self._baseline = text
            self._parse()
            self.stateChanged.emit()

    @Slot(bool)
    def set_presentation_dirty(self, pending):
        if self._presentation_dirty != bool(pending):
            self._presentation_dirty = bool(pending)
            self.stateChanged.emit()

    def _select_source(self, source):
        self._source = source
        configuration = self._configuration or {}
        selected = next((row['xml'] for row in configuration.get('sources', []) if row['id'] == source), None)
        inherited = next((row['xml'] for row in configuration.get('layers', []) if row.get('view') == self._view and 'sobject-layout' in row.get('xml', '')), None)
        # A generated blank override is supplied by the common reducer when needed.
        self._xml = self._baseline = selected or inherited or ''
        self._checked = self._diff = self._error = self._message = ''
        self._preview = None
        self._presentation_dirty = False
        self._parse()
        self._schedule_preview()

    @Slot('QVariant')
    def select_source(self, source):
        if not self.busy and not self.dirty and self._configuration:
            if source != '':
                # QML QVariant numbers arrive as doubles; retain the server's integer id.
                selected = next((row for row in self._configuration.get('sources', [])
                                 if row['id'] == source and not isinstance(source, bool)), None)
                if selected is None:
                    return
                source = selected['id']
            self._select_source(source)
            self.stateChanged.emit()

    @Slot(str, str)
    def set_context(self, field, value):
        if self.busy or self.dirty or field not in ('searchType', 'view'):
            return
        if field == 'searchType':
            if value not in {row['value'] for row in self._types}:
                return
            self._search_type = value
        elif not re.fullmatch(r'[A-Za-z_][\w.@-]{0,127}', value):
            return
        else:
            self._view = value
        self._pending_template = None
        self._loaded = False
        self.reload()

    @Slot(str, str, 'QVariant')
    def open_reference(self, search_type: str, view: str, source=None) -> None:
        if (self.busy or self.dirty or not self._application.can_manage_tools
                or search_type not in {row['value'] for row in self._types}
                or not re.fullmatch(r'[A-Za-z_][\w.@-]{0,127}', view)):
            return
        if search_type != self._search_type:
            self._sample_filters = None
        self._search_type, self._view = search_type, view
        self._pending_template = None
        self._pending_reference = dict(source=source)
        self._request('read')

    @Slot(str, str)
    def new_view(self, view, xml):
        if self.busy or self.dirty or not self._configuration or not re.fullmatch(r'[A-Za-z_][\w.@-]{0,127}', view):
            return
        self._view = view
        self._loaded = False
        self._pending_template = (self._search_type, view, xml)
        self.reload()

    @Slot()
    @Slot(bool)
    def reload(self, force=False):
        if self.busy or self.dirty and not force:
            return
        self._request('read' if self._search_type else 'catalog')

    @Slot()
    def discard(self):
        if self.busy:
            return
        if self._uncertain:
            self.reload(True)
        else:
            self._presentation_dirty = False
            self._select_source(self._source)
            self.stateChanged.emit()

    @Slot()
    def check(self):
        if not self.busy and not self._uncertain and self._configuration and self._loaded_scope == (self._project, self._search_type, self._view) and not self._presentation_dirty and not self._parse_error:
            self._request('preview')

    @Slot()
    def save(self):
        if not self.busy and not self._uncertain and self._configuration and self._loaded_scope == (self._project, self._search_type, self._view) and self.dirty and not self._presentation_dirty and self._checked == self._xml:
            self._request('save')

    def _request(self, action):
        if self._closed or self.busy or not self._application.can_manage_tools or not self._project or (action != 'catalog' and not self._search_type):
            return
        from thlib import tactic_classes as tc
        from thlib.environment import env_inst
        try:
            server = tc.server_start(project=self._project)
        except Exception as error:
            self._error = str(error)
            self.stateChanged.emit()
            return
        self._generation += 1
        generation, project, search_type, view, xml = self._generation, self._project, self._search_type, self._view, self._xml
        reference = self._pending_reference if action == 'read' else None
        if action == 'read':
            self._pending_reference = None
        procedure = layout_editor_request
        parameters = dict(action=action, project_code=project, search_type=search_type, view=view)
        if action == 'read' and self._sample_filters is not None:
            parameters['filters'] = copy.deepcopy(self._sample_filters)
        if action not in ('read', 'catalog'):
            parameters.update(source_id=self._source if self._source != '' else None, xml=xml, revision=self._configuration['revision'])
        self._error = self._message = ''
        self._project_unavailable = False
        if action == 'read':
            self._loaded = False
            self._configuration = None
            self._sample_generation += 1
            self._live_interface = None
            self._preview_model.replace_nodes([])

        def operation():
            if generation != self._generation or self._closed:
                raise RuntimeError('Layout request was cancelled')
            execute = tc.execute_procedure_serverside if action == 'save' else tc._execute_read_only_procedure_serverside
            result = execute(procedure, parameters, project=project, server=server)
            if action == 'read' and result.get('sampleItems'):
                from .controllers.search_runtime import SearchRuntimeMixin
                keys = [item['record']['code'] for item in result['sampleItems'] if item.get('record', {}).get('code')]
                if keys:
                    objects, _info, stype = SearchRuntimeMixin._query_sobjects(
                        search_type, project, (), [('code', 'in', keys)], 3, 0)
                    order = {code: index for index, code in enumerate(keys)}
                    objects.sort(key=lambda item: order.get(item.get_info().get('code'), len(order)))
                    result = dict(result, nativeObjects=objects, nativeSType=stype)
            if action == 'save':
                from thlib import server_cache
                server_cache.invalidate_domains(('reference', 'search'), project)
            return result

        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            self._error = self.tr('Server worker pool is unavailable')
            self.stateChanged.emit()
            return
        self._worker = worker

        def loaded(result):
            if generation != self._generation or self._closed:
                return
            self._release()
            try:
                if action == 'catalog':
                    records = result['stypes']
                    if not isinstance(records, list) or any(not isinstance(row, dict) or not isinstance(row.get('code'), str) or not row['code'] or not isinstance(row.get('__record_read__') or {}, dict) for row in records):
                        raise ValueError('Invalid Search Type catalog response')
                    options = [dict(value=row['code'], label=str(row.get('title') or row['code'])) for row in records if (row.get('__record_read__') or {}).get('available') is not False]
                elif action == 'preview':
                    if not isinstance(result['interface'], dict):
                        raise ValueError('Invalid layout preview response')
                else:
                    configuration = result['configuration'] if action == 'read' else result
                    if not isinstance(configuration.get('revision'), str) or not isinstance(configuration.get('sources'), list):
                        raise ValueError('Invalid layout configuration response')
                    if reference is not None:
                        if view not in configuration.get('layout_views', []):
                            raise ValueError(self.tr('Referenced item layout is unavailable'))
                        source = reference['source']
                        if source not in (None, '') and not any(row['id'] == source and not isinstance(source, bool) for row in configuration['sources']):
                            raise ValueError(self.tr('The original configuration source is unavailable'))
                    templates = [dict(row, tree=layout_tree(row['xml'])) for row in configuration.get('layout_templates', [])]
            except Exception as error:
                self._uncertain = action == 'save'
                self._error = 'The save result is unknown. Refresh before trying again.' if self._uncertain else str(error)
                self.stateChanged.emit()
                return
            if action == 'catalog':
                self._types = sorted(options, key=lambda row: row['label'].lower())
                self._select_type()
                self._loaded = not bool(self._search_type)
                self.stateChanged.emit()
                if self._search_type:
                    self.reload()
                return
            if action == 'preview':
                self._preview, self._checked, self._diff = result['interface'], xml, result.get('diff', '')
                self._live_interface = self._preview
            else:
                self._configuration = configuration
                self._loaded_scope = (project, search_type, view)
                self._templates = templates
                self._uncertain = False
                self._loaded = True
                source = configuration['sources'][0]['id'] if configuration['sources'] else ''
                self._select_source(reference['source'] if reference is not None and reference['source'] is not None else source)
                if action == 'read':
                    self._preview_model.replace_sobjects(result.get('nativeObjects') or [], result.get('nativeSType'))
                    self._prepare_preview_images()
                    self._sample_items = copy.deepcopy(result.get('sampleItems', []))
                    self._sample_error = str(result.get('sampleError') or '')
                    for item in self._sample_items:
                        if isinstance(item.get('preview'), dict):
                            item['preview'].pop('local', None)
                    if self._pending_template and self._pending_template[:2] == (search_type, view):
                        self._xml = self._pending_template[2]
                        self._baseline = ''
                        self._source = ''
                        self._pending_template = None
                        self._parse()
                    self._resolve_previews()
                    self._schedule_preview()
                else:
                    self._message = 'Layout saved'
                    self.committed.emit()
            self.stateChanged.emit()

        def failed(error):
            if generation != self._generation or self._closed:
                return
            self._release()
            payload, _worker = error
            self._uncertain = action == 'save'
            exception = payload.get('exception') or error
            self._error = 'The save result is unknown. Refresh before trying again.' if self._uncertain else str(exception)
            lowered = str(exception).lower()
            self._project_unavailable = 'database [' in lowered and '] does not exist' in lowered
            self.stateChanged.emit()
            if self._application.debug_log:
                self._application.debug_log.raise_error(exception, stacktrace=payload.get('stacktrace', ''), group='administration/layouts')

        self._callbacks = loaded, failed
        worker.result.connect(loaded, Qt.QueuedConnection)
        worker.error.connect(failed, Qt.QueuedConnection)
        self.stateChanged.emit()
        try:
            worker.start()
        except Exception as error:
            self._release()
            self._error = str(error)
            self.stateChanged.emit()

    def _resolve_previews(self):
        if self._previews is None or self._closed:
            return
        for item in self._sample_items:
            key = (item.get('record') or {}).get('__search_key__')
            if not key:
                continue
            rows = self._previews.records_for_text('skey://' + key)
            if rows and rows[0].get('previewUrl'):
                item['preview'] = dict(item.get('preview') or {}, image=rows[0]['previewUrl'], local=True)

    def _schedule_preview(self):
        self._draft_serial += 1
        self._draft_error = ''
        self._draft_timer.start()

    def _prepare_preview_images(self):
        from thlib.environment import env_inst
        model, generation = self._preview_model, self._sample_generation
        requests = []
        for node in model._items:
            if node.node_type not in ('sobject', 'snapshot'):
                continue
            pending = model.begin_preview_request(node.node_id)
            if pending:
                kind, source = pending
                requests.append((node.node_id, kind, source, model.preview_request_token(node.node_id)))
        if not requests:
            return

        def prepare():
            return [(identity, source, token, model.prepare_preview(kind, source))
                    for identity, kind, source, token in requests]

        worker = env_inst.server_pool.add_task(prepare)
        if worker is None:
            for identity, _kind, source, token in requests:
                model.cancel_preview_request(identity, source, token)
            return
        self._preview_workers.add(worker)

        def loaded(result):
            self._preview_workers.discard(worker)
            if not self._closed and generation == self._sample_generation:
                for identity, source, token, candidates in result:
                    model.apply_preview(identity, source, candidates, token)

        def failed(error):
            self._preview_workers.discard(worker)
            if not self._closed and generation == self._sample_generation:
                for identity, _kind, source, token in requests:
                    model.cancel_preview_request(identity, source, token)
                payload, _ = error
                self._sample_error = str(payload.get('exception') or error)
                self.stateChanged.emit()

        worker.result.connect(loaded, Qt.QueuedConnection)
        worker.error.connect(failed, Qt.QueuedConnection)
        worker.start()

    def _resolve_draft(self):
        if self._closed or self.busy or not self._configuration or self._parse_error or not self._xml:
            return
        if self._draft_worker is not None:
            self._draft_timer.start()
            return
        from thlib import tactic_classes as tc
        from thlib.environment import env_inst
        generation, serial, xml = self._generation, self._draft_serial, self._xml
        project = self._project
        parameters = dict(action='preview', project_code=project, search_type=self._search_type,
                          view=self._view, source_id=None if self._source == '' else self._source,
                          xml=xml, revision=self._configuration['revision'])
        server = tc.server_start(project=project)
        worker = env_inst.server_pool.add_task(lambda: tc._execute_read_only_procedure_serverside(
            layout_editor_request, parameters, project=project, server=server))
        if worker is None:
            return
        self._preview_workers.add(worker)
        self._draft_worker = worker

        def loaded(result):
            self._preview_workers.discard(worker)
            self._draft_worker = None
            if not self._closed and generation == self._generation and serial == self._draft_serial and xml == self._xml:
                self._preview = result['interface']
                self._live_interface = self._preview
                self.stateChanged.emit()

        def failed(error):
            self._preview_workers.discard(worker)
            self._draft_worker = None
            if not self._closed and generation == self._generation and serial == self._draft_serial:
                payload, _ = error
                self._draft_error = str(payload.get('exception') or error)
                self.stateChanged.emit()

        worker.result.connect(loaded, Qt.QueuedConnection)
        worker.error.connect(failed, Qt.QueuedConnection)
        worker.start()

    @Slot(str, bool)
    def toggle_result_node_recursive(self, node_id, recursive=False):
        if self._closed or self.busy:
            return
        model, generation = self._preview_model, self._sample_generation
        node = model._nodes.get(node_id)
        if not node or not node.has_children or node.loading:
            return
        if node.loaded:
            model.toggle_node(node_id)
            return
        from thlib.environment import env_inst
        worker = env_inst.server_pool.add_task(lambda: model.load_node(node_id))
        if worker is None:
            return
        self._preview_workers.add(worker)
        model.set_node_loading(node_id, True)

        def loaded(result):
            self._preview_workers.discard(worker)
            if not self._closed and generation == self._sample_generation:
                model.set_node_loading(node_id, False)
                identity, _loaded, prepared = result
                if model.apply_loaded_node(identity, prepared):
                    model.toggle_node(identity)
                    self._prepare_preview_images()

        def failed(error):
            self._preview_workers.discard(worker)
            if not self._closed and generation == self._sample_generation:
                model.set_node_loading(node_id, False)
                payload, _ = error
                self._sample_error = str(payload.get('exception') or error)
                self.stateChanged.emit()

        worker.result.connect(loaded, Qt.QueuedConnection)
        worker.error.connect(failed, Qt.QueuedConnection)
        worker.start()

    def _preview_ready(self, _key, _record):
        self._resolve_previews()
        self.stateChanged.emit()

    def _previews_ready(self, _records):
        self._resolve_previews()
        self.stateChanged.emit()

    @Slot()
    def open_view(self):
        if self.dirty or self.busy or not self._configuration or not self._configuration.get('resolved', {}).get('configured'):
            return
        from thlib.environment import env_server
        base = normalize_tactic_server_url(env_server.get_server())
        if is_valid_tactic_server_url(base):
            QDesktopServices.openUrl(QUrl(base + '/projects/' + quote(self._project, safe='') + '/?' + urlencode(dict(search_type=self._search_type, view=self._view))))

    def shutdown(self):
        self._closed = True
        self._draft_timer.stop()
        for worker in self._preview_workers:
            worker.cancel()
        self._preview_workers.clear()
        self._generation += 1
        self._release(cancel=True)
        self._reset_state()
