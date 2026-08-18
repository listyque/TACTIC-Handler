from __future__ import annotations

import copy
from urllib.parse import urlparse

from PySide6.QtCore import QObject, Property, QSettings, Signal, Slot


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
    "repositoryIndex": ("QComboBox", "repositoryComboBox", 0),
    "checkinMethod": ("QComboBox", "checkinMethodComboBox", 4),
    "checkoutMethod": ("QComboBox", "checkoutMethodComboBox", 1),
    "updateVersionless": ("QCheckBox", "updateVersionlessCheckBox", True),
    "generatePreviews": ("QCheckBox", "generatePreviewsCheckBox", True),
    "createMayaDirs": ("QCheckBox", "createMayaDirsCheckBox", False),
    "createPlayblast": ("QCheckBox", "createPlayblastCheckBox", True),
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

_CHECKIN_OUT_CONTROLS = {
    "processFilterEnabled": ("QGroupBox", "processTabsFilterGroupBox", False),
    "controlsFilterEnabled": ("QGroupBox", "controlsTabsFilterGroupBox", False),
    "globalMode": ("QRadioButton", "applyToAllProjectsRadioButton", True),
    "perProjectMode": ("QRadioButton", "applyPerProjectsRadioButton", False),
    "lastViewForAllTabs": ("QCheckBox", "lastViewOnAllTabscheckBox", False),
}

_DEFAULT_CONTROL_TABS = (
    ("Checkin / Checkout ", "Checkin / Checkout", True),
    ("My Tactic", "My Tactic", True),
    ("Assets Browser", "Assets Browser", True),
)


class ConfigurationController(QObject):
    currentPageChanged = Signal()
    dirtyChanged = Signal()
    sessionStarted = Signal()
    pageReset = Signal(str)
    confirmationRequested = Signal()
    closeAllowed = Signal()
    serverTestChanged = Signal()
    checkinOutProjectLoaded = Signal(str, list)

    _pages = {
        "server",
        "project",
        "checkin_preferences",
        "checkinout_preferences",
        "global_preferences",
        "tasks_preferences",
        "maya_preferences",
    }
    _resettable_pages = {
        "server", "checkin_preferences", "checkinout_preferences",
        "global_preferences", "tasks_preferences", "maya_preferences",
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
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._apply_server_configuration = apply_server_configuration
        self._notify = notify
        self._global_values = global_values
        self._apply_global_configuration = apply_global_configuration
        self._flush_search_cache = flush_search_cache
        self._apply_checkin_configuration = apply_checkin_configuration
        self._task_values = task_values
        self._apply_task_configuration = apply_task_configuration
        self._background_values = background_values
        self._apply_background_configuration = apply_background_configuration
        self._settings = QSettings("TACTIC-Handler", "modern-qml")
        self._current_page = self._settings.value(
            "configuration/currentPage", "server", type=str
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
        self._checkinout_project_requests: set[str] = set()

    def _server_values(self) -> dict:
        from thlib.environment import env_server

        site = dict(env_server.get_site() or {})
        proxy = dict(env_server.get_proxy() or {})
        values = {
            "serverUrl": str(env_server.get_server() or ""),
            "presetName": str(env_server.get_cur_srv_preset() or ""),
            "userName": str(env_server.get_user() or ""),
            "siteEnabled": bool(site.get("enabled")),
            "siteName": str(site.get("site_name") or ""),
            "proxyEnabled": bool(proxy.get("enabled")),
            "proxyLogin": str(proxy.get("login") or ""),
            "proxyServer": str(proxy.get("server") or ""),
            "proxyPassword": "",
            "hasProxyPassword": bool(proxy.get("pass")),
        }
        if self._background_values:
            values.update(dict(self._background_values()))
        return values

    def _values_for_page(self, page_id: str) -> dict:
        if page_id == "server":
            return self._server_values()
        if page_id == "checkin_preferences":
            return self._checkin_values()
        if page_id == "checkinout_preferences":
            return self._checkinout_values()
        if page_id == "global_preferences" and self._global_values:
            return dict(self._global_values())
        if page_id == "tasks_preferences" and self._task_values:
            return dict(self._task_values())
        if page_id == "maya_preferences":
            return self._maya_values()
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

    @classmethod
    def _checkin_values(cls) -> dict:
        from thlib.environment import cfg_controls, env_tactic

        values = cls._controls_values(
            cfg_controls.get_checkin() or {}, _CHECKIN_CONTROLS
        )
        repositories = []
        base_dirs = env_tactic.base_dirs or {}
        available = env_tactic.get_all_base_dirs() if base_dirs else []
        for _alias, repository in available:
            data = list((repository or {}).get("value") or [])
            if len(data) > 4 and data[4]:
                repositories.append({
                    "title": str(data[1] or data[3] or "Repository"),
                    "path": str(data[0] or ""),
                    "code": str(data[3] or ""),
                })
        values["repositories"] = repositories
        if not repositories:
            values["repositoryIndex"] = -1
        else:
            values["repositoryIndex"] = max(
                0,
                min(int(values["repositoryIndex"] or 0), len(repositories) - 1),
            )
        return values

    @staticmethod
    def _tab_records(tabs) -> list[dict]:
        return [
            {
                "name": str(tab[0] if len(tab) > 0 else ""),
                "label": str(tab[1] if len(tab) > 1 else ""),
                "enabled": bool(tab[2] if len(tab) > 2 else True),
            }
            for tab in (tabs or _DEFAULT_CONTROL_TABS)
        ]

    @classmethod
    def _checkinout_values(cls) -> dict:
        from thlib.environment import cfg_controls, env_inst

        values = cls._controls_values(
            cfg_controls.get_checkin_out() or {}, _CHECKIN_OUT_CONTROLS
        )
        projects_config = copy.deepcopy(
            cfg_controls.get_checkin_out_projects() or {}
        )
        global_tabs = projects_config.get("!tabs_list!")
        values["globalTabs"] = cls._tab_records(global_tabs)
        projects = []
        for code, project in (env_inst.projects or {}).items():
            if code == "sthpw" or bool(project.is_template()):
                continue
            project_values = dict(projects_config.get(code) or {})
            included = set(project_values.get("stypes_list") or [])
            search_types = []
            for stype in (project.stypes or {}).values():
                info = stype.get_info()
                search_types.append({
                    "code": str(stype.get_code() or ""),
                    "title": str(stype.get_pretty_name() or stype.get_code()),
                    "category": str(info.get("type") or "Category"),
                    "enabled": stype.get_code() in included,
                })
            projects.append({
                "code": str(code),
                "title": str(project.get_title() or code),
                "category": str(project.get_info().get("category") or "Projects"),
                "searchTypes": search_types,
                "tabs": cls._tab_records(project_values.get("tabs_list")),
            })
        values["projects"] = projects
        return values

    @staticmethod
    def _load_project_search_types(project_code: str):
        from thlib.environment import cfg_controls, env_inst

        project = env_inst.projects.get(project_code)
        if not project:
            raise RuntimeError("Project is unavailable: " + project_code)
        if not project.stypes:
            project.query_search_types()
        projects_config = cfg_controls.get_checkin_out_projects() or {}
        included = set(
            (projects_config.get(project_code) or {}).get("stypes_list") or []
        )
        records = []
        for stype in (project.stypes or {}).values():
            info = stype.get_info()
            records.append({
                "code": str(stype.get_code() or ""),
                "title": str(stype.get_pretty_name() or stype.get_code()),
                "category": str(info.get("type") or "Category"),
                "enabled": stype.get_code() in included,
            })
        return project_code, records

    @Slot(str)
    def load_checkinout_project(self, project_code: str) -> None:
        project_code = str(project_code or "")
        if not project_code or project_code in self._checkinout_project_requests:
            return
        from thlib.environment import env_inst

        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        self._checkinout_project_requests.add(project_code)
        worker = env_inst.server_pool.add_task(
            self._load_project_search_types, project_code
        )
        worker.result.connect(self._checkinout_project_result)
        worker.error.connect(self._checkinout_project_error)
        worker.start()

    @Slot(object)
    def _checkinout_project_result(self, result) -> None:
        project_code, records = result
        self._checkinout_project_requests.discard(project_code)
        for page_values in (
            self._original_values.get("checkinout_preferences"),
            self._pending_values.get("checkinout_preferences"),
        ):
            if not page_values:
                continue
            for project in page_values.get("projects") or []:
                if project.get("code") == project_code:
                    project["searchTypes"] = copy.deepcopy(records)
                    break
        self.checkinOutProjectLoaded.emit(project_code, records)

    @Slot(object)
    def _checkinout_project_error(self, error) -> None:
        payload = error[0] if isinstance(error, tuple) and error else {}
        message = (
            str(payload.get("exception") or error)
            if isinstance(payload, dict) else str(error)
        )
        self._checkinout_project_requests.clear()
        self._notify(message)

    @staticmethod
    def _maya_values() -> dict:
        from thlib.environment import cfg_controls

        config = dict(cfg_controls.get_maya_scene() or {})

        def control_value(group: str, name: str, default):
            values = dict(config.get(group) or {})
            names = list(values.get("obj_name") or [])
            data = list(values.get("value") or [])
            if name in names:
                index = names.index(name)
                if index < len(data):
                    return data[index]
            return config.get(name, default)

        format_index = int(control_value(
            "QComboBox", "formatTypeComboBox", 0
        ) or 0)
        return {
            "currentWorkdir": str(control_value(
                "QLineEdit", "currentWorkdirLineEdit", ""
            ) or ""),
            "createMayaDirs": bool(control_value(
                "QCheckBox", "createMayaDirsCheckBox", True
            )),
            "createPlayblast": bool(control_value(
                "QCheckBox", "createPlayblastCheckBox", True
            )),
            "saveFormat": (
                "mayaBinary" if format_index == 1 else "mayaAscii"
            ),
        }

    @staticmethod
    def _normalize_server(values: dict) -> dict:
        server_url = str(values.get("serverUrl") or "").strip().rstrip("/")
        if server_url.lower().endswith("/tactic"):
            server_url = server_url[:-7].rstrip("/")
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
            "userName": str(values.get("userName") or "").strip(),
            "siteEnabled": bool(values.get("siteEnabled")),
            "siteName": str(values.get("siteName") or "").strip(),
            "proxyEnabled": bool(values.get("proxyEnabled")),
            "proxyLogin": str(values.get("proxyLogin") or "").strip(),
            "proxyServer": str(values.get("proxyServer") or "").strip(),
            "proxyPassword": str(values.get("proxyPassword") or ""),
            "hasProxyPassword": bool(values.get("hasProxyPassword")),
            "pingInterval": ping_interval,
            "serverUpdateInterval": update_interval,
            "presenceHeartbeatInterval": heartbeat_interval,
        }

    @staticmethod
    def _normalize_global(values: dict) -> dict:
        from modern_ui.localization import normalize_language
        from modern_ui.theme_catalog import normalize_theme_style

        diagnostic_levels = (
            "LOG", "INFO", "WARNING", "MISSING", "EXCEPTION", "ERROR",
            "CRITICAL", "API",
        )
        selected_levels = {
            str(level or "").upper()
            for level in (values.get("debugLogLevels") or [])
        }

        values = {
            "cacheProcessTabs": bool(values.get("cacheProcessTabs")),
            "darkTheme": bool(values.get("darkTheme")),
            "themeStyle": normalize_theme_style(values.get("themeStyle")),
            "language": normalize_language(values.get("language")),
            "debugLogLevels": [
                level for level in diagnostic_levels
                if level in selected_levels
            ],
            "configPath": str(values.get("configPath") or ""),
        }
        return values

    @staticmethod
    def _normalize_tasks(values: dict) -> dict:
        view_mode = str(values.get("viewMode") or "list")
        sort_mode = str(values.get("sortMode") or "due")
        group_mode = str(values.get("groupMode") or "process")
        if view_mode not in {"list", "gantt"}:
            view_mode = "list"
        if sort_mode not in {
            "due", "recent", "process", "user", "status", "object"
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
            "inspectorExpanded": bool(values.get("inspectorExpanded")),
            "columns": columns,
        }

    @staticmethod
    def _normalize_maya(values: dict) -> dict:
        save_format = str(values.get("saveFormat") or "mayaAscii")
        if save_format not in {"mayaAscii", "mayaBinary"}:
            save_format = ""
        return {
            "currentWorkdir": str(values.get("currentWorkdir") or ""),
            "createMayaDirs": bool(values.get("createMayaDirs")),
            "createPlayblast": bool(values.get("createPlayblast")),
            "saveFormat": save_format,
        }

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
        try:
            normalized["repositoryIndex"] = int(
                values.get("repositoryIndex", 0)
            )
        except (TypeError, ValueError):
            normalized["repositoryIndex"] = 0
        normalized["repositories"] = list(values.get("repositories") or [])
        return normalized

    @classmethod
    def _normalize_checkinout(cls, values: dict) -> dict:
        normalized = {}
        for key, (_group, _control, default) in _CHECKIN_OUT_CONTROLS.items():
            normalized[key] = bool(values.get(key, default))
        normalized["globalTabs"] = cls._tab_records(values.get("globalTabs"))
        normalized["projects"] = []
        for project in values.get("projects") or []:
            normalized["projects"].append({
                "code": str(project.get("code") or ""),
                "title": str(project.get("title") or ""),
                "category": str(project.get("category") or "Projects"),
                "searchTypes": [
                    {
                        "code": str(stype.get("code") or ""),
                        "title": str(stype.get("title") or ""),
                        "category": str(stype.get("category") or "Category"),
                        "enabled": bool(stype.get("enabled")),
                    }
                    for stype in project.get("searchTypes") or []
                ],
                "tabs": cls._tab_records(project.get("tabs")),
            })
        return normalized

    @staticmethod
    def _server_validation_error(values: dict) -> str:
        parsed = urlparse(str(values.get("serverUrl") or ""))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return "Enter a valid http:// or https:// TACTIC server address."
        if not str(values.get("presetName") or ""):
            return "Select a server preset."
        if not str(values.get("userName") or ""):
            return "Enter a TACTIC user name."
        if values.get("siteEnabled") and not str(values.get("siteName") or ""):
            return "Enter a portal site name or disable portal site."
        if (
            values.get("proxyEnabled")
            and not str(values.get("proxyServer") or "")
        ):
            return "Enter a proxy server or disable the proxy."
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
        self._settings.setValue("configuration/currentPage", page_id)
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
        if page_id == "server":
            values["proxyPassword"] = ""
        return values

    @Slot(str, result="QVariantMap")
    def server_preset_values(self, preset_name: str) -> dict:
        from thlib.environment import env_server

        preset = dict(
            env_server.get_server_preset(str(preset_name or "")) or {}
        )
        site = dict(preset.get("site") or {})
        proxy = dict(preset.get("proxy") or {})
        values = {
            "serverUrl": str(preset.get("server") or ""),
            "presetName": str(preset_name or ""),
            "userName": str(preset.get("user") or ""),
            "siteEnabled": bool(site.get("enabled")),
            "siteName": str(site.get("site_name") or ""),
            "proxyEnabled": bool(proxy.get("enabled")),
            "proxyLogin": str(proxy.get("login") or ""),
            "proxyServer": str(proxy.get("server") or ""),
            "proxyPassword": "",
            "hasProxyPassword": bool(proxy.get("pass")),
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
        elif page_id == "checkinout_preferences":
            normalized = self._normalize_checkinout(values)
        elif page_id == "global_preferences":
            normalized = self._normalize_global(values)
        elif page_id == "tasks_preferences":
            normalized = self._normalize_tasks(values)
        elif page_id == "maya_preferences":
            normalized = self._normalize_maya(values)
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
            preset = dict(env_server.get_server_preset(preset_name) or {})
            preset_proxy = dict(preset.get("proxy") or {})
            env_server.set_user(str(values.get("userName") or ""))
            env_server.set_site(
                str(values.get("siteName") or ""),
                bool(values.get("siteEnabled")),
            )
            env_server.set_proxy(
                str(values.get("proxyLogin") or ""),
                str(values.get("proxyPassword") or "")
                or str(preset_proxy.get("pass") or ""),
                str(values.get("proxyServer") or ""),
                bool(values.get("proxyEnabled")),
            )
            self._apply_server_configuration(
                server_url, preset_name, True
            )
            if self._apply_background_configuration:
                self._apply_background_configuration(dict(values))
            for preset_page in (
                "checkin_preferences",
                "checkinout_preferences",
                "maya_preferences",
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
                self._apply_checkin_configuration()
        elif page_id == "checkinout_preferences":
            from thlib.environment import cfg_controls

            config = self._store_controls(
                cfg_controls.get_checkin_out() or {},
                values,
                _CHECKIN_OUT_CONTROLS,
            )
            cfg_controls.set_checkin_out(config)
            projects_config = copy.deepcopy(
                cfg_controls.get_checkin_out_projects() or {}
            )
            projects_config["!tabs_list!"] = [
                [tab["name"], tab["label"], bool(tab["enabled"])]
                for tab in values.get("globalTabs") or []
            ]
            for project in values.get("projects") or []:
                code = str(project.get("code") or "")
                if not code:
                    continue
                projects_config[code] = {
                    "tabs_list": [
                        [tab["name"], tab["label"], bool(tab["enabled"])]
                        for tab in project.get("tabs") or []
                    ],
                    "stypes_list": [
                        stype["code"]
                        for stype in project.get("searchTypes") or []
                        if stype.get("enabled")
                    ],
                }
            cfg_controls.set_checkin_out_projects(projects_config)
        elif page_id == "global_preferences":
            if self._apply_global_configuration:
                self._apply_global_configuration(dict(values))
        elif page_id == "tasks_preferences":
            if self._apply_task_configuration:
                self._apply_task_configuration(dict(values))
        elif page_id == "maya_preferences":
            if not values.get("saveFormat"):
                self._notify("Select a supported Maya scene format")
                return False
            from thlib.environment import cfg_controls

            format_index = (
                1 if values["saveFormat"] == "mayaBinary" else 0
            )
            cfg_controls.set_maya_scene({
                "QLineEdit": {
                    "obj_name": ["currentWorkdirLineEdit"],
                    "value": [values["currentWorkdir"]],
                },
                "QCheckBox": {
                    "obj_name": [
                        "createMayaDirsCheckBox",
                        "createPlayblastCheckBox",
                    ],
                    "value": [
                        int(values["createMayaDirs"]),
                        int(values["createPlayblast"]),
                    ],
                },
                "QComboBox": {
                    "obj_name": ["formatTypeComboBox"],
                    "value": [format_index],
                },
            })
        stored_values = dict(values)
        if page_id == "server":
            stored_values["proxyPassword"] = ""
            stored_values["hasProxyPassword"] = bool(
                values.get("proxyPassword")
                or values.get("hasProxyPassword")
            )
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
            "login": values["proxyLogin"],
            "pass": values["proxyPassword"]
            or str(preset_proxy.get("pass") or ""),
            "server": values["proxyServer"],
            "enabled": values["proxyEnabled"],
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
    def apply_current(self) -> bool:
        return self._apply_page(self._current_page)

    @Slot()
    def save_and_close(self) -> None:
        page_order = (
            "server",
            "global_preferences",
            "tasks_preferences",
            "checkin_preferences",
            "checkinout_preferences",
            "maya_preferences",
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
