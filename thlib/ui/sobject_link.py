from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
import uuid

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QObject,
    Property,
    Qt,
    QUrl,
    Signal,
    Slot,
)

from .search_suggestion_data import (
    SEARCH_SUGGESTION_ROLES,
    search_suggestion_records,
    search_suggestion_spec,
)


def configured_instance_relation(relation, stype) -> dict | None:
    """Return native metadata for a schema-declared instance relation.

    The path is optional save metadata, so the instance editor remains
    available when the reverse schema lookup has no matching record.
    """
    definition = dict(relation or {})
    if str(definition.get("relationship") or "") != "instance":
        return None
    instance_type = str(definition.get("instance_type") or "")
    if not instance_type or stype is None:
        return None
    try:
        target_code = str(stype.get_code() or "")
        configured = stype.get_schema().get_parent_instance(
            instance_type,
            target_code,
        )
    except (AttributeError, KeyError, TypeError):
        configured = None
    return {
        "instance_type": instance_type,
        "path": configured.get("path") if isinstance(configured, dict) else None,
    }


class LinkObjectModel(QAbstractListModel):
    """Lightweight, selectable sObject rows used by Link SObjects."""

    SearchKeyRole = Qt.UserRole + 1
    TitleRole = Qt.UserRole + 2
    SubtitleRole = Qt.UserRole + 3
    PreviewUrlRole = Qt.UserRole + 4
    FallbackTextRole = Qt.UserRole + 5
    AccentRole = Qt.UserRole + 6
    SelectedRole = Qt.UserRole + 7

    countChanged = Signal()
    selectionChanged = Signal()
    _roles = {
        SearchKeyRole: b"searchKey",
        TitleRole: b"title",
        SubtitleRole: b"subtitle",
        PreviewUrlRole: b"previewUrl",
        FallbackTextRole: b"fallbackText",
        AccentRole: b"accent",
        SelectedRole: b"selected",
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._records: list[dict] = []
        self._selection_anchor = -1

    def roleNames(self) -> dict[int, bytes]:
        return self._roles

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._records)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._records):
            return None
        key = self._roles.get(role)
        return self._records[index.row()].get(key.decode()) if key else None

    def replace(self, records) -> None:
        selected_keys = set(self.selected_keys())
        anchor_key = (
            str(self._records[self._selection_anchor].get("searchKey") or "")
            if 0 <= self._selection_anchor < len(self._records) else ""
        )
        self.beginResetModel()
        self._records = [dict(record) for record in records]
        for record in self._records:
            record["selected"] = (
                str(record.get("searchKey") or "") in selected_keys
            )
        self._selection_anchor = next((
            row for row, record in enumerate(self._records)
            if str(record.get("searchKey") or "") == anchor_key
        ), -1)
        self.endResetModel()
        self.countChanged.emit()
        self.selectionChanged.emit()

    def append(self, records) -> None:
        additions = [dict(record) for record in records]
        if not additions:
            return
        first = len(self._records)
        self.beginInsertRows(
            QModelIndex(), first, first + len(additions) - 1
        )
        for record in additions:
            record["selected"] = False
        self._records.extend(additions)
        self.endInsertRows()

    def selected_keys(self) -> list[str]:
        return [
            str(record.get("searchKey") or "")
            for record in self._records
            if record.get("selected") and record.get("searchKey")
        ]

    def clear_selection(self) -> None:
        changed = []
        for row, record in enumerate(self._records):
            if record.get("selected"):
                record["selected"] = False
                changed.append(row)
        for row in changed:
            index = self.index(row, 0)
            self.dataChanged.emit(index, index, [self.SelectedRole])
        if changed:
            self.selectionChanged.emit()

    def select(self, row: int, modifiers=0) -> bool:
        if not 0 <= row < len(self._records):
            return False
        if isinstance(modifiers, bool):
            control = modifiers
            shift = False
        else:
            flags = Qt.KeyboardModifiers(int(modifiers))
            control = bool(flags & Qt.ControlModifier)
            shift = bool(flags & Qt.ShiftModifier)
        changed = []
        if shift and 0 <= self._selection_anchor < len(self._records):
            first = min(self._selection_anchor, row)
            last = max(self._selection_anchor, row)
            for index, record in enumerate(self._records):
                selected = first <= index <= last
                if control:
                    selected = selected or bool(record.get("selected"))
                if bool(record.get("selected")) != selected:
                    record["selected"] = selected
                    changed.append(index)
        elif not control:
            for index, record in enumerate(self._records):
                selected = index == row
                if bool(record.get("selected")) != selected:
                    record["selected"] = selected
                    changed.append(index)
        else:
            record = self._records[row]
            record["selected"] = not bool(record.get("selected"))
            changed.append(row)
        self._selection_anchor = row
        for index in changed:
            model_index = self.index(index, 0)
            self.dataChanged.emit(
                model_index, model_index, [self.SelectedRole]
            )
        if changed:
            self.selectionChanged.emit()
        return bool(changed)

    def toggle(self, row: int, additive: bool) -> bool:
        return self.select(row, bool(additive))
    @Property(int, notify=countChanged)

    def count(self) -> int:
        return len(self._records)

    @Property(int, notify=selectionChanged)
    def selected_count(self) -> int:
        return len(self.selected_keys())



class LinkSearchController(QObject):
    """Independent search state for one Link SObjects panel."""

    search_text_changed = Signal()

    def __init__(self, owner, scope: str) -> None:
        super().__init__(owner)
        self._owner = owner
        self._scope = scope
        self._text = ""
        self._worker = None
        self._request_id = ""
        self._pending_value: str | None = None
        from .workspace_models.records import RecordListModel

        self.suggestion_model = RecordListModel(SEARCH_SUGGESTION_ROLES)
        self.suggestion_model.setParent(self)

    def reset(self) -> None:
        worker = self._worker
        self._worker = None
        if worker is not None:
            try:
                worker.cancel()
            except (AttributeError, RuntimeError):
                pass
        self._request_id = ""
        self._pending_value = None
        self._text = ""
        self.suggestion_model.clear()
        self.search_text_changed.emit()

    @Property(str, notify=search_text_changed)
    def current_search_text(self) -> str:
        return self._text

    @Property(QObject, constant=True)
    def suggestions(self):
        return self.suggestion_model

    @Slot(str)
    def update_search_text(self, value: str) -> None:
        value = str(value or "")
        if value == self._text:
            return
        self._text = value
        self.search_text_changed.emit()

    @Slot()
    def clear_search_suggestions(self) -> None:
        self._pending_value = None
        self._request_id = ""
        self.suggestion_model.clear()


    def _linked_suggestions(self, value: str) -> None:
        records = []
        for sobject in self._owner._linked.values():
            try:
                info = dict(sobject.get_info() or {})
                info.setdefault("name", sobject.get_title())
            except (AttributeError, KeyError, TypeError):
                continue
            if self._owner._matches(sobject, value):
                records.append(info)
        self.suggestion_model.replace(
            search_suggestion_records(records, value, "name")
        )

    @Slot(str)
    def request_search_suggestions(self, value: str) -> None:
        value = str(value or "").strip()
        if not value:
            self.clear_search_suggestions()
            return
        if self._scope == "linked":
            self._linked_suggestions(value)
            return
        stype = self._owner._context_data.get("stype")
        if stype is None:
            self.clear_search_suggestions()
            return
        if self._worker is not None:
            self._pending_value = value
            try:
                self._worker.cancel()
            except (AttributeError, RuntimeError):
                pass
            return
        suggest_column, columns, filters = search_suggestion_spec(stype, value)
        from thlib.environment import env_inst
        import thlib.tactic_classes as tc
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        request_id = uuid.uuid4().hex
        self._request_id = request_id

        def operation():
            return (tc.server_query(
                filters=filters,
                stype=stype.get_code(),
                columns=columns,
                project=stype.get_project().get_code(),
                limit=50,
                offset=0,
            ),)

        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            self.clear_search_suggestions()
            return
        self._worker = worker
        worker.add_result_data((request_id, value, suggest_column))
        worker.result.connect(self._suggestions_ready)
        worker.error.connect(self._suggestions_failed)
        worker.settled.connect(
            self._suggestions_settled,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    @Slot(object)
    def _suggestions_ready(self, result) -> None:
        records, metadata = result
        request_id, value, suggest_column = metadata
        if request_id != self._request_id:
            return
        self.suggestion_model.replace(
            search_suggestion_records(records, value, suggest_column)
        )

    @Slot(object)
    def _suggestions_failed(self, _error) -> None:
        self.suggestion_model.clear()

    @Slot(object)
    def _suggestions_settled(self, worker) -> None:
        if worker is self._worker:
            self._worker = None
        pending = self._pending_value
        self._pending_value = None
        if pending:
            self.request_search_suggestions(pending)

    @Slot(int)
    def accept_search_suggestion(self, row: int) -> None:
        record = self.suggestion_model.get(row)
        value = str(record.get("title") or "")
        if not value:
            return
        self.update_search_text(value)
        self.clear_search_suggestions()
        self.search(value)

    @Slot(str)
    def search(self, value: str) -> None:
        self.update_search_text(value)
        callback = (
            self._owner.search_available
            if self._scope == "available"
            else self._owner.search_linked
        )
        callback(value)


class SObjectLinkController(QObject):
    """Staged editor for native TACTIC instance relations."""
    stateChanged = Signal()

    sessionStarted = Signal()
    saved = Signal()

    def __init__(self, context, notify=None, repository_sync=None,
                 parent=None) -> None:
        super().__init__(parent)
        self._context = context
        self._notify = notify or (lambda _message: None)
        self._repository_sync = repository_sync
        self._context_data: dict = {}
        self._available: OrderedDict[str, object] = OrderedDict()
        self._linked: OrderedDict[str, object] = OrderedDict()
        self._initial_keys: set[str] = set()
        self._request_id = 0
        self._worker = None
        self._busy = False
        self._loading_available = False
        self._loading_linked = False
        self._dirty = False
        self._error = ""
        self._available_query = ""
        self._linked_query = ""
        self._pending_available_query: str | None = None
        self._pending_linked_query: str | None = None
        self._available_offset = 0
        self._available_total = 0
        self._page_size = 20
        self._transfer_direction = "add"
        self._target_title = ""
        self._target_code = ""
        self._parent_title = ""
        self._parent_code = ""
        self._parent_type_title = ""
        self._accent = "#607d8b"
        self._session_token = ""
        self._preview_tokens: dict[str, str] = {}
        self._preview_cache: dict[str, str] = {}
        self._script_triggers = None
        self._trigger_payload = {}
        self.available_model = LinkObjectModel(self)
        self.linked_model = LinkObjectModel(self)
        self.available_search = LinkSearchController(self, "available")
        self.linked_search = LinkSearchController(self, "linked")
        self.available_model.selectionChanged.connect(
            self._available_selection_changed
        )
        self.linked_model.selectionChanged.connect(
            self._linked_selection_changed
        )
        if repository_sync is not None:
            repository_sync.task_finished.connect(self._preview_ready)
            repository_sync.task_failed.connect(self._preview_failed)

    def attach_script_triggers(self, triggers) -> None:
        self._script_triggers = triggers

    @staticmethod
    def _search_key(sobject) -> str:
        try:
            return str(sobject.get_search_key() or "")
        except (AttributeError, KeyError, TypeError):
            return ""

    @staticmethod
    def _objects(result) -> list:
        if isinstance(result, tuple):
            result = result[0]
        if isinstance(result, dict):
            return list(result.values())
        return list(result or [])

    @staticmethod
    def _initials(value: str) -> str:
        parts = [part for part in str(value or "").replace("_", " ").split()
                 if part]
        return "".join(part[0] for part in parts[:2]).upper() or "?"

    @staticmethod
    def _local_file_url(file_object) -> str:
        try:
            path = str(file_object.get_full_abs_path() or "")
        except (AttributeError, KeyError, TypeError):
            return ""
        if path and file_object.is_local_current():
            return QUrl.fromLocalFile(str(Path(path).resolve())).toString()
        return ""

    def _preview_url(self, sobject, search_key: str) -> str:
        if search_key in self._preview_cache:
            return self._preview_cache[search_key]
        # Reuse the same native File/Snapshot presentation contract as the
        # workspace item delegate.  Link SObjects must not reconstruct a
        # repository path or invent another preview priority.
        from .workspace_models.results import WorkspaceItemModel
        try:
            candidates = WorkspaceItemModel.prepare_preview(
                "sobject", sobject
            )
        except (AttributeError, KeyError, TypeError):
            candidates = []
        for file_object in candidates:
            url = self._local_file_url(file_object)
            if url:
                self._preview_cache[search_key] = url
                return url
            if self._repository_sync is None:
                continue
            try:
                if not self._repository_sync.previews_through_http_enabled():
                    continue
                handle = self._repository_sync.schedule_file_object(
                    file_object, process="preview", auto_start=True,
                    is_ui_preview=True,
                )
            except (AttributeError, KeyError, TypeError, ValueError, OSError):
                continue
            token = f"pending-preview:{handle.task_id}"
            self._preview_tokens[token] = search_key
            self._preview_cache[search_key] = token
            return token
        self._preview_cache[search_key] = ""
        return ""

    def _record(self, sobject) -> dict:
        info = sobject.get_info() or {}
        search_key = self._search_key(sobject)
        title = str(
            sobject.get_title()
            or info.get("name")
            or info.get("title")
            or info.get("code")
            or ""
        )
        subtitle_values = []
        for key in ("description", "status"):
            value = str(info.get(key) or "").strip()
            if value and value != title and value not in subtitle_values:
                subtitle_values.append(value)
            if len(subtitle_values) >= 2:
                break
        return {
            "searchKey": search_key,
            "title": title,
            "subtitle": "  ·  ".join(subtitle_values),
            "previewUrl": self._preview_url(sobject, search_key),
            "fallbackText": self._initials(title),
            "accent": self._accent,
            "selected": False,
        }

    @staticmethod
    def _matches(sobject, query: str) -> bool:
        if not query:
            return True
        try:
            info = sobject.get_info() or {}
            values = (
                sobject.get_title(), info.get("name"), info.get("title"),
                info.get("code"), info.get("description"),
            )
        except (AttributeError, KeyError, TypeError):
            values = ()
        folded = query.casefold()
        return any(folded in str(value or "").casefold() for value in values)

    def _reset(self) -> None:
        self._request_id += 1
        self._worker = None
        self._context_data = {}
        self._available.clear()
        self._linked.clear()
        self._initial_keys.clear()
        self._available_query = ""
        self._linked_query = ""
        self._pending_available_query = None
        self._pending_linked_query = None
        self._available_offset = 0
        self._available_total = 0
        self._transfer_direction = "add"
        self._target_title = ""
        self._target_code = ""
        self._parent_title = ""
        self._parent_code = ""
        self._parent_type_title = ""
        self._accent = "#607d8b"
        self._session_token = uuid.uuid4().hex
        self._preview_tokens.clear()
        self._preview_cache.clear()
        self._busy = False
        self._loading_available = False
        self._loading_linked = False
        self._dirty = False
        self._error = ""
        self.available_search.reset()
        self.linked_search.reset()
        self.available_model.replace([])
        self.linked_model.replace([])

    @staticmethod
    def _validated_context(context: dict) -> dict:
        stype = context.get("stype")
        parent = context.get("parent_sobject")
        relation = dict(context.get("relation") or {})
        project_code = str(context.get("project_code") or "")
        if stype is None or parent is None or not project_code:
            raise ValueError("Select an instance relation first")
        if str(relation.get("relationship") or "") != "instance":
            raise ValueError("Link SObjects supports instance relations only")
        instance_type = str(relation.get("instance_type") or "")
        if not instance_type:
            raise ValueError("This relation has no instance type")
        try:
            parent_stype = parent.get_stype()
            parent_key = str(parent.get_search_key() or "")
            target_code = str(stype.get_code() or "")
            parent_code = str(parent_stype.get_code() or "")
            target_project = str(stype.get_project().get_code() or "")
        except (AttributeError, KeyError, TypeError) as error:
            raise ValueError("The relation context is incomplete") from error
        if not parent_key or not target_code or not parent_code:
            raise ValueError("The relation context is incomplete")
        if target_project != project_code:
            raise ValueError("The relation belongs to another project")
        configured = configured_instance_relation(relation, stype)
        if configured is None:
            raise ValueError("The instance relationship is not configured")
        path = configured.get("path")
        validated = dict(context)
        validated.update({
            "relation": relation,
            "instance_type": instance_type,
            "path": path,
            "parent_stype": parent_stype,
            "parent_key": parent_key,
            "search_type": target_code,
        })
        return validated

    @Slot()
    def begin_session(self) -> None:
        self._reset()
        try:
            context = self._validated_context(dict(self._context() or {}))
        except (ValueError, AttributeError, KeyError, TypeError) as error:
            self._set_error(str(error))
            return
        self._context_data = context
        stype = context["stype"]
        parent = context["parent_sobject"]
        try:
            self._target_title = str(
                stype.get_pretty_name()
                or stype.info.get("title")
                or stype.get_code()
            )
        except (AttributeError, KeyError, TypeError):
            self._target_title = str(context["search_type"])
        self._target_code = str(context["search_type"])
        try:
            self._parent_title = str(parent.get_title() or parent.get_code())
            self._parent_code = str(parent.get_code() or "")
        except (AttributeError, KeyError, TypeError):
            self._parent_title = ""
            self._parent_code = ""
        parent_stype = context.get("parent_stype")
        try:
            self._parent_type_title = str(
                parent_stype.get_pretty_name()
                or parent_stype.info.get("title")
                or parent_stype.get_code()
            )
        except (AttributeError, KeyError, TypeError):
            try:
                self._parent_type_title = str(
                    parent_stype.get_code() or ""
                )
            except (AttributeError, KeyError, TypeError):
                self._parent_type_title = ""
        try:
            self._accent = str(stype.get_stype_color(fmt="hex") or "#607d8b")
        except (AttributeError, KeyError, TypeError):
            self._accent = "#607d8b"
        self.sessionStarted.emit()
        self.stateChanged.emit()
        self._load_linked()
        self._load_available(0, append=False)

    def _start_worker(self, callback, result_handler, failure_handler=None) -> None:
        from thlib.environment import env_inst
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(callback)
        self._worker = worker
        worker.result.connect(
            result_handler,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            failure_handler or self._request_failed,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    def _load_linked(self, force: bool = False) -> None:
        if not self._context_data or self._loading_linked:
            return
        self._request_id += 1
        request_id = self._request_id
        session = self._session_token
        context = dict(self._context_data)
        self._loading_linked = True
        self._busy = True
        self._error = ""
        self.stateChanged.emit()

        def operation():
            parent = context["parent_sobject"]
            kwargs = dict(
                child_stype=context["stype"],
                parent_stype=context["parent_stype"],
                path="child",
                get_all_snapshots=False,
            )
            if force:
                kwargs["force"] = True
            return parent.get_related_sobjects(**kwargs)

        self._start_worker(
            operation,
            lambda result: self._linked_loaded(
                session, request_id, result
            ),
            lambda error: self._linked_failed(session, request_id, error),
        )

    def _load_available(self, offset: int, append: bool) -> None:
        if not self._context_data or self._loading_available:
            return
        self._request_id += 1
        request_id = self._request_id
        session = self._session_token
        context = dict(self._context_data)
        query = self._available_query
        offset = max(0, int(offset))
        self._loading_available = True
        self._busy = True
        self._error = ""
        self.stateChanged.emit()

        def operation():
            import thlib.tactic_classes as tc
            filters = [("name", "EQI", query)] if query else []
            return tc.get_sobjects(
                context["search_type"],
                filters=filters,
                order_bys=["name"],
                project_code=context["project_code"],
                limit=self._page_size,
                offset=offset,
                get_all_snapshots=False,
                include_snapshots=True,
                include_info=True,
            )

        self._start_worker(
            operation,
            lambda result: self._available_loaded(
                session, request_id, query, offset, append, result
            ),
            lambda error: self._available_failed(session, request_id, error),
        )

    @staticmethod
    def _result_info(result) -> dict:
        return dict(result[1] or {}) if isinstance(result, tuple) and len(result) > 1 else {}

    def _linked_loaded(self, session: str, _request_id: int, result) -> None:
        if session != self._session_token:
            return
        linked = OrderedDict()
        for sobject in self._objects(result):
            search_key = self._search_key(sobject)
            if search_key:
                linked[search_key] = sobject
        self._linked = linked
        self._initial_keys = set(linked)
        for search_key in list(self._available):
            if search_key in linked:
                self._available.pop(search_key, None)
        self._dirty = False
        self._loading_linked = False
        self._finish_load()
        self._sync_models()

    def _available_loaded(self, session: str, _request_id: int,
                          query: str, offset: int, append: bool, result) -> None:
        if session != self._session_token or query != self._available_query:
            return
        # Do not flash results for an obsolete query while a newer value is
        # already waiting for this request to finish.
        if self._pending_available_query is not None:
            self._loading_available = False
            self._finish_load()
            return
        previous_visible_keys = {
            key for key in self._available if key not in self._linked
        } if append else set()
        records = OrderedDict(self._available if append else {})
        for sobject in self._objects(result):
            search_key = self._search_key(sobject)
            if search_key and search_key not in self._linked:
                records[search_key] = sobject
        self._available = records
        info = self._result_info(result)
        self._available_offset = offset + len(self._objects(result))
        total = info.get("total_sobjects_count")
        if total is None:
            total = info.get("total_sobjects_query_count")
        self._available_total = int(total or self._available_offset)
        self._loading_available = False
        self._finish_load()
        # During initial loading the linked-key baseline is authoritative for
        # duplicate removal.  Keep the candidate pane covered by its loader
        # until that baseline arrives instead of briefly showing linked rows.
        if not self._loading_linked:
            if append:
                self.available_model.append([
                    self._record(sobject)
                    for key, sobject in self._available.items()
                    if key not in self._linked
                    and key not in previous_visible_keys
                ])
                self.stateChanged.emit()
            else:
                self._sync_models()

    def _finish_load(self) -> None:
        self._busy = self._loading_available or self._loading_linked
        self._worker = None if not self._busy else self._worker
        self.stateChanged.emit()
        if self._pending_available_query is not None and not self._loading_available:
            query = self._pending_available_query
            self._pending_available_query = None
            self._available_query = query
            self._available.clear()
            self._available_offset = 0
            self._load_available(0, append=False)
        if self._pending_linked_query is not None:
            self._linked_query = self._pending_linked_query
            self._pending_linked_query = None
            self._sync_models()

    def _failure_message(self, error) -> str:
        payload = error[0] if isinstance(error, (tuple, list)) else error
        if isinstance(payload, dict):
            return str(payload.get("exception") or payload.get("message") or payload)
        return str(payload or "The server request failed")

    def _linked_failed(self, session: str, _request_id: int, error) -> None:
        if session != self._session_token:
            return
        self._loading_linked = False
        self._set_error(self._failure_message(error))
        # A linked-pane search may have been typed while its initial relation
        # query was running.  Even when that query fails, consume the pending
        # value so the UI never keeps an older search state indefinitely.
        self._finish_load()

    def _available_failed(self, session: str, _request_id: int, error) -> None:
        if session != self._session_token:
            return
        self._loading_available = False
        self._set_error(self._failure_message(error))
        # The latest candidate query is deliberately queued while a previous
        # page is in flight.  A failed older request must not swallow it.
        self._finish_load()

    def _request_failed(self, error) -> None:
        self._loading_available = False
        self._loading_linked = False
        self._set_error(self._failure_message(error))

    def _visible_available(self) -> list[object]:
        return [
            sobject for key, sobject in self._available.items()
            if key not in self._linked
        ]

    def _visible_linked(self) -> list[object]:
        return [
            sobject for sobject in self._linked.values()
            if self._matches(sobject, self._linked_query)
        ]

    def _sync_models(self) -> None:
        self.available_model.replace([
            self._record(sobject) for sobject in self._visible_available()
        ])
        self.linked_model.replace([
            self._record(sobject) for sobject in self._visible_linked()
        ])
        self.stateChanged.emit()

    @Slot(str)
    def search_available(self, query: str) -> None:
        value = str(query or "").strip()
        if self._loading_available:
            self._pending_available_query = value
            return
        if value == self._available_query and self._available:
            return
        self._available_query = value
        self._available.clear()
        self._available_offset = 0
        self._load_available(0, append=False)

    @Slot(str)
    def search_linked(self, query: str) -> None:
        value = str(query or "").strip()
        if self._loading_linked:
            self._pending_linked_query = value
            return
        if value == self._linked_query:
            return
        self._linked_query = value
        self._sync_models()

    @Slot()
    def load_more_available(self) -> None:
        if self.can_load_more and not self._loading_available:
            self._load_available(self._available_offset, append=True)

    @Slot(int, int)
    def select_available(self, row: int, modifiers: int) -> None:
        if self.available_model.select(row, modifiers):
            self._transfer_direction = "add"
            self.linked_model.clear_selection()
            self.stateChanged.emit()

    @Slot(int, int)
    def select_linked(self, row: int, modifiers: int) -> None:
        if self.linked_model.select(row, modifiers):
            self._transfer_direction = "remove"
            self.available_model.clear_selection()
            self.stateChanged.emit()

    def _available_selection_changed(self) -> None:
        if self.available_model.selected_count:
            self._transfer_direction = "add"
            self.stateChanged.emit()

    def _linked_selection_changed(self) -> None:
        if self.linked_model.selected_count:
            self._transfer_direction = "remove"
            self.stateChanged.emit()

    @Slot()
    def transfer_selected(self) -> None:
        if not self._can_stage_links():
            return
        if self._transfer_direction == "remove":
            self._remove_keys(self.linked_model.selected_keys())
        else:
            self._add_keys(self.available_model.selected_keys())

    def _add_keys(self, keys) -> None:
        for search_key in dict.fromkeys(str(key) for key in keys if key):
            sobject = self._available.pop(search_key, None)
            if sobject is not None:
                self._linked[search_key] = sobject
        self._dirty = set(self._linked) != self._initial_keys
        self._transfer_direction = "add"
        self._sync_models()

    def _remove_keys(self, keys) -> None:
        for search_key in dict.fromkeys(str(key) for key in keys if key):
            sobject = self._linked.pop(search_key, None)
            if sobject is not None:
                self._available[search_key] = sobject
        self._dirty = set(self._linked) != self._initial_keys
        self._transfer_direction = "remove"
        self._sync_models()

    def _can_stage_links(self) -> bool:
        return not self._loading_linked and (
            not self._busy or self._loading_available
        )

    @Slot("QVariantList")
    def add_keys(self, keys) -> None:
        if self._can_stage_links():
            self._add_keys(keys)

    @Slot("QVariantList")
    def remove_keys(self, keys) -> None:
        if self._can_stage_links():
            self._remove_keys(keys)

    @Slot(str)
    def add(self, search_key: str) -> None:
        if self._can_stage_links():
            self._add_keys([search_key])

    @Slot(str)
    def remove(self, search_key: str) -> None:
        if self._can_stage_links():
            self._remove_keys([search_key])

    @Slot()
    def save(self) -> None:
        if self._busy or not self._dirty or not self._context_data:
            return
        current_keys = set(self._linked)
        insert_keys = sorted(current_keys - self._initial_keys)
        exclude_keys = sorted(self._initial_keys - current_keys)
        context = dict(self._context_data)
        session = self._session_token
        self._trigger_payload = {
            "project_code": str(context.get("project_code") or ""),
            "search_key": str(context.get("parent_key") or ""),
            "search_type": str(context.get("parent_type") or ""),
            "insert_search_keys": insert_keys,
            "exclude_search_keys": exclude_keys,
            "instance_type": str(context.get("instance_type") or ""),
            "path": str(context.get("path") or ""),
        }
        self._busy = True
        self._error = ""
        self.stateChanged.emit()

        triggers = self._script_triggers
        if triggers is not None:
            def start(success: bool, error: str) -> None:
                if not success:
                    self._busy = False
                    self._error = str(error or "Script trigger failed")
                    self.stateChanged.emit()
                    return
                self._save_now(
                    context, session, insert_keys, exclude_keys
                )

            triggers.run_before(
                "relation.update", self._trigger_payload, start
            )
            return
        self._save_now(context, session, insert_keys, exclude_keys)

    def _save_now(
        self, context: dict, session: str,
        insert_keys: list[str], exclude_keys: list[str],
    ) -> None:

        def operation():
            from thlib import server_cache
            import thlib.tactic_classes as tc
            result = tc.edit_multiple_instance_sobjects(
                context["project_code"],
                insert_search_keys=insert_keys,
                exclude_search_keys=exclude_keys,
                parent_key=context["parent_key"],
                instance_type=context["instance_type"],
                path=context.get("path"),
            )
            server_cache.invalidate_domains(
                ("relations", "search", "activity"),
                context["project_code"],
            )
            return result

        self._start_worker(
            operation,
            lambda _result: self._save_finished(session),
            lambda error: self._save_failed(session, error),
        )

    def _save_finished(self, session: str) -> None:
        if session != self._session_token:
            return
        self._busy = False
        self._dirty = False
        self._initial_keys = set(self._linked)
        self._worker = None
        refresh = self._context_data.get("refresh")
        if callable(refresh):
            refresh()
        self._notify("Links updated")
        self.stateChanged.emit()
        self.saved.emit()
        if self._script_triggers is not None:
            self._script_triggers.run_after(
                "relation.update", self._trigger_payload
            )

    def _save_failed(self, session: str, error) -> None:
        if session != self._session_token:
            return
        self._set_error(self._failure_message(error))
        self._notify(self._error)

    @Slot()
    def refresh(self) -> None:
        if self._busy or not self._context_data:
            return
        self._available.clear()
        self._linked.clear()
        self._initial_keys.clear()
        self._available_offset = 0
        self._preview_cache.clear()
        self._preview_tokens.clear()
        self._dirty = False
        self._error = ""
        self._sync_models()
        self._load_linked(force=True)
        self._load_available(0, append=False)

    @Slot(str, str)
    def _preview_ready(self, task_id: str, local_path: str) -> None:
        token = f"pending-preview:{task_id}"
        search_key = self._preview_tokens.pop(token, "")
        if not search_key or not local_path:
            return
        ready_url = QUrl.fromLocalFile(str(Path(local_path).resolve())).toString()
        self._preview_cache[search_key] = ready_url
        self._replace_preview(search_key, ready_url)

    @Slot(str)
    def _preview_failed(self, task_id: str) -> None:
        token = f"pending-preview:{task_id}"
        search_key = self._preview_tokens.pop(token, "")
        if search_key:
            self._preview_cache[search_key] = ""
            self._replace_preview(search_key, "")

    def _replace_preview(self, search_key: str, value: str) -> None:
        for model in (self.available_model, self.linked_model):
            for row, record in enumerate(model._records):
                if record.get("searchKey") != search_key:
                    continue
                record["previewUrl"] = value
                index = model.index(row, 0)
                model.dataChanged.emit(index, index, [model.PreviewUrlRole])

    def _set_error(self, message: str) -> None:
        self._busy = self._loading_available or self._loading_linked
        self._worker = None if not self._busy else self._worker
        self._error = str(message or "The server request failed")
        self.stateChanged.emit()

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(bool, notify=stateChanged)
    def loading_available(self) -> bool:
        return self._loading_available

    @Property(bool, notify=stateChanged)
    def loading_linked(self) -> bool:
        return self._loading_linked

    @Property(bool, notify=stateChanged)
    def dirty(self) -> bool:
        return self._dirty

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error

    @Property(str, notify=stateChanged)
    def transfer_direction(self) -> str:
        return self._transfer_direction

    @Property(int, notify=stateChanged)
    def selected_count(self) -> int:
        return (
            self.available_model.selected_count
            if self._transfer_direction == "add"
            else self.linked_model.selected_count
        )

    @Property(bool, notify=stateChanged)
    def can_transfer(self) -> bool:
        return self._can_stage_links() and self.selected_count > 0

    @Property(bool, notify=stateChanged)
    def can_load_more(self) -> bool:
        return self._available_offset < self._available_total

    @Property(int, notify=stateChanged)
    def available_total(self) -> int:
        return self._available_total

    @Property(QObject, constant=True)
    def available_search_controller(self):
        return self.available_search

    @Property(QObject, constant=True)
    def linked_search_controller(self):
        return self.linked_search

    @Property("QVariantList", notify=stateChanged)
    def available_selected_keys(self) -> list[str]:
        return self.available_model.selected_keys()

    @Property("QVariantList", notify=stateChanged)
    def linked_selected_keys(self) -> list[str]:
        return self.linked_model.selected_keys()

    @Property(str, notify=stateChanged)
    def target_title(self) -> str:
        return self._target_title

    @Property(str, notify=stateChanged)
    def target_code(self) -> str:
        return self._target_code

    @Property(str, notify=stateChanged)
    def parent_title(self) -> str:
        return self._parent_title

    @Property(str, notify=stateChanged)
    def parent_code(self) -> str:
        return self._parent_code

    @Property(str, notify=stateChanged)
    def parent_type_title(self) -> str:
        return self._parent_type_title

    @Property(str, notify=stateChanged)
    def accent(self) -> str:
        return self._accent
