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

from .sidebar_icons import icon_name_from_tactic


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
    search_view: str = ""
    view_mode: str = ""
    layout_preset: str = ""
    script_shelf: str = ""
    filter_records: tuple = ()


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

    def set_script_shelf(self, key: str, view: str) -> bool:
        for row, entry in enumerate(self._entries):
            if entry.key == key:
                self._entries[row] = replace(entry, script_shelf=str(view or ""))
                return True
        return False

    def clear_script_shelf(self, view: str) -> bool:
        changed = False
        for row, entry in enumerate(self._entries):
            if entry.script_shelf == view:
                self._entries[row] = replace(entry, script_shelf="")
                changed = True
        return changed

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
        """Preserve the icon configured by the project's sidebar XML.

        Icon Manager stores a resolved MaterialIcon/Font Awesome name in the
        XML.  The Search Type must not silently replace it with a client-side
        guess.
        """
        del search_type
        return icon_name_from_tactic(server_icon) or "sidebar-link"

    @staticmethod
    def _item_filter_records(project, item, search_type: str) -> tuple:
        search_view_node = item.find("search_view")
        if not search_view_node:
            return ()
        search_view = search_view_node.get_text(strip=True)
        definition = project.get_config_views().get_view(
            search_type,
            search_view,
            bs=True,
        )
        from .search_presets import records_from_definition

        return tuple(records_from_definition(definition))

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
                is_visible = str(item.get("is_visible") or "on").lower()
                if is_visible in {"off", "false", "no", "0"}:
                    continue
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
                filter_records = (
                    cls._item_filter_records(project, item, search_type)
                    if search_type else ()
                )
                search_view_node = item.find("search_view")
                search_view = (
                    search_view_node.get_text(strip=True)
                    if search_view_node else ""
                )
                widget_key_node = (
                    display_node.find("widget_key") if display_node else None
                )
                widget_key = (
                    widget_key_node.get_text(strip=True)
                    if widget_key_node else ""
                )
                view_mode_node = (
                    display_node.find("view_mode") if display_node else None
                )
                view_mode = (
                    view_mode_node.get_text(strip=True)
                    if view_mode_node else ""
                )
                layout_preset_node = (
                    display_node.find("layout_preset")
                    if display_node else None
                )
                layout_preset = (
                    layout_preset_node.get_text(strip=True)
                    if layout_preset_node else ""
                )
                script_shelf_node = (
                    display_node.find("script_shelf")
                    if display_node else None
                )
                script_shelf = (
                    script_shelf_node.get_text(strip=True)
                    if script_shelf_node else ""
                )
                if view_mode not in {
                    "continious", "tiles", "compact",
                    "splitted_vertical", "splitted_horizontal", "table",
                }:
                    view_mode = (
                        "tiles" if widget_key == "tile_layout"
                        else "compact" if widget_key == "fast_layout"
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
                    available=bool(search_type),
                    depth=depth,
                    accent=accent,
                    search_type=search_type,
                    search_view=search_view,
                    view_mode=view_mode,
                    layout_preset=layout_preset,
                    script_shelf=script_shelf,
                    filter_records=filter_records,
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
    DetailsRole = Qt.UserRole + 8
    ProjectTypeRole = Qt.UserRole + 9
    BuiltinRole = Qt.UserRole + 10
    ActiveRole = Qt.UserRole + 11
    SystemStatusRole = Qt.UserRole + 12
    filter_changed = Signal()
    projects_changed = Signal()
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
        self._show_builtins = False

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.CodeRole: b"projectCode", self.TitleRole: b"title",
            self.CategoryRole: b"category", self.StatusRole: b"status",
            self.PreviewRole: b"preview", self.TemplateRole: b"isTemplate",
            self.RetiredRole: b"isRetired", self.DetailsRole: b"projectDetails",
            self.ProjectTypeRole: b"projectType",
            self.BuiltinRole: b"isBuiltin", self.ActiveRole: b"isActive",
            self.SystemStatusRole: b"systemStatus",
        }

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._entries)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._entries):
            return None
        project = self._entries[index.row()]
        if role == self.DetailsRole:
            return self.details(project)
        values = self.values(project)
        return {
            self.CodeRole: values["code"],
            self.TitleRole: values["title"],
            self.CategoryRole: values["category"],
            self.StatusRole: values["status"],
            self.PreviewRole: values["preview"],
            self.TemplateRole: values["isTemplate"],
            self.RetiredRole: values["isRetired"],
            self.ProjectTypeRole: values["projectType"],
            self.BuiltinRole: values["isBuiltin"],
            self.ActiveRole: values["isActive"],
            self.SystemStatusRole: values["systemStatus"],
        }.get(role)

    def replace(self, entries: Iterable[object]) -> None:
        self._all_entries = list(entries)
        self._preview_cache.clear()
        self._pending_preview_paths.clear()
        self._apply_filter()
        self.projects_changed.emit()

    @Property("QVariantList", notify=projects_changed)
    def allProjects(self) -> list[dict]:
        """Unfiltered selector data, without preview discovery or chooser state."""
        return [
            {"projectCode": project.get_code(),
             "title": project.get_title() or project.get_code()}
            for project in self._all_entries
        ]

    def refresh_previews(self) -> None:
        self._preview_cache.clear()
        self._pending_preview_paths.clear()
        if not self._entries:
            return
        first = self.index(0, 0)
        last = self.index(len(self._entries) - 1, 0)
        self.dataChanged.emit(
            first, last, [self.PreviewRole, self.DetailsRole]
        )

    def _apply_filter(self) -> None:
        self.beginResetModel()
        self._entries = [
            project for project in self._all_entries
            if (
                self._is_builtin(project) and self._show_builtins
                or (
                    not self._is_builtin(project)
                    and (
                        (bool(project.is_template()) and self._show_templates)
                        or (
                            not bool(project.is_template())
                            and (
                                self._show_retired
                                or str(
                                    project.get_info().get("s_status") or ""
                                ).lower() != "retired"
                            )
                        )
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
    @Property(bool, notify=filter_changed)
    def showBuiltins(self) -> bool:
        return self._show_builtins

    @Slot(bool)
    def setShowBuiltins(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if self._show_builtins == enabled:
            return
        self._show_builtins = enabled
        self._apply_filter()


    @Property(int, notify=filter_changed)
    def totalCount(self) -> int:
        return len(self._all_entries)

    @Property(int, notify=filter_changed)
    def visibleCount(self) -> int:
        return len(self._entries)

    @Property(int, notify=filter_changed)
    def retiredCount(self) -> int:
        return sum(
            str(project.get_info().get("s_status") or "").lower() == "retired"
            for project in self._all_entries
        )

    @Property(int, notify=filter_changed)
    def templateCount(self) -> int:
        return sum(bool(project.is_template()) for project in self._all_entries)

    @Property(int, notify=filter_changed)
    def builtinCount(self) -> int:
        return sum(self._is_builtin(project) for project in self._all_entries)

    def details(self, project) -> dict:
        values = self.values(project)
        return {
            **values,
            "initials": "".join(
                word[0]
                for word in values["title"].replace("_", " ").split()[:2]
            ).upper(),
        }

    @Property("QVariantList", notify=filter_changed)
    def groups(self) -> list[dict]:
        grouped: dict[str, list[dict]] = {}
        for project in self._entries:
            values = self.details(project)
            category = values["category"] or "No Category"
            grouped.setdefault(category, []).append(values)
        return [
            {"title": title, "projects": projects}
            for title, projects in grouped.items()
        ]

    @staticmethod
    def _is_builtin(project) -> bool:
        try:
            return bool(project.is_builtin())
        except AttributeError:
            return bool(project.get_info().get("__builtin__"))

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
        path_resolution_pending = False
        for process_name in ("icon", "publish"):
            process = project.get_process(process_name)
            if not process:
                continue
            for context in process.get_contexts().values():
                snapshots = context.get_versionless() or context.get_versions()
                if not snapshots:
                    continue
                snapshot = next(iter(snapshots.values()))
                try:
                    grouped = snapshot.get_files_objects(group_by="type") or {}
                except (AttributeError, KeyError, TypeError):
                    grouped = {}
                try:
                    previewable = list(
                        snapshot.get_previewable_files_objects() or []
                    )
                except (AttributeError, KeyError, TypeError):
                    previewable = []
                files = (
                    previewable
                    or list(grouped.get("web") or [])
                    or list(grouped.get("image") or [])
                    or list(grouped.get("icon") or [])
                )
                if not files:
                    continue
                source_file = files[0]
                try:
                    preview = source_file.get_web_preview()
                except (AttributeError, KeyError, TypeError):
                    preview = None
                if not preview:
                    try:
                        preview = source_file.get_icon_preview() or source_file
                    except (AttributeError, KeyError, TypeError):
                        preview = source_file
                if not preview:
                    continue
                try:
                    local_path = str(preview.get_full_abs_path() or "")
                except (AttributeError, KeyError, TypeError, ValueError):
                    # ProjectModel is populated before repository configuration
                    # during the fast startup path. File owns path resolution, so
                    # defer instead of reconstructing its path or caching a miss.
                    path_resolution_pending = True
                    continue
                if local_path and preview.is_local_current():
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
                            preview, process="preview", auto_start=True,
                            is_ui_preview=True,
                        )
                        preview_url = f"pending-preview:{handle.task_id}"
                        self._pending_preview_paths[preview_url] = local_path
                    except (AttributeError, TypeError, ValueError):
                        preview_url = ""
                if preview_url:
                    break
            if preview_url:
                break
        if path_resolution_pending and not preview_url:
            return ""
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
                self.dataChanged.emit(
                    index, index, [self.PreviewRole, self.DetailsRole]
                )

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
        status = str(info.get("status") or "")
        system_status = str(info.get("s_status") or "")
        is_retired = system_status.lower() == "retired"
        is_builtin = self._is_builtin(project)
        is_template = bool(project.is_template())
        return {
            "code": project.get_code(),
            "title": project.get_title() or project.get_code(),
            "category": str(info.get("category") or ""),
            "status": status,
            "systemStatus": system_status,
            "preview": self.preview_for(project),
            "isTemplate": is_template,
            "isRetired": is_retired,
            "isBuiltin": is_builtin,
            "isActive": not is_retired and not is_template,
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
