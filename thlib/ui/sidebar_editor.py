"""QML editor for the project ``SideBarWdg`` widget configuration."""

from __future__ import annotations

from copy import deepcopy
import re
import traceback
from xml.etree import ElementTree

from PySide6.QtCore import QCoreApplication, QObject, Property, QSortFilterProxyModel, Signal, Slot

from .sidebar_icons import icon_name_for_tactic
from .sidebar_search import SidebarSearchMixin
from .script_shelf import SCRIPT_SHELF_CATEGORY
from .workspace_models.records import RecordListModel
from .workspace_layout_presets import WORKSPACE_LAYOUT_CATEGORY


_LINK_CLASS = "LinkWdg"
_SECTION_CLASS = "SideBarSectionLinkWdg"
_SEPARATOR_CLASS = "SeparatorWdg"

_WIDGET_TYPE_VALUES = {
    "view_panel", "custom_layout", "edit_layout", "tile_layout",
    "fast_layout", "__class__",
}
_RESULT_VIEW_VALUES = {
    "continious", "tiles", "compact", "splitted_vertical",
    "splitted_horizontal", "table",
}


def _slug(value: object, fallback: str = "sidebar_item") -> str:
    value = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower())
    return value.strip("_") or fallback


def _children(root: ElementTree.Element) -> list[ElementTree.Element]:
    if root.tag == "element":
        return [root]
    return [child for child in list(root) if child.tag == "element"]


def _all_elements(root: ElementTree.Element) -> list[ElementTree.Element]:
    """Match ``ViewsConfig.get_view``: every element belongs to the view."""
    if root.tag == "element":
        return [root]
    return list(root.iter("element"))


def _view_elements(root: ElementTree.Element) -> list[ElementTree.Element]:
    """Return only the ordered elements owned by one SideBarWdg view.

    TACTIC stores a folder's children in another named SideBarWdg view.  Using
    ``iter('element')`` here destroys that boundary and turns the native tree
    into a flat catalog.  Configs may have a ``config/view`` wrapper, so locate
    the first container which directly owns elements and keep only its direct
    children.
    """
    if root.tag == "element":
        return [root]
    direct = [child for child in list(root) if child.tag == "element"]
    if direct:
        return direct
    for container in root.iter():
        direct = [child for child in list(container) if child.tag == "element"]
        if direct:
            return direct
    return []


def _nested_elements(element: ElementTree.Element) -> list[ElementTree.Element]:
    """Return inline children when a definition uses nested element nodes."""
    return [child for child in list(element) if child.tag == "element"]


def _element_parent(
        root: ElementTree.Element,
        element: ElementTree.Element) -> ElementTree.Element | None:
    for parent in root.iter():
        if element in list(parent):
            return parent
    return None


def _element_container(root: ElementTree.Element) -> ElementTree.Element:
    """Append beside existing view references, preserving wrapper elements."""
    elements = _view_elements(root)
    if elements:
        parent = _element_parent(root, elements[0])
        return parent if parent is not None else root
    return root


def _parse_document(value: object) -> ElementTree.Element:
    text = str(value or "").strip()
    if not text:
        return ElementTree.Element("config")
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError:
        root = ElementTree.fromstring(f"<config>{text}</config>")
    if root.tag == "element":
        wrapper = ElementTree.Element("config")
        wrapper.append(root)
        return wrapper
    return root


def _serialize(root: ElementTree.Element) -> str:
    try:
        ElementTree.indent(root, space="  ")
    except AttributeError:
        pass
    return ElementTree.tostring(root, encoding="unicode")


def _serialize_element(element: ElementTree.Element) -> str:
    """Serialize one effective sidebar definition without mutating it."""
    return _serialize(deepcopy(element))


def _parse_element(value: object) -> ElementTree.Element:
    element = ElementTree.fromstring(str(value or "").strip())
    if element.tag != "element":
        raise ElementTree.ParseError("The root node must be <element>")
    return element


def _security_document(value: object) -> ElementTree.Element:
    """Parse a complete TACTIC access_rules value or one rule fragment."""
    text = str(value or "").strip()
    if not text:
        return ElementTree.Element("rules")
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError:
        root = ElementTree.fromstring(f"<rules>{text}</rules>")
    if root.tag == "rule":
        wrapper = ElementTree.Element("rules")
        wrapper.append(root)
        return wrapper
    return root


def _sidebar_rule_allowed(
        access_rules: object, element_name: str, project_code: str) -> bool:
    """Return the explicit project link permission used by check_security."""
    try:
        root = _security_document(access_rules)
    except ElementTree.ParseError:
        return False
    for rule in root.iter("rule"):
        if (
            str(rule.get("group") or "") == "link"
            and str(rule.get("element") or "") == str(element_name or "")
            and str(rule.get("project") or "") == str(project_code or "")
        ):
            return str(rule.get("access") or "").lower() == "allow"
    return False


def _direct_text(element: ElementTree.Element, name: str) -> str:
    node = element.find(f"./{name}")
    if node is None:
        node = element.find(f"./display/{name}")
    return str(node.text or "").strip() if node is not None else ""


def _set_direct_text(
        element: ElementTree.Element, name: str, value: object) -> None:
    text = str(value or "").strip()
    node = element.find(f"./{name}")
    parent = element
    if node is None:
        node = element.find(f"./display/{name}")
        if node is not None:
            display_parent = element.find("./display")
            parent = display_parent if display_parent is not None else element
    if not text:
        if node is not None:
            parent.remove(node)
        return
    if node is None:
        display = element.find("./display")
        if display is None:
            display = ElementTree.SubElement(element, "display")
            display.set("class", _LINK_CLASS)
        node = ElementTree.SubElement(display, name)
    node.text = text


def _display_class(element: ElementTree.Element) -> str:
    display = element.find("./display")
    return str(display.get("class") or _LINK_CLASS) if display is not None else _LINK_CLASS


def _set_display_class(element: ElementTree.Element, value: str) -> None:
    display = element.find("./display")
    if display is None:
        display = ElementTree.SubElement(element, "display")
    display.set("class", value)


def _display_option(element: ElementTree.Element, name: str) -> str:
    node = element.find(f"./display/{name}")
    return str(node.text or "").strip() if node is not None else ""


def _set_display_option(
        element: ElementTree.Element, name: str, value: object) -> None:
    display = element.find("./display")
    text = str(value or "").strip()
    node = display.find(f"./{name}") if display is not None else None
    if not text:
        if display is not None and node is not None:
            display.remove(node)
        return
    if display is None:
        display = ElementTree.SubElement(element, "display")
        display.set("class", _LINK_CLASS)
    if node is None:
        node = ElementTree.SubElement(display, name)
    node.text = text


def _widget_type(element: ElementTree.Element) -> str:
    if element.find("./display/class_name") is not None:
        return "__class__"
    value = _display_option(element, "widget_key")
    return value if value in _WIDGET_TYPE_VALUES else "view_panel"


def _result_view_mode(element: ElementTree.Element) -> str:
    value = _display_option(element, "view_mode")
    if value in _RESULT_VIEW_VALUES:
        return value
    widget_type = _widget_type(element)
    if widget_type == "tile_layout":
        return "tiles"
    if widget_type == "fast_layout":
        return "compact"
    return "continious"


class SidebarEditorController(SidebarSearchMixin, QObject):
    """Edit the same sidebar XML consumed by the server configuration and the application UI."""

    stateChanged = Signal()
    groupManagementRequested = Signal()

    _entry_roles = (
        "key", "name", "title", "entryType", "icon", "searchType",
        "searchView", "targetView", "ownerView", "depth", "displayDepth",
        "selected", "glyph", "accent", "included", "expanded", "entryVisible",
        "hasChildren", "handlerBranch", "isVisible", "widgetType",
        "displayView", "displayClassName", "resultViewMode",
        "layoutPreset", "scriptShelf",
    )

    _security_roles = (
        "code", "groupName", "label", "allowed", "changed",
    )

    def __init__(
        self, application, users, parent=None, *, layout_presets=None,
    ) -> None:
        super().__init__(parent)
        self._application = application
        self._users = users
        self._layout_presets = layout_presets
        self._script_shelf = None
        self.entries = RecordListModel(self._entry_roles)
        self.security_groups = RecordListModel(self._security_roles)
        self._search_preset_options: list[dict] = []
        self._search_preset_context: tuple[str, str] = ("", "")
        self._search_preset_request = ""
        self._search_preset_worker = None
        self._documents: dict[str, ElementTree.Element] = {}
        self._records: dict[str, dict] = {}
        self._original_xml: dict[str, str] = {}
        self._flat_refs: list[
            tuple[str, ElementTree.Element | None, ElementTree.Element]
        ] = []
        self._security_pending: dict[tuple[str, str], bool] = {}
        self._security_objects: dict[str, object] = {}
        self._collapsed_folders: set[str] = set()
        self._handler_only = False
        self._selected_row = -1
        self._root_view = "tactic_handler"
        self._xml_view = ""
        self._xml_text = ""
        self._mode = "simple"
        self._busy = False
        self._error = ""
        self._project_code = ""
        self._project_title = ""
        self._project = None
        self._workers = set()
        self._filter_editor = None
        self._pending_search_open: tuple[str, str] | None = None
        self._preview_context: tuple[str, str] | None = None
        self._preview_return_section = ""
        self._preview_surfaces = QSortFilterProxyModel(self)
        if hasattr(application, "search_state_changed"):
            application.search_state_changed.connect(self._finish_search_open)
        if hasattr(application, "project_changed"):
            application.project_changed.connect(self._finish_search_open)
        windows = getattr(application, "window_model", None)
        if windows is not None:
            windows.windowVisibilityChanged.connect(self._window_visibility_changed)
        try:
            users.stateChanged.connect(self.stateChanged.emit)
        except (AttributeError, TypeError):
            pass
        self._application._registry.register("show_sidebar_editor", self.open)

    def attach_filter_editor(self, controller) -> None:
        self._filter_editor = controller

    def attach_script_shelf(self, controller) -> None:
        self._script_shelf = controller
        controller.stateChanged.connect(self.stateChanged.emit)

    @Property(QObject, constant=True)
    def scriptShelf(self):
        return self._script_shelf

    @Property(QObject, constant=True)
    def previewSurfaces(self):
        return self._preview_surfaces

    @Property(QObject, constant=True)
    def layoutPresets(self):
        return self._layout_presets

    @Property(bool, notify=stateChanged)
    def canEdit(self) -> bool:
        try:
            return bool(self._users.canManageUsers)
        except (AttributeError, RuntimeError):
            return False

    @Property(bool, notify=stateChanged)
    def canManageGroups(self) -> bool:
        return self._application.can_administer

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(bool, notify=stateChanged)
    def canOpenSearch(self) -> bool:
        selected = self.selectedEntry
        return bool(
            self.canEdit and not self.busy and not self.dirty
            and selected.get("entryType") == "link"
            and selected.get("searchType") and selected.get("name")
        )

    @Property(bool, notify=stateChanged)
    def dirty(self) -> bool:
        return any(
            _serialize(document) != self._original_xml.get(view, "")
            for view, document in self._documents.items()
        ) or any(view not in self._records for view in self._documents) or bool(
            self._security_pending
        )

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error

    @Property(str, notify=stateChanged)
    def mode(self) -> str:
        return self._mode

    @Property(bool, notify=stateChanged)
    def handlerOnly(self) -> bool:
        return self._handler_only

    @Property(str, notify=stateChanged)
    def projectTitle(self) -> str:
        return self._project_title

    @Property(int, notify=stateChanged)
    def selectedRow(self) -> int:
        return self._selected_row

    @Property("QVariantMap", notify=stateChanged)
    def selectedEntry(self) -> dict:
        if not 0 <= self._selected_row < len(self._flat_refs):
            return {}
        return dict(self.entries._records[self._selected_row])

    @Property(int, notify=stateChanged)
    def securityGroupCount(self) -> int:
        return len(self.security_groups._records)

    @Property("QVariantList", notify=stateChanged)
    def searchTypes(self) -> list[dict]:
        values = []
        try:
            stypes = (self._project.get_stypes() or {}).values()
            values = [
                {
                    "value": str(stype.get_code() or ""),
                    "label": str(stype.get_pretty_name() or stype.get_code() or ""),
                }
                for stype in stypes if stype.get_code()
            ]
        except (AttributeError, TypeError):
            pass
        values.sort(key=lambda item: item["label"].lower())
        return [{
            "value": "",
            "label": QCoreApplication.translate(
                "TacticHandler", "Select Search Type"
            ),
        }, *values]

    @Property("QVariantList", notify=stateChanged)
    def searchPresetOptions(self) -> list[dict]:
        return [dict(option) for option in self._search_preset_options]

    @Property(bool, notify=stateChanged)
    def searchPresetsBusy(self) -> bool:
        return self._search_preset_worker is not None

    @Property("QVariantList", notify=stateChanged)
    def viewOptions(self) -> list[dict]:
        return [
            {"value": name, "label": name}
            for name in sorted(self._documents)
        ]

    @Property("QVariantList", constant=True)
    def widgetTypeOptions(self) -> list[dict]:
        translate = lambda value: QCoreApplication.translate("TacticHandler", value)
        return [
            {"value": "view_panel", "label": translate("Layout with Search"),
             "icon": "search"},
            {"value": "custom_layout", "label": translate("Custom Layout"),
             "icon": "dashboard_customize"},
            {"value": "edit_layout", "label": translate("Edit Layout"),
             "icon": "edit"},
            {"value": "tile_layout", "label": translate("Tile Layout"),
             "icon": "grid_view"},
            {"value": "fast_layout", "label": translate("Fast Table Layout"),
             "icon": "view_list"},
            {"value": "__class__", "label": translate("Class Path"),
             "icon": "code"},
        ]

    @Property("QVariantList", constant=True)
    def resultViewOptions(self) -> list[dict]:
        translate = lambda value: QCoreApplication.translate("TacticHandler", value)
        return [
            {"value": "continious", "label": translate("Continuous tree"),
             "icon": "account_tree"},
            {"value": "tiles", "label": translate("Cards"),
             "icon": "grid_view"},
            {"value": "table", "label": translate("Table"),
             "icon": "table"},
            {"value": "compact", "label": translate("Compact rows"),
             "icon": "view_list"},
            {"value": "splitted_vertical",
             "label": translate("Versions on the right"),
             "icon": "view-column"},
            {"value": "splitted_horizontal",
             "label": translate("Versions at the bottom"),
             "icon": "view-agenda"},
        ]

    @Property(str, notify=stateChanged)
    def xmlView(self) -> str:
        return self._xml_view

    @Property(str, notify=stateChanged)
    def xmlText(self) -> str:
        return self._xml_text

    @Slot()
    def open(self) -> None:
        if not self.canEdit:
            self._application._notify("Sidebar editing requires supervisor access")
            return
        self._application.window_model.show_window("sidebar_editor")

    @Slot()
    def begin_session(self) -> None:
        if not self.canEdit:
            return
        self._pending_search_open = None
        self._handler_only = True
        self.reload()

    @Slot()
    def open_group_manager(self) -> None:
        if self.canManageGroups:
            self.groupManagementRequested.emit()
            self._application.window_model.show_child_window("administration", "sidebar_editor")

    @Slot()
    def refresh_security_groups(self) -> None:
        login = self._current_login_object()
        groups = login.get_all_login_groups() if login is not None else []
        self._security_objects = {
            str(group.get_code()): group for group in groups or []
        }
        self._rebuild_security_groups()
        self.stateChanged.emit()

    @Slot(str, bool)
    def _window_visibility_changed(self, window_id: str, visible: bool) -> None:
        if window_id == "sidebar_editor" and visible:
            self.begin_session()
        elif window_id == "sidebar_search_preview" and not visible:
            self._close_search_preview()

    @Slot()
    def reload(self) -> None:
        if self._busy or not self.canEdit:
            return
        try:
            from thlib.environment import env_inst
            project_code = str(self._application.current_project_code or "")
            project = (env_inst.projects or {}).get(project_code)
        except (AttributeError, ImportError):
            project_code, project = "", None
        if not project_code or project is None:
            self._set_busy(False, "Select a project before editing its sidebar")
            return

        def operation():
            views = project.get_config_views()
            records = [
                deepcopy(record) for record in (views.config_dict or [])
                if str(record.get("search_type") or "") == "SideBarWdg"
                and str(record.get("category") or "") not in {
                    WORKSPACE_LAYOUT_CATEGORY, SCRIPT_SHELF_CATEGORY,
                }
            ]
            if not records:
                import thlib.tactic_classes as tc
                records = tc.server_start(project=project_code).query(
                    "config/widget_config",
                    [("search_type", "SideBarWdg")],
                ) or []
                records = [
                    record for record in records
                    if str(record.get("category") or "") not in {
                        WORKSPACE_LAYOUT_CATEGORY, SCRIPT_SHELF_CATEGORY,
                    }
                ]
            return project_code, self._application.current_project_title, project, records

        self._run(operation, self._loaded)

    @Slot(str)
    def set_mode(self, value: str) -> None:
        value = str(value or "simple")
        if value not in {"simple", "xml"} or value == self._mode:
            return
        if self._mode == "xml" and value == "simple":
            if not self._apply_xml_text():
                return
        elif self._mode == "simple" and value == "xml":
            self._sync_xml_text()
        self._mode = value
        self.stateChanged.emit()

    @Slot(bool)
    def set_handler_only(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled == self._handler_only:
            return
        selected_id = None
        if 0 <= self._selected_row < len(self._flat_refs):
            selector = self._flat_refs[self._selected_row][1]
            element = self._flat_refs[self._selected_row][2]
            selected_id = id(selector if selector is not None else element)
        self._handler_only = enabled
        self._rebuild_entries(selected_element_id=selected_id)

    @Slot(int)
    def select_entry(self, row: int) -> None:
        if not 0 <= row < len(self._flat_refs):
            return
        self._selected_row = row
        self._xml_view = self._flat_refs[row][0]
        self._sync_xml_text()
        self._rebuild_entries()


    def _accent_for_search_type(self, search_type: str) -> str:
        entries_for_search_type = getattr(
            self._application.navigation_model,
            "entries_for_search_type",
            None,
        )
        if not callable(entries_for_search_type) or not search_type:
            return ""
        return next((
            entry.accent
            for entry in entries_for_search_type(search_type)
            if entry.accent
        ), "")

    @Slot(int)
    def activate_entry(self, row: int) -> None:
        if not 0 <= row < len(self._flat_refs):
            return
        owner, selector, element = self._flat_refs[row]
        record = self.entries._records[row]
        self._selected_row = row
        self._xml_view = owner
        if record.get("entryType") == "section" and record.get("hasChildren"):
            key = str(record.get("key") or "")
            if key in self._collapsed_folders:
                self._collapsed_folders.remove(key)
            else:
                self._collapsed_folders.add(key)
        self._sync_xml_text()
        self._rebuild_entries(
            selected_element_id=id(selector if selector is not None else element)
        )

    @Slot(int)
    def toggle_folder(self, row: int) -> None:
        if not 0 <= row < len(self._flat_refs):
            return
        record = self.entries._records[row]
        if record.get("entryType") != "section":
            return
        key = str(record.get("key") or "")
        if key in self._collapsed_folders:
            self._collapsed_folders.remove(key)
        else:
            self._collapsed_folders.add(key)
        selected_id = None
        if 0 <= self._selected_row < len(self._flat_refs):
            selector = self._flat_refs[self._selected_row][1]
            element = self._flat_refs[self._selected_row][2]
            selected_id = id(selector if selector is not None else element)
        self._rebuild_entries(selected_element_id=selected_id)

    @Slot(str, bool)
    def set_group_allowed(self, group_code: str, allowed: bool) -> None:
        if not self.canEdit or not 0 <= self._selected_row < len(self._flat_refs):
            return
        element = self._flat_refs[self._selected_row][2]
        element_name = str(element.get("name") or "")
        group_code = str(group_code or "")
        group = self._security_objects.get(group_code)
        if not element_name or group is None:
            return
        base = self._group_rule_allowed(group, element_name)
        key = (element_name, group_code)
        if bool(allowed) == base:
            self._security_pending.pop(key, None)
        else:
            self._security_pending[key] = bool(allowed)
        self._rebuild_security_groups()
        self.stateChanged.emit()

    @Slot(bool)
    def set_selected_in_sidebar(self, included: bool) -> None:
        if not self.canEdit or not 0 <= self._selected_row < len(self._flat_refs):
            return
        owner, selector, element = self._flat_refs[self._selected_row]
        if bool(included) == (selector is not None):
            return
        if included:
            root = self._documents.setdefault(
                self._root_view, ElementTree.Element("config")
            )
            selector = ElementTree.SubElement(
                _element_container(root), "element",
                {"name": str(element.get("name") or "")},
            )
            self._rebuild_entries(selected_element_id=id(selector))
            return
        root = self._documents.get(owner)
        parent = _element_parent(root, selector) if root is not None else None
        if parent is not None and selector is not None:
            parent.remove(selector)
        self._rebuild_entries(selected_element_id=id(element))

    @Slot(str)
    def set_xml_view(self, view: str) -> None:
        view = str(view or "")
        if view not in self._documents:
            return
        self._xml_view = view
        self._sync_xml_text()
        self.stateChanged.emit()

    @Slot(str)
    def set_xml_text(self, value: str) -> None:
        self._xml_text = str(value or "")
        self.stateChanged.emit()

    @Slot()
    def apply_xml(self) -> None:
        self._apply_xml_text()

    def _apply_xml_text(self) -> bool:
        if not self.canEdit or not 0 <= self._selected_row < len(self._flat_refs):
            return False
        try:
            replacement = _parse_element(self._xml_text)
        except ElementTree.ParseError as error:
            self._error = f"Invalid sidebar XML: {error}"
            self.stateChanged.emit()
            return False
        owner, selector, element = self._flat_refs[self._selected_row]
        containing_root = None
        parent = None
        for document in self._documents.values():
            candidate = _element_parent(document, element)
            if candidate is not None:
                containing_root = document
                parent = candidate
                break
        if containing_root is None or parent is None:
            self._error = "Selected sidebar element no longer exists"
            self.stateChanged.emit()
            return False
        previous_name = str(element.get("name") or "")
        replacement_name = str(replacement.get("name") or "").strip()
        if not replacement_name:
            self._error = "Sidebar element name is required"
            self.stateChanged.emit()
            return False
        index = list(parent).index(element)
        parent.remove(element)
        parent.insert(index, replacement)
        if replacement_name != previous_name:
            for view, document in self._documents.items():
                if document is containing_root:
                    continue
                for reference in _all_elements(document):
                    if str(reference.get("name") or "") == previous_name:
                        reference.set("name", replacement_name)
            if selector is not None and selector is not element:
                selector.set("name", replacement_name)
        self._error = ""
        selected_id = (
            id(selector) if selector is not None and selector is not element
            else id(replacement)
        )
        self._rebuild_entries(selected_element_id=selected_id)
        return True

    @Slot(str, "QVariant")
    def update_selected(self, field: str, value) -> None:
        if not self.canEdit or not 0 <= self._selected_row < len(self._flat_refs):
            return
        _view, selector, element = self._flat_refs[self._selected_row]
        field = str(field or "")
        text = str(value or "")
        if field in {"name", "title", "icon"}:
            if field == "name":
                previous = str(element.get("name") or "")
                text = _slug(text)
            elif field == "icon":
                text = icon_name_for_tactic(text)
            if text:
                element.set(field, text)
            else:
                element.attrib.pop(field, None)
            if field == "name" and text != previous:
                for group_code, group in self._security_objects.items():
                    old_allowed = self._group_rule_allowed(group, previous)
                    self._security_pending[(previous, group_code)] = False
                    if old_allowed:
                        self._security_pending[(text, group_code)] = True
                for view, document in self._documents.items():
                    if view == "definition":
                        continue
                    for reference in _all_elements(document):
                        if str(reference.get("name") or "") == previous:
                            reference.set("name", text)
                if selector is not None:
                    selector.set("name", text)
        elif field == "entryType":
            classes = {
                "link": _LINK_CLASS,
                "section": _SECTION_CLASS,
                "separator": _SEPARATOR_CLASS,
            }
            if text not in classes:
                return
            _set_display_class(element, classes[text])
            if text != "link":
                _set_direct_text(element, "search_type", "")
                _set_direct_text(element, "search_view", "")
            if text != "section":
                _set_direct_text(element, "view", "")
        elif field == "searchType":
            _set_direct_text(element, "search_type", text)
        elif field == "searchView":
            _set_direct_text(element, "search_view", text)
        elif field == "targetView":
            _set_direct_text(element, "view", _slug(text, "sidebar_section"))
        elif field == "isVisible":
            element.set("is_visible", "on" if bool(value) else "off")
        elif field == "widgetType":
            if text not in _WIDGET_TYPE_VALUES:
                return
            _set_display_class(element, _LINK_CLASS)
            _set_display_option(element, "widget_key", "")
            _set_display_option(element, "class_name", "")
            if text == "__class__":
                display = element.find("./display")
                if display is None:
                    display = ElementTree.SubElement(element, "display")
                    display.set("class", _LINK_CLASS)
                ElementTree.SubElement(display, "class_name")
            else:
                _set_display_option(element, "widget_key", text)
        elif field == "displayView":
            _set_display_option(element, "view", text)
        elif field == "displayClassName":
            _set_display_option(element, "widget_key", "")
            _set_display_option(element, "class_name", text)
        elif field == "resultViewMode":
            if text not in _RESULT_VIEW_VALUES:
                return
            _set_display_option(element, "view_mode", text)
        elif field == "layoutPreset":
            _set_display_option(element, "layout_preset", text)
        elif field == "scriptShelf":
            _set_display_option(element, "script_shelf", text)
        else:
            return
        self._error = ""
        selected_key = id(selector if selector is not None else element)
        self._rebuild_entries(selected_element_id=selected_key)

    @Slot(str)
    def add_entry(self, entry_type: str) -> None:
        if not self.canEdit:
            return
        entry_type = str(entry_type or "link")
        owner = self._root_view
        if 0 <= self._selected_row < len(self._flat_refs):
            owner, _selector, selected = self._flat_refs[self._selected_row]
            if _display_class(selected) == _SECTION_CLASS:
                owner = _direct_text(selected, "view") or owner
        if owner not in self._documents:
            self._documents[owner] = ElementTree.Element("config")
        if "definition" not in self._documents:
            self._documents["definition"] = ElementTree.Element("config")
        definition_root = self._documents["definition"]
        definition_names = {
            str(item.get("name") or "")
            for item in _all_elements(definition_root)
        }
        number = len(definition_names) + 1
        name = f"sidebar_item_{number}"
        while name in definition_names:
            number += 1
            name = f"sidebar_item_{number}"
        element = ElementTree.SubElement(
            _element_container(definition_root),
            "element",
            {
                "name": name,
                "title": "New sidebar item",
                "icon": icon_name_for_tactic("link"),
            },
        )
        if entry_type == "section":
            element.set("title", "New section")
            element.set("icon", icon_name_for_tactic("folder"))
            _set_display_class(element, _SECTION_CLASS)
            view_name = self._unique_view_name("sidebar_section")
            _set_direct_text(element, "view", view_name)
            self._documents[view_name] = ElementTree.Element("config")
        elif entry_type == "separator":
            element.attrib.update({"title": "", "icon": ""})
            _set_display_class(element, _SEPARATOR_CLASS)
        else:
            _set_display_class(element, _LINK_CLASS)
            _set_direct_text(element, "search_type", "")
        selector = element if owner == "definition" else ElementTree.SubElement(
            _element_container(self._documents[owner]),
            "element",
            {"name": name},
        )
        self._rebuild_entries(selected_element_id=id(selector))

    @Slot()
    def delete_selected(self) -> None:
        if not self.canEdit or not 0 <= self._selected_row < len(self._flat_refs):
            return
        owner, selector, _element = self._flat_refs[self._selected_row]
        if selector is None:
            return
        root = self._documents.get(owner)
        if root is None:
            return
        parent = _element_parent(root, selector)
        if parent is not None:
            parent.remove(selector)
        self._selected_row = -1
        self._rebuild_entries()

    @Slot(int)
    def move_selected(self, offset: int) -> None:
        if not self.canEdit or not 0 <= self._selected_row < len(self._flat_refs):
            return
        owner, selector, _element = self._flat_refs[self._selected_row]
        if selector is None:
            return
        root = self._documents.get(owner)
        if root is None:
            return
        parent = _element_parent(root, selector)
        if parent is None:
            return
        items = [item for item in list(parent) if item.tag == "element"]
        try:
            row = items.index(selector)
        except ValueError:
            return
        target = row + (-1 if offset < 0 else 1)
        if not 0 <= target < len(items):
            return
        target_element = items[target]
        target_index = list(parent).index(target_element)
        parent.remove(selector)
        parent.insert(target_index, selector)
        self._rebuild_entries(selected_element_id=id(selector))

    @Slot()
    def discard(self) -> None:
        self._documents = {
            view: _parse_document(value)
            for view, value in self._original_xml.items()
        }
        self._selected_row = -1
        self._security_pending.clear()
        self._error = ""
        self._rebuild_entries()

    @Slot()
    def save(self) -> None:
        if not self.canEdit or self._busy or not self._project_code:
            return
        documents = {view: _serialize(root) for view, root in self._documents.items()}
        records = deepcopy(self._records)
        project_code = self._project_code
        project = self._project
        security_updates = [
            {
                "element": element_name,
                "group_code": group_code,
                "allowed": allowed,
            }
            for (element_name, group_code), allowed
            in sorted(self._security_pending.items())
        ]

        def operation():
            import thlib.tactic_classes as tc
            server = tc.server_start(project=project_code)
            saved = []
            for view, config in documents.items():
                current = records.get(view, {})
                data = {
                    "search_type": "SideBarWdg",
                    "view": view,
                    "title": str(current.get("title") or view.replace("_", " ").title()),
                    "config": config,
                    "login": str(current.get("login") or ""),
                }
                if current.get("category"):
                    data["category"] = current["category"]
                if current.get("code"):
                    search_key = server.build_search_key(
                        "config/widget_config", current["code"],
                        project_code=project_code,
                    )
                    server.insert_update(search_key, data, triggers=False)
                    saved_record = {**current, **data}
                else:
                    created = server.insert(
                        "config/widget_config", data, triggers=False
                    ) or {}
                    saved_record = {**data, **created}
                saved.append(saved_record)
            security_result = (
                tc.mutate_sidebar_security(project_code, security_updates)
                if security_updates else {}
            )
            return documents, saved, project, security_result

        self._run(operation, self._saved)

    def _unique_view_name(self, prefix: str) -> str:
        index = 1
        while True:
            name = f"{prefix}_{index}"
            if name not in self._documents:
                return name
            index += 1

    def _set_busy(self, value: bool, error: str = "") -> None:
        self._busy = bool(value)
        self._error = str(error or "")
        self.stateChanged.emit()

    def _run(self, callback, handler) -> None:
        try:
            from thlib.environment import env_inst
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            worker = env_inst.server_pool.add_task(callback)
            self._workers.add(worker)
            worker.result.connect(handler)
            worker.error.connect(self._failed)
            worker.finished.connect(lambda: self._workers.discard(worker))
            worker.start()
            self._set_busy(True)
        except Exception as error:
            self._set_busy(False, str(error))

    @Slot(object)
    def _loaded(self, payload) -> None:
        project_code, title, project, records = payload
        self._project_code = project_code
        self._project_title = str(title or project_code)
        self._project = project
        self._security_pending.clear()
        self._security_objects = {}
        login = self._current_login_object()
        try:
            groups = login.get_all_login_groups() or []
        except AttributeError:
            groups = []
        for group in groups:
            try:
                code = str(group.get_code() or group.get_login_group() or "")
            except AttributeError:
                continue
            if code:
                self._security_objects[code] = group
        self._records = {}
        for record in records:
            if (
                str(record.get("category") or "")
                in {WORKSPACE_LAYOUT_CATEGORY, SCRIPT_SHELF_CATEGORY}
            ):
                continue
            self._records.setdefault(
                str(record.get("view") or "definition"), dict(record)
            )
        self._documents = {
            view: _parse_document(record.get("config"))
            for view, record in self._records.items()
        }
        # The editor mirrors TACTIC's complete Project Views tree.  The
        # ``tactic_handler`` view is one branch of that tree and remains the
        # source used by the runtime navigation model; it is not the editor
        # root.
        if "project_view" in self._documents:
            self._root_view = "project_view"
        elif "definition" in self._documents:
            self._root_view = "definition"
        elif "tactic_handler" in self._documents:
            self._root_view = "tactic_handler"
        else:
            self._root_view = "project_view"
            self._documents[self._root_view] = ElementTree.Element("config")
        self._original_xml = {
            view: _serialize(document)
            for view, document in self._documents.items()
        }
        self._xml_view = self._root_view
        self._selected_row = -1
        self._rebuild_entries()
        self._set_busy(False)

    @Slot(object)
    def _saved(self, payload) -> None:
        documents, saved, project, security_result = payload
        views = project.get_config_views()
        saved_by_view = {str(record.get("view") or ""): record for record in saved}
        untouched = [
            record for record in (views.config_dict or [])
            if not (
                str(record.get("search_type") or "") == "SideBarWdg"
                and str(record.get("view") or "") in saved_by_view
            )
        ]
        views.config_dict = [*untouched, *saved]
        if self._layout_presets is not None:
            self._layout_presets.reload_from_project()
        self._records.update(saved_by_view)
        self._original_xml = dict(documents)
        for group_code, access_rules in dict(security_result or {}).items():
            group = self._security_objects.get(str(group_code))
            if group is None:
                continue
            try:
                group.info["access_rules"] = str(access_rules or "")
                group.security = {}
                group.projects_security = {}
            except AttributeError:
                pass
        self._security_pending.clear()
        self._rebuild_security_groups()
        self._set_busy(False)
        entries = self._application.navigation_model.build_project_entries(
            project,
            self._current_login_object(),
        )
        self._application._apply_selected_project(
            self._project_code,
            self._project_title,
            entries,
            project,
        )
        self._application._notify("Sidebar saved")

    def _current_login_object(self):
        try:
            from thlib.environment import env_inst
            return env_inst.get_current_login_object()
        except (AttributeError, ImportError):
            return None

    @Slot(object)
    def _failed(self, payload) -> None:
        message = str(
            payload.get("exception") if isinstance(payload, dict) else payload
        )
        stacktrace = (
            str(payload.get("stacktrace") or "")
            if isinstance(payload, dict) else traceback.format_exc()
        )
        if self._application.debug_log:
            self._application.debug_log.log(
                "ERROR",
                f"Sidebar editor: {message}",
                group="ui/sidebar-editor",
                source="SidebarEditorController",
                stacktrace=stacktrace,
                caller=2,
            )
        self._set_busy(False, message)

    def _sync_xml_text(self) -> None:
        if 0 <= self._selected_row < len(self._flat_refs):
            self._xml_text = _serialize_element(
                self._flat_refs[self._selected_row][2]
            )
        else:
            self._xml_text = ""

    def _group_rule_allowed(self, group, element_name: str) -> bool:
        try:
            access_rules = group.get_info().get("access_rules")
        except (AttributeError, TypeError):
            access_rules = ""
        return _sidebar_rule_allowed(
            access_rules, element_name, self._project_code
        )

    def _rebuild_security_groups(self) -> None:
        if not 0 <= self._selected_row < len(self._flat_refs):
            self.security_groups.replace([])
            return
        element = self._flat_refs[self._selected_row][2]
        element_name = str(element.get("name") or "")
        records = []
        for code, group in self._security_objects.items():
            try:
                group_name = str(group.get_login_group() or code)
                label = str(group.get_pretty_name() or group_name)
            except AttributeError:
                group_name = label = code
            base = self._group_rule_allowed(group, element_name)
            allowed = self._security_pending.get((element_name, code), base)
            records.append({
                "code": code,
                "groupName": group_name,
                "label": label,
                "allowed": bool(allowed),
                "changed": bool(allowed) != base,
            })
        records.sort(key=lambda item: item["label"].lower())
        self.security_groups.replace(records)

    def _rebuild_entries(self, selected_element_id: int | None = None) -> None:
        records: list[dict] = []
        refs: list[
            tuple[str, ElementTree.Element | None, ElementTree.Element]
        ] = []
        definition_document = self._documents.get("definition")
        definitions = {
            str(element.get("name") or ""): element
            for element in (
                _all_elements(definition_document)
                if definition_document is not None else []
            )
            if element.get("name")
        }

        def walk_elements(
                owner: str,
                selectors: list[ElementTree.Element],
                depth: int,
                path: str,
                view_ancestors: tuple[str, ...],
                handler_branch: bool = False,
                handler_root_depth: int = 0) -> None:
            for index, selector in enumerate(selectors):
                name = str(selector.get("name") or "")
                element = definitions.get(name, selector)
                display = _display_class(element)
                entry_type = (
                    "section" if display == _SECTION_CLASS
                    else "separator" if display == _SEPARATOR_CLASS
                    else "link"
                )
                target = _direct_text(element, "view")
                is_handler_root = target == "tactic_handler"
                in_handler_branch = (
                    handler_branch or is_handler_root
                    or owner == "tactic_handler"
                    or self._root_view == "tactic_handler"
                )
                branch_root_depth = (
                    depth if is_handler_root and not handler_branch
                    else handler_root_depth
                )
                selector_children = _nested_elements(selector)
                definition_children = (
                    _nested_elements(element) if element is not selector else []
                )
                target_children = (
                    _view_elements(self._documents[target])
                    if target in self._documents else []
                )
                has_children = bool(
                    selector_children or definition_children or target_children
                )
                is_selected = (
                    id(selector) == selected_element_id
                    if selected_element_id is not None
                    else len(refs) == self._selected_row
                )
                key = f"{path}/{index}:{name or 'separator'}"
                records.append({
                    "key": key,
                    "name": str(element.get("name") or "untitled"),
                    "title": str(element.get("title") or element.get("name") or "Untitled"),
                    "entryType": entry_type,
                    "icon": str(element.get("icon") or (
                        "folder" if entry_type == "section" else "link"
                    )),
                    "searchType": _direct_text(element, "search_type"),
                    "searchView": _direct_text(element, "search_view"),
                    "targetView": target,
                    "ownerView": owner,
                    "depth": depth,
                    "displayDepth": (
                        max(0, depth - branch_root_depth)
                        if in_handler_branch else depth
                    ),
                    "selected": is_selected,
                    "glyph": self._application.navigation_model._icon_name(
                        str(element.get("icon") or ""),
                        _direct_text(element, "search_type"),
                    ),
                    "accent": self._accent_for_search_type(
                        _direct_text(element, "search_type")
                    ),
                    "included": True,
                    "expanded": key not in self._collapsed_folders,
                    "entryVisible": True,
                    "hasChildren": has_children,
                    "handlerBranch": in_handler_branch,
                    "isVisible": str(
                        element.get("is_visible") or "on"
                    ).strip().lower() not in {"off", "false", "no", "0"},
                    "widgetType": _widget_type(element),
                    "displayView": _display_option(element, "view"),
                    "displayClassName": _display_option(
                        element, "class_name"
                    ),
                    "resultViewMode": _result_view_mode(element),
                    "layoutPreset": _display_option(
                        element, "layout_preset"
                    ),
                    "scriptShelf": _display_option(
                        element, "script_shelf"
                    ),
                })
                refs.append((owner, selector, element))
                if entry_type != "section":
                    continue
                if selector_children:
                    walk_elements(
                        owner, selector_children, depth + 1, key,
                        view_ancestors, in_handler_branch, branch_root_depth,
                    )
                elif definition_children:
                    walk_elements(
                        "definition", definition_children, depth + 1, key,
                        view_ancestors, in_handler_branch, branch_root_depth,
                    )
                elif target_children and target not in view_ancestors:
                    walk_elements(
                        target, target_children, depth + 1, key,
                        (*view_ancestors, target),
                        in_handler_branch, branch_root_depth,
                    )

        root_document = self._documents.get(self._root_view)
        if root_document is not None:
            walk_elements(
                self._root_view,
                _view_elements(root_document),
                0,
                self._root_view,
                (self._root_view,),
            )

        if self._handler_only:
            branch = [
                (record, reference)
                for record, reference in zip(records, refs)
                if record.get("handlerBranch")
            ]
            records = [record for record, _reference in branch]
            refs = [reference for _record, reference in branch]
            if records and not any(record["selected"] for record in records):
                records[0]["selected"] = True

        expanded_by_depth: dict[int, bool] = {}
        for record in records:
            depth = int(record.get("depth") or 0)
            for ancestor_depth in tuple(expanded_by_depth):
                if ancestor_depth >= depth:
                    del expanded_by_depth[ancestor_depth]
            record["entryVisible"] = all(expanded_by_depth.values())
            if record.get("entryType") == "section":
                expanded_by_depth[depth] = bool(record.get("expanded"))
        self._flat_refs = refs
        self._selected_row = next(
            (index for index, record in enumerate(records) if record["selected"]),
            -1,
        )
        self.entries.replace(records)
        if self._selected_row >= 0:
            self._xml_view = refs[self._selected_row][0]
        elif self._xml_view not in self._documents:
            self._xml_view = self._root_view
        self._sync_xml_text()
        self._rebuild_security_groups()
        self.stateChanged.emit()
