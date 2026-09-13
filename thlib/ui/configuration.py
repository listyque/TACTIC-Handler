from __future__ import annotations

import copy

from PySide6.QtCore import QObject, Property, Signal, Slot

from tactic_handler_dcc.connectors import (
    dcc_configuration_fields,
    dcc_configuration_pages,
    normalize_dcc_values,
)
from thlib.environment import env_read_config, env_write_config


def _thread_count(value) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = 4
    return max(1, min(32, value))


_CHECKIN_CONTROLS = {
    "previewsThroughHttp": ("QCheckBox", "getPreviewsThroughHttpCheckbox", True),
    "verifyRepositoryMd5": ("QCheckBox", "verifyRepositoryMd5CheckBox", False),
    "autoCleanRepositorySync": (
        "QCheckBox", "autoCleanRepositorySyncCheckBox", False
    ),
    "repositorySyncScopeMode": (
        "QComboBox", "repositorySyncScopeModeComboBox", 0
    ),
    "repositorySyncPartialChunkSize": (
        "QSpinBox", "repositorySyncPartialChunkSizeSpinBox", 10
    ),
    "doubleClickSave": ("QCheckBox", "doubleClickSaveCheckBox", False),
    "doubleClickOpen": ("QCheckBox", "doubleClickOpenCheckBox", False),
    "showBuiltinProcesses": ("QCheckBox", "showAllProcessCheckBox", False),
    "versionsSeparate": ("QCheckBox", "versionsSeparateCheckinCheckBox", False),
    "descriptionLimitEnabled": ("QCheckBox", "snapshotDescriptionLimitCheckBox", True),
    "descriptionLimit": ("QSpinBox", "snapshotDescriptionLimitSpinBox", 80),
    "displayLimit": ("QSpinBox", "displayLimitSpinBox", 20),
    "defaultViewMode": ("QComboBox", "defaultSearchViewComboBox", 0),
    "versionsRight": ("QRadioButton", "rightVersionsRadioButton", True),
    "versionsBottom": ("QRadioButton", "bottomVersionsRadioButton", False),
    "checkinMethod": ("QComboBox", "checkinMethodComboBox", 4),
    "checkoutMethod": ("QComboBox", "checkoutMethodComboBox", 1),
    "updateVersionless": ("QCheckBox", "updateVersionlessCheckBox", True),
    "generatePreviews": ("QCheckBox", "generatePreviewsCheckBox", True),
    "confirmSaving": ("QCheckBox", "askBeforeSaveCheckBox", True),
    "confirmRevision": ("QCheckBox", "askReplaceRevisionCheckBox", True),
    "sequencePaddingEnabled": ("QCheckBox", "sequencePaddingCheckBox", False),
    "sequencePadding": ("QSpinBox", "sequencePaddingSpinBox", 3),
    "sequenceNaming": ("QLineEdit", "sequenceNamingTemplateLineEdit", "$FILENAME_$LAYER_$UDIM/UV.$FRAME.$EXT"),
    "syncDropPlate": ("QCheckBox", "syckDropPlateCheckBox", True),
    "uncheckDropPlate": ("QCheckBox", "uncheckFromDropPlateCheckBox", True),
    "clearDropPlate": ("QCheckBox", "clearDropPlateAfterCheckincheckBox", True),
    "groupCheckin": ("QCheckBox", "groupCheckinCheckBox", False),
    "keepFilename": ("QCheckBox", "keepFilenameCheckBox", False),
    "includeSubfolders": ("QCheckBox", "includeSubfoldersCheckBox", False),
    "allowSingleUdim": ("QCheckBox", "oneUdimDetectionCheckBox", True),
    "allowSingleFrame": ("QCheckBox", "oneFrameSequenceDetectionCheckBox", True),
    "minimumFramePadding": ("QSpinBox", "minFramesPaddingSpinBox", 3),
}


def normalize_dcc_preferences(application: str, values: dict) -> dict:
    return normalize_dcc_values(
        dcc_configuration_fields(application), values
    )


def read_dcc_preferences(application: str) -> dict:
    application = str(application or "").lower()
    stored = dict(env_read_config(
        filename="ui_dcc_preferences",
        unique_id="ui_main",
        long_abs_path=True,
    ) or {})
    return normalize_dcc_preferences(
        application, dict(stored.get(application) or {})
    )


def write_dcc_preferences(application: str, values: dict) -> None:
    application = str(application or "").lower()
    stored = dict(env_read_config(
        filename="ui_dcc_preferences",
        unique_id="ui_main",
        long_abs_path=True,
    ) or {})
    stored[application] = normalize_dcc_preferences(application, values)
    env_write_config(
        stored,
        filename="ui_dcc_preferences",
        unique_id="ui_main",
        long_abs_path=True,
    )


class ConfigurationController(QObject):
    currentPageChanged = Signal()
    dirtyChanged = Signal()
    sessionStarted = Signal()
    pageReset = Signal(str)
    confirmationRequested = Signal()
    closeAllowed = Signal()
    serverTestChanged = Signal()

    _builtin_pages = {
        "server",
        "repository",
        "project",
        "checkin_preferences",
        "global_preferences",
        "appearance",
        "tasks_preferences",
        "cache",
    }
    _builtin_resettable_pages = {
        "server", "checkin_preferences",
        "global_preferences", "appearance", "tasks_preferences", "cache",
    }

    def __init__(
        self,
        apply_server_configuration,
        notify,
        global_values=None,
        apply_global_configuration=None,
        flush_search_cache=None,
        apply_checkin_configuration=None,
        task_values=None,
        apply_task_configuration=None,
        background_values=None,
        apply_background_configuration=None,
        cache_values=None,
        apply_cache_configuration=None,
        clear_cache=None,
        parent=None,
        *,
        appearance_values=None,
        apply_appearance_configuration=None,
        checkin_values=None,
    ) -> None:
        super().__init__(parent)
        self._apply_server_configuration = apply_server_configuration
        self._notify = notify
        self._global_values = global_values
        self._apply_global_configuration = apply_global_configuration
        self._appearance_values = appearance_values
        self._apply_appearance_configuration = apply_appearance_configuration
        self._flush_search_cache = flush_search_cache
        self._checkin_runtime_values = checkin_values
        self._apply_checkin_configuration = apply_checkin_configuration
        self._task_values = task_values
        self._apply_task_configuration = apply_task_configuration
        self._background_values = background_values
        self._apply_background_configuration = apply_background_configuration
        self._cache_values = cache_values
        self._apply_cache_configuration = apply_cache_configuration
        self._clear_cache = clear_cache
        self._dcc_pages = {
            page["id"]: page for page in dcc_configuration_pages()
        }
        self._pages = self._builtin_pages | set(self._dcc_pages)
        self._resettable_pages = (
            self._builtin_resettable_pages | set(self._dcc_pages)
        )
        self._settings = dict(env_read_config(
            filename="ui_settings",
            unique_id="ui_conf",
            long_abs_path=True,
        ) or {})
        self._current_page = str(
            self._settings.get("configuration/currentPage", "server")
            or "server"
        )
        if self._current_page not in self._pages:
            self._current_page = "server"
        self._original_values: dict[str, dict] = {}
        self._pending_values: dict[str, dict] = {}
        self._dirty_pages: set[str] = set()
        self._server_test_busy = False
        self._server_test_status = "idle"
        self._server_test_message = ""
        self._server_test_worker = None

    def _server_values(self) -> dict:
        from thlib.environment import env_server

        values = {
            "serverUrl": str(env_server.get_server() or ""),
            "presetName": str(env_server.get_cur_srv_preset() or ""),
        }
        if self._background_values:
            values.update(dict(self._background_values()))
        return values

    def _values_for_page(self, page_id: str) -> dict:
        if page_id == "server":
            return self._server_values()
        if page_id == "checkin_preferences":
            return self._checkin_values()
        if page_id == "global_preferences" and self._global_values:
            return dict(self._global_values())
        if page_id == "appearance" and self._appearance_values:
            return dict(self._appearance_values())
        if page_id == "tasks_preferences" and self._task_values:
            return dict(self._task_values())
        if page_id == "cache" and self._cache_values:
            return dict(self._cache_values())
        if page_id in self._dcc_pages:
            return read_dcc_preferences(
                self._dcc_pages[page_id]["application"]
            )
        return {}

    @staticmethod
    def _control_value(config: dict, control: str, default):
        for values in (config or {}).values():
            names = list(values.get("obj_name") or [])
            data = list(values.get("value") or [])
            if control in names:
                index = names.index(control)
                if index < len(data):
                    return data[index]
        return default

    @classmethod
    def _controls_values(cls, config: dict, controls: dict) -> dict:
        return {
            key: cls._control_value(config, name, default)
            for key, (_group, name, default) in controls.items()
        }

    @staticmethod
    def _store_controls(config: dict, values: dict, controls: dict) -> dict:
        result = copy.deepcopy(config or {})
        for key, (group, control, _default) in controls.items():
            bucket = result.setdefault(group, {"obj_name": [], "value": []})
            names = list(bucket.get("obj_name") or [])
            data = list(bucket.get("value") or [])
            value = values.get(key)
            if isinstance(value, bool):
                value = int(value)
            if control in names:
                index = names.index(control)
                while len(data) <= index:
                    data.append(None)
                data[index] = value
            else:
                names.append(control)
                data.append(value)
            bucket["obj_name"] = names
            bucket["value"] = data
        return result

    def _checkin_values(self) -> dict:
        from thlib.environment import cfg_controls

        values = self._controls_values(
            cfg_controls.get_checkin() or {}, _CHECKIN_CONTROLS
        )
        if self._checkin_runtime_values:
            values.update(dict(self._checkin_runtime_values()))
        return self._normalize_checkin(values)

    @staticmethod
    def _normalize_server(values: dict) -> dict:
        from thlib.ui.server_address import normalize_tactic_server_url

        server_url = normalize_tactic_server_url(values.get("serverUrl"))
        ping_interval = int(values.get("pingInterval", 0))
        if ping_interval not in {0, 10, 60}:
            ping_interval = 0
        update_interval = int(values.get("serverUpdateInterval", 30))
        if update_interval not in {5, 10, 30, 60}:
            update_interval = 30
        heartbeat_interval = int(
            values.get("presenceHeartbeatInterval", 120)
        )
        if heartbeat_interval not in {30, 60, 120, 300}:
            heartbeat_interval = 120
        return {
            "serverUrl": server_url,
            "presetName": str(values.get("presetName") or "").strip(),
            "pingInterval": ping_interval,
            "serverUpdateInterval": update_interval,
            "presenceHeartbeatInterval": heartbeat_interval,
        }

    @staticmethod
    def _normalize_global(values: dict) -> dict:
        diagnostic_levels = (
            "LOG", "INFO", "WARNING", "MISSING", "EXCEPTION", "ERROR",
            "CRITICAL", "API",
        )
        selected_levels = {
            str(level or "").upper()
            for level in (values.get("debugLogLevels") or [])
        }
        return {
            "closeToTray": bool(values.get("closeToTray", True)),
            "serverThreads": _thread_count(values.get("serverThreads", 4)),
            "localThreads": _thread_count(values.get("localThreads", 4)),
            "debugLogLevels": [
                level for level in diagnostic_levels if level in selected_levels
            ],
            "configPath": str(values.get("configPath") or ""),
        }

    @staticmethod
    def _normalize_appearance(values: dict) -> dict:
        from thlib.ui.localization import normalize_language
        from thlib.ui.rendering import normalize_render_backend
        from thlib.ui.theme_catalog import (
            normalize_icon_set,
            normalize_theme_accents,
            normalize_theme_style,
        )

        values = {
            "darkTheme": bool(values.get("darkTheme")),
            "themeStyle": normalize_theme_style(values.get("themeStyle")),
            "themeAccents": normalize_theme_accents(
                values.get("themeAccents")
            ),
            "iconSet": normalize_icon_set(values.get("iconSet")),
            "clickAnimations": bool(
                values.get("clickAnimations", True)
            ),
            "hoverAnimations": bool(
                values.get("hoverAnimations", True)
            ),
            "fadeAnimations": bool(
                values.get("fadeAnimations", True)
            ),
            "popupAnimations": bool(
                values.get("popupAnimations", values.get("fadeAnimations", True))
            ),
            "renderBackend": normalize_render_backend(
                values.get("renderBackend")
            ),
            "language": normalize_language(values.get("language")),
        }
        return values

    @staticmethod
    def _normalize_tasks(values: dict) -> dict:
        view_mode = str(values.get("viewMode") or "list")
        sort_mode = str(values.get("sortMode") or "due")
        group_mode = str(values.get("groupMode") or "process")
        quick_view_mode = str(values.get("quickViewMode") or "cards")
        workspace_surface = str(values.get("workspaceSurface") or "quick")
        if view_mode not in {"list", "gantt"}:
            view_mode = "list"
        if sort_mode not in {
            "due", "recent", "process", "user", "status", "object",
            "priority", "milestone", "supervisor",
        }:
            sort_mode = "due"
        if group_mode not in {
            "process", "status", "user", "object", "project",
            "search_type", "none",
        }:
            group_mode = "process"
        columns = []
        for order, source in enumerate(values.get("columns") or []):
            source = dict(source or {})
            try:
                width = max(40, min(480, int(source.get("width") or 80)))
            except (TypeError, ValueError):
                width = 80
            columns.append({
                "key": str(source.get("key") or ""),
                "label": str(source.get("label") or ""),
                "width": width,
                "visible": bool(source.get("visible")),
                "required": bool(source.get("required")),
                "order": order,
            })
        return {
            "viewMode": view_mode,
            "sortMode": sort_mode,
            "groupMode": group_mode,
            "quickViewMode": (
                quick_view_mode
                if quick_view_mode in {"cards", "compact"}
                else "cards"
            ),
            "workspaceSurface": (
                workspace_surface
                if workspace_surface in {"quick", "browser"}
                else "quick"
            ),
            "inspectorExpanded": bool(values.get("inspectorExpanded")),
            "columns": columns,
        }

    @staticmethod
    def _normalize_cache(values: dict) -> dict:
        from thlib.server_cache import CACHE_DOMAINS

        normalized = {
            domain: bool(values.get(domain, True))
            for domain in CACHE_DOMAINS
        }
        normalized["cacheProcessTabs"] = bool(
            values.get("cacheProcessTabs", True)
        )
        return normalized

    @staticmethod
    def _normalize_checkin(values: dict) -> dict:
        normalized = {}
        for key, (_group, _control, default) in _CHECKIN_CONTROLS.items():
            value = values.get(key, default)
            if isinstance(default, bool):
                value = bool(value)
            elif isinstance(default, int):
                try:
                    value = int(value)
                except (TypeError, ValueError):
                    value = default
            else:
                value = str(value or default)
            normalized[key] = value
        normalized["descriptionLimit"] = max(
            20, min(50000, normalized["descriptionLimit"])
        )
        normalized["displayLimit"] = max(
            20, min(5000, normalized["displayLimit"])
        )
        normalized["defaultViewMode"] = max(
            0, min(1, normalized["defaultViewMode"])
        )
        normalized["sequencePadding"] = max(
            1, min(9, normalized["sequencePadding"])
        )
        normalized["minimumFramePadding"] = max(
            1, min(9, normalized["minimumFramePadding"])
        )
        normalized["repositorySyncScopeMode"] = max(
            0, min(1, normalized["repositorySyncScopeMode"])
        )
        normalized["repositorySyncPartialChunkSize"] = max(
            1, min(250, normalized["repositorySyncPartialChunkSize"])
        )
        normalized["checkinMethod"] = max(
            0, min(4, normalized["checkinMethod"])
        )
        normalized["checkoutMethod"] = max(
            0, min(1, normalized["checkoutMethod"])
        )
        loading_mode = str(values.get("loadingMode") or "pages")
        normalized["loadingMode"] = (
            loading_mode if loading_mode in {"pages", "infinite"}
            else "pages"
        )
        normalized["snapshotShowAll"] = bool(
            values.get("snapshotShowAll", False)
        )
        normalized["snapshotShowMore"] = bool(
            values.get("snapshotShowMore", False)
        )
        content_mode = str(
            values.get("snapshotContentMode") or "both"
        )
        normalized["snapshotContentMode"] = (
            content_mode if content_mode in {"both", "preview", "files"}
            else "both"
        )
        orientation = str(
            values.get("snapshotOrientation") or "horizontal"
        )
        normalized["snapshotOrientation"] = (
            orientation if orientation in {"horizontal", "vertical"}
            else "horizontal"
        )
        normalized["commitQueueAutoClean"] = bool(
            values.get("commitQueueAutoClean", False)
        )
        return normalized

    @staticmethod
    def _server_validation_error(values: dict) -> str:
        from thlib.ui.server_address import is_valid_tactic_server_url

        if not is_valid_tactic_server_url(values.get("serverUrl")):
            return "Enter a valid TACTIC server address."
        if not str(values.get("presetName") or ""):
            return "Select a server preset."
        return ""

    def _emit_dirty_if_changed(self, previous: set[str]) -> None:
        if previous != self._dirty_pages:
            self.dirtyChanged.emit()

    @Property(str, notify=currentPageChanged)
    def current_page(self) -> str:
        return self._current_page

    @Property(bool, notify=dirtyChanged)
    def dirty(self) -> bool:
        return bool(self._dirty_pages)

    @Property(bool, notify=dirtyChanged)
    def current_page_dirty(self) -> bool:
        return self._current_page in self._dirty_pages

    @Property(bool, notify=currentPageChanged)
    def can_reset_current_page(self) -> bool:
        return self._current_page in self._resettable_pages

    @Slot()
    def begin_session(self) -> None:
        self._original_values = {
            page_id: self._values_for_page(page_id)
            for page_id in self._pages
        }
        self._pending_values.clear()
        previous = set(self._dirty_pages)
        self._dirty_pages.clear()
        self._emit_dirty_if_changed(previous)
        self.sessionStarted.emit()

    @Slot(str)
    def select_page(self, page_id: str) -> None:
        page_id = str(page_id or "")
        if page_id not in self._pages or page_id == self._current_page:
            return
        self._current_page = page_id
        self._settings["configuration/currentPage"] = page_id
        env_write_config(
            self._settings,
            filename="ui_settings",
            unique_id="ui_conf",
            long_abs_path=True,
        )
        self.currentPageChanged.emit()
        self.dirtyChanged.emit()

    @Slot(str, result="QVariantMap")
    def page_values(self, page_id: str) -> dict:
        page_id = str(page_id or "")
        if page_id in self._pending_values:
            values = dict(self._pending_values[page_id])
        elif page_id in self._original_values:
            values = dict(self._original_values[page_id])
        else:
            values = self._values_for_page(page_id)
        return values

    @Slot(str, result="QVariantMap")
    def page_schema(self, page_id: str) -> dict:
        return dict(self._dcc_pages.get(str(page_id or "")) or {})

    @Slot(str, result="QVariantMap")
    def server_preset_values(self, preset_name: str) -> dict:
        from thlib.environment import env_server

        preset = dict(
            env_server.get_server_preset(str(preset_name or "")) or {}
        )
        values = {
            "serverUrl": str(preset.get("server") or ""),
            "presetName": str(preset_name or ""),
        }
        if self._background_values:
            values.update(dict(self._background_values()))
        return values

    @Slot(str, "QVariantMap", result=str)
    def validation_error(self, page_id: str, values: dict) -> str:
        if str(page_id or "") == "server":
            return self._server_validation_error(
                self._normalize_server(values)
            )
        return ""

    @Slot(str, "QVariantMap")
    def update_page(self, page_id: str, values: dict) -> None:
        page_id = str(page_id or "")
        if page_id == "server":
            normalized = self._normalize_server(values)
        elif page_id == "checkin_preferences":
            normalized = self._normalize_checkin(values)
        elif page_id == "global_preferences":
            normalized = self._normalize_global(values)
        elif page_id == "appearance":
            normalized = self._normalize_appearance(values)
        elif page_id == "tasks_preferences":
            normalized = self._normalize_tasks(values)
        elif page_id == "cache":
            normalized = self._normalize_cache(values)
        elif page_id in self._dcc_pages:
            normalized = normalize_dcc_preferences(
                self._dcc_pages[page_id]["application"], values
            )
        else:
            return
        previous = set(self._dirty_pages)
        self._pending_values[page_id] = normalized
        if normalized == self._original_values.get(page_id, {}):
            self._dirty_pages.discard(page_id)
        else:
            self._dirty_pages.add(page_id)
        self._emit_dirty_if_changed(previous)

    def _apply_page(self, page_id: str) -> bool:
        if page_id not in self._dirty_pages:
            return True
        values = self._pending_values.get(page_id, {})
        if page_id == "server":
            validation_error = self._server_validation_error(values)
            if validation_error:
                self._notify(validation_error)
                return False
            from thlib.environment import env_server

            server_url = str(values.get("serverUrl") or "")
            preset_name = str(values.get("presetName") or "")
            presets = env_server.get_server_presets().get("presets_list", [])
            if preset_name not in presets:
                self._notify("Select an existing server preset")
                return False
            self._apply_server_configuration(
                server_url, preset_name, False
            )
            if self._apply_background_configuration:
                self._apply_background_configuration(dict(values))
            for preset_page in (
                "checkin_preferences",
                *self._dcc_pages,
            ):
                if preset_page in self._dirty_pages:
                    continue
                self._original_values.pop(preset_page, None)
                self._pending_values.pop(preset_page, None)
        elif page_id == "checkin_preferences":
            from thlib.environment import cfg_controls

            config = self._store_controls(
                cfg_controls.get_checkin() or {},
                values,
                _CHECKIN_CONTROLS,
            )
            cfg_controls.set_checkin(config)
            if self._apply_checkin_configuration:
                self._apply_checkin_configuration(dict(values))
        elif page_id == "global_preferences":
            if self._apply_global_configuration:
                self._apply_global_configuration(dict(values))
        elif page_id == "appearance":
            if self._apply_appearance_configuration:
                self._apply_appearance_configuration(dict(values))
        elif page_id == "tasks_preferences":
            if self._apply_task_configuration:
                self._apply_task_configuration(dict(values))
        elif page_id == "cache":
            if self._apply_cache_configuration:
                self._apply_cache_configuration(dict(values))
        elif page_id in self._dcc_pages:
            write_dcc_preferences(
                self._dcc_pages[page_id]["application"], values
            )
        stored_values = dict(values)
        self._original_values[page_id] = stored_values
        previous = set(self._dirty_pages)
        self._dirty_pages.discard(page_id)
        self._pending_values.pop(page_id, None)
        self._emit_dirty_if_changed(previous)
        if page_id == "server":
            self.pageReset.emit(page_id)
        return True

    @Property(bool, notify=serverTestChanged)
    def server_test_busy(self) -> bool:
        return self._server_test_busy

    @Property(str, notify=serverTestChanged)
    def server_test_status(self) -> str:
        return self._server_test_status

    @Property(str, notify=serverTestChanged)
    def server_test_message(self) -> str:
        return self._server_test_message

    def _set_server_test(self, busy: bool, status: str, message: str) -> None:
        self._server_test_busy = busy
        self._server_test_status = status
        self._server_test_message = message
        self.serverTestChanged.emit()

    @Slot("QVariantMap", result=bool)
    def test_server(self, values: dict) -> bool:
        if self._server_test_busy:
            return False
        values = self._normalize_server(values)
        validation_error = self._server_validation_error(values)
        if validation_error:
            self._set_server_test(False, "error", validation_error)
            return False

        from thlib.environment import env_inst
        from thlib.environment import env_server
        import thlib.tactic_classes as tc

        preset = dict(
            env_server.get_server_preset(values["presetName"]) or {}
        )
        preset_proxy = dict(preset.get("proxy") or {})
        proxy = {
            "login": str(preset_proxy.get("login") or ""),
            "pass": str(preset_proxy.get("pass") or ""),
            "server": str(preset_proxy.get("server") or ""),
            "enabled": bool(preset_proxy.get("enabled")),
        }
        self._set_server_test(True, "checking", "Checking TACTIC API…")
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(
            tc.server_fast_ping_predefined,
            values["serverUrl"],
            proxy,
        )
        self._server_test_worker = worker
        worker.result.connect(self._server_test_result)
        worker.error.connect(self._server_test_error)
        worker.start()
        return True

    def _server_test_result(self, result) -> None:
        self._server_test_worker = None
        if result == "ping_ok":
            self._set_server_test(
                False,
                "success",
                "TACTIC API is available. Generate a ticket to sign in.",
            )
        else:
            self._set_server_test(
                False, "error", "TACTIC API did not respond."
            )

    def _server_test_error(self, error) -> None:
        self._server_test_worker = None
        payload = (
            error[0]
            if isinstance(error, tuple) and error
            and isinstance(error[0], dict)
            else {}
        )
        text = str(payload.get("exception") or error or "")
        lowered = text.lower()
        if "405" in lowered or "method not allowed" in lowered:
            message = (
                "TACTIC API endpoint rejected the request. "
                "Use the server address without /tactic."
            )
        elif "timed out" in lowered or "timeout" in lowered:
            message = "The TACTIC server did not respond in time."
        else:
            message = "Cannot connect to the configured TACTIC server."
        self._set_server_test(False, "error", message)

    @Slot()
    def flush_search_cache(self) -> None:
        if not self._flush_search_cache:
            return
        self._flush_search_cache()
        self._notify("Saved search tabs cache cleared")

    @Slot(result=bool)
    def clear_data_cache(self) -> bool:
        if not self._clear_cache:
            return False
        return bool(self._clear_cache())

    @Slot(result=bool)
    def apply_current(self) -> bool:
        return self._apply_page(self._current_page)

    @Slot()
    def save_and_close(self) -> None:
        page_order = (
            "server",
            "appearance",
            "global_preferences",
            "tasks_preferences",
            "cache",
            "checkin_preferences",
            *self._dcc_pages,
            "project",
        )
        for page_id in page_order:
            if not self._apply_page(page_id):
                return
        self.closeAllowed.emit()

    @Slot()
    def reset_current(self) -> None:
        if self._current_page not in self._resettable_pages:
            return
        previous = set(self._dirty_pages)
        self._pending_values.pop(self._current_page, None)
        self._dirty_pages.discard(self._current_page)
        self._emit_dirty_if_changed(previous)
        self.pageReset.emit(self._current_page)

    @Slot()
    def request_close(self) -> None:
        if self._dirty_pages:
            self.confirmationRequested.emit()
        else:
            self.closeAllowed.emit()

    @Slot()
    def discard_and_close(self) -> None:
        previous = set(self._dirty_pages)
        self._pending_values.clear()
        self._dirty_pages.clear()
        self._emit_dirty_if_changed(previous)
        self.closeAllowed.emit()
