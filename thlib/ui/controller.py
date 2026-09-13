"""Public QML application controller."""

from __future__ import annotations

import math

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot

from thlib.environment import env_read_config, env_write_config

from .controllers.types import (
    STANDARD_QUICK_FILTER_TAB_KINDS,
    ActionRegistry,
    SearchTabSession,
    SectionSession,
)
from .menu_schema import MenuRegistry
from .models import NavigationModel, ProjectModel
from .quick_filters import QuickFilterCatalog, QuickFilterRuntime
from .theme_catalog import (
    ACCENT_PRESETS,
    ICON_SETS,
    THEME_STYLES,
    accent_color,
    base_color,
    normalize_icon_set,
    normalize_theme_accents,
    normalize_theme_style,
)
from .window_geometry import load_main_window_state
from .repository_sync import RepositorySyncController
from .workspace import (
    DockPanelModel,
    DetachedDockPanelModel,
    FloatingWindowModel,
    VisibleDockPanelModel,
    VisibleFloatingWindowModel,
    SectionTabModel,
    WorkspaceItemModel,
    WorkspaceState,
)
from .controllers.item_mutations import ItemMutationsMixin
from .controllers.lifecycle import LifecycleMixin
from .controllers.connection import ConnectionMixin
from .controllers.navigation import NavigationMixin
from .controllers.tab_switch_performance import SearchTabSwitchMonitor
from .config_persistence import ConfigWriteQueue
from .ui_performance import UiPerformanceMonitor
from .controllers.search_runtime import SearchRuntimeMixin
from .controllers.commands import CommandsMixin
from .controllers.snapshot_actions import SnapshotActionsMixin
from .controllers.item_actions import ItemActionsMixin
from .controllers.search_tabs import SearchTabsMixin
from .controllers.advanced_search import AdvancedSearchMixin
from .controllers.search_suggestions import SearchSuggestionsMixin
from .controllers.result_tree import ResultTreeMixin
from .controllers.item_operations import ItemOperationsMixin
from .controllers.selection import SelectionMixin
from .controllers.snapshot_details import SnapshotDetailsMixin
from .controllers.view_state import ViewStateMixin
from .controllers.item_editing import ItemEditingMixin
from .controllers.rich_text_links import RichTextLinksMixin


class ApplicationController(
        RichTextLinksMixin,
        ItemMutationsMixin,
        LifecycleMixin,
        ConnectionMixin,
        NavigationMixin,
        SearchRuntimeMixin,
        CommandsMixin,
        SnapshotActionsMixin,
        ItemActionsMixin,
        SearchTabsMixin,
        AdvancedSearchMixin,
        SearchSuggestionsMixin,
        ResultTreeMixin,
        ItemOperationsMixin,
        SelectionMixin,
        SnapshotDetailsMixin,
        ViewStateMixin,
        ItemEditingMixin,
        QObject):
    """QML API for application state, navigation, and commands."""

    dark_theme_changed = Signal(bool)

    theme_style_changed = Signal(str)
    accent_changed = Signal()
    icon_set_changed = Signal(str)
    animation_preferences_changed = Signal()
    dcc_state_changed = Signal()

    page_changed = Signal(str, str)

    command_requested = Signal(str)

    notification_changed = Signal(str)

    project_changed = Signal(str, str)

    project_state_changed = Signal()

    server_state_changed = Signal()

    result_count_changed = Signal()

    section_state_changed = Signal()

    result_viewport_capture_requested = Signal()

    result_viewport_restore_requested = Signal(float, float, bool, bool)

    result_node_reveal_requested = Signal(str)

    selected_node_changed = Signal()
    taskContextRequested = Signal(str, str, str)

    results_view_changed = Signal()

    paging_state_changed = Signal()

    loading_changed = Signal()

    activity_log_changed = Signal()

    connection_settings_changed = Signal()

    search_text_changed = Signal()

    search_tab_history_changed = Signal()

    advanced_filter_suggestions_changed = Signal()

    authentication_changed = Signal()

    snapshot_browser_changed = Signal()

    snapshot_data_changed = Signal(str, str)

    search_state_changed = Signal()

    quick_filters_changed = Signal()

    tag_cloud_changed = Signal()

    tools_requested = Signal()

    checkinFilesRequested = Signal()

    revisionCheckinConfirmationRequested = Signal()

    multiFileCheckinModeRequested = Signal(int)

    repositorySyncEditorRequested = Signal()
    repository_sync_changed = Signal()
    processFilterEditorRequested = Signal()
    sobjectEditorRequested = Signal()
    sobjectLinkRequested = Signal()
    projectEditRequested = Signal()

    def __init__(self, debug_log=None, cache_controller=None) -> None:
        super().__init__()
        self.debug_log = debug_log
        self.cache_controller = cache_controller
        if self.cache_controller is not None:
            self.cache_controller.invalidated.connect(
                self.apply_cache_invalidation
            )
        # A section/tab replacement can also replace its selected node.
        # Ordinary item selection emits only selected_node_changed so the
        # whole section UI is not invalidated on every click.
        self.section_state_changed.connect(self.selected_node_changed.emit)
        self.section_state_changed.connect(self.results_view_changed.emit)
        self._settings = dict(env_read_config(
            filename="ui_settings",
            unique_id="ui_main",
            long_abs_path=True,
        ) or {})
        self._search_cache = dict(env_read_config(
            filename="search_tabs",
            unique_id="cache",
            long_abs_path=True,
        ) or {})
        # Runtime tag records are only a hot in-memory projection. Persistent
        # storage is owned by thlib.server_cache together with every other
        # server-backed reference catalog.
        self._tag_catalog_cache = {}
        self._window_state = load_main_window_state(self._settings)
        self._window_state_timer = QTimer(self)
        self._window_state_timer.setSingleShot(True)
        self._window_state_timer.timeout.connect(self._write_window_state)
        # The production interface and reference recording start dark.  The
        # persisted preference can still select the light theme on later runs.
        self._dark_theme = bool(self._settings.get("appearance/darkTheme", True))
        self._theme_style = normalize_theme_style(
            self._settings.get("appearance/themeStyle", "md3")
        )
        self._theme_accents = normalize_theme_accents(
            self._settings.get("appearance/themeAccents")
        )
        self._icon_set = normalize_icon_set(
            self._settings.get("appearance/iconSet")
        )
        # Animation preferences are a hot runtime projection of ui_main.
        # Delegates bind to these QObject properties through the shared Theme;
        # they never read the configuration file themselves.
        self._click_animations_enabled = bool(
            self._settings.get("appearance/clickAnimations", True)
        )
        self._hover_animations_enabled = bool(
            self._settings.get("appearance/hoverAnimations", True)
        )
        self._fade_animations_enabled = bool(
            self._settings.get("appearance/fadeAnimations", True)
        )
        self._popup_animations_enabled = bool(
            self._settings.get(
                "appearance/popupAnimations", self._fade_animations_enabled,
            )
        )
        self._current_project_code = ""
        self._current_project_title = ""
        self._current_project_preview = ""
        self._sobject_editor_request = {}
        self._project_editor_request = {}
        self._sobject_link_request = {}
        self._server_state = "connecting"
        self._server_message = ""
        self._administration_identity = None
        self._result_count = 0
        self._current_page_key = ""
        self._current_page_title = ""
        self._current_user_initials = ""
        self._current_section_key = ""
        self._performance = UiPerformanceMonitor(self)
        self._config_write_queue = ConfigWriteQueue(self)
        self._config_write_queue.failed.connect(
            self._config_write_failed
        )
        self._search_tab_switch_monitor = SearchTabSwitchMonitor(
            debug_log, self, performance=self._performance
        )
        self._loading = False
        self._loading_message = ""
        self._authentication_required = False
        self._authentication_dialog_visible = False
        self._authentication_busy = False
        self._authentication_error = ""
        self._authentication_started_at = 0.0
        self._login_name = str(self._settings.get("server/lastLogin", "") or "")
        if not self._login_name:
            try:
                from thlib.environment import env_server
                self._login_name = str(env_server.get_user() or "")
            except Exception:
                self._login_name = ""
        self._activity_log: list[str] = []
        self._bootstrap_request_id = ""
        self._bootstrap_worker = None
        self._bootstrap_started_at = 0.0
        self._project_request_id = ""
        self._project_started_at: dict[str, float] = {}
        self._ping_interval = int(self._settings.get("server/pingInterval", 0) or 0)
        if self._ping_interval not in {0, 10, 60}:
            self._ping_interval = 0
        self._ping_in_progress = False
        self._ping_started_at = 0.0
        self._ping_timer = QTimer(self)
        self._ping_timer.timeout.connect(self.ping_server)
        if self._ping_interval:
            self._ping_timer.start(self._ping_interval * 1000)
        self._loading_mode = str(
            self._settings.get("search/loadingMode", "pages") or "pages"
        )
        if self._loading_mode not in {"pages", "infinite"}:
            self._loading_mode = "pages"
        self._page_size = 20
        self._default_view_mode = "continious"
        self._description_limit_enabled = True
        self._description_limit = 80
        self._read_checkin_defaults()
        self._snapshot_browser_show_all = bool(
            self._settings.get("snapshotBrowser/showAll", False)
        )
        self._snapshot_browser_show_more = bool(
            self._settings.get("snapshotBrowser/showMore", False)
        )
        self._snapshot_browser_content_mode = str(
            self._settings.get("snapshotBrowser/contentMode", "both")
            or "both"
        )
        if self._snapshot_browser_content_mode not in {
            "both", "preview", "files",
        }:
            self._snapshot_browser_content_mode = "both"
        self._snapshot_browser_orientation = str(
            self._settings.get("snapshotBrowser/orientation", "horizontal")
            or "horizontal"
        )
        if self._snapshot_browser_orientation not in {
            "horizontal", "vertical"
        }:
            self._snapshot_browser_orientation = "horizontal"
        self._snapshot_browser_splitter_ratio = max(
            0.22,
            min(
                0.78,
                float(self._settings.get(
                    "snapshotBrowser/splitterRatio", 0.52
                ) or 0.52),
            ),
        )
        self._task_snapshot_source = None
        self._task_snapshot_identity = ("", "", "")
        self._task_snapshot_request_id = ""
        self._task_snapshot_worker = None
        self._task_snapshot_loaded_sources = set()
        self._snapshot_splitter_save_timer = QTimer(self)
        self._snapshot_splitter_save_timer.setSingleShot(True)
        self._snapshot_splitter_save_timer.timeout.connect(
            self._save_snapshot_splitter_ratio
        )
        self._sessions: dict[str, SectionSession] = {}
        self._section_state_save_timer = QTimer(self)
        self._section_state_save_timer.setSingleShot(True)
        self._section_state_save_timer.setInterval(250)
        self._section_state_save_timer.timeout.connect(
            self._write_opened_sections
        )
        self._search_cache_save_timer = QTimer(self)
        self._search_cache_save_timer.setSingleShot(True)
        self._search_cache_save_timer.setInterval(250)
        self._search_cache_save_timer.timeout.connect(
            self._write_search_cache
        )
        self._active_request_id = ""
        self._search_workers = {}
        self._pending_search_loads = {}
        self._sidebar_preset_workers = {}
        self._sidebar_preset_requests = {}
        self._quick_filter_workers = {}
        self._selected_detail_key = ""
        self._selected_detail_process = ""
        self._selected_detail_snapshot_node_id = ""
        self._detail_request_id = ""
        self._detail_worker = None
        self._detail_started_at = 0.0
        self._selected_update_started_at = 0.0
        self._versions_request_id = ""
        self._versions_worker = None
        self._pending_versions_node_id = ""
        self._pending_selection_load = None
        self._selection_load_timer = QTimer(self)
        self._selection_load_timer.setSingleShot(True)
        self._selection_load_timer.setInterval(100)
        self._selection_load_timer.timeout.connect(
            self._flush_selected_loads
        )
        self._pending_multi_file_checkin: dict = {}
        self._pending_file_open_tasks: set[str] = set()
        self._suggestion_request_id = ""
        self._suggestion_worker = None
        self._pending_suggestion_value = None
        self._suggestion_column = ""
        self._filter_suggestion_request_id = ""
        self._filter_suggestion_worker = None
        self._pending_filter_suggestion = None
        self._filter_suggestion_row = -1
        self._skey_request_id = ""
        self._skey_worker = None
        self._saved_search_link_request_id = ""
        self._saved_search_link_worker = None
        self._tag_context_key = ""
        self._tag_workers: dict[str, object] = {}
        self._tag_records: list[dict] = []
        self._tag_loading = False
        self._tag_error = ""
        self._applying_tag_filters = False
        self._quick_filter_runtime = QuickFilterRuntime()
        self._snapshot_check_request_id = ""
        self._node_load_requests: dict[str, tuple[str, float, str]] = {}
        self._checkin_tree_refresh_requests: dict[str, tuple] = {}
        self._restoring_nodes: set[str] = set()
        self._recursive_node_loads: set[str] = set()
        self._card_path: list[str] = []
        self._pending_card_focus_id = ""
        self._knowledge_link_index: dict[str, list[str]] = {}
        self._dcc_bridge = None
        self._registry = ActionRegistry()
        self._menus = MenuRegistry()
        self._quick_filters = QuickFilterCatalog()
        self.project_model = ProjectModel()
        self.navigation_model = NavigationModel()
        self.section_model = SectionTabModel()
        self._workspace_model = WorkspaceItemModel()
        self._workspace_model.setParent(self)
        self.versions_model = WorkspaceItemModel()
        self.workspace_state = WorkspaceState()
        self.repository_sync = RepositorySyncController(
            debug_log=self.debug_log,
            parent=self,
        )
        self.repository_sync.configuration_changed.connect(
            self.repository_sync_changed.emit
        )
        self.project_model.repository_sync = self.repository_sync
        self.workspace_model.repository_sync = self.repository_sync
        self.versions_model.repository_sync = self.repository_sync
        self.workspace_state._preview_helper.repository_sync = (
            self.repository_sync
        )
        self.repository_sync.task_finished.connect(
            self._repository_file_ready
        )
        self.repository_sync.task_failed.connect(
            self._repository_preview_failed
        )
        self.project_model.preview_ready.connect(
            self._project_preview_ready
        )
        try:
            from thlib.environment import env_inst
            env_inst.ui_repo_sync_queue = self.repository_sync
        except (ImportError, AttributeError):
            pass
        self.workspace_state.tab_activated.connect(self._activate_workspace_tab)
        self.workspace_state.tab_add_requested.connect(self.add_search_tab)
        self.workspace_state.tab_close_requested.connect(self.close_search_tab)
        self.workspace_state.tab_reorder_requested.connect(self.reorder_search_tab)
        self.workspace_state.description_save_requested.connect(
            self._save_description_async
        )
        self.workspace_state.note_add_requested.connect(self._add_note_async)
        self.workspace_state.task_status_requested.connect(
            self._set_task_status_async
        )
        self.dock_model = DockPanelModel(self._settings)
        self.window_model = FloatingWindowModel(self._settings)
        self.visible_dock_model = VisibleDockPanelModel(
            self.dock_model, self
        )
        self.detached_dock_model = DetachedDockPanelModel(
            self.dock_model, self
        )
        self.visible_window_model = VisibleFloatingWindowModel(
            self.window_model, self
        )
        self.repository_sync.visibility_requested.connect(
            lambda visible: (
                self.window_model.show_window("repository_sync")
                if visible
                else self.window_model.close_window("repository_sync")
            )
        )
        self.repository_sync.visibility_probe = lambda: (
            self.window_model.is_window_visible("repository_sync")
        )
        if self.debug_log:
            self.debug_log.show_requested.connect(
                lambda: self.window_model.show_window("debug_log")
            )
            self.debug_log.authentication_requested.connect(
                self._request_authentication
            )
            self.debug_log.error_dismissed.connect(
                self._error_dialog_dismissed
            )
            self.debug_log.configuration_requested.connect(
                lambda: self.window_model.show_window("configuration")
            )
        self._register_shell_commands()

    @property
    def workspace_model(self) -> WorkspaceItemModel:
        """Return the stable result model owned by the selected search tab."""
        tab = self._current_tab()
        if tab is not None:
            return self._ensure_tab_workspace_model(tab)
        return self._workspace_model

    def _workspace_models(self):
        """Iterate live result models once for cross-tab server updates."""
        models = [self._workspace_model]
        for section in self._sessions.values():
            models.extend(
                tab.workspace_model
                for tab in (*section.tabs, *section.closed_tabs)
            )
        seen = set()
        for model in models:
            if model is None or id(model) in seen:
                continue
            seen.add(id(model))
            yield model

    @Slot(str, str, int, object)
    def update_workspace_note_count(
        self,
        search_key: str,
        process: str,
        count: int,
        note_codes=None,
    ) -> None:
        for model in self._workspace_models():
            model.update_note_count(
                search_key, process, count, note_codes
            )

    @Slot(object)
    def apply_workspace_server_batch(self, batch) -> None:
        for model in self._workspace_models():
            model.apply_server_batch(batch)

    @Slot(object)
    def update_workspace_knowledge_index(self, values) -> None:
        self._knowledge_link_index = {
            str(search_key or ""): [
                str(identity or "")
                for identity in identities or []
                if str(identity or "")
            ]
            for search_key, identities in dict(values or {}).items()
            if str(search_key or "")
        }
        for model in self._workspace_models():
            model.set_knowledge_index(self._knowledge_link_index)

    @Slot(object)
    def apply_cache_invalidation(self, payload) -> None:
        """Invalidate server data without discarding live search sessions."""
        payload = dict(payload or {})
        hard_reset = bool(payload.get("all"))
        domains = {
            str(domain) for domain in payload.get("domains") or ()
        }
        if hard_reset:
            domains.update(("reference", "search", "snapshots", "relations"))
        for scope in (self._current_project_code, "sthpw"):
            domains.update(str(domain) for domain in payload.get(scope) or ())

        if "reference" in domains:
            self._tag_catalog_cache.clear()
            self._tag_context_key = ""
            self._quick_filter_runtime.invalidate()

        if not domains.intersection({
            "reference", "search", "snapshots", "relations",
        }):
            return

        generation_reset = bool(hard_reset or payload.get("preferences"))
        if generation_reset:
            for worker in tuple(self._search_workers.values()):
                worker.cancel()
            self._pending_search_loads.clear()
        for section in self._sessions.values():
            for tab in section.tabs:
                if generation_reset and tab.loading:
                    tab.request_id = ""
                    tab.loading = False
                    tab.loading_append = False
        if generation_reset:
            self._active_request_id = ""
            self._set_loading(False)
        self.search_state_changed.emit()
        self.tag_cloud_changed.emit()
        self.quick_filters_changed.emit()

    def _write_settings(self) -> None:
        env_write_config(
            self._settings,
            filename="ui_settings",
            unique_id="ui_main",
            long_abs_path=True,
        )

    def _write_search_cache_config(self) -> None:
        self._config_write_queue.submit(
            self._search_cache,
            filename="search_tabs",
            unique_id="cache",
            long_abs_path=True,
        )

    @Slot(str, str)
    def _config_write_failed(self, message: str, stacktrace: str) -> None:
        if not self.debug_log:
            return
        self.debug_log.log(
            "EXCEPTION",
            message,
            group="configs/persistence",
            source="Configuration writer",
            stacktrace=stacktrace,
        )

    def _save_snapshot_splitter_ratio(self) -> None:
        self._settings["snapshotBrowser/splitterRatio"] = (
            self._snapshot_browser_splitter_ratio
        )
        self._write_settings()

    @Property(str, notify=theme_style_changed)
    def theme_style(self) -> str:
        return self._theme_style

    @Property(str, notify=dcc_state_changed)
    def selected_dcc_application(self) -> str:
        return str(getattr(
            getattr(self, "_dcc_bridge", None),
            "selectedApplicationType",
            "standalone",
        ) or "standalone").lower()

    @Property(QObject, constant=True)
    def search_tab_switch_monitor(self) -> QObject:
        return self._search_tab_switch_monitor

    @Property(QObject, constant=True)
    def ui_performance(self) -> QObject:
        return self._performance

    @Property("QVariantList", constant=True)
    def theme_options(self) -> list[dict]:
        return [dict(record) for record in THEME_STYLES]

    @Property("QVariantList", constant=True)
    def accent_presets(self) -> list[dict]:
        return [dict(record) for record in ACCENT_PRESETS]

    @Property("QVariantMap", notify=accent_changed)
    def theme_accents(self) -> dict:
        return {
            style: dict(values)
            for style, values in self._theme_accents.items()
        }

    @Property(str, notify=accent_changed)
    def accent_preset(self) -> str:
        mode = "dark" if self._dark_theme else "light"
        return self._theme_accents[self._theme_style][mode]

    @Property(str, notify=accent_changed)
    def accent_color(self) -> str:
        return accent_color(self.accent_preset, self._dark_theme)

    @Property(str, notify=accent_changed)
    def base_color(self) -> str:
        return base_color(self.accent_preset, self._dark_theme)

    @Property("QVariantList", constant=True)
    def icon_set_options(self) -> list[dict]:
        return [dict(record) for record in ICON_SETS]

    @Property(str, notify=icon_set_changed)
    def icon_set(self) -> str:
        return self._icon_set

    @Property(bool, notify=animation_preferences_changed)
    def click_animations_enabled(self) -> bool:
        return self._click_animations_enabled

    @Property(bool, notify=animation_preferences_changed)
    def hover_animations_enabled(self) -> bool:
        return self._hover_animations_enabled

    @Property(bool, notify=animation_preferences_changed)
    def fade_animations_enabled(self) -> bool:
        return self._fade_animations_enabled

    @Property(bool, notify=animation_preferences_changed)
    def popup_animations_enabled(self) -> bool:
        return self._popup_animations_enabled

    @Property("QVariantList", notify=selected_node_changed)
    def selected_result_records(self) -> list[dict]:
        tab = self._current_tab()
        records = []
        for node_id in (tab.selected_node_ids if tab else []):
            node = self.workspace_model.node_for(node_id)
            if not node:
                continue
            values = self._editable_node_values(node)
            records.append({
                "nodeId": node.node_id,
                "searchKey": node.search_key,
                "title": node.title or node.code,
                "code": node.code,
                "type": node.node_type,
                "status": node.status or str(values.get("status") or ""),
                "description": str(
                    values.get("description") or node.subtitle or ""
                ),
                "values": {
                    str(key): "" if value is None else str(value)
                    for key, value in values.items()
                    if not str(key).startswith("__")
                },
            })
        return records

    @Property("QVariantList", notify=selected_node_changed)
    def selected_result_fields(self) -> list[str]:
        """Columns shared by the selected items, as in Ui_editDBTableWidget."""
        tab = self._current_tab()
        nodes = [
            self.workspace_model.node_for(node_id)
            for node_id in (tab.selected_node_ids if tab else [])
        ]
        nodes = [node for node in nodes if node and node.source]
        if not nodes:
            return []
        common = set(self._editable_columns_for_node(nodes[0]))
        for node in nodes[1:]:
            common.intersection_update(self._editable_columns_for_node(node))
        return sorted(common)

    @Property(str, notify=results_view_changed)
    def results_view_mode(self) -> str:
        tab = self._current_tab()
        return tab.view_mode if tab else self._default_view_mode

    @Property(str, notify=results_view_changed)
    def result_sort_mode(self) -> str:
        tab = self._current_tab()
        return tab.sort_mode if tab else "name_asc"

    @Property(str, notify=results_view_changed)
    def result_group_mode(self) -> str:
        tab = self._current_tab()
        return tab.group_mode if tab else "none"

    @Property("QVariantList", notify=results_view_changed)
    def result_sort_actions(self) -> list[dict]:
        mode = self.result_sort_mode
        return [
            {"title": "Sort items", "header": True},
            {
                "title": "Name A-Z", "icon": "sort-items",
                "command": "name_asc", "checked": mode == "name_asc",
            },
            {
                "title": "Name Z-A", "icon": "sort-items",
                "command": "name_desc", "checked": mode == "name_desc",
            },
            {
                "title": "Recently updated", "icon": "history",
                "command": "updated_desc",
                "checked": mode == "updated_desc",
            },
            {
                "title": "Oldest updated", "icon": "history",
                "command": "updated_asc", "checked": mode == "updated_asc",
            },
        ]

    @Property("QVariantList", notify=results_view_changed)
    def result_group_actions(self) -> list[dict]:
        tab = self._current_tab()
        if not tab:
            return []
        actions = [
            {"title": "Group items", "header": True},
            {
                "title": "No grouping", "icon": "list-alt",
                "command": "none", "checked": tab.group_mode == "none",
            },
            {
                "title": "SObject status", "icon": "group-items",
                "command": "status", "checked": tab.group_mode == "status",
            },
            {
                "title": "Pipeline", "icon": "process",
                "command": "pipeline",
                "checked": tab.group_mode == "pipeline",
            },
        ]
        processes = self._quick_filters.task_group_processes(
            tab.stype, tab.sobjects, tab.quick_filter_tasks
        ) if tab.stype else []
        if processes:
            actions.extend((
                {"separator": True},
                {"title": "Task status by process", "header": True},
            ))
        for process in processes:
            key = str(process.get("key") or "")
            actions.append({
                "title": str(process.get("title") or key),
                "translate": False,
                "accent": str(process.get("accent") or "#607d8b"),
                "command": "task_status:" + key,
                "checked": tab.group_mode == "task_status"
                    and tab.task_group_process == key,
            })
        return actions

    @Property(bool, notify=results_view_changed)
    def description_limit_enabled(self) -> bool:
        return self._description_limit_enabled

    @Property(int, notify=results_view_changed)
    def description_limit(self) -> int:
        return self._description_limit

    def _read_checkin_defaults(self) -> None:
        from thlib import global_functions as gf
        from thlib.environment import cfg_controls

        config = cfg_controls.get_checkin() or {}

        def value(control, default):
            stored = gf.get_value_from_config(config, control)
            return default if stored is None else stored

        try:
            self._page_size = max(20, min(
                5000, int(value("displayLimitSpinBox", 20))
            ))
        except (TypeError, ValueError):
            self._page_size = 20
        try:
            view_index = int(value("defaultSearchViewComboBox", 0))
        except (TypeError, ValueError):
            view_index = 0
        self._default_view_mode = "tiles" if view_index == 1 else "continious"
        self._description_limit_enabled = bool(value(
            "snapshotDescriptionLimitCheckBox", True
        ))
        try:
            self._description_limit = max(20, min(
                50000, int(value("snapshotDescriptionLimitSpinBox", 80))
            ))
        except (TypeError, ValueError):
            self._description_limit = 80

    @Slot()
    def refresh_checkin_defaults(self) -> None:
        previous = (
            self._page_size,
            self._default_view_mode,
            self._description_limit_enabled,
            self._description_limit,
        )
        self._read_checkin_defaults()
        self.project_model.refresh_previews()
        preview_nodes = list(dict.fromkeys(
            self.workspace_model.refresh_previews()
            + self.versions_model.refresh_previews()
        ))
        for node_id in preview_nodes:
            if self.results_view_mode == "tiles":
                self.request_item_card_preview(node_id)
            else:
                self.request_item_preview(node_id)
        if self._current_project_code:
            project = next(
                (
                    item for item in self.project_model._all_entries
                    if item.get_code() == self._current_project_code
                ),
                None,
            )
            if project:
                self._current_project_preview = (
                    self.project_model.preview_for(project)
                )
                self.project_state_changed.emit()
        current = (
            self._page_size,
            self._default_view_mode,
            self._description_limit_enabled,
            self._description_limit,
        )
        if current != previous:
            self.paging_state_changed.emit()
            self.results_view_changed.emit()

    @Property(bool, notify=results_view_changed)
    def card_can_go_back(self) -> bool:
        return bool(self._card_path)

    @Property(str, notify=results_view_changed)
    def card_level_title(self) -> str:
        if not self._card_path:
            return "Search results"
        node = self.workspace_model.node_for(self._card_path[-1])
        return str(node.title if node else "Search results")

    @Property("QVariantList", notify=results_view_changed)
    def card_breadcrumb(self) -> list[dict]:
        items = [{
            "depth": 0,
            "title": "Search results",
            "icon": "dashboard",
        }]
        for depth, node_id in enumerate(self._card_path, 1):
            node = self.workspace_model.node_for(node_id)
            if not node:
                continue
            icon = {
                "process": "process",
                "relation": "stream",
                "snapshot": "camera",
                "file": "file",
            }.get(node.node_type, "sobject")
            items.append({
                "depth": depth,
                "title": str(node.title or node.code or node_id),
                "icon": icon,
            })
        return items

    @Property(bool, notify=results_view_changed)
    def card_compact_level(self) -> bool:
        items = self.workspace_model._items
        return bool(items) and all(
            node.node_type in {"process", "relation"} for node in items
        )

    @Property(float, notify=results_view_changed)
    def results_splitter_ratio(self) -> float:
        tab = self._current_tab()
        return tab.splitter_ratio if tab else 0.58

    @Property(bool, notify=snapshot_browser_changed)
    def snapshot_browser_show_all(self) -> bool:
        return self._snapshot_browser_show_all

    @Property(bool, notify=snapshot_browser_changed)
    def snapshot_browser_show_more(self) -> bool:
        return self._snapshot_browser_show_more

    @Property(str, notify=snapshot_browser_changed)
    def snapshot_browser_content_mode(self) -> str:
        return self._snapshot_browser_content_mode

    @Property(str, notify=snapshot_browser_changed)
    def snapshot_browser_orientation(self) -> str:
        return self._snapshot_browser_orientation

    @Property(float, notify=snapshot_browser_changed)
    def snapshot_browser_splitter_ratio(self) -> float:
        return self._snapshot_browser_splitter_ratio

    @Property(bool, notify=loading_changed)
    def loading(self) -> bool:
        return self._loading

    @Property(str, notify=loading_changed)
    def loading_message(self) -> str:
        return self._loading_message

    @Property("QVariantList", notify=activity_log_changed)
    def activity_log(self) -> list[str]:
        return list(self._activity_log)

    @Property(str, notify=paging_state_changed)
    def loading_mode(self) -> str:
        return self._loading_mode

    @Property(int, notify=paging_state_changed)
    def page_size(self) -> int:
        tab = self._current_tab()
        return tab.limit if tab else self._page_size

    @Property(int, notify=paging_state_changed)
    def current_page(self) -> int:
        tab = self._current_tab()
        return (tab.offset // tab.limit) + 1 if tab and tab.limit else 1

    @Property(int, notify=paging_state_changed)
    def page_count(self) -> int:
        tab = self._current_tab()
        return max(1, math.ceil(tab.total / tab.limit)) if tab and tab.limit else 1

    @Property("QVariantList", notify=paging_state_changed)
    def page_numbers(self) -> list[int]:
        total = self.page_count
        current = self.current_page
        start = max(1, min(current - 2, total - 4))
        end = min(total, start + 4)
        return list(range(start, end + 1))

    @Property(int, notify=paging_state_changed)
    def first_result(self) -> int:
        tab = self._current_tab()
        if not tab or not tab.total:
            return 0
        if self._loading_mode == "infinite":
            return 1
        return tab.offset + 1

    @Property(int, notify=paging_state_changed)
    def last_result(self) -> int:
        tab = self._current_tab()
        if not tab:
            return 0
        if self._loading_mode == "infinite":
            return min(tab.total, len(tab.sobjects))
        return min(tab.total, tab.offset + len(tab.sobjects))

    @Property(bool, notify=paging_state_changed)
    def has_more(self) -> bool:
        tab = self._current_tab()
        return bool(
            tab
            and not tab.error
            and not tab.cancelled
            and not tab.exhausted
            and (tab.total <= 0 or tab.next_offset < tab.total)
        )

    @Property(str, notify=search_state_changed)
    def search_state(self) -> str:
        tab = self._current_tab()
        if not tab:
            return "idle"
        if tab.loading:
            return "loading"
        if tab.error:
            return "error"
        if tab.cancelled:
            return "cancelled"
        if tab.loaded and not self._visible_sobjects(tab):
            return "empty"
        return "ready" if tab.loaded else "idle"

    @Property(bool, notify=search_state_changed)
    def loading_more(self) -> bool:
        tab = self._current_tab()
        return bool(
            tab and tab.loading and tab.loading_append
        )

    @Property(str, notify=search_state_changed)
    def search_error(self) -> str:
        tab = self._current_tab()
        return tab.error if tab else ""

    @Property(str, notify=server_state_changed)
    def current_user_initials(self) -> str:
        return self._current_user_initials

    @Property(str, notify=server_state_changed)
    def server_url(self) -> str:
        from thlib.environment import env_server
        return str(env_server.get_server() or "")

    @Property(str, notify=server_state_changed)
    def server_user(self) -> str:
        from thlib.environment import env_server
        return str(env_server.get_user() or "")

    @Property(bool, notify=server_state_changed)
    def can_administer(self) -> bool:
        return (
            self._server_state == "online" and self.has_ticket
            and self._administration_identity == (self.server_url, self.server_user)
        )

    @Property(str, notify=server_state_changed)
    def server_preset(self) -> str:
        from thlib.environment import env_server
        return str(env_server.get_cur_srv_preset() or "")

    @Property(str, notify=server_state_changed)
    def server_site(self) -> str:
        from thlib.environment import env_server
        return str((env_server.get_site() or {}).get("site_name") or "")

    @Property(str, notify=server_state_changed)
    def server_proxy(self) -> str:
        from thlib.environment import env_server
        return str((env_server.get_proxy() or {}).get("server") or "")

    @Property(bool, notify=server_state_changed)
    def has_ticket(self) -> bool:
        from thlib.environment import env_server
        return bool(env_server.get_ticket())

    @Property(bool, notify=authentication_changed)
    def authentication_required(self) -> bool:
        return self._authentication_required

    @Property(bool, notify=authentication_changed)
    def authentication_dialog_visible(self) -> bool:
        return self._authentication_dialog_visible

    @Property(bool, notify=authentication_changed)
    def authentication_busy(self) -> bool:
        return self._authentication_busy

    @Property(str, notify=authentication_changed)
    def authentication_error(self) -> str:
        return self._authentication_error

    @Property(str, notify=authentication_changed)
    def login_name(self) -> str:
        return self._login_name

    @Property(str, notify=project_state_changed)
    def current_project_title(self) -> str:
        return self._current_project_title

    @Property(str, notify=project_state_changed)
    def current_project_code(self) -> str:
        return self._current_project_code

    @Property(int, constant=True)
    def window_x(self) -> int:
        return self._window_state["x"]

    @Property(int, constant=True)
    def window_y(self) -> int:
        return self._window_state["y"]

    @Property(int, constant=True)
    def window_width(self) -> int:
        return self._window_state["width"]

    @Property(int, constant=True)
    def window_height(self) -> int:
        return self._window_state["height"]

    @Property(bool, constant=True)
    def window_maximized(self) -> bool:
        return self._window_state["maximized"]

    @Property(str, notify=project_state_changed)
    def current_project_preview(self) -> str:
        return self._current_project_preview

    @Property(str, notify=server_state_changed)
    def server_state(self) -> str:
        return self._server_state

    @Property(str, notify=server_state_changed)
    def server_message(self) -> str:
        return self._server_message

    @Property(int, notify=connection_settings_changed)
    def ping_interval(self) -> int:
        return self._ping_interval

    @Property(int, notify=result_count_changed)
    def result_count(self) -> int:
        return self._result_count

    @Property(str, notify=result_count_changed)
    def current_page_key(self) -> str:
        return self._current_page_key

    @Property(str, notify=search_text_changed)
    def current_search_text(self) -> str:
        tab = self._current_tab()
        return tab.search_text if tab else ""

    @Property(str, notify=search_text_changed)
    def current_search_tab_title(self) -> str:
        tab = self._current_tab()
        return tab.title if tab else ""

    @Property("QVariantList", notify=quick_filters_changed)
    def quick_filter_groups(self) -> list[dict]:
        section = self._current_section()
        tab = self._current_tab()
        if not section or not tab:
            return []
        return self._quick_filters.groups(
            section.entry_key,
            tab.stype or self._active_stype(),
            tab.sobjects,
            tab.quick_filters,
            tab.quick_filter_tasks,
            self._login_name,
            self._active_quick_filter_facets(),
            local_groups=tab.quick_filter_layout,
        )

    @Property(bool, notify=quick_filters_changed)
    def quick_filter_catalog_loading(self) -> bool:
        return self._quick_filter_runtime.loading

    @Property(str, notify=quick_filters_changed)
    def quick_filter_catalog_error(self) -> str:
        return self._quick_filter_runtime.error

    @Property("QVariantList", notify=quick_filters_changed)
    def quick_filter_assignee_logins(self) -> list[str]:
        tab = self._current_tab()
        if not tab:
            return []
        return sorted(
            str(value)
            for value in tab.quick_filters.get("assigned", set())
            if value != self._quick_filters.CURRENT_LOGIN_FILTER
        )

    @Property(bool, notify=quick_filters_changed)
    def quick_filter_my_tasks(self) -> bool:
        tab = self._current_tab()
        return bool(
            tab
            and self._quick_filters.CURRENT_LOGIN_FILTER
            in tab.quick_filters.get("assigned", set())
        )

    @Property(bool, notify=quick_filters_changed)
    def quick_filter_is_personalized(self) -> bool:
        tab = self._current_tab()
        return bool(
            tab
            and tab.tab_kind in STANDARD_QUICK_FILTER_TAB_KINDS
            and tab.quick_filter_personalized
        )


    @Property(int, notify=quick_filters_changed)
    def active_quick_filter_count(self) -> int:
        tab = self._current_tab()
        return sum(
            len(values)
            for values in (tab.quick_filters.values() if tab else ())
        )

    @Property("QVariantList", notify=tag_cloud_changed)
    def tag_cloud(self) -> list[dict]:
        tab = self._current_tab()
        selected = tab.selected_tags if tab else set()
        return [
            {
                **record,
                "selected": record.get("tag") in selected,
            }
            for record in self._tag_records
        ]

    @Property(bool, notify=tag_cloud_changed)
    def tag_cloud_loading(self) -> bool:
        return self._tag_loading

    @Property(str, notify=tag_cloud_changed)
    def tag_cloud_error(self) -> str:
        return self._tag_error

    @Property(int, notify=tag_cloud_changed)
    def active_tag_count(self) -> int:
        tab = self._current_tab()
        return len(tab.selected_tags) if tab else 0

    @Property(int, notify=advanced_filter_suggestions_changed)
    def advanced_filter_suggestion_row(self) -> int:
        return self._filter_suggestion_row

    @Property("QVariantList", notify=search_tab_history_changed)
    def closed_search_tabs(self) -> list[dict]:
        section = self._current_section()
        if not section or not section.closed_tabs:
            return []
        actions = [
            {
                "title": "Clear history",
                "icon": "delete",
                "command": "clear_history",
            },
            {"separator": True},
        ]
        actions.extend(
            {
                "title": tab.title or "Search tab",
                "icon": "history",
                "command": f"restore_tab:{row}",
            }
            for row, tab in enumerate(section.closed_tabs)
        )
        return actions

    @Property(str, notify=result_count_changed)
    def current_page_title(self) -> str:
        return self._current_page_title

    @Property(str, notify=section_state_changed)
    def current_section_key(self) -> str:
        return self._current_section_key

    @Property(str, notify=selected_node_changed)
    def selected_node_id(self) -> str:
        tab = self._current_tab()
        return tab.selected_node_id if tab else ""

    @Property("QVariantList", notify=selected_node_changed)
    def selected_result_node_ids(self) -> list[str]:
        tab = self._current_tab()
        return list(tab.selected_node_ids) if tab else []

    @Property(int, notify=selected_node_changed)
    def selected_result_count(self) -> int:
        tab = self._current_tab()
        return len(tab.selected_node_ids) if tab else 0
