from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path

from PySide6.QtCore import QObject, Property, QTimer, Qt, Signal, Slot

from .workspace_models.records import RecordListModel
from .workspace_models.watch_folders import _watch_folder_settings


_FIELDS = (
    "assets_codes", "assets_names", "assets_stypes", "assets_skeys",
    "assets_pipelines", "paths", "repos", "statuses",
)


class WatchFoldersController(QObject):
    stateChanged = Signal()
    editorChanged = Signal()
    canSaveEditorChanged = Signal()
    deleteChanged = Signal()

    def __init__(
        self, application, checkin_controller, commit_queue, parent=None
    ):
        super().__init__(parent)
        self._application = application
        self._workspace = application.workspace_state
        self._checkin = checkin_controller
        self._commit_queue = commit_queue
        self._project = None
        self._observer = None
        self._observer_owned = False
        self._observer_started = False
        self._editor = {}
        self._editor_origin = ""
        self._editing_row = -1
        self._delete_row = -1
        self._delete_origin = ""
        self._busy = False
        self._message = ""
        self._presentation_visible = False
        self._selection_presentation_dirty = False
        self._workers = set()
        self._repository_retry_timer = QTimer(self)
        self._repository_retry_timer.setSingleShot(True)
        self._repository_retry_timer.setInterval(1000)
        self._repository_retry_timer.timeout.connect(
            self._retry_repository_starts
        )
        self.model = RecordListModel((
            "title", "code", "searchKey", "stype", "path", "watchEnabled",
            "repository", "repositories", "pipeline", "watcherStatus",
            "selected",
        ))
        self.editorChanged.connect(self.canSaveEditorChanged.emit)
        self.stateChanged.connect(self.canSaveEditorChanged.emit)
        application.project_state_changed.connect(self.reload)
        self._workspace.selection_changed.connect(
            self._workspace_selection_changed
        )

    def _workspace_selection_changed(self):
        if not self._presentation_visible:
            self._selection_presentation_dirty = True
            return
        self.editorChanged.emit()

    @Slot(bool)
    def set_presentation_visible(self, value):
        value = bool(value)
        if value == self._presentation_visible:
            return
        self._presentation_visible = value
        if value and self._selection_presentation_dirty:
            self._selection_presentation_dirty = False
            self.editorChanged.emit()

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._busy

    @Property(str, notify=stateChanged)
    def message(self):
        return self._message

    @Property("QVariantMap", notify=editorChanged)
    def editor(self):
        return dict(self._editor)

    @Property(bool, notify=editorChanged)
    def editorOpen(self):
        return bool(self._editor)

    @Property(str, notify=editorChanged)
    def editorOrigin(self):
        return self._editor_origin

    @Property(bool, notify=editorChanged)
    def editingExisting(self):
        return self._editing_row >= 0

    @Property(bool, notify=deleteChanged)
    def deletePending(self):
        return self._delete_row >= 0

    @Property(str, notify=deleteChanged)
    def deleteOrigin(self):
        return self._delete_origin

    @Property(bool, notify=canSaveEditorChanged)
    def canSaveEditor(self):
        path = str(self._editor.get("path") or "").strip()
        repositories = list(self._editor.get("repositories") or [])
        removing_existing = self._removing_existing_editor(repositories)
        return bool(
            self._editor.get("searchKey")
            and not self._busy
            and (
                removing_existing
                or (
                    path and repositories
                    and not Path(path).is_absolute()
                    and ".." not in Path(path).parts
                )
            )
        )

    def _removing_existing_editor(self, repositories):
        if repositories:
            return False
        if not 0 <= self._editing_row < len(self.model._records):
            return False
        return (
            str(self._editor.get("searchKey") or "")
            == str(self.model._records[self._editing_row]["searchKey"])
        )

    @Property("QVariantList", notify=stateChanged)
    def repositories(self):
        from thlib.environment import env_tactic

        result = []
        try:
            repositories = env_tactic.get_all_base_dirs() or []
        except (AttributeError, KeyError, TypeError):
            repositories = []
        for alias, repository in repositories:
            values = repository.get("value") or []
            if len(values) > 4 and values[4]:
                result.append({
                    "label": str(values[1] or alias),
                    "value": str(values[3] or alias),
                })
        return result

    def _repository_labels(self, codes):
        labels = {item["value"]: item["label"] for item in self.repositories}
        return [labels.get(str(code), str(code)) for code in codes]

    def _publish_watch_state(self, search_key, enabled=None):
        model = getattr(self._application, "workspace_model", None)
        update = getattr(model, "update_watch_state", None)
        if not callable(update):
            return
        state = "none" if enabled is None else (
            "enabled" if bool(enabled) else "disabled"
        )
        update(str(search_key or ""), state)
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
            record = {
                "title": str(self._value(values, "assets_names", row)),
                "code": str(self._value(values, "assets_codes", row)),
                "searchKey": str(self._value(values, "assets_skeys", row)),
                "stype": str(self._value(values, "assets_stypes", row)),
                "path": str(self._value(values, "paths", row)),
                "watchEnabled": enabled,
                "repository": ", ".join(self._repository_labels(repos)),
                "repositories": repos,
                "pipeline": str(self._value(
                    values, "assets_pipelines", row
                )),
                "watcherStatus": "Stopped",
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
                    "asset_code": record["code"],
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
        if getattr(env_tactic, "base_dirs", None) is None:
            return paths, repos, True
        for code in record.get("repositories") or []:
            try:
                repository = env_tactic.get_base_dir(code) or {}
            except (AttributeError, KeyError, TypeError):
                continue
            values = repository.get("value") or []
            if not values or not values[0]:
                continue
            paths.append(gf.form_path(os.path.join(
                str(values[0]), str(record.get("path") or "")
            )))
            repos.append(code)
        return paths, repos, False

    def _schedule_repository_retry(self):
        if not self._repository_retry_timer.isActive():
            self._repository_retry_timer.start()

    @Slot()
    def _retry_repository_starts(self):
        if not self._project:
            return
        for row, record in enumerate(list(self.model._records)):
            if (
                record.get("watchEnabled")
                and record.get("watcherStatus") != "Watching"
            ):
                self._start_row(row)

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
            self._set_row_state(row, "Waiting", "Watcher is unavailable")
            return False
        record = self.model._records[row]
        paths, repos, pending = self._absolute_paths(record)
        if pending:
            self._set_row_state(
                row, "Waiting", "Repository configuration is loading"
            )
            self._schedule_repository_retry()
            return False
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
            self._set_row_state(row, "Waiting", str(error))
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
            self._set_row_state(row, "Waiting", str(error))

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
        self._publish_watch_state(
            self.model._records[row]["searchKey"], enabled
        )

    def _selected_source(self):
        return getattr(self._workspace, "_selected_sobject", None)

    @staticmethod
    def _process_names(sobject):
        builtins = ["icon", "attachment", "publish"]
        try:
            stype = sobject.get_stype()
            pipelines = stype.get_pipeline() or {}
            pipeline = pipelines.get(sobject.get_pipeline_code())
            if not pipeline:
                return builtins
            names = list(pipeline.get_all_pipeline_names() or [])
            workflow = stype.get_workflow()
            for process, info in (pipeline.pipeline or {}).items():
                if info.get("type") != "hierarchy":
                    continue
                child = workflow.get_child_pipeline_by_process_code(
                    pipeline, process
                )
                if child:
                    names.extend(child.get_all_pipeline_names() or [])
            return list(dict.fromkeys(str(name) for name in names if name))
        except (AttributeError, KeyError, TypeError):
            return builtins

    @Slot()
    def begin_add(self):
        self.begin_add_for_source(self._selected_source(), "manager")

    def _show_editor_window(self):
        model = getattr(self._application, "window_model", None)
        if model is not None:
            model.show_window("watch_folder_editor")

    def _close_editor_window(self):
        model = getattr(self._application, "window_model", None)
        if model is not None:
            model.close_window("watch_folder_editor")

    def begin_add_for_source(self, sobject, origin="item"):
        if not sobject:
            self._message = "Select an sObject before adding a watch folder."
            self.stateChanged.emit()
            return
        try:
            search_key = str(sobject.get_search_key() or "")
            info = dict(sobject.get_info() or {})
            pipeline = str(sobject.get_pipeline_code() or "")
            title = str(
                sobject.get_title() or info.get("name") or info.get("code")
            )
            code = str(info.get("code") or "")
            stype = sobject.get_stype()
            stype_title = str(stype.get_pretty_name() if stype else "")
            processes = self._process_names(sobject)
        except (AttributeError, KeyError, TypeError) as error:
            self._message = str(error)
            self.stateChanged.emit()
            return
        existing = next((
            row for row, record in enumerate(self.model._records)
            if record["searchKey"] == search_key
        ), -1)
        if existing >= 0:
            self._begin_edit(existing, origin)
            return
        self._editing_row = -1
        self._editor_origin = str(origin or "item")
        self._editor = {
            "title": title, "code": code, "searchKey": search_key,
            "stype": stype_title, "pipeline": pipeline, "path": "",
            "repositories": [], "watchEnabled": True,
            "processes": processes,
        }
        self._message = ""
        self.editorChanged.emit()
        self._show_editor_window()
        self._load_naming_path(search_key)

    @Slot(str)
    @Slot(str, str)
    def begin_edit_search_key(self, search_key, origin="item"):
        row = next((
            index for index, record in enumerate(self.model._records)
            if record["searchKey"] == str(search_key or "")
        ), -1)
        if row >= 0:
            self._begin_edit(row, origin)

    @Slot(int)
    def begin_edit(self, row):
        self._begin_edit(row, "manager")

    def _begin_edit(self, row, origin):
        if not 0 <= row < len(self.model._records):
            return
        self._editing_row = row
        self._editor_origin = str(origin or "manager")
        self._editor = dict(self.model._records[row])
        self.editorChanged.emit()
        self._show_editor_window()

    @Slot(str, "QVariant")
    def set_editor_value(self, key, value):
        if key not in {"path", "repositories", "watchEnabled"}:
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
        self._editor_origin = ""
        self._message = ""
        self.editorChanged.emit()
        self.stateChanged.emit()
        self._close_editor_window()

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
            lambda result, current=worker, key=search_key:
                self._naming_ready(current, result, key),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error, current=worker: self._worker_failed(current, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    def _naming_ready(self, worker, result, search_key):
        self._workers.discard(worker)
        if self._editor.get("searchKey") == search_key:
            try:
                self._editor["path"] = str(
                    ((result or {}).get("versionless") or [""])[0]
                )
            except (IndexError, TypeError):
                self._editor["path"] = ""
            self.editorChanged.emit()
        self._busy = bool(self._workers)
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
        removing_existing = self._removing_existing_editor(repos)
        if removing_existing:
            removed = self._remove_record(self._editing_row)
            self.cancel_edit()
            return bool(removed)
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
                "repository": ", ".join(self._repository_labels(repos)),
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
                "repository": ", ".join(self._repository_labels(repos)), "repositories": repos,
                "pipeline": str(editor.get("pipeline") or ""),
                "watcherStatus": "Waiting", "selected": False,
            }])
        self._persist()
        self._publish_watch_state(
            editor["searchKey"], editor.get("watchEnabled")
        )
        self._create_paths(row, editor.get("processes") or [])
        self.cancel_edit()
        return True

    def _process_names_for_record(self, record):
        try:
            import thlib.tactic_classes as tc
            parsed = tc.split_search_key(record["searchKey"])
            stype = (self._project.get_stypes() or {}).get(
                parsed.get("search_type")
            )
            pipeline = (stype.get_pipeline() or {}).get(record["pipeline"])
            if not pipeline:
                return ["icon", "attachment", "publish"]
            names = list(pipeline.get_all_pipeline_names() or [])
            workflow = stype.get_workflow()
            for process, info in (pipeline.pipeline or {}).items():
                if info.get("type") != "hierarchy":
                    continue
                child = workflow.get_child_pipeline_by_process_code(
                    pipeline, process
                )
                if child:
                    names.extend(child.get_all_pipeline_names() or [])
            return list(dict.fromkeys(str(name) for name in names if name))
        except (AttributeError, KeyError, TypeError, ValueError):
            return []

    def _create_paths(self, row, processes=None):
        from thlib.environment import env_inst

        if not 0 <= row < len(self.model._records):
            return
        record = self.model._records[row]
        paths, _repos, pending = self._absolute_paths(record)
        if pending:
            self._set_row_state(
                row, "Waiting", "Repository configuration is loading"
            )
            self._schedule_repository_retry()
            return
        process_names = list(processes or self._process_names_for_record(record))
        worker = env_inst.local_pool.add_task(
            self._mkdirs, paths, process_names
        )
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
    def _mkdirs(paths, processes):
        for value in paths:
            root = Path(value)
            root.mkdir(parents=True, exist_ok=True)
            for process in processes:
                (root / process).mkdir(parents=True, exist_ok=True)
        return True

    def _paths_ready(self, worker, row):
        self._workers.discard(worker)
        self._busy = bool(self._workers)
        if 0 <= row < len(self.model._records):
            if self.model._records[row]["watchEnabled"]:
                self._start_row(row)
        self.stateChanged.emit()

    @Slot(int)
    def request_remove(self, row, origin="manager"):
        if not 0 <= row < len(self.model._records):
            return
        self._delete_row = row
        self._delete_origin = str(origin or "manager")
        self.deleteChanged.emit()

    def request_remove_search_key(self, search_key, origin="item"):
        row = next((
            index for index, record in enumerate(self.model._records)
            if record["searchKey"] == str(search_key or "")
        ), -1)
        if row >= 0:
            self.request_remove(row, origin)

    @Slot()
    def cancel_remove(self):
        self._delete_row = -1
        self._delete_origin = ""
        self.deleteChanged.emit()

    @Slot(bool)
    def confirm_remove(self, delete_files):
        row = self._delete_row
        if not 0 <= row < len(self.model._records):
            self.cancel_remove()
            return
        record = dict(self.model._records[row])
        paths, _repos, pending = self._absolute_paths(record)
        if pending and delete_files:
            self._message = (
                "Repository configuration is still loading; "
                "the watch was removed without deleting local files."
            )
            self.stateChanged.emit()
        self._remove_record(row)
        self.cancel_edit()
        self.cancel_remove()
        if not delete_files or pending:
            return
        from thlib.environment import env_inst
        worker = env_inst.local_pool.add_task(self._remove_paths, paths)
        self._workers.add(worker)
        self._busy = True
        worker.result.connect(
            lambda _result, current=worker: self._delete_ready(current),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error, current=worker: self._worker_failed(current, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()
        self.stateChanged.emit()

    def _remove_record(self, row):
        if not 0 <= row < len(self.model._records):
            return None
        record = dict(self.model._records[row])
        self._stop_row(row)
        self.model.remove(row)
        self._persist()
        self._publish_watch_state(record["searchKey"], None)
        return record

    @staticmethod
    def _remove_paths(paths):
        def onerror(function, path, _error):
            if not os.access(path, os.W_OK):
                os.chmod(path, stat.S_IWUSR)
                function(path)
        for value in paths:
            path = Path(value)
            if path.exists():
                shutil.rmtree(path, onerror=onerror)
        return True

    def _delete_ready(self, worker):
        self._workers.discard(worker)
        self._busy = bool(self._workers)
        self.stateChanged.emit()

    @Slot(int)
    def remove(self, row):
        self.request_remove(row)

    @staticmethod
    def _file_type(path):
        try:
            import thlib.global_functions as gf
            return str(gf.file_format(path.suffix.lstrip("."))[3] or "file")
        except (AttributeError, IndexError, TypeError):
            return "file"

    def _watch_checkin_target(self, record, context):
        try:
            import thlib.tactic_classes as tc
            parsed = tc.split_search_key(record["searchKey"])
            stype = (self._project.get_stypes() or {}).get(
                parsed.get("search_type")
            )
            pipelines = stype.get_pipeline() or {}
            pipeline = pipelines.get(record.get("pipeline"))
            if not pipeline and pipelines:
                pipeline = next(iter(pipelines.values()))
            if not pipeline:
                return "publish", "file"
            process = pipeline.get_pipeline_process(context)
            if not process:
                return "publish", "file"
            return context, str(process.get("checkin_mode") or "file")
        except (AttributeError, KeyError, TypeError, ValueError):
            return context or "publish", "file"

    def _watch_payload(self, record, path, repository, context):
        context, checkin_type = self._watch_checkin_target(record, context)
        extension = path.suffix.lstrip(".").lower()
        file_type = self._file_type(path)
        values = {
            "t": [file_type], "s": [""], "e": [extension],
            "p": [""], "m": None,
        }
        if file_type == "preview":
            values["t"].extend(("web", "icon"))
            values["s"].extend(("", ""))
            values["e"].extend(("jpg", "png"))
            values["p"].extend(("", ""))
        try:
            mode = str(self._checkin._checkin_mode() or "upload")
        except (AttributeError, TypeError):
            mode = "upload"
        return {
            "searchKey": record["searchKey"],
            "context": context,
            "process": context.split("/", 1)[0] or "publish",
            "description": "From watch folder",
            "version": None,
            "isRevision": False,
            "updateVersionless": bool(
                getattr(self._checkin, "updateVersionless", True)
            ),
            "onlyVersionless": False,
            "keepFileName": False,
            "generatePreviews": bool(
                getattr(self._checkin, "generatePreviews", True)
            ),
            "explicitFilename": "",
            "contextAsFilename": False,
            "ignoreKeepFileName": False,
            "snapshotType": "file",
            "checkinType": checkin_type,
            "repository": str(repository or ""),
            "mode": mode,
            "sequencePadding": 3,
            "filesDict": [(path.stem, values)],
            "files": [{
                "path": str(path), "paths": [str(path)],
                "template": "$FILENAME.$EXT", "type": file_type,
                "extension": extension,
            }],
        }

    @Slot(object, object)
    def _watch_created(self, event, watch):
        if bool(getattr(event, "is_directory", False)):
            return
        path = Path(str(getattr(event, "src_path", "") or ""))
        if not path.is_file():
            return
        row = next((
            index for index, record in enumerate(self.model._records)
            if record["searchKey"] == getattr(watch, "watch_name", "")
        ), -1)
        if row < 0:
            return
        record = self.model._records[row]
        commit_dir = os.path.normcase(os.path.normpath(str(path.parent)))
        watch_dir = os.path.normcase(os.path.normpath(str(watch.path)))
        context = (
            "publish" if commit_dir == watch_dir
            else path.parent.name or "publish"
        )
        self._commit_queue.add_prepared(
            self._watch_payload(
                record, path, getattr(watch, "repo", ""), context
            ),
            record["title"],
        )
        self._application.window_model.show_window("commit_queue")

    def _persist(self):
        if not self._project:
            return
        from thlib.environment import env_write_config

        settings = self._empty_settings()
        for record in self.model._records:
            row = {
                "assets_codes": record.get("code") or "",
                "assets_names": record["title"],
                "assets_stypes": record["stype"],
                "assets_skeys": record["searchKey"],
                "assets_pipelines": record["pipeline"],
                "paths": record["path"],
                "repos": list(record["repositories"]),
                "statuses": bool(record["watchEnabled"]),
            }
            for key in _FIELDS:
                settings[key].append(row[key])
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
        self._repository_retry_timer.stop()
        self._remove_all_watches()
        if self._observer_owned and self._observer and self._observer.is_started():
            self._observer.stop()
            try:
                self._observer.join(2)
            except (RuntimeError, TimeoutError) as error:
                self._message = str(error)
