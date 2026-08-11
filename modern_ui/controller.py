"""Public QML application controller."""

from __future__ import annotations

import math

from PySide6.QtCore import QObject, Property, QSettings, QTimer, Signal, Slot

from .controllers.types import (
    ActionRegistry,
    SearchTabSession,
    SectionSession,
)
from .menu_schema import MenuRegistry
from .models import NavigationModel, ProjectModel
from .quick_filters import QuickFilterCatalog
from .theme_catalog import THEME_STYLES, normalize_theme_style
from .repository_sync import RepositorySyncController
from .workspace import (
    DockPanelModel,
    FloatingWindowModel,
    SectionTabModel,
    WorkspaceItemModel,
    WorkspaceState,
)
from .controllers.item_mutations import ItemMutationsMixin
from .controllers.lifecycle import LifecycleMixin
from .controllers.connection import ConnectionMixin
from .controllers.navigation import NavigationMixin
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


class ApplicationController(
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

    page_changed = Signal(str, str)

    command_requested = Signal(str)

    notification_changed = Signal(str)

    project_changed = Signal(str, str)

    project_state_changed = Signal()

    server_state_changed = Signal()

    result_count_changed = Signal()

    section_state_changed = Signal()

    selected_node_changed = Signal()

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

    temporary_tools_requested = Signal()

    checkinFilesRequested = Signal()

    revisionCheckinConfirmationRequested = Signal()

    def __init__(self, debug_log=None) -> None:
        super().__init__()
        self.debug_log = debug_log
        # A section/tab replacement can also replace its selected node.
        # Ordinary item selection emits only selected_node_changed so the
        # whole section UI is not invalidated on every click.
        self.section_state_changed.connect(self.selected_node_changed.emit)
        self.section_state_changed.connect(self.results_view_changed.emit)
        self._settings = QSettings("TACTIC-Handler", "modern-qml")
        self._window_state = {
            "x": self._settings.value("window/x", 80, type=int),
            "y": self._settings.value("window/y", 60, type=int),
            "width": max(760, self._settings.value("window/width", 1280, type=int)),
            "height": max(560, self._settings.value("window/height", 820, type=int)),
            "maximized": self._settings.value("window/maximized", False, type=bool),
        }
        self._window_state_timer = QTimer(self)
        self._window_state_timer.setSingleShot(True)
        self._window_state_timer.timeout.connect(self._write_window_state)
        # The production interface and reference recording start dark.  The
        # persisted preference can still select the light theme on later runs.
        self._dark_theme = self._settings.value("appearance/darkTheme", True, type=bool)
        self._theme_style = normalize_theme_style(
            self._settings.value("appearance/themeStyle", "md3", type=str)
        )
        self._current_project_code = ""
        self._current_project_title = ""
        self._current_project_preview = ""
        self._sobject_editor_request = {}
        self._sobject_link_request = {}
        self._server_state = "connecting"
        self._server_message = ""
        self._result_count = 0
        self._current_page_key = ""
        self._current_page_title = ""
        self._current_user_initials = ""
        self._current_section_key = ""
        self._loading = False
        self._loading_message = ""
        self._authentication_required = False
        self._authentication_dialog_visible = False
        self._authentication_busy = False
        self._authentication_error = ""
        self._authentication_started_at = 0.0
        self._login_name = self._settings.value("server/lastLogin", "", type=str)
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
        self._ping_interval = self._settings.value(
            "server/pingInterval", 0, type=int
        )
        if self._ping_interval not in {0, 10, 60}:
            self._ping_interval = 0
        self._ping_in_progress = False
        self._ping_started_at = 0.0
        self._ping_timer = QTimer(self)
        self._ping_timer.timeout.connect(self.ping_server)
        if self._ping_interval:
            self._ping_timer.start(self._ping_interval * 1000)
        self._loading_mode = self._settings.value("search/loadingMode", "pages", type=str)
        if self._loading_mode not in {"pages", "infinite"}:
            self._loading_mode = "pages"
        self._page_size = 20
        self._default_view_mode = "continious"
        self._description_limit_enabled = True
        self._description_limit = 80
        self._read_checkin_defaults()
        self._snapshot_browser_show_all = self._settings.value(
            "snapshotBrowser/showAll", False, type=bool
        )
        self._snapshot_browser_show_more = self._settings.value(
            "snapshotBrowser/showMore", False, type=bool
        )
        self._snapshot_browser_orientation = self._settings.value(
            "snapshotBrowser/orientation", "horizontal", type=str
        )
        if self._snapshot_browser_orientation not in {
            "horizontal", "vertical"
        }:
            self._snapshot_browser_orientation = "horizontal"
        self._snapshot_browser_splitter_ratio = max(
            0.22,
            min(
                0.78,
                self._settings.value(
                    "snapshotBrowser/splitterRatio", 0.52, type=float
                ),
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
            lambda: self._settings.setValue(
                "snapshotBrowser/splitterRatio",
                self._snapshot_browser_splitter_ratio,
            )
        )
        self._sessions: dict[str, SectionSession] = {}
        self._search_cache_save_timer = QTimer(self)
        self._search_cache_save_timer.setSingleShot(True)
        self._search_cache_save_timer.setInterval(250)
        self._search_cache_save_timer.timeout.connect(
            self._write_search_cache
        )
        self._active_request_id = ""
        self._search_workers = {}
        self._pending_search_loads = {}
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
        self._pending_item_node_id = ""
        self._pending_item_action = ""
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
        self._tag_request_id = ""
        self._tag_records: list[dict] = []
        self._tag_loading = False
        self._tag_error = ""
        self._applying_tag_filters = False
        self._snapshot_check_request_id = ""
        self._snapshot_editors = []
        self._node_load_requests: dict[str, tuple[str, float, str]] = {}
        self._restoring_nodes: set[str] = set()
        self._recursive_node_loads: set[str] = set()
        self._card_path: list[str] = []
        self._pending_card_focus_id = ""
        self._dcc_bridge = None
        self._registry = ActionRegistry()
        self._menus = MenuRegistry()
        self._quick_filters = QuickFilterCatalog()
        self.project_model = ProjectModel()
        self.navigation_model = NavigationModel()
        self.section_model = SectionTabModel()
        self.workspace_model = WorkspaceItemModel()
        self.versions_model = WorkspaceItemModel()
        self.workspace_state = WorkspaceState()
        self.repository_sync = RepositorySyncController(
            debug_log=self.debug_log,
            parent=self,
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

    @Property(str, notify=theme_style_changed)
    def theme_style(self) -> str:
        return self._theme_style

    @Property("QVariantList", constant=True)
    def theme_options(self) -> list[dict]:
        return [dict(record) for record in THEME_STYLES]

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
            section.search_type,
            tab.stype or self._active_stype(),
            tab.sobjects,
            tab.quick_filters,
            tab.quick_filter_tasks,
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
