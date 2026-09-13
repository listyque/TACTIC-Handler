from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
import time
import unittest
from unittest.mock import patch

from PySide6.QtCore import QObject

from thlib.ui.controllers.search_tabs import SearchTabsMixin
from thlib.ui.search_contract import (
    create_search_tab,
    filters_from_records,
    records_from_filters,
    set_primary_name,
)
from thlib.ui.controllers.navigation import NavigationMixin
from thlib.ui.controllers.tab_switch_performance import SearchTabSwitchMonitor
from thlib.ui.controllers.search_runtime import SearchRuntimeMixin
from thlib.ui.controllers.types import SearchTabSession, SectionSession
from thlib.ui.workspace_models.state_project_state import ProjectStateMixin
from thlib.ui.workspace_models.state import WorkspaceState
from thlib.ui.request_metrics import request_metrics


class _RecordModel:
    def __init__(self):
        self.records = []

    def replace(self, records):
        self.records = [dict(record) for record in records]


class _ProjectState(ProjectStateMixin):
    def __init__(self):
        self.columns_model = _RecordModel()
        self.filter_column_model = _RecordModel()
        self.filter_relation_model = _RecordModel()


class _SearchType:
    _columns = {
        "name": {"data_type": "varchar"},
        "title": {"data_type": "varchar"},
        "code": {"data_type": "varchar"},
    }

    def __init__(self):
        self.columns_info_calls = 0

    def get_columns_info(self):
        self.columns_info_calls += 1
        return self._columns

    def get_column_data_type(self, column):
        return self._columns[column]["data_type"]


class _NavigationCacheHarness(NavigationMixin):
    _loading_mode = "infinite"
    _page_size = 25
    _default_view_mode = "continious"

    @staticmethod
    def _default_search_filter_record():
        from thlib.ui.search_contract import default_name_record
        return default_name_record()


class _SearchTabsHarness(SearchTabsMixin):
    def __init__(self, standard_starts_load):
        current = create_search_tab(
            "demo/assets", "Assets", tab_kind="base", limit=25,
            view_mode="continious",
        )
        self.section = SectionSession(
            entry_key="demo/assets", title="Assets", accent="#fff",
            search_type="demo/assets", tabs=[current],
            current_tab_id=current.tab_id,
        )
        self._page_size = 25
        self._default_view_mode = "continious"
        self.load_calls = []

        def emit():
            if standard_starts_load:
                self.section.tabs[-1].loading = True

        self.section_state_changed = SimpleNamespace(emit=emit)

    def _current_section(self):
        return self.section

    def _current_tab(self):
        return next(
            tab for tab in self.section.tabs
            if tab.tab_id == self.section.current_tab_id
        )

    def _capture_current_tree_state(self, persist_tree=False):
        pass

    def _capture_current_workspace_layout(self):
        current = next(
            tab for tab in self.section.tabs
            if tab.tab_id == self.section.current_tab_id
        )
        current.workspace_layout = {"layout": "current"}

    def _sync_search_tabs(self):
        pass

    def _load_tab(self, tab):
        self.load_calls.append(tab)


class _LoadingNavigationHarness(NavigationMixin):
    def __init__(self):
        self._card_path = []
        self._pending_card_focus_id = ""
        self.workspace_model = SimpleNamespace(
            set_process_ignore=lambda _value: None
        )
        self.versions_model = SimpleNamespace(clear=lambda: None)
        self.workspace_state = SimpleNamespace(clear_selection=lambda: None)
        self.load_calls = []
        self.restore_calls = []
        self.state_calls = []

    def _configure_result_organization(self, _tab, rebuild=True):
        pass

    def _set_result_state(self, tab):
        self.state_calls.append(tab)

    def _load_tab(self, tab, append=False):
        self.load_calls.append((tab, append))

    def _restore_cached_tab(self, tab):
        self.restore_calls.append(tab)


class _CacheWriterHarness(NavigationMixin):
    def __init__(self, tab):
        section = SectionSession(
            entry_key="demo/assets",
            title="Assets",
            accent="#fff",
            search_type="demo/assets",
            tabs=[tab],
            current_tab_id=tab.tab_id,
        )
        self._current_project_code = "demo"
        self._settings = {"workspace/cacheProcessTabs": True}
        self._sessions = {section.entry_key: section}
        self._current_section_key = section.entry_key
        self._search_cache = {}
        self.writes = 0

    def _capture_current_tree_state(self, persist_tree=False):
        pass

    def _write_search_cache_config(self):
        self.writes += 1


class _PerTabModelHarness(NavigationMixin, QObject):
    def __init__(self):
        QObject.__init__(self)
        first = SearchTabSession(tab_id="first", title="First")
        second = SearchTabSession(tab_id="second", title="Second")
        self.section = SectionSession(
            entry_key="demo/assets",
            title="Assets",
            accent="#fff",
            search_type="demo/assets",
            tabs=[first, second],
            current_tab_id=first.tab_id,
        )
        self.repository_sync = None

    def _current_section(self):
        return self.section


class _CachedResultHarness(SearchRuntimeMixin):
    def __init__(self, tab):
        section = SectionSession(
            entry_key="demo/assets",
            title="Assets",
            accent="#fff",
            search_type="demo/assets",
            tabs=[tab],
            current_tab_id=tab.tab_id,
        )
        self._sessions = {section.entry_key: section}
        self._current_section_key = "another-section"
        self._search_workers = {}
        self._active_request_id = ""
        self._server_state = "online"
        self.saved = 0
        self.load_calls = []
        self.detail_loads = []
        self.viewport_restores = []
        self._card_path = []
        self._pending_card_focus_id = ""
        self._versions_request_id = ""
        self.workspace_state = SimpleNamespace(
            load_stype=lambda _stype: None,
            clear_selection=lambda: None,
        )
        self.versions_model = SimpleNamespace(clear=lambda: None)
        self.section_state_changed = SimpleNamespace(emit=lambda: None)
        self._search_tab_switch_monitor = SimpleNamespace(
            record_phase=lambda _name, _duration: None,
        )
        self.search_state_changed = SimpleNamespace(emit=lambda: None)
        self.quick_filters_changed = SimpleNamespace(emit=lambda: None)

    @property
    def workspace_model(self):
        return self._current_tab().workspace_model

    def _current_section(self):
        return self._sessions.get(self._current_section_key)

    def _current_tab(self):
        section = self._current_section()
        if section is None:
            return None
        return next(
            candidate for candidate in section.tabs
            if candidate.tab_id == section.current_tab_id
        )

    @staticmethod
    def _ensure_tab_workspace_model(tab):
        if tab.workspace_model is None:
            tab.workspace_model = _RetainedWorkspaceModel([])
        return tab.workspace_model

    @staticmethod
    def _configure_result_organization(
        _tab, model=None, rebuild=True,
    ):
        del model, rebuild

    @staticmethod
    def _visible_sobjects(tab, section=None):
        del section
        return list(tab.sobjects)

    @staticmethod
    def _set_result_state(_tab):
        pass

    def _load_sobject_details(self, search_key, **_kwargs):
        self.detail_loads.append(search_key)

    def _restore_result_viewport(self, tab):
        self.viewport_restores.append(tab.tab_id)

    def _save_search_cache(self):
        self.saved += 1

    def _load_tab(self, tab, append=False):
        self.load_calls.append((tab, append))


class _LoadedNavigationHarness(NavigationMixin):
    def __init__(self):
        self._card_path = []
        self._pending_card_focus_id = ""
        self._versions_request_id = ""
        self.replace_calls = []
        self.projection_restores = []
        self.organization_rebuilds = []
        self.load_calls = []
        self.detail_loads = []
        self.viewport_restores = []
        self.workspace_model = SimpleNamespace(
            _roots=[],
            set_process_ignore=lambda _value: None,
            restore_projection=lambda projection:
                self.projection_restores.append(projection)
                or projection is not None,
            replace_nodes=lambda nodes, stype, preserve_slots=False:
                self.replace_calls.append((nodes, stype, preserve_slots)),
            replace_sobjects=lambda values, stype, preserve_slots=False:
                self.replace_calls.append((values, stype, preserve_slots)),
            node_for=lambda _node_id: None,
            show_card_level=lambda: None,
        )
        self.workspace_model.capture_projection = lambda: SimpleNamespace(
            owner_model=self.workspace_model
        )
        self.versions_model = SimpleNamespace(clear=lambda: None)
        self.workspace_state = SimpleNamespace(
            load_stype=lambda _stype: None,
            clear_selection=lambda: None,
        )
        self.section_state_changed = SimpleNamespace(emit=lambda: None)
        self._search_tab_switch_monitor = SimpleNamespace(
            record_phase=lambda _name, _duration: None
        )

    def _configure_result_organization(self, _tab, rebuild=True):
        self.organization_rebuilds.append(rebuild)

    @staticmethod
    def _visible_sobjects(tab):
        return list(tab.sobjects)

    def _set_result_state(self, _tab):
        pass

    def _restore_result_viewport(self, tab):
        self.viewport_restores.append(tab.tab_id)

    def _load_sobject_details(self, search_key, **_kwargs):
        self.detail_loads.append(search_key)

    def _load_tab(self, tab, append=False):
        self.load_calls.append((tab, append))


class _TabSwitchNavigationHarness(NavigationMixin):
    def __init__(self):
        first_layout = {
            "panels": [{"id": "tasks", "visible": True}],
            "layout": {"kind": "panel", "panel": "tasks"},
        }
        second_layout = {
            "panels": [{"id": "tasks", "visible": False}],
            "layout": {"kind": "panel", "panel": "results"},
        }
        first = SearchTabSession(
            tab_id="first", title="First", loaded=True,
            workspace_layout=deepcopy(first_layout),
        )
        second = SearchTabSession(
            tab_id="second", title="Second", loaded=True,
            workspace_layout=deepcopy(second_layout),
        )
        section = SectionSession(
            entry_key="demo/assets",
            title="Assets",
            accent="#fff",
            search_type="demo/assets",
            tabs=[first, second],
            current_tab_id=first.tab_id,
        )
        self._sessions = {section.entry_key: section}
        self._current_section_key = section.entry_key
        self._search_tab_switch_started_at = 0.0
        self._selection_load_timer = SimpleNamespace(stop=lambda: None)
        self._pending_selection_load = None
        self._detail_worker = None
        self._versions_worker = None
        self._pending_versions_node_id = ""
        self._detail_request_id = ""
        self._versions_request_id = ""
        self.workspace_model = SimpleNamespace(rowCount=lambda: 17)
        self.dock_model = _DockLayoutProbe(first_layout)
        self.events = []
        self.committed = None
        self._search_tab_switch_monitor = SimpleNamespace(
            started_at=0.0,
            metrics={"serial": 7},
            begin=self._begin_switch,
            commit=self._commit_switch,
        )

    def _begin_switch(self, _title):
        self.events.append(("begin", "second"))
        return 7

    def _capture_current_tree_state(self, persist_tree=False):
        self.events.append(("capture", persist_tree))

    def _sync_search_tabs(self, clear_suggestions=True):
        self.events.append(("sync", clear_suggestions))

    def _show_tab_if_current(self, section_key, tab_id):
        self.events.append(("show", section_key, tab_id))

    def _commit_switch(self, serial, metrics):
        self.events.append(("commit", serial))
        self.committed = dict(metrics)

    @staticmethod
    def _cancel_selected_payload_worker():
        pass

    @staticmethod
    def _cancel_versions_worker():
        pass


class _SectionSwitchNavigationHarness(NavigationMixin):
    def __init__(self):
        first_tab = SearchTabSession(
            tab_id="first-tab", title="First tab", loaded=True
        )
        second_tab = SearchTabSession(
            tab_id="second-tab", title="Second tab", loaded=True
        )
        first = SectionSession(
            entry_key="demo/first",
            title="First",
            accent="#fff",
            search_type="demo/first",
            tabs=[first_tab],
            current_tab_id=first_tab.tab_id,
        )
        second = SectionSession(
            entry_key="demo/second",
            title="Second",
            accent="#fff",
            search_type="demo/second",
            tabs=[second_tab],
            current_tab_id=second_tab.tab_id,
        )
        self._sessions = {
            first.entry_key: first,
            second.entry_key: second,
        }
        self._current_section_key = first.entry_key
        self._search_tab_switch_monitor = SearchTabSwitchMonitor()
        self.workspace_model = SimpleNamespace(rowCount=lambda: 23)
        self.events = []

    def _capture_current_tree_state(self, persist_tree=False):
        self.events.append(("capture", persist_tree))

    def _save_opened_sections(self):
        self.events.append(("save", self._current_section_key))

    @staticmethod
    def _save_search_cache():
        pass

    def _sync_section_model(self):
        self.events.append(("sections", self._current_section_key))

    def _sync_search_tabs(self, clear_suggestions=True):
        self.events.append(("tabs", clear_suggestions))

    def _show_tab_if_current(self, section_key, tab_id):
        self.events.append(("show", section_key, tab_id))


class _ProjectionCaptureHarness(NavigationMixin):
    def __init__(self):
        self.tab = SearchTabSession(
            tab_id="one", title="One", loaded=True
        )
        self._card_path = ["asset", "asset:process:publish"]
        self.viewport_captures = 0
        self.tree_serializations = 0
        self.projection = object()
        self.result_viewport_capture_requested = SimpleNamespace(
            emit=self._capture_viewport
        )
        self.workspace_model = SimpleNamespace(
            _roots=["root"],
            capture_projection=lambda: self.projection,
            collect_tree_state=self._collect_tree_state,
        )

    def _current_tab(self):
        return self.tab

    def _capture_viewport(self):
        self.viewport_captures += 1

    def _collect_tree_state(self, _selected_node_id):
        self.tree_serializations += 1
        return {"saved": True}


class _DockLayoutProbe:
    def __init__(self, layout):
        self.current = deepcopy(layout)
        self.applied = []
        self.prehidden = []

    def capture_layout(self):
        return deepcopy(self.current)

    def apply_layout(self, layout):
        restored = deepcopy(layout)
        self.applied.append(restored)
        self.current = restored
        return True

    def prehide_for_layout(self, layout):
        self.prehidden.append(deepcopy(layout))
        return True


class _RetainedWorkspaceModel:
    def __init__(self, rows):
        self._roots = list(rows)
        self.replacements = 0
        self.clear_calls = 0

    def clear(self):
        self.clear_calls += 1
        self._roots = []

    def set_process_ignore(self, _value):
        pass

    def restore_projection(self, projection):
        return getattr(projection, "owner_model", None) is self

    def replace_nodes(self, rows, _stype=None, preserve_slots=False):
        del preserve_slots
        self.replacements += 1
        self._roots = list(rows)

    def replace_sobjects(self, rows, _stype=None):
        self.replacements += 1
        self._roots = list(rows)

    def append_sobjects(self, rows, _stype=None):
        self._roots.extend(rows)

    @staticmethod
    def apply_tree_state(_tree_state):
        return [], ""

    def capture_projection(self):
        return SimpleNamespace(owner_model=self)

    @staticmethod
    def node_for(_node_id):
        return None

    @staticmethod
    def show_card_level(_node_id=""):
        pass

    def rowCount(self):
        return len(self._roots)


class _CallbackSignal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback, *_args):
        self.callbacks.append(callback)

    def emit(self, *args):
        for callback in list(self.callbacks):
            callback(*args)


class _SearchWorkerProbe:
    def __init__(self):
        self.result = _CallbackSignal()
        self.error = _CallbackSignal()
        self.settled = _CallbackSignal()
        self.metadata = None
        self.cancel_calls = 0
        self.started = False

    def add_result_data(self, metadata):
        self.metadata = metadata

    def get_result_data(self):
        return self.metadata

    def start(self):
        self.started = True

    def cancel(self):
        self.cancel_calls += 1


class _ServerPoolProbe:
    def __init__(self):
        self.is_stopped = False
        self.workers = []

    def start(self):
        self.is_stopped = False

    def add_task(self, *_args, **_kwargs):
        worker = _SearchWorkerProbe()
        self.workers.append(worker)
        return worker


class _ClearProbe:
    def __init__(self):
        self.clear_calls = 0

    def clear(self):
        self.clear_calls += 1


class _SearchRaceHarness(SearchRuntimeMixin):
    def __init__(self):
        first_tab = SearchTabSession(
            tab_id="tab-a", title="A", limit=2,
        )
        second_tab = SearchTabSession(
            tab_id="tab-b", title="B", loaded=True,
        )
        first_tab.workspace_model = _RetainedWorkspaceModel([])
        second_tab.workspace_model = _RetainedWorkspaceModel(["b-live"])
        first = SectionSession(
            entry_key="demo/a", title="A", accent="#fff",
            search_type="demo/a", tabs=[first_tab],
            current_tab_id=first_tab.tab_id,
        )
        second = SectionSession(
            entry_key="demo/b", title="B", accent="#fff",
            search_type="demo/b", tabs=[second_tab],
            current_tab_id=second_tab.tab_id,
        )
        self.first_tab = first_tab
        self.second_tab = second_tab
        self._sessions = {
            first.entry_key: first,
            second.entry_key: second,
        }
        self._current_section_key = first.entry_key
        self._current_project_code = "demo"
        self._search_workers = {}
        self._pending_search_loads = {}
        self._active_request_id = ""
        self._card_path = []
        self._pending_card_focus_id = ""
        self._versions_request_id = ""
        self._server_state = "online"
        self._loading = False
        self._loading_message = ""
        self._result_count = 0
        self.saved = 0
        self.activity = []
        self.errors = []
        self.notices = []
        self.load_more_calls = []
        self.versions_model = _ClearProbe()
        self.selection_clear_calls = 0
        self.workspace_state = SimpleNamespace(
            load_stype=lambda _stype: None,
            clear_selection=self._clear_selection,
        )
        signal = lambda: SimpleNamespace(emit=lambda *_args: None)
        self.loading_changed = signal()
        self.search_state_changed = signal()
        self.quick_filters_changed = signal()
        self.paging_state_changed = signal()
        self.result_count_changed = signal()
        self.section_state_changed = signal()

    @property
    def workspace_model(self):
        return self._current_tab().workspace_model

    def _current_section(self):
        return self._sessions.get(self._current_section_key)

    def _current_tab(self):
        section = self._current_section()
        if section is None:
            return None
        return next(
            candidate for candidate in section.tabs
            if candidate.tab_id == section.current_tab_id
        )

    @staticmethod
    def _ensure_tab_workspace_model(tab):
        return tab.workspace_model

    @staticmethod
    def _configure_result_organization(
        _tab, model=None, rebuild=True,
    ):
        del model, rebuild

    @staticmethod
    def _visible_sobjects(tab, section=None):
        del section
        return list(tab.sobjects)

    def _clear_selection(self):
        self.selection_clear_calls += 1

    def _save_search_cache(self):
        self.saved += 1

    def _append_activity(self, message):
        self.activity.append(message)

    def _report_error_payload(self, payload, group, worker):
        self.errors.append((payload, group, worker))

    def _notify(self, message):
        self.notices.append(message)

    @staticmethod
    def _transaction_metrics(*_args):
        return "0 ms"

    def _set_server_state(self, state, _message):
        self._server_state = state

    @staticmethod
    def _set_result_state(_tab):
        pass

    @staticmethod
    def _load_sobject_details(*_args, **_kwargs):
        pass

    @staticmethod
    def _restore_result_viewport(_tab):
        pass

    @staticmethod
    def _restore_tree_nodes(_nodes):
        pass

    @staticmethod
    def request_quick_filter_data():
        pass

    def load_more(self):
        current = self._current_tab()
        self.load_more_calls.append(current.tab_id if current else "")


class _SwitchMonitor:
    def __init__(self):
        self.started_at = time.perf_counter()
        self.metrics = {}
        self._serial = 0

    def begin(self, title):
        self._serial += 1
        self.started_at = time.perf_counter()
        self.metrics = {"serial": self._serial, "tab": title}
        return self._serial

    def record_phase(self, name, duration):
        self.metrics[name] = duration

    def commit(self, serial, metrics):
        if self.metrics.get("serial") == serial:
            self.metrics.update(metrics)

    def cancel(self):
        self.metrics = {}


class _WarmSectionNavigationHarness(NavigationMixin):
    def __init__(self, first_layout, second_layout):
        first_tab = SearchTabSession(
            tab_id="first-tab", title="First", loaded=True,
            workspace_layout=deepcopy(first_layout),
        )
        second_tab = SearchTabSession(
            tab_id="second-tab", title="Second",
            workspace_layout=deepcopy(second_layout),
        )
        first_model = _RetainedWorkspaceModel(["first-row"])
        second_model = _RetainedWorkspaceModel(["second-row"])
        first_tab.workspace_model = first_model
        second_tab.workspace_model = second_model
        first_tab.workspace_projection = SimpleNamespace(
            owner_model=first_model,
        )
        first = SectionSession(
            entry_key="demo/first", title="First", accent="#fff",
            search_type="demo/asset", tabs=[first_tab],
            current_tab_id=first_tab.tab_id,
            sidebar_presets_initialized=True,
        )
        second = SectionSession(
            entry_key="demo/second", title="Second", accent="#fff",
            search_type="demo/shot", tabs=[second_tab],
            current_tab_id=second_tab.tab_id,
            sidebar_presets_initialized=True,
        )
        self._sessions = {
            first.entry_key: first,
            second.entry_key: second,
        }
        self._current_section_key = first.entry_key
        self.dock_model = _DockLayoutProbe(first_layout)
        self._performance = None
        self._search_tab_switch_monitor = _SwitchMonitor()
        self._card_path = []
        self._pending_card_focus_id = ""
        self._versions_request_id = ""
        self.result_viewport_capture_requested = SimpleNamespace(
            emit=lambda: None,
        )
        self.workspace_state = SimpleNamespace(
            load_stype=lambda _stype: None,
            clear_selection=lambda: None,
        )
        self.versions_model = SimpleNamespace(clear=lambda: None)
        self.section_state_changed = SimpleNamespace(emit=lambda: None)
        self.load_calls = []
        self.preset_requests = []

    @property
    def workspace_model(self):
        return self._current_tab().workspace_model

    def _save_opened_sections(self):
        pass

    def _save_search_cache(self):
        pass

    def _sync_section_model(self):
        pass

    def _sync_search_tabs(self, clear_suggestions=True):
        del clear_suggestions

    def _configure_result_organization(self, _tab, rebuild=True):
        del rebuild

    def _set_result_state(self, _tab):
        pass

    def _restore_result_viewport(self, _tab):
        pass

    def _load_tab(self, tab, append=False):
        self.load_calls.append((tab.tab_id, append))
        tab.loaded = True
        tab.workspace_projection = SimpleNamespace(
            owner_model=tab.workspace_model,
        )

    def _request_sidebar_presets(self, section):
        self.preset_requests.append(section.entry_key)


class SearchContractTests(unittest.TestCase):
    def test_primary_search_preserves_the_sidebar_or_preset_scope(self):
        records = records_from_filters([
            ("_expression", "in", "@SOBJECT(sthpw/task['assigned', '$LOGIN'])"),
        ])

        records = set_primary_name(records, "chair")

        self.assertEqual(records[0]["column"], "name")
        self.assertEqual(records[0]["value"], "chair")
        self.assertEqual(records[1]["column"], "_expression")
        self.assertIn(
            ("_expression", "in", "@SOBJECT(sthpw/task['assigned', '$LOGIN'])"),
            filters_from_records(records),
        )

    def test_all_entry_points_create_the_same_runtime_contract(self):
        source_filters = [("status", "=", "Ready")]

        related = create_search_tab(
            "demo/assets@direct",
            "Related",
            tab_kind="related",
            limit=25,
            view_mode="continious",
            filters=source_filters,
        )
        preset = create_search_tab(
            "demo/assets@sidebar",
            "Preset",
            tab_kind="preset",
            limit=25,
            view_mode="continious",
            records=records_from_filters(source_filters),
        )

        self.assertEqual(related.filter_records, preset.filter_records)
        self.assertEqual(related.extra_filters, preset.extra_filters)

    def test_user_tab_has_primary_name_card_immediately(self):
        tab = create_search_tab(
            "demo/assets@sidebar",
            "New Search",
            tab_kind="user",
            limit=25,
            view_mode="continious",
            ensure_name_row=True,
        )

        self.assertEqual(len(tab.filter_records), 1)
        self.assertEqual(tab.filter_records[0]["column"], "name")
        self.assertEqual(tab.filter_records[0]["relation"], "EQI")
        self.assertEqual(tab.extra_filters, [])

    def test_search_tab_does_not_report_append_during_initial_load(self):
        tab = create_search_tab(
            "demo/assets",
            "Assets",
            tab_kind="base",
            limit=25,
            view_mode="continious",
        )

        tab.loading = True

        self.assertFalse(tab.loading_append)

    def test_only_normal_new_tabs_start_under_server_standard_ownership(self):
        base = create_search_tab(
            "demo/assets", "Assets", tab_kind="base", limit=25,
            view_mode="continious",
        )
        user = create_search_tab(
            "demo/assets", "Search", tab_kind="user", limit=25,
            view_mode="continious",
        )
        preset = create_search_tab(
            "demo/assets", "Preset", tab_kind="preset", limit=25,
            view_mode="continious",
        )

        self.assertFalse(base.quick_filter_personalized)
        self.assertFalse(user.quick_filter_personalized)
        self.assertTrue(preset.quick_filter_personalized)

    def test_cached_tabs_without_filter_ownership_are_discarded(self):
        section = SectionSession(
            entry_key="demo/assets", title="Assets", accent="#fff",
            search_type="demo/assets",
        )

        _NavigationCacheHarness()._restore_section_tabs(section, {
            "tabs": [{
                "tab_id": "incomplete",
                "title": "Assets",
                "filter_records": [],
            }],
        })

        self.assertEqual(section.tabs, [])

    def test_cached_server_owned_state_remains_server_owned(self):
        section = SectionSession(
            entry_key="demo/assets", title="Assets", accent="#fff",
            search_type="demo/assets",
        )

        _NavigationCacheHarness()._restore_section_tabs(section, {
            "tabs": [{
                "tab_id": "standard",
                "title": "Assets",
                "filter_records": [],
                "quick_filter_personalized": False,
            }],
        })

        self.assertFalse(section.tabs[0].quick_filter_personalized)

    def test_cached_tab_restores_each_result_viewport(self):
        section = SectionSession(
            entry_key="demo/assets", title="Assets", accent="#fff",
            search_type="demo/assets",
        )

        _NavigationCacheHarness()._restore_section_tabs(section, {
            "tabs": [{
                "tab_id": "viewport",
                "title": "Assets",
                "filter_records": [],
                "quick_filter_personalized": False,
                "list_content_y": 412.5,
                "tile_content_y": 228.0,
                "list_content_y_valid": True,
                "tile_content_y_valid": True,
                "next_offset": 75,
                "total": 180,
                "exhausted": False,
                "loaded_page_offsets": [0, 25, 50],
            }],
        })

        tab = section.tabs[0]
        self.assertEqual(tab.list_content_y, 412.5)
        self.assertEqual(tab.tile_content_y, 228.0)
        self.assertTrue(tab.list_content_y_valid)
        self.assertTrue(tab.tile_content_y_valid)
        self.assertEqual(tab.next_offset, 75)
        self.assertEqual(tab.total, 180)
        self.assertFalse(tab.exhausted)
        self.assertEqual(tab.loaded_page_offsets, [0, 25, 50])

    def test_search_cache_writes_loaded_infinite_page_offsets(self):
        tab = SearchTabSession(
            tab_id="one",
            title="One",
            quick_filter_personalized=True,
            next_offset=75,
            total=180,
            loaded_page_offsets=[0, 25, 50],
        )
        controller = _CacheWriterHarness(tab)

        controller._write_search_cache()

        record = controller._search_cache["demo"]["sections"][0]["tabs"][0]
        self.assertEqual(record["next_offset"], 75)
        self.assertEqual(record["total"], 180)
        self.assertEqual(record["loaded_page_offsets"], [0, 25, 50])
        self.assertEqual(controller.writes, 1)

    def test_search_tab_workspace_layout_round_trips_with_search_cache(self):
        layout = {
            "panels": [
                {
                    "id": "results",
                    "width": 0.37,
                    "height": 1.0,
                },
            ],
            "layout": {
                "kind": "panel",
                "panel": "results",
            },
        }
        tab = SearchTabSession(
            tab_id="one",
            title="One",
            quick_filter_personalized=True,
            selected_node_id="asset-one",
            selected_node_ids=["asset-one", "asset-two"],
            list_content_y=412.5,
            list_content_y_valid=True,
            view_mode="splitted_vertical",
            sort_mode="updated_desc",
            group_mode="status",
            splitter_ratio=0.37,
        )
        controller = _CacheWriterHarness(tab)
        source = controller._sessions["demo/assets"]
        tab.workspace_layout = deepcopy(layout)

        controller._write_search_cache()

        cached = controller._load_search_cache("demo")[source.entry_key]
        cached_tab = cached["tabs"][0]
        self.assertEqual(cached_tab["workspace_layout"], layout)
        restored = SectionSession(
            entry_key=source.entry_key,
            title=source.title,
            accent=source.accent,
            search_type=source.search_type,
        )
        _NavigationCacheHarness()._restore_section_tabs(
            restored, deepcopy(cached),
        )
        restored_tab = restored.tabs[0]
        self.assertEqual(restored_tab.workspace_layout, layout)
        self.assertIsNot(
            restored_tab.workspace_layout,
            cached_tab["workspace_layout"],
        )
        self.assertEqual(
            restored_tab.selected_node_ids,
            ["asset-one", "asset-two"],
        )
        self.assertEqual(restored_tab.list_content_y, 412.5)
        self.assertTrue(restored_tab.list_content_y_valid)
        self.assertEqual(restored_tab.view_mode, "splitted_vertical")
        self.assertEqual(restored_tab.sort_mode, "updated_desc")
        self.assertEqual(restored_tab.group_mode, "status")
        self.assertEqual(restored_tab.splitter_ratio, 0.37)

    def test_section_switch_restores_live_layout_and_loads_only_first_show(self):
        first_layout = {
            "panels": [{"id": "results", "width": 0.42}],
            "layout": {"kind": "panel", "panel": "results"},
        }
        second_layout = {
            "panels": [{"id": "results", "width": 0.63}],
            "layout": {"kind": "panel", "panel": "results"},
        }
        live_first_layout = {
            "panels": [{"id": "results", "width": 0.31}],
            "layout": {"kind": "panel", "panel": "results"},
        }
        live_second_layout = {
            "panels": [{"id": "results", "width": 0.71}],
            "layout": {"kind": "panel", "panel": "results"},
        }
        controller = _WarmSectionNavigationHarness(
            first_layout, second_layout,
        )
        first = controller._sessions["demo/first"]
        second = controller._sessions["demo/second"]
        first_model = first.tabs[0].workspace_model
        second_model = second.tabs[0].workspace_model
        controller.dock_model.current = deepcopy(live_first_layout)

        controller.activate_section(second.entry_key)

        self.assertEqual(first.tabs[0].workspace_layout, live_first_layout)
        self.assertEqual(controller.dock_model.current, second_layout)
        self.assertEqual(controller.load_calls, [("second-tab", False)])

        controller.dock_model.current = deepcopy(live_second_layout)
        controller.activate_section(first.entry_key)

        self.assertEqual(second.tabs[0].workspace_layout, live_second_layout)
        self.assertEqual(controller.dock_model.current, live_first_layout)
        self.assertEqual(controller.load_calls, [("second-tab", False)])

        controller.activate_section(second.entry_key)

        self.assertEqual(controller.dock_model.current, live_second_layout)
        self.assertEqual(controller.load_calls, [("second-tab", False)])
        self.assertEqual(controller.preset_requests, [])
        self.assertIs(first.tabs[0].workspace_model, first_model)
        self.assertIs(second.tabs[0].workspace_model, second_model)
        self.assertEqual(first_model.replacements, 0)
        self.assertEqual(second_model.replacements, 0)

    def test_section_restores_target_details_before_presenting_its_docks(self):
        first_layout = {
            "panels": [{"id": "tasks", "visible": False}],
            "layout": {"kind": "panel", "panel": "results"},
        }
        second_layout = {
            "panels": [{"id": "tasks", "visible": True}],
            "layout": {"kind": "panel", "panel": "tasks"},
        }
        controller = _WarmSectionNavigationHarness(
            first_layout, second_layout,
        )
        second = controller._sessions["demo/second"]
        second_tab = second.tabs[0]
        second_tab.loaded = True
        second_tab.details_node_id = "second-node"
        second_tab.workspace_projection = SimpleNamespace(
            owner_model=second_tab.workspace_model,
        )
        second_tab.workspace_model.node_for = lambda node_id: (
            SimpleNamespace(node_id=node_id, search_key="demo/shot?code=B")
            if node_id == "second-node" else None
        )
        controller.workspace_state.target = "first-tab"

        def restore_details(tab, _node):
            controller.workspace_state.target = tab.tab_id
            return True

        controller._restore_tab_details = restore_details
        prehidden_targets = []
        prehide = controller.dock_model.prehide_for_layout

        def prehide_layout(layout):
            prehidden_targets.append(controller.workspace_state.target)
            return prehide(layout)

        controller.dock_model.prehide_for_layout = prehide_layout
        presented_targets = []
        apply_layout = controller.dock_model.apply_layout

        def publish_layout(layout):
            # DockPanelModel.apply_layout emits presentation changes
            # synchronously. Record the selection a TasksController would see.
            presented_targets.append(controller.workspace_state.target)
            return apply_layout(layout)

        controller.dock_model.apply_layout = publish_layout

        controller.activate_section(second.entry_key)

        self.assertEqual(prehidden_targets, ["first-tab"])
        self.assertEqual(presented_targets, ["second-tab"])
        self.assertNotIn("first-tab", presented_targets)

    def test_section_presents_empty_details_for_a_background_first_load(self):
        first_layout = {
            "panels": [{"id": "tasks", "visible": False}],
            "layout": {"kind": "panel", "panel": "results"},
        }
        second_layout = {
            "panels": [{"id": "tasks", "visible": True}],
            "layout": {"kind": "panel", "panel": "tasks"},
        }
        controller = _WarmSectionNavigationHarness(
            first_layout, second_layout,
        )
        second = controller._sessions["demo/second"]
        second.tabs[0].loading = True
        controller.workspace_state.target = "first-tab"
        controller.workspace_state.clear_selection = lambda: setattr(
            controller.workspace_state, "target", ""
        )
        presented_targets = []
        apply_layout = controller.dock_model.apply_layout

        def publish_layout(layout):
            presented_targets.append(controller.workspace_state.target)
            return apply_layout(layout)

        controller.dock_model.apply_layout = publish_layout

        controller.activate_section(second.entry_key)

        self.assertEqual(presented_targets, [""])
        self.assertEqual(controller.load_calls, [])

    def test_first_section_layout_seed_is_saved_after_it_is_captured(self):
        first_layout = {
            "panels": [{"id": "results", "visible": True}],
            "layout": {"kind": "panel", "panel": "results"},
        }
        controller = _WarmSectionNavigationHarness(first_layout, {})
        second = controller._sessions["demo/second"]
        second.tabs[0].workspace_layout = {}
        saved_layouts = []
        controller._save_search_cache = lambda: saved_layouts.append(
            deepcopy(second.tabs[0].workspace_layout)
        )

        controller.activate_section(second.entry_key)

        self.assertEqual(saved_layouts, [first_layout])
        self.assertEqual(second.tabs[0].workspace_layout, first_layout)

    def test_inactive_query_populates_retained_model_and_paging_cursor(self):
        tab = SearchTabSession(
            tab_id="one", title="One", request_id="request", loading=True
        )
        controller = _CachedResultHarness(tab)
        records = [
            SimpleNamespace(get_search_key=lambda: "asset-one"),
            SimpleNamespace(get_search_key=lambda: "asset-two"),
        ]

        controller._async_query_result((
            records,
            {
                "cachedProjection": True,
                "pageOffsets": [0, 25, 50],
                "nextOffset": 75,
                "savedTotal": 180,
                "savedExhausted": False,
            },
            None,
            ("demo/assets", "one", False, "request", 0),
        ))

        self.assertTrue(tab.loaded)
        self.assertEqual(tab.sobjects, records)
        self.assertEqual(tab.loaded_page_offsets, [0, 25, 50])
        self.assertEqual(tab.next_offset, 75)
        self.assertEqual(tab.total, 180)
        self.assertFalse(tab.exhausted)
        result_model = tab.workspace_model
        self.assertIsNotNone(result_model)
        self.assertEqual(result_model._roots, records)
        self.assertEqual(tab.workspace_roots, records)
        projection = tab.workspace_projection
        self.assertIs(projection.owner_model, result_model)
        self.assertTrue(tab.viewport_restore_pending)
        self.assertEqual(controller.load_calls, [])
        self.assertEqual(controller.saved, 1)

        controller._current_section_key = "demo/assets"
        replacements = result_model.replacements
        NavigationMixin._show_or_load_tab(controller, tab)

        self.assertIs(tab.workspace_model, result_model)
        self.assertIs(tab.workspace_projection, projection)
        self.assertEqual(result_model.replacements, replacements)
        self.assertEqual(controller.load_calls, [])
        self.assertEqual(controller.viewport_restores, ["one"])

    def test_superseded_load_continues_after_its_tab_becomes_hidden(self):
        from thlib.environment import env_inst

        controller = _SearchRaceHarness()
        pool = _ServerPoolProbe()
        tab = controller.first_tab

        with patch.object(env_inst, "server_pool", pool):
            controller._load_tab(tab)
            first_worker = pool.workers[0]
            first_request_id = tab.request_id

            controller._load_tab(tab, bypass_cache=True)
            self.assertEqual(first_worker.cancel_calls, 1)
            self.assertIn(tab.tab_id, controller._pending_search_loads)

            controller._current_section_key = "demo/b"
            controller._search_worker_settled(first_worker)

            self.assertEqual(len(pool.workers), 2)
            replacement_worker = pool.workers[1]
            self.assertTrue(replacement_worker.started)
            self.assertEqual(replacement_worker.metadata[0], "demo/a")
            self.assertIs(
                controller._find_tab(*replacement_worker.metadata[:2]),
                tab,
            )
            self.assertNotEqual(tab.request_id, first_request_id)
            self.assertTrue(tab.loading)
            self.assertFalse(controller._loading)
            self.assertEqual(controller._active_request_id, "")

            record = SimpleNamespace(
                get_search_key=lambda: "demo/a?code=A001",
            )
            controller._async_query_result((
                [record],
                {"total_sobjects_query_count": 1},
                None,
                replacement_worker.metadata,
            ))

        self.assertFalse(tab.loading)
        self.assertTrue(tab.loaded)
        self.assertEqual(tab.sobjects, [record])
        self.assertEqual(tab.workspace_model._roots, [record])
        self.assertEqual(controller.second_tab.workspace_model._roots, ["b-live"])

    def test_hidden_request_error_does_not_clear_current_tab_model(self):
        controller = _SearchRaceHarness()
        hidden = controller.first_tab
        controller._current_section_key = "demo/b"
        hidden.request_id = "hidden-request"
        hidden.loading = True
        controller._active_request_id = hidden.request_id
        controller._loading = True
        worker = _SearchWorkerProbe()
        worker.add_result_data((
            "demo/a", hidden.tab_id, False, hidden.request_id, 0,
        ))
        controller._search_workers[hidden.tab_id] = worker

        controller._async_query_error((
            {"exception": RuntimeError("hidden search failed")},
            worker,
        ))

        self.assertFalse(hidden.loading)
        self.assertFalse(hidden.loaded)
        self.assertEqual(controller.second_tab.workspace_model._roots, ["b-live"])
        self.assertEqual(controller.second_tab.workspace_model.clear_calls, 0)
        self.assertEqual(controller.versions_model.clear_calls, 0)
        self.assertEqual(controller.selection_clear_calls, 0)
        self.assertEqual(controller._active_request_id, "")
        self.assertFalse(controller._loading)

    def test_hidden_duplicate_append_does_not_page_the_current_tab(self):
        controller = _SearchRaceHarness()
        first = SimpleNamespace(get_search_key=lambda: "demo/a?code=A001")
        second = SimpleNamespace(get_search_key=lambda: "demo/a?code=A002")
        hidden = controller.first_tab
        hidden.sobjects = [first, second]
        hidden.workspace_model._roots = [first, second]
        hidden.loaded = True
        hidden.loading = True
        hidden.loading_append = True
        hidden.request_id = "append-request"
        controller._current_section_key = "demo/b"

        controller._async_query_result((
            [first, second],
            {"total_sobjects_query_count": 10},
            None,
            ("demo/a", hidden.tab_id, True, hidden.request_id, 2),
        ))

        self.assertFalse(hidden.loading)
        self.assertFalse(hidden.exhausted)
        self.assertEqual(hidden.duplicate_pages, 1)
        self.assertEqual(controller.load_more_calls, [])
        self.assertEqual(controller.second_tab.workspace_model._roots, ["b-live"])

    def test_viewport_capture_is_owned_by_the_current_tab(self):
        tab = SearchTabSession(tab_id="one", title="One", loaded=True)
        harness = _NavigationCacheHarness()
        harness._current_tab = lambda: tab

        harness.capture_current_result_viewport(315.25, 98.5)

        self.assertEqual(tab.list_content_y, 315.25)
        self.assertEqual(tab.tile_content_y, 98.5)
        self.assertTrue(tab.list_content_y_valid)
        self.assertTrue(tab.tile_content_y_valid)

    def test_each_search_tab_keeps_one_stable_result_model(self):
        controller = _PerTabModelHarness()
        first, second = controller.section.tabs

        first_model = controller._ensure_tab_workspace_model(first)
        second_model = controller._ensure_tab_workspace_model(second)

        self.assertIsNot(first_model, second_model)
        self.assertIs(
            controller._ensure_tab_workspace_model(first), first_model
        )
        self.assertIs(first_model.parent(), controller)
        self.assertIs(second_model.parent(), controller)

    def test_section_switch_keeps_every_result_surface_model_identity(self):
        state = WorkspaceState()
        first_model = QObject()
        second_model = QObject()
        state.set_result_surfaces([
            {
                "surfaceKey": "assets::main",
                "current": True,
                "resultModel": first_model,
                "viewMode": "continious",
                "splitterRatio": 0.58,
            },
            {
                "surfaceKey": "shots::main",
                "current": False,
                "resultModel": second_model,
                "viewMode": "continious",
                "splitterRatio": 0.58,
            },
        ])
        resets = []
        changed_roles = []
        state.result_surfaces_model.modelReset.connect(
            lambda: resets.append(True)
        )
        state.result_surfaces_model.dataChanged.connect(
            lambda _first, _last, roles: changed_roles.extend(roles)
        )

        state.set_result_surfaces([
            {
                "surfaceKey": "assets::main",
                "current": False,
                "resultModel": first_model,
                "viewMode": "continious",
                "splitterRatio": 0.58,
            },
            {
                "surfaceKey": "shots::main",
                "current": True,
                "resultModel": second_model,
                "viewMode": "continious",
                "splitterRatio": 0.58,
            },
        ])

        records = state.result_surfaces_model.records()
        self.assertEqual(resets, [])
        self.assertEqual(
            set(changed_roles),
            {state.result_surfaces_model._role_ids["current"]},
        )
        self.assertIs(records[0]["resultModel"], first_model)
        self.assertIs(records[1]["resultModel"], second_model)

    def test_tab_switch_capture_keeps_live_model_without_copying_projection(self):
        controller = _ProjectionCaptureHarness()

        controller._capture_current_tree_state()

        self.assertEqual(controller.viewport_captures, 1)
        self.assertIsNone(controller.tab.workspace_projection)
        self.assertEqual(controller.tab.workspace_roots, [])
        self.assertEqual(
            controller.tab.card_path,
            ["asset", "asset:process:publish"],
        )
        self.assertEqual(controller.tree_serializations, 0)

        controller._capture_current_tree_state(persist_tree=True)

        self.assertEqual(controller.tree_serializations, 1)
        self.assertEqual(controller.tab.tree_state, {"saved": True})

    def test_new_tab_does_not_restart_a_request_started_by_standard(self):
        controller = _SearchTabsHarness(standard_starts_load=True)

        controller.add_search_tab()

        self.assertEqual(controller.load_calls, [])
        self.assertTrue(controller.section.tabs[-1].loading)
        self.assertEqual(
            controller.section.tabs[-1].workspace_layout,
            {"layout": "current"},
        )

    def test_new_tab_starts_normally_when_standard_needs_no_request(self):
        controller = _SearchTabsHarness(standard_starts_load=False)

        controller.add_search_tab()

        self.assertEqual(controller.load_calls, [controller.section.tabs[-1]])
        self.assertEqual(
            controller.section.tabs[-1].workspace_layout,
            {"layout": "current"},
        )

    def test_showing_a_loading_tab_does_not_cancel_and_restart_it(self):
        tab = create_search_tab(
            "demo/assets", "Assets", tab_kind="base", limit=25,
            view_mode="continious",
        )
        tab.loading = True
        controller = _LoadingNavigationHarness()

        controller._show_or_load_tab(tab)

        self.assertEqual(controller.load_calls, [])
        self.assertEqual(controller.state_calls, [tab])

    def test_restored_tab_rebuilds_all_saved_pages_as_one_projection(self):
        tab = create_search_tab(
            "demo/assets", "Assets", tab_kind="base", limit=25,
            view_mode="continious",
        )
        tab.loaded_page_offsets = [0, 25, 50]
        controller = _LoadingNavigationHarness()

        controller._show_or_load_tab(tab)

        self.assertEqual(controller.restore_calls, [tab])
        self.assertEqual(controller.load_calls, [])

    def test_showing_a_loaded_tab_reuses_the_live_result_projection(self):
        root = object()
        tab = create_search_tab(
            "demo/assets", "Assets", tab_kind="base", limit=25,
            view_mode="continious",
        )
        tab.loaded = True
        tab.workspace_roots = [root]
        tab.selected_node_id = "asset-one"
        tab.selected_node_ids = ["asset-one", "asset-two"]
        controller = _LoadedNavigationHarness()
        projection = SimpleNamespace(owner_model=controller.workspace_model)
        tab.workspace_projection = projection

        controller._show_or_load_tab(tab)

        self.assertEqual(controller.organization_rebuilds, [False])
        self.assertEqual(controller.projection_restores, [])
        self.assertEqual(controller.replace_calls, [])
        self.assertEqual(controller.load_calls, [])
        self.assertEqual(tab.selected_node_id, "asset-one")
        self.assertEqual(
            tab.selected_node_ids, ["asset-one", "asset-two"]
        )
        self.assertEqual(controller.viewport_restores, [])

    def test_cached_tab_switch_is_committed_without_an_event_loop_gap(self):
        controller = _TabSwitchNavigationHarness()

        controller._activate_workspace_tab("second", "Second")

        self.assertEqual(
            controller.events,
            [
                ("begin", "second"),
                ("capture", False),
                ("sync", True),
                ("show", "demo/assets", "second"),
                ("commit", 7),
            ],
        )
        self.assertEqual(
            controller._current_section().current_tab_id,
            "second",
        )
        self.assertTrue(controller.committed["cached"])
        self.assertEqual(controller.committed["rows"], 17)

    def test_search_tabs_restore_independent_dock_visibility(self):
        controller = _TabSwitchNavigationHarness()
        section = controller._current_section()
        first, second = section.tabs
        live_first_layout = {
            "panels": [{"id": "knowledge", "visible": True}],
            "layout": {"kind": "panel", "panel": "knowledge"},
        }
        live_second_layout = {
            "panels": [{"id": "knowledge", "visible": False}],
            "layout": {"kind": "panel", "panel": "results"},
        }
        controller.dock_model.current = deepcopy(live_first_layout)

        controller._activate_workspace_tab(second.tab_id, second.title)

        self.assertEqual(first.workspace_layout, live_first_layout)
        self.assertEqual(controller.dock_model.current, second.workspace_layout)
        self.assertEqual(
            controller.dock_model.prehidden[-1], second.workspace_layout
        )

        controller.dock_model.current = deepcopy(live_second_layout)
        controller._activate_workspace_tab(first.tab_id, first.title)

        self.assertEqual(second.workspace_layout, live_second_layout)
        self.assertEqual(controller.dock_model.current, live_first_layout)

    def test_search_type_section_switch_is_timed_and_published(self):
        controller = _SectionSwitchNavigationHarness()

        controller.activate_section("demo/second")

        self.assertTrue(controller._search_tab_switch_monitor.switching)
        metrics = controller._search_tab_switch_monitor.metrics
        self.assertEqual(controller._current_section_key, "demo/second")
        self.assertEqual(metrics["kind"], "section")
        self.assertEqual(metrics["tab"], "Second")
        self.assertEqual(metrics["rows"], 23)
        self.assertIn(("show", "demo/second", "second-tab"), controller.events)

    def test_tab_switch_first_frame_is_recorded_as_runtime_metric(self):
        changed = []
        monitor = SearchTabSwitchMonitor()
        monitor._serial = 9
        monitor._switching = True
        monitor._metrics = {"serial": 9, "tab": "Assets"}
        monitor._sample = 42
        monitor.changed.connect(lambda: changed.append(True))
        request_metrics.reset()
        try:
            monitor._sample_finished(42, {"readyMs": 5.0})

            metric = request_metrics.snapshot()["ui.search_tab_switch"]
            self.assertFalse(monitor.switching)
            self.assertEqual(metric["calls"], 1)
            self.assertGreater(metric["duration_seconds"], 0)
            self.assertGreater(
                monitor.metrics["firstFrameMs"],
                0,
            )
            self.assertGreaterEqual(
                monitor.metrics["afterPythonMs"],
                0,
            )
            self.assertEqual(changed, [True])
        finally:
            request_metrics.reset()

    def test_latest_section_click_wins_with_synchronous_switches(self):
        controller = _SectionSwitchNavigationHarness()

        controller.activate_section("demo/second")
        controller.activate_section("demo/first")

        self.assertEqual(controller._current_section_key, "demo/first")

    def test_latest_tab_click_wins_with_synchronous_switches(self):
        controller = _TabSwitchNavigationHarness()
        controller._search_tab_switch_monitor = SearchTabSwitchMonitor()

        controller._activate_workspace_tab("second", "Second")
        controller._activate_workspace_tab("first", "First")

        self.assertEqual(controller._current_section().current_tab_id, "first")

    def test_tab_switch_phase_metrics_survive_the_final_commit(self):
        monitor = SearchTabSwitchMonitor()
        serial = monitor.begin("Assets")

        monitor.record_phase("detailsMs", 123.4567)
        monitor.commit(serial, {"pythonMs": 140.0, "rows": 25})

        self.assertEqual(monitor.metrics["detailsMs"], 123.457)
        self.assertEqual(monitor.metrics["pythonMs"], 140.0)
        self.assertEqual(monitor.metrics["rows"], 25)

    def test_first_projection_of_a_loaded_tab_creates_its_delegates(self):
        sobject = SimpleNamespace(
            get_search_key=lambda: "demo/assets?code=ASSET001"
        )
        tab = create_search_tab(
            "demo/assets", "Assets", tab_kind="base", limit=25,
            view_mode="continious",
        )
        tab.loaded = True
        tab.sobjects = [sobject]
        controller = _LoadedNavigationHarness()

        controller._show_or_load_tab(tab)

        self.assertEqual(
            controller.replace_calls,
            [([sobject], None, False)],
        )

    def test_advanced_search_columns_keep_native_tactic_schema_order(self):
        state = _ProjectState()

        state.load_stype(_SearchType())

        self.assertEqual(
            [record["value"] for record in state.filter_column_model.records],
            ["name", "title", "code", "_expression"],
        )

    def test_same_search_type_schema_is_not_rebuilt_for_sibling_tabs(self):
        state = _ProjectState()
        stype = _SearchType()

        state.load_stype(stype)
        state.load_stype(stype)

        self.assertEqual(stype.columns_info_calls, 1)


if __name__ == "__main__":
    unittest.main()
