from __future__ import annotations

import traceback
import uuid
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QObject, Property, QTimer, Qt, Signal, Slot

from thlib.ui.task_data import format_hours_label
from thlib.ui.workspace_models.records import RecordListModel


ENTRY_ROLES = (
    "entryCode", "searchKey", "taskCode", "taskTitle", "process",
    "login", "loginLabel", "day", "startTime", "endTime",
    "regularHours", "overtimeHours", "totalHours", "category",
    "status", "statusLabel", "description", "canEdit", "canApprove",
    "selected",
)

REPORT_ROLES = (
    "key", "title", "description", "icon", "permission", "selected",
)

REPORT_VALUE_ROLES = (
    "label", "value", "valueLabel", "secondary", "accent", "share",
)


def _decimal(value) -> Decimal:
    try:
        return Decimal(str(value or 0))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")


def _hours(value) -> float:
    return float(_decimal(value).quantize(Decimal("0.01")))


def _day_text(value) -> str:
    return str(value or "")[:10]


class WorkHoursController(QObject):
    stateChanged = Signal()
    taskSummaryChanged = Signal(str, object)
    entrySaved = Signal()

    def __init__(self, application, tasks=None, users=None, parent=None):
        super().__init__(parent or application)
        self._application = application
        self._tasks = tasks
        self._users = users
        self.entries = RecordListModel(ENTRY_ROLES)
        self.timesheet_entries = RecordListModel(ENTRY_ROLES)
        self.report_descriptors = RecordListModel(REPORT_ROLES)
        self.report_values = RecordListModel(REPORT_VALUE_ROLES)
        self._task = None
        self._task_code = ""
        self._entries_by_task = {}
        self._summary_by_task = {}
        self._bid_duration_unit = "hour"
        self._permissions = {"manage": False, "viewCosts": False}
        self._rates = {}
        self._busy = False
        self._error = ""
        self._request_id = ""
        self._worker = None
        self._communication = None
        self._task_context_visible = False
        self._task_context_dirty = True
        self._selected_login = self._current_login()
        today = date.today()
        self._week_start = today - timedelta(days=today.weekday())
        self._selected_report = "my_hours"
        self._report_message = ""
        self._refresh_current_after_load = False
        self._visible_timer = QTimer(self)
        self._visible_timer.setSingleShot(True)
        self._visible_timer.setInterval(120)
        self._visible_timer.timeout.connect(self._load_visible_tasks)
        self._set_report_descriptors()
        if tasks is not None:
            tasks.visibleTaskSetChanged.connect(self.schedule_visible_refresh)
            tasks.advancedChanged.connect(self._apply_task_model_summaries)
            if tasks.advanced_model.count():
                self.schedule_visible_refresh()

    def attach_communication(self, controller):
        if controller is self._communication:
            return
        if self._communication is not None:
            try:
                self._communication.stateChanged.disconnect(
                    self._communication_state_changed
                )
            except (RuntimeError, TypeError):
                pass
        self._communication = controller
        if controller is not None:
            controller.stateChanged.connect(
                self._communication_state_changed
            )
        self._communication_state_changed()

    def _communication_state_changed(self):
        if not self._task_context_visible:
            self._task_context_dirty = True
            return
        self.sync_task_context()

    @staticmethod
    def _current_login():
        from thlib.environment import env_server
        return str(env_server.get_user() or "")

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._busy

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Property(bool, notify=stateChanged)
    def hasTask(self):
        return bool(self._task_code)

    @Property(str, notify=stateChanged)
    def taskCode(self):
        return self._task_code

    @Property(bool, notify=stateChanged)
    def canManage(self):
        return bool(self._permissions.get("manage"))

    @Property(bool, notify=stateChanged)
    def canViewCosts(self):
        return bool(self._permissions.get("viewCosts"))

    @Property("QVariantMap", notify=stateChanged)
    def currentSummary(self):
        return dict(self._summary_by_task.get(
            self._task_code, self._empty_summary(self._task)
        ))

    @Property("QVariantMap", notify=stateChanged)
    def timesheetSummary(self):
        records = self.timesheet_entries._records
        logged = sum(
            (_decimal(record.get("totalHours")) for record in records),
            Decimal("0"),
        )
        approved = sum(
            (
                _decimal(record.get("totalHours")) for record in records
                if record.get("status") == "approved"
            ),
            Decimal("0"),
        )
        overtime = sum(
            (_decimal(record.get("overtimeHours")) for record in records),
            Decimal("0"),
        )
        return {
            "logged": _hours(logged),
            "approved": _hours(approved),
            "pending": _hours(max(logged - approved, Decimal("0"))),
            "overtime": _hours(overtime),
            "entries": len(records),
        }

    @Property(str, notify=stateChanged)
    def selectedLogin(self):
        return self._selected_login

    @Property(str, notify=stateChanged)
    def weekStart(self):
        return self._week_start.isoformat()

    @Property(str, notify=stateChanged)
    def weekEnd(self):
        return (self._week_start + timedelta(days=6)).isoformat()

    @Property(str, notify=stateChanged)
    def selectedReport(self):
        return self._selected_report

    @Property(str, notify=stateChanged)
    def reportMessage(self):
        return self._report_message

    @Property(int, notify=stateChanged)
    def selectedCount(self):
        return sum(
            1 for record in self.timesheet_entries._records
            if record.get("selected")
        )

    def _task_planned_hours(self, task):
        if task is None:
            return Decimal("0")
        native_duration = getattr(task, "get_bid_duration", None)
        if callable(native_duration):
            return _decimal(native_duration("hour"))
        try:
            value = _decimal((task.get_info() or {}).get("bid_duration"))
        except (AttributeError, TypeError):
            return Decimal("0")
        if self._bid_duration_unit == "minute":
            value /= Decimal("60")
        return value

    def _empty_summary(self, task=None):
        planned = self._task_planned_hours(task)
        return {
            "planned": _hours(planned),
            "logged": 0.0,
            "approved": 0.0,
            "pending": 0.0,
            "remaining": _hours(max(planned, Decimal("0"))),
            "overPlan": 0.0,
            "overtime": 0.0,
            "entryCount": 0,
            "progress": 0.0,
            "label": format_hours_label(0.0, planned),
        }

    def _summary(self, task, entries):
        planned = self._task_planned_hours(task)
        logged = sum(
            (_decimal(entry.get_total_hours()) for entry in entries),
            Decimal("0"),
        )
        approved = sum(
            (
                _decimal(entry.get_total_hours())
                for entry in entries if entry.is_approved()
            ),
            Decimal("0"),
        )
        overtime = sum(
            (_decimal(entry.get_overtime_hours()) for entry in entries),
            Decimal("0"),
        )
        pending = max(logged - approved, Decimal("0"))
        remaining = max(planned - approved, Decimal("0"))
        over_plan = max(approved - planned, Decimal("0"))
        progress = (
            min(Decimal("100"), approved * Decimal("100") / planned)
            if planned > 0 else Decimal("0")
        )
        return {
            "planned": _hours(planned),
            "logged": _hours(logged),
            "approved": _hours(approved),
            "pending": _hours(pending),
            "remaining": _hours(remaining),
            "overPlan": _hours(over_plan),
            "overtime": _hours(overtime),
            "entryCount": len(entries),
            "progress": _hours(progress),
            "label": format_hours_label(approved, planned),
        }

    def _user_label(self, login):
        if self._users is not None:
            for record in self._users._records:
                if str(record.get("login") or "") == str(login or ""):
                    return str(record.get("displayName") or login)
        return str(login or "Removed user")

    def _task_object(self, task_code):
        if self._task is not None and task_code == self._task_code:
            return self._task
        store = getattr(self._tasks, "task_store", None)
        return store.tasks.get(task_code) if store is not None else None

    def _task_title(self, task_code):
        if self._tasks is not None:
            for record in self._tasks.advanced_model._records:
                if str(record.get("taskCode") or "") == task_code:
                    return str(
                        record.get("parentTitle")
                        or record.get("processLabel") or task_code
                    )
        return task_code

    def _entry_record(self, entry):
        info = dict(entry.get_info() or {})
        login = str(info.get("login") or "")
        total = entry.get_total_hours()
        status = str(info.get("status") or "")
        return {
            "entryCode": str(info.get("code") or ""),
            "searchKey": str(entry.get_search_key() or ""),
            "taskCode": str(info.get("task_code") or ""),
            "taskTitle": self._task_title(str(info.get("task_code") or "")),
            "process": str(info.get("process") or ""),
            "login": login,
            "loginLabel": self._user_label(login),
            "day": _day_text(info.get("day")),
            "startTime": str(info.get("start_time") or ""),
            "endTime": str(info.get("end_time") or ""),
            "regularHours": _hours(entry.get_regular_hours()),
            "overtimeHours": _hours(entry.get_overtime_hours()),
            "totalHours": _hours(total),
            "category": str(info.get("category") or "regular"),
            "status": status,
            "statusLabel": "Approved" if entry.is_approved() else "Pending",
            "description": str(info.get("description") or ""),
            "canEdit": entry.can_edit(),
            "canApprove": entry.can_approve(),
            "selected": False,
        }

    def _replace_current_entries(self):
        values = self._entries_by_task.get(self._task_code, [])
        records = [self._entry_record(entry) for entry in values]
        records.sort(key=lambda item: (item["day"], item["startTime"]), reverse=True)
        self.entries.replace(records)

    @Slot()
    def sync_task_context(self):
        task = (
            self._communication.selected_task_object()
            if self._communication is not None else None
        )
        try:
            task_code = str(task.get_code() or "") if task else ""
        except AttributeError:
            try:
                task_code = str((task.get_info() or {}).get("code") or "")
            except (AttributeError, TypeError):
                task_code = ""
        if task_code == self._task_code and task is self._task:
            return
        self._task = task
        self._task_code = task_code
        self._replace_current_entries()
        self.stateChanged.emit()
        if task_code:
            self.refresh_current()

    @Slot(bool)
    def set_task_context_visible(self, value):
        value = bool(value)
        if value == self._task_context_visible:
            return
        self._task_context_visible = value
        if value and self._task_context_dirty:
            self._task_context_dirty = False
            self.sync_task_context()

    @Slot()
    def schedule_visible_refresh(self):
        if not self._visible_timer.isActive():
            self._visible_timer.start()

    def _visible_task_codes(self):
        if self._tasks is None:
            return []
        return list(dict.fromkeys(
            str(record.get("taskCode") or "")
            for record in self._tasks.advanced_model._records
            if (
                record.get("taskCode")
                and not record.get("isNew")
                and not str(record.get("taskCode") or "").startswith(
                    "__new_task__"
                )
            )
        ))

    def _project_code(self):
        if self._task is not None:
            try:
                return str(self._task.get_project().get_code() or "")
            except AttributeError:
                pass
        from thlib.environment import env_inst
        project = env_inst.get_current_project()
        if isinstance(project, str):
            return project
        try:
            return str(project.get_code() or "")
        except AttributeError:
            return ""

    @Slot()
    def refresh_current(self):
        if self._task_code:
            self._load([self._task_code], mode="task")

    def reload_current(self):
        if self._task_code:
            self._load(
                [self._task_code], mode="task", bypass_cache=True
            )

    def _load_visible_tasks(self):
        codes = self._visible_task_codes()
        if codes:
            self._load(codes, mode="visible")

    @Slot()
    def refresh_timesheet(self):
        self._load_timesheet(True)

    @Slot()
    def load_timesheet(self):
        self._load_timesheet(False)

    def _load_timesheet(self, bypass_cache):
        self._load(
            [], mode="timesheet", login=self._selected_login,
            start_day=self.weekStart, end_day=self.weekEnd,
            include_rates=self.canManage,
            bypass_cache=bypass_cache,
        )

    def _load(self, task_codes, mode, login=None, start_day=None,
              end_day=None, include_rates=False, bypass_cache=False):
        project_code = self._project_code()
        if not project_code or self._busy:
            return
        request_id = uuid.uuid4().hex
        self._request_id = request_id
        self._busy = True
        self._error = ""
        self.stateChanged.emit()

        def operation():
            import json
            from thlib import server_cache
            import thlib.tactic_classes as tc

            cache_key = json.dumps(
                {
                    "tasks": sorted(str(value) for value in task_codes),
                    "login": str(login or ""),
                    "start": str(start_day or ""),
                    "end": str(end_day or ""),
                    "rates": bool(include_rates),
                },
                ensure_ascii=False, separators=(",", ":"), sort_keys=True,
            )
            if bypass_cache:
                server_cache.invalidate_domains(
                    ("work_hours", "tasks", "activity"), project_code
                )
            cache_token = server_cache.token("work_hours", project_code)
            cached = None if bypass_cache else server_cache.read_entry(
                "work_hours", cache_key, project_code,
            )
            if isinstance(cached, dict):
                return tc.query_work_hours(
                    task_codes, project_code, login=login,
                    start_day=start_day, end_day=end_day,
                    include_rates=include_rates, payload=cached,
                )
            result, raw_payload = tc.query_work_hours(
                task_codes, project_code, login=login,
                start_day=start_day, end_day=end_day,
                include_rates=include_rates,
                return_payload=True,
            )
            if cache_token is not None:
                server_cache.write_entry(
                    "work_hours", cache_key, raw_payload, project_code,
                    expected_token=cache_token,
                )
            return result

        self._run(
            operation,
            lambda result: self._loaded(request_id, mode, result),
            request_id,
        )

    def _loaded(self, request_id, mode, result):
        if request_id != self._request_id:
            return
        result = dict(result or {})
        self._bid_duration_unit = str(
            result.get("bidDurationUnit") or "hour"
        ).lower()
        self._permissions.update(result.get("permissions") or {})
        self._rates = dict(result.get("rates") or {})
        grouped = {}
        for entry in result.get("entries") or []:
            code = str(entry.get_value("task_code") or "")
            grouped.setdefault(code, []).append(entry)
        if mode in {"task", "visible"}:
            requested = (
                [self._task_code] if mode == "task"
                else self._visible_task_codes()
            )
            for code in requested:
                self._entries_by_task[code] = grouped.get(code, [])
                task = self._task_object(code)
                if task is not None:
                    try:
                        task.get_info()["__bid_duration_unit__"] = (
                            self._bid_duration_unit
                        )
                    except (AttributeError, TypeError):
                        pass
                summary = self._summary(task, self._entries_by_task[code])
                self._summary_by_task[code] = summary
                self.taskSummaryChanged.emit(code, summary)
            self._apply_task_model_summaries()
            self._replace_current_entries()
        else:
            self._entries_by_task.update(grouped)
            records = [
                self._entry_record(entry)
                for entries in grouped.values() for entry in entries
            ]
            records.sort(
                key=lambda item: (item["day"], item["loginLabel"]),
                reverse=True,
            )
            self.timesheet_entries.replace(records)
            self._rebuild_report_values(records)
        refresh_current = (
            mode == "timesheet" and self._refresh_current_after_load
        )
        self._refresh_current_after_load = False
        self._finish()
        if refresh_current:
            self.refresh_current()

    def _apply_task_model_summaries(self):
        if self._tasks is None:
            return
        for model in (
                self._tasks.advanced_model, self._tasks.table_model):
            for row, record in enumerate(model._records):
                # A virtual task has no native sthpw/task or work-hour rows yet.
                # Its planned hours are the bid_duration default supplied by the
                # selected workflow process and must survive background refreshes.
                if (
                        record.get("isNew")
                        or str(record.get("taskCode") or "").startswith(
                            "__new_task__"
                        )):
                    continue
                code = str(record.get("taskCode") or "")
                summary = self._summary_by_task.get(code)
                if not summary:
                    continue
                model.update_record(row, {
                    "plannedHours": summary["planned"],
                    "loggedHours": summary["logged"],
                    "approvedHours": summary["approved"],
                    "pendingHours": summary["pending"],
                    "remainingHours": summary["remaining"],
                    "overPlanHours": summary["overPlan"],
                    "hoursLabel": summary["label"],
                })

    @Slot(str)
    def set_selected_login(self, login):
        login = str(login or self._current_login())
        if login != self._current_login() and not self.canManage:
            return
        if login == self._selected_login:
            return
        self._selected_login = login
        self.stateChanged.emit()
        self.load_timesheet()

    @Slot(int)
    def move_week(self, offset):
        self._week_start += timedelta(days=int(offset) * 7)
        self.stateChanged.emit()
        self.load_timesheet()

    @Slot(str)
    def set_week(self, value):
        try:
            selected = date.fromisoformat(str(value or "")[:10])
        except ValueError:
            return
        self._week_start = selected - timedelta(days=selected.weekday())
        self.stateChanged.emit()
        self.load_timesheet()

    @Slot()
    def open_timesheet(self):
        self._application.dock_model.show_panel("timesheet")
        self.load_timesheet()

    @Slot()
    def open_work_reports(self):
        self._application.dock_model.show_panel("work_reports")
        self.load_report()

    @Slot()
    def open_cost_reports(self):
        if not self.canViewCosts:
            return
        self._application.dock_model.show_panel("cost_reports")
        self.select_report("labor_cost")

    @Slot(str, str, float, str, str, result=bool)
    @Slot(str, str, float, str, str, bool, result=bool)
    def log_time(self, day, category, duration, description, login,
                 approve=False):
        if not self._task or self._busy:
            return False
        if approve and not self.canManage:
            return False
        task = self._task
        login = str(login or self._current_login())

        def operation():
            import thlib.tactic_classes as tc
            return tc.WorkHour.create(
                task, day, duration, description=description,
                category=category, login=login, approve=bool(approve),
            )

        self._mutate(operation, refresh="current")
        return True

    @Slot(str, str, str, float, str, str, result=bool)
    @Slot(str, str, str, float, str, str, bool, result=bool)
    def update_time(self, entry_code, day, category, duration,
                    description, login, approve=False):
        entry = self._entry_by_code(entry_code)
        if entry is None or not entry.can_edit() or self._busy:
            return False
        if approve and (not self.canManage or not entry.can_approve()):
            return False

        def operation():
            return entry.update_entry(
                day=day, category=category, straight_time=duration,
                description=description, login=login,
                approve=bool(approve),
            )

        self._mutate(operation, refresh="timesheet")
        return True

    @Slot(str, bool)
    def set_approved(self, entry_code, approved):
        entry = self._entry_by_code(entry_code)
        if entry is None or not entry.can_approve() or self._busy:
            return
        self._mutate(
            lambda: entry.approve(bool(approved)), refresh="timesheet"
        )

    @Slot(str)
    def remove_entry(self, entry_code):
        entry = self._entry_by_code(entry_code)
        if entry is None or not entry.can_edit() or self._busy:
            return
        self._mutate(entry.delete, refresh="timesheet")

    @Slot(int)
    def toggle_timesheet_selected(self, row):
        if not 0 <= row < len(self.timesheet_entries._records):
            return
        record = self.timesheet_entries._records[row]
        if not record.get("canApprove"):
            return
        self.timesheet_entries.set_value(
            row, "selected", not bool(record.get("selected"))
        )
        self.stateChanged.emit()

    @Slot()
    def clear_timesheet_selection(self):
        changed = False
        for row, record in enumerate(self.timesheet_entries._records):
            if record.get("selected"):
                self.timesheet_entries.set_value(row, "selected", False)
                changed = True
        if changed:
            self.stateChanged.emit()

    @Slot(bool)
    def approve_selected(self, approved):
        if not self.canManage or self._busy:
            return
        codes = [
            str(record.get("entryCode") or "")
            for record in self.timesheet_entries._records
            if record.get("selected") and record.get("canApprove")
        ]
        if not codes:
            return
        project_code = self._project_code()

        def operation():
            import thlib.tactic_classes as tc
            return tc.set_work_hour_statuses(
                codes, bool(approved), project_code
            )

        self._mutate(operation, refresh="timesheet")

    def _entry_by_code(self, code):
        code = str(code or "")
        for entries in self._entries_by_task.values():
            for entry in entries:
                if str(entry.get_code() or "") == code:
                    return entry
        return None

    def _mutate(self, callback, refresh="current"):
        if self._busy:
            return
        request_id = uuid.uuid4().hex
        self._request_id = request_id
        self._busy = True
        self._error = ""
        self.stateChanged.emit()

        def ready(_result):
            if request_id != self._request_id:
                return
            self._busy = False
            self._worker = None
            self.entrySaved.emit()
            self.stateChanged.emit()
            self._summary_by_task.pop(self._task_code, None)
            if refresh == "timesheet":
                self._refresh_current_after_load = bool(self._task_code)
                self.refresh_timesheet()
            else:
                self.reload_current()

        self._run(callback, ready, request_id)

    def _set_report_descriptors(self):
        values = [
            ("my_hours", "My Work Hours", "Daily logged time", "schedule", "user"),
            ("bid_actual", "Bid vs Actual", "Planned and approved hours", "monitoring", "user"),
            ("approval", "Approval", "Approved and pending time", "approval", "supervisor"),
            ("team", "Team Hours", "Hours by user", "groups", "supervisor"),
            ("process", "Process Hours", "Hours by process", "account_tree", "supervisor"),
            ("labor_cost", "Labor Cost", "Authorized wage-based cost", "payments", "finance"),
        ]
        self.report_descriptors.replace([
            {
                "key": key, "title": title, "description": description,
                "icon": icon, "permission": permission,
                "selected": key == self._selected_report,
            }
            for key, title, description, icon, permission in values
        ])

    @Slot(str)
    def select_report(self, key):
        key = str(key or "")
        descriptor = next((
            value for value in self.report_descriptors._records
            if value["key"] == key
        ), None)
        if not descriptor:
            return
        if descriptor["permission"] in {"supervisor", "finance"}:
            if not self.canManage:
                return
        if descriptor["permission"] == "finance" and not self.canViewCosts:
            return
        self._selected_report = key
        self._report_message = ""
        for row, record in enumerate(self.report_descriptors._records):
            self.report_descriptors.set_value(
                row, "selected", record["key"] == key
            )
        self.load_report()
        self.stateChanged.emit()

    @Slot()
    def refresh_report(self):
        self._load_report(True)

    @Slot()
    def load_report(self):
        self._load_report(False)

    def _load_report(self, bypass_cache):
        project_code = self._project_code()
        if not project_code or self._busy:
            return
        request_id = uuid.uuid4().hex
        self._request_id = request_id
        self._busy = True
        self._error = ""
        self.stateChanged.emit()

        def operation():
            import json
            from thlib import server_cache
            import thlib.tactic_classes as tc

            cache_key = "report:" + json.dumps(
                {
                    "report": self._selected_report,
                    "start": self.weekStart,
                    "end": self.weekEnd,
                    "login": self._selected_login,
                },
                ensure_ascii=False, separators=(",", ":"), sort_keys=True,
            )
            if bypass_cache:
                server_cache.invalidate_domains(
                    ("work_hours", "tasks", "activity"), project_code
                )
            cache_token = server_cache.token("work_hours", project_code)
            cached = None if bypass_cache else server_cache.read_entry(
                "work_hours", cache_key, project_code,
            )
            if isinstance(cached, dict):
                return cached
            result = tc.query_work_hour_report(
                self._selected_report, project_code,
                start_day=self.weekStart, end_day=self.weekEnd,
                login=self._selected_login,
            )
            if cache_token is not None and isinstance(result, dict):
                server_cache.write_entry(
                    "work_hours", cache_key, result, project_code,
                    expected_token=cache_token,
                )
            return result

        self._run(
            operation,
            lambda result: self._report_loaded(request_id, result),
            request_id,
        )

    def _report_loaded(self, request_id, result):
        if request_id != self._request_id:
            return
        result = dict(result or {})
        self._report_message = str(result.get("message") or "")
        self._permissions.update(result.get("permissions") or {})
        values = [
            (str(row.get("label") or "Unspecified"), _decimal(row.get("value")))
            for row in result.get("rows") or []
        ]
        total = sum((value for _label, value in values), Decimal("0"))
        cost = result.get("unit") == "cost"
        self.report_values.replace([
            {
                "label": label,
                "value": _hours(value),
                "valueLabel": (
                    "{:.2f}".format(value) if cost
                    else "{} h".format(_hours(value))
                ),
                "secondary": "",
                "accent": "",
                "share": float(value / total) if total > 0 else 0.0,
            }
            for label, value in values
        ])
        self._finish()

    def _rebuild_report_values(self, records):
        key = self._selected_report
        groups = {}
        if key == "my_hours":
            source = [
                row for row in records
                if row.get("login") == self._selected_login
            ]
            group_role = "day"
        elif key == "team":
            source = list(records)
            group_role = "loginLabel"
        elif key == "process":
            source = list(records)
            group_role = "process"
        elif key == "approval":
            source = list(records)
            group_role = "statusLabel"
        elif key == "labor_cost":
            source = list(records)
            group_role = "loginLabel"
        else:
            source = list(records)
            group_role = "taskTitle"
        for row in source:
            label = str(row.get(group_role) or "Unspecified")
            groups.setdefault(label, Decimal("0"))
            if key == "labor_cost":
                rate = _decimal(self._rates.get(row.get("login")))
                groups[label] += _decimal(row.get("totalHours")) * rate
            elif key == "bid_actual":
                groups[label] += _decimal(row.get("totalHours"))
            else:
                groups[label] += _decimal(row.get("totalHours"))
        total = sum(groups.values(), Decimal("0"))
        self.report_values.replace([
            {
                "label": label,
                "value": _hours(value),
                "valueLabel": (
                    "{:.2f}".format(value) if key == "labor_cost"
                    else "{} h".format(_hours(value))
                ),
                "secondary": "",
                "accent": "",
                "share": float(value / total) if total > 0 else 0.0,
            }
            for label, value in sorted(
                groups.items(), key=lambda item: item[1], reverse=True
            )
        ])

    def _run(self, callback, success, request_id):
        from thlib.environment import env_inst
        worker = env_inst.server_pool.add_task(callback)
        self._worker = worker
        worker.result.connect(
            success, Qt.ConnectionType.QueuedConnection
        )
        worker.error.connect(
            lambda error: self._failed(request_id, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    def _failed(self, request_id, error):
        if request_id != self._request_id:
            return
        payload = error[0] if isinstance(error, tuple) and error else error
        stack = ""
        if isinstance(payload, dict):
            stack = str(payload.get("stacktrace") or "")
            payload = payload.get("exception") or payload.get("message")
        self._error = str(payload or "Work-hours request failed")
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.raise_error(
                self._error, stacktrace=stack or traceback.format_exc(),
                group="tasks/work-hours",
            )
        self._finish()

    def _finish(self):
        self._busy = False
        self._worker = None
        self.stateChanged.emit()

    def shutdown(self):
        self._visible_timer.stop()
        self._request_id = uuid.uuid4().hex
        self._worker = None
