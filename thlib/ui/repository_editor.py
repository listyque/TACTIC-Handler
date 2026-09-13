from __future__ import annotations

import copy
import os
from pathlib import Path

from PySide6.QtCore import QObject, Property, Signal, Slot

from .workspace_models.records import RecordListModel


_REPOSITORIES = (
    ("base", "asset_base_dir", "asset_base_dir"),
    ("client", "win32_client_repo_dir", "linux_client_repo_dir"),
    ("local", "win32_local_repo_dir", "linux_local_repo_dir"),
    ("sandbox", "win32_sandbox_dir", "linux_sandbox_dir"),
    ("client_handoff", "win32_client_handoff_dir", "linux_client_handoff_dir"),
    ("server_handoff", "win32_server_handoff_dir", "linux_server_handoff_dir"),
)


def _empty_base_dirs():
    defaults = {
        "asset_base_dir": ["", "General", (128, 128, 128), "base", True],
        "web_base_dir": ["", "Web", (128, 128, 128), "web", False],
    }
    for _alias, win_key, linux_key in _REPOSITORIES[1:]:
        title = _alias.replace("_", " ").title()
        active = _alias == "local"
        defaults[win_key] = ["", title, "", _alias, active]
        defaults[linux_key] = ["", title, "", _alias, active]
    return defaults


class RepositoryEditorController(QObject):
    dirtyChanged = Signal()
    busyChanged = Signal()
    messageChanged = Signal()
    configurationChanged = Signal()
    saved = Signal()

    def __init__(self, checkin_controller=None, workspace_state=None, parent=None):
        super().__init__(parent)
        self.model = RecordListModel((
            "alias", "title", "code", "windowsPath", "linuxPath", "active",
            "isDefault", "defaultEligible", "status", "statusText",
            "projectMapping", "selected", "custom", "color",
        ))
        self._checkin_controller = checkin_controller
        self._workspace_state = workspace_state
        self._original = {}
        self._original_records = []
        self._busy = False
        self._message = ""
        self._worker = None
        self._configuration_loaded = False
        self._configuration_required = False
        self._current_title = ""
        self._current_code = ""
        self._current_path = ""
        self._active_count = 0
        self.model.dataChanged.connect(self._model_changed)

    @Property(bool, notify=dirtyChanged)
    def dirty(self):
        return bool(self._original) and self._snapshot() != self._original

    @Property(bool, notify=busyChanged)
    def busy(self):
        return self._busy

    @Property(str, notify=messageChanged)
    def message(self):
        return self._message

    @Property(bool, notify=configurationChanged)
    def configuration_loaded(self):
        return self._configuration_loaded

    @Property(bool, notify=configurationChanged)
    def configuration_required(self):
        return self._configuration_required

    @Property(str, notify=configurationChanged)
    def current_title(self):
        return self._current_title

    @Property(str, notify=configurationChanged)
    def current_code(self):
        return self._current_code

    @Property(int, notify=configurationChanged)
    def active_count(self):
        return self._active_count

    @Property(str, notify=configurationChanged)
    def current_path(self):
        return self._current_path

    @staticmethod
    def _configuration_summary(records, platform_role):
        active = [record for record in records if record.get("active")]
        destinations = [
            record for record in active
            if record.get("defaultEligible", True)
        ]
        current = next(
            (record for record in destinations if record.get("isDefault")),
            destinations[0] if destinations else {},
        )
        path = str(current.get(platform_role) or "").strip()
        return {
            "configured": bool(path),
            "title": str(current.get("title") or ""),
            "code": str(current.get("code") or ""),
            "path": path,
            "activeCount": len(active),
        }

    def _set_configuration_summary(self, loaded, records):
        platform_role = "windowsPath" if os.name == "nt" else "linuxPath"
        summary = self._configuration_summary(records, platform_role)
        state = (
            bool(loaded),
            bool(loaded) and not summary["configured"],
            summary["title"],
            summary["code"],
            summary["path"],
            summary["activeCount"],
        )
        previous = (
            self._configuration_loaded,
            self._configuration_required,
            self._current_title,
            self._current_code,
            self._current_path,
            self._active_count,
        )
        (
            self._configuration_loaded,
            self._configuration_required,
            self._current_title,
            self._current_code,
            self._current_path,
            self._active_count,
        ) = state
        if state != previous:
            self.configurationChanged.emit()

    def _set_message(self, value):
        value = str(value or "")
        if value != self._message:
            self._message = value
            self.messageChanged.emit()

    def _snapshot(self):
        return [
            {
                key: record.get(key)
                for key in (
                    "alias", "title", "windowsPath", "linuxPath", "active",
                    "isDefault",
                    "code", "custom", "color",
                )
            }
            for record in self.model._records
        ]

    def _model_changed(self, *_args):
        defaults = [
            row for row, record in enumerate(self.model._records)
            if record.get("isDefault") and record.get("active")
        ]
        if len(defaults) > 1:
            keep = defaults[-1]
            for row in defaults[:-1]:
                self.model._records[row]["isDefault"] = False
                index = self.model.index(row, 0)
                self.model.dataChanged.emit(index, index)
        self.dirtyChanged.emit()

    @staticmethod
    def _value(base_dirs, key):
        value = list(base_dirs.get(key) or [])
        while len(value) < 5:
            value.append(False if len(value) == 4 else "")
        return value

    def _project_mapping(self, code):
        project = getattr(self._workspace_state, "_project", None)
        if not project:
            return "No current project mappings"
        try:
            from .workspace_models.watch_folders import _watch_folder_settings
            settings = _watch_folder_settings(project)
            names = list(settings.get("assets_names") or [])
            repositories = list(settings.get("repos") or [])
            mapped = [
                str(names[index])
                for index, values in enumerate(repositories)
                if code in (values or []) and index < len(names)
            ]
            project_name = project.get_code()
            return (
                f"{project_name}: {', '.join(mapped)}"
                if mapped else f"{project_name}: no watch folders"
            )
        except (AttributeError, KeyError, TypeError):
            return "Project mapping unavailable"

    @Slot()
    def begin_edit(self):
        from thlib.environment import cfg_controls, env_tactic
        import thlib.global_functions as gf

        configuration_loaded = env_tactic.base_dirs is not None
        base_dirs = copy.deepcopy(
            env_tactic.base_dirs or _empty_base_dirs()
        )
        custom_dirs = copy.deepcopy(env_tactic.get_custom_dirs() or {})
        windows_custom = custom_dirs.get("win32_custom_asset_dir") or {}
        linux_custom = custom_dirs.get("linux_custom_asset_dir") or {}
        active = []
        for alias, win_key, linux_key in _REPOSITORIES[:4]:
            current = self._value(
                base_dirs, win_key if os.name == "nt" else linux_key
            )
            if current[4]:
                active.append(alias)
        current_custom = windows_custom if os.name == "nt" else linux_custom
        if current_custom.get("enabled"):
            custom_paths = list(current_custom.get("path") or [])
            custom_visible = list(current_custom.get("visible") or [])
            custom_current = list(
                current_custom.get("current") or range(len(custom_paths))
            )
            active.extend(
                f"custom_{index}" for index in custom_current
                if 0 <= index < len(custom_paths)
                and (
                    index >= len(custom_visible)
                    or bool(custom_visible[index])
                )
            )
        try:
            default_index = int(gf.get_value_from_config(
                cfg_controls.get_checkin() or {}, "repositoryComboBox"
            ) or 0)
        except (TypeError, ValueError):
            default_index = 0
        default_alias = active[default_index] if 0 <= default_index < len(active) else ""

        records = []
        for row, (alias, win_key, linux_key) in enumerate(_REPOSITORIES):
            win_value = self._value(base_dirs, win_key)
            linux_value = self._value(base_dirs, linux_key)
            current = win_value if os.name == "nt" else linux_value
            records.append({
                "alias": alias,
                "title": str(current[1] or alias.replace("_", " ").title()),
                "code": str(current[3] or alias),
                "windowsPath": str(win_value[0] or ""),
                "linuxPath": str(linux_value[0] or ""),
                "active": bool(current[4]),
                "isDefault": alias == default_alias,
                "defaultEligible": row < 4,
                "status": "unchecked",
                "statusText": "Not checked",
                "projectMapping": self._project_mapping(str(current[3] or alias)),
                "selected": row == 0,
                "custom": False,
                "color": current[2] if len(current) > 2 else "",
            })
        custom_count = max(
            len(windows_custom.get("path") or []),
            len(linux_custom.get("path") or []),
            len(windows_custom.get("name") or []),
            len(linux_custom.get("name") or []),
        )
        for index in range(custom_count):
            win_paths = list(windows_custom.get("path") or [])
            linux_paths = list(linux_custom.get("path") or [])
            names = list(
                windows_custom.get("name")
                or linux_custom.get("name") or []
            )
            visible = list(
                (windows_custom if os.name == "nt" else linux_custom).get(
                    "visible"
                ) or []
            )
            colors = list(
                (windows_custom if os.name == "nt" else linux_custom).get(
                    "color"
                ) or []
            )
            alias = f"custom_{index}"
            enabled = bool(
                (windows_custom if os.name == "nt" else linux_custom).get(
                    "enabled"
                )
            ) and (index >= len(visible) or bool(visible[index]))
            records.append({
                "alias": alias,
                "title": str(names[index] if index < len(names) else alias),
                "code": alias,
                "windowsPath": str(
                    win_paths[index] if index < len(win_paths) else ""
                ),
                "linuxPath": str(
                    linux_paths[index] if index < len(linux_paths) else ""
                ),
                "active": enabled,
                "isDefault": alias == default_alias,
                "defaultEligible": True,
                "status": "unchecked",
                "statusText": "Not checked",
                "projectMapping": self._project_mapping(alias),
                "selected": False,
                "custom": True,
                "color": colors[index] if index < len(colors) else "",
            })
        self.model.replace(records)
        self._original = self._snapshot()
        self._original_records = copy.deepcopy(records)
        self._set_message("")
        self._set_configuration_summary(configuration_loaded, records)
        self.dirtyChanged.emit()

    @Slot()
    def cancel(self):
        if self._original_records:
            self.model.replace(copy.deepcopy(self._original_records))
        self._set_message("")
        self.dirtyChanged.emit()

    @Slot()
    def add_custom_repository(self):
        custom_count = sum(
            1 for record in self.model._records if record.get("custom")
        )
        index = custom_count
        used = {record.get("alias") for record in self.model._records}
        while f"custom_{index}" in used:
            index += 1
        records = list(self.model._records)
        records.append({
            "alias": f"custom_{index}",
            "title": "Custom repository",
            "code": f"custom_{index}",
            "windowsPath": "",
            "linuxPath": "",
            "active": False,
            "isDefault": False,
            "defaultEligible": True,
            "status": "unchecked",
            "statusText": "Not checked",
            "projectMapping": self._project_mapping(f"custom_{index}"),
            "selected": False,
            "custom": True,
            "color": "",
        })
        self.model.replace(records)
        self.dirtyChanged.emit()

    @Slot(int)
    def remove_custom_repository(self, row):
        if not 0 <= row < len(self.model._records):
            return
        if not self.model._records[row].get("custom"):
            return
        records = list(self.model._records)
        records.pop(row)
        self.model.replace(records)
        self.dirtyChanged.emit()

    @staticmethod
    def _check_paths(paths):
        result = {}
        for key, raw_path in paths.items():
            path = Path(str(raw_path or "")).expanduser()
            exists = path.is_dir()
            readable = exists and os.access(path, os.R_OK)
            writable = exists and os.access(path, os.W_OK)
            result[key] = {
                "ok": bool(readable and writable),
                "text": (
                    "Available" if readable and writable
                    else "Read only" if readable
                    else "Folder not found or inaccessible"
                ),
            }
        return result

    @Slot()
    def check_paths(self):
        if self._busy:
            return
        from thlib.environment import env_inst

        paths = {}
        platform_role = "windowsPath" if os.name == "nt" else "linuxPath"
        for record in self.model._records:
            if record.get("active"):
                paths[record["alias"]] = record.get(platform_role)
        self._busy = True
        self.busyChanged.emit()
        self._worker = env_inst.local_pool.add_task(self._check_paths, paths)
        self._worker.result.connect(self._paths_checked)
        self._worker.error.connect(self._path_check_failed)
        self._worker.start()

    @Slot(object)
    def _paths_checked(self, result):
        for row, record in enumerate(self.model._records):
            status = result.get(record["alias"])
            if not status:
                continue
            record["status"] = "available" if status["ok"] else "unavailable"
            record["statusText"] = status["text"]
            index = self.model.index(row, 0)
            self.model.dataChanged.emit(index, index)
        self._busy = False
        self._worker = None
        self.busyChanged.emit()

    @Slot(object)
    def _path_check_failed(self, error):
        self._busy = False
        self._worker = None
        self._set_message(str(error or "Path check failed"))
        self.busyChanged.emit()

    @staticmethod
    def _set_checkin_default(index):
        from thlib.environment import cfg_controls

        config = copy.deepcopy(cfg_controls.get_checkin() or {})
        combo = config.setdefault("QComboBox", {"obj_name": [], "value": []})
        names = list(combo.get("obj_name") or [])
        values = list(combo.get("value") or [])
        if "repositoryComboBox" in names:
            row = names.index("repositoryComboBox")
            while len(values) <= row:
                values.append(0)
            values[row] = index
        else:
            names.append("repositoryComboBox")
            values.append(index)
        combo["obj_name"] = names
        combo["value"] = values
        cfg_controls.set_checkin(config)

    @Slot(result=bool)
    def save(self):
        from thlib.environment import env_tactic

        current_role = "windowsPath" if os.name == "nt" else "linuxPath"
        active_records = [
            record for record in self.model._records if record.get("active")
        ]
        if not active_records:
            self._set_message("Enable at least one repository.")
            return False
        invalid = [
            record["title"] for record in active_records
            if not Path(str(record.get(current_role) or "")).expanduser().is_dir()
        ]
        if invalid:
            self._set_message(
                "Unavailable repository path: " + ", ".join(invalid)
            )
            return False

        base_dirs = copy.deepcopy(
            env_tactic.base_dirs or _empty_base_dirs()
        )
        fixed_records = {
            record["alias"]: record for record in self.model._records
            if not record.get("custom")
        }
        for alias, win_key, linux_key in _REPOSITORIES:
            record = fixed_records[alias]
            if win_key == linux_key:
                value = self._value(base_dirs, win_key)
                value[0] = str(record.get(current_role) or "")
                value[1] = str(record.get("title") or "")
                value[3] = str(record.get("code") or record["alias"])
                value[4] = bool(record.get("active"))
                base_dirs[win_key] = value
                continue
            for key, role in ((win_key, "windowsPath"), (linux_key, "linuxPath")):
                value = self._value(base_dirs, key)
                value[0] = str(record.get(role) or "")
                value[1] = str(record.get("title") or "")
                value[3] = str(record.get("code") or record["alias"])
                value[4] = bool(record.get("active"))
                base_dirs[key] = value
        env_tactic.base_dirs = base_dirs
        env_tactic.save_base_dirs()

        custom_records = [
            record for record in self.model._records if record.get("custom")
        ]
        custom_dirs = {}
        for key, role in (
            ("win32_custom_asset_dir", "windowsPath"),
            ("linux_custom_asset_dir", "linuxPath"),
        ):
            custom_dirs[key] = {
                "path": [str(record.get(role) or "") for record in custom_records],
                "name": [str(record.get("title") or "") for record in custom_records],
                "current": list(range(len(custom_records))),
                "visible": [bool(record.get("active")) for record in custom_records],
                "color": [record.get("color") or "" for record in custom_records],
                "enabled": any(record.get("active") for record in custom_records),
            }
        env_tactic.custom_dirs = custom_dirs
        env_tactic.save_custom_dirs()

        default_records = [
            record for record in self.model._records
            if record.get("active") and record.get("defaultEligible")
        ]
        default_index = 0
        for index, record in enumerate(default_records):
            if record.get("isDefault"):
                default_index = index
                break
        self._set_checkin_default(default_index)
        if self._checkin_controller:
            self._checkin_controller.reload_repository_configuration()
        self._original = self._snapshot()
        self._original_records = copy.deepcopy(self.model._records)
        self._set_configuration_summary(True, self.model._records)
        self._set_message("Repository settings saved.")
        self.dirtyChanged.emit()
        self.saved.emit()
        return True
