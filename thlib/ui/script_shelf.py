"""Server-backed project and personal shelves for saved DCC scripts."""

from __future__ import annotations

import json
import traceback
import uuid
from xml.etree import ElementTree

from PySide6.QtCore import QObject, Property, Signal, Slot

from thlib.environment import env_read_config, env_write_config

from .workspace_models.records import RecordListModel


SCRIPT_SHELF_CATEGORY = "script_shelf"
SCRIPT_SHELF_SEARCH_TYPE = "SideBarWdg"
SCRIPT_SHELF_VIEW_PREFIX = "script_shelf@"
SCRIPT_SHELF_GLOBAL_VIEW = SCRIPT_SHELF_VIEW_PREFIX + "global"

_BUTTON_ROLES = (
    "buttonId", "title", "description", "iconName", "script",
    "available", "running",
)
_PRESET_ROLES = (
    "code", "view", "title", "globalShelf", "selected", "valid", "error",
)


def shelf_configuration_xml(
    buttons: list[dict], view: str, *, scope: str, entry_key: str = "",
) -> str:
    root = ElementTree.Element("config")
    view_node = ElementTree.SubElement(root, "view", {"name": view})
    values = ElementTree.SubElement(view_node, "values", {"type": "json"})
    values.text = json.dumps(
        {
            "scope": scope,
            "entryKey": entry_key,
            "buttons": [
                {
                    "id": str(button.get("buttonId") or uuid.uuid4().hex),
                    "title": str(button.get("title") or ""),
                    "description": str(button.get("description") or ""),
                    "icon": str(button.get("iconName") or "play-arrow"),
                    "script": str(button.get("script") or ""),
                }
                for button in buttons
            ],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return ElementTree.tostring(root, encoding="unicode")


def shelf_configuration_from_xml(value: object, view: str) -> dict:
    root = ElementTree.fromstring(str(value or ""))
    if root.tag != "config":
        raise ValueError("Script shelf configuration must have a config root")
    view_node = next(
        (node for node in root.findall("view") if node.get("name") == view),
        None,
    )
    values = view_node.find("values") if view_node is not None else None
    if values is None or not str(values.text or "").strip():
        raise ValueError("Script shelf values are missing")
    payload = json.loads(values.text)
    if not isinstance(payload, dict) or payload.get("scope") not in {
        "global", "preset", "tab",
    }:
        raise ValueError("Script shelf scope is invalid")
    source = payload.get("buttons")
    if not isinstance(source, list):
        raise ValueError("Script shelf buttons are invalid")
    buttons = []
    identities = set()
    for item in source:
        if not isinstance(item, dict):
            raise ValueError("Script shelf button is invalid")
        identity = str(item.get("id") or "").strip()
        script = str(item.get("script") or "").strip().strip("/")
        if not identity or identity in identities or not script:
            raise ValueError("Script shelf button identity or script is invalid")
        identities.add(identity)
        buttons.append({
            "buttonId": identity,
            "title": str(item.get("title") or script.rsplit("/", 1)[-1]),
            "description": str(item.get("description") or ""),
            "iconName": str(item.get("icon") or "play-arrow"),
            "script": script,
        })
    return {
        "scope": str(payload["scope"]),
        "entryKey": str(payload.get("entryKey") or ""),
        "buttons": buttons,
    }


def shelf_is_assigned(records: list[dict], view: str) -> bool:
    for record in records:
        try:
            root = ElementTree.fromstring(str(record.get("config") or ""))
        except ElementTree.ParseError:
            continue
        if any(
            str(node.text or "").strip() == view
            for node in root.findall(".//script_shelf")
        ):
            return True
    return False


def _assign_sidebar_shelf(
    server, project_code: str, entry_key: str, shelf_view: str,
) -> dict:
    search_type, separator, entry_name = str(entry_key or "").rpartition("@")
    if not separator or not search_type or not entry_name:
        raise ValueError("Current sidebar tab is invalid")
    records = server.query(
        "config/widget_config", [("search_type", "SideBarWdg")]
    ) or []
    if isinstance(records, dict):
        records = [records]
    records.sort(key=lambda record: bool(record.get("login")))
    for record in records:
        if str(record.get("category") or "") == SCRIPT_SHELF_CATEGORY:
            continue
        try:
            root = ElementTree.fromstring(str(record.get("config") or ""))
        except ElementTree.ParseError:
            continue
        element = next((
            node for node in root.iter("element")
            if str(node.get("name") or "") == entry_name
            and str(
                node.findtext("./search_type")
                or node.findtext("./display/search_type")
                or ""
            ).strip() == search_type
        ), None)
        if element is None:
            continue
        display = element.find("./display")
        if display is None:
            display = ElementTree.SubElement(element, "display", {"class": "LinkWdg"})
        node = display.find("./script_shelf")
        if node is None:
            node = ElementTree.SubElement(display, "script_shelf")
        node.text = shelf_view
        config = ElementTree.tostring(root, encoding="unicode")
        code = str(record.get("code") or "")
        if not code:
            continue
        key = server.build_search_key(
            "config/widget_config", code, project_code=project_code
        )
        server.insert_update(key, {"config": config}, triggers=False)
        return {**record, "config": config}
    raise RuntimeError("Current sidebar tab could not be assigned a script shelf")


def _clear_sidebar_shelf_assignments(
    server, project_code: str, shelf_view: str,
) -> list[dict]:
    records = server.query(
        "config/widget_config", [("search_type", SCRIPT_SHELF_SEARCH_TYPE)]
    ) or []
    if isinstance(records, dict):
        records = [records]
    saved = []
    for record in records:
        if str(record.get("category") or "") == SCRIPT_SHELF_CATEGORY:
            continue
        try:
            root = ElementTree.fromstring(str(record.get("config") or ""))
        except ElementTree.ParseError:
            continue
        changed = False
        for parent in root.iter():
            for node in tuple(parent):
                if (
                    node.tag == "script_shelf"
                    and str(node.text or "").strip() == shelf_view
                ):
                    parent.remove(node)
                    changed = True
        code = str(record.get("code") or "")
        if not changed or not code:
            continue
        config = ElementTree.tostring(root, encoding="unicode")
        key = server.build_search_key(
            "config/widget_config", code, project_code=project_code
        )
        server.insert_update(key, {"config": config}, triggers=False)
        saved.append({**record, "config": config})
    return saved


class ScriptShelfController(QObject):
    """Own shelf persistence, editing and Script Editor execution."""

    stateChanged = Signal()
    sharedPresetsChanged = Signal(str)

    def __init__(
        self, application, users, script_editor, server_pool=None, parent=None,
    ) -> None:
        super().__init__(parent)
        self._application = application
        self._users = users
        self._script_editor = script_editor
        self._server_pool = server_pool
        self._project_code = ""
        self._records: list[dict] = []
        self._payloads: dict[str, dict] = {}
        self._generation = 0
        self._workers = set()
        self._busy = False
        self._refresh_after_busy = False
        self._loaded_login: str | None = None
        self._error = ""
        self._running_id = ""
        self._dcc_bridge = None
        self._dcc_shelf_request = ""
        self._settings = dict(env_read_config(
            filename="ui_script_shelf",
            unique_id="ui_main",
            long_abs_path=True,
        ) or {})
        saved_mode = str(
            self._settings.get("scriptShelf/activeMode") or ""
        )
        self._active_mode = (
            saved_mode if saved_mode in {"personal", "shared"} else "shared"
        )
        self._active_mode_selected = saved_mode in {"personal", "shared"}
        self._editor_mode = "personal"
        self._personal_scope = "global"
        self._shared_scope = "global"
        self._editor_view = ""
        self._editor_title = ""
        self._original_editor_payload: dict = {}
        self.buttons = RecordListModel(_BUTTON_ROLES, identity_role="buttonId")
        self.editor_buttons = RecordListModel(
            _BUTTON_ROLES, identity_role="buttonId"
        )
        self.presets = RecordListModel(_PRESET_ROLES, identity_role="view")

        application.project_changed.connect(self._project_changed)
        application.search_state_changed.connect(self._context_changed)
        script_editor.stateChanged.connect(self._scripts_changed)
        users.stateChanged.connect(self._user_changed)
        application.window_model.windowVisibilityChanged.connect(
            self._window_visibility_changed
        )
        application._registry.register("show_script_shelf_editor", self.open_editor)
        self._project_changed(
            str(getattr(application, "current_project_code", "") or ""), ""
        )

    @Property(QObject, constant=True)
    def model(self):
        return self.buttons

    @Property(QObject, constant=True)
    def editorModel(self):
        return self.editor_buttons

    @Property(QObject, constant=True)
    def presetModel(self):
        return self.presets

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(bool, notify=stateChanged)
    def executionBusy(self) -> bool:
        return bool(self._running_id or self._script_editor.busy)

    @Property(bool, notify=stateChanged)
    def canExportDccShelf(self) -> bool:
        bridge = self._dcc_bridge
        return bool(
            self._project_code
            and bridge
            and bridge.has_dcc_capability("create_script_shelf")
        )

    @Property(bool, notify=stateChanged)
    def dccShelfBusy(self) -> bool:
        return bool(self._dcc_shelf_request)

    @Property(str, notify=stateChanged)
    def dccShelfName(self) -> str:
        record = self._effective_record()
        title = (
            self.tr("Shared shelf")
            if not record.get("login")
            and record.get("view") == SCRIPT_SHELF_GLOBAL_VIEW
            else str(record.get("title") or "").strip()
        )
        if not title:
            return "TACTIC Handler"
        return title if title.casefold().startswith("tactic") else "TACTIC " + title

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error

    @Property(bool, notify=stateChanged)
    def canManage(self) -> bool:
        try:
            return bool(self._users.canManageUsers)
        except (AttributeError, RuntimeError):
            return False

    @Property(str, notify=stateChanged)
    def editorMode(self) -> str:
        return self._editor_mode

    @Property(str, notify=stateChanged)
    def personalScope(self) -> str:
        return self._personal_scope

    @Property(str, notify=stateChanged)
    def sharedScope(self) -> str:
        return self._shared_scope

    @Property(str, notify=stateChanged)
    def editorView(self) -> str:
        return self._editor_view

    @Property(str, notify=stateChanged)
    def editorTitle(self) -> str:
        return self._editor_title

    @Property(bool, notify=stateChanged)
    def canRename(self) -> bool:
        return bool(
            self._editor_mode == "shared"
            and self._editor_view != SCRIPT_SHELF_GLOBAL_VIEW
        )

    @Property(bool, notify=stateChanged)
    def editorDirty(self) -> bool:
        current = self._editor_payload()
        if (
            current.get("mode") == "shared"
            and self._original_editor_payload.get("mode") == "shared"
        ):
            current["entryKey"] = self._original_editor_payload.get(
                "entryKey", ""
            )
        return current != self._original_editor_payload

    @Property(bool, notify=stateChanged)
    def assignmentPending(self) -> bool:
        context = self._context()
        return bool(
            self._editor_mode == "shared"
            and self._shared_scope == "tab"
            and context.get("entryKey")
            and self._editor_view
            and self._editor_view
            != str(context.get("shelfPreset") or "")
        )

    @Property(bool, notify=stateChanged)
    def canRemove(self) -> bool:
        return bool(self._editor_record()) and (
            self._editor_mode == "personal"
            or self._editor_view != SCRIPT_SHELF_GLOBAL_VIEW
        )

    @Property(str, notify=stateChanged)
    def removeTargetTitle(self) -> str:
        record = self._editor_record()
        return str(record.get("title") or self._editor_title) if record else ""

    @Property(str, notify=stateChanged)
    def activeMode(self) -> str:
        return self._active_mode

    @Property("QVariantList", notify=stateChanged)
    def activeModeOptions(self) -> list[dict]:
        return [
            {
                "value": "personal", "label": self.tr("Mine"),
                "icon": "user", "enabled": bool(self._login()),
                "translate": False,
            },
            {
                "value": "shared", "label": self.tr("Shared"),
                "icon": "users", "translate": False,
            },
        ]

    @Property("QVariantList", notify=stateChanged)
    def scriptOptions(self) -> list[dict]:
        return [
            dict(option) for option in self._script_editor.shelfScriptOptions
        ]

    @Property("QVariantList", notify=stateChanged)
    def sharedOptions(self) -> list[dict]:
        return [
            {
                "value": str(record.get("view") or ""),
                "label": str(record.get("title") or self.tr("Untitled shelf")),
            }
            for record in self.presets.records()
            if record.get("valid")
        ]

    @Property("QVariantList", notify=stateChanged)
    def sharedTabOptions(self) -> list[dict]:
        return [
            option for option in self.sharedOptions
            if option["value"] != SCRIPT_SHELF_GLOBAL_VIEW
        ]

    @Property("QVariantList", notify=stateChanged)
    def assignmentOptions(self) -> list[dict]:
        return [
            {"value": "", "label": self.tr("Project default shelf")},
            *[
                {
                    "value": str(record.get("view") or ""),
                    "label": str(record.get("title") or self.tr("Untitled shelf")),
                }
                for record in self.presets.records()
                if record.get("valid") and not record.get("globalShelf")
            ],
        ]

    @Property("QVariantList", notify=stateChanged)
    def personalScopeOptions(self) -> list[dict]:
        context = self._context()
        result = [{
            "value": "global", "label": self.tr("All tabs"),
            "translate": False,
        }]
        if context.get("entryKey"):
            result.append({
                "value": "tab",
                "label": self.tr("Only this tab: ")
                + str(context.get("title") or ""),
                "translate": False,
            })
        return result

    def _login(self) -> str:
        try:
            return str(self._users.login or "")
        except (AttributeError, RuntimeError):
            return ""

    def attach_dcc_bridge(self, bridge) -> None:
        if bridge is self._dcc_bridge:
            return
        if self._dcc_bridge is not None:
            try:
                self._dcc_bridge.stateChanged.disconnect(self.stateChanged)
                self._dcc_bridge.commandFinished.disconnect(
                    self._dcc_shelf_finished
                )
            except (RuntimeError, TypeError):
                pass
        self._dcc_bridge = bridge
        if bridge is not None:
            bridge.stateChanged.connect(self.stateChanged)
            bridge.commandFinished.connect(self._dcc_shelf_finished)
        self.stateChanged.emit()

    def _context(self) -> dict:
        context = self._application.script_shelf_context()
        return dict(context or {})

    @staticmethod
    def _is_record(record: dict) -> bool:
        return (
            str(record.get("category") or "") == SCRIPT_SHELF_CATEGORY
            and str(record.get("search_type") or "")
            == SCRIPT_SHELF_SEARCH_TYPE
            and str(record.get("view") or "").startswith(
                SCRIPT_SHELF_VIEW_PREFIX
            )
        )

    def _record(self, view: str) -> dict:
        login = self._login() if self._editor_mode == "personal" else ""
        return next((
            record for record in self._records
            if str(record.get("view") or "") == str(view or "")
            and str(record.get("login") or "") == login
        ), {})

    def _personal_record(self, scope: str) -> dict:
        login = self._login()
        entry_key = str(self._context().get("entryKey") or "")
        return next((
            record for record in self._records
            if str(record.get("login") or "") == login
            and self._payloads.get(str(record.get("view") or ""), {}).get("scope")
            == scope
            and (
                scope != "tab"
                or self._payloads.get(str(record.get("view") or ""), {}).get(
                    "entryKey"
                ) == entry_key
            )
        ), {})

    def _shared_record(self, view: str) -> dict:
        return next((
            record for record in self._records
            if not record.get("login")
            and str(record.get("view") or "") == str(view or "")
        ), {})

    def _effective_record(self) -> dict:
        context = self._context()
        if self._active_mode == "personal":
            return self._personal_record("tab") or self._personal_record(
                "global"
            )
        return self._shared_record(
            str(context.get("shelfPreset") or "")
        ) or self._shared_record(SCRIPT_SHELF_GLOBAL_VIEW)

    def _available_scripts(self) -> set[str]:
        return {
            str(option.get("value") or "")
            for option in self.scriptOptions
            if option.get("value")
        }

    def _present_buttons(self, source: list[dict]) -> list[dict]:
        available = self._available_scripts()
        return [{
            **button,
            "description": str(button.get("description") or ""),
            "available": str(button.get("script") or "") in available,
            "running": str(button.get("buttonId") or "") == self._running_id,
        } for button in source]

    def _refresh_effective(self) -> None:
        record = self._effective_record()
        payload = self._payloads.get(str(record.get("view") or ""), {})
        self.buttons.replace(self._present_buttons(payload.get("buttons") or []))
        self.stateChanged.emit()

    def _save_active_mode(self) -> None:
        self._settings["scriptShelf/activeMode"] = self._active_mode
        env_write_config(
            self._settings,
            filename="ui_script_shelf",
            unique_id="ui_main",
            long_abs_path=True,
        )

    def _sync_records(self, records: list[dict]) -> None:
        payloads = {}
        projected = []
        retained = []
        for record in records:
            if not self._is_record(record):
                continue
            view = str(record.get("view") or "")
            valid = True
            error = ""
            try:
                payload = shelf_configuration_from_xml(record.get("config"), view)
            except (ElementTree.ParseError, json.JSONDecodeError, TypeError, ValueError) as exception:
                valid = False
                error = str(exception)
                payload = {}
            normalized = dict(record)
            normalized["valid"] = valid
            normalized["error"] = error
            retained.append(normalized)
            if valid:
                payloads[view] = payload
            if not record.get("login"):
                projected.append({
                    "code": str(record.get("code") or ""),
                    "view": view,
                    "title": (
                        self.tr("Shared shelf")
                        if view == SCRIPT_SHELF_GLOBAL_VIEW
                        else str(
                            record.get("title")
                            or self.tr("Untitled shelf")
                        )
                    ),
                    "globalShelf": view == SCRIPT_SHELF_GLOBAL_VIEW,
                    "selected": view == self._editor_view,
                    "valid": valid,
                    "error": error,
                })
        if not any(item["globalShelf"] for item in projected):
            projected.append({
                "code": "",
                "view": SCRIPT_SHELF_GLOBAL_VIEW,
                "title": self.tr("Shared shelf"),
                "globalShelf": True,
                "selected": self._editor_view == SCRIPT_SHELF_GLOBAL_VIEW,
                "valid": True,
                "error": "",
            })
        projected.sort(key=lambda item: (not item["globalShelf"], item["title"].casefold()))
        self._records = retained
        self._payloads = payloads
        if not self._active_mode_selected:
            self._active_mode = (
                "personal"
                if self._personal_record("tab")
                or self._personal_record("global")
                else "shared"
            )
        self.presets.replace(projected)
        self._refresh_effective()
        if not self._editor_view or not self.editorDirty:
            self._load_editor()

    @Slot(str, str)
    def _project_changed(self, project_code: str, _title: str) -> None:
        self._generation += 1
        for worker in tuple(self._workers):
            try:
                worker.cancel()
            except (AttributeError, RuntimeError):
                pass
        self._project_code = str(project_code or "")
        self._records = []
        self._payloads = {}
        self._loaded_login = None
        self._refresh_after_busy = False
        self._error = ""
        self._shared_scope = "global"
        self.presets.clear()
        self.buttons.clear()
        self.editor_buttons.clear()
        self._editor_view = ""
        self._original_editor_payload = self._editor_payload()
        if self._project_code:
            self.refresh()
        else:
            self.stateChanged.emit()

    @Slot()
    def _context_changed(self) -> None:
        if self._personal_scope == "tab" and not self._context().get("entryKey"):
            self._personal_scope = "global"
        if self._shared_scope == "tab" and not self._context().get("entryKey"):
            self._shared_scope = "global"
        self._refresh_effective()
        if not self.editorDirty:
            self._load_editor()

    @Slot()
    def _scripts_changed(self) -> None:
        if self._running_id and not self._script_editor.busy:
            self._running_id = ""
        self._refresh_effective()
        self.editor_buttons.replace(
            self._present_buttons(self.editor_buttons.records())
        )

    @Slot()
    def _user_changed(self) -> None:
        self.stateChanged.emit()
        if self._project_code and self._login() != self._loaded_login:
            self.refresh()

    @Slot()
    def refresh(self) -> None:
        if not self._project_code:
            return
        if self._busy:
            self._refresh_after_busy = True
            return
        project_code = self._project_code
        login = self._login()
        generation = self._generation

        def operation():
            import thlib.tactic_classes as tc

            server = tc.server_start(project=project_code)
            filters = [
                ("category", SCRIPT_SHELF_CATEGORY),
                ("search_type", SCRIPT_SHELF_SEARCH_TYPE),
            ]
            records = server.query("config/widget_config", filters) or []
            if isinstance(records, dict):
                records = [records]
            records = [
                record for record in records
                if not record.get("login") or record.get("login") == login
            ]
            return project_code, generation, login, records

        self._run(operation, self._refreshed)

    @Slot(object)
    def apply_server_batch(self, batch) -> None:
        records = [
            *list((batch or {}).get("cacheChanges") or []),
            *list((batch or {}).get("cacheRetired") or []),
        ]
        if any(
            str(record.get("searchType") or "").split("?", 1)[0]
            == "config/widget_config"
            and str(record.get("projectCode") or "") == self._project_code
            for record in records
        ):
            self.refresh()

    @Slot()
    def open_editor(self) -> None:
        if not self.editorDirty:
            self._select_active_editor()
            self._load_editor()
        self._application.window_model.show_window("script_shelf_editor")

    @Slot(str)
    def export_dcc_shelf(self, name: str) -> None:
        if not self.canExportDccShelf or self._dcc_shelf_request:
            return
        name = " ".join(str(name or "").split())
        if not name:
            self._set_error(self.tr("Enter a DCC shelf name"))
            return
        request_id = self._dcc_bridge.send_active_command(
            "create_script_shelf",
            {
                "project": self._project_code,
                "name": name,
                "buttons": [
                    {
                        "title": str(button.get("title") or ""),
                        "description": str(button.get("description") or ""),
                        "icon": str(button.get("iconName") or "play-arrow"),
                        "script": str(button.get("script") or ""),
                    }
                    for button in self.buttons.records()
                ],
            },
            30.0,
        )
        if not request_id:
            self._set_error(
                str(self._dcc_bridge.error or self.tr(
                    "DCC shelf could not be created"
                ))
            )
            return
        self._dcc_shelf_request = str(request_id)
        self.stateChanged.emit()

    @Slot(str, bool, "QVariantMap", str)
    def _dcc_shelf_finished(
        self, request_id: str, success: bool, payload: dict, error: str,
    ) -> None:
        if request_id != self._dcc_shelf_request:
            return
        self._dcc_shelf_request = ""
        if success:
            self._error = ""
            self.stateChanged.emit()
            message = (
                self.tr("DCC shelf updated")
                if payload.get("updated")
                else self.tr("DCC shelf created")
            )
            self._application._notify(message)
        else:
            self._set_error(
                error or self.tr("DCC shelf could not be created")
            )

    @Slot(str)
    def set_active_mode(self, mode: str) -> None:
        mode = str(mode or "shared")
        if mode not in {"personal", "shared"} or (
            mode == "personal" and not self._login()
        ):
            return
        self._active_mode = mode
        self._active_mode_selected = True
        self._save_active_mode()
        self._refresh_effective()

    @Slot(str, bool)
    def _window_visibility_changed(self, window_id: str, visible: bool) -> None:
        if window_id == "script_shelf_editor" and visible:
            if not self.editorDirty:
                self._select_active_editor()
                self._load_editor()
            self.refresh()

    def _select_active_editor(self) -> None:
        if self._active_mode == "shared" and self.canManage:
            assigned = str(self._context().get("shelfPreset") or "")
            self._editor_mode = "shared"
            self._shared_scope = (
                "tab" if self._shared_record(assigned) else "global"
            )
            self._editor_view = (
                assigned if self._shared_record(assigned)
                else SCRIPT_SHELF_GLOBAL_VIEW
            )
            return
        self._editor_mode = "personal"
        self._personal_scope = (
            "tab" if self._personal_record("tab") else "global"
        )
        self._editor_view = ""

    def _can_change_editor(self) -> bool:
        return not self.editorDirty

    @Slot(str)
    def set_editor_mode(self, mode: str) -> None:
        mode = str(mode or "personal")
        if mode not in {"personal", "shared"} or (
            mode == "shared" and not self.canManage
        ) or not self._can_change_editor():
            return
        self._editor_mode = mode
        if mode == "shared":
            assigned = str(self._context().get("shelfPreset") or "")
            self._shared_scope = (
                "tab" if self._shared_record(assigned) else "global"
            )
            self._editor_view = (
                assigned if self._shared_scope == "tab"
                else SCRIPT_SHELF_GLOBAL_VIEW
            )
        else:
            self._editor_view = ""
        self._load_editor()

    @Slot(str)
    def set_personal_scope(self, scope: str) -> None:
        scope = str(scope or "global")
        if scope not in {"global", "tab"} or not self._can_change_editor():
            return
        if scope == "tab" and not self._context().get("entryKey"):
            return
        self._personal_scope = scope
        self._load_editor()

    @Slot(str)
    def set_shared_scope(self, scope: str) -> None:
        scope = str(scope or "global")
        if scope not in {"global", "tab"} or not self._can_change_editor():
            return
        context = self._context()
        if scope == "tab" and not context.get("entryKey"):
            return
        assigned = str(context.get("shelfPreset") or "")
        self._shared_scope = scope
        self._editor_view = (
            SCRIPT_SHELF_GLOBAL_VIEW if scope == "global"
            else assigned if self._shared_record(assigned)
            else ""
        )
        self._load_editor()

    @Slot(str)
    def select_shared(self, view: str) -> None:
        if (
            self._editor_mode != "shared"
            or not self.canManage
            or not self._can_change_editor()
        ):
            return
        if not any(record.get("view") == view for record in self.presets.records()):
            return
        self._shared_scope = (
            "global" if view == SCRIPT_SHELF_GLOBAL_VIEW else "tab"
        )
        self._editor_view = str(view or "")
        self._load_editor()

    @Slot()
    def create_shared(self) -> None:
        if self._busy or not self.canManage or not self._can_change_editor():
            return
        self._error = ""
        self._editor_mode = "shared"
        self._shared_scope = "tab"
        self._editor_view = SCRIPT_SHELF_VIEW_PREFIX + uuid.uuid4().hex
        self._editor_title = self.tr("New shelf")
        self.editor_buttons.clear()
        self._original_editor_payload = {}
        self.stateChanged.emit()

    @Slot(str)
    def set_editor_title(self, title: str) -> None:
        if not self.canRename:
            return
        title = str(title or "")
        if title == self._editor_title:
            return
        self._editor_title = title
        self.stateChanged.emit()

    @Slot()
    def discard(self) -> None:
        self._error = ""
        self._load_editor()

    def _editor_record(self) -> dict:
        if self._editor_mode == "shared":
            return self._shared_record(self._editor_view)
        return self._personal_record(self._personal_scope)

    def _load_editor(self) -> None:
        self._error = ""
        record = self._editor_record()
        if self._editor_mode == "shared":
            assigned = str(self._context().get("shelfPreset") or "")
            view = (
                SCRIPT_SHELF_GLOBAL_VIEW
                if self._shared_scope == "global"
                else self._editor_view
                or (assigned if self._shared_record(assigned) else "")
            )
            record = self._shared_record(view)
            self._editor_view = view
            self._editor_title = (
                self.tr("Shared shelf")
                if view == SCRIPT_SHELF_GLOBAL_VIEW
                else str(
                    record.get("title")
                    or self.tr("Shelf for") + " "
                    + str(self._context().get("title") or "")
                )
            )
        else:
            self._editor_view = str(record.get("view") or "")
            self._editor_title = self.tr("My shelf")
        payload = self._payloads.get(str(record.get("view") or ""), {})
        self.editor_buttons.replace(
            self._present_buttons(payload.get("buttons") or [])
        )
        self._original_editor_payload = self._editor_payload()
        self._select_preset_row()
        self.stateChanged.emit()

    def _select_preset_row(self) -> None:
        rows = self.presets.records()
        for row, record in enumerate(rows):
            record["selected"] = record.get("view") == self._editor_view
            self.presets.update_record(row, {"selected": record["selected"]})

    def _editor_payload(self) -> dict:
        context = self._context()
        return {
            "mode": self._editor_mode,
            "scope": (
                "global" if self._editor_mode == "shared"
                and self._editor_view == SCRIPT_SHELF_GLOBAL_VIEW
                else "preset" if self._editor_mode == "shared"
                else self._personal_scope
            ),
            "entryKey": (
                str(context.get("entryKey") or "")
                if (
                    self._editor_mode == "personal"
                    and self._personal_scope == "tab"
                ) or (
                    self._editor_mode == "shared"
                    and self._shared_scope == "tab"
                )
                else ""
            ),
            "title": self._editor_title.strip(),
            "buttons": [
                {
                    key: record.get(key)
                    for key in (
                        "buttonId", "title", "description", "iconName",
                        "script",
                    )
                }
                for record in self.editor_buttons.records()
            ],
        }

    @Slot()
    def add_button(self) -> None:
        options = self.scriptOptions
        script = str(options[0].get("value") or "") if options else ""
        title = str(options[0].get("label") or self.tr("New button")) if options else self.tr("New button")
        rows = self.editor_buttons.records()
        rows.append({
            "buttonId": uuid.uuid4().hex,
            "title": title.rsplit("/", 1)[-1],
            "description": "",
            "iconName": "play-arrow",
            "script": script,
            "available": bool(script),
            "running": False,
        })
        self.editor_buttons.replace(rows)
        self.stateChanged.emit()

    @Slot(int, str, "QVariant")
    def update_button(self, row: int, field: str, value) -> None:
        if field not in {"title", "description", "iconName", "script"}:
            return
        if self.editor_buttons.update_record(row, {field: str(value or "")}):
            if field == "script":
                self.editor_buttons.update_record(row, {
                    "available": str(value or "") in self._available_scripts()
                })
            self.stateChanged.emit()

    @Slot(int)
    def remove_button(self, row: int) -> None:
        self.editor_buttons.remove(row)
        self.stateChanged.emit()

    @Slot(int, int)
    def move_button(self, row: int, offset: int) -> None:
        records = self.editor_buttons.records()
        target = row + offset
        if not 0 <= row < len(records) or not 0 <= target < len(records):
            return
        records.insert(target, records.pop(row))
        self.editor_buttons.replace(records)
        self.stateChanged.emit()

    @Slot()
    def save(self) -> None:
        if self._busy or not self._project_code:
            return
        payload = self._editor_payload()
        if self._editor_mode == "shared" and not self.canManage:
            return
        if self._editor_mode == "personal" and not self._login():
            self._set_error(self.tr("Sign in to save a personal shelf"))
            return
        if self._editor_mode == "shared" and not payload["title"]:
            self._set_error(self.tr("Enter a shelf name"))
            return
        if self._editor_mode == "shared" and any(
            str(item.get("view") or "") != self._editor_view
            and str(item.get("title") or "").casefold()
            == payload["title"].casefold()
            for item in self.presets.records()
        ):
            self._set_error(self.tr(
                "A shelf preset with this name already exists"
            ))
            return
        if any(not button["script"] for button in payload["buttons"]):
            self._set_error(self.tr("Choose a script for every shelf button"))
            return
        record = self._editor_record()
        view = str(record.get("view") or self._editor_view or "")
        if not view:
            view = SCRIPT_SHELF_VIEW_PREFIX + uuid.uuid4().hex
        login = self._login() if self._editor_mode == "personal" else ""
        title = payload["title"] or self.tr("My shelf")
        config = shelf_configuration_xml(
            payload["buttons"], view,
            scope=payload["scope"], entry_key=payload["entryKey"],
        )
        assigned_view = str(self._context().get("shelfPreset") or "")
        assignment_entry = (
            payload["entryKey"]
            if self._editor_mode == "shared"
            and self._shared_scope == "tab"
            and assigned_view != view
            else ""
        )
        project_code = self._project_code
        generation = self._generation
        code = str(record.get("code") or "")

        def operation():
            import thlib.tactic_classes as tc

            server = tc.server_start(project=project_code)
            data = {
                "search_type": SCRIPT_SHELF_SEARCH_TYPE,
                "category": SCRIPT_SHELF_CATEGORY,
                "view": view,
                "title": title,
                "login": login,
                "config": config,
            }
            if code:
                key = server.build_search_key(
                    "config/widget_config", code, project_code=project_code
                )
                server.insert_update(key, data, triggers=True)
                saved_code = code
            else:
                created = server.insert(
                    "config/widget_config", data, triggers=True
                ) or {}
                saved_code = str(created.get("code") or "")
            sidebar_record = (
                _assign_sidebar_shelf(
                    server, project_code, assignment_entry, view
                )
                if assignment_entry else {}
            )
            return (
                project_code,
                generation,
                {**data, "code": saved_code},
                assignment_entry,
                sidebar_record,
            )

        self._run(operation, self._saved)

    @Slot()
    def apply_to_current_tab(self) -> None:
        context = self._context()
        entry_key = str(context.get("entryKey") or "")
        view = str(self._editor_view or "")
        record = self._editor_record()
        if (
            self._busy
            or not self.canManage
            or self._editor_mode != "shared"
            or self._shared_scope != "tab"
            or self.editorDirty
            or not entry_key
            or not record.get("code")
            or view == str(context.get("shelfPreset") or "")
        ):
            return
        project_code = self._project_code
        generation = self._generation

        def operation():
            import thlib.tactic_classes as tc

            server = tc.server_start(project=project_code)
            return (
                project_code,
                generation,
                entry_key,
                view,
                _assign_sidebar_shelf(server, project_code, entry_key, view),
            )

        self._run(operation, self._applied_to_current_tab)

    @Slot()
    def remove(self) -> None:
        record = self._editor_record()
        if self._busy or not record or not record.get("code"):
            return
        if self._editor_mode == "shared" and (
            not self.canManage or self._editor_view == SCRIPT_SHELF_GLOBAL_VIEW
        ):
            return
        project_code = self._project_code
        generation = self._generation
        code = str(record["code"])
        view = str(record.get("view") or "")
        login = str(record.get("login") or "")

        def operation():
            import thlib.tactic_classes as tc

            server = tc.server_start(project=project_code)
            sidebar_records = (
                _clear_sidebar_shelf_assignments(server, project_code, view)
                if not login else []
            )
            key = server.build_search_key(
                "config/widget_config", code, project_code=project_code
            )
            server.delete_sobject(key)
            return (
                project_code, generation, code, view, login, sidebar_records,
            )

        self._run(operation, self._deleted)

    @Slot(str)
    def run(self, button_id: str) -> None:
        if self._running_id or self._script_editor.busy:
            return
        button = self.buttons.lookup("buttonId", str(button_id or ""))
        if not button or not button.get("available"):
            self._application._notify(self.tr("This shelf script is unavailable"))
            return
        self._running_id = str(button_id)
        if not self._script_editor.run_saved_script(button["script"]):
            self._running_id = ""
            self._application._notify(
                str(
                    self._script_editor.error
                    or self.tr("Script could not be started")
                )
            )
        self._refresh_effective()

    def _run(self, operation, handler) -> None:
        try:
            if self._server_pool is None:
                raise RuntimeError(self.tr("Server worker is unavailable"))
            if self._server_pool.is_stopped:
                self._server_pool.start()
            worker = self._server_pool.add_task(operation)
            if worker is None:
                raise RuntimeError(self.tr("Server worker is unavailable"))
            self._workers.add(worker)
            worker.result.connect(handler)
            worker.error.connect(self._failed)

            def release(_worker):
                self._workers.discard(worker)
                self._busy = bool(self._workers)
                refresh = self._refresh_after_busy and not self._busy
                if refresh:
                    self._refresh_after_busy = False
                self.stateChanged.emit()
                if refresh:
                    self.refresh()

            worker.settled.connect(release)
            self._busy = True
            self._error = ""
            self.stateChanged.emit()
            worker.start()
        except Exception as exception:
            self._set_error(str(exception))

    @Slot(object)
    def _refreshed(self, payload) -> None:
        project_code, generation, login, records = payload
        if project_code != self._project_code or generation != self._generation:
            return
        self._loaded_login = login
        self._sync_records(records)

    @Slot(object)
    def _saved(self, payload) -> None:
        project_code, generation, saved, entry_key, sidebar_record = payload
        if project_code != self._project_code or generation != self._generation:
            return
        code = str(saved.get("code") or "")
        view = str(saved.get("view") or "")
        login = str(saved.get("login") or "")
        records = [
            record for record in self._records
            if not (
                (code and str(record.get("code") or "") == code)
                or (
                    str(record.get("view") or "") == view
                    and str(record.get("login") or "") == login
                )
            )
        ]
        self._editor_view = view
        self._active_mode = "personal" if login else "shared"
        self._active_mode_selected = True
        self._save_active_mode()
        if entry_key and sidebar_record:
            self._application.apply_script_shelf_assignment(
                project_code, entry_key, view, sidebar_record
            )
        self._sync_records([*records, saved])
        self._load_editor()
        self._application._notify(self.tr("Script shelf saved"))
        if not login:
            self.sharedPresetsChanged.emit(project_code)

    @Slot(object)
    def _applied_to_current_tab(self, payload) -> None:
        project_code, generation, entry_key, view, sidebar_record = payload
        if project_code != self._project_code or generation != self._generation:
            return
        self._active_mode = "shared"
        self._active_mode_selected = True
        self._save_active_mode()
        self._application.apply_script_shelf_assignment(
            project_code, entry_key, view, sidebar_record
        )
        self._application._notify(self.tr("Shelf applied to current tab"))

    @Slot(object)
    def _deleted(self, payload) -> None:
        project_code, generation, code, view, login, sidebar_records = payload
        if project_code != self._project_code or generation != self._generation:
            return
        self._records = [
            record for record in self._records
            if str(record.get("code") or "") != code
        ]
        if self._editor_mode == "shared":
            self._shared_scope = "global"
            self._editor_view = SCRIPT_SHELF_GLOBAL_VIEW
        else:
            if not self._personal_record("tab"):
                self._personal_scope = "global"
            if self._active_mode == "personal" and not (
                self._personal_record("tab")
                or self._personal_record("global")
            ):
                self._active_mode = "shared"
                self._save_active_mode()
        self._sync_records(self._records)
        self._load_editor()
        if not login:
            self._application.remove_script_shelf_assignments(
                project_code, view, sidebar_records
            )
        self._application._notify(self.tr("Script shelf removed"))
        if not login:
            self.sharedPresetsChanged.emit(project_code)

    def _set_error(self, message: str) -> None:
        self._error = str(message or "")
        self.stateChanged.emit()
        if self._error:
            self._application._notify(self._error)

    @Slot(object)
    def _failed(self, error) -> None:
        payload, _worker = error
        message = str(payload.get("exception") or error)
        stacktrace = str(
            payload.get("traceback")
            or payload.get("stacktrace")
            or traceback.format_exc()
        )
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.log(
                "ERROR", message, group="ui/script-shelf",
                source="ScriptShelfController", stacktrace=stacktrace,
                caller=2,
            )
        self._set_error(message)

    def shutdown(self) -> None:
        self.attach_dcc_bridge(None)
        for worker in tuple(self._workers):
            try:
                worker.cancel()
            except (AttributeError, RuntimeError):
                pass
