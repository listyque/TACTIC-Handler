"""Small value objects shared by application controllers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

@dataclass(slots=True)
class SearchTabSession:
    tab_id: str
    title: str
    tab_kind: str = "search"
    navigation_target: str = ""
    search_text: str = ""
    extra_filters: list = field(default_factory=list)
    # Exact Advanced Search presentation state. This intentionally differs
    # from ``extra_filters``: legacy presets may contain enabled blank rows
    # which must remain visible but must not be sent as server filters.
    filter_records: list[dict] = field(default_factory=list)
    offset: int = 0
    next_offset: int = 0
    limit: int = 25
    total: int = 0
    exhausted: bool = False
    duplicate_pages: int = 0
    sobjects: list = field(default_factory=list)
    stype: object = None
    loaded: bool = False
    request_id: str = ""
    started_at: float = 0.0
    workspace_roots: list = field(default_factory=list)
    tree_state: dict = field(default_factory=dict)
    selected_node_id: str = ""
    selected_node_ids: list[str] = field(default_factory=list)
    selection_anchor_id: str = ""
    view_mode: str = "continious"
    splitter_ratio: float = 0.58
    loading: bool = False
    error: str = ""
    cancelled: bool = False
    failure_count: int = 0
    failure_signature: str = ""
    quick_filters: dict[str, set[str]] = field(default_factory=dict)
    quick_filter_tasks: dict[str, list] = field(default_factory=dict)
    quick_filter_task_codes: set[str] = field(default_factory=set)
    quick_filter_task_loaded_at: float = 0.0
    quick_filter_task_request_id: str = ""
    selected_tags: set[str] = field(default_factory=set)
    tag_column: str = ""
    process_ignore: dict = field(default_factory=dict)
    pending_snapshot_code: str = ""
    pending_snapshot_process: str = ""
    pending_detail_process: str = ""
    details_node_id: str = ""
    details_payload: tuple | None = None
    details_versions: list = field(default_factory=list)

    def clear_details(self) -> None:
        self.details_node_id = ""
        self.details_payload = None
        self.details_versions.clear()

@dataclass(slots=True)
class SectionSession:
    entry_key: str
    title: str
    accent: str
    search_type: str
    search_view: str = ""
    base_filters: tuple = ()
    tabs: list[SearchTabSession] = field(default_factory=list)
    closed_tabs: list[SearchTabSession] = field(default_factory=list)
    current_tab_id: str = ""

class ActionRegistry:
    """Named commands keep QML controls independent of their implementation."""

    def __init__(self) -> None:
        self._commands: dict[str, Callable[[], None]] = {}

    def register(self, name: str, callback: Callable[[], None]) -> None:
        self._commands[name] = callback

    def invoke(self, name: str) -> bool:
        callback = self._commands.get(name)
        if callback is None:
            return False
        callback()
        return True
