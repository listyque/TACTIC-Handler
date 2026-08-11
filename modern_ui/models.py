"""QML-facing models; no TACTIC network calls are allowed in this module."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    Property,
    Qt,
    QUrl,
    Signal,
    Slot,
)


@dataclass(frozen=True, slots=True)
class NavigationEntry:
    key: str
    title: str
    glyph: str
    group: str
    command: str
    badge: int = 0
    available: bool = True
    entry_type: str = "link"
    depth: int = 0
    accent: str = ""
    expanded: bool = True
    visible: bool = True
    search_type: str = ""
    filters: tuple = ()


class NavigationModel(QAbstractListModel):
    """Flat SideBarWdg navigation rendered by QML."""

    KeyRole = Qt.UserRole + 1
    TitleRole = Qt.UserRole + 2
    GlyphRole = Qt.UserRole + 3
    GroupRole = Qt.UserRole + 4
    CommandRole = Qt.UserRole + 5
    BadgeRole = Qt.UserRole + 6
    EnabledRole = Qt.UserRole + 7
    TypeRole = Qt.UserRole + 8
    DepthRole = Qt.UserRole + 9
    AccentRole = Qt.UserRole + 10
    ExpandedRole = Qt.UserRole + 11
    VisibleRole = Qt.UserRole + 12

    def __init__(self, entries: Iterable[NavigationEntry] = ()) -> None:
        super().__init__()
        self._entries = list(entries)

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.KeyRole: b"entryKey",
            self.TitleRole: b"title",
            self.GlyphRole: b"glyph",
            self.GroupRole: b"group",
            self.CommandRole: b"command",
            self.BadgeRole: b"badge",
            self.EnabledRole: b"available",
            self.TypeRole: b"entryType",
            self.DepthRole: b"entryDepth",
            self.AccentRole: b"accent",
            self.ExpandedRole: b"expanded",
            self.VisibleRole: b"entryVisible",
        }

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._entries)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._entries):
            return None
        entry = asdict(self._entries[index.row()])
        role_keys = {
            self.KeyRole: "key", self.TitleRole: "title", self.GlyphRole: "glyph",
            self.GroupRole: "group", self.CommandRole: "command", self.BadgeRole: "badge",
            self.EnabledRole: "available", self.TypeRole: "entry_type", self.DepthRole: "depth",
            self.AccentRole: "accent", self.ExpandedRole: "expanded", self.VisibleRole: "visible",
        }
        return entry.get(role_keys.get(role, ""))

    def replace(self, entries: Iterable[NavigationEntry]) -> None:
        self.beginResetModel()
        self._entries = list(entries)
        self.endResetModel()

    def append(self, entry: NavigationEntry) -> None:
        row = len(self._entries)
        self.beginInsertRows(QModelIndex(), row, row)
        self._entries.append(entry)
        self.endInsertRows()

    def entry(self, key: str) -> NavigationEntry | None:
        return next((entry for entry in self._entries if entry.key == key), None)

    def key_for_search_type(self, search_type: str) -> str:
        entry = next(
            (
                entry for entry in self._entries
                if entry.search_type == search_type
            ),
            None,
        )
        return entry.key if entry else ""

    def entries_for_search_type(
        self,
        search_type: str,
    ) -> tuple[NavigationEntry, ...]:
        return tuple(
            entry for entry in self._entries
            if entry.entry_type == "link"
            and entry.search_type == search_type
        )

    @staticmethod
    def _icon_name(server_icon: str, search_type: str) -> str:
        source = f"{server_icon or ''} {search_type or ''}".lower()
        if "task" in source or "calendar-check" in source:
            return "task_alt"
        if "snapshot" in source or "publish" in source:
            return "publish"
        if any(value in source for value in ("film", "scene", "episode")):
            return "movie"
        if "login" in source or "user" in source:
            return "person"
        if "project" in source:
            return "project-diagram"
        if any(value in source for value in ("message", "note", "chat")):
            return "comment"
        if "process" in source:
            return "process"
        if "asset" in source:
            return "sobject"
        if "list" in source:
            return "view_kanban"
        return "sobject"

    @staticmethod
    def _item_filters(project, item, search_type: str) -> tuple:
        search_view_node = item.find("search_view")
        if not search_view_node:
            return ()
        search_view = search_view_node.get_text(strip=True)
        definition = project.get_config_views().get_view(
            search_type,
            search_view,
            bs=True,
        )
        values = definition.find("values") if definition else None
        if not values or not values.string:
            return ()
        import thlib.global_functions as gf
        import thlib.tactic_classes as tc

        records = gf.from_json(values.string) or []
        filters = []
        for record in records[1:-1]:
            relation = record.get("main_body_relation")
            if relation == "expression":
                relation = record.get("main_body_op")
            filters.append((
                record.get("main_body_column"),
                tc.get_search_relation(relation),
                record.get("main_body_value"),
            ))
        return tuple(filters)

    @classmethod
    def build_project_entries(
        cls,
        project,
        current_login,
    ) -> list[NavigationEntry]:
        views = project.get_config_views()
        if not views or not views.has_definition() or not current_login:
            return []
        definitions = views.get_view("SideBarWdg")
        requested = views.get_view("SideBarWdg", "tactic_handler")
        if not requested:
            requested = views.get_view("SideBarWdg", "project_view")
        by_name = {
            definition["name"]: definition
            for definition in definitions
        }

        def selected(view):
            return [
                by_name[entry["name"]]
                for entry in view
                if entry["name"] in by_name
            ]

        def flatten(items, depth=0):
            entries = []
            for item in items:
                name = item.get("name") or "untitled"
                access = current_login.check_security(
                    group="link",
                    path=f"element:{name}",
                    project=project.get_code(),
                )
                if access != "allow":
                    continue
                display_node = item.find("display")
                display = display_node.get("class") if display_node else []
                display_class = display[0] if display else "LinkWdg"
                title = item.get("title") or name.replace("_", " ").title()
                if display_class == "SeparatorWdg":
                    entries.append(NavigationEntry(
                        f"separator:{depth}:{name}",
                        "",
                        "",
                        "",
                        "",
                        entry_type="separator",
                        depth=depth,
                    ))
                    continue
                if display_class == "SideBarSectionLinkWdg":
                    entries.append(NavigationEntry(
                        f"section:{name}",
                        title,
                        "keyboard_arrow_down",
                        "",
                        "",
                        entry_type="section",
                        depth=depth,
                    ))
                    if item.view:
                        nested = views.get_view(
                            "SideBarWdg",
                            item.view.string,
                        ) or []
                        entries.extend(flatten(selected(nested), depth + 1))
                    continue
                search_node = item.find("search_type")
                search_type = (
                    search_node.get_text(strip=True)
                    if search_node else ""
                )
                if search_type.startswith("sthpw"):
                    from thlib.environment import env_inst
                    # Building the project sidebar must not pull the complete
                    # sthpw schema/pipeline catalog merely to obtain an accent
                    # color.  Reuse it when another workflow already loaded
                    # the native Project data; otherwise fall back to the
                    # normal themed accent used below.
                    sthpw_project = (env_inst.projects or {}).get("sthpw")
                    loaded_stypes = (
                        getattr(sthpw_project, "stypes", None) or {}
                    )
                    stype = loaded_stypes.get(search_type)
                else:
                    stype = (
                        project.get_stypes().get(search_type)
                        if search_type else None
                    )
                accent = (
                    stype.get_stype_color(fmt="hex")
                    if stype and stype.get_stype_color(fmt="hex")
                    else ""
                )
                entries.append(NavigationEntry(
                    key=f"{search_type or name}@{name}",
                    title=title,
                    glyph=cls._icon_name(
                        item.get("icon", ""),
                        search_type,
                    ),
                    group="",
                    command="open_sidebar_item",
                    depth=depth,
                    accent=accent,
                    search_type=search_type,
                    filters=cls._item_filters(
                        project,
                        item,
                        search_type,
                    ) if search_type else (),
                ))
            return entries

        return flatten(selected(requested))

    def _recalculate_visibility(self) -> None:
        expanded_by_depth: dict[int, bool] = {}
        changed_rows: list[int] = []
        for row, entry in enumerate(self._entries):
            for depth in tuple(expanded_by_depth):
                if depth >= entry.depth:
                    del expanded_by_depth[depth]
            visible = all(expanded_by_depth.values())
            if entry.visible != visible:
                self._entries[row] = replace(entry, visible=visible)
                changed_rows.append(row)
                entry = self._entries[row]
            if entry.entry_type == "section":
                expanded_by_depth[entry.depth] = entry.expanded
        for row in changed_rows:
            index = self.index(row, 0)
            self.dataChanged.emit(index, index)

    @Slot(int)
    def toggle_section(self, row: int) -> None:
        if not 0 <= row < len(self._entries):
            return
        entry = self._entries[row]
        if entry.entry_type != "section":
            return
        self._entries[row] = replace(entry, expanded=not entry.expanded)
        index = self.index(row, 0)
        self.dataChanged.emit(index, index)
        self._recalculate_visibility()


class ProjectModel(QAbstractListModel):
    CodeRole = Qt.UserRole + 1
    TitleRole = Qt.UserRole + 2
    CategoryRole = Qt.UserRole + 3
    StatusRole = Qt.UserRole + 4
    PreviewRole = Qt.UserRole + 5
    TemplateRole = Qt.UserRole + 6
    RetiredRole = Qt.UserRole + 7
    filter_changed = Signal()
    preview_ready = Signal(str, str)
    _preview_cache_limit = 256

    def __init__(self) -> None:
        super().__init__()
        self._all_entries: list[object] = []
        self._entries: list[object] = []
        self._preview_cache: OrderedDict[str, str] = OrderedDict()
        self._pending_preview_paths: dict[str, str] = {}
        self.repository_sync = None
        self._show_retired = False
        self._show_templates = False

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.CodeRole: b"projectCode", self.TitleRole: b"title",
            self.CategoryRole: b"category", self.StatusRole: b"status",
            self.PreviewRole: b"preview", self.TemplateRole: b"isTemplate",
            self.RetiredRole: b"isRetired",
        }

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._entries)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._entries):
            return None
        project = self._entries[index.row()]
        values = self.values(project)
        return {
            self.CodeRole: values["code"],
            self.TitleRole: values["title"],
            self.CategoryRole: values["category"],
            self.StatusRole: values["status"],
            self.PreviewRole: values["preview"],
            self.TemplateRole: values["isTemplate"],
            self.RetiredRole: values["isRetired"],
        }.get(role)

    def replace(self, entries: Iterable[object]) -> None:
        self._all_entries = list(entries)
        self._preview_cache.clear()
        self._pending_preview_paths.clear()
        self._apply_filter()

    def refresh_previews(self) -> None:
        self._preview_cache.clear()
        self._pending_preview_paths.clear()
        if not self._entries:
            return
        first = self.index(0, 0)
        last = self.index(len(self._entries) - 1, 0)
        self.dataChanged.emit(first, last, [self.PreviewRole])

    def _apply_filter(self) -> None:
        self.beginResetModel()
        self._entries = [
            project for project in self._all_entries
            if (
                (bool(project.is_template()) and self._show_templates)
                or (
                    not bool(project.is_template())
                    and (
                        self._show_retired
                        or str(
                            project.get_info().get("status")
                            or project.get_info().get("s_status")
                            or ""
                        ).lower() != "retired"
                    )
                )
            )
        ]
        self.endResetModel()
        self.filter_changed.emit()

    @Property(bool, notify=filter_changed)
    def showRetired(self) -> bool:
        return self._show_retired

    @Slot(bool)
    def setShowRetired(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if self._show_retired == enabled:
            return
        self._show_retired = enabled
        self._apply_filter()

    @Property(bool, notify=filter_changed)
    def showTemplates(self) -> bool:
        return self._show_templates

    @Slot(bool)
    def setShowTemplates(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if self._show_templates == enabled:
            return
        self._show_templates = enabled
        self._apply_filter()

    @Property(int, notify=filter_changed)
    def totalCount(self) -> int:
        return len(self._all_entries)

    @Property(int, notify=filter_changed)
    def visibleCount(self) -> int:
        return len(self._entries)

    @Property(int, notify=filter_changed)
    def retiredCount(self) -> int:
        return sum(self.values(project)["isRetired"] for project in self._all_entries)

    @Property(int, notify=filter_changed)
    def templateCount(self) -> int:
        return sum(bool(project.is_template()) for project in self._all_entries)

    @Property("QVariantList", notify=filter_changed)
    def groups(self) -> list[dict]:
        grouped: dict[str, list[dict]] = {}
        for project in self._entries:
            values = self.values(project)
            category = values["category"] or "No Category"
            grouped.setdefault(category, []).append({
                **values,
                "initials": "".join(
                    word[0]
                    for word in values["title"].replace("_", " ").split()[:2]
                ).upper(),
            })
        return [
            {"title": title, "projects": projects}
            for title, projects in grouped.items()
        ]

    @staticmethod
    def _safe_int(value) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def preview_count(project) -> int:
        return sum(
            len(context.versionless or {}) + len(context.versions or {})
            for process in (project.get_all_processes() or {}).values()
            for context in process.get_contexts().values()
        )

    def preview_for(self, project) -> str:
        code = project.get_code()
        if code in self._preview_cache:
            self._preview_cache.move_to_end(code)
            return self._preview_cache[code]
        preview_url = ""
        for process_name in ("icon", "publish"):
            process = project.get_process(process_name)
            if not process:
                continue
            for context in process.get_contexts().values():
                snapshots = context.get_versionless() or context.get_versions()
                if not snapshots:
                    continue
                snapshot = next(iter(snapshots.values()))
                files = snapshot.get_files_objects(group_by="type").get("icon") or []
                if not files:
                    continue
                preview = files[0].get_icon_preview()
                if not preview:
                    continue
                local_path = str(preview.get_full_abs_path() or "")
                if local_path and Path(local_path).is_file():
                    preview_url = QUrl.fromLocalFile(
                        str(Path(local_path).resolve())
                    ).toString()
                elif (
                    local_path
                    and self.repository_sync
                    and self.repository_sync.previews_through_http_enabled()
                ):
                    try:
                        handle = self.repository_sync.schedule_file_object(
                            preview, process="preview", auto_start=True
                        )
                        preview_url = f"pending-preview:{handle.task_id}"
                        self._pending_preview_paths[preview_url] = local_path
                    except (AttributeError, TypeError, ValueError):
                        preview_url = ""
                if preview_url:
                    break
            if preview_url:
                break
        self._store_preview(code, preview_url)
        return preview_url

    def _store_preview(self, code: str, preview_url: str) -> None:
        self._preview_cache[code] = preview_url
        self._preview_cache.move_to_end(code)
        while len(self._preview_cache) > self._preview_cache_limit:
            self._preview_cache.popitem(last=False)

    def localize_preview(self, local_path: str) -> None:
        resolved = str(Path(local_path).resolve())
        ready_url = QUrl.fromLocalFile(resolved).toString()
        changed_codes = []
        for code, value in tuple(self._preview_cache.items()):
            pending_path = self._pending_preview_paths.get(value)
            if pending_path and str(Path(pending_path).resolve()) == resolved:
                self._preview_cache[code] = ready_url
                self._pending_preview_paths.pop(value, None)
                changed_codes.append(code)
                self.preview_ready.emit(code, ready_url)
        for row, project in enumerate(self._entries):
            if project.get_code() in changed_codes:
                index = self.index(row, 0)
                self.dataChanged.emit(index, index, [self.PreviewRole])

    def fail_preview(self, task_id: str) -> None:
        token = f"pending-preview:{task_id}"
        self._pending_preview_paths.pop(token, None)
        for code, value in tuple(self._preview_cache.items()):
            if value == token:
                self._preview_cache[code] = ""

    def values(self, project) -> dict:
        info = project.get_info()
        created = (
            info.get("creation_date")
            or info.get("created")
            or info.get("timestamp")
            or ""
        )
        updated = (
            info.get("last_updated")
            or info.get("updated")
            or info.get("login_timestamp")
            or ""
        )
        status = str(info.get("status") or info.get("s_status") or "")
        return {
            "code": project.get_code(),
            "title": project.get_title() or project.get_code(),
            "category": info.get("category") or "Projects",
            "status": status,
            "preview": self.preview_for(project),
            "isTemplate": bool(project.is_template()),
            "isRetired": status.lower() == "retired",
            "description": str(info.get("description") or ""),
            "created": str(created),
            "updated": str(updated),
            "projectType": str(project.get_type() or ""),
            "lead": str(
                info.get("project_lead")
                or info.get("lead")
                or info.get("login")
                or ""
            ),
            "objectCount": self._safe_int(
                info.get("object_count") or info.get("total_objects")
            ),
            "userCount": self._safe_int(
                info.get("user_count") or info.get("users_count")
            ),
            "previewCount": self.preview_count(project),
        }
