from __future__ import annotations

import traceback
import uuid
from datetime import date, timedelta

from PySide6.QtCore import QObject, Property, QTimer, Qt, Signal, Slot

from thlib.ui.activity import (
    activity_record,
    activity_timestamp_labels,
    present_activity_records,
)
from thlib.ui.task_data import due_state, parse_datetime, progress_value
from thlib.ui.user_identity import user_avatar_color
from thlib.ui.workspace_models.records import RecordListModel


class SObjectInfoController(QObject):
    """Read-only, cached reporting projection for the selected SObject."""

    stateChanged = Signal()
    _activity_page_size = 50

    def __init__(
            self, application, users=None, navigation=None, tasks=None,
            parent=None, clock=None):
        super().__init__(parent or application)
        self._application = application
        self._users = users
        self._navigation = navigation
        self._tasks_controller = tasks
        self._clock = clock
        self._summary = {}
        self._metrics = {}
        self._busy = False
        self._error = ""
        self._request_id = ""
        self._worker = None
        self._refreshed_tasks = None
        self._refreshed_notes = None
        self._refreshed_children = None
        self._refreshed_work_hours = None
        self._refreshed_activity = None
        self._activity_has_more = False
        self._activity_loading_more = False
        self._activity_offset = 0
        self._activity_request_id = ""
        self._activity_worker = None
        self._file_objects = {}
        self._page = 0
        self._file_metadata = {}
        self._file_worker = None
        self._file_request_id = ""
        self._file_inspection_error = False
        self._preview_download_ids = set()
        self._tracked_download_ids = set()
        self._projection_dirty = True
        self._download_refresh_timer = QTimer(self)
        self._download_refresh_timer.setSingleShot(True)
        self._download_refresh_timer.setInterval(250)
        self._download_refresh_timer.timeout.connect(self._rebuild)
        self.task_statuses = RecordListModel(("value", "label", "count", "accent"))
        self.task_processes = RecordListModel(("value", "label", "count", "accent"))
        self.tasks = RecordListModel((
            "searchKey", "process", "processLabel", "processColor", "status",
            "statusColor", "assigned", "assignedLabel", "assignedAvatar",
            "assignedColor",
            "start", "startPretty", "startFull", "end", "endPretty",
            "endFull", "dueState", "progress", "description",
            "notesCount", "loggedHours", "plannedHours", "taskCode",
        ))
        self.participants = RecordListModel((
            "login", "displayName", "initials", "avatarUrl", "avatarColor", "taskCount",
            "noteCount", "snapshotCount", "hours", "cost",
        ))
        self.snapshots = RecordListModel((
            "searchKey", "title", "process", "context", "version",
            "author", "timestamp", "timestampPretty", "timestampFull",
            "previewUrl", "fileCount", "sizeText",
            "description", "repository", "isLatest", "isVersionless", "processLabel", "processColor", "modelIndex",
        ))
        self.notes = RecordListModel((
            "searchKey", "body", "author", "authorLabel", "avatarUrl",
            "initials", "authorColor", "timestamp", "timestampPretty",
            "timestampFull", "process", "taskCode", "taskTitle",
            "isTaskNote",
        ))
        self.children = RecordListModel((
            "searchKey", "title", "subtitle", "typeTitle", "typeCode",
            "relationship", "status", "accent", "previewUrl",
        ))
        self.child_types = RecordListModel((
            "value", "label", "count", "accent",
        ))
        self.snapshot_processes = RecordListModel((
            "value", "label", "accent", "snapshotCount", "fileCount", "sizeText",
            "snapshots", "files",
        ))
        self.files = RecordListModel((
            "token", "searchKey", "title", "extension", "type", "sizeText",
            "path", "repository", "exists", "previewUrl", "snapshotTitle",
            "process", "context",
        ))
        self.activity = RecordListModel((
            "searchKey", "targetSearchKey", "targetTitle", "targetType",
            "targetTypeTitle",
            "kind", "title", "detail", "actor", "actorLabel",
            "actorAvatar", "actorInitials", "actorColor", "timestamp", "timestampPretty",
            "timestampFull", "itemCode", "itemTitle", "project", "process",
            "pipelineCode", "typeColor", "processColor", "context", "version",
            "statusBefore", "statusAfter", "statusBeforeColor",
            "statusAfterColor", "changes", "canOpen",
            "taskCode", "serverGenerated", "itemType", "itemTypeTitle",
            "itemTypeColor", "relationAction", "hours", "workDay",
            "workDayPretty", "workHourAction", "workHourCategory",
            "workHourStatus", "workHourOwner",
        ))
        self.properties = RecordListModel(("label", "value"))

        state = application.workspace_state
        state.selection_changed.connect(self._selection_changed)
        state.task_model.contentReplaced.connect(self._rebuild)
        state.note_model.contentReplaced.connect(self._rebuild)
        state.snapshot_model.contentReplaced.connect(self._rebuild)
        if users is not None:
            users.users.contentReplaced.connect(self._rebuild)
        file_download_done = getattr(
            application.repository_sync, "file_download_done", None
        )
        if file_download_done is not None:
            file_download_done.connect(self._repository_file_ready)
        self._rebuild()

    @Property("QVariantMap", notify=stateChanged)
    def summary(self) -> dict:
        return dict(self._summary)

    @Property("QVariantMap", notify=stateChanged)
    def metrics(self) -> dict:
        return dict(self._metrics)

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy or self._file_worker is not None

    @Property(bool, notify=stateChanged)
    def activityHasMore(self) -> bool:
        return self._activity_has_more

    @Property(bool, notify=stateChanged)
    def activityLoadingMore(self) -> bool:
        return self._activity_loading_more

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error

    @Property(bool, notify=stateChanged)
    def hasObject(self) -> bool:
        return bool(self._summary.get("searchKey"))

    @staticmethod
    def _safe_int(value) -> int:
        try:
            return int(float(value or 0))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _safe_float(value) -> float:
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _pretty_size(value) -> str:
        size = max(0, SObjectInfoController._safe_int(value))
        units = ("B", "KB", "MB", "GB", "TB")
        number = float(size)
        for unit in units:
            if number < 1024.0 or unit == units[-1]:
                precision = 0 if unit == "B" else 1
                return f"{number:.{precision}f} {unit}"
            number /= 1024.0
        return "0 B"

    @staticmethod
    def _initials(value: str) -> str:
        words = [word for word in str(value or "").replace("_", " ").split() if word]
        return "".join(word[0] for word in words[:2]).upper() or "?"

    @staticmethod
    def _records(result) -> list:
        if not result:
            return []
        values = result[0] if isinstance(result, tuple) else result
        if isinstance(values, dict):
            return list(values.values())
        return list(values or [])

    @staticmethod
    def _object_info(value) -> dict:
        try:
            return dict(value.get_info() or {})
        except (AttributeError, TypeError, ValueError):
            return {}

    @staticmethod
    def _search_key(value) -> str:
        try:
            return str(value.get_search_key() or "")
        except (AttributeError, KeyError, TypeError):
            return ""

    def _user_records(self) -> dict[str, dict]:
        if self._users is None:
            return {}
        return {
            str(record.get("login") or ""): dict(record)
            for record in self._users.users._records
            if record.get("login")
        }

    @staticmethod
    def _pipeline(sobject):
        try:
            stype = sobject.get_stype()
            pipelines = stype.get_pipeline() or {}
            return stype, pipelines.get(sobject.get_pipeline_code())
        except (AttributeError, KeyError, TypeError):
            return None, None

    @classmethod
    def _process_style(cls, sobject, process: str) -> tuple[str, str]:
        _stype, pipeline = cls._pipeline(sobject)
        try:
            info = pipeline.get_process_info(process) or {}
            process_object = pipeline.get_pipeline_process(process) or {}
        except (AttributeError, KeyError, TypeError):
            info, process_object = {}, {}
        return (
            str(info.get("label") or process or "Unspecified"),
            str(info.get("color") or process_object.get("color") or "#607d8b"),
        )

    @classmethod
    def _status_color(cls, sobject, task, status: str, fallback: str) -> str:
        info = cls._object_info(task)
        try:
            stype = sobject.get_stype()
            workflow = stype.get_workflow()
            task_pipeline = workflow.get_by_pipeline_code(
                "sthpw/task", info.get("pipeline_code")
            )
            status_info = (task_pipeline.pipeline or {}).get(status) or {}
            return str(status_info.get("color") or fallback)
        except (AttributeError, KeyError, TypeError):
            return str(fallback or "#607d8b")

    @staticmethod
    def _loaded_snapshots(sobject) -> list[tuple[str, object]]:
        try:
            processes = sobject.get_all_processes() or {}
        except (AttributeError, KeyError, TypeError):
            processes = {}
        result = []
        seen = set()
        for process_name, process_object in processes.items():
            try:
                contexts = process_object.get_contexts() or {}
            except (AttributeError, KeyError, TypeError):
                contexts = {}
            for context in contexts.values():
                for getter in ("get_versions", "get_versionless"):
                    try:
                        values = getattr(context, getter)() or {}
                    except (AttributeError, KeyError, TypeError):
                        values = {}
                    for snapshot in values.values():
                        try:
                            code = str(snapshot.get_code() or "")
                        except (AttributeError, KeyError, TypeError):
                            code = ""
                        token = code or id(snapshot)
                        if token in seen:
                            continue
                        seen.add(token)
                        result.append((str(process_name or ""), snapshot))
        return result

    @Slot(int)
    def set_page(self, page: int) -> None:
        if not 0 <= page <= 4 or page == self._page:
            return
        self._page = page
        self._rebuild()

    @staticmethod
    def _inspect_files(files: list) -> dict:
        from .workspace_models.results_presentation import PresentationMixin

        prepared = {}
        for file_object in files:
            prepared[id(file_object)] = {
                "exists": bool(file_object.is_exists()),
                "url": (PresentationMixin._safe_file_url(file_object)
                        if PresentationMixin._is_image_file(file_object) else ""),
            }
        return prepared

    def _request_file_inspection(self, snapshots) -> None:
        from thlib.environment import env_inst
        from .workspace_models.results_presentation import PresentationMixin

        candidates = {}
        for _process, snapshot in snapshots:
            for file_object in snapshot.get_files_objects() or []:
                candidates[id(file_object)] = file_object
                preview = file_object.get_web_preview() or file_object.get_icon_preview()
                if preview:
                    candidates[id(preview)] = preview
            for preview in PresentationMixin._snapshot_preview_candidates(snapshot):
                candidates[id(preview)] = preview
        missing = [item for identity, item in candidates.items()
                   if identity not in self._file_metadata]
        if not missing or self._file_worker is not None or self._file_inspection_error:
            return
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        request_id = uuid.uuid4().hex
        worker = env_inst.server_pool.add_task(self._inspect_files, missing)
        if worker is None:
            self._error = "Server worker pool is unavailable"
            return
        self._file_request_id = request_id
        self._file_worker = worker
        worker.result.connect(
            lambda result: self._files_ready(request_id, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._files_failed(request_id, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    def _files_ready(self, request_id, result):
        if request_id != self._file_request_id:
            return
        self._file_worker = None
        self._file_metadata.update(result)
        self._rebuild()

    def _files_failed(self, request_id, error):
        if request_id != self._file_request_id:
            return
        self._file_worker = None
        self._file_inspection_error = True
        self._report_error(error)

    def _prepared_preview(self, file_object) -> str:
        from .workspace_models.results_presentation import PresentationMixin

        if not file_object or not PresentationMixin._is_image_file(file_object):
            return ""
        metadata = self._file_metadata.get(id(file_object))
        if metadata is None:
            return ""
        if metadata["url"]:
            return metadata["url"]
        sync = self._application.repository_sync
        if (id(file_object) not in self._preview_download_ids
                and sync.previews_through_http_enabled()):
            self._tracked_download_ids.add(id(file_object))
            self._preview_download_ids.add(id(file_object))
            sync.schedule_file_object(
                file_object, process="preview", auto_start=True, is_ui_preview=True,
            )
        return ""

    def _snapshot_preview(self, snapshot) -> str:
        from .workspace_models.results_presentation import PresentationMixin

        return next((url for candidate in PresentationMixin._snapshot_preview_candidates(snapshot)
                     if (url := self._prepared_preview(candidate))), "")

    def _file_preview(self, file_object) -> str:
        return self._prepared_preview(
            file_object.get_web_preview() or file_object.get_icon_preview() or file_object
        )

    def _root_preview(self, sobject, search_key: str) -> str:
        # The browser owns object preview discovery. Reuse its cached URL;
        # rebuilding a report must not probe repository paths on the Qt thread.
        return str(self._application.workspace_model.preview_url_for_search_key(search_key) or "")

    @Slot()
    def shutdown(self) -> None:
        self._request_id = self._file_request_id = self._activity_request_id = ""
        self._download_refresh_timer.stop()
        for worker in (self._worker, self._file_worker, self._activity_worker):
            if worker is not None:
                worker.cancel()
        self._worker = self._file_worker = self._activity_worker = None

    def _selection_changed(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
        if self._file_worker is not None:
            self._file_worker.cancel()
        self._file_worker = None
        self._file_request_id = ""
        self._file_metadata.clear()
        self._tracked_download_ids.clear()
        self._preview_download_ids.clear()
        self._file_inspection_error = False
        for page, model in ((0, self.tasks), (1, self.notes), (2, self.children),
                            (3, self.snapshots), (3, self.snapshot_processes),
                            (3, self.files), (4, self.activity)):
            if page != self._page:
                model.clear()
        self._refreshed_tasks = None
        self._refreshed_notes = None
        self._refreshed_children = None
        self._refreshed_work_hours = None
        self._refreshed_activity = None
        self._activity_has_more = False
        self._activity_loading_more = False
        self._activity_offset = 0
        self._activity_request_id = ""
        if self._activity_worker is not None:
            cancel = getattr(self._activity_worker, "cancel", None)
            if cancel is not None:
                cancel()
        self._activity_worker = None
        self._error = ""
        self._request_id = uuid.uuid4().hex
        self._busy = False
        self._worker = None
        windows = getattr(self._application, "window_model", None)
        if windows and windows.is_window_visible("sobject_info"):
            self.refresh()
        self._rebuild()

    @Slot()
    def window_opened(self) -> None:
        self._rebuild()
        self.refresh()

    def _window_visible(self) -> bool:
        windows = getattr(self._application, "window_model", None)
        if windows is None:
            return True
        try:
            return bool(windows.is_window_visible("sobject_info"))
        except (AttributeError, RuntimeError, TypeError):
            return False

    def _rebuild(self) -> None:
        if getattr(
            self._application.workspace_state,
            "_selection_projection_restoring",
            False,
        ):
            self._projection_dirty = True
            return
        # This report walks every task, status log, snapshot and file. Keeping
        # it hot while its native window is closed made an unrelated Search
        # Tab switch pay the full report cost several times in one signal turn.
        if not self._window_visible():
            self._projection_dirty = True
            return
        self._projection_dirty = False
        state = self._application.workspace_state
        sobject = getattr(state, "_selected_sobject", None)
        if not sobject:
            self._clear()
            return

        info = self._object_info(sobject)
        search_key = self._search_key(sobject)
        title = str(sobject.get_title() or sobject.get_code() or "")
        search_type = str(
            info.get("__search_type__")
            or search_key.removeprefix("skey://").split("?", 1)[0]
        )
        try:
            stype = sobject.get_stype()
            type_title = str(stype.get_pretty_name() or search_type)
            accent = str(stype.get_stype_color(fmt="hex") or "#607d8b")
        except (AttributeError, KeyError, TypeError):
            type_title = search_type.split("/")[-1].replace("_", " ").title()
            accent = "#607d8b"
        try:
            project = sobject.get_project()
            project_title = str(project.get_title() or project.get_code() or "")
            project_code = str(project.get_code() or "")
        except (AttributeError, KeyError, TypeError):
            project_title = str(info.get("project_code") or "")
            project_code = project_title

        tasks = list(
            self._refreshed_tasks
            if self._refreshed_tasks is not None
            else getattr(state, "_task_sobjects", ())
        )
        notes = list(
            self._refreshed_notes
            if self._refreshed_notes is not None
            else getattr(state, "_note_sobjects", ())
        )
        snapshot_objects = self._loaded_snapshots(sobject)
        if self._page == 3:
            self._request_file_inspection(snapshot_objects)
        users = self._user_records()
        work_result = dict(self._refreshed_work_hours or {})
        work_entries = list(work_result.get("entries") or [])
        work_permissions = dict(work_result.get("permissions") or {})
        work_rates = dict(work_result.get("rates") or {})
        can_view_costs = bool(work_permissions.get("viewCosts"))
        task_hours: dict[str, float] = {}
        participant_hours: dict[str, float] = {}
        participant_costs: dict[str, float] = {}
        total_hours = 0.0
        total_cost = 0.0
        for entry in work_entries:
            try:
                task_code = str(entry.get_value("task_code") or "")
                login = str(entry.get_value("login") or "")
                hours = float(entry.get_total_hours() or 0.0)
            except (AttributeError, TypeError, ValueError):
                continue
            total_hours += hours
            task_hours[task_code] = task_hours.get(task_code, 0.0) + hours
            if login:
                participant_hours[login] = (
                    participant_hours.get(login, 0.0) + hours
                )
            if can_view_costs and login:
                try:
                    cost = float(entry.get_labor_cost(work_rates.get(login)))
                except (AttributeError, TypeError, ValueError):
                    cost = 0.0
                total_cost += cost
                participant_costs[login] = (
                    participant_costs.get(login, 0.0) + cost
                )

        status_counts: dict[str, dict] = {}
        process_counts: dict[str, dict] = {}
        participant_counts: dict[str, dict] = {}
        activity_values = []
        task_records = []
        active_tasks = 0
        completed_tasks = 0
        overdue_tasks = 0
        unassigned_tasks = 0
        due_this_week = 0
        progress_total = 0
        today = date.today()
        week_end = today + timedelta(days=6 - today.weekday())
        root_code = str(info.get("code") or "")
        task_by_code = {
            str(self._object_info(task).get("code") or ""): task
            for task in tasks
            if self._object_info(task).get("code")
        }
        notes_by_parent: dict[str, list] = {}
        for note in notes:
            parent_code = str(self._object_info(note).get("search_code") or "")
            notes_by_parent.setdefault(parent_code, []).append(note)

        for task in tasks:
            task_info = self._object_info(task)
            task_code = str(task_info.get("code") or "")
            process = str(task_info.get("process") or "")
            process_label, process_color = self._process_style(sobject, process)
            process_bucket = process_counts.setdefault(process, {
                "value": process, "label": process_label, "count": 0, "accent": process_color,
            })
            process_bucket["count"] += 1
            status = str(task_info.get("status") or "Unspecified")
            status_bucket = status_counts.setdefault(status, {
                "value": status,
                "label": status,
                "count": 0,
                "accent": self._status_color(
                    sobject, task, status, process_color
                ),
            })
            status_bucket["count"] += 1
            assigned = str(
                task_info.get("assigned") or task_info.get("login") or ""
            )
            progress = progress_value(task_info)
            end = str(
                task_info.get("bid_end_date") or task_info.get("end_date") or ""
            )
            start = str(
                task_info.get("bid_start_date") or task_info.get("start_date") or ""
            )
            # Planned task dates are calendar values, not server instants.
            start_pretty, start_full = activity_timestamp_labels(start)
            end_pretty, end_full = activity_timestamp_labels(end)
            task_due_state = due_state(end)
            progress_total += progress
            if progress >= 100:
                completed_tasks += 1
            else:
                active_tasks += 1
                if task_due_state == "overdue":
                    overdue_tasks += 1
                deadline = parse_datetime(end)
                if deadline and today <= deadline.date() <= week_end:
                    due_this_week += 1
            if not assigned:
                unassigned_tasks += 1
            if assigned:
                participant_counts.setdefault(assigned, {
                    "taskCount": 0, "noteCount": 0, "snapshotCount": 0,
                })["taskCount"] += 1
            notes_count = len(notes_by_parent.get(task_code, ()))
            user = users.get(assigned, {})
            if self._page == 0:
                task_records.append({
                    "searchKey": self._search_key(task),
                    "process": process,
                    "processLabel": process_label,
                    "processColor": process_color,
                    "status": status,
                    "statusColor": status_bucket["accent"],
                    "assigned": assigned,
                    "assignedLabel": str(
                        user.get("displayName") or assigned or "Not assigned"
                    ),
                    "assignedAvatar": str(user.get("avatarUrl") or ""),
                    "assignedColor": str(
                        user.get("avatarColor") or user_avatar_color(assigned)
                    ),
                    "start": start,
                    "startPretty": start_pretty,
                    "startFull": start_full,
                    "end": end,
                    "endPretty": end_pretty,
                    "endFull": end_full,
                    "dueState": task_due_state,
                    "progress": progress,
                    "description": str(task_info.get("description") or ""),
                    "notesCount": notes_count,
                    "loggedHours": float(task_hours.get(task_code, 0.0)),
                    "plannedHours": self._safe_float(task_info.get("bid_duration")),
                    "taskCode": task_code,
                })

            try:
                status_logs = (
                    task.get_status_log() or []
                    if self._page == 4 and self._refreshed_activity is None else []
                )
                if isinstance(status_logs, dict):
                    status_logs = list(status_logs.values())
            except (AttributeError, KeyError, TypeError):
                status_logs = []
            for status_log in status_logs:
                status_info = self._object_info(status_log)
                status_to = str(
                    status_info.get("to_status") or status_info.get("status") or ""
                )
                status_from = str(status_info.get("from_status") or "")
                transition = " → ".join(
                    value for value in (status_from, status_to) if value
                )
                status_key = self._search_key(status_log)
                if self._page == 4:
                    activity_values.append(activity_record({
                        "eventId": status_key or (
                            f"{self._search_key(task)}:{status_info.get('timestamp')}:{status_to}"
                        ),
                        "kind": "status",
                        "title": status_to or process_label,
                        "detail": " · ".join(
                            value for value in (process_label, transition) if value
                        ),
                        "actor": str(status_info.get("login") or ""),
                        "timestamp": str(status_info.get("timestamp") or ""),
                        "itemCode": task_code,
                        "itemTitle": task_code or process_label,
                        "searchKey": status_key or self._search_key(task),
                        "targetSearchKey": search_key,
                        "targetTitle": title,
                        "targetType": search_type,
                        "project": project_code,
                        "process": process,
                        "taskCode": task_code,
                        "statusBefore": status_from,
                        "statusAfter": status_to,
                    }, clock=self._clock))

        note_records = []
        for note in notes:
            note_info = self._object_info(note)
            parent_code = str(note_info.get("search_code") or "")
            task = task_by_code.get(parent_code)
            task_info = self._object_info(task)
            task_process = str(task_info.get("process") or "")
            process = str(note_info.get("process") or task_process)
            process_label, _process_color = self._process_style(
                sobject, process
            )
            author = str(note_info.get("login") or note_info.get("author") or "")
            user = users.get(author, {})
            task_title = process_label if task is not None else ""
            if author:
                participant_counts.setdefault(author, {
                    "taskCount": 0, "noteCount": 0, "snapshotCount": 0,
                })["noteCount"] += 1
            note_timestamp = str(note_info.get("timestamp") or "")
            note_timestamp_pretty, note_timestamp_full = (
                activity_timestamp_labels(note_timestamp, self._clock)
            )
            if self._page == 1:
                note_records.append({
                    "searchKey": self._search_key(note),
                    "body": str(note_info.get("note") or ""),
                    "author": author,
                    "authorLabel": str(user.get("displayName") or author),
                    "avatarUrl": str(user.get("avatarUrl") or ""),
                    "initials": str(user.get("initials") or self._initials(
                        user.get("displayName") or author
                    )),
                    "authorColor": str(
                        user.get("avatarColor") or user_avatar_color(author)
                    ),
                    "timestamp": note_timestamp,
                    "timestampPretty": note_timestamp_pretty,
                    "timestampFull": note_timestamp_full,
                    "process": process,
                    "taskCode": parent_code if task is not None else "",
                    "taskTitle": task_title,
                    "isTaskNote": task is not None,
                })
            if self._page == 4:
                activity_values.append(activity_record({
                    "eventId": self._search_key(note),
                    "kind": "note",
                    "title": "Added note",
                    "detail": str(note_info.get("note") or ""),
                    "actor": author,
                    "timestamp": str(note_info.get("timestamp") or ""),
                    "itemCode": str(note_info.get("code") or ""),
                    "itemTitle": str(note_info.get("code") or ""),
                    "searchKey": self._search_key(note),
                    "targetSearchKey": search_key,
                    "targetTitle": title,
                    "targetType": search_type,
                    "project": project_code,
                    "process": process,
                    "context": str(note_info.get("context") or ""),
                    "taskCode": parent_code if task is not None else "",
                }, clock=self._clock))

        child_records = []
        child_type_counts: dict[str, dict] = {}
        seen_children = set()
        for relation, child_stype, child in list(
                self._refreshed_children or ()):
            child_key = self._search_key(child)
            if not child_key or child_key in seen_children:
                continue
            seen_children.add(child_key)
            child_info = self._object_info(child)
            try:
                child_type_code = str(child_stype.get_code() or "")
                child_type_title = str(
                    child_stype.get_pretty_name() or child_type_code
                )
                child_accent = str(
                    child_stype.get_stype_color(fmt="hex") or accent
                )
            except (AttributeError, KeyError, TypeError):
                child_type_code = str(relation.get("from") or "")
                child_type_title = child_type_code
                child_accent = accent
            relationship = str(
                relation.get("relationship") or relation.get("type") or ""
            )
            child_type_counts.setdefault(child_type_code, {
                "value": child_type_code,
                "label": child_type_title,
                "count": 0,
                "accent": child_accent,
            })["count"] += 1
            try:
                child_title = str(
                    child.get_title() or child.get_code() or child_key
                )
            except (AttributeError, KeyError, TypeError):
                child_title = str(child_info.get("name") or child_info.get("code") or child_key)
            if self._page == 2:
                child_records.append({
                    "searchKey": child_key,
                    "title": child_title,
                    "subtitle": str(
                        child_info.get("description") or child_info.get("code") or ""
                    ),
                    "typeTitle": child_type_title,
                    "typeCode": child_type_code,
                    "relationship": relationship,
                    "status": str(child_info.get("status") or ""),
                    "accent": child_accent,
                    "previewUrl": self._root_preview(child, child_key),
                })
        child_records.sort(key=lambda item: (
            item["typeTitle"].lower(), item["title"].lower()
        ))
        snapshot_records = []
        file_records = []
        self._file_objects = {}
        total_size = 0
        primary_file_count = 0
        latest_version = 0
        snapshot_process_counts: dict[str, dict] = {}
        snapshot_count = 0
        for process_name, snapshot in snapshot_objects:
            try:
                snapshot_info = dict(snapshot.get_snapshot() or {})
                snapshot_key = str(snapshot.get_search_key() or "")
                version_number = self._safe_int(snapshot.get_version())
                is_versionless = bool(snapshot.is_versionless())
                is_latest = bool(snapshot.is_latest())
                all_files = list(snapshot.get_files_objects() or [])
            except (AttributeError, KeyError, TypeError, ValueError):
                continue
            if not is_versionless:
                latest_version = max(latest_version, version_number)
            snapshot_count += 1
            primary_files = []
            for file_object in all_files:
                try:
                    file_type = str(file_object.get_type() or "")
                except (AttributeError, KeyError, TypeError):
                    file_type = ""
                if file_type not in {"icon", "web"}:
                    primary_files.append(file_object)
            display_files = primary_files or all_files
            snapshot_size = 0
            for file_index, file_object in enumerate(display_files):
                try:
                    file_size = self._safe_int(file_object.get_file_size())
                    filename = str(file_object.get_filename_with_ext() or "")
                    extension = str(file_object.get_ext() or "")
                    file_type = str(file_object.get_type() or "")
                    path = str(file_object.get_full_abs_path() or "")
                    exists = bool((self._file_metadata.get(id(file_object)) or {}).get("exists"))
                except (AttributeError, KeyError, TypeError, OSError, ValueError):
                    continue
                token = f"{snapshot_key}:{file_index}:{filename}"
                self._file_objects[token] = file_object
                self._tracked_download_ids.add(id(file_object))
                snapshot_size += file_size
                total_size += file_size
                primary_file_count += 1
                if self._page == 3:
                    file_records.append({
                        "token": token,
                        "searchKey": self._search_key(file_object),
                        "title": filename,
                        "extension": extension,
                        "type": file_type,
                        "sizeText": self._pretty_size(file_size),
                        "path": path,
                        "repository": str(snapshot_info.get("repo") or "base"),
                        "exists": exists,
                        "previewUrl": self._file_preview(file_object) if self._page == 3 else "",
                        "snapshotTitle": str(
                            snapshot_info.get("description")
                            or snapshot_info.get("context") or process_name
                        ),
                        "process": process_name,
                        "context": str(snapshot_info.get("context") or ""),
                    })
            author = str(snapshot_info.get("login") or "")
            if author:
                participant_counts.setdefault(author, {
                    "taskCount": 0, "noteCount": 0, "snapshotCount": 0,
                })["snapshotCount"] += 1
            context = str(snapshot_info.get("context") or process_name)
            version_text = "Current" if is_versionless else f"v{version_number:03d}"
            snapshot_title = str(
                snapshot_info.get("description") or context or process_name
            )
            process_label, process_color = self._process_style(
                sobject, process_name
            )
            process_bucket = snapshot_process_counts.setdefault(process_name, {
                "value": process_name,
                "label": process_label,
                "accent": process_color,
                "snapshotCount": 0,
                "fileCount": 0,
                "size": 0,
            })
            process_bucket["snapshotCount"] += 1
            process_bucket["fileCount"] += len(display_files)
            process_bucket["size"] += snapshot_size
            snapshot_timestamp = str(snapshot_info.get("timestamp") or "")
            snapshot_timestamp_pretty, snapshot_timestamp_full = (
                activity_timestamp_labels(snapshot_timestamp, self._clock)
            )
            if self._page == 3:
                snapshot_records.append({
                    "searchKey": snapshot_key,
                    "title": snapshot_title,
                    "process": process_name,
                    "context": context,
                    "version": version_text,
                    "author": users.get(author, {}).get("displayName") or author,
                    "timestamp": snapshot_timestamp,
                    "timestampPretty": snapshot_timestamp_pretty,
                    "timestampFull": snapshot_timestamp_full,
                    "previewUrl": self._snapshot_preview(snapshot) if self._page == 3 else "",
                    "fileCount": len(display_files),
                    "sizeText": self._pretty_size(snapshot_size),
                    "description": str(snapshot_info.get("description") or ""),
                    "repository": str(snapshot_info.get("repo") or "base"),
                    "isLatest": is_latest,
                    "isVersionless": is_versionless,
                    "processLabel": process_label,
                    "processColor": process_color,
                })
            if self._page == 4:
                activity_values.append(activity_record({
                    "eventId": snapshot_key,
                    "kind": "publication",
                    "title": "Published snapshot",
                    "detail": snapshot_title,
                    "actor": author,
                    "timestamp": str(snapshot_info.get("timestamp") or ""),
                    "itemCode": str(snapshot_info.get("code") or ""),
                    "itemTitle": snapshot_title,
                    "searchKey": snapshot_key,
                    "targetSearchKey": search_key,
                    "targetTitle": title,
                    "targetType": search_type,
                    "project": project_code,
                    "process": process_name,
                    "context": context,
                    "version": version_text,
                }, clock=self._clock))

        for login in participant_hours:
            participant_counts.setdefault(login, {
                "taskCount": 0, "noteCount": 0, "snapshotCount": 0,
            })
        participants = []
        for login, counts in participant_counts.items():
            record = users.get(login, {})
            display_name = str(record.get("displayName") or login)
            participants.append({
                "login": login,
                "displayName": display_name,
                "initials": str(record.get("initials") or self._initials(display_name)),
                "avatarUrl": str(record.get("avatarUrl") or ""),
                "avatarColor": str(
                    record.get("avatarColor") or user_avatar_color(login)
                ),
                **counts,
                "hours": float(participant_hours.get(login, 0.0)),
                "cost": float(participant_costs.get(login, 0.0)),
            })
        participants.sort(
            key=lambda item: (
                -(item["taskCount"] + item["noteCount"] + item["snapshotCount"]),
                item["displayName"].lower(),
            )
        )
        snapshot_records.sort(key=lambda item: item["timestamp"], reverse=True)
        snapshot_records.sort(key=lambda item: item["processLabel"].lower())
        snapshots_by_process: dict[str, list[dict]] = {}
        for model_index, snapshot_record in enumerate(snapshot_records):
            snapshot_record["modelIndex"] = model_index
            snapshots_by_process.setdefault(
                snapshot_record["process"], []
            ).append(dict(snapshot_record))
        files_by_process: dict[str, list[dict]] = {}
        for file_record in file_records:
            files_by_process.setdefault(file_record["process"], []).append(
                dict(file_record)
            )
        for process_files in files_by_process.values():
            process_files.sort(key=lambda item: item["title"].lower())
        snapshot_process_records = []
        for bucket in snapshot_process_counts.values():
            record = dict(bucket)
            record["sizeText"] = self._pretty_size(record.pop("size", 0))
            record["snapshots"] = snapshots_by_process.get(record["value"], [])
            record["files"] = files_by_process.get(record["value"], [])
            snapshot_process_records.append(record)
        snapshot_process_records.sort(key=lambda item: item["label"].lower())
        file_records.sort(key=lambda item: item["title"].lower())
        if self._page == 4 and self._refreshed_activity is not None:
            activity_values = [
                activity_record(record)
                for record in self._refreshed_activity
            ]
        activity_values = present_activity_records(
            activity_values, users.values()
        )
        activity_values.sort(
            key=lambda item: item.get("timestamp") or "", reverse=True
        )

        excluded = {
            "id", "code", "name", "title", "description", "pipeline_code",
            "project_code", "timestamp", "last_updated", "__snapshots__",
            "__notes_count__", "__tasks_count__", "snapshot", "metadata", "skey", "search_key", "search_type",
        }
        property_records = []
        for key, value in info.items():
            if key.startswith("__") or key in excluded or value in (None, "", [], {}):
                continue
            if not isinstance(value, (str, int, float, bool)):
                continue
            property_records.append({
                "label": str(key).replace("_", " ").title(),
                "value": str(value),
            })
        property_records.sort(key=lambda item: item["label"].lower())

        updated = str(
            info.get("last_updated") or info.get("timestamp") or ""
        )
        updated_pretty, updated_full = activity_timestamp_labels(
            updated, self._clock
        )
        self._summary = {
            "title": title,
            "code": str(info.get("code") or ""),
            "searchKey": search_key,
            "searchType": search_type,
            "typeTitle": type_title,
            "pipeline": str(info.get("pipeline_code") or ""),
            "project": project_title,
            "description": str(info.get("description") or ""),
            "previewUrl": self._root_preview(sobject, search_key),
            "accent": accent,
            "timestamp": str(info.get("timestamp") or ""),
            "updated": updated,
            "updatedPretty": updated_pretty,
            "updatedFull": updated_full,
        }
        self._metrics = {
            "tasks": len(tasks),
            "activeTasks": active_tasks,
            "completedTasks": completed_tasks,
            "overdueTasks": overdue_tasks,
            "unassignedTasks": unassigned_tasks,
            "dueThisWeek": due_this_week,
            "averageProgress": int(round(progress_total / len(tasks))) if tasks else 0,
            "notes": len(notes),
            "objectNotes": len(notes_by_parent.get(root_code, ())),
            "taskNotes": sum(
                len(notes_by_parent.get(code, ())) for code in task_by_code
            ),
            "children": len(seen_children),
            "childTypes": len(child_type_counts),
            "workHours": round(total_hours, 2),
            "totalCost": round(total_cost, 2),
            "canViewCosts": can_view_costs,
            "snapshots": snapshot_count,
            "files": primary_file_count,
            "participants": len(participants),
            "processes": len(process_counts),
            "totalSize": self._pretty_size(total_size),
            "latestVersion": f"v{latest_version:03d}" if latest_version else "—",
            "snapshotProcesses": len(snapshot_process_records),
        }
        self.task_statuses.replace(sorted(
            status_counts.values(), key=lambda item: (-item["count"], item["label"])
        ))
        self.task_processes.replace(sorted(
            process_counts.values(), key=lambda item: (-item["count"], item["label"])
        ))
        if self._page == 0:
            self.tasks.replace(task_records)
        elif self._page == 1:
            self.notes.replace(note_records)
        elif self._page == 2:
            self.children.replace(child_records)
        self.child_types.replace(sorted(
            child_type_counts.values(), key=lambda item: item["label"].lower()
        ))
        self.participants.replace(participants)
        if self._page == 3:
            self.snapshots.replace(snapshot_records)
            self.snapshot_processes.replace(snapshot_process_records)
            self.files.replace(file_records)
        elif self._page == 4:
            self.activity.replace(activity_values)
        self.properties.replace(property_records[:24])
        self.stateChanged.emit()

    def _clear(self) -> None:
        changed = bool(self._summary or self._metrics)
        self._summary = {}
        self._metrics = {}
        self._file_objects = {}
        self._file_metadata.clear()
        self._tracked_download_ids = set()
        self._preview_download_ids.clear()
        self._activity_has_more = False
        self._activity_loading_more = False
        self._activity_offset = 0
        self._activity_request_id = ""
        self._activity_worker = None
        for model in (
            self.task_statuses, self.task_processes, self.tasks, self.participants,
            self.notes, self.children, self.child_types, self.snapshots,
            self.snapshot_processes, self.files, self.activity, self.properties,
        ):
            model.clear()
        if changed:
            self.stateChanged.emit()

    @classmethod
    def _query_related_children(
        cls, sobject, force=False
    ) -> list[tuple[dict, object, object]]:
        stype = sobject.get_stype()
        project = stype.get_project()
        stypes = project.get_stypes() or {}
        schema = stype.get_schema()
        children = []
        for relation in list(schema.get_children() or ()):
            # The native relation tree does not resolve many-to-many schema
            # entries through SObject.get_related_sobjects(). Those entries
            # require their instance owner and must not abort the remaining
            # direct child relations in this report.
            if relation.get("type") == "many_to_many":
                continue
            child_code = str(relation.get("from") or "")
            child_stype = stypes.get(child_code)
            if not child_code or child_stype is None:
                continue
            kwargs = dict(
                child_stype=child_stype,
                parent_stype=stype,
                path="child",
                get_all_snapshots=True,
            )
            if force:
                kwargs["force"] = True
            related = cls._records(sobject.get_related_sobjects(**kwargs))
            children.extend(
                (dict(relation), child_stype, child)
                for child in related
            )
        return children

    @classmethod
    def _activity_scope(cls, sobject) -> tuple[dict, dict]:
        """Describe the root and schema relations for server-side audit."""
        info = cls._object_info(sobject)
        search_key = cls._search_key(sobject)
        search_type = str(
            info.get("__search_type__")
            or search_key.removeprefix("skey://").split("?", 1)[0]
        ).split("?", 1)[0]
        search_code = str(info.get("code") or "")
        search_id = str(info.get("id") or "")
        child_types = set()
        instance_relations = {}
        try:
            stype = sobject.get_stype()
            schema = stype.get_schema()
            definitions = [
                ("children", definition)
                for definition in list(schema.get_children() or ())
            ] + [
                ("parents", definition)
                for definition in list(schema.get_parents() or ())
            ]
        except (AttributeError, KeyError, TypeError):
            definitions = []
        for direction, raw_definition in definitions:
            definition = dict(raw_definition or {})
            from_type = str(definition.get("from") or "").split("?", 1)[0]
            to_type = str(definition.get("to") or "").split("?", 1)[0]
            relationship = str(definition.get("relationship") or "")
            if direction == "children" and from_type:
                child_types.add(from_type)
            if relationship != "instance":
                continue
            instance_type = str(definition.get("instance_type") or "")
            endpoints = [
                value for value in (
                    (from_type, search_type)
                    if direction == "children" else
                    (search_type, to_type)
                ) if value
            ]
            if (
                    instance_type and len(endpoints) == 2
                    and search_type in endpoints):
                instance_relations[instance_type] = endpoints
        return ({
            "searchType": search_type,
            "searchCode": search_code,
            "searchId": search_id,
            "childTypes": sorted(child_types),
        }, instance_relations)

    @classmethod
    def _activity_reference(cls, value, fallback_type: str = "") -> dict:
        info = cls._object_info(value)
        if not info:
            try:
                info = dict(value.get_snapshot() or {})
            except (AttributeError, TypeError, ValueError):
                info = {}
        search_key = cls._search_key(value)
        search_type = str(
            info.get("__search_type__")
            or search_key.removeprefix("skey://").split("?", 1)[0]
            or fallback_type
        ).split("?", 1)[0]
        code = str(info.get("code") or "")
        if not code:
            try:
                code = str(value.get_code() or "")
            except (AttributeError, TypeError, ValueError):
                code = ""
        search_id = str(info.get("id") or "")
        if not search_type or not (code or search_id):
            return {}
        return {
            "searchType": search_type,
            "searchCode": code,
            "searchId": search_id,
        }

    @classmethod
    def _activity_query_context(
            cls, sobject, task_objects, note_objects, child_objects,
            work_hours) -> tuple[dict, dict]:
        object_scope, instance_relations = cls._activity_scope(sobject)
        indexed_objects = []
        seen_references = set()

        def add_reference(value, fallback_type=""):
            reference = cls._activity_reference(value, fallback_type)
            identity = (
                reference.get("searchType"),
                reference.get("searchCode"),
                reference.get("searchId"),
            )
            if not reference or identity in seen_references:
                return
            seen_references.add(identity)
            indexed_objects.append(reference)

        add_reference(sobject, object_scope.get("searchType") or "")
        for task in task_objects:
            add_reference(task, "sthpw/task")
        for note in note_objects:
            add_reference(note, "sthpw/note")
        for _process, snapshot in cls._loaded_snapshots(sobject):
            add_reference(snapshot, "sthpw/snapshot")
        for relation, child_stype, child in child_objects:
            try:
                child_type = str(child_stype.get_code() or "")
            except (AttributeError, TypeError, ValueError):
                child_type = str((relation or {}).get("from") or "")
            add_reference(child, child_type)
        work_entries = list(dict(work_hours or {}).get("entries") or [])
        for entry in work_entries:
            add_reference(entry, "sthpw/work_hour")

        object_scope["indexedObjects"] = indexed_objects
        object_scope["taskCodes"] = [
            reference["searchCode"] for reference in indexed_objects
            if reference.get("searchType") == "sthpw/task"
            and reference.get("searchCode")
        ]
        object_scope["taskIds"] = [
            reference["searchId"] for reference in indexed_objects
            if reference.get("searchType") == "sthpw/task"
            and reference.get("searchId")
        ]
        object_scope["noteCodes"] = [
            reference["searchCode"] for reference in indexed_objects
            if reference.get("searchType") == "sthpw/note"
            and reference.get("searchCode")
        ]
        object_scope["snapshotCodes"] = [
            reference["searchCode"] for reference in indexed_objects
            if reference.get("searchType") == "sthpw/snapshot"
            and reference.get("searchCode")
        ]
        object_scope["workHourCodes"] = [
            reference["searchCode"] for reference in indexed_objects
            if reference.get("searchType") == "sthpw/work_hour"
            and reference.get("searchCode")
        ]
        return object_scope, instance_relations

    @Slot()
    def refresh(self) -> None:
        state = self._application.workspace_state
        sobject = getattr(state, "_selected_sobject", None)
        if not sobject or self._busy:
            return
        self._file_inspection_error = False
        from thlib.environment import env_inst

        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        request_id = uuid.uuid4().hex
        selected_key = self._search_key(sobject)
        page_size = self._activity_page_size

        if self._activity_worker is not None:
            cancel = getattr(self._activity_worker, "cancel", None)
            if cancel is not None:
                cancel()
        self._activity_worker = None
        self._activity_loading_more = False
        self._activity_request_id = ""

        def operation():
            from thlib import tactic_classes as tc

            task_objects = self._records(sobject.get_tasks_sobjects(
                process=None, include_status_log=True
            ))
            project = sobject.get_project()
            project_code = str(project.get_code() or "")
            root_code = str(sobject.get_code() or "")
            root_id = str(self._object_info(sobject).get("id") or "")
            task_codes = [
                str(self._object_info(task).get("code") or "")
                for task in task_objects
            ]
            task_ids = [
                str(self._object_info(task).get("id") or "")
                for task in task_objects
            ]
            note_parent_ids = [
                value for value in [root_id, *task_ids] if value
            ]
            note_parent_codes = [
                code for code in [root_code, *task_codes] if code
            ]
            note_parent_field = (
                "search_id" if note_parent_ids else "search_code"
            )
            note_parent_values = (
                note_parent_ids if note_parent_ids else note_parent_codes
            )
            note_objects = self._records(tc.get_sobjects(
                "sthpw/note",
                filters=[
                    (
                        note_parent_field, "in",
                        "|".join(note_parent_values),
                    ),
                    ("project_code", project_code),
                ],
                include_snapshots=False,
                project_code=project_code,
            )) if note_parent_values else []

            child_objects = self._query_related_children(sobject, force=True)

            sobject.update_snapshots(
                order_bys=["timestamp desc"], force=True
            )

            work_hours = tc.query_work_hours(
                [], project_code, include_rates=True,
                parent_codes=[root_code],
            )
            object_scope, instance_relations = self._activity_query_context(
                sobject, task_objects, note_objects, child_objects,
                work_hours,
            )
            activity = tc.get_user_recent_activity(
                project_code=project_code,
                limit=page_size + 1,
                offset=0,
                kinds=(
                    "status", "publication", "note", "task",
                    "create", "change", "delete", "work_hour",
                ),
                instance_relations=instance_relations,
                object_scope=object_scope,
            )
            activity = list(activity or [])
            return {
                "searchKey": selected_key,
                "tasks": task_objects,
                "notes": note_objects,
                "children": child_objects,
                "workHours": work_hours,
                "activity": activity[:page_size],
                "activityHasMore": len(activity) > page_size,
                "activityOffset": min(len(activity), page_size),
            }
        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            self._error = "Server worker pool is unavailable"
            self.stateChanged.emit()
            return
        self._request_id = request_id
        self._worker = worker
        self._busy = True
        self._error = ""
        self.stateChanged.emit()
        worker.result.connect(
            lambda result: self._refresh_ready(request_id, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._refresh_failed(request_id, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    def _refresh_ready(self, request_id: str, result) -> None:
        if request_id != self._request_id:
            return
        result = dict(result or {})
        search_key = str(result.get("searchKey") or "")
        current = getattr(self._application.workspace_state, "_selected_sobject", None)
        if current and self._search_key(current) == search_key:
            self._refreshed_tasks = list(result.get("tasks") or [])
            self._refreshed_notes = list(result.get("notes") or [])
            self._refreshed_children = list(result.get("children") or [])
            self._refreshed_work_hours = dict(result.get("workHours") or {})
            self._refreshed_activity = list(result.get("activity") or [])
            self._activity_has_more = bool(
                result.get("activityHasMore")
            )
            self._activity_offset = int(
                result.get("activityOffset")
                or len(self._refreshed_activity)
            )
        self._worker = None
        self._busy = False
        self._error = ""
        self._rebuild()

    @Slot()
    def load_more_activity(self) -> None:
        state = self._application.workspace_state
        sobject = getattr(state, "_selected_sobject", None)
        if (
                not sobject or self._busy or self._activity_loading_more
                or not self._activity_has_more
                or self._refreshed_activity is None):
            return
        from thlib.environment import env_inst

        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        request_id = uuid.uuid4().hex
        selected_key = self._search_key(sobject)
        page_size = self._activity_page_size
        offset = self._activity_offset
        task_objects = list(self._refreshed_tasks or [])
        note_objects = list(self._refreshed_notes or [])
        child_objects = list(self._refreshed_children or [])
        work_hours = dict(self._refreshed_work_hours or {})

        def operation():
            from thlib import tactic_classes as tc

            project = sobject.get_project()
            project_code = str(project.get_code() or "")
            object_scope, instance_relations = self._activity_query_context(
                sobject, task_objects, note_objects, child_objects,
                work_hours,
            )
            activity = list(tc.get_user_recent_activity(
                project_code=project_code,
                limit=page_size + 1,
                offset=offset,
                kinds=(
                    "status", "publication", "note", "task",
                    "create", "change", "delete", "work_hour",
                ),
                instance_relations=instance_relations,
                object_scope=object_scope,
            ) or [])
            return {
                "searchKey": selected_key,
                "activity": activity[:page_size],
                "activityHasMore": len(activity) > page_size,
                "consumed": min(len(activity), page_size),
            }

        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            self._error = "Server worker pool is unavailable"
            self.stateChanged.emit()
            return
        self._activity_request_id = request_id
        self._activity_worker = worker
        self._activity_loading_more = True
        self._error = ""
        self.stateChanged.emit()
        worker.result.connect(
            lambda result: self._activity_page_ready(
                request_id, offset, result
            ),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._activity_page_failed(request_id, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    def _activity_page_ready(
            self, request_id: str, offset: int, result) -> None:
        if request_id != self._activity_request_id:
            return
        result = dict(result or {})
        current = getattr(
            self._application.workspace_state, "_selected_sobject", None
        )
        if (
                not current
                or self._search_key(current)
                != str(result.get("searchKey") or "")):
            self._activity_loading_more = False
            self._activity_request_id = ""
            self._activity_worker = None
            self.stateChanged.emit()
            return
        existing = list(self._refreshed_activity or [])
        seen = {
            str(record.get("eventId") or "")
            for record in existing if record.get("eventId")
        }
        for record in result.get("activity") or []:
            event_id = str(record.get("eventId") or "")
            if event_id and event_id in seen:
                continue
            if event_id:
                seen.add(event_id)
            existing.append(dict(record))
        self._refreshed_activity = existing
        self._activity_offset = offset + int(result.get("consumed") or 0)
        self._activity_has_more = bool(result.get("activityHasMore"))
        self._activity_loading_more = False
        self._activity_request_id = ""
        self._activity_worker = None
        self._error = ""
        self._rebuild()

    def _activity_page_failed(self, request_id: str, error) -> None:
        if request_id != self._activity_request_id:
            return
        payload = error[0] if isinstance(error, tuple) and error else error
        self._activity_loading_more = False
        self._activity_request_id = ""
        self._activity_worker = None
        self._error = str(
            payload.get("exception") if isinstance(payload, dict) else payload
        )
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.log(
                "ERROR", self._error,
                group="sobject/info/activity",
                source="SObjectInfoController",
                stacktrace=(
                    str(payload.get("stacktrace") or "")
                    if isinstance(payload, dict) else traceback.format_exc()
                ),
                caller=2,
            )
        self.stateChanged.emit()

    def _refresh_failed(self, request_id: str, error) -> None:
        if request_id != self._request_id:
            return
        self._worker = None
        self._busy = False
        self._report_error(error)

    def _report_error(self, error) -> None:
        payload = error[0] if isinstance(error, tuple) and error else error
        self._error = str(
            payload.get("exception") if isinstance(payload, dict) else payload
        )
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.log(
                "ERROR", self._error,
                group="sobject/info", source="SObjectInfoController",
                stacktrace=(
                    str(payload.get("stacktrace") or "")
                    if isinstance(payload, dict) else traceback.format_exc()
                ),
                caller=2,
            )
        self.stateChanged.emit()

    @Slot(str)
    def open_search_key(self, search_key: str) -> None:
        search_key = str(search_key or "").strip()
        if search_key:
            self._application.open_search_key(search_key)

    def _open_root_process(self, process: str, panel: str = "") -> None:
        root_key = str(self._summary.get("searchKey") or "")
        if not root_key:
            return
        if process:
            self._application.open_search_key_in_process(root_key, process)
        else:
            self._application.open_search_key(root_key)
        if panel:
            self._application.dock_model.show_panel(panel)

    @Slot(str, str)
    def open_task(self, task_code: str, process: str = "") -> None:
        root_key = str(self._summary.get("searchKey") or "")
        if self._tasks_controller is not None and root_key:
            self._tasks_controller.open_object_context(
                root_key, str(task_code or ""), str(process or "")
            )

    @Slot(str, str)
    def open_tasks_filter(self, field: str, value: str) -> None:
        root_key = str(self._summary.get("searchKey") or "")
        if self._tasks_controller is not None and root_key:
            self._tasks_controller.open_object_filter(
                root_key, str(field or ""), str(value or "")
            )

    @Slot(int)
    def open_note(self, row: int) -> None:
        if not 0 <= row < len(self.notes._records):
            return
        record = self.notes._records[row]
        search_key = str(record.get("searchKey") or "")
        root_key = str(self._summary.get("searchKey") or "")
        process = str(record.get("process") or "")
        task_code = str(record.get("taskCode") or "")
        if self._navigation is not None and search_key:
            self._navigation.open_in_context(
                search_key, root_key, process, task_code
            )

    @Slot(int)
    def open_snapshot(self, row: int) -> None:
        if not 0 <= row < len(self.snapshots._records):
            return
        process = str(self.snapshots._records[row].get("process") or "")
        self._open_root_process(process, "snapshot")

    @Slot(int)
    def open_activity(self, row: int) -> None:
        if not 0 <= row < len(self.activity._records):
            return
        record = self.activity._records[row]
        kind = str(record.get("kind") or "")
        search_key = str(record.get("searchKey") or "")
        root_key = str(self._summary.get("searchKey") or "")
        process = str(record.get("process") or "")
        task_code = str(record.get("taskCode") or "")
        if task_code and (
                kind in {"status", "task", "work_hour"}
                or str(record.get("itemType") or "") == "sthpw/task"):
            self.open_task(task_code, process)
        elif kind == "note" and self._navigation is not None and search_key:
            self._navigation.open_in_context(
                search_key, root_key, process, task_code
            )
        elif kind in {"publication", "snapshot"}:
            self._open_root_process(process, "snapshot")
        elif search_key and str(record.get("itemType") or ""):
            self._application.open_search_key(search_key)
        elif root_key:
            self._application.open_search_key(root_key)

    @Slot(str)
    def open_participant(self, login: str) -> None:
        if self._users is not None and str(login or "").strip():
            self._users.open_profile(str(login))

    @Slot(str)
    def activate_file(self, token: str) -> None:
        file_object = self._file_objects.get(str(token or ""))
        if not file_object:
            return
        try:
            self._application.open_file_object(file_object)
        except (
            AttributeError,
            KeyError,
            OSError,
            RuntimeError,
            TimeoutError,
            TypeError,
            ValueError,
        ) as error:
            self._error = str(error)
            self.stateChanged.emit()

    @Slot(str)
    def show_file_folder(self, token: str) -> None:
        file_object = self._file_objects.get(str(token or ""))
        if not file_object:
            return
        try:
            file_object.open_folder()
        except (AttributeError, KeyError, TypeError, OSError) as error:
            self._error = str(error)
            self.stateChanged.emit()

    def _repository_file_ready(self, file_object) -> None:
        if id(file_object) in self._tracked_download_ids and self._summary:
            self._file_metadata.pop(id(file_object), None)
            if not self._download_refresh_timer.isActive():
                self._download_refresh_timer.start()
