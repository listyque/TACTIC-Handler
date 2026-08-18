from __future__ import annotations

import datetime
import html
import json
import re
import traceback
import uuid

from PySide6.QtCore import QObject, Property, QSettings, Qt, QUrl, Signal, Slot

from .skey_previews import display_html_without_skeys


class CommunicationController(QObject):
    stateChanged = Signal()
    noteSent = Signal()
    noteFocusRequested = Signal(str)
    visibilityChanged = Signal(bool)
    noteCountChanged = Signal(str, str, int, object)

    _url_pattern = re.compile(r"(skey://[^\s<]+|https?://[^\s<]+)")

    def __init__(
        self, application, attachments=None, users=None, parent=None,
        skey_previews=None,
    ):
        super().__init__(parent)
        self._application = application
        self._workspace = application.workspace_state
        self.attachments = attachments
        self._users = users
        self._skey_previews = skey_previews
        self._tasks_controller = None
        self._settings = QSettings("TACTIC-Handler", "modern-qml")
        self._notes = {}
        self._files = {}
        self._preview_files = {}
        self._busy = False
        self._loading = False
        self._error = ""
        self._request_id = ""
        self._process_count_request_id = ""
        self._process = "publish"
        self._process_choices = []
        self._process_tasks = []
        self._selected_task_code = ""
        self._loaded_task_context = None
        self._pending_task_context = None
        self._request_context = None
        self._preferred_tasks = {}
        self._note_records = []
        self._task_status_records = {}
        self._selected_object = {}
        self._task_expanded = self._settings.value(
            "communication/taskExpanded", False, type=bool
        )
        self._pending_body = ""
        self._pending_target = ("", "")
        self._clear_composer_after_mutation = False
        self._worker = None
        self._open_after_download = set()
        self._pending_note_focus = ""
        self._visible = False
        if attachments:
            attachments.uploaded.connect(self._attachments_uploaded)
            attachments.failed.connect(self._attachments_failed)
            attachments.stateChanged.connect(self.stateChanged)
        self._workspace.selection_changed.connect(self._selection_changed)
        self._workspace.task_model.contentReplaced.connect(
            self._workspace_tasks_changed
        )
        self._workspace.task_model.dataChanged.connect(
            lambda _first, _last, _roles: self.stateChanged.emit()
        )
        workspace_model = getattr(application, "workspace_model", None)
        preview_signal = getattr(workspace_model, "dataChanged", None)
        if preview_signal:
            preview_signal.connect(self._selected_preview_changed)
        if users:
            users.contentReplaced.connect(self._users_changed)
        application.repository_sync.file_download_done.connect(
            self._attachment_downloaded
        )
        if skey_previews:
            skey_previews.previewReady.connect(self._skey_preview_ready)
            skey_previews.previewsReady.connect(self._skey_previews_ready)
        self._selection_changed()

    def attach_tasks_controller(self, controller):
        if controller is self._tasks_controller:
            return
        self._tasks_controller = controller
        controller.stateChanged.connect(self.stateChanged)
        controller.advancedChanged.connect(self.stateChanged)
        self._sync_task_editor_selection()

    def _sync_task_editor_selection(self):
        if self._tasks_controller and self._selected_task_code:
            self._tasks_controller.select_process_task_code(
                self._process, self._selected_task_code
            )

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._busy or bool(self.attachments and self.attachments.busy)

    @Property(bool, notify=stateChanged)
    def loading(self):
        return self._loading

    @Property(bool, notify=stateChanged)
    def hasTarget(self):
        return self._workspace._selected_sobject is not None

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Property(str, notify=stateChanged)
    def process(self):
        return self._process

    @Property("QVariantList", notify=stateChanged)
    def processChoices(self):
        return list(self._process_choices)

    @Property(str, notify=stateChanged)
    def processLabel(self):
        return next((
            value["label"] for value in self._process_choices
            if value["value"] == self._process
        ), self._process.replace("_", " ").title())

    @Property("QVariantMap", notify=stateChanged)
    def selectedObject(self):
        return dict(self._selected_object)

    def _object_record(self, sobject):
        if not sobject:
            return {}
        try:
            info = dict(sobject.get_info() or {})
        except (AttributeError, TypeError):
            info = {}
        try:
            stype = sobject.get_stype()
            type_title = str(stype.get_pretty_name() or stype.get_code() or "")
        except (AttributeError, TypeError):
            type_title = ""
        search_key = str(sobject.get_search_key() or "")
        workspace_model = getattr(self._application, "workspace_model", None)
        preview_url = ""
        preview_for_key = getattr(
            workspace_model, "preview_url_for_search_key", None
        )
        if callable(preview_for_key):
            preview_url = str(preview_for_key(search_key) or "")
        return {
            "title": str(
                sobject.get_title()
                or info.get("name")
                or info.get("code")
                or "Selected object"
            ),
            "code": str(info.get("code") or info.get("id") or ""),
            "type": type_title,
            "pipeline": str(info.get("pipeline_code") or ""),
            "status": str(info.get("status") or info.get("state") or ""),
            "description": str(info.get("description") or info.get("detail") or ""),
            "searchKey": search_key,
            "previewUrl": preview_url,
        }

    def _selected_preview_changed(self, _first, _last, _roles):
        search_key = str(self._selected_object.get("searchKey") or "")
        if not search_key:
            return
        workspace_model = getattr(self._application, "workspace_model", None)
        preview_for_key = getattr(
            workspace_model, "preview_url_for_search_key", None
        )
        if not callable(preview_for_key):
            return
        preview_url = str(preview_for_key(search_key) or "")
        if preview_url == self._selected_object.get("previewUrl"):
            return
        self._selected_object["previewUrl"] = preview_url
        self.stateChanged.emit()

    def _build_process_choices(self, sobject):
        choices = []
        known = set()
        pipeline_processes = []
        try:
            note_counts = dict(sobject.get_notes_count() or {}) if sobject else {}
        except (AttributeError, TypeError, ValueError):
            note_counts = {}

        def append(value, label="", process_type="", color=""):
            value = str(value or "").strip()
            if not value or value in known:
                return
            known.add(value)
            choices.append({
                "label": str(label or value.replace("_", " ").title()),
                "value": value,
                "type": str(process_type or ""),
                "color": str(color or ""),
                "count": int(note_counts.get(value) or 0),
            })

        if sobject:
            try:
                stype = sobject.get_stype()
                pipelines = stype.get_pipeline() or {}
                pipeline = pipelines.get(sobject.get_pipeline_code())
                names = pipeline.get_all_pipeline_names() if pipeline else []
                for name in names:
                    info = pipeline.get_process_info(name) or {}
                    try:
                        process_object = (
                            pipeline.get_pipeline_process(name) or {}
                        )
                    except AttributeError:
                        process_object = {}
                    append(
                        name,
                        pipeline.get_process_label(name) or info.get("label"),
                        info.get("type"),
                        info.get("color") or process_object.get("color"),
                    )
                    pipeline_processes.append(str(name))
            except (AttributeError, KeyError, TypeError):
                pass
        for task in self._workspace._task_sobjects:
            try:
                append((task.get_info() or {}).get("process"))
            except (AttributeError, TypeError):
                pass
        show_builtins = False
        try:
            import thlib.global_functions as gf
            from thlib.environment import cfg_controls
            show_builtins = bool(int(gf.get_value_from_config(
                cfg_controls.get_checkin() or {},
                "showAllProcessCheckBox",
            ) or 0))
        except (AttributeError, KeyError, TypeError, ValueError):
            pass
        if show_builtins or not pipeline_processes:
            for name in ("icon", "attachment", "publish"):
                append(name, name.title(), "built-in")
        return choices

    @Property("QVariantMap", notify=stateChanged)
    def currentTask(self):
        task = self._selected_task()
        if task:
            info = dict(task.get_info() or {})
            code = str(info.get("code") or "")
            assigned = str(info.get("assigned") or info.get("login") or "")
            if not assigned and self._tasks_controller:
                assigned = self._tasks_controller.task_store.assignee_for_task_info(
                    info
                )
            user = self._user_record(assigned)
            progress = info.get("progress") or info.get("completion") or 0
            try:
                progress = int(float(str(progress).rstrip("%")))
            except (TypeError, ValueError):
                progress = 0
            status_records = self._task_status_records.get(code, [])
            latest = status_records[-1] if status_records else {}
            record = {
                "code": code,
                "searchKey": str(task.get_search_key() or ""),
                "process": str(info.get("process") or self._process),
                "context": str(info.get("context") or self._process),
                "status": str(info.get("status") or ""),
                "statusColor": self._status_color(task, info.get("status")),
                "assigned": assigned,
                "assignedDisplay": str(
                    user.get("displayName") or assigned or "Not assigned"
                ),
                "start": str(info.get("bid_start_date") or ""),
                "end": str(info.get("bid_end_date") or ""),
                "progress": progress,
                "description": str(info.get("description") or ""),
                "historyCount": len(status_records),
                "latestHistory": str(latest.get("statusTo") or ""),
                "taskCount": len(self._process_tasks),
            }
            if self._tasks_controller:
                editor = self._tasks_controller.task_inspector_record(code)
                for key in (
                    "status", "statusColor", "assigned", "assignedLabel",
                    "statusChoices", "userChoices", "start", "end", "progress",
                    "progressInput", "validationError", "dirty",
                ):
                    if key in editor:
                        record[key] = editor[key]
                if editor.get("assignedLabel"):
                    record["assignedDisplay"] = editor["assignedLabel"]
            return record
        return {}

    @Property("QVariantList", notify=stateChanged)
    def taskChoices(self):
        choices = []
        for task in self._process_tasks:
            try:
                info = dict(task.get_info() or {})
            except (AttributeError, TypeError):
                continue
            code = str(info.get("code") or "")
            if not code:
                continue
            assigned = str(info.get("assigned") or info.get("login") or "")
            if not assigned and self._tasks_controller:
                assigned = self._tasks_controller.task_store.assignee_for_task_info(
                    info
                )
            user = self._user_record(assigned)
            assigned_label = str(
                user.get("displayName") or assigned or "Not assigned"
            )
            context = str(info.get("context") or self._process or "No context")
            status = str(info.get("status") or "")
            choices.append({
                "value": code,
                "label": " / ".join((context, assigned_label)),
                "status": "  |  ".join(
                    value for value in (status, code) if value
                ),
                "selected": code == self._selected_task_code,
            })
        return choices

    @Property(str, notify=stateChanged)
    def selectedTaskCode(self):
        return self._selected_task_code

    @Property(int, notify=stateChanged)
    def unreadCount(self):
        return sum(
            1 for record in self._workspace.note_model._records
            if record.get("unread")
        )

    @Property(bool, notify=stateChanged)
    def taskExpanded(self):
        return self._task_expanded

    @Slot()
    def toggle_task_expanded(self):
        self.set_task_expanded(not self._task_expanded)

    @Slot()
    def create_task_for_process(self):
        if not self._tasks_controller or not self.hasTarget:
            return
        row = next((
            index for index, record in enumerate(
                self._tasks_controller.process_model._records
            )
            if str(record.get("process") or "") == self._process
        ), -1)
        if row >= 0:
            self._tasks_controller.begin_create_for_process(row)

    @Slot(bool)
    def set_task_expanded(self, value):
        value = bool(value)
        if value == self._task_expanded:
            return
        self._task_expanded = value
        self._settings.setValue(
            "communication/taskExpanded", self._task_expanded
        )
        self._settings.sync()
        self.stateChanged.emit()

    def _task_preference_key(self):
        sobject = self._workspace._selected_sobject
        try:
            search_key = str(sobject.get_search_key() or "") if sobject else ""
        except AttributeError:
            search_key = ""
        return search_key, self._process

    def _selected_task(self):
        return next((
            task for task in self._process_tasks
            if str((task.get_info() or {}).get("code") or "")
            == self._selected_task_code
        ), None)

    def selected_task_object(self):
        return self._selected_task()

    def _select_preferred_task(self):
        valid = {}
        for task in self._process_tasks:
            try:
                code = str((task.get_info() or {}).get("code") or "")
            except (AttributeError, TypeError):
                code = ""
            if code:
                valid[code] = task
        preferred = self._preferred_tasks.get(self._task_preference_key(), "")
        if self._selected_task_code in valid:
            preferred = self._selected_task_code
        if preferred not in valid:
            from thlib.environment import env_server
            current_login = str(env_server.get_user() or "")
            preferred = next((
                code for code, task in valid.items()
                if str(
                    (task.get_info() or {}).get("assigned")
                    or (task.get_info() or {}).get("login")
                    or ""
                ) == current_login
            ), "")
        if preferred not in valid:
            preferred = next(iter(valid), "")
        self._selected_task_code = preferred
        if preferred:
            self._preferred_tasks[self._task_preference_key()] = preferred

    @Slot(str)
    def select_task(self, task_code):
        task_code = str(task_code or "")
        if not task_code or task_code == self._selected_task_code:
            return
        if not any(
                str((task.get_info() or {}).get("code") or "") == task_code
                for task in self._process_tasks):
            return
        self._selected_task_code = task_code
        self._preferred_tasks[self._task_preference_key()] = task_code
        self._sync_task_editor_selection()
        self._rebuild_history_records()
        self.stateChanged.emit()

    @Slot(str, str, str)
    def select_task_context(self, parent_key, process, task_code):
        parent_key = str(parent_key or "")
        process = str(process or "")
        task_code = str(task_code or "")
        if not task_code or not parent_key:
            return
        self._preferred_tasks[(parent_key, process)] = task_code
        sobject = self._workspace._selected_sobject
        try:
            current_key = str(sobject.get_search_key() or "") if sobject else ""
        except AttributeError:
            current_key = ""
        if not current_key or parent_key != current_key:
            return
        if process and process != self._process:
            self.set_process(process)
            return
        self.select_task(task_code)
        if not self._process_tasks and self._visible and not self._busy:
            self.refresh()

    @Slot(str, str, str)
    def activate_task_context(self, task_code, parent_key, process):
        context = (
            str(parent_key or ""), str(process or ""), str(task_code or "")
        )
        if context != self._loaded_task_context:
            self._pending_task_context = context
        self.select_task_context(parent_key, process, task_code)
        self._refresh_pending_task_context()

    def _refresh_pending_task_context(self):
        pending = self._pending_task_context
        if not pending or not self._visible:
            return
        sobject = self._workspace._selected_sobject
        try:
            current_key = str(sobject.get_search_key() or "") if sobject else ""
        except AttributeError:
            current_key = ""
        parent_key, process, _task_code = pending
        if parent_key != current_key or process != self._process:
            return
        request_context = (current_key, self._process)
        if self._busy:
            if self._request_context == request_context:
                self._pending_task_context = None
            return
        self._pending_task_context = None
        self.refresh()

    def _selection_changed(self):
        self._request_id = uuid.uuid4().hex
        self._process_count_request_id = uuid.uuid4().hex
        self._busy = False
        self._loading = False
        self._worker = None
        self._notes.clear()
        self._files.clear()
        self._preview_files.clear()
        self._process_tasks = []
        self._selected_task_code = ""
        self._loaded_task_context = None
        self._request_context = None
        self._note_records = []
        self._task_status_records.clear()
        if self.attachments and not self.attachments.busy:
            self.attachments.clear()
        sobject = self._workspace._selected_sobject
        self._selected_object = self._object_record(sobject)
        self._process_choices = self._build_process_choices(sobject)
        selected_process = str(
            getattr(self._application, "_selected_detail_process", "") or ""
        )
        if selected_process:
            self._process = selected_process
        else:
            self._process = "publish"
        self._workspace.note_model.clear()
        self._error = ""
        self.stateChanged.emit()
        if self._visible:
            if not self._use_workspace_history():
                self.refresh()
            self._refresh_process_counts(sobject)
            self._refresh_pending_task_context()

    @Slot(bool)
    def set_visible(self, value):
        value = bool(value)
        if value == self._visible:
            return
        self._visible = value
        self.visibilityChanged.emit(value)
        if value and self.hasTarget and not self._busy:
            if not self._use_workspace_history():
                self.refresh()
            self._refresh_process_counts(self._workspace._selected_sobject)
            self._refresh_pending_task_context()

    def _use_workspace_history(self):
        if not getattr(self._workspace, "_notes_loaded", False):
            return False
        loaded_process = getattr(self._workspace, "_notes_process", None)
        if loaded_process not in (None, "", self._process):
            return False
        notes = []
        for note in self._workspace._note_sobjects:
            try:
                process = str((note.get_info() or {}).get("process") or "")
            except (AttributeError, TypeError):
                process = ""
            if not self._process or process == self._process:
                notes.append(note)
        tasks = []
        for task in self._workspace._task_sobjects:
            try:
                process = str((task.get_info() or {}).get("process") or "")
            except (AttributeError, TypeError):
                process = ""
            if not self._process or process == self._process:
                tasks.append(task)
        request_id = uuid.uuid4().hex
        self._request_id = request_id
        self._busy = True
        self._history_ready(request_id, (tasks, notes))
        return True

    def _refresh_process_counts(self, sobject):
        processes = [choice["value"] for choice in self._process_choices]
        if not self._visible or not sobject or not processes:
            return
        if (
            getattr(self._workspace, "_notes_loaded", False)
            and getattr(self._workspace, "_notes_process", None) in (None, "")
        ):
            counts = {}
            for note in self._workspace._note_sobjects:
                try:
                    process = str(
                        (note.get_info() or {}).get("process") or ""
                    )
                except (AttributeError, TypeError):
                    process = ""
                if process:
                    counts[process] = counts.get(process, 0) + 1
            for choice in self._process_choices:
                count = int(counts.get(choice["value"]) or 0)
                choice["count"] = count
                sobject.set_notes_count(choice["value"], count)
            self.stateChanged.emit()
            return
        request_id = uuid.uuid4().hex
        self._process_count_request_id = request_id
        from thlib.environment import env_inst
        import thlib.tactic_classes as tc
        worker = env_inst.server_pool.add_task(
            tc.get_notes_count,
            sobject=sobject,
            process=processes,
            children_stypes=[],
        )
        worker.result.connect(
            lambda result: self._process_counts_ready(request_id, sobject, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._process_counts_failed(request_id, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    def _process_counts_ready(self, request_id, sobject, result):
        if request_id != self._process_count_request_id:
            return
        notes = (result or {}).get("notes") or {}
        for choice in self._process_choices:
            count = int(notes.get(choice["value"]) or 0)
            choice["count"] = count
            sobject.set_notes_count(choice["value"], count)
        self.stateChanged.emit()

    def _process_counts_failed(self, request_id, error):
        if request_id != self._process_count_request_id:
            return
        payload = error[0] if isinstance(error, tuple) and error else error
        stacktrace = ""
        if isinstance(payload, dict):
            stacktrace = str(payload.get("stacktrace") or "")
            payload = payload.get("exception") or payload.get("message")
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.log(
                "ERROR",
                payload or "Unable to load note counts",
                group="communication/notes/counts",
                source="Controller",
                stacktrace=stacktrace,
                caller=2,
            )

    @Slot(str)
    def set_process(self, value):
        if not self.hasTarget:
            return
        value = str(value or "").strip()
        if value and value != self._process:
            self._request_id = uuid.uuid4().hex
            self._busy = False
            self._loading = False
            self._worker = None
            self._process = value
            self._process_tasks = []
            self._selected_task_code = ""
            self._loaded_task_context = None
            self._note_records = []
            self._task_status_records.clear()
            self.stateChanged.emit()
            if not self._use_workspace_history():
                self.refresh()

    @Slot()
    def refresh(self):
        sobject = self._workspace._selected_sobject
        if not self._visible or not sobject or self._busy:
            return
        request_id = uuid.uuid4().hex
        self._request_id = request_id
        self._busy = True
        self._loading = True
        self._request_context = (
            str(sobject.get_search_key() or ""), self._process
        )
        self._error = ""
        self.stateChanged.emit()
        from thlib.environment import env_inst
        import thlib.tactic_classes as tc
        worker = env_inst.server_pool.add_task(
            tc.get_tasks_and_notes, sobject=sobject, process=self._process
        )
        self._worker = worker
        worker.result.connect(
            lambda result: self._history_ready(request_id, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._failed(request_id, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    @Slot()
    def cancel_loading(self):
        if not self._loading:
            return
        self._request_id = uuid.uuid4().hex
        worker = self._worker
        self._worker = None
        self._busy = False
        self._loading = False
        self._request_context = None
        if worker:
            try:
                worker.cancel()
            except (AttributeError, RuntimeError):
                pass
        self.stateChanged.emit()

    @classmethod
    def _display_html(cls, value):
        escaped = html.escape(str(value or ""))
        linked = cls._url_pattern.sub(
            lambda match: (
                f'<a href="{match.group(1)}">{match.group(1)}</a>'
            ),
            escaped,
        )
        return linked.replace("\n", "<br>")

    def _attachment_records(self, note):
        records = []
        try:
            process = note.get_process("attachment")
            contexts = process.get_contexts() if process else {}
            snapshots = [
                snapshot
                for context in (contexts or {}).values()
                for snapshot in (context.get_versions() or {}).values()
            ]
        except (AttributeError, TypeError):
            snapshots = []
        for snapshot in snapshots:
            for file_object in snapshot.get_files_objects() or []:
                try:
                    if file_object.get_type() in {"web", "icon"}:
                        continue
                except AttributeError:
                    continue
                token = uuid.uuid4().hex
                self._files[token] = file_object
                try:
                    preview_object = file_object.get_web_preview()
                except (AttributeError, KeyError, TypeError):
                    preview_object = None
                if not preview_object:
                    try:
                        preview_object = file_object if file_object.is_previewable() else None
                    except (AttributeError, TypeError):
                        preview_object = None
                if preview_object:
                    self._preview_files[token] = preview_object
                try:
                    local = bool(file_object.is_exists())
                    preview_local = bool(preview_object and preview_object.is_exists())
                    preview_url = (
                        QUrl.fromLocalFile(
                            str(preview_object.get_full_abs_path())
                        ).toString() if preview_local else ""
                    )
                    if (
                            preview_object and not preview_local
                            and self._application.repository_sync
                            .previews_through_http_enabled()):
                        self._application.repository_sync.schedule_file_object(
                            preview_object, process="attachment", auto_start=True
                        )
                except (AttributeError, OSError, RuntimeError, ValueError):
                    local = False
                    preview_url = ""
                records.append({
                    "token": token,
                    "title": str(file_object.get_filename_with_ext()),
                    "size": self._file_size(file_object),
                    "extension": str(file_object.get_ext() or "").upper(),
                    "previewUrl": preview_url,
                    "local": local,
                })
        return records

    @staticmethod
    def _file_size(file_object):
        try:
            import thlib.global_functions as gf
            return str(gf.sizes(file_object.get_file_size()) or "")
        except (AttributeError, OSError, TypeError, ValueError):
            return ""

    def _user_record(self, login):
        if not self._users:
            return {}
        return next((
            record for record in self._users._records
            if str(record.get("login") or "") == str(login or "")
        ), {})

    def _users_changed(self):
        changed = False
        for row, record in enumerate(self._workspace.note_model._records):
            user = self._user_record(record.get("author"))
            if not user:
                continue
            values = {
                "authorDisplay": str(
                    user.get("displayName") or record.get("author") or "User"
                ),
                "avatarUrl": str(user.get("avatarUrl") or ""),
                "initials": str(user.get("initials") or "?")[:2].upper(),
            }
            for role, value in values.items():
                if record.get(role) != value:
                    self._workspace.note_model.set_value(row, role, value)
                    changed = True
        if changed:
            self._note_records = [
                dict(record) for record in self._workspace.note_model._records
                if record.get("entryType") == "note"
            ]
            self.stateChanged.emit()

    def _workspace_tasks_changed(self):
        tasks = []
        for task in self._workspace._task_sobjects:
            try:
                process = str((task.get_info() or {}).get("process") or "")
            except (AttributeError, TypeError):
                process = ""
            if process == self._process:
                tasks.append(task)
        self._process_tasks = tasks
        self._task_status_records.clear()
        self._select_preferred_task()
        self._sync_task_editor_selection()
        if self._note_records:
            self._rebuild_history_records()
        self.stateChanged.emit()

    @staticmethod
    def _timestamp_values(sobject, fallback):
        try:
            pretty = str(sobject.get_timestamp(pretty=True) or fallback)
            simple = str(sobject.get_timestamp(simple=True) or fallback)
        except (AttributeError, TypeError, ValueError):
            pretty = simple = str(fallback or "")
        return pretty, simple

    @staticmethod
    def _author_color(login):
        try:
            import thlib.global_functions as gf
            return str(gf.gen_color(str(login or "removed user")))
        except (AttributeError, TypeError, ValueError):
            return "#808080"

    def _record(self, note):
        info = note.get_info() or {}
        raw_metadata = info.get("metadata") or {}
        if isinstance(raw_metadata, dict):
            metadata = dict(raw_metadata)
        else:
            try:
                metadata = json.loads(raw_metadata)
            except (TypeError, ValueError):
                metadata = {}
        edit_history = list(metadata.get("editHistory") or [])
        latest_edit = edit_history[-1] if edit_history else {}
        search_key = str(note.get_search_key() or "")
        attachments = self._attachment_records(note)
        from thlib.environment import env_server
        author = str(info.get("login") or "")
        user = self._user_record(author)
        timestamp = str(info.get("timestamp") or "")
        pretty, simple = self._timestamp_values(note, timestamp)
        return {
            "noteId": str(info.get("code") or search_key),
            "searchKey": search_key,
            "author": author,
            "time": timestamp,
            "body": str(info.get("note") or ""),
            "bodyHtml": self._display_html(info.get("note")),
            "displayHtml": display_html_without_skeys(info.get("note")),
            "skeyPreviews": self._preview_records(info.get("note")),
            "status": str(info.get("status") or ""),
            "process": str(info.get("process") or ""),
            "isOwn": author == str(env_server.get_user() or ""),
            "unread": False,
            "attachments": attachments,
            "attachmentCount": len(attachments),
            "entryType": "note",
            "authorDisplay": str(user.get("displayName") or author or "Removed user"),
            "avatarUrl": str(user.get("avatarUrl") or ""),
            "initials": str(user.get("initials") or "?")[:2].upper(),
            "authorColor": self._author_color(author),
            "timePretty": pretty,
            "timeSimple": simple,
            "statusFrom": "",
            "statusTo": "",
            "statusColor": "#00000000",
            "statusTimelineBefore": False,
            "statusTimelineAfter": False,
            "edited": bool(edit_history),
            "editedBy": str(latest_edit.get("editedBy") or ""),
            "editedAt": str(latest_edit.get("editedAt") or ""),
            "editHistory": edit_history,
            "canEdit": author == str(env_server.get_user() or ""),
            "canDelete": author == str(env_server.get_user() or ""),
        }

    def _status_color(self, task, status):
        status_color = "#ffffff"
        sobject = self._workspace._selected_sobject
        try:
            workflow = sobject.get_stype().get_workflow()
            pipelines = workflow.get_by_stype_code("sthpw/task") or {}
            pipeline = pipelines.get((task.get_info() or {}).get("pipeline_code"))
            process = pipeline.get_pipeline_process(status) if pipeline else None
            if process and process.get("color"):
                status_color = str(process["color"])
        except (AttributeError, KeyError, TypeError):
            pass
        return status_color

    def _status_record(self, status, task):
        info = dict(status.get_info() or {})
        from thlib.environment import env_server
        author = str(info.get("login") or "")
        user = self._user_record(author)
        timestamp = str(info.get("timestamp") or "")
        pretty, simple = self._timestamp_values(status, timestamp)
        status_to = str(info.get("to_status") or info.get("status") or "")
        status_from = str(info.get("from_status") or "")
        search_key = str(status.get_search_key() or "")
        return {
            "noteId": str(info.get("code") or info.get("id") or search_key),
            "searchKey": search_key,
            "author": author,
            "time": timestamp,
            "body": status_to,
            "bodyHtml": html.escape(status_to),
            "displayHtml": html.escape(status_to),
            "skeyPreviews": [],
            "status": status_to,
            "process": str((task.get_info() or {}).get("process") or self._process),
            "isOwn": author == str(env_server.get_user() or ""),
            "unread": False,
            "attachments": [],
            "attachmentCount": 0,
            "entryType": "status",
            "authorDisplay": str(user.get("displayName") or author or "Removed user"),
            "avatarUrl": str(user.get("avatarUrl") or ""),
            "initials": str(user.get("initials") or "?")[:2].upper(),
            "authorColor": self._author_color(author),
            "timePretty": pretty,
            "timeSimple": simple,
            "statusFrom": status_from,
            "statusTo": status_to,
            "statusColor": self._status_color(task, status_to),
            "statusTimelineBefore": False,
            "statusTimelineAfter": False,
            "canEdit": False,
            "canDelete": False,
        }

    def _preview_records(self, value):
        if not self._skey_previews:
            return []
        return self._skey_previews.records_for_text(value)

    @Slot(str, result=int)
    def note_index(self, note_id):
        note_id = str(note_id or "")
        return next((
            row for row, record in enumerate(self._workspace.note_model._records)
            if note_id in {record.get("noteId"), record.get("searchKey")}
        ), -1)

    @Slot(str, result=bool)
    def show_note(self, note_id):
        note_id = str(note_id or "")
        if not note_id:
            return False
        self._pending_note_focus = note_id
        if self.note_index(note_id) >= 0:
            self._pending_note_focus = ""
            self.noteFocusRequested.emit(note_id)
        return True

    @Slot(str, object)
    def _skey_preview_ready(self, search_key, descriptor):
        self._apply_skey_previews({search_key: dict(descriptor or {})})

    @Slot(object)
    def _skey_previews_ready(self, descriptors):
        self._apply_skey_previews({
            str(item.get("searchKey") or ""): dict(item)
            for item in descriptors or []
            if item.get("searchKey")
        })

    def _apply_skey_previews(self, descriptors):
        if not descriptors:
            return
        changed = False
        for row, record in enumerate(self._workspace.note_model._records):
            previews = [dict(item) for item in record.get("skeyPreviews") or []]
            row_changed = False
            for index, item in enumerate(previews):
                descriptor = descriptors.get(str(item.get("searchKey") or ""))
                if descriptor is not None:
                    previews[index] = descriptor
                    row_changed = True
            if row_changed:
                self._workspace.note_model.set_value(row, "skeyPreviews", previews)
                changed = True
        if changed:
            self._note_records = [
                dict(record) for record in self._workspace.note_model._records
                if record.get("entryType") == "note"
            ]
            self.stateChanged.emit()

    @Slot(str)
    def open_skey_preview(self, search_key):
        if self._skey_previews:
            self._skey_previews.open(search_key)
        else:
            self._application.open_search_key(search_key)

    @Slot(str)
    def copy_skey_preview(self, search_key):
        if self._skey_previews:
            self._skey_previews.copy(search_key)

    @Slot(str)
    def retry_skey_preview(self, search_key):
        if self._skey_previews:
            self._skey_previews.retry(search_key)

    def _status_records_for_task(self, task):
        try:
            code = str((task.get_info() or {}).get("code") or "")
        except (AttributeError, TypeError):
            return []
        if code in self._task_status_records:
            return list(self._task_status_records[code])
        try:
            statuses = task.get_status_log() or []
        except (AttributeError, TypeError):
            statuses = []
        records = [self._status_record(status, task) for status in statuses]
        records.sort(key=lambda record: record["time"])
        self._task_status_records[code] = records
        return list(records)

    def _rebuild_history_records(self):
        records = [dict(record) for record in self._note_records]
        task = self._selected_task()
        if task:
            records.extend(self._status_records_for_task(task))
        records.sort(key=lambda record: record["time"])
        last_read = self._last_read_value()
        for index, record in enumerate(records):
            is_status = record["entryType"] == "status"
            record["statusTimelineBefore"] = (
                is_status and index > 0
                and records[index - 1]["entryType"] == "status"
            )
            record["statusTimelineAfter"] = (
                is_status and index + 1 < len(records)
                and records[index + 1]["entryType"] == "status"
            )
            record["unread"] = (
                not is_status
                and not record["isOwn"] and record["time"] > last_read
            )
        self._workspace.note_model.replace(records)

    def _history_ready(self, request_id, result):
        if request_id != self._request_id:
            return
        if isinstance(result, tuple) and len(result) == 2:
            tasks_value, notes_value = result
        elif isinstance(result, tuple) and len(result) == 1:
            tasks_value, notes_value = {}, result[0]
        else:
            tasks_value, notes_value = {}, result
        tasks = (
            list((tasks_value or {}).values())
            if isinstance(tasks_value, dict) else list(tasks_value or [])
        )
        notes = (
            list((notes_value or {}).values())
            if isinstance(notes_value, dict) else list(notes_value or [])
        )
        self._process_tasks = [
            task for task in tasks
            if str((task.get_info() or {}).get("process") or "") == self._process
        ]
        self._task_status_records.clear()
        self._select_preferred_task()
        self._sync_task_editor_selection()
        for choice in self._process_choices:
            if choice["value"] == self._process:
                choice["count"] = len(notes)
                break
        sobject = self._workspace._selected_sobject
        if sobject:
            sobject.set_notes_count(self._process, len(notes))
            self.noteCountChanged.emit(
                str(sobject.get_search_key() or ""), self._process,
                len(notes), [
                    str((note.get_info() or {}).get("code") or "")
                    for note in notes
                ],
            )
        self._files.clear()
        self._preview_files.clear()
        self._notes.clear()
        self._note_records = []
        for note in notes:
            record = self._record(note)
            self._notes[record["searchKey"]] = note
            self._note_records.append(record)
        self._rebuild_history_records()
        self._loaded_task_context = (
            str(sobject.get_search_key() or "") if sobject else "",
            self._process,
            self._selected_task_code,
        )
        self._finish()
        if self._pending_note_focus and self.note_index(self._pending_note_focus) >= 0:
            note_id = self._pending_note_focus
            self._pending_note_focus = ""
            self.noteFocusRequested.emit(note_id)

    def _last_read_key(self):
        sobject = self._workspace._selected_sobject
        key = sobject.get_search_key() if sobject else ""
        return f"communication/lastRead/{key}"

    def _last_read_value(self):
        return self._settings.value(self._last_read_key(), "", type=str)

    @Slot()
    def mark_all_read(self):
        records = self._workspace.note_model._records
        if not records:
            return
        self._settings.setValue(
            self._last_read_key(), max(record["time"] for record in records)
        )
        for row, record in enumerate(records):
            if record.get("unread"):
                self._workspace.note_model.set_value(row, "unread", False)
        self.stateChanged.emit()

    @Slot(str, result=bool)
    def send(self, body):
        if self._busy:
            return False
        body = str(body or "").strip()
        has_staged = bool(self.attachments and self.attachments.count)
        if not body and not has_staged:
            self._error = "Enter a note or attach a file."
            self.stateChanged.emit()
            return False
        sobject = self._workspace._selected_sobject
        if not sobject:
            self._error = "Select an sObject before sending a message."
            self.stateChanged.emit()
            return False
        self._pending_body = body
        self._pending_target = (sobject.get_search_key(), self._process)
        if has_staged:
            self._busy = True
            self._error = ""
            self.stateChanged.emit()
            if not self.attachments.begin_target(
                    sobject.get_search_key(),
                    "attachment/{0}".format(self._process),
                    "Note attachment"):
                self._busy = False
                self._error = self.attachments.error
                self.stateChanged.emit()
                return False
        else:
            self._send_payload([])
        return True

    def _attachments_uploaded(self, snapshot_keys):
        self._busy = False
        values = [str(value) for value in (snapshot_keys or []) if value]
        self._send_payload(values)

    def _attachments_failed(self, message, stacktrace):
        self._busy = False
        self._error = str(message or "Attachment upload failed")
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log and "cancelled" not in self._error.casefold():
            debug_log.raise_error(
                self._error, stacktrace=stacktrace,
                group="communication/notes/attachments",
            )
        self.stateChanged.emit()

    def _send_payload(self, attachments):
        search_key, process = self._pending_target
        if not search_key:
            return
        body = self._pending_body

        def operation():
            import thlib.tactic_classes as tc
            from thlib.environment import env_server
            return tc.add_note(
                search_key, process, process, body,
                env_server.get_user(), attachments=list(attachments or []),
            )

        self._run(operation, clear_composer=True)

    @Slot(int, str, result=bool)
    def edit(self, row, body):
        if self._busy or not 0 <= row < len(self._workspace.note_model._records):
            return False
        body = str(body or "")
        if not body.strip():
            self._set_error("A note cannot be empty.")
            return False
        record = self._workspace.note_model._records[row]
        if record.get("entryType") != "note" or not record.get("canEdit"):
            return False
        if body == str(record.get("body") or ""):
            return True
        note = self._notes.get(record.get("searchKey"))
        if not note:
            self._set_error("The note is no longer available.")
            return False

        def operation():
            from thlib.environment import env_server
            info = note.get_info() or {}
            raw_metadata = info.get("metadata") or {}
            if isinstance(raw_metadata, dict):
                metadata = dict(raw_metadata)
            else:
                try:
                    metadata = json.loads(raw_metadata)
                except (TypeError, ValueError):
                    metadata = {}
            history = list(metadata.get("editHistory") or [])
            history.append({
                "body": str(info.get("note") or ""),
                "editedBy": str(env_server.get_user() or ""),
                "editedAt": datetime.datetime.now(datetime.UTC).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            })
            metadata["editHistory"] = history
            note.set_value("note", body)
            note.set_value("metadata", metadata)
            return note.commit(triggers=True)

        self._run(operation)
        return True

    @Slot(int, result=bool)
    def copy_skey(self, row):
        if not 0 <= row < len(self._workspace.note_model._records):
            return False
        record = self._workspace.note_model._records[row]
        if record.get("entryType") != "note":
            return False
        search_key = str(record.get("searchKey") or "").strip()
        if not search_key:
            return False
        from PySide6.QtGui import QGuiApplication

        value = (
            search_key if search_key.startswith("skey://")
            else "skey://" + search_key
        )
        QGuiApplication.clipboard().setText(value)
        return True

    @Slot(int)
    def remove(self, row):
        if self._busy or not 0 <= row < len(self._workspace.note_model._records):
            return
        record = self._workspace.note_model._records[row]
        if record.get("entryType") != "note" or not record.get("canDelete"):
            return
        note = self._notes.get(record.get("searchKey"))
        if not note:
            return
        self._run(lambda: note.delete_sobject(confirm=False))

    @Slot(str)
    def download_attachment(self, token):
        self.attachment_action(token, "download")

    @Slot(str, str)
    def attachment_action(self, token, action):
        token = str(token or "")
        action = str(action or "")
        file_object = self._files.get(str(token or ""))
        if not file_object:
            return
        try:
            if action == "download":
                if not file_object.is_exists():
                    self._application.repository_sync.schedule_file_object(
                        file_object, process="attachment", auto_start=True
                    )
            elif action == "open":
                if file_object.is_exists():
                    file_object.open_file()
                else:
                    self._open_after_download.add(token)
                    self._application.repository_sync.schedule_file_object(
                        file_object, process="attachment", auto_start=True
                    )
            elif action == "folder":
                file_object.open_folder()
            elif action == "copy_path":
                from PySide6.QtGui import QGuiApplication
                QGuiApplication.clipboard().setText(
                    str(file_object.get_full_abs_path() or "")
                )
            elif action == "copy_web":
                from PySide6.QtGui import QGuiApplication
                QGuiApplication.clipboard().setText(
                    str(file_object.get_full_web_path() or "")
                )
            elif action == "copy_image":
                from PySide6.QtGui import QGuiApplication, QImage
                image = QImage(str(file_object.get_full_abs_path() or ""))
                if image.isNull():
                    raise ValueError("The attachment is not a local image")
                QGuiApplication.clipboard().setImage(image)
        except Exception as error:
            self._set_error(error)
            debug_log = getattr(self._application, "debug_log", None)
            if debug_log:
                debug_log.raise_error(
                    error,
                    stacktrace=traceback.format_exc(),
                    group="communication/notes/attachments",
                )

    def _attachment_downloaded(self, file_object):
        if not any(
            tracked is file_object
            for tracked in (*self._files.values(), *self._preview_files.values())
        ):
            return
        changed = False
        for row, note in enumerate(self._workspace.note_model._records):
            attachments = [dict(record) for record in note.get("attachments") or []]
            row_changed = False
            for attachment in attachments:
                token = str(attachment.get("token") or "")
                tracked = self._files.get(token)
                preview = self._preview_files.get(token)
                if tracked is not file_object and preview is not file_object:
                    continue
                try:
                    attachment["local"] = bool(tracked and tracked.is_exists())
                    if preview and preview.is_exists():
                        attachment["previewUrl"] = QUrl.fromLocalFile(
                            str(preview.get_full_abs_path())
                        ).toString()
                except (AttributeError, OSError, RuntimeError, ValueError):
                    continue
                row_changed = True
                if tracked is file_object and token in self._open_after_download:
                    self._open_after_download.discard(token)
                    if tracked.is_exists():
                        tracked.open_file()
            if row_changed:
                self._workspace.note_model.set_value(row, "attachments", attachments)
                changed = True
        if changed:
            self._note_records = [
                dict(record) for record in self._workspace.note_model._records
                if record.get("entryType") == "note"
            ]
            self.stateChanged.emit()

    def _run(self, callback, clear_composer=False):
        from thlib.environment import env_inst
        request_id = uuid.uuid4().hex
        self._request_id = request_id
        self._busy = True
        self._clear_composer_after_mutation = bool(clear_composer)
        self._error = ""
        self.stateChanged.emit()
        worker = env_inst.server_pool.add_task(callback)
        self._worker = worker
        worker.result.connect(
            lambda _result: self._mutation_ready(),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._failed(request_id, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    def _mutation_ready(self):
        clear_composer = self._clear_composer_after_mutation
        self._clear_composer_after_mutation = False
        if clear_composer:
            self._pending_body = ""
            self._pending_target = ("", "")
            if self.attachments:
                self.attachments.clear()
        self._busy = False
        self._worker = None
        self.stateChanged.emit()
        if clear_composer:
            self.noteSent.emit()
        self.refresh()

    @Slot(str)
    def open_link(self, value):
        value = str(value or "").strip()
        if value.startswith("skey://"):
            self.open_skey_preview(value)
        elif value.startswith(("http://", "https://")):
            from PySide6.QtGui import QDesktopServices
            QDesktopServices.openUrl(QUrl(value))

    def _failed(self, request_id, error):
        if request_id and request_id != self._request_id:
            return
        payload = error[0] if isinstance(error, tuple) and error else error
        stacktrace = ""
        if isinstance(payload, dict):
            stacktrace = str(payload.get("stacktrace") or "")
            payload = payload.get("exception") or payload.get("message")
        self._set_error(payload or "Communication request failed")
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.raise_error(
                payload, stacktrace=stacktrace, group="communication"
            )
        self._finish()

    def _finish(self):
        self._busy = False
        self._loading = False
        self._worker = None
        self._request_context = None
        self.stateChanged.emit()

    def _set_error(self, value):
        self._error = str(value or "")
        self.stateChanged.emit()
