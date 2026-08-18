from __future__ import annotations

import json
import os
from pathlib import Path
import traceback
import threading

from PySide6.QtCore import (
    QObject, Property, QSettings, Qt, QTimer, Signal, Slot, QUrl,
)

from .workspace_models.records import RecordListModel


def _naming_snapshots(result) -> list[dict]:
    if isinstance(result, dict):
        return [result]
    if not isinstance(result, (list, tuple)):
        return []
    snapshots = []
    for item in result:
        if isinstance(item, dict):
            snapshots.append(item)
        elif (
            isinstance(item, (list, tuple)) and len(item) > 1
            and isinstance(item[1], dict)
        ):
            snapshots.append(item[1])
    return snapshots


def _naming_path(snapshot: dict, version: str) -> str:
    destination = snapshot.get(version) or {}
    names = list(destination.get("names") or [])
    paths = list(destination.get("paths") or [])
    if not names or not paths:
        return ""
    name = names[0]
    if isinstance(name, (list, tuple)):
        name = "".join(
            "" if part is None else str(part) for part in name
        )
    return str(Path(str(paths[0])) / str(name)).replace("\\", "/")


class CheckinOutController(QObject):
    stateChanged = Signal()
    preparationChanged = Signal()
    operationFinished = Signal(bool, str)
    checkoutChanged = Signal()
    fileConflictRequested = Signal()
    preparedValidationFinished = Signal(str, bool, "QVariantMap", str)

    _builtin_processes = ("publish", "icon", "attachment")

    def __init__(
        self, application_controller, commit_queue=None, parent=None
    ) -> None:
        super().__init__(parent)
        self._application = application_controller
        self._commit_queue = commit_queue
        self._settings = QSettings("TACTIC-Handler", "modern-qml")
        self._tabs = self._restore_tabs()
        self._current_tab = min(
            self._settings.value(
                "checkinOut/currentTab", 0, type=int
            ),
            max(0, len(self._tabs) - 1),
        )
        self._mode = self._settings.value(
            "checkinOut/mode", "checkin", type=str
        )
        if self._mode not in {"checkin", "checkout"}:
            self._mode = "checkin"
        self._processes: list[str] = []
        self._contexts: list[str] = []
        self._process = ""
        self._context = ""
        self._source = None
        self._external_sources = {}
        self._queue_after_naming = False
        self.files = RecordListModel((
            "name", "path", "size", "extension", "fileType",
            "namingVersioned", "namingVersionless", "error",
        ))
        self.checkout_snapshots = RecordListModel((
            "nodeId", "title", "version", "context", "selected",
        ))
        self.checkout_files = RecordListModel((
            "token", "title", "fileType", "size", "path", "repository",
            "version", "exists", "matchesRemote", "selected",
        ))
        self._description = ""
        self._version = 0
        self._is_revision = False
        self._keep_file_name = False
        self._update_versionless = True
        self._generate_previews = True
        self._repository = {}
        self._naming_busy = False
        self._naming_error = ""
        self._naming_request = 0
        self._naming_worker = None
        self._pending_naming_request = None
        self._naming_timer = QTimer(self)
        self._naming_timer.setSingleShot(True)
        self._naming_timer.setInterval(160)
        self._naming_timer.timeout.connect(self._start_scheduled_naming)
        self._debug_enabled = bool(os.environ.get("TACTIC_QML_DEBUG"))
        self._operation_worker = None
        self._operation_id = 0
        self._operation_state = "idle"
        self._operation_stage = ""
        self._operation_message = ""
        self._operation_file = ""
        self._operation_progress = 0.0
        self._operation_error = ""
        self._operation_inputs = None
        self._operation_repository = {}
        self._operation_payload = None
        self._operation_cancel_requested = False
        self._operation_cancel_event = threading.Event()
        self._queue_operation = False
        self._worker_stages = {}
        self._checkout_snapshot_id = ""
        self._checkout_file_token = ""
        self._checkout_task_id = ""
        self._checkout_action = ""
        self._checkout_repeat_count = 1
        self._checkout_dcc_options = {}
        self._checkout_remote_request = ""
        self._dcc_bridge = None
        self._checkout_state = "idle"
        self._checkout_message = ""
        self._checkout_progress = 0.0
        self._checkout_error = ""
        self._pending_conflict_action = ""
        self._load_checkin_options()
        state = application_controller.workspace_state
        state.snapshot_model.contentReplaced.connect(
            self._rebuild_checkout_models
        )
        state.snapshot_file_model.contentReplaced.connect(
            self._rebuild_checkout_models
        )
        state.snapshot_file_model.dataChanged.connect(
            self._rebuild_checkout_models
        )
        application_controller.repository_sync.state_changed.connect(
            self._checkout_sync_changed
        )
        task_updated = getattr(
            application_controller.repository_sync, "task_updated", None
        )
        if task_updated is not None:
            task_updated.connect(self._checkout_task_updated)
        application_controller.repository_sync.task_finished.connect(
            self._checkout_task_updated
        )
        application_controller.repository_sync.task_failed.connect(
            self._checkout_task_failed
        )
        application_controller.selected_node_changed.connect(
            self._selection_changed
        )
        self._selection_changed()
        self._rebuild_checkout_models()

    def _rebuild_checkout_models(self, *_args) -> None:
        state = self._application.workspace_state
        snapshots = [
            {
                "nodeId": str(record.get("nodeId") or ""),
                "title": str(record.get("title") or "Snapshot"),
                "version": str(record.get("version") or ""),
                "context": str(record.get("context") or ""),
                "selected": False,
            }
            for record in state.snapshot_model._records
            if record.get("nodeId")
        ]
        available_ids = {record["nodeId"] for record in snapshots}
        if self._checkout_snapshot_id not in available_ids:
            self._checkout_snapshot_id = (
                snapshots[0]["nodeId"] if snapshots else ""
            )
        for record in snapshots:
            record["selected"] = (
                record["nodeId"] == self._checkout_snapshot_id
            )
        self.checkout_snapshots.replace(snapshots)
        seen = set()
        files = []
        for record in state.snapshot_file_model._records:
            token = str(record.get("token") or "")
            if (
                record.get("rowType") != "file"
                or int(record.get("depth") or 0) != 2
                or not token or token in seen
                or (
                    self._checkout_snapshot_id
                    and record.get("snapshotNodeId")
                    != self._checkout_snapshot_id
                )
            ):
                continue
            seen.add(token)
            files.append({
                "token": token,
                "title": str(record.get("title") or "File"),
                "fileType": str(record.get("fileType") or ""),
                "size": str(record.get("size") or ""),
                "path": str(record.get("path") or ""),
                "repository": str(record.get("repository") or ""),
                "version": str(record.get("version") or ""),
                "exists": bool(record.get("exists")),
                "matchesRemote": bool(record.get("matchesRemote")),
                "selected": False,
            })
        tokens = {record["token"] for record in files}
        if self._checkout_file_token not in tokens:
            self._checkout_file_token = files[0]["token"] if files else ""
        for record in files:
            record["selected"] = (
                record["token"] == self._checkout_file_token
            )
        self.checkout_files.replace(files)
        self.checkoutChanged.emit()

    def _load_checkin_options(self) -> None:
        try:
            from thlib.environment import cfg_controls, env_tactic
            import thlib.global_functions as gf

            values = cfg_controls.get_checkin() or {}
            update_versionless = gf.get_value_from_config(
                values, "updateVersionlessCheckBox"
            )
            generate_previews = gf.get_value_from_config(
                values, "generatePreviewsCheckBox"
            )
            keep_file_name = gf.get_value_from_config(
                values, "keepFilenameCheckBox"
            )
            self._update_versionless = (
                True if update_versionless is None else bool(update_versionless)
            )
            self._generate_previews = (
                True if generate_previews is None else bool(generate_previews)
            )
            self._keep_file_name = bool(keep_file_name)
            if self._keep_file_name:
                self._update_versionless = False
            self._repository = env_tactic.get_current_repo() or {}
        except (AttributeError, IndexError, TypeError):
            self._repository = {}

    @Slot()
    def reload_repository_configuration(self) -> None:
        self._load_checkin_options()
        self.preparationChanged.emit()
        self._schedule_naming()

    def _checkin_mode(self) -> str:
        try:
            from thlib.environment import cfg_controls
            import thlib.global_functions as gf

            index = gf.get_value_from_config(
                cfg_controls.get_checkin() or {},
                "checkinMethodComboBox",
            )
            return {
                0: "preallocate",
                1: "inplace",
                2: "copy",
                3: "move",
                4: "upload",
            }.get(int(index), "upload")
        except (TypeError, ValueError):
            return "upload"

    def _restore_tabs(self) -> list[dict]:
        raw = self._settings.value("checkinOut/tabs", "", type=str)
        if not raw:
            return []
        try:
            tabs = json.loads(raw)
        except (TypeError, ValueError):
            return []
        return [
            {
                "nodeId": str(tab.get("nodeId") or ""),
                "searchKey": str(tab.get("searchKey") or ""),
                "title": str(tab.get("title") or tab.get("code") or "Object"),
                "code": str(tab.get("code") or ""),
                "type": str(tab.get("type") or "sObject"),
                "process": str(tab.get("process") or ""),
                "context": str(tab.get("context") or ""),
                "available": False,
            }
            for tab in tabs
            if isinstance(tab, dict) and tab.get("searchKey")
        ][-12:]

    def _save(self) -> None:
        serializable = [
            {key: value for key, value in tab.items() if key != "available"}
            for tab in self._tabs
        ]
        self._settings.setValue(
            "checkinOut/tabs", json.dumps(serializable)
        )
        self._settings.setValue("checkinOut/currentTab", self._current_tab)
        self._settings.setValue("checkinOut/mode", self._mode)

    @staticmethod
    def _source_pipeline(source):
        if source is None:
            return None
        try:
            stype = source.get_stype()
            pipelines = stype.get_pipeline() or {}
            return pipelines.get(source.get_pipeline_code())
        except (AttributeError, KeyError, TypeError):
            return None

    @classmethod
    def _pipeline_for_process(cls, source, process: str):
        root = cls._source_pipeline(source)
        if root is None or not process:
            return root
        try:
            stype = source.get_stype()
            workflow = stype.get_workflow()
        except (AttributeError, KeyError, TypeError):
            workflow = None
        visited = set()

        def find(pipeline):
            if pipeline is None or id(pipeline) in visited:
                return None
            visited.add(id(pipeline))
            names = list((getattr(pipeline, "pipeline", None) or {}).keys())
            if process in names:
                return pipeline
            if workflow is None:
                return None
            for name in names:
                try:
                    info = pipeline.get_pipeline_process(name) or {}
                except (AttributeError, KeyError, TypeError):
                    info = {}
                if info.get("type") != "hierarchy":
                    continue
                try:
                    child = workflow.get_child_pipeline_by_process_code(
                        pipeline, name
                    )
                except (AttributeError, KeyError, TypeError):
                    child = None
                found = find(child)
                if found is not None:
                    return found
            return None

        return find(root) or root

    @staticmethod
    def _show_builtin_processes() -> bool:
        try:
            import thlib.global_functions as gf
            from thlib.environment import cfg_controls

            return bool(int(gf.get_value_from_config(
                cfg_controls.get_checkin() or {},
                "showAllProcessCheckBox", 0,
            )))
        except (AttributeError, TypeError, ValueError):
            return False

    @classmethod
    def _source_processes(cls, source, current_process: str = "") -> list[str]:
        pipeline = cls._pipeline_for_process(source, current_process)
        names = list((getattr(pipeline, "pipeline", None) or {}).keys())
        if cls._show_builtin_processes():
            names.extend(
                process for process in cls._builtin_processes
                if process not in names
            )
        if not names:
            names = list(cls._builtin_processes)
        return list(dict.fromkeys(str(name) for name in names if name))

    @classmethod
    def _source_contexts(cls, source, process: str) -> list[str]:
        pipeline = cls._pipeline_for_process(source, process)
        try:
            process_info = pipeline.get_pipeline_process(process) or {}
        except (AttributeError, KeyError, TypeError):
            process_info = {}
        options = str(process_info.get("context_options") or "")
        return list(dict.fromkeys(
            cls._full_context(process, option)
            for option in options.split("|") if option.strip()
        ))

    @staticmethod
    def _full_context(process: str, context: str) -> str:
        process = str(process or "publish").strip() or "publish"
        context = str(context or "").strip().replace(" ", "_")
        if not context or context == process:
            return process
        if context.startswith(f"{process}/"):
            return context
        return f"{process}/{context}"

    def _selection_changed(self) -> None:
        node_id = self._application.selected_node_id
        selected = self._application.workspace_model.node_for(node_id)
        if not selected or selected.node_type not in {
            "sobject", "process", "snapshot"
        }:
            self._source = None
            self._processes = []
            self._contexts = []
            self.stateChanged.emit()
            return
        node = selected
        while node and node.node_type != "sobject" and node.parent_id:
            node = self._application.workspace_model.node_for(node.parent_id)
        if not node or node.node_type != "sobject" or node.source is None:
            self._source = None
            self._processes = []
            self._contexts = []
            self.stateChanged.emit()
            return
        selected_process = (
            str(selected.process or "publish")
            if selected.node_type in {"process", "snapshot"}
            else "publish"
        )
        selected_context = (
            str(selected.context or selected_process)
            if selected.node_type == "snapshot"
            else selected_process
        )
        tab = {
            "nodeId": node.node_id,
            "searchKey": node.search_key,
            "title": node.title or node.code or "Object",
            "code": node.code,
            "type": "sobject",
            "process": selected_process,
            "context": selected_context,
            "available": True,
        }
        row = next(
            (
                index for index, item in enumerate(self._tabs)
                if item["searchKey"] == tab["searchKey"]
            ),
            -1,
        )
        if row < 0:
            self._tabs.append(tab)
            self._tabs = self._tabs[-12:]
            row = len(self._tabs) - 1
        else:
            self._tabs[row].update(tab)
        self._current_tab = row
        self._source = node.source
        self._processes = self._source_processes(
            self._source, selected_process
        )
        if selected_process not in self._processes:
            self._processes.append(selected_process)
        self._process = selected_process
        self._contexts = self._source_contexts(
            self._source, self._process
        )
        selected_context = self._full_context(
            self._process, selected_context
        )
        if selected.node_type == "snapshot":
            if selected_context not in self._contexts:
                self._contexts.append(selected_context)
            self._context = selected_context
        else:
            self._context = (
                self._contexts[0] if self._contexts else self._process
            )
        self._tabs[row]["process"] = self._process
        self._tabs[row]["context"] = self._context
        self._save()
        self.stateChanged.emit()
        self._schedule_naming()

    def prepare_workspace_target(
        self, search_key: str, source, project_code: str, title: str,
        code: str, process: str, context: str, description: str = "",
        save_revision: bool = False, snapshot_version=None,
    ) -> None:
        search_key = str(search_key or "").strip()
        if not search_key or source is None:
            raise ValueError("A valid sObject is required for check-in")
        process = str(process or "publish").strip() or "publish"
        context = self._full_context(process, context)
        tab = {
            "nodeId": f"checkin:{search_key}",
            "searchKey": search_key,
            "title": str(title or code or "sObject"),
            "code": str(code or ""),
            "type": "sobject",
            "process": process,
            "context": context,
            "available": True,
        }
        row = next((
            index for index, item in enumerate(self._tabs)
            if item["searchKey"] == search_key
        ), -1)
        if row < 0:
            self._tabs.append(tab)
            self._tabs = self._tabs[-12:]
            row = len(self._tabs) - 1
        else:
            self._tabs[row].update(tab)
        self._external_sources[search_key] = source
        self._current_tab = row
        self._source = source
        self._processes = self._source_processes(source, process)
        if process not in self._processes:
            self._processes.append(process)
        self._process = process
        self._contexts = self._source_contexts(source, process)
        if context == process and self._contexts:
            context = self._contexts[0]
        elif context not in self._contexts:
            self._contexts.append(context)
        self._context = context
        self._mode = "checkin"
        self._description = str(description or "")
        self._is_revision = bool(save_revision)
        self._version = max(0, int(snapshot_version or 0))
        self.files.clear()
        self._naming_error = ""
        self._queue_after_naming = False
        self._tabs[row]["process"] = self._process
        self._tabs[row]["context"] = self._context
        self._save()
        self.stateChanged.emit()
        self.preparationChanged.emit()

    def set_process_and_context(self, process: str, context: str) -> None:
        process = str(process or "publish").strip() or "publish"
        context = self._full_context(process, context)
        if process not in self._processes:
            self._processes.append(process)
        self._process = process
        self._contexts = self._source_contexts(self._source, process)
        if context not in self._contexts:
            self._contexts.append(context)
        self._context = context
        if self._tabs:
            self._tabs[self._current_tab]["process"] = process
            self._tabs[self._current_tab]["context"] = context
        self._save()
        self.stateChanged.emit()
        self._schedule_naming()

    @Property("QVariantList", notify=stateChanged)
    def tabs(self) -> list[dict]:
        return [dict(tab) for tab in self._tabs]

    @Property(int, notify=stateChanged)
    def currentTab(self) -> int:
        return self._current_tab

    @Property(str, notify=stateChanged)
    def mode(self) -> str:
        return self._mode

    @Property("QVariantMap", notify=stateChanged)
    def currentObject(self) -> dict:
        if not self._tabs or self._current_tab >= len(self._tabs):
            return {}
        return dict(self._tabs[self._current_tab])

    @Property("QVariantList", notify=stateChanged)
    def processes(self) -> list[str]:
        return list(self._processes)

    @Property("QVariantList", notify=stateChanged)
    def contexts(self) -> list[str]:
        return list(self._contexts)

    @Property(str, notify=stateChanged)
    def process(self) -> str:
        return self._process

    @Property(str, notify=stateChanged)
    def context(self) -> str:
        return self._context

    @Property(bool, notify=stateChanged)
    def hasObject(self) -> bool:
        return bool(self._source)

    @Property(bool, notify=stateChanged)
    def actionAvailable(self) -> bool:
        return bool(
            self._source and self._process and self._context
        )

    @Slot(int)
    def select_tab(self, row: int) -> None:
        if row < 0 or row >= len(self._tabs):
            return
        self._current_tab = row
        tab = self._tabs[row]
        current_node = self._application.workspace_model.node_for(
            tab["nodeId"]
        )
        self._source = (
            current_node.source if current_node else
            self._external_sources.get(tab["searchKey"])
        )
        tab["available"] = bool(self._source)
        if tab["searchKey"] in self._external_sources:
            self._processes = [tab["process"]] if tab["process"] else []
        else:
            self._processes = self._source_processes(
                self._source, str(tab.get("process") or "")
            )
        if tab["process"] and tab["process"] not in self._processes:
            self._processes.append(tab["process"])
        self._process = (
            tab["process"] if tab["process"] in self._processes
            else (self._processes[0] if self._processes else "")
        )
        self._contexts = (
            [tab["context"]] if tab["searchKey"] in self._external_sources
            and tab["context"] else
            self._source_contexts(self._source, self._process)
        )
        saved_context = self._full_context(
            self._process, str(tab.get("context") or "")
        )
        if saved_context == self._process and self._contexts:
            saved_context = self._contexts[0]
        elif saved_context not in self._contexts:
            self._contexts.append(saved_context)
        self._context = saved_context
        tab["process"] = self._process
        tab["context"] = self._context
        self._save()
        self.stateChanged.emit()
        self._schedule_naming()

    def prepare_external_checkin(
        self, search_key: str, source, project_code: str, title: str,
        code: str, context: str, description: str, paths: list[str],
        save_revision: bool = False, snapshot_version=None,
        keep_file_name: bool = False, update_versionless=None,
        queue_when_ready: bool = True,
    ) -> dict:
        search_key = str(search_key or "").strip()
        context = str(context or "publish").strip() or "publish"
        paths = [str(path or "") for path in paths if str(path or "")]
        if not search_key or source is None:
            raise ValueError("A valid sObject is required for check-in")
        if not paths:
            raise ValueError("At least one file is required for check-in")

        process = context.split("/", 1)[0] or context
        tab = {
            "nodeId": f"external:{search_key}",
            "searchKey": search_key,
            "title": str(title or code or "sObject"),
            "code": str(code or ""),
            "type": "sobject",
            "process": process,
            "context": context,
            "available": True,
        }
        row = next((
            index for index, item in enumerate(self._tabs)
            if item["searchKey"] == search_key
        ), -1)
        if row < 0:
            self._tabs.append(tab)
            self._tabs = self._tabs[-12:]
            row = len(self._tabs) - 1
        else:
            self._tabs[row].update(tab)

        self._external_sources[search_key] = source
        self._current_tab = row
        self._source = source
        self._processes = list(dict.fromkeys(
            [process, *self._builtin_processes]
        ))
        self._contexts = [context]
        self._process = process
        self._context = context
        self._mode = "checkin"
        self._description = str(description or "")
        self._is_revision = bool(save_revision)
        self._version = max(0, int(snapshot_version or 0))
        self._keep_file_name = bool(keep_file_name)
        if update_versionless is not None:
            self._update_versionless = bool(update_versionless)
        if self._keep_file_name:
            self._update_versionless = False
        self._queue_after_naming = bool(queue_when_ready)
        self._save()
        self.stateChanged.emit()

        self.files.clear()
        self._naming_error = ""
        self.add_files(paths)
        accepted = len(self.files._records)
        if not accepted:
            self._queue_after_naming = False
            raise ValueError(self._naming_error or "No readable files were supplied")
        return {
            "accepted": True,
            "projectCode": str(project_code or ""),
            "searchKey": search_key,
            "context": context,
            "fileCount": accepted,
            "queued": bool(queue_when_ready),
        }

    @Slot(int)
    def close_tab(self, row: int) -> None:
        if row < 0 or row >= len(self._tabs):
            return
        self._tabs.pop(row)
        self._current_tab = min(
            self._current_tab, max(0, len(self._tabs) - 1)
        )
        if not self._tabs:
            self._source = None
            self._processes = []
            self._contexts = []
            self._process = ""
            self._context = ""
            self._save()
            self.stateChanged.emit()
            return
        self.select_tab(self._current_tab)

    @Slot(str)
    def set_mode(self, mode: str) -> None:
        if mode not in {"checkin", "checkout"} or mode == self._mode:
            return
        self._mode = mode
        self._save()
        self.stateChanged.emit()
        self._schedule_naming()

    @Slot(str)
    def set_process(self, process: str) -> None:
        if process not in self._processes or process == self._process:
            return
        self._process = process
        self._contexts = self._source_contexts(self._source, process)
        self._context = self._contexts[0] if self._contexts else process
        if self._tabs:
            self._tabs[self._current_tab]["process"] = process
            self._tabs[self._current_tab]["context"] = self._context
        self._save()
        self.stateChanged.emit()
        self._schedule_naming()

    @Slot(str, result="QVariantList")
    def contexts_for_process(self, process: str) -> list[str]:
        if process not in self._processes:
            return []
        contexts = self._source_contexts(self._source, process)
        return contexts or [process]

    @staticmethod
    def _pretty_size(size: int) -> str:
        value = float(size)
        for unit in ("B", "KB", "MB", "GB"):
            if value < 1024 or unit == "GB":
                return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
            value /= 1024
        return ""

    @staticmethod
    def _file_type(path: Path) -> str:
        try:
            import thlib.global_functions as gf
            file_info = gf.file_format(path.suffix.lstrip("."))
            return str(file_info[3] or "file")
        except (AttributeError, IndexError, TypeError):
            return "file"

    @Slot("QVariantList")
    def add_files(self, values: list) -> None:
        records = list(self.files._records)
        known = {record["path"].casefold() for record in records}
        errors = []
        for value in values:
            url = value if isinstance(value, QUrl) else QUrl(str(value))
            path = Path(url.toLocalFile() if url.isLocalFile() else str(value))
            try:
                path = path.resolve(strict=True)
                if not path.is_file():
                    errors.append(f"{path.name or path}: directories are not supported")
                    continue
                key = str(path).casefold()
                if key in known:
                    continue
                stat = path.stat()
            except OSError as error:
                errors.append(f"{path.name or path}: {error}")
                continue
            extension = path.suffix.lstrip(".").lower()
            records.append({
                "name": path.name,
                "path": str(path),
                "size": self._pretty_size(stat.st_size),
                "extension": extension.upper() or "FILE",
                "fileType": self._file_type(path),
                "namingVersioned": "",
                "namingVersionless": "",
                "error": "",
            })
            known.add(key)
        self.files.replace(records)
        self._naming_error = "; ".join(errors)
        self.preparationChanged.emit()
        self._schedule_naming()

    @Slot(int)
    def remove_file(self, row: int) -> None:
        self.files.remove(row)
        self.preparationChanged.emit()
        self._schedule_naming()

    @Slot()
    def clear_files(self) -> None:
        self.files.clear()
        self._naming_error = ""
        self.preparationChanged.emit()

    def _files_dict(self) -> list:
        result = []
        for record in self.files._records:
            extension = record["extension"].lower()
            file_type = record["fileType"] or "file"
            values = {
                "t": [file_type],
                "s": [""],
                "e": [extension],
                "p": [""],
                "m": None,
            }
            if file_type == "preview":
                values["t"].extend(("web", "icon"))
                values["s"].extend(("", ""))
                values["e"].extend(("jpg", "png"))
                values["p"].extend(("", ""))
            result.append((Path(record["path"]).stem, values))
        return result

    def _schedule_naming(self) -> None:
        self._naming_request += 1
        self._naming_timer.stop()
        if (
            not self._source or not self.files._records
            or not self._context or not self._repository
        ):
            self._pending_naming_request = None
            if self._naming_worker is not None:
                self._naming_worker.cancel()
            self._naming_busy = False
            if not self._repository:
                self._naming_error = "No active repository is configured"
                self._queue_after_naming = False
            self.preparationChanged.emit()
            return
        self._naming_busy = True
        self._naming_error = ""
        self.preparationChanged.emit()
        self._naming_timer.start()

    @Slot()
    def _start_scheduled_naming(self) -> None:
        request_id = self._naming_request
        if self._naming_worker is not None:
            self._pending_naming_request = request_id
            self._naming_worker.cancel()
            return
        self._pending_naming_request = None
        from thlib.environment import env_inst
        import thlib.tactic_classes as tc

        tab = self._tabs[self._current_tab]
        worker = env_inst.server_pool.add_task(
            tc.get_virtual_snapshot,
            tab["searchKey"],
            self._context,
            self._files_dict(),
            is_revision=self._is_revision,
            keep_file_name=self._keep_file_name,
            version=self._version or None,
            checkin_type="file",
        )
        if worker is None:
            self._naming_busy = False
            self._naming_error = "Server worker pool is not available"
            self.preparationChanged.emit()
            return
        self._naming_worker = worker
        worker.result.connect(
            lambda result: self._naming_ready(request_id, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._naming_failed(request_id, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.settled.connect(
            self._naming_worker_settled,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    @Slot(object)
    def _naming_worker_settled(self, worker) -> None:
        if self._naming_worker is worker:
            self._naming_worker = None
        pending = self._pending_naming_request
        self._pending_naming_request = None
        if pending == self._naming_request:
            QTimer.singleShot(0, self._start_scheduled_naming)

    def _naming_ready(self, request_id: int, result) -> None:
        if request_id != self._naming_request:
            return
        snapshots = _naming_snapshots(result)
        if len(snapshots) < len(self.files._records):
            self._naming_failed(
                request_id,
                ValueError("TACTIC naming returned incomplete file destinations"),
            )
            return
        records = []
        for index, record in enumerate(self.files._records):
            updated = dict(record)
            updated["namingVersioned"] = _naming_path(
                snapshots[index], "versioned"
            )
            updated["namingVersionless"] = _naming_path(
                snapshots[index], "versionless"
            )
            records.append(updated)
        self.files.replace(records)
        self._naming_busy = False
        self._naming_error = ""
        self.preparationChanged.emit()
        if self._queue_after_naming and self.payloadReady:
            self._queue_after_naming = False
            self.queue_current_operation()

    def _naming_failed(self, request_id: int, error) -> None:
        if request_id != self._naming_request:
            return
        self._naming_busy = False
        self._queue_after_naming = False
        self._naming_error = str(error or "Naming preview failed")
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            stacktrace = (
                str(error.get("stacktrace") or "")
                if isinstance(error, dict) else ""
            )
            debug_log.raise_error(
                error, stacktrace=stacktrace, group="checkin/naming"
            )
        self.preparationChanged.emit()

    @Property(str, notify=preparationChanged)
    def description(self) -> str:
        return self._description

    @Property(int, notify=preparationChanged)
    def version(self) -> int:
        return self._version

    @Property(bool, notify=preparationChanged)
    def isRevision(self) -> bool:
        return self._is_revision

    @Property(bool, notify=preparationChanged)
    def keepFileName(self) -> bool:
        return self._keep_file_name

    @Property(bool, notify=preparationChanged)
    def updateVersionless(self) -> bool:
        return self._update_versionless

    @Property(bool, notify=preparationChanged)
    def generatePreviews(self) -> bool:
        return self._generate_previews

    @Property(str, notify=preparationChanged)
    def repositoryTitle(self) -> str:
        values = self._repository.get("value") or []
        return str(values[1]) if len(values) > 1 else ""

    @Property(bool, notify=preparationChanged)
    def namingBusy(self) -> bool:
        return self._naming_busy

    @Property(str, notify=preparationChanged)
    def preparationError(self) -> str:
        return self._naming_error

    @Property(bool, notify=preparationChanged)
    def payloadReady(self) -> bool:
        return bool(
            self.actionAvailable and self.files._records
            and self._repository and not self._naming_busy
            and not self._naming_error
            and all(row.get("namingVersioned") for row in self.files._records)
        )

    @Property(bool, constant=True)
    def debugEnabled(self) -> bool:
        return self._debug_enabled

    @Property(str, notify=preparationChanged)
    def debugPayload(self) -> str:
        if not self._debug_enabled:
            return ""
        return json.dumps(self.operation_payload(), indent=2, ensure_ascii=False)

    @Property(bool, notify=preparationChanged)
    def operationBusy(self) -> bool:
        return self._operation_state in {"queued", "running"}

    @Property(str, notify=preparationChanged)
    def operationState(self) -> str:
        return self._operation_state

    @Property(str, notify=preparationChanged)
    def operationStage(self) -> str:
        return self._operation_stage

    @Property(str, notify=preparationChanged)
    def operationMessage(self) -> str:
        return self._operation_message

    @Property(str, notify=preparationChanged)
    def operationFile(self) -> str:
        return self._operation_file

    @Property(float, notify=preparationChanged)
    def operationProgress(self) -> float:
        return self._operation_progress

    @Property(str, notify=preparationChanged)
    def operationError(self) -> str:
        return self._operation_error

    @Property(bool, notify=preparationChanged)
    def canRetryOperation(self) -> bool:
        return (
            self._operation_state == "failed"
            and not self._queue_operation
            and self.payloadReady
        )

    @Slot(str)
    def set_description(self, value: str) -> None:
        self._description = str(value or "")
        self.preparationChanged.emit()

    @Slot(int)
    def set_version(self, value: int) -> None:
        self._version = max(0, int(value))
        self.preparationChanged.emit()
        self._schedule_naming()

    @Slot(bool)
    def set_revision(self, value: bool) -> None:
        self._is_revision = bool(value)
        self.preparationChanged.emit()
        self._schedule_naming()

    @Slot(bool)
    def set_keep_file_name(self, value: bool) -> None:
        self._keep_file_name = bool(value)
        if self._keep_file_name:
            self._update_versionless = False
        self.preparationChanged.emit()
        self._schedule_naming()

    @Slot(bool)
    def set_update_versionless(self, value: bool) -> None:
        self._update_versionless = bool(value) and not self._keep_file_name
        self.preparationChanged.emit()

    @Slot(bool)
    def set_generate_previews(self, value: bool) -> None:
        self._generate_previews = bool(value)
        self.preparationChanged.emit()

    @Slot(result="QVariantMap")
    def operation_payload(self) -> dict:
        tab = self._tabs[self._current_tab] if self._tabs else {}
        repo_values = self._repository.get("value") or []
        sequence_padding = 3
        try:
            from thlib.environment import cfg_controls
            import thlib.global_functions as gf

            enabled = gf.get_value_from_config(
                cfg_controls.get_checkin() or {}, "sequencePaddingCheckBox", False
            )
            if enabled:
                sequence_padding = max(1, min(9, int(
                    gf.get_value_from_config(
                        cfg_controls.get_checkin() or {},
                        "sequencePaddingSpinBox", 3,
                    )
                )))
        except (AttributeError, TypeError, ValueError):
            sequence_padding = 3
        return {
            "searchKey": tab.get("searchKey", ""),
            "context": self._context,
            "process": self._process,
            "description": self._description,
            "version": self._version or None,
            "isRevision": self._is_revision,
            "updateVersionless": self._update_versionless,
            "onlyVersionless": False,
            "keepFileName": self._keep_file_name,
            "generatePreviews": self._generate_previews,
            "explicitFilename": "",
            "contextAsFilename": False,
            "ignoreKeepFileName": False,
            "snapshotType": "file",
            "checkinType": "file",
            "repository": str(repo_values[3]) if len(repo_values) > 3 else "",
            "mode": self._checkin_mode(),
            "sequencePadding": sequence_padding,
            "filesDict": self._files_dict(),
            "files": [
                {
                    "path": row["path"],
                    "type": row["fileType"],
                    "extension": row["extension"].lower(),
                    "versioned": row["namingVersioned"],
                    "versionless": row["namingVersionless"],
                }
                for row in self.files._records
            ],
        }

    @Slot()
    def queue_current_operation(self) -> None:
        if not self._commit_queue or not self.payloadReady:
            return
        current = self.currentObject
        self._commit_queue.add_prepared(
            self.operation_payload(),
            str(current.get("title") or current.get("code") or "sObject"),
        )
        self._application.window_model.show_window("commit_queue")

    @Slot()
    def start_checkin(self) -> None:
        if self.operationBusy or not self.payloadReady:
            return
        self._start_operation(
            self.operation_payload(), self._repository, queued=False
        )

    def start_prepared_operation(self, payload: dict) -> bool:
        if self.operationBusy or not isinstance(payload, dict):
            return False
        repository = self._repository_for_name(
            str(payload.get("repository") or "")
        )
        if not repository:
            self._operation_state = "failed"
            self._operation_stage = "failed"
            self._operation_error = "Configured repository is unavailable"
            self.preparationChanged.emit()
            self.operationFinished.emit(False, self._operation_error)
            return True
        self._start_operation(dict(payload), repository, queued=True)
        return True

    def validate_prepared_operation(self, request_id: str, payload: dict) -> None:
        from thlib.environment import env_inst

        worker = env_inst.commit_pool.add_task(
            self._validate_prepared_payload, dict(payload)
        )
        if worker is None:
            self.preparedValidationFinished.emit(
                request_id, False, {}, "Check-in worker pool is unavailable"
            )
            return
        worker.result.connect(
            lambda result: self.preparedValidationFinished.emit(
                request_id, True, result, ""
            ),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self.preparedValidationFinished.emit(
                request_id, False, {}, self._worker_error_text(error)
            ),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    @staticmethod
    def _worker_error_text(error) -> str:
        payload = error[0] if isinstance(error, tuple) and error else error
        exception = (
            payload.get("exception") if isinstance(payload, dict) else payload
        )
        return str(exception or "Naming validation failed")

    @staticmethod
    def _validate_prepared_payload(payload: dict, progress_signal=None) -> dict:
        from .checkin_operation import prepare_checkin

        inputs = prepare_checkin(payload, progress_signal=progress_signal)
        versioned_paths = []
        versionless_paths = []
        for _key, snapshot in inputs["virtualSnapshot"]:
            for destination, target in (
                (snapshot.get("versioned") or {}, versioned_paths),
                (snapshot.get("versionless") or {}, versionless_paths),
            ):
                paths = list(destination.get("paths") or [])
                names = list(destination.get("names") or [])
                if paths and names:
                    target.append(str(Path(str(paths[0])) / "".join(names[0])))
        return {
            "versionedPaths": versioned_paths,
            "versionlessPaths": versionless_paths,
        }

    @staticmethod
    def _repository_for_name(name: str) -> dict:
        try:
            from thlib.environment import env_tactic

            for _base_name, repository in env_tactic.get_all_base_dirs():
                values = repository.get("value") or []
                if len(values) > 3 and str(values[3]) == name:
                    return repository
        except (AttributeError, IndexError, TypeError):
            return {}
        return {}

    def _start_operation(
        self, payload: dict, repository: dict, queued: bool
    ) -> None:
        if self.operationBusy:
            return
        self._operation_id += 1
        operation_id = self._operation_id
        self._operation_state = "queued"
        self._operation_stage = "preparing"
        self._operation_message = "Preparing files"
        self._operation_file = ""
        self._operation_progress = 0.0
        self._operation_error = ""
        self._operation_inputs = None
        self._operation_payload = dict(payload)
        self._operation_repository = repository
        self._operation_cancel_requested = False
        self._operation_cancel_event.clear()
        self._queue_operation = queued
        self.preparationChanged.emit()
        from thlib.environment import env_inst

        worker = env_inst.commit_pool.add_task(
            self._prepare_checkin,
            self._operation_payload,
            self._operation_cancel_event,
        )
        if worker is None:
            self._operation_failed(
                operation_id, RuntimeError("Check-in worker pool is unavailable")
            )
            return
        self._connect_operation_worker(
            worker,
            operation_id,
            "preparing",
            self._checkin_prepared,
        )
        worker.start()

    @staticmethod
    def _prepare_checkin(payload: dict, cancel_event=None, progress_signal=None):
        from .checkin_operation import prepare_checkin

        return prepare_checkin(
            payload, progress_signal=progress_signal,
            cancel_event=cancel_event,
        )

    def _connect_operation_worker(
        self, worker, operation_id: int, stage: str, result_handler
    ) -> None:
        self._operation_worker = worker
        self._worker_stages[worker] = (operation_id, stage)
        worker.started.connect(
            lambda: self._operation_started(operation_id, stage),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.result.connect(
            lambda result: result_handler(operation_id, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.connect_progress(self._worker_progressed)
        worker.error.connect(
            lambda error: self._operation_failed(
                operation_id, error, worker
            ),
            Qt.ConnectionType.QueuedConnection,
        )

    @Slot(object)
    def _worker_progressed(self, value) -> None:
        operation_id, stage = self._worker_stages.get(
            self.sender(), (-1, "")
        )
        self._operation_progressed(operation_id, stage, value)

    def _operation_started(self, operation_id: int, stage: str) -> None:
        if operation_id != self._operation_id:
            return
        self._operation_state = "running"
        self._operation_stage = stage
        self._operation_error = ""
        self.preparationChanged.emit()

    def _operation_progressed(
        self, operation_id: int, stage: str, value
    ) -> None:
        if operation_id != self._operation_id:
            return
        try:
            progress, info = value
            total = max(1, int(info.get("total_count") or 1))
            self._operation_progress = min(
                1.0, max(0.0, (int(progress) + 1) / total)
            )
            self._operation_file = str(info.get("status_text") or "")
        except (AttributeError, TypeError, ValueError):
            return
        self._operation_stage = stage
        self.preparationChanged.emit()

    def _checkin_prepared(self, operation_id: int, inputs) -> None:
        if operation_id != self._operation_id:
            return
        if self._operation_cancel_requested:
            self._operation_cancelled(operation_id)
            return
        self._operation_inputs = inputs
        self._operation_message = "Copying files to repository"
        self._operation_progress = 0.0
        from .checkin_operation import stage_checkin
        from thlib.environment import env_inst

        worker = env_inst.commit_pool.add_task(
            stage_checkin,
            inputs,
            self._operation_repository,
            cancel_event=self._operation_cancel_event,
        )
        if worker is None:
            self._operation_failed(
                operation_id, RuntimeError("Check-in worker pool is unavailable")
            )
            return
        self._connect_operation_worker(
            worker, operation_id, "copying", self._files_copied
        )
        worker.start()

    def _files_copied(self, operation_id: int, result) -> None:
        if operation_id != self._operation_id or not self._operation_inputs:
            return
        if result is False:
            self._operation_failed(
                operation_id,
                OSError("One or more files could not be copied to repository"),
            )
            return
        if self._operation_cancel_requested:
            self._operation_cancelled(operation_id)
            return
        inputs = self._operation_inputs
        payload = inputs["payload"]
        mode = payload["mode"]
        snapshot_mode = (
            "upload" if mode == "upload"
            else "preallocate" if mode == "preallocate"
            else "inplace"
        )
        self._operation_message = (
            "Uploading and creating snapshot"
            if snapshot_mode == "upload" else "Creating snapshot"
        )
        self._operation_progress = 0.0
        from thlib.environment import env_inst

        worker = env_inst.commit_pool.add_task(
            self._create_snapshot,
            search_key=payload["searchKey"],
            context=payload["context"],
            snapshot_type=payload.get("snapshotType") or "file",
            is_revision=payload["isRevision"],
            description=payload["description"],
            version=payload["version"],
            update_versionless=payload["updateVersionless"],
            only_versionless=payload.get("onlyVersionless", False),
            keep_file_name=payload["keepFileName"],
            repo_name=self._operation_repository,
            virtual_snapshot=inputs["virtualSnapshot"],
            files_dict=inputs["filesDict"],
            mode=snapshot_mode,
            create_icon=payload["generatePreviews"],
            files_objects=inputs["filesObjects"],
        )
        if worker is None:
            self._operation_failed(
                operation_id, RuntimeError("Check-in worker pool is unavailable")
            )
            return
        self._connect_operation_worker(
            worker, operation_id, "snapshot", self._checkin_finished
        )
        worker.start()

    @staticmethod
    def _create_snapshot(**kwargs):
        import thlib.tactic_classes as tc

        result = tc.checkin_snapshot(**kwargs)
        if result is None:
            raise RuntimeError("TACTIC did not return the created snapshot")
        return result

    def _checkin_finished(self, operation_id: int, _result) -> None:
        if operation_id != self._operation_id:
            return
        search_key = str(
            (self._operation_payload or {}).get("searchKey") or ""
        )
        self._operation_worker = None
        self._worker_stages.clear()
        self._operation_inputs = None
        self._operation_payload = None
        self._operation_repository = {}
        self._operation_state = "completed"
        self._operation_stage = "completed"
        self._operation_message = "Check-in completed"
        self._operation_file = ""
        self._operation_progress = 1.0
        self._operation_error = ""
        self.preparationChanged.emit()
        self._application.refresh_snapshot_browser_for(search_key)
        self.operationFinished.emit(True, "")
        self._queue_operation = False

    def _operation_failed(
        self, operation_id: int, error, worker=None
    ) -> None:
        if operation_id != self._operation_id:
            return
        payload = error[0] if isinstance(error, tuple) and error else error
        exception = (
            payload.get("exception")
            if isinstance(payload, dict) else payload
        )
        stacktrace = (
            str(payload.get("stacktrace") or "")
            if isinstance(payload, dict) else ""
        )
        if self._operation_cancel_requested or isinstance(
            exception, InterruptedError
        ):
            self._operation_cancelled(operation_id)
            return
        self._operation_state = "failed"
        self._operation_message = "Check-in failed"
        self._operation_error = str(exception or "Unknown check-in error")
        self._operation_worker = worker
        self.preparationChanged.emit()
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.raise_error(
                exception,
                stacktrace=stacktrace,
                group="checkin/operation",
                retry_worker=None if self._queue_operation else worker,
            )
        self.operationFinished.emit(False, self._operation_error)

    @Slot()
    def retry_checkin(self) -> None:
        if not self.canRetryOperation:
            return
        if self._operation_worker is not None:
            self._operation_worker.dispose()
            self._operation_worker = None
        self._worker_stages.clear()
        payload = self._operation_payload
        repository = self._operation_repository
        if payload and repository:
            self._operation_state = "idle"
            self._start_operation(payload, repository, queued=False)
        else:
            self.start_checkin()

    @Slot()
    def cancel_checkin(self) -> None:
        if not self.operationBusy:
            return
        self._operation_cancel_requested = True
        self._operation_cancel_event.set()
        self._operation_message = (
            "Cancelling after the current safe stage"
            if self._operation_stage != "snapshot"
            else "Snapshot creation is already finishing"
        )
        self.preparationChanged.emit()

    def _operation_cancelled(self, operation_id: int) -> None:
        if operation_id != self._operation_id:
            return
        if self._operation_worker is not None:
            self._operation_worker.dispose()
        self._operation_worker = None
        self._worker_stages.clear()
        self._operation_inputs = None
        self._operation_state = "cancelled"
        self._operation_stage = "cancelled"
        self._operation_message = "Check-in cancelled"
        self._operation_progress = 0.0
        self._operation_error = ""
        self._operation_payload = None
        self._operation_repository = {}
        self.preparationChanged.emit()
        self.operationFinished.emit(False, "")
        self._queue_operation = False

    @Property(str, notify=checkoutChanged)
    def checkoutState(self) -> str:
        return self._checkout_state

    @Property(str, notify=checkoutChanged)
    def checkoutMessage(self) -> str:
        return self._checkout_message

    @Property(float, notify=checkoutChanged)
    def checkoutProgress(self) -> float:
        return self._checkout_progress

    @Property(str, notify=checkoutChanged)
    def checkoutError(self) -> str:
        return self._checkout_error

    @Property(bool, notify=checkoutChanged)
    def checkoutBusy(self) -> bool:
        return self._checkout_state in {"queued", "downloading", "executing"}

    @Property(bool, notify=checkoutChanged)
    def hasCheckoutFile(self) -> bool:
        return bool(self._checkout_file_token)

    @Property("QVariantMap", notify=checkoutChanged)
    def selectedCheckoutFile(self) -> dict:
        for record in self.checkout_files._records:
            if record.get("token") == self._checkout_file_token:
                return dict(record)
        return {}

    @Property(bool, notify=checkoutChanged)
    def openAvailable(self) -> bool:
        return bool(self._checkout_file_token) and self.dcc_operation_availability(
            "open"
        )[0]

    @Property(bool, notify=checkoutChanged)
    def importAvailable(self) -> bool:
        return bool(self._checkout_file_token) and self.dcc_operation_availability(
            "import"
        )[0]

    @Property(bool, notify=checkoutChanged)
    def referenceAvailable(self) -> bool:
        return bool(self._checkout_file_token) and self.dcc_operation_availability(
            "reference"
        )[0]

    @Property(str, notify=checkoutChanged)
    def dccUnavailableReason(self) -> str:
        if self.dcc_operation_availability("import")[0]:
            return ""
        return self.dcc_operation_availability("import")[1]

    @Property(bool, notify=checkoutChanged)
    def mayaClientAvailable(self) -> bool:
        bridge = getattr(self, "_dcc_bridge", None)
        return bool(bridge and bridge.has_dcc_capability("open"))

    def attach_dcc_bridge(self, bridge) -> None:
        previous = getattr(self, "_dcc_bridge", None)
        if previous:
            try:
                previous.commandFinished.disconnect(self._remote_dcc_finished)
                previous.stateChanged.disconnect(self.checkoutChanged.emit)
            except (RuntimeError, TypeError):
                previous = None
        self._dcc_bridge = bridge
        if bridge:
            bridge.commandFinished.connect(self._remote_dcc_finished)
            bridge.stateChanged.connect(self.checkoutChanged.emit)
        self.checkoutChanged.emit()

    def dcc_operation_availability(self, operation: str) -> tuple[bool, str]:
        bridge = getattr(self, "_dcc_bridge", None)
        if bridge and bridge.has_dcc_capability(operation):
            return True, ""
        from .dcc_operations import operation_availability
        return operation_availability(operation)

    @Slot(int)
    def select_checkout_snapshot(self, row: int) -> None:
        record = self.checkout_snapshots.get(row)
        node_id = str(record.get("nodeId") or "")
        if not node_id or node_id == self._checkout_snapshot_id:
            return
        self._checkout_snapshot_id = node_id
        self._checkout_file_token = ""
        self._rebuild_checkout_models()

    @Slot(int)
    def select_checkout_file(self, row: int) -> None:
        record = self.checkout_files.get(row)
        token = str(record.get("token") or "")
        if not token or token == self._checkout_file_token:
            return
        self._checkout_file_token = token
        self._rebuild_checkout_models()

    def _selected_file_object(self):
        return self._application.workspace_state.snapshot_file_for(
            self._checkout_file_token
        )

    @Slot(str)
    @Slot(str, int)
    @Slot(str, int, "QVariantMap")
    def request_checkout_action(
        self, action: str, repeat_count: int = 1, options=None
    ) -> None:
        if (
            self.checkoutBusy
            or action not in {"checkout", "open", "import", "reference"}
        ):
            return
        file_object = self._selected_file_object()
        record = self.selectedCheckoutFile
        if not file_object or not record:
            self._checkout_failed("The selected snapshot file is unavailable")
            return
        if action in {"open", "import", "reference"}:
            available, reason = self.dcc_operation_availability(action)
            if not available:
                self._checkout_failed(reason)
                return
        self._checkout_action = action
        self._checkout_repeat_count = (
            max(1, min(100, int(repeat_count)))
            if action in {"import", "reference"} else 1
        )
        self._checkout_dcc_options = dict(options or {})
        self._checkout_error = ""
        if record.get("exists") and record.get("matchesRemote"):
            self._finish_file_action(file_object, skipped=True)
            return
        if record.get("exists") and not record.get("matchesRemote"):
            self._pending_conflict_action = action
            self.fileConflictRequested.emit()
            return
        self._start_download("overwrite")

    @Slot(str)
    def resolve_file_conflict(self, policy: str) -> None:
        if not self._pending_conflict_action:
            return
        action = self._pending_conflict_action
        self._pending_conflict_action = ""
        self._checkout_action = action
        if policy == "cancel":
            self._checkout_state = "cancelled"
            self._checkout_message = "Operation cancelled"
            self.checkoutChanged.emit()
            return
        if policy == "skip":
            file_object = self._selected_file_object()
            if file_object:
                self._finish_file_action(file_object, skipped=True)
            return
        self._start_download("overwrite")

    def _start_download(self, overwrite_policy: str) -> None:
        file_object = self._selected_file_object()
        if not file_object:
            self._checkout_failed("The selected snapshot file is unavailable")
            return
        try:
            handle = self._application.repository_sync.schedule_file_object(
                file_object,
                process="checkout",
                auto_start=False,
                overwrite_policy=overwrite_policy,
            )
            self._checkout_task_id = handle.task_id
            self._checkout_state = "queued"
            self._checkout_message = "Queued for download"
            self._checkout_progress = 0.0
            self._checkout_error = ""
            handle.downloaded.connect(
                self._checkout_downloaded,
                Qt.ConnectionType.QueuedConnection,
            )
            handle.failed.connect(
                lambda _file: self._checkout_task_failed(handle.task_id),
                Qt.ConnectionType.QueuedConnection,
            )
            self.checkoutChanged.emit()
            handle.download()
        except Exception as error:
            self._checkout_failed(error)

    @Slot()
    def cancel_checkout(self) -> None:
        remote_request = getattr(self, "_checkout_remote_request", "")
        bridge = getattr(self, "_dcc_bridge", None)
        if remote_request and bridge:
            bridge.cancel_request(remote_request)
            return
        if self._checkout_task_id and self.checkoutBusy:
            self._application.repository_sync.cancel_task(
                self._checkout_task_id
            )

    @Slot(object)
    def _checkout_downloaded(self, file_object) -> None:
        if not self._checkout_task_id:
            return
        self._finish_file_action(file_object)

    def _finish_file_action(self, file_object, skipped: bool = False) -> None:
        action = self._checkout_action or "checkout"
        try:
            if action != "checkout":
                self._checkout_state = "executing"
                self._checkout_message = f"Running {action}"
                self.checkoutChanged.emit()
                bridge = getattr(self, "_dcc_bridge", None)
                if bridge and bridge.has_dcc_capability(action):
                    options = dict(
                        getattr(self, "_checkout_dcc_options", {}) or {}
                    )
                    options["repeat_count"] = self._checkout_repeat_count
                    current = self.currentObject
                    selected_file = self.selectedCheckoutFile
                    selected_snapshot = next((
                        dict(record)
                        for record in self.checkout_snapshots._records
                        if record.get("nodeId") == self._checkout_snapshot_id
                    ), {})
                    options.update({
                        "project_code": str(
                            getattr(self._application, "_current_project_code", "")
                            or ""
                        ),
                        "search_key": str(current.get("searchKey") or ""),
                        "code": str(current.get("code") or ""),
                        "title": str(current.get("title") or ""),
                        "process": str(current.get("process") or self._process or "publish"),
                        "context": str(current.get("context") or self._context or "publish"),
                        "snapshot": selected_snapshot,
                        "file": {
                            key: selected_file.get(key)
                            for key in (
                                "title", "fileType", "size", "path",
                                "repository", "version",
                            )
                            if selected_file.get(key) not in (None, "")
                        },
                    })
                    request_id = bridge.send_dcc_action(
                        action, file_object.get_full_abs_path(), options
                    )
                    if request_id:
                        self._checkout_remote_request = request_id
                        self._checkout_task_id = ""
                        self.checkoutChanged.emit()
                        return
                from .dcc_operations import execute_file_operation
                for _index in range(self._checkout_repeat_count):
                    execute_file_operation(action, file_object)
            self._checkout_state = "completed"
            self._checkout_message = (
                "Local file kept"
                if skipped and action == "checkout"
                else f"{action.title()} completed"
            )
            self._checkout_progress = 1.0
            self._checkout_error = ""
            self._checkout_task_id = ""
            self._checkout_repeat_count = 1
            self.checkoutChanged.emit()
            self._application.workspace_state.update_snapshot_file_status(
                self._checkout_file_token, True, True
            )
            self._application.refresh_snapshot_browser()
        except Exception as error:
            self._checkout_failed(error)

    @Slot(str, bool, "QVariantMap", str)
    def _remote_dcc_finished(self, request_id, success, payload, error):
        if request_id != getattr(self, "_checkout_remote_request", ""):
            return
        self._checkout_remote_request = ""
        if not success:
            if str(error or "").lower() == "cancelled":
                self._checkout_state = "cancelled"
                self._checkout_message = "Operation cancelled"
                self._checkout_error = ""
                self.checkoutChanged.emit()
            else:
                self._checkout_failed(error or "DCC command failed")
            return
        opened_path = str(
            payload.get("opened_path") or payload.get("path") or ""
        )
        self._checkout_state = "completed"
        self._checkout_message = opened_path or f"{self._checkout_action.title()} completed"
        self._checkout_progress = 1.0
        self._checkout_error = ""
        self._checkout_repeat_count = 1
        self.checkoutChanged.emit()
        self._application.workspace_state.update_snapshot_file_status(
            self._checkout_file_token, True, True
        )
        self._application.refresh_snapshot_browser()

    @Slot()
    def _checkout_sync_changed(self) -> None:
        if not self._checkout_task_id:
            return
        record = self._application.repository_sync.model.record(
            self._checkout_task_id
        )
        if not record:
            return
        self._checkout_state = str(record.get("status") or "queued")
        self._checkout_message = str(record.get("progress") or "")
        self._checkout_progress = float(record.get("progressValue") or 0.0)
        self._checkout_error = str(record.get("error") or "")
        self.checkoutChanged.emit()

    @Slot(str)
    @Slot(str, str)
    def _checkout_task_updated(self, task_id: str, *_args) -> None:
        if task_id == self._checkout_task_id:
            self._checkout_sync_changed()

    @Slot(str)
    def _checkout_task_failed(self, task_id: str) -> None:
        if task_id != self._checkout_task_id:
            return
        record = self._application.repository_sync.model.record(task_id)
        status = str(record.get("status") or "failed")
        self._checkout_state = status
        self._checkout_message = (
            "Download cancelled" if status == "cancelled"
            else "Download failed"
        )
        self._checkout_error = str(record.get("error") or "")
        self._checkout_task_id = ""
        self.checkoutChanged.emit()

    def _checkout_failed(self, error) -> None:
        self._checkout_remote_request = ""
        self._checkout_state = "failed"
        self._checkout_message = "Operation failed"
        self._checkout_error = str(error or "Unknown file operation error")
        self._checkout_task_id = ""
        self.checkoutChanged.emit()
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            stacktrace = traceback.format_exc()
            debug_log.raise_error(
                error,
                stacktrace=(
                    "" if stacktrace.startswith("NoneType: None") else stacktrace
                ),
                group="checkout/operation",
            )

    @Slot(str)
    def set_context(self, context: str) -> None:
        context = self._full_context(self._process, context)
        if not context or context == self._context:
            return
        self._context = context
        if self._tabs:
            self._tabs[self._current_tab]["context"] = context
        self._save()
        self.stateChanged.emit()
        self._schedule_naming()
