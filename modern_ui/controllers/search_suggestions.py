"""Application controller: search suggestions."""

from __future__ import annotations

from collections.abc import Callable
import json
import math
import re
import sys
import time
import traceback
from urllib.parse import parse_qsl, urlparse
import uuid

from PySide6.QtCore import (
    QDateTime,
    QObject,
    Property,
    QSettings,
    Qt,
    QTimer,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QGuiApplication, QImage

from ..menu_schema import MenuRegistry
from ..quick_filters import QuickFilterCatalog
from ..repository_sync import RepositorySyncController
from ..search_contract import (
    create_search_tab,
    filters_from_records,
    records_from_filters,
)
from ..models import NavigationModel, ProjectModel
from ..workspace import (
    DockPanelModel,
    FloatingWindowModel,
    SectionTab,
    SectionTabModel,
    WorkspaceItemModel,
    WorkspaceState,
)
from .types import ActionRegistry, SearchTabSession, SectionSession

class SearchSuggestionsMixin:
    @staticmethod
    def _resolve_search_key(value: str):
        import thlib.tactic_classes as tc

        value = str(value or "").strip()
        if value.startswith("skey://"):
            return tc.parce_skey(value)
        if "?" not in value or not ("code=" in value or "id=" in value):
            return None, None
        parsed = tc.split_search_key(value)
        project_code = parsed.get("project_code")
        search_type = value.partition("?")[0]
        filters = []
        if parsed.get("asset_code"):
            filters.append(("code", "=", parsed["asset_code"]))
        elif parsed.get("id"):
            filters.append(("id", "=", parsed["id"]))
        result = tc.get_sobjects(
            search_type,
            filters=filters,
            project_code=project_code,
            limit=1,
        )
        if not result or not result[0]:
            return None, None
        sobject = next(iter(result[0].values()))
        info = sobject.get_info()
        return {
            "namespace": search_type.partition("/")[0],
            "pipeline_code": search_type.partition("/")[2],
            "project": project_code,
            "code": info.get("code") or parsed.get("asset_code"),
            "type": "sobject",
        }, sobject

    def _active_stype(self):
        tab = self._current_tab()
        if tab and tab.stype:
            return tab.stype
        section = self._current_section()
        if not section:
            return None
        try:
            from thlib.environment import env_inst
            project = env_inst.projects.get(self._current_project_code)
            return project.stypes.get(section.search_type) if project and project.stypes else None
        except (AttributeError, KeyError, TypeError):
            return None

    @staticmethod
    def _suggestion_spec(stype, text: str) -> tuple[str, list[str], list]:
        from thlib.search_helpers import get_suggestion_filter

        columns_info = (stype.get_columns_info() or {}) if stype else {}
        suggest_column = "name"
        if suggest_column not in columns_info:
            suggest_column = "title"
            if suggest_column not in columns_info:
                suggest_column = "code"
        columns = [suggest_column]
        for column in ("keywords", "code", "description"):
            if column in columns_info and column not in columns:
                columns.append(column)
        filters = get_suggestion_filter(suggest_column, text, columns)
        return suggest_column, columns, filters

    @Slot(str)
    def update_search_text(self, value: str) -> None:
        """Keep draft text local until the user submits the search."""
        tab = self._current_tab()
        if not tab:
            return
        tab.search_text = value

    @Slot()
    def clear_search_suggestions(self) -> None:
        self._pending_suggestion_value = None
        if self._suggestion_worker is not None:
            self._suggestion_worker.cancel()
        self._suggestion_request_id = ""
        self.workspace_state.search_suggestion_model.clear()

    @Slot(str)
    def request_search_suggestions(self, value: str) -> None:
        """Load search suggestions through the shared server API."""
        value = (value or "").strip()
        if (
            not value
            or value.startswith("skey://")
        ):
            self.clear_search_suggestions()
            return
        stype = self._active_stype()
        if not stype:
            self.clear_search_suggestions()
            return
        suggest_column, columns, filters = self._suggestion_spec(stype, value)
        self._suggestion_column = suggest_column
        if self._suggestion_worker is not None:
            self._pending_suggestion_value = value
            self._suggestion_worker.cancel()
            return
        self._pending_suggestion_value = None
        request_id = uuid.uuid4().hex
        self._suggestion_request_id = request_id
        try:
            from thlib.environment import env_inst
            import thlib.tactic_classes as tc
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            project = stype.get_project()

            def query_suggestions():
                return (tc.server_query(
                    filters=filters,
                    stype=stype.get_code(),
                    columns=columns,
                    project=project.get_code(),
                    limit=50,
                    offset=0,
                ),)

            worker = env_inst.server_pool.add_task(query_suggestions)
            if worker is None:
                raise RuntimeError("Server worker pool is not available")
            self._suggestion_worker = worker
            worker.add_result_data((request_id, value, suggest_column))
            worker.result.connect(self._search_suggestions_result)
            worker.error.connect(self._search_suggestions_error)
            worker.settled.connect(
                self._search_suggestion_worker_settled,
                Qt.ConnectionType.QueuedConnection,
            )
            worker.start()
        except Exception as error:
            self.clear_search_suggestions()
            self._notify(str(error))

    @Slot(object)
    def _search_suggestion_worker_settled(self, worker) -> None:
        if self._suggestion_worker is worker:
            self._suggestion_worker = None
        pending = self._pending_suggestion_value
        self._pending_suggestion_value = None
        if pending:
            QTimer.singleShot(
                0,
                lambda value=pending: self.request_search_suggestions(value),
            )

    @Slot(object)
    def _search_suggestions_result(self, result) -> None:
        records, metadata = result
        request_id, key, suggest_column = metadata
        if request_id != self._suggestion_request_id:
            return
        self._suggestion_worker = None
        suggestions = []
        seen = set()
        for record in records or []:
            title = record.get(suggest_column)
            if title in (None, ""):
                continue
            title = str(title)
            code = str(record.get("code") or "")
            keywords = str(record.get("keywords") or "")
            keyword = ""
            for candidate in keywords.replace(",", " ").split():
                if candidate.find(key) != -1:
                    keyword = candidate
            description = " ".join(str(record.get("description") or "").splitlines())
            suggestion_key = (title, description, keyword)
            if suggestion_key in seen:
                continue
            seen.add(suggestion_key)
            values = {suggest_column: title}
            for column in ("keywords", "description"):
                value = record.get(column)
                if value not in (None, ""):
                    values[column] = value
            suggestions.append({
                "title": title,
                "description": description,
                "keyword": keyword,
                "code": code,
                "values": values,
                "selected": False,
            })
            if len(suggestions) >= 20:
                break
        self.workspace_state.search_suggestion_model.replace(suggestions)

    @Slot(object)
    def _search_suggestions_error(self, error) -> None:
        payload, worker = error
        metadata = worker.get_result_data() if worker else None
        if metadata and metadata[0] != self._suggestion_request_id:
            return
        self._suggestion_worker = None
        self._report_error_payload(payload, "server/search_suggestions", worker)
        self.workspace_state.search_suggestion_model.clear()
        self._notify(str(payload.get("exception") or error))

    @Slot(int)
    def accept_search_suggestion(self, row: int) -> None:
        records = self.workspace_state.search_suggestion_model._records
        tab = self._current_tab()
        if not tab or not 0 <= row < len(records):
            return
        self._capture_current_tree_state()
        record = records[row]
        values = dict(record.get("values") or {})
        selected_value = values.get(self._suggestion_column) or record.get("title")
        tab.title = str(record.get("title") or selected_value or "")
        tab.search_text = tab.title
        self._set_primary_search_filter(tab.search_text, relation="=")
        tab.offset = 0
        tab.loaded = False
        tab.workspace_roots.clear()
        self._sync_search_tabs()
        self.clear_search_suggestions()
        self._load_tab(tab)

    @Slot(str)
    def search(self, value: str) -> None:
        value = (value or "").strip()
        if value.startswith("skey://") or ("?" in value and ("code=" in value or "id=" in value)):
            self.clear_search_suggestions()
            self._search_by_key(value)
            return
        if self._skey_worker is not None:
            self._skey_worker.cancel()
            self._skey_worker = None
        self._skey_request_id = ""
        section = self._current_section()
        tab = self._current_tab()
        if not section or not tab:
            return
        self._capture_current_tree_state()
        self._set_primary_search_filter(value)
        tab.title = value or section.title
        tab.search_text = value
        tab.offset = 0
        tab.loaded = False
        tab.workspace_roots.clear()
        self.clear_search_suggestions()
        self._sync_search_tabs()
        self._load_tab(tab, append=False)

    @Slot(str)
    def open_search_key(self, value: str) -> None:
        value = str(value or "").strip()
        if value:
            self._search_by_key(value)

    @Slot(str, str)
    def open_search_key_in_process(self, value: str, process: str) -> None:
        value = str(value or "").strip()
        if value:
            self._search_by_key(value, str(process or "").strip())

    @staticmethod
    def _local_search_key_identity(value: str) -> dict | None:
        if value.startswith("skey://"):
            parsed_url = urlparse(value)
            search_type = (
                f"{parsed_url.netloc}/{parsed_url.path.lstrip('/')}"
            )
            values = dict(parse_qsl(parsed_url.query))
        elif "?" in value:
            search_type, _, query = value.partition("?")
            values = dict(parse_qsl(query))
        else:
            return None
        if not values.get("code") or search_type.endswith("/snapshot"):
            return None
        namespace, separator, pipeline_code = search_type.partition("/")
        if not separator or not namespace or not pipeline_code:
            return None
        return {
            "namespace": namespace,
            "pipeline_code": pipeline_code,
            "project": values.get("project") or values.get("project_code"),
            "code": values["code"],
            "type": "sobject",
        }

    def _search_by_key(self, value: str, navigation_process: str = "") -> None:
        if self._skey_worker is not None:
            self._skey_worker.cancel()
            self._skey_worker = None
        local = self._local_search_key_identity(value)
        if local and (
            not local.get("project")
            or local.get("project") == self._current_project_code
        ):
            search_type = (
                f"{local['namespace']}/{local['pipeline_code']}"
            )
            loaded = self._loaded_search_key_target(
                search_type,
                str(local["code"]),
            )
            if loaded:
                section, tab, sobject = loaded
                self._skey_request_id = ""
                self._activate_loaded_search_key(
                    section,
                    tab,
                    sobject,
                    local,
                    navigation_process,
                )
                return
        request_id = uuid.uuid4().hex
        self._skey_request_id = request_id
        started_at = time.perf_counter()
        try:
            from thlib.environment import env_inst
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()

            def resolve():
                parsed, sobject = self._resolve_search_key(value)
                if not parsed or not sobject:
                    raise LookupError("TACTIC item was not found")
                prepared_project = None
                project_code = (
                    parsed.get("project") or parsed.get("project_code")
                )
                if request_id != self._skey_request_id:
                    return parsed, sobject, None
                if project_code and project_code != self._current_project_code:
                    target = env_inst.projects.get(project_code)
                    if not target:
                        raise LookupError(
                            f"Project is not available: {project_code}"
                        )
                    prepared_project = self._prepare_project_selection(
                        target.get_code(),
                        target.get_title() or target.get_code(),
                    )
                return parsed, sobject, prepared_project

            self._set_loading(True, "Resolving TACTIC search key")
            worker = env_inst.server_pool.add_task(resolve)
            if worker is None:
                raise RuntimeError("Server worker pool is not available")
            self._skey_worker = worker
            worker.add_result_data((
                request_id, value, started_at, navigation_process,
            ))
            worker.result.connect(self._skey_result)
            worker.error.connect(self._skey_error)
            worker.start()
        except Exception as error:
            self._set_loading(False, f"Search key failed: {error}")
            self._notify(str(error))

    def _ordered_search_tabs(self, search_type: str):
        sections = list(self._sessions.values())
        current = self._current_section()
        if current in sections:
            sections.remove(current)
            sections.insert(0, current)
        for section in sections:
            if section.search_type != search_type:
                continue
            tabs = list(section.tabs)
            current_tab = next(
                (
                    tab for tab in tabs
                    if tab.tab_id == section.current_tab_id
                ),
                None,
            )
            if current_tab in tabs:
                tabs.remove(current_tab)
                tabs.insert(0, current_tab)
            for tab in tabs:
                yield section, tab

    def _loaded_search_key_target(self, search_type: str, code: str):
        for section, tab in self._ordered_search_tabs(search_type):
            if not tab.loaded:
                continue
            for sobject in self._visible_sobjects(tab, section):
                if str(sobject.get_code() or "") == code:
                    return section, tab, sobject
        return None

    def _unfiltered_search_key_section(
        self,
        search_type: str,
        title: str,
        accent: str,
    ) -> SectionSession:
        sections = list(self._sessions.values())
        current = self._current_section()
        if current in sections:
            sections.remove(current)
            sections.insert(0, current)
        def is_unfiltered(candidate: SectionSession) -> bool:
            entry = self.navigation_model.entry(candidate.entry_key)
            return not entry or not entry.filter_records

        section = next(
            (
                candidate for candidate in sections
                if candidate.search_type == search_type
                and not candidate.base_filters
                and is_unfiltered(candidate)
            ),
            None,
        )
        if section:
            return section
        entry = next(
            (
                candidate
                for candidate in self.navigation_model.entries_for_search_type(
                    search_type
                )
                if not candidate.filter_records
            ),
            None,
        )
        if entry:
            return self._create_section(
                entry.key,
                entry.title or title,
                entry.accent or accent,
            )
        return self._create_section(
            f"{search_type}@direct",
            title,
            accent,
        )

    def _prepare_search_key_tab(
        self,
        section: SectionSession,
        title: str,
        code: str,
        parsed: dict,
        navigation_process: str = "",
    ) -> SearchTabSession:
        tab = next(
            (
                candidate for candidate in section.tabs
                if candidate.tab_kind == "navigation"
            ),
            None,
        )
        direct_base = (
            len(section.tabs) == 1
            and section.entry_key.endswith("@direct")
            and section.tabs[0].tab_kind == "base"
            and not section.tabs[0].loaded
            and not section.tabs[0].extra_filters
        )
        if tab is None and direct_base:
            tab = section.tabs[0]
        if tab is None:
            tab = create_search_tab(
                section.entry_key,
                title,
                tab_id=(
                    f"{section.entry_key}:navigation:"
                    f"{uuid.uuid4().hex[:8]}"
                ),
                tab_kind="navigation",
                limit=self._page_size,
                view_mode=self._default_view_mode,
                filters=[("code", "=", code)],
                navigation_target=code,
            )
            section.tabs.append(tab)
        tab.title = title
        tab.tab_kind = "navigation"
        tab.navigation_target = code
        tab.search_text = ""
        tab.filter_records = records_from_filters([("code", "=", code)])
        tab.extra_filters = filters_from_records(tab.filter_records)
        tab.offset = 0
        tab.next_offset = 0
        tab.total = 0
        tab.exhausted = False
        tab.duplicate_pages = 0
        tab.sobjects.clear()
        tab.stype = None
        tab.loaded = False
        tab.request_id = uuid.uuid4().hex
        tab.workspace_roots.clear()
        tab.tree_state.clear()
        tab.selected_node_id = ""
        tab.selected_node_ids.clear()
        tab.selection_anchor_id = ""
        tab.loading = False
        tab.error = ""
        tab.cancelled = False
        tab.failure_count = 0
        tab.failure_signature = ""
        tab.quick_filters.clear()
        tab.selected_tags.clear()
        tab.tag_column = ""
        tab.pending_snapshot_code = (
            str(parsed.get("item_code") or "")
            if parsed.get("type") == "snapshot" else ""
        )
        tab.pending_snapshot_process = (
            str(parsed.get("context") or "").partition("/")[0]
            if parsed.get("type") == "snapshot" else ""
        )
        tab.pending_detail_process = str(navigation_process or "")
        tab.clear_details()
        section.current_tab_id = tab.tab_id
        return tab

    def _activate_loaded_search_key(
        self,
        section: SectionSession,
        tab: SearchTabSession,
        sobject,
        parsed: dict,
        navigation_process: str = "",
    ) -> None:
        search_key = str(sobject.get_search_key() or "")
        tab.selected_node_id = search_key
        tab.selected_node_ids = [search_key]
        tab.selection_anchor_id = search_key
        tab.clear_details()
        tab.pending_snapshot_code = (
            str(parsed.get("item_code") or "")
            if parsed.get("type") == "snapshot" else ""
        )
        tab.pending_snapshot_process = (
            str(parsed.get("context") or "").partition("/")[0]
            if parsed.get("type") == "snapshot" else ""
        )
        tab.pending_detail_process = str(navigation_process or "")
        section.current_tab_id = tab.tab_id
        self.activate_section(section.entry_key)

    @Slot(object)
    def _skey_result(self, result) -> None:
        parsed, sobject, prepared_project, metadata = result
        request_id, _value, started_at, navigation_process = metadata
        if request_id != self._skey_request_id:
            return
        self._skey_worker = None
        try:
            if prepared_project:
                self._apply_selected_project(*prepared_project)
            search_type = f"{parsed.get('namespace')}/{parsed.get('pipeline_code')}"
            stype = sobject.get_stype()
            title = stype.get_pretty_name() if stype else search_type
            accent = (
                stype.get_stype_color(fmt="hex") or ""
                if stype else ""
            )
            code = str(parsed.get("code") or sobject.get_code() or "")
            loaded = self._loaded_search_key_target(search_type, code)
            if loaded:
                section, tab, loaded_sobject = loaded
                self._activate_loaded_search_key(
                    section,
                    tab,
                    loaded_sobject,
                    parsed,
                    navigation_process,
                )
            else:
                section = self._unfiltered_search_key_section(
                    search_type,
                    title,
                    accent,
                )
                tab = self._prepare_search_key_tab(
                    section,
                    str(sobject.get_title() or code or "Search key"),
                    code,
                    parsed,
                    navigation_process,
                )
                self.activate_section(section.entry_key)
            if parsed.get("type") == "snapshot":
                self.dock_model.show_panel("snapshot")
            self._set_loading(
                False,
                "Search key resolved · {}".format(
                    self._transaction_metrics(started_at)
                ),
            )
        except Exception as error:
            self._set_loading(False, f"Search key failed: {error}")
            self._notify(str(error))

    @Slot(object)
    def _skey_error(self, error) -> None:
        payload, worker = error
        metadata = worker.get_result_data() if worker else ()
        if not metadata or metadata[0] != self._skey_request_id:
            return
        self._skey_worker = None
        self._report_error_payload(payload, "server/search_key", worker)
        message = str(payload.get("exception") or error)
        self._set_loading(False, f"Search key failed: {message}")
        self._notify(message)
