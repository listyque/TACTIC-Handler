from __future__ import annotations

import traceback
import uuid
from datetime import date, timedelta

from PySide6.QtCore import QObject, Property, QTimer, Qt, Signal, Slot

from modern_ui.activity import activity_record
from modern_ui.task_data import due_state, format_hours_label, parse_datetime, progress_value
from modern_ui.workspace_models.records import RecordListModel


class SObjectInfoController(QObject):
    """Read-only, cached reporting projection for the selected SObject."""

    stateChanged = Signal()

    def __init__(self, application, users=None, navigation=None, parent=None):
        super().__init__(parent or application)
        self._application = application
        self._users = users
        self._navigation = navigation
        self._summary = {}
        self._metrics = {}
        self._busy = False
        self._error = ""
        self._request_id = ""
        self._worker = None
        self._refreshed_tasks = None
        self._refreshed_notes = None
        self._file_objects = {}
        self._preview_file_objects = {}
        self._tracked_download_ids = set()
        self._download_refresh_timer = QTimer(self)
        self._download_refresh_timer.setSingleShot(True)
        self._download_refresh_timer.setInterval(250)
        self._download_refresh_timer.timeout.connect(self._rebuild)
        self.task_statuses = RecordListModel(("label", "count", "accent"))
        self.task_processes = RecordListModel(("label", "count", "accent"))
        self.tasks = RecordListModel((
            "searchKey", "process", "processLabel", "processColor", "status",
            "statusColor", "assigned", "assignedLabel", "assignedAvatar",
            "start", "end", "dueState", "progress", "description",
            "notesCount", "hoursLabel",
        ))
        self.participants = RecordListModel((
            "login", "displayName", "initials", "avatarUrl", "taskCount",
            "noteCount", "snapshotCount",
        ))
        self.snapshots = RecordListModel((
            "searchKey", "title", "process", "context", "version",
            "author", "timestamp", "previewUrl", "fileCount", "sizeText",
            "description", "repository", "isLatest", "isVersionless",
        ))
        self.files = RecordListModel((
            "token", "searchKey", "title", "extension", "type", "sizeText",
            "path", "repository", "exists", "previewUrl", "snapshotTitle",
            "process", "context",
        ))
        self.activity = RecordListModel((
            "searchKey", "targetSearchKey", "targetTitle", "targetType",
            "kind", "title", "detail", "actor", "timestamp", "project",
            "process", "context", "version", "canOpen",
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
        return self._busy

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

    def _snapshot_preview(self, snapshot) -> str:
        try:
            return str(self._application.workspace_model._snapshot_preview(snapshot) or "")
        except (AttributeError, KeyError, TypeError, ValueError, OSError):
            return ""

    def _file_preview(self, file_object) -> str:
        candidate = file_object
        try:
            candidate = (
                file_object.get_web_preview()
                or file_object.get_icon_preview()
                or file_object
            )
        except (AttributeError, KeyError, TypeError):
            pass
        try:
            preview_url = str(
                self._application.workspace_model._preview_url(candidate) or ""
            )
            if preview_url.startswith("pending-preview:"):
                self._preview_file_objects[id(candidate)] = candidate
                self._tracked_download_ids.add(id(candidate))
            return preview_url
        except (AttributeError, KeyError, TypeError, ValueError, OSError):
            return ""

    def _root_preview(self, sobject, search_key: str) -> str:
        preview = self._application.workspace_model.preview_url_for_search_key(
            search_key
        )
        if preview:
            return str(preview)
        try:
            return str(self._application.workspace_model._root_preview(sobject) or "")
        except (AttributeError, KeyError, TypeError, ValueError, OSError):
            return ""

    def _selection_changed(self) -> None:
        self._refreshed_tasks = None
        self._refreshed_notes = None
        self._error = ""
        self._rebuild()

    @Slot()
    def window_opened(self) -> None:
        self._rebuild()

    def _rebuild(self) -> None:
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
        users = self._user_records()

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

        for task in tasks:
            task_info = self._object_info(task)
            process = str(task_info.get("process") or "")
            process_label, process_color = self._process_style(sobject, process)
            process_bucket = process_counts.setdefault(process, {
                "label": process_label, "count": 0, "accent": process_color,
            })
            process_bucket["count"] += 1
            status = str(task_info.get("status") or "Unspecified")
            status_bucket = status_counts.setdefault(status, {
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
            try:
                task_notes = task.get_notes_count() or {}
                notes_count = sum(self._safe_int(value) for value in task_notes.values())
            except (AttributeError, KeyError, TypeError, ValueError):
                notes_count = 0
            user = users.get(assigned, {})
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
                "start": start,
                "end": end,
                "dueState": task_due_state,
                "progress": progress,
                "description": str(task_info.get("description") or ""),
                "notesCount": notes_count,
                "hoursLabel": format_hours_label(
                    0.0, task_info.get("bid_duration")
                ),
            })

            try:
                status_logs = task.get_status_log() or []
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
                    "searchKey": status_key or self._search_key(task),
                    "targetSearchKey": search_key,
                    "targetTitle": title,
                    "targetType": search_type,
                    "project": project_code,
                    "process": process,
                }))

        for note in notes:
            note_info = self._object_info(note)
            author = str(note_info.get("login") or note_info.get("author") or "")
            if author:
                participant_counts.setdefault(author, {
                    "taskCount": 0, "noteCount": 0, "snapshotCount": 0,
                })["noteCount"] += 1
            activity_values.append(activity_record({
                "eventId": self._search_key(note),
                "kind": "note",
                "title": "Added note",
                "detail": str(note_info.get("note") or ""),
                "actor": author,
                "timestamp": str(note_info.get("timestamp") or ""),
                "searchKey": self._search_key(note),
                "targetSearchKey": search_key,
                "targetTitle": title,
                "targetType": search_type,
                "project": project_code,
                "process": str(note_info.get("process") or ""),
                "context": str(note_info.get("context") or ""),
            }))

        snapshot_records = []
        file_records = []
        self._file_objects = {}
        self._preview_file_objects = {}
        self._tracked_download_ids = set()
        total_size = 0
        primary_file_count = 0
        latest_version = 0
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
                    exists = bool(file_object.is_exists())
                except (AttributeError, KeyError, TypeError, OSError, ValueError):
                    continue
                token = f"{snapshot_key}:{file_index}:{filename}"
                self._file_objects[token] = file_object
                self._tracked_download_ids.add(id(file_object))
                snapshot_size += file_size
                total_size += file_size
                primary_file_count += 1
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
                    "previewUrl": self._file_preview(file_object),
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
            snapshot_records.append({
                "searchKey": snapshot_key,
                "title": snapshot_title,
                "process": process_name,
                "context": context,
                "version": version_text,
                "author": users.get(author, {}).get("displayName") or author,
                "timestamp": str(snapshot_info.get("timestamp") or ""),
                "previewUrl": self._snapshot_preview(snapshot),
                "fileCount": len(display_files),
                "sizeText": self._pretty_size(snapshot_size),
                "description": str(snapshot_info.get("description") or ""),
                "repository": str(snapshot_info.get("repo") or "base"),
                "isLatest": is_latest,
                "isVersionless": is_versionless,
            })
            activity_values.append(activity_record({
                "eventId": snapshot_key,
                "kind": "publication",
                "title": "Published snapshot",
                "detail": snapshot_title,
                "actor": author,
                "timestamp": str(snapshot_info.get("timestamp") or ""),
                "searchKey": snapshot_key,
                "targetSearchKey": search_key,
                "targetTitle": title,
                "targetType": search_type,
                "project": project_code,
                "process": process_name,
                "context": context,
                "version": version_text,
            }))

        participants = []
        for login, counts in participant_counts.items():
            record = users.get(login, {})
            display_name = str(record.get("displayName") or login)
            participants.append({
                "login": login,
                "displayName": display_name,
                "initials": str(record.get("initials") or self._initials(display_name)),
                "avatarUrl": str(record.get("avatarUrl") or ""),
                **counts,
            })
        participants.sort(
            key=lambda item: (
                -(item["taskCount"] + item["noteCount"] + item["snapshotCount"]),
                item["displayName"].lower(),
            )
        )
        snapshot_records.sort(
            key=lambda item: (item["timestamp"], not item["isVersionless"]),
            reverse=True,
        )
        file_records.sort(key=lambda item: item["title"].lower())
        activity_values.sort(key=lambda item: item.get("timestamp") or "", reverse=True)

        excluded = {
            "id", "code", "name", "title", "description", "pipeline_code",
            "project_code", "timestamp", "last_updated", "__snapshots__",
            "__notes_count__", "__tasks_count__", "snapshot", "metadata",
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
            "updated": str(info.get("last_updated") or info.get("timestamp") or ""),
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
            "snapshots": len(snapshot_records),
            "files": primary_file_count,
            "participants": len(participants),
            "processes": len(process_counts),
            "totalSize": self._pretty_size(total_size),
            "latestVersion": f"v{latest_version:03d}" if latest_version else "—",
        }
        self.task_statuses.replace(sorted(
            status_counts.values(), key=lambda item: (-item["count"], item["label"])
        ))
        self.task_processes.replace(sorted(
            process_counts.values(), key=lambda item: (-item["count"], item["label"])
        ))
        self.tasks.replace(task_records)
        self.participants.replace(participants)
        self.snapshots.replace(snapshot_records)
        self.files.replace(file_records)
        self.activity.replace(activity_values[:50])
        self.properties.replace(property_records[:24])
        self.stateChanged.emit()

    def _clear(self) -> None:
        changed = bool(self._summary or self._metrics)
        self._summary = {}
        self._metrics = {}
        self._file_objects = {}
        self._preview_file_objects = {}
        self._tracked_download_ids = set()
        for model in (
            self.task_statuses, self.task_processes, self.tasks, self.participants,
            self.snapshots, self.files, self.activity, self.properties,
        ):
            model.clear()
        if changed:
            self.stateChanged.emit()

    @Slot()
    def refresh(self) -> None:
        state = self._application.workspace_state
        sobject = getattr(state, "_selected_sobject", None)
        if not sobject or self._busy:
            return
        from thlib.environment import env_inst

        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        request_id = uuid.uuid4().hex
        selected_key = self._search_key(sobject)

        def operation():
            tasks = self._records(sobject.get_tasks_sobjects(
                process=None, include_status_log=True
            ))
            notes = self._records(sobject.get_notes_sobjects(process=None))
            sobject.update_snapshots(order_bys=["timestamp desc"])
            return selected_key, tasks, notes

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
        search_key, tasks, notes = result
        current = getattr(self._application.workspace_state, "_selected_sobject", None)
        if current and self._search_key(current) == search_key:
            self._refreshed_tasks = list(tasks or [])
            self._refreshed_notes = list(notes or [])
        self._worker = None
        self._busy = False
        self._error = ""
        self._rebuild()

    def _refresh_failed(self, request_id: str, error) -> None:
        if request_id != self._request_id:
            return
        payload = error[0] if isinstance(error, tuple) and error else error
        self._worker = None
        self._busy = False
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

    @Slot(int)
    def open_activity(self, row: int) -> None:
        if not 0 <= row < len(self.activity._records):
            return
        record = self.activity._records[row]
        search_key = str(record.get("searchKey") or "")
        target_key = str(record.get("targetSearchKey") or "")
        process = str(record.get("process") or "")
        if self._navigation is not None and search_key:
            self._navigation.open_in_context(search_key, target_key, process)
        elif search_key:
            self._application.open_search_key(search_key)

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
            if file_object.is_exists():
                file_object.open_file()
                return
            self._application.repository_sync.schedule_file_object(
                file_object, process="sobject-info", auto_start=True
            )
        except (AttributeError, KeyError, TypeError, ValueError, OSError) as error:
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
            if not self._download_refresh_timer.isActive():
                self._download_refresh_timer.start()
