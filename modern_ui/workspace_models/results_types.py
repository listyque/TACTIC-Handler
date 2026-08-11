"""Value objects for workspace models."""

from __future__ import annotations

from dataclasses import dataclass, field

@dataclass(slots=True)
class WorkspaceNode:
    node_id: str
    node_type: str
    search_key: str
    code: str
    title: str
    subtitle: str = ""
    status: str = ""
    accent: str = "#607d8b"
    comments: int = 0
    tasks: int = 0
    depth: int = 0
    expanded: bool = False
    has_children: bool = False
    loaded: bool = False
    loading: bool = False
    context: str = ""
    version: str = ""
    file_path: str = ""
    file_size: str = ""
    parent_id: str = ""
    process: str = ""
    author: str = ""
    timestamp: str = ""
    revision: str = ""
    repository: str = ""
    repository_color: str = ""
    preview_url: str = ""
    preview_source: object = None
    preview_requested: bool = False
    preview_revealed: bool = False
    relationship: str = ""
    watch_state: str = "none"
    file_exists: bool = False
    is_latest: bool = False
    is_versionless: bool = False
    is_multiple: bool = False
    needs_sync: bool = False
    child_count: int = 0
    progress_items: list[dict] = field(default_factory=list)
    controls_cache: list[dict] = field(default_factory=list)
    controls_signature: tuple = field(default_factory=tuple)
    values: dict = field(default_factory=dict)
    chips: list[dict] = field(default_factory=list)
    source: object = None
    relation: object = None
    lazy_versions: list = field(default_factory=list)
    children: list["WorkspaceNode"] = field(default_factory=list)
    restore_state: dict = field(default_factory=dict)
    restore_expanded: bool = False
