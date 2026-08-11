from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Property, QUrl, Qt, Signal, Slot

from .workspace_models.records import RecordListModel
from .workspace_models.watch_folders import _watch_folder_settings


_FIELDS = (
    "assets_codes", "assets_names", "assets_stypes", "assets_skeys",
    "assets_pipelines", "paths", "repos", "statuses", "processes",
    "contexts", "matching_templates", "last_checks", "errors",
)


class WatchFoldersController(QObject):
    stateChanged = Signal()
    editorChanged = Signal()

    def __init__(
        self, application, drop_plate, matching_templates, parent=None
    ):
        super().__init__(parent)
        self._application = application
        self._workspace = application.workspace_state
        self._drop_plate = drop_plate
        self._matching_templates = matching_templates
        self._project = None
        self._observer = None
        self._observer_owned = False
        self._observer_started = False
        self._editor = {}
        self._editing_row = -1
        self._busy = False
        self._message = ""
        self._workers = set()
        self.model = RecordListModel((
            "title", "code", "searchKey", "stype", "path", "watchEnabled", "repository",
            "repositories", "pipeline", "process", "context",
            "matchingTemplate", "watcherStatus", "lastCheck", "error",
            "selected",
        ))
        application.project_state_changed.connect(self.reload)
        self._workspace.selection_changed.connect(self.editorChanged)

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._busy

    @Property(str, notify=stateChanged)
    def message(self):
        return self._message

    @Property("QVariantMap", notify=editorChanged)
    def editor(self):
        return dict(self._editor)

    @Property("QVariantList", notify=stateChanged)
    def repositories(self):
        from thlib.environment import env_tactic

        result = []
        for alias, repository in env_tactic.get_all_base_dirs():
            values = repository.get("value") or []
            if len(values) > 4 and values[4]:
                result.append({
                    "label": str(values[1] or alias),
                    "value": str(values[3] or alias),
                })
        return result

    @Property("QVariantList", notify=stateChanged)
    def matchingTemplates(self):
        return [
            {
                "label": str(record.get("pattern") or ""),
                "value": str(record.get("pattern") or ""),
            }
            for record in self._matching_templates.model._records
            if record.get("templateEnabled")
        ]

    @staticmethod
    def _value(values, key, row, default=""):
        items = list(values.get(key) or [])
        return items[row] if row < len(items) else default

    @staticmethod
    def _empty_settings():
        return {key: [] for key in _FIELDS}

    def _settings(self):
        settings = self._empty_settings()
        source = _watch_folder_settings(self._project)
        for key in _FIELDS:
            settings[key] = list(source.get(key) or [])
        return settings

    def _observer_for_project(self):
        from thlib.environment import env_inst
        import thlib.global_functions as gf

        if not self._project:
            return None
        code = self._project.get_code()
        existing = env_inst.watch_folders.get(code)
        if existing is not None and existing is not self:
            observer = getattr(existing, "fs_watcher", None)
            if observer:
                self._observer = observer
                self._observer_owned = False
                return observer
        if self._observer is None:
            self._observer = gf.FSObserver()
            self._observer.set_created_signal(self._watch_created)
            self._observer_owned = True
        env_inst.watch_folders[code] = self
        return self._observer

    @Slot()
    def reload(self):
        project = getattr(self._workspace, "_project", None)
        if project is not self._project:
            previous = self._project
            self._remove_all_watches()
            if previous:
                try:
                    from thlib.environment import env_inst
                    if env_inst.watch_folders.get(previous.get_code()) is self:
                        env_inst.watch_folders.pop(previous.get_code(), None)
                except (AttributeError, KeyError, TypeError) as error:
                    self._message = str(error)
            self._project = project
            self._observer_for_project()
        values = self._settings()
        count = len(values["assets_skeys"])
        records = []
        for row in range(count):
            repos = list(self._value(values, "repos", row, []))
            enabled = bool(self._value(values, "statuses", row, False))
            error = str(self._value(values, "errors", row, ""))
            record = {
                "title": str(self._value(values, "assets_names", row)),
                "code": str(self._value(values, "assets_codes", row)),
                "searchKey": str(self._value(values, "assets_skeys", row)),
                "stype": str(self._value(values, "assets_stypes", row)),
                "path": str(self._value(values, "paths", row)),
                "watchEnabled": enabled,
                "repository": ", ".join(repos),
                "repositories": repos,
                "pipeline": str(self._value(
                    values, "assets_pipelines", row
                )),
                "process": str(self._value(
                    values, "processes", row, "publish"
                ) or "publish"),
                "context": str(self._value(
                    values, "contexts", row, "publish"
                ) or "publish"),
                "matchingTemplate": str(self._value(
                    values, "matching_templates", row, "$FILENAME.$EXT"
                ) or "$FILENAME.$EXT"),
                "watcherStatus": "Stopped",
                "lastCheck": str(self._value(
                    values, "last_checks", row, "Never"
                ) or "Never"),
                "error": error,
                "selected": False,
            }
            records.append(record)
        self.model.replace(records)
        for row, record in enumerate(records):
            if record["watchEnabled"]:
                self._start_row(row)
        self.stateChanged.emit()

    def get_watch_dict_by_skey(self, search_key):
        for row, record in enumerate(self.model._records):
            if record["searchKey"] == search_key:
                return {
                    "asset_code": "",
                    "asset_name": record["title"],
                    "asset_stype": record["stype"],
                    "asset_skey": search_key,
                    "asset_pipeline": record["pipeline"],
                    "path": record["path"],
                    "rep": list(record["repositories"]),
                    "status": record["watchEnabled"],
                    "idx": row,
                }
        return None

    def _absolute_paths(self, record):
        from thlib.environment import env_tactic
        import thlib.global_functions as gf

        paths = []
        repos = []
        for code in record.get("repositories") or []:
            repository = env_tactic.get_base_dir(code) or {}
            values = repository.get("value") or []
            if not values or not values[0]:
                continue
            paths.append(gf.form_path(os.path.join(
                str(values[0]), str(record.get("path") or "")
            )))
            repos.append(code)
        return paths, repos

    def _set_row_state(self, row, status, error=""):
        if not 0 <= row < len(self.model._records):
            return
        record = self.model._records[row]
        record["watcherStatus"] = status
        record["error"] = str(error or "")
        index = self.model.index(row, 0)
        self.model.dataChanged.emit(index, index)
        self.stateChanged.emit()

    def _start_row(self, row):
        if not 0 <= row < len(self.model._records):
            return False
        observer = self._observer_for_project()
        if not observer:
            self._set_row_state(row, "Error", "Watcher is unavailable")
            return False
        record = self.model._records[row]
        paths, repos = self._absolute_paths(record)
        missing = [path for path in paths if not Path(path).is_dir()]
        if not paths or missing:
            self._set_row_state(
                row, "Waiting",
                "Folder not found: " + ", ".join(missing[:2])
                if missing else "No active repository is selected",
            )
            return False
        try:
            observer.append_watch(
                watch_name=record["searchKey"], paths=paths, repos=repos,
                pipeline=record["pipeline"], recursive=True,
            )
            if not observer.is_started():
                observer.start()
            self._observer_started = True
            self._set_row_state(row, "Watching")
            return True
        except (OSError, RuntimeError, ValueError) as error:
            self._set_row_state(row, "Error", str(error))
            return False

    def _stop_row(self, row):
        if not 0 <= row < len(self.model._records):
            return
        try:
            if self._observer:
                self._observer.remove_watch(
                    self.model._records[row]["searchKey"]
                )
            self._set_row_state(row, "Stopped")
        except (OSError, RuntimeError, ValueError) as error:
            self._set_row_state(row, "Error", str(error))

    def _remove_all_watches(self):
        if not self._observer:
            return
        for record in list(self.model._records):
            try:
                self._observer.remove_watch(record["searchKey"])
            except (OSError, RuntimeError, ValueError) as error:
                self._message = str(error)

    @Slot(int, bool)
    def set_enabled(self, row, enabled):
        if not 0 <= row < len(self.model._records):
            return
        self.model._records[row]["watchEnabled"] = bool(enabled)
        if enabled:
            self._start_row(row)
        else:
            self._stop_row(row)
        self._persist()

    def _selected_source(self):
        return getattr(self._workspace, "_selected_sobject", None)

    @Slot()
    def begin_add(self):
        sobject = self._selected_source()
        if not sobject:
            self._message = "Select an sObject before adding a watch folder."
            self.stateChanged.emit()
            return
        try:
            search_key = str(sobject.get_search_key() or "")
            info = dict(sobject.get_info() or {})
            pipeline = str(sobject.get_pipeline_code() or "")
            title = str(sobject.get_title() or info.get("name") or info.get("code"))
            code = str(info.get("code") or "")
            stype = sobject.get_stype()
            stype_title = str(stype.get_pretty_name() if stype else "")
        except (AttributeError, KeyError, TypeError) as error:
            self._message = str(error)
            self.stateChanged.emit()
            return
        self._editing_row = -1
        self._editor = {
            "title": title, "code": code, "searchKey": search_key,
            "stype": stype_title, "pipeline": pipeline, "path": "",
            "repositories": [
                item["value"] for item in self.repositories[:1]
            ],
            "process": "publish", "context": "publish",
            "matchingTemplate": "$FILENAME.$EXT", "watchEnabled": True,
        }
        self._message = ""
        self.editorChanged.emit()
        self._load_naming_path(search_key)

    @Slot(int)
    def begin_edit(self, row):
        if not 0 <= row < len(self.model._records):
            return
        self._editing_row = row
        self._editor = dict(self.model._records[row])
        self.editorChanged.emit()

    @Slot(str, "QVariant")
    def set_editor_value(self, key, value):
        if key not in {
            "path", "repositories", "process", "context",
            "matchingTemplate", "watchEnabled",
        }:
            return
        self._editor[key] = value
        self.editorChanged.emit()

    @Slot(str, bool)
    def toggle_editor_repository(self, repository, enabled):
        values = list(self._editor.get("repositories") or [])
        repository = str(repository or "")
        if enabled and repository not in values:
            values.append(repository)
        elif not enabled and repository in values:
            values.remove(repository)
        self._editor["repositories"] = values
        self.editorChanged.emit()

    @Slot()
    def cancel_edit(self):
        self._editing_row = -1
        self._editor = {}
        self._message = ""
        self.editorChanged.emit()
        self.stateChanged.emit()

    def _load_naming_path(self, search_key):
        from thlib.environment import env_inst
        import thlib.tactic_classes as tc

        self._busy = True
        self.stateChanged.emit()
        worker = env_inst.server_pool.add_task(
            tc.get_dirs_with_naming, search_key,
            process_list=["watch_folder"],
        )
        self._workers.add(worker)
        worker.result.connect(
            lambda result, current=worker: self._naming_ready(current, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error, current=worker: self._worker_failed(current, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    def _naming_ready(self, worker, result):
        self._workers.discard(worker)
        try:
            self._editor["path"] = str(
                ((result or {}).get("versionless") or [""])[0]
            )
        except (IndexError, TypeError):
            self._editor["path"] = ""
        self._busy = bool(self._workers)
        self.editorChanged.emit()
        self.stateChanged.emit()

    def _worker_failed(self, worker, error):
        self._workers.discard(worker)
        payload = error[0] if isinstance(error, tuple) and error else error
        if isinstance(payload, dict):
            payload = payload.get("exception") or payload
        self._message = str(payload or "Watch folder operation failed")
        self._busy = bool(self._workers)
        self.stateChanged.emit()

    @Slot(result=bool)
    def save_edit(self):
        editor = dict(self._editor)
        path = str(editor.get("path") or "").strip().replace("\\", "/")
        repos = [str(value) for value in editor.get("repositories") or []]
        if (
            not editor.get("searchKey") or not path or not repos
            or Path(path).is_absolute() or ".." in Path(path).parts
        ):
            self._message = (
                "Choose repositories and enter a safe relative watch path."
            )
            self.stateChanged.emit()
            return False
        if self._editing_row >= 0:
            self._stop_row(self._editing_row)
            self.model._records[self._editing_row].update({
                "path": path,
                "repositories": repos,
                "repository": ", ".join(repos),
                "process": str(editor.get("process") or "publish"),
                "context": str(editor.get("context") or "publish"),
                "matchingTemplate": str(
                    editor.get("matchingTemplate") or "$FILENAME.$EXT"
                ),
                "watchEnabled": bool(editor.get("watchEnabled")),
            })
            row = self._editing_row
            self.model.replace(self.model._records)
        else:
            if any(
                record["searchKey"] == editor["searchKey"]
                for record in self.model._records
            ):
                self._message = "This sObject already has a watch folder."
                self.stateChanged.emit()
                return False
            row = len(self.model._records)
            self.model.replace(self.model._records + [{
                "title": str(editor.get("title") or ""),
                "code": str(editor.get("code") or ""),
                "searchKey": str(editor.get("searchKey") or ""),
                "stype": str(editor.get("stype") or ""),
                "path": path,
                "watchEnabled": bool(editor.get("watchEnabled")),
                "repository": ", ".join(repos), "repositories": repos,
                "pipeline": str(editor.get("pipeline") or ""),
                "process": str(editor.get("process") or "publish"),
                "context": str(editor.get("context") or "publish"),
                "matchingTemplate": str(
                    editor.get("matchingTemplate") or "$FILENAME.$EXT"
                ),
                "watcherStatus": "Waiting", "lastCheck": "Never",
                "error": "", "selected": False,
            }])
        self._persist()
        self._create_paths(row)
        self.cancel_edit()
        return True

    def _create_paths(self, row):
        from thlib.environment import env_inst

        paths, _repos = self._absolute_paths(self.model._records[row])
        worker = env_inst.local_pool.add_task(self._mkdirs, paths)
        self._workers.add(worker)
        self._busy = True
        worker.result.connect(
            lambda _result, current=worker, item=row:
                self._paths_ready(current, item),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error, current=worker: self._worker_failed(current, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()
        self.stateChanged.emit()

    @staticmethod
    def _mkdirs(paths):
        for value in paths:
            Path(value).mkdir(parents=True, exist_ok=True)
        return True

    def _paths_ready(self, worker, row):
        self._workers.discard(worker)
        self._busy = bool(self._workers)
        if 0 <= row < len(self.model._records):
            if self.model._records[row]["watchEnabled"]:
                self._start_row(row)
        self.stateChanged.emit()

    @Slot(int)
    def remove(self, row):
        if not 0 <= row < len(self.model._records):
            return
        self._stop_row(row)
        self.model.remove(row)
        self._persist()
        self.cancel_edit()

    @Slot(int)
    def scan(self, row):
        if not 0 <= row < len(self.model._records):
            return
        record = self.model._records[row]
        paths, _repos = self._absolute_paths(record)
        available = [QUrl.fromLocalFile(path) for path in paths if Path(path).is_dir()]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record["lastCheck"] = now
        if not available:
            record["error"] = "No accessible repository paths"
            record["watcherStatus"] = "Error"
        else:
            self._drop_plate.add_watch_paths(
                available, record["process"], record["context"],
                [record["matchingTemplate"]],
            )
            self._application.dock_model.show_panel("drop_plate")
            record["error"] = ""
        self.model.replace(self.model._records)
        self._persist()

    @Slot(object, object)
    def _watch_created(self, event, watch):
        path = str(getattr(event, "src_path", "") or "")
        if not path or bool(getattr(event, "is_directory", False)):
            return
        row = next((
            index for index, record in enumerate(self.model._records)
            if record["searchKey"] == getattr(watch, "watch_name", "")
        ), -1)
        if row < 0:
            return
        record = self.model._records[row]
        record["lastCheck"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.model.replace(self.model._records)
        self._persist()
        self._drop_plate.add_watch_paths(
            [QUrl.fromLocalFile(path)], record["process"], record["context"],
            [record["matchingTemplate"]],
        )
        self._application.dock_model.show_panel("drop_plate")

    def _persist(self):
        if not self._project:
            return
        from thlib.environment import env_write_config

        settings = self._empty_settings()
        for record in self.model._records:
            values = {
                "assets_codes": record.get("code") or "",
                "assets_names": record["title"],
                "assets_stypes": record["stype"],
                "assets_skeys": record["searchKey"],
                "assets_pipelines": record["pipeline"],
                "paths": record["path"],
                "repos": list(record["repositories"]),
                "statuses": bool(record["watchEnabled"]),
                "processes": record["process"],
                "contexts": record["context"],
                "matching_templates": record["matchingTemplate"],
                "last_checks": record["lastCheck"],
                "errors": record["error"],
            }
            for key, value in values.items():
                settings[key].append(value)
        env_write_config(
            {"watch_folders_dict": settings},
            filename="ui_watch_folder",
            unique_id=(
                f"ui_main/{self._project.get_type()}/"
                f"{self._project.get_code()}"
            ),
            long_abs_path=True,
        )

    @Slot()
    def shutdown(self):
        self._remove_all_watches()
        if self._observer_owned and self._observer and self._observer.is_started():
            self._observer.stop()
            try:
                self._observer.join(2)
            except (RuntimeError, TimeoutError) as error:
                self._message = str(error)
