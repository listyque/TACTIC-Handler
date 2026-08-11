from __future__ import annotations

import calendar
import copy
import json
import uuid
from datetime import date, datetime, timedelta

from PySide6.QtCore import QObject, Property, QTimer, Qt, Signal, Slot

from modern_ui.task_data import (
    calendar_cells,
    due_state,
    filtered_records,
    format_hours_label,
    gantt_layout,
    is_recent_record,
    is_review_record,
    parent_search_key,
    parse_datetime,
    progress_value,
    sort_and_group,
    task_record,
)
from modern_ui.task_workspace import TASK_ROLES, TaskWorkspaceStore
from modern_ui.task_workspace.field_catalog import load_task_field_catalog
from modern_ui.workspace_models.records import RecordListModel
from modern_ui.workflow_data import process_task_configuration


PROCESS_ROLES = (
    "process", "label", "color", "taskCount", "hasTask",
    "currentTaskCode", "currentTaskRow", "context", "status",
    "statusColor", "assigned", "assignedLabel", "start", "end",
    "dueState", "progress", "progressInput", "description", "notes",
    "statusChoices", "userChoices", "taskChoices", "validationError", "expanded",
    "dirty",
)

GANTT_ROLES = TASK_ROLES + (
    "ganttScheduled", "ganttStartDay", "ganttDurationDays",
    "ganttStartLabel", "ganttEndLabel", "ganttIssue", "ganttColor",
    "ganttSection", "ganttSectionFirst", "ganttWarning",
    "ganttGroupStartDay", "ganttGroupDurationDays", "ganttGroupProgress",
)

TASK_COLUMN_DEFAULTS = (
    ("object", "Object", 210, True, True),
    ("process", "Task / Process", 126, True, False),
    ("status", "Status", 138, True, True),
    ("assignee", "Assignee", 154, True, False),
    ("dates", "Start / Deadline", 112, True, False),
    ("progress", "Progress", 94, True, False),
    ("hours", "Hours", 86, True, False),
    ("notes", "Notes", 48, True, False),
    ("priority", "Priority", 96, False, False),
    ("milestone", "Milestone", 132, False, False),
    ("supervisor", "Supervisor", 154, False, False),
)

class TasksController(QObject):
    stateChanged = Signal()
    editorChanged = Signal()
    advancedChanged = Signal()
    bulkChanged = Signal()
    taskActivated = Signal(str, str, str)
    taskDraftCreated = Signal(str)
    taskDraftRemoved = Signal(str)
    advancedVisibilityChanged = Signal(bool)
    visibleTaskSetChanged = Signal()

    @property
    def _advanced_visible(self):
        return self.task_store.visible

    @_advanced_visible.setter
    def _advanced_visible(self, value):
        self.task_store.visible = bool(value)

    @property
    def _advanced_busy(self):
        return self.task_store.busy

    @_advanced_busy.setter
    def _advanced_busy(self, value):
        self.task_store.busy = bool(value)

    @property
    def _advanced_error(self):
        return self.task_store.error

    @_advanced_error.setter
    def _advanced_error(self, value):
        self.task_store.error = str(value or "")

    @property
    def _advanced_scope(self):
        return self.task_store.scope

    @_advanced_scope.setter
    def _advanced_scope(self, value):
        self.task_store.scope = str(value or "object")

    @property
    def _advanced_user(self):
        return self.task_store.user

    @_advanced_user.setter
    def _advanced_user(self, value):
        self.task_store.user = str(value or "")

    @property
    def _advanced_target(self):
        return self.task_store.target

    @_advanced_target.setter
    def _advanced_target(self, value):
        self.task_store.target = value

    @property
    def _advanced_target_key(self):
        return self.task_store.target_key

    @_advanced_target_key.setter
    def _advanced_target_key(self, value):
        self.task_store.target_key = str(value or "")

    @property
    def _advanced_target_title(self):
        return self.task_store.target_title

    @_advanced_target_title.setter
    def _advanced_target_title(self, value):
        self.task_store.target_title = str(value or "")

    @property
    def _advanced_request_id(self):
        return self.task_store.request_id

    @_advanced_request_id.setter
    def _advanced_request_id(self, value):
        self.task_store.request_id = str(value or "")

    @property
    def _advanced_worker(self):
        return self.task_store.worker

    @_advanced_worker.setter
    def _advanced_worker(self, value):
        self.task_store.worker = value

    @property
    def _advanced_tasks(self):
        return self.task_store.tasks

    @_advanced_tasks.setter
    def _advanced_tasks(self, value):
        values = value.values() if isinstance(value, dict) else value
        self.task_store.set_tasks(values or [])

    @property
    def _advanced_parents(self):
        return self.task_store.parents

    @_advanced_parents.setter
    def _advanced_parents(self, value):
        self.task_store.set_parents(value or [])

    @property
    def _advanced_raw(self):
        return self.task_store.records

    @_advanced_raw.setter
    def _advanced_raw(self, value):
        self.task_store.set_records(value or [])

    @property
    def _multiple_targets(self):
        return self.task_store.targets

    @_multiple_targets.setter
    def _multiple_targets(self, value):
        self.task_store.targets = list(value or [])

    def __init__(self, application, parent=None):
        super().__init__(parent or application)
        self._application = application
        self._workspace = application.workspace_state
        self.task_store = TaskWorkspaceStore(self)
        self._settings = getattr(application, "_settings", None)
        self.process_model = RecordListModel(PROCESS_ROLES)
        self.advanced_model = self.task_store.model
        self.table_model = RecordListModel(TASK_ROLES)
        self.gantt_model = RecordListModel(GANTT_ROLES)
        self.calendar_model = RecordListModel((
            "date", "day", "inMonth", "today", "taskCount",
            "overdueCount", "tasks", "milestoneCount", "milestones",
            "selected",
        ))
        self.history_model = RecordListModel((
            "timestamp", "fromStatus", "toStatus", "login", "color",
        ))

        self._mode = ""
        self._row = -1
        self._editor = {}
        self._editor_task = None
        self._editor_target = None
        self._busy = False
        self._error = ""
        self._processes = []
        self._statuses = []
        self._users = []
        self._worker = None
        self._request_id = ""
        self._full_target_key = ""
        self._compact_visible = False
        self._preferred_task = {}
        self._process_drafts = {}
        self._quick_view_mode = self._saved_choice(
            "tasks/quickViewMode", "cards", {"cards", "compact"}
        )
        self._workspace_surface = self._saved_choice(
            "tasks/workspaceSurface", "quick", {"quick", "browser"}
        )

        self._advanced_visible = False
        self._advanced_busy = False
        self._advanced_error = ""
        self._advanced_scope = "object"
        self._advanced_user = ""
        self._advanced_target = None
        self._advanced_target_key = ""
        self._advanced_target_title = ""
        self._advanced_object_process = ""
        self._advanced_request_id = ""
        self._advanced_worker = None
        self._advanced_tasks = {}
        self._advanced_parents = {}
        self._advanced_raw = []
        self._task_field_catalogs = {}
        self._task_field_catalog_worker = None
        self._task_field_catalog_attempts = {}
        self._milestone_controller = None
        self._filters = {
            "text": "", "process": "", "status": "", "assigned": "",
            "due": "", "hasNotes": False, "day": "", "priority": "",
            "milestone": "", "supervisor": "",
        }
        self._quick_filters = {
            "preset": set(), "process": set(),
            "status": set(), "assigned": set(), "priority": set(),
            "milestone": set(), "supervisor": set(),
        }
        self._sort_mode = self._saved_choice(
            "tasks/sortMode", "due",
            {
                "due", "recent", "process", "user", "status", "object",
                "priority", "milestone", "supervisor",
            },
        )
        self._group_mode = self._saved_choice(
            "tasks/groupMode", "process",
            {
                "process", "status", "user", "object", "project",
                "search_type", "none",
            },
        )
        self._collapsed_groups = set()
        self._view_mode = self._saved_choice(
            "tasks/viewMode", "list", {"list", "gantt"}
        )
        self._task_columns = self._load_task_columns()
        self._gantt = gantt_layout([])
        today = date.today()
        self._calendar_year = today.year
        self._calendar_month = today.month
        self._selected_advanced_code = ""
        self._history_request_id = ""
        self._history_busy = False
        self._history_loaded = set()
        self._multiple_targets = []
        self._bulk = {}
        self._bulk_busy = False
        self._bulk_worker = None
        self._bulk_request_id = ""
        self._advanced_checked = set()
        self._advanced_selection_anchor = ""
        self._advanced_drafts = {}
        self._advanced_inserts = {}
        self._advanced_row_errors = {}
        self._advanced_conflicts = {}
        self._gantt_undo = []
        self._gantt_redo = []
        self._gantt_working_days = False
        self._gantt_resource_mode = False
        self._gantt_resource_previous = None
        self._advanced_saving = False
        self._advanced_save_worker = None
        self._snapshot_refresh_requests = {}
        self._live_task_codes = set()
        self._seen_note_events = set()
        self._seen_note_event_order = []
        self._visible_work_hour_task_codes = frozenset()
        self._live_worker = None
        self._live_inflight_codes = set()
        self._live_request_id = ""
        self._live_timer = QTimer(self)
        self._live_timer.setSingleShot(True)
        self._live_timer.setInterval(200)
        self._live_timer.timeout.connect(self._flush_live_task_updates)
        self._performance_metrics = {
            "projectionRebuilds": 0,
            "modelResets": 0,
            "modelDataChanges": 0,
            "rowStructureChanges": 0,
            "advancedSignals": 0,
            "serverQueries": 0,
            "liveBatches": 0,
        }
        self.advanced_model.modelReset.connect(
            lambda: self._increment_performance_metric("modelResets")
        )
        self.advanced_model.dataChanged.connect(
            lambda _first, _last, _roles: self._increment_performance_metric(
                "modelDataChanges"
            )
        )
        self.advanced_model.rowsInserted.connect(
            lambda _parent, _first, _last: self._increment_performance_metric(
                "rowStructureChanges"
            )
        )
        self.advanced_model.rowsRemoved.connect(
            lambda _parent, _first, _last: self._increment_performance_metric(
                "rowStructureChanges"
            )
        )
        self.advancedChanged.connect(
            lambda: self._increment_performance_metric("advancedSignals")
        )

        self._workspace.selection_changed.connect(self._selection_changed)
        application.project_changed.connect(self._project_changed)
        snapshot_signal = getattr(
            application, "snapshot_data_changed", None
        )
        if snapshot_signal is not None:
            snapshot_signal.connect(self._snapshot_data_changed)
        visibility_signal = getattr(
            application.dock_model, "panelVisibilityChanged", None
        )
        if visibility_signal is not None:
            visibility_signal.connect(self._dock_visibility_changed)
        application._registry.register(
            "show_tasks_workspace", self.open_workspace
        )
        application._registry.register(
            "show_task_calendar", self.open_calendar
        )
        self._selection_changed()

    def _saved_choice(self, key, default, allowed):
        if self._settings is None:
            return default
        value = str(self._settings.value(key, default, type=str) or default)
        return value if value in allowed else default

    def _increment_performance_metric(self, key, amount=1):
        self._performance_metrics[key] = (
            int(self._performance_metrics.get(key, 0)) + int(amount)
        )

    @staticmethod
    def _default_task_columns():
        return [
            {
                "key": key, "label": label, "width": width,
                "visible": visible, "required": required, "order": order,
            }
            for order, (key, label, width, visible, required)
            in enumerate(TASK_COLUMN_DEFAULTS)
        ]

    @classmethod
    def _normalize_task_columns(cls, values):
        defaults = {
            item["key"]: item for item in cls._default_task_columns()
        }
        ordered = []
        seen = set()
        source_values = [
            dict(item) for item in (values or []) if isinstance(item, dict)
        ]
        try:
            source_values.sort(
                key=lambda item: int(item.get("order", len(defaults)))
            )
        except (TypeError, ValueError):
            pass
        for value in source_values:
            key = str(value.get("key") or "")
            if key not in defaults or key in seen:
                continue
            item = dict(defaults[key])
            try:
                item["width"] = max(
                    40, min(480, int(value.get("width", item["width"])))
                )
            except (TypeError, ValueError):
                pass
            item["visible"] = (
                True if item["required"] else bool(
                    value.get("visible", item["visible"])
                )
            )
            ordered.append(item)
            seen.add(key)
        ordered.extend(
            dict(item) for key, item in defaults.items() if key not in seen
        )
        for order, item in enumerate(ordered):
            item["order"] = order
        return ordered

    def _load_task_columns(self):
        if self._settings is None:
            return self._default_task_columns()
        raw = self._settings.value("tasks/columns", "", type=str)
        try:
            values = json.loads(raw) if raw else []
        except (TypeError, ValueError):
            values = []
        return self._normalize_task_columns(values)

    def _store_workspace_preferences(self):
        if self._settings is None:
            return
        self._settings.setValue("tasks/viewMode", self._view_mode)
        self._settings.setValue("tasks/sortMode", self._sort_mode)
        self._settings.setValue("tasks/groupMode", self._group_mode)
        self._settings.setValue(
            "tasks/quickViewMode", self._quick_view_mode
        )
        self._settings.setValue(
            "tasks/workspaceSurface", self._workspace_surface
        )
        self._settings.setValue(
            "tasks/columns", json.dumps(self._task_columns)
        )
        self._settings.sync()

    def configuration_values(self):
        return {
            "viewMode": self._view_mode,
            "sortMode": self._sort_mode,
            "groupMode": self._group_mode,
            "columns": [dict(item) for item in self._task_columns],
        }

    def apply_configuration(self, values):
        values = dict(values or {})
        view_mode = str(values.get("viewMode") or "list")
        sort_mode = str(values.get("sortMode") or "due")
        group_mode = str(values.get("groupMode") or "process")
        if view_mode in {"list", "gantt"}:
            self._view_mode = view_mode
        if sort_mode in {
            "due", "recent", "process", "user", "status", "object"
        }:
            self._sort_mode = sort_mode
        if group_mode in {
            "process", "status", "user", "object", "project",
            "search_type", "none",
        }:
            self._group_mode = group_mode
        self._task_columns = self._normalize_task_columns(
            values.get("columns")
        )
        self._store_workspace_preferences()
        self._rebuild_advanced_models()

    def attach_commit_queue(self, commit_queue):
        signal = getattr(commit_queue, "operationCompleted", None)
        if signal is not None:
            signal.connect(self._checkin_completed)

    @Slot("QVariantMap")
    def _checkin_completed(self, payload):
        payload = dict(payload or {})
        parent_key = str(payload.get("searchKey") or "")
        process = str(payload.get("process") or "")
        if not parent_key or not process:
            return
        invalidator = getattr(
            self._application, "invalidate_task_snapshot_context", None
        )
        if callable(invalidator):
            invalidator(parent_key, process)
        visibility = getattr(
            self._application.dock_model, "is_panel_visible", None
        )
        snapshot_visible = (
            bool(visibility("snapshot")) if callable(visibility) else True
        )
        if (
            parent_key == getattr(
                self._application, "_selected_detail_key", ""
            )
            and (
                getattr(self._application, "_task_snapshot_source", None)
                is None
                or snapshot_visible
            )
        ):
            return
        parent = next((
            value for value in self.task_store.parents.values()
            if self.task_store._target_token(value) == parent_key
        ), None)
        if parent is None:
            return
        request_id = uuid.uuid4().hex
        token = (parent_key, process)
        self._snapshot_refresh_requests[token] = request_id
        try:
            from thlib.environment import env_inst

            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            worker = env_inst.server_pool.add_task(
                parent.update_snapshots,
                order_bys=["timestamp desc"],
            )
            if worker is None:
                raise RuntimeError("Server worker pool is not available")
            worker.result.connect(
                lambda _result: self._snapshot_summary_refresh_ready(
                    token, request_id
                ),
                Qt.ConnectionType.QueuedConnection,
            )
            worker.error.connect(
                lambda error: self._snapshot_summary_refresh_failed(
                    token, request_id, error
                ),
                Qt.ConnectionType.QueuedConnection,
            )
            worker.start()
        except Exception as error:
            self._snapshot_summary_refresh_failed(
                token, request_id, error
            )

    def _snapshot_summary_refresh_ready(self, token, request_id):
        if self._snapshot_refresh_requests.get(token) != request_id:
            return
        self._snapshot_refresh_requests.pop(token, None)
        marker = getattr(
            self._application, "mark_task_snapshot_source_current", None
        )
        if callable(marker):
            marker(token[0])
        self._snapshot_data_changed(*token)

    def _snapshot_summary_refresh_failed(
        self, token, request_id, error,
    ):
        if self._snapshot_refresh_requests.get(token) != request_id:
            return
        self._snapshot_refresh_requests.pop(token, None)
        if self._application.debug_log:
            payload = error[0] if isinstance(error, tuple) and error else error
            self._application.debug_log.raise_error(
                payload, group="tasks/snapshot-summary"
            )

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._busy

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Property(bool, notify=editorChanged)
    def editorVisible(self):
        return bool(self._mode)

    @Property(str, notify=editorChanged)
    def mode(self):
        return self._mode

    @Property("QVariantMap", notify=editorChanged)
    def editor(self):
        return dict(self._editor)

    @Property("QVariantList", notify=editorChanged)
    def processes(self):
        return list(self._processes)

    @Property("QVariantList", notify=editorChanged)
    def statuses(self):
        return list(self._statuses)

    @Property("QVariantList", notify=editorChanged)
    def users(self):
        return list(self._users)

    @Property(bool, notify=editorChanged)
    def progressSupported(self):
        return bool(self._progress_column())

    @Property(bool, notify=stateChanged)
    def hasTarget(self):
        return self._workspace._selected_sobject is not None

    @Property(str, notify=stateChanged)
    def targetTitle(self):
        target = self._workspace._selected_sobject
        try:
            return str(target.get_title() or target.get_code() or "")
        except AttributeError:
            return ""

    @Property(str, notify=stateChanged)
    def targetSearchKey(self):
        target = self._workspace._selected_sobject
        try:
            return str(target.get_search_key() or "")
        except AttributeError:
            return ""

    @Property(str, notify=stateChanged)
    def quickViewMode(self):
        return self._quick_view_mode

    @Property(str, notify=stateChanged)
    def workspaceSurface(self):
        return self._workspace_surface

    @Property(int, notify=stateChanged)
    def dirtyProcessCount(self):
        return len(self._process_drafts)

    @Property(bool, notify=advancedChanged)
    def advancedBusy(self):
        return self._advanced_busy

    @Property(str, notify=advancedChanged)
    def advancedError(self):
        return self._advanced_error

    @Property(str, notify=advancedChanged)
    def advancedScope(self):
        return self._advanced_scope

    @Property(str, notify=advancedChanged)
    def advancedTitle(self):
        if self._advanced_scope == "user":
            label = self._login_label(self._advanced_user)
            return "Tasks assigned to {}".format(label or self._advanced_user)
        if self._advanced_scope == "project":
            return "Project tasks"
        if self._advanced_scope == "search_type":
            return self._advanced_target_title or "Search type tasks"
        if self._advanced_scope == "team":
            team = next((
                item for item in self._team_options()
                if item["value"] == self._advanced_user
            ), {})
            return "Team tasks: {}".format(
                team.get("label") or self._advanced_user or "All members"
            )
        if self._advanced_scope == "multiple":
            return "{} selected sObjects".format(len(self._multiple_targets))
        return self._advanced_target_title or self.targetTitle or "Object tasks"

    @Property(str, notify=advancedChanged)
    def advancedDockTitle(self):
        if self._advanced_scope == "user":
            label = self._login_label(self._advanced_user)
            return "Tasks for: {}".format(
                label or self._advanced_user or "User"
            )
        if self._advanced_scope == "project":
            return "Tasks for: Project"
        if self._advanced_scope == "search_type":
            return "Tasks for: {}".format(
                self._advanced_target_title or "Search Type"
            )
        if self._advanced_scope == "team":
            team = next((
                item for item in self._team_options()
                if item["value"] == self._advanced_user
            ), {})
            return "Tasks for: {}".format(
                team.get("label") or self._advanced_user or "All Members"
            )
        if self._advanced_scope == "multiple":
            return "Tasks for: {} selected objects".format(
                len(self._multiple_targets)
            )
        title = self._advanced_target_title or self.targetTitle
        return "Tasks for: {}".format(title or "Current Object")

    @Property(str, notify=advancedChanged)
    def advancedDockSubject(self):
        """Return only the data portion of the task dock title."""
        if self._advanced_scope == "user":
            return self._login_label(self._advanced_user) \
                or self._advanced_user or ""
        if self._advanced_scope == "search_type":
            return self._advanced_target_title or ""
        if self._advanced_scope == "team":
            team = next((
                item for item in self._team_options()
                if item["value"] == self._advanced_user
            ), {})
            return str(team.get("label") or self._advanced_user or "")
        if self._advanced_scope == "multiple":
            return str(len(self._multiple_targets))
        if self._advanced_scope == "project":
            return ""
        return self._advanced_target_title or self.targetTitle or ""

    @Property(str, notify=advancedChanged)
    def advancedUser(self):
        return self._advanced_user

    @Property(bool, notify=advancedChanged)
    def advancedHasMore(self):
        return self.task_store.has_more

    @Property(int, notify=advancedChanged)
    def advancedLoadedCount(self):
        return len(self.task_store.tasks)

    @Property(int, notify=advancedChanged)
    def advancedTotalCount(self):
        return self.task_store.total_count

    @Property(int, notify=advancedChanged)
    def advancedProcessCount(self):
        return len({
            str(record.get("process") or "")
            for record in self.advanced_model._records
            if record.get("process")
        })

    @Property(bool, notify=advancedChanged)
    def advancedFiltersActive(self):
        return any(bool(value) for value in self._filters.values()) or any(
            bool(values) for values in self._quick_filters.values()
        )

    @Property(str, notify=advancedChanged)
    def advancedEmptyMessage(self):
        if self.advancedFiltersActive:
            return "No tasks match the current filters"
        if self._advanced_scope == "object":
            if not self._advanced_target_key:
                return "Select an sObject to view tasks"
            if self._advanced_object_process:
                return "No task exists for the selected process"
            return "This sObject has no tasks"
        if self._advanced_scope == "multiple":
            return "The selected sObjects have no tasks"
        if self._advanced_scope == "search_type":
            return "No tasks exist for objects of this search type"
        return "No tasks are available in the current scope"

    @Property("QVariantMap", notify=advancedChanged)
    def performanceMetrics(self):
        values = dict(self._performance_metrics)
        values["delegateCount"] = self.table_model.count()
        return values

    @Property(bool, notify=advancedChanged)
    def managementScope(self):
        return self._advanced_scope in {
            "team", "project", "multiple", "search_type",
        }

    @Property(bool, notify=advancedChanged)
    def personalScope(self):
        return (
            self._advanced_scope == "user"
            and self._advanced_user == self._current_login()
        )

    def _advanced_creation_target(self):
        task = self._advanced_tasks.get(self._selected_advanced_code)
        target = self.task_store.parent_for_task(task) if task else None
        return target or self._workspace._selected_sobject

    @Property(bool, notify=advancedChanged)
    def canCreateAdvancedTask(self):
        target = self._advanced_creation_target()
        return bool(target and self._process_choices_for(target))

    @Property("QVariantList", notify=advancedChanged)
    def teamOptions(self):
        return self._team_options()

    @Property(bool, notify=advancedChanged)
    def searchTypeScopeAvailable(self):
        return bool(self._selected_search_type_scope()[0])

    @Property(str, notify=advancedChanged)
    def searchTypeScopeLabel(self):
        name = self.searchTypeScopeName
        return "All {}".format(name) if name else "Search Type"

    @Property(str, notify=advancedChanged)
    def searchTypeScopeName(self):
        """Return the server-defined Search Type name without UI wording."""
        return self._selected_search_type_scope()[1]

    @Property("QVariantMap", notify=advancedChanged)
    def workspaceSummary(self):
        records = self._quick_filter_source()
        total = self.task_store.total_count
        loaded = len(records)
        complete = not self.task_store.has_more and (
            total < 0 or loaded >= total
        )
        return {
            "loaded": loaded,
            "total": total,
            "complete": complete,
            "unassigned": sum(
                1 for record in records if not record.get("assigned")
            ),
            "overdue": sum(
                1 for record in records
                if record.get("dueState") == "overdue"
            ),
            "today": sum(
                1 for record in records if record.get("dueState") == "today"
            ),
            "review": sum(is_review_record(record) for record in records),
            "recent": sum(is_recent_record(record) for record in records),
        }

    @Property("QVariantList", notify=advancedChanged)
    def workloadSummary(self):
        users = {}
        for record in self._quick_filter_source():
            login = str(record.get("assigned") or "")
            item = users.setdefault(login, {
                "login": login,
                "label": str(
                    record.get("assignedLabel") or "Not assigned"
                ),
                "avatarUrl": str(record.get("assignedAvatar") or ""),
                "count": 0,
                "overdue": 0,
                "review": 0,
            })
            item["count"] += 1
            item["overdue"] += record.get("dueState") == "overdue"
            item["review"] += is_review_record(record)
            if not item["avatarUrl"]:
                item["avatarUrl"] = str(record.get("assignedAvatar") or "")
        return sorted(
            users.values(),
            key=lambda item: (
                not bool(item["overdue"]), -item["count"],
                item["label"].casefold(),
            ),
        )

    @Property("QVariantList", notify=advancedChanged)
    def statusDistribution(self):
        statuses = {}
        for record in self._quick_filter_source():
            status = str(record.get("status") or "")
            key = status or "__none__"
            item = statuses.setdefault(key, {
                "status": status,
                "label": status or "No status",
                "color": str(record.get("statusColor") or ""),
                "count": 0,
            })
            item["count"] += 1
        return sorted(
            statuses.values(),
            key=lambda item: (-item["count"], item["label"].casefold()),
        )

    @Property(int, notify=advancedChanged)
    def advancedCheckedCount(self):
        return len(self._advanced_checked)

    @Property(bool, notify=advancedChanged)
    def advancedAllVisibleChecked(self):
        codes = {
            str(record.get("taskCode") or "")
            for record in self.advanced_model._records
            if record.get("taskCode")
        }
        return bool(codes) and codes.issubset(self._advanced_checked)

    @Property(int, notify=advancedChanged)
    def advancedDirtyCount(self):
        return len(self._advanced_drafts)

    @Property(bool, notify=advancedChanged)
    def advancedSaving(self):
        return self._advanced_saving

    @Property("QVariantMap", notify=advancedChanged)
    def advancedFilters(self):
        return dict(self._filters)

    @Property("QVariantList", notify=advancedChanged)
    def quickFilterGroups(self):
        return self._quick_filter_groups()

    @Property("QVariantList", notify=advancedChanged)
    def activeQuickFilters(self):
        active = []
        for group in self._quick_filter_groups():
            for option in group.get("options") or []:
                if option.get("selected"):
                    active.append({
                        "group": group["key"],
                        "key": option["key"],
                        "title": option["title"],
                        "accent": option.get("accent") or "",
                    })
        return active

    @Property(int, notify=advancedChanged)
    def activeQuickFilterCount(self):
        return sum(len(values) for values in self._quick_filters.values())

    @Property(str, notify=advancedChanged)
    def viewMode(self):
        return self._view_mode

    @Property("QVariantList", notify=advancedChanged)
    def taskColumns(self):
        return [dict(item) for item in self._task_columns]

    @Property("QVariantList", notify=advancedChanged)
    def taskPriorityChoices(self):
        project_code = str(self._application._current_project_code or "")
        catalog = dict(self._task_field_catalogs.get(project_code) or {})
        return [
            dict(item) for item in catalog.get("priorityChoices") or []
        ]

    @Slot(str)
    def toggle_task_column(self, key):
        key = str(key or "")
        for item in self._task_columns:
            if item.get("key") != key or item.get("required"):
                continue
            item["visible"] = not bool(item.get("visible"))
            self._store_workspace_preferences()
            self.advancedChanged.emit()
            return

    @Property("QVariantMap", notify=advancedChanged)
    def ganttRange(self):
        return {
            key: self._gantt.get(key)
            for key in ("rangeStart", "rangeEnd", "days", "todayDay")
        }

    @Property("QVariantList", notify=advancedChanged)
    def ganttTicks(self):
        return list(self._gantt.get("ticks") or [])

    @Property("QVariantMap", notify=advancedChanged)
    def ganttTickSets(self):
        return dict(self._gantt.get("tickSets") or {})

    @Property(int, notify=advancedChanged)
    def ganttScheduledCount(self):
        return int(self._gantt.get("scheduled") or 0)

    @Property(int, notify=advancedChanged)
    def ganttUnscheduledCount(self):
        return int(self._gantt.get("unscheduled") or 0)

    @Property("QVariantList", notify=advancedChanged)
    def ganttWeekendSpans(self):
        return list(self._gantt.get("weekends") or [])

    @Property("QVariantList", notify=advancedChanged)
    def ganttOverview(self):
        return list(self._gantt.get("overview") or [])

    @Property("QVariantList", notify=advancedChanged)
    def ganttMilestones(self):
        return list(self._gantt.get("milestones") or [])

    @Property(int, notify=advancedChanged)
    def ganttWarningCount(self):
        return int(self._gantt.get("warnings") or 0)

    @Property(bool, notify=advancedChanged)
    def ganttCanUndo(self):
        return bool(self._gantt_undo) and not self._advanced_saving

    @Property(bool, notify=advancedChanged)
    def ganttCanRedo(self):
        return bool(self._gantt_redo) and not self._advanced_saving

    @Property(bool, notify=advancedChanged)
    def ganttWorkingDays(self):
        return self._gantt_working_days

    @Property(bool, notify=advancedChanged)
    def ganttResourceMode(self):
        return self._gantt_resource_mode

    @Property("QVariantList", notify=advancedChanged)
    def ganttChangePreview(self):
        result = []
        for record in self._advanced_raw:
            code = str(record.get("taskCode") or "")
            draft = self._advanced_drafts.get(code) or {}
            if not any(key in draft for key in ("start", "end", "progress")):
                continue
            current = self._advanced_record_with_draft(record)
            result.append({
                "taskCode": code,
                "title": str(current.get("parentTitle") or "sObject"),
                "process": str(current.get("processLabel") or "Task"),
                "start": str(current.get("start") or ""),
                "end": str(current.get("end") or ""),
                "progress": int(current.get("progress") or 0),
            })
        return result

    @Property(str, notify=advancedChanged)
    def sortMode(self):
        return self._sort_mode

    @Property(str, notify=advancedChanged)
    def groupMode(self):
        return self._group_mode

    @Property("QVariantList", notify=advancedChanged)
    def sortOptions(self):
        return [
            {"label": "Deadline", "value": "due"},
            {"label": "Recently changed", "value": "recent"},
            {"label": "Process", "value": "process"},
            {"label": "Assignee", "value": "user"},
            {"label": "Status", "value": "status"},
            {"label": "Parent object", "value": "object"},
            {"label": "Priority", "value": "priority"},
            {"label": "Milestone", "value": "milestone"},
            {"label": "Supervisor", "value": "supervisor"},
        ]

    @Property("QVariantList", notify=advancedChanged)
    def groupOptions(self):
        options = [
            {"label": "By Process", "value": "process"},
            {"label": "By Status", "value": "status"},
            {"label": "By Assignee", "value": "user"},
            {"label": "By Parent Object", "value": "object"},
        ]
        projects = {
            str(record.get("project") or "")
            for record in self._advanced_raw if record.get("project")
        }
        search_types = {
            str(record.get("parentSearchType") or "")
            for record in self._advanced_raw if record.get("parentSearchType")
        }
        if len(projects) > 1:
            options.append({"label": "By Project", "value": "project"})
        if len(search_types) > 1:
            options.append({
                "label": "By Search Type", "value": "search_type"
            })
        options.append({"label": "No Groups", "value": "none"})
        return options

    @Property(str, notify=advancedChanged)
    def calendarTitle(self):
        return "{} {}".format(
            calendar.month_name[self._calendar_month], self._calendar_year
        )

    @Property(str, notify=advancedChanged)
    def selectedDay(self):
        return str(self._filters.get("day") or "")

    @Property(bool, notify=advancedChanged)
    def historyBusy(self):
        return self._history_busy

    @Property("QVariantList", notify=advancedChanged)
    def processFilterOptions(self):
        return self._filter_options("process", "processLabel", "All processes")

    @Property("QVariantList", notify=advancedChanged)
    def statusFilterOptions(self):
        return self._filter_options("status", "status", "All statuses")

    @Property("QVariantList", notify=advancedChanged)
    def userFilterOptions(self):
        return self._all_user_choices("All users")

    @Property("QVariantList", notify=advancedChanged)
    def bulkProcessOptions(self):
        if not self._multiple_targets:
            return []
        common = None
        labels = {}
        for target in self._multiple_targets:
            choices = self._process_choices_for(target)
            values = {item["value"] for item in choices}
            common = values if common is None else common.intersection(values)
            labels.update({item["value"]: item for item in choices})
        return [labels[value] for value in labels if value in (common or set())]

    @Property("QVariantList", notify=bulkChanged)
    def bulkStatusOptions(self):
        return self._common_bulk_choices("statusChoices")

    @Property("QVariantList", notify=bulkChanged)
    def bulkUserOptions(self):
        return self._common_bulk_choices("userChoices")

    @Property("QVariantList", notify=bulkChanged)
    def bulkPriorityOptions(self):
        return self._common_bulk_choices("priorityChoices")

    @Property("QVariantList", notify=bulkChanged)
    def bulkMilestoneOptions(self):
        return self._common_bulk_choices("milestoneChoices")

    @Property("QVariantList", notify=bulkChanged)
    def bulkSupervisorOptions(self):
        return self._common_bulk_choices("supervisorChoices")

    @Property(bool, notify=bulkChanged)
    def bulkBusy(self):
        return self._bulk_busy

    @Property(bool, notify=bulkChanged)
    def bulkCanApply(self):
        preview = self.bulkPreview
        return bool(
            self._bulk and not self._bulk_busy
            and not self._advanced_drafts
            and preview.get("eligible")
            and not preview.get("invalid")
        )

    @Property("QVariantMap", notify=bulkChanged)
    def bulkEditor(self):
        return dict(self._bulk)

    @Property("QVariantMap", notify=bulkChanged)
    def bulkPreview(self):
        return self._bulk_plan()[0]

    def _selection_changed(self):
        self._request_id = uuid.uuid4().hex
        self._full_target_key = self.targetSearchKey
        self._process_drafts.clear()
        self._processes = self._process_choices_for(
            self._workspace._selected_sobject
        )
        if self._mode:
            self.cancel()
        self._rebuild_process_model()
        if self._advanced_visible:
            if self._advanced_scope == "search_type":
                self.use_current_search_type()
            elif self._advanced_scope in {"object", "multiple"}:
                self.use_current_object()
        self.stateChanged.emit()
        self.editorChanged.emit()

    def _project_changed(self, *_args):
        self.task_store.clear()
        self._reset_advanced_interaction()
        self._history_loaded.clear()
        self.calendar_model.clear()
        self.gantt_model.clear()
        self._gantt = gantt_layout([])
        self.advancedChanged.emit()

    @staticmethod
    def _pipeline(target):
        if not target:
            return None, None
        try:
            stype = target.get_stype()
            pipelines = stype.get_pipeline() or {}
            return stype, pipelines.get(target.get_pipeline_code())
        except (AttributeError, KeyError, TypeError):
            return None, None

    @staticmethod
    def _process_task_configuration(pipeline, process):
        return process_task_configuration(pipeline, process)

    @staticmethod
    def _number(value, default=0.0):
        try:
            return float(str(value or "").strip())
        except (TypeError, ValueError):
            return float(default)

    def _process_task_defaults(self, target, process):
        _stype, pipeline = self._pipeline(target)
        values = self._process_task_configuration(pipeline, process)
        duration = max(0.0, self._number(values.get("duration")))
        planned_hours = max(
            0.0, self._number(values.get("bid_duration"))
        )
        completion = max(
            0, min(100, int(self._number(values.get("completion"))))
        )
        start = ""
        end = ""
        if duration > 0:
            start_value = datetime.now().replace(
                minute=0, second=0, microsecond=0
            )
            end_value = start_value + timedelta(days=duration)
            start = start_value.strftime("%Y-%m-%d %H:%M:%S")
            end = end_value.strftime("%Y-%m-%d %H:%M:%S")
        return {
            "start": start,
            "end": end,
            "progress": completion,
            "plannedHours": planned_hours,
            "remainingHours": planned_hours,
            "hoursLabel": format_hours_label(0.0, planned_hours),
            "status": str(values.get("status") or ""),
            "assigned": str(values.get("assigned") or ""),
            "supervisor": str(values.get("supervisor") or ""),
            "taskPipeline": str(values.get("task_pipeline") or ""),
        }

    def _native_process_task_defaults(self, target, process):
        """Map workflow defaults to native sthpw/task column names."""
        defaults = self._process_task_defaults(target, process)
        data = {
            "process": str(process or ""),
            "context": str(process or ""),
        }
        field_map = {
            "status": "status",
            "assigned": "assigned",
            "supervisor": "supervisor",
            "start": "bid_start_date",
            "end": "bid_end_date",
            "plannedHours": "bid_duration",
            "taskPipeline": "pipeline_code",
        }
        for source, target_name in field_map.items():
            value = defaults.get(source)
            if value not in (None, "", 0, 0.0):
                data[target_name] = value
        progress_column = self._progress_column()
        if progress_column and int(defaults.get("progress") or 0) > 0:
            data[progress_column] = int(defaults["progress"])
        return data
    def _process_choices_for(self, target):
        _stype, pipeline = self._pipeline(target)
        result = []
        for code in pipeline.pipeline if pipeline else ():
            info = pipeline.get_process_info(code) or {}
            configuration = self._process_task_configuration(pipeline, code)
            process_type = configuration.get("type") or info.get("type")
            if process_type in {
                "action", "condition", "dependency", "progress",
            }:
                continue
            process_object = pipeline.get_pipeline_process(code) or {}
            result.append({
                "label": str(info.get("label") or code),
                "value": str(code),
                "color": str(info.get("color") or process_object.get("color") or "#607d8b"),
                "type": str(process_type or ""),
                "taskPipeline": str(
                    configuration.get("task_pipeline") or ""
                ),
            })
        return result

    @staticmethod
    def _loaded_snapshots(parent, process):
        if not parent or not process:
            return []
        try:
            process_object = (parent.get_all_processes() or {}).get(process)
            contexts = process_object.get_contexts() if process_object else {}
        except (AttributeError, KeyError, TypeError):
            return []
        snapshots = []
        seen = set()
        for context in (contexts or {}).values():
            for getter in ("get_versions", "get_versionless"):
                try:
                    values = getattr(context, getter)() or {}
                except (AttributeError, KeyError, TypeError):
                    values = {}
                values = values.values() if isinstance(values, dict) else values
                for snapshot in values or []:
                    try:
                        code = str(snapshot.get_code() or "")
                    except AttributeError:
                        code = ""
                    token = code or id(snapshot)
                    if token not in seen:
                        snapshots.append(snapshot)
                        seen.add(token)
        return snapshots

    @staticmethod
    def _snapshot_preview_url(snapshot):
        try:
            grouped = snapshot.get_files_objects(group_by="type") or {}
        except (AttributeError, KeyError, TypeError):
            return ""
        for file_type in ("icon", "web", "image", "playblast", "main"):
            for file_object in grouped.get(file_type) or []:
                candidate = file_object
                try:
                    candidate = (
                        file_object.get_icon_preview()
                        or file_object.get_web_preview()
                        or file_object
                    )
                except (AttributeError, KeyError, TypeError):
                    pass
                try:
                    url = str(candidate.get_full_web_path() or "")
                except (AttributeError, KeyError, TypeError):
                    url = ""
                if url:
                    return url
        return ""

    @classmethod
    def _snapshot_summary_for(cls, parent, process):
        snapshots = cls._loaded_snapshots(parent, process)

        def version(snapshot):
            try:
                return int(snapshot.get_version())
            except (AttributeError, TypeError, ValueError):
                return -1

        versioned = [snapshot for snapshot in snapshots if version(snapshot) >= 0]
        latest = max(versioned, key=version, default=None)
        preview_url = ""
        for preview_process in ("icon", process, "publish"):
            candidates = cls._loaded_snapshots(parent, preview_process)
            candidates.sort(key=version, reverse=True)
            for snapshot in candidates:
                preview_url = cls._snapshot_preview_url(snapshot)
                if preview_url:
                    break
            if preview_url:
                break
        latest_version = ""
        file_count = 0
        if latest is not None:
            latest_version = "v{:03d}".format(max(0, version(latest)))
            try:
                files = latest.get_files_objects() or []
            except (AttributeError, KeyError, TypeError):
                files = []
            if isinstance(files, dict):
                files = [
                    file_object
                    for values in files.values()
                    for file_object in (values or [])
                ]
            seen_files = set()
            for file_object in files:
                try:
                    token = str(file_object.get_code() or "")
                except AttributeError:
                    token = ""
                seen_files.add(token or id(file_object))
            file_count = len(seen_files)
        return {
            "parentPreviewUrl": preview_url,
            "snapshotCount": len(versioned),
            "snapshotFileCount": file_count,
            "latestVersion": latest_version,
        }

    def _status_choices_for(self, target, process):
        stype, pipeline = self._pipeline(target)
        if not stype or not pipeline:
            return []
        try:
            info = self._process_task_configuration(pipeline, process)
            workflow = stype.get_workflow()
            pipeline_code = info.get("task_pipeline")
            task_pipeline = (
                workflow.get_by_pipeline_code("sthpw/task", pipeline_code)
                if pipeline_code else workflow.get_by_process_node_type(
                    "sthpw/task", info.get("type")
                )
            )
        except (AttributeError, KeyError, TypeError):
            task_pipeline = None
        result = []
        for value, status_info in task_pipeline.pipeline.items() if task_pipeline else ():
            result.append({
                "label": str(value),
                "value": str(value),
                "color": str((status_info or {}).get("color") or "#607d8b"),
                "available": True,
            })
        return result

    @staticmethod
    def _with_current_status(choices, status, fallback_color):
        values = [dict(item) for item in choices or []]
        status = str(status or "")
        if status and not any(
            str(item.get("value") or "") == status for item in values
        ):
            values.append({
                "label": "{} (unavailable)".format(status),
                "value": status,
                "color": str(fallback_color or "#607d8b"),
                "available": False,
            })
        return values

    def _user_choices_for(self, target, process, include_login=""):
        from thlib.environment import env_inst

        logins = None
        _stype, pipeline = self._pipeline(target)
        try:
            info = self._process_task_configuration(pipeline, process)
            group_code = info.get("assigned_login_group")
            if not group_code:
                group_code = info.get("assigned_group")
            current_login = env_inst.get_current_login_object()
            group = current_login.get_login_group(group_code) if (
                current_login and group_code
            ) else None
            logins = group.get_logins() if group else None
        except (AttributeError, KeyError, TypeError):
            logins = None
        if not logins:
            logins = list((env_inst.get_all_logins() or {}).values())
        result = [{"label": "Not assigned", "value": "", "avatarUrl": ""}]
        seen = set()
        for login_object in logins:
            try:
                value = str(login_object.get_login() or "")
                label = str(login_object.get_display_name() or value)
            except AttributeError:
                continue
            if value and value not in seen:
                result.append({
                    "label": label, "value": value,
                    "avatarUrl": self._login_avatar_url(login_object),
                })
                seen.add(value)
        include_login = str(include_login or "")
        if include_login and include_login not in seen:
            result.append({
                "label": self._login_label(include_login) or include_login,
                "value": include_login, "avatarUrl": "",
            })
        result[1:] = sorted(
            result[1:], key=lambda item: item["label"].casefold()
        )
        return result

    def _supervisor_choices_for(self, target, process, include_login=""):
        from thlib.environment import env_inst

        _stype, pipeline = self._pipeline(target)
        info = self._process_task_configuration(pipeline, process)
        group_code = str(info.get("supervisor_group") or "")
        logins = None
        try:
            current_login = env_inst.get_current_login_object()
            group = current_login.get_login_group(group_code) if (
                current_login and group_code
            ) else None
            logins = group.get_logins() if group else None
        except (AttributeError, KeyError, TypeError):
            logins = None
        if not logins:
            return self._all_user_choices(
                "No supervisor", include_login=include_login
            )
        result = [{
            "label": "No supervisor", "value": "", "avatarUrl": "",
        }]
        seen = set()
        for login_object in logins:
            try:
                value = str(login_object.get_login() or "")
                label = str(login_object.get_display_name() or value)
            except AttributeError:
                continue
            if value and value not in seen:
                result.append({
                    "label": label, "value": value,
                    "avatarUrl": self._login_avatar_url(login_object),
                })
                seen.add(value)
        include_login = str(include_login or "")
        if include_login and include_login not in seen:
            result.append({
                "label": self._login_label(include_login) or include_login,
                "value": include_login, "avatarUrl": "",
            })
        result[1:] = sorted(
            result[1:], key=lambda item: item["label"].casefold()
        )
        return result

    @staticmethod
    def _login_avatar_url(login_object):
        processes = getattr(login_object, "process", {}) or {}
        for process_name in ("icon", "publish"):
            process = processes.get(process_name)
            contexts = getattr(process, "contexts", {}) if process else {}
            for context in (contexts or {}).values():
                versionless = getattr(context, "versionless", {}) or {}
                versions = getattr(context, "versions", {}) or {}
                snapshots = list(versionless.values()) or list(versions.values())
                for snapshot in reversed(snapshots):
                    try:
                        grouped = snapshot.get_files_objects(
                            group_by="type"
                        ) or {}
                    except (AttributeError, KeyError, TypeError):
                        grouped = {}
                    for file_type in ("icon", "web", "preview", "main"):
                        for file_object in grouped.get(file_type) or []:
                            try:
                                candidate = (
                                    file_object.get_icon_preview()
                                    or file_object
                                )
                                url = str(
                                    candidate.get_full_web_path() or ""
                                )
                            except (AttributeError, KeyError, TypeError):
                                url = ""
                            if url:
                                return url
        return ""

    @staticmethod
    def _login_label(login):
        from thlib.environment import env_inst
        login = str(login or "")
        logins = env_inst.get_all_logins() or {}
        login_object = logins.get(login)
        if login_object is None:
            login_object = next((
                item for item in logins.values()
                if login in {
                    str(getattr(item, "get_login", lambda: "")() or ""),
                    str(getattr(item, "get_code", lambda: "")() or ""),
                }
            ), None)
        try:
            return str(login_object.get_display_name() or login)
        except AttributeError:
            return login

    def _all_user_choices(self, first_label="Not assigned", include_login=""):
        from thlib.environment import env_inst
        result = [{"label": first_label, "value": "", "avatarUrl": ""}]
        for login, user in sorted((env_inst.get_all_logins() or {}).items()):
            try:
                label = user.get_display_name() or user.get_login() or login
                value = user.get_login() or login
            except AttributeError:
                label = value = str(login)
            result.append({
                "label": str(label), "value": str(value),
                "avatarUrl": self._login_avatar_url(user),
            })
        include_login = str(include_login or "")
        if include_login and not any(
                str(item.get("value") or "") == include_login
                for item in result):
            result.append({
                "label": self._login_label(include_login) or include_login,
                "value": include_login, "avatarUrl": "",
            })
        return result

    def _status_choices(self, process):
        return self._status_choices_for(self._editor_target or self._workspace._selected_sobject, process)

    def _rebuild_process_model(self):
        target = self._workspace._selected_sobject
        tasks = list(self._workspace._task_sobjects or [])
        by_process = {}
        task_rows = {}
        for row, task in enumerate(tasks):
            info = dict(task.get_info() or {})
            by_process.setdefault(str(info.get("process") or ""), []).append(task)
            task_rows[str(info.get("code") or "")] = row
        current_login = self._current_login()
        records = []
        for choice in self._process_choices_for(target):
            process = choice["value"]
            process_tasks = by_process.get(process, [])
            preferred = self._preferred_task.get(process)
            current = next((
                task for task in process_tasks
                if str((task.get_info() or {}).get("code") or "") == preferred
            ), None)
            if not current:
                current = next((
                    task for task in process_tasks
                    if self.task_store.assignee_for_task_info(
                        task.get_info() or {}
                    ) == current_login
                ), None)
            current = current or (process_tasks[0] if process_tasks else None)
            info = dict(current.get_info() or {}) if current else {}
            defaults = (
                {} if current else self._process_task_defaults(target, process)
            )
            code = str(info.get("code") or "")
            statuses = self._with_current_status(
                self._status_choices_for(target, process),
                info.get("status"), choice["color"],
            )
            assigned = self.task_store.assignee_for_task_info(info)
            draft_key = "{}|{}".format(process, code or "new")
            draft = dict(self._process_drafts.get(draft_key) or {})
            effective_status = str(draft.get(
                "status", info.get("status") or defaults.get("status") or ""
            ))
            effective_assigned = str(draft.get(
                "assigned", assigned or defaults.get("assigned") or ""
            ))
            progress_input = str(draft.get(
                "progress", progress_value(info)
                if current else defaults.get("progress") or 0
            ))
            effective_start = str(draft.get(
                "start", info.get("bid_start_date")
                or defaults.get("start") or ""
            ))
            effective_end = str(draft.get(
                "end", info.get("bid_end_date")
                or defaults.get("end") or ""
            ))
            try:
                effective_progress = max(
                    0, min(100, int(float(progress_input.rstrip("%"))))
                )
            except (TypeError, ValueError):
                effective_progress = progress_value(info)
            status_color = next((
                item["color"] for item in statuses
                if item["value"] == effective_status
            ), choice["color"])
            users = self._user_choices_for(
                target, process, include_login=effective_assigned
            )
            assigned_label = next((
                item["label"] for item in users
                if item["value"] == effective_assigned
            ), effective_assigned or "Not assigned")
            notes = 0
            if current:
                notes = sum(int(value or 0) for value in (current.get_notes_count() or {}).values())
            records.append({
                "process": process,
                "label": choice["label"],
                "color": choice["color"],
                "taskCount": len(process_tasks),
                "hasTask": bool(current),
                "currentTaskCode": code,
                "currentTaskRow": task_rows.get(code, -1),
                "context": str(info.get("context") or ""),
                "status": effective_status,
                "statusColor": status_color,
                "assigned": effective_assigned,
                "assignedLabel": assigned_label,
                "start": effective_start,
                "end": effective_end,
                "dueState": due_state(effective_end),
                "progress": effective_progress,
                "progressInput": progress_input,
                "description": str(info.get("description") or ""),
                "notes": notes,
                "statusChoices": statuses,
                "userChoices": users,
                "taskChoices": [
                    {
                        "value": str((task.get_info() or {}).get("code") or ""),
                        "label": " / ".join(value for value in (
                            str((task.get_info() or {}).get("context") or "No context"),
                            self._login_label((task.get_info() or {}).get("assigned")) or "Not assigned",
                        ) if value),
                    }
                    for task in process_tasks
                ],
                "validationError": self._process_draft_error(info, draft),
                "expanded": False,
                "dirty": bool(draft),
            })
        self.process_model.replace(records)

    def _process_task(self, row):
        if not 0 <= row < len(self.process_model._records):
            return None
        code = str(
            self.process_model._records[row].get("currentTaskCode") or ""
        )
        return next((
            task for task in self._workspace._task_sobjects
            if str((task.get_info() or {}).get("code") or "") == code
        ), None)

    @Slot(str)
    def set_quick_view_mode(self, mode):
        mode = str(mode or "")
        if mode not in {"cards", "compact"} or mode == self._quick_view_mode:
            return
        self._quick_view_mode = mode
        self._store_workspace_preferences()
        self.stateChanged.emit()

    @Slot(int, str, "QVariant")
    def set_process_draft(self, row, field, value):
        if (
            field not in {"status", "assigned", "start", "end", "progress"}
            or not 0 <= row < len(self.process_model._records)
        ):
            return
        record = self.process_model._records[row]
        key = "{}|{}".format(
            record.get("process") or "",
            record.get("currentTaskCode") or "new",
        )
        draft = dict(self._process_drafts.get(key) or {})
        value = str(value or "")
        task = self._process_task(row)
        info = dict(task.get_info() or {}) if task else {}
        source_field = {
            "start": "bid_start_date",
            "end": "bid_end_date",
            "progress": self._progress_column() or "progress",
        }.get(field, field)
        original_value = info.get(source_field)
        if field == "assigned" and not original_value:
            original_value = info.get("login")
        if field == "progress":
            original_value = progress_value(info)
        original = str(original_value or "")
        if value == original:
            draft.pop(field, None)
        else:
            draft[field] = value
        if draft:
            self._process_drafts[key] = draft
        else:
            self._process_drafts.pop(key, None)
        self._rebuild_process_model()
        self.stateChanged.emit()

    def _process_draft_error(self, info, draft):
        start_value = str(draft.get(
            "start", info.get("bid_start_date") or ""
        ) or "").strip()
        end_value = str(draft.get(
            "end", info.get("bid_end_date") or ""
        ) or "").strip()
        parsed_start = parse_datetime(start_value) if start_value else None
        parsed_end = parse_datetime(end_value) if end_value else None
        if start_value and not parsed_start:
            return "Start must use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS."
        if end_value and not parsed_end:
            return "Deadline (end date) must use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS."
        if parsed_start and parsed_end and parsed_end < parsed_start:
            return "Deadline cannot be earlier than start."
        if "progress" in draft:
            try:
                progress = int(str(draft.get("progress") or "0").rstrip("%"))
            except (TypeError, ValueError):
                return "Progress must be a number from 0 to 100."
            if not 0 <= progress <= 100:
                return "Progress must be between 0 and 100."
        return ""

    def _prepared_process_draft(self, draft):
        prepared = {}
        for field, value in draft.items():
            if field == "start":
                prepared["bid_start_date"] = str(value or "")
            elif field == "end":
                prepared["bid_end_date"] = str(value or "")
            elif field == "progress":
                progress_column = self._progress_column()
                if not progress_column:
                    return {}, "Task progress is not available in this schema."
                prepared[progress_column] = int(str(value or "0").rstrip("%"))
            else:
                prepared[field] = value
        return prepared, ""

    @Slot(int)
    def discard_process_changes(self, row):
        if not 0 <= row < len(self.process_model._records):
            return
        record = self.process_model._records[row]
        self._process_drafts.pop("{}|{}".format(
            record.get("process") or "",
            record.get("currentTaskCode") or "new",
        ), None)
        self._rebuild_process_model()
        self.stateChanged.emit()

    @Slot()
    def discard_all_process_changes(self):
        if not self._process_drafts:
            return
        self._process_drafts.clear()
        self._rebuild_process_model()
        self.stateChanged.emit()

    @Slot(int, result=bool)
    def save_process_changes(self, row):
        if self._busy or not 0 <= row < len(self.process_model._records):
            return False
        record = dict(self.process_model._records[row])
        process = str(record.get("process") or "")
        code = str(record.get("currentTaskCode") or "")
        key = "{}|{}".format(process, code or "new")
        draft = dict(self._process_drafts.get(key) or {})
        if not draft:
            return False
        target = self._workspace._selected_sobject
        task = self._process_task(row)
        info = dict(task.get_info() or {}) if task else {}
        error = self._process_draft_error(info, draft)
        prepared, preparation_error = self._prepared_process_draft(draft)
        if error or preparation_error:
            self._set_error(error or preparation_error)
            return False

        def operation():
            if task is not None:
                for name, value in prepared.items():
                    task.set_value(name, value)
                return task.commit(triggers=True)
            import thlib.tactic_classes as tc
            data = self._native_process_task_defaults(target, process)
            data.update(prepared)
            return tc.insert_sobjects(
                "sthpw/task", target.get_project().get_code(), data,
                parent_key=target.get_search_key(), triggers=True,
            )

        self._run(
            "Saving task", operation, target, process, False,
            on_success=lambda: self._process_drafts.pop(key, None),
        )
        return True

    @Slot(int, str)
    def set_process_assignee(self, row, login):
        if not 0 <= row < len(self.process_model._records):
            return
        self.set_process_draft(row, "assigned", login)

    @Slot(result=bool)
    def save_all_process_changes(self):
        if self._busy or not self._process_drafts:
            return False
        target = self._workspace._selected_sobject
        if target is None:
            return False
        pending = dict(self._process_drafts)
        task_by_code = {
            str((task.get_info() or {}).get("code") or ""): task
            for task in self._workspace._task_sobjects
        }
        changes = []
        for key, source in pending.items():
            process, code = key.rsplit("|", 1)
            task = task_by_code.get(code) if code != "new" else None
            if code != "new" and task is None:
                self._set_error(
                    "A changed task is no longer available. Refresh tasks and retry."
                )
                return False
            info = dict(task.get_info() or {}) if task else {}
            error = self._process_draft_error(info, source)
            prepared, preparation_error = self._prepared_process_draft(source)
            if error or preparation_error:
                self._set_error(error or preparation_error)
                return False
            changes.append((task, process, prepared))

        def operation():
            import thlib.tactic_classes as tc
            results = []
            project_code = target.get_project().get_code()
            for task, process, draft in changes:
                if task is not None:
                    for name, value in draft.items():
                        task.set_value(name, value)
                    results.append(task.commit(triggers=True))
                    continue
                data = self._native_process_task_defaults(target, process)
                data.update(draft)
                results.append(tc.insert_sobjects(
                    "sthpw/task", project_code, data,
                    parent_key=target.get_search_key(), triggers=True,
                ))
            return results

        self._run(
            "Saving task changes", operation, target, "", False,
            on_success=lambda: self._clear_process_drafts(pending),
        )
        return True

    def _clear_process_drafts(self, drafts):
        for key in drafts:
            self._process_drafts.pop(key, None)

    @staticmethod
    def _current_login():
        from thlib.environment import env_server
        return str(env_server.get_user() or "")

    def _selected_search_type_scope(self):
        target = self._workspace._selected_sobject
        if target is None:
            return "", ""
        try:
            search_type = str(target.get_plain_search_type() or "")
        except AttributeError:
            try:
                search_type = str(target.get_search_key() or "")
                search_type = search_type.removeprefix("skey://").split("?", 1)[0]
            except AttributeError:
                search_type = ""
        try:
            stype = target.get_stype()
            title = str(stype.get_pretty_name() or stype.get_code() or "")
        except AttributeError:
            title = ""
        if not title and search_type:
            title = search_type.rsplit("/", 1)[-1].replace("_", " ").title()
        return search_type, title.strip()

    @staticmethod
    def _team_options():
        from thlib.environment import env_inst

        current_login = env_inst.get_current_login_object()
        try:
            getter = getattr(current_login, "get_all_login_groups", None)
            if not callable(getter):
                getter = getattr(current_login, "get_login_groups", None)
            groups = getter() or [] if callable(getter) else []
        except (AttributeError, TypeError):
            groups = []
        options = []
        for group in groups:
            try:
                code = str(group.get_code() or group.get_login_group() or "")
                label = str(group.get_pretty_name() or code)
                members = list(group.get_logins() or [])
            except (AttributeError, TypeError):
                continue
            if code:
                options.append({
                    "label": label,
                    "value": code,
                    "members": len(members),
                })
        return sorted(options, key=lambda item: item["label"].casefold())

    @Slot(bool)
    def set_compact_visible(self, value):
        self._compact_visible = bool(value)
        if self._compact_visible and self.hasTarget:
            key = self.targetSearchKey
            if key != self._full_target_key and not self._busy:
                self.refresh()

    @Slot(int, str)
    def select_process_task(self, row, task_code):
        if not 0 <= row < len(self.process_model._records):
            return
        process = str(self.process_model._records[row].get("process") or "")
        self._preferred_task[process] = str(task_code or "")
        self._rebuild_process_model()

    @Slot(int, str)
    def activate_process_task(self, row, task_code):
        if not 0 <= row < len(self.process_model._records):
            return
        task_code = str(task_code or "")
        record = self.process_model._records[row]
        if not any(
                str(choice.get("value") or "") == task_code
                for choice in record.get("taskChoices") or []):
            return
        process = str(record.get("process") or "")
        self.select_process_task(row, task_code)
        self.taskActivated.emit(task_code, self.targetSearchKey, process)

    def _process_row_for_task(self, task_code):
        task_code = str(task_code or "")
        return next((
            row for row, record in enumerate(self.process_model._records)
            if str(record.get("currentTaskCode") or "") == task_code
        ), -1)

    @Slot(str, str)
    def select_process_task_code(self, process, task_code):
        process = str(process or "")
        task_code = str(task_code or "")
        row = next((
            index for index, record in enumerate(self.process_model._records)
            if str(record.get("process") or "") == process
        ), -1)
        if (
            row >= 0
            and str(
                self.process_model._records[row].get("currentTaskCode") or ""
            ) != task_code
        ):
            self.select_process_task(row, task_code)

    @Slot(str, result="QVariantMap")
    def task_inspector_record(self, task_code):
        row = self._process_row_for_task(task_code)
        if row < 0:
            return {}
        record = dict(self.process_model._records[row])
        record["processRow"] = row
        return record

    @Slot(str, str, "QVariant")
    def set_inspector_task_value(self, task_code, field, value):
        row = self._process_row_for_task(task_code)
        if row >= 0:
            self.set_process_draft(row, field, value)

    @Slot(str, result=bool)
    def save_inspector_task(self, task_code):
        row = self._process_row_for_task(task_code)
        return row >= 0 and self.save_process_changes(row)

    @Slot(str)
    def discard_inspector_task(self, task_code):
        row = self._process_row_for_task(task_code)
        if row >= 0:
            self.discard_process_changes(row)

    @Slot(int)
    def begin_create_for_process(self, row):
        if not 0 <= row < len(self.process_model._records):
            return
        self._open_task_schema_editor(row, "insert")

    @Slot(int)
    def begin_edit_for_process(self, row):
        if self._process_task(row) is not None:
            self._open_task_schema_editor(row, "edit")

    @Slot(int)
    def remove_process_task(self, row):
        if self._busy:
            return
        task = self._process_task(row)
        if task is None:
            return
        info = dict(task.get_info() or {})
        process = str(info.get("process") or "")
        self._run(
            "Deleting task",
            lambda: task.delete_sobject(include_dependencies=True),
            self._workspace._selected_sobject, process, False,
        )

    def _open_task_schema_editor(self, row, mode):
        if not 0 <= row < len(self.process_model._records):
            return
        target = self._workspace._selected_sobject
        process = str(
            self.process_model._records[row].get("process") or ""
        )
        task = None
        if mode == "edit":
            task = self._process_task(row)
            if task is None:
                return
        self._open_task_sobject_editor(target, process, task)

    def _open_task_sobject_editor(self, target, process, task=None):
        if target is None and task is None:
            action = "editing" if task is not None else "creating"
            self._set_error(f"Select an sObject before {action} a task.")
            return
        if not process:
            self._set_error("The selected sObject has no task processes.")
            return
        from thlib.environment import env_inst
        task_stype = env_inst.get_stype_by_code("sthpw/task")
        if task_stype is None:
            self._set_error("The task schema is unavailable.")
            return
        request = {
            "mode": "edit" if task is not None else "insert",
            "stype": task_stype,
            "parent_sobject": target,
            "info_dict": (
                {"process": process} if task is not None
                else self._native_process_task_defaults(target, process)
            ),
            "refresh": lambda: self._task_editor_saved(target),
            "_prepared": True,
        }
        if task is not None:
            request["sobject"] = task
        self._application._sobject_editor_request = request
        self._application.open_window("task_editor")

    def _task_editor_saved(self, target):
        selected = self._workspace._selected_sobject
        if target is not None and selected is not None:
            try:
                if target.get_search_key() == selected.get_search_key():
                    self.refresh()
                    return
            except (AttributeError, KeyError, TypeError):
                pass
        if self._advanced_visible:
            self.refresh_advanced()

    @staticmethod
    def _target_value(target, method, fallback=""):
        try:
            return str(getattr(target, method)() or fallback or "")
        except (AttributeError, TypeError):
            return str(fallback or "")

    def _new_advanced_task_record(self, code, target, process_choices):
        parent_key = self._target_value(target, "get_search_key")
        parent_code = self._target_value(target, "get_code")
        parent_title = self._target_value(
            target, "get_title", parent_code or "sObject"
        )
        parent_search_type = self._target_value(
            target, "get_plain_search_type"
        )
        if not parent_search_type:
            try:
                parent_search_type = str(target.get_stype().get_code() or "")
            except AttributeError:
                parent_search_type = ""
        project_code = str(self._application._current_project_code or "")
        try:
            project_code = str(target.get_project().get_code() or project_code)
        except AttributeError:
            pass
        preferred_process = str(
            getattr(self._application, "_selected_detail_process", "") or ""
        )
        process_choice = next((
            item for item in process_choices
            if str(item.get("value") or "") == preferred_process
        ), process_choices[0])
        process = str(process_choice.get("value") or "")
        defaults = self._process_task_defaults(target, process)
        statuses = self._status_choices_for(target, process)
        default_status = str(defaults.get("status") or "")
        default_status_color = next((
            str(item.get("color") or "") for item in statuses
            if str(item.get("value") or "") == default_status
        ), str(process_choice.get("color") or "#607d8b"))
        assigned = str(defaults.get("assigned") or "")
        supervisor = str(defaults.get("supervisor") or "")
        users = self._user_choices_for(
            target, process, include_login=assigned
        )
        project_catalog = dict(
            self._task_field_catalogs.get(project_code) or {}
        )
        priority_choices = list(project_catalog.get("priorityChoices") or [])
        milestone_choices = list(
            project_catalog.get("milestoneChoices") or []
        )
        supervisor_choices = self._supervisor_choices_for(
            target, process, include_login=supervisor
        )
        assigned_choice = next((
            (index, item) for index, item in enumerate(users)
            if str(item.get("value") or "") == assigned
        ), (0 if users else -1, {}))
        supervisor_choice = next((
            item for item in supervisor_choices
            if str(item.get("value") or "") == supervisor
        ), {})
        record = {role: "" for role in TASK_ROLES}
        record.update({
            "taskCode": code,
            "parentKey": parent_key,
            "parentTitle": parent_title,
            "parentSearchType": parent_search_type,
            "parentCode": parent_code,
            "project": project_code,
            "process": process,
            "processLabel": str(process_choice.get("label") or process),
            "processColor": str(
                process_choice.get("color") or "#607d8b"
            ),
            "processType": str(process_choice.get("type") or ""),
            "taskPipeline": str(
                defaults.get("taskPipeline")
                or process_choice.get("taskPipeline") or ""
            ),
            "processChoices": [dict(item) for item in process_choices],
            "isNew": True,
            "context": process,
            "statusChoices": statuses,
            "userChoices": users,
            "assigned": assigned,
            "assignedLabel": str(
                assigned_choice[1].get("label") or "Not assigned"
            ),
            "assignedAvatar": str(
                assigned_choice[1].get("avatarUrl") or ""
            ),
            "assignedChoiceIndex": assigned_choice[0],
            "supervisorChoices": supervisor_choices,
            "supervisor": supervisor,
            "supervisorLabel": str(
                supervisor_choice.get("label") or "No supervisor"
            ),
            "priorityChoices": priority_choices,
            "priorityLabel": "No priority",
            "milestoneChoices": milestone_choices,
            "milestoneLabel": "No milestone",
            "status": default_status,
            "statusColor": default_status_color,
            "start": str(defaults.get("start") or ""),
            "end": str(defaults.get("end") or ""),
            "dueState": due_state(defaults.get("end")),
            "progress": int(defaults.get("progress") or 0),
            "plannedHours": float(defaults.get("plannedHours") or 0.0),
            "loggedHours": 0.0,
            "approvedHours": 0.0,
            "pendingHours": 0.0,
            "remainingHours": float(
                defaults.get("remainingHours") or 0.0
            ),
            "overPlanHours": 0.0,
            "hoursLabel": str(
                defaults.get("hoursLabel") or "0.0 / 0.0 h"
            ),
            "notes": 0,
            "snapshotCount": 0,
            "snapshotFileCount": 0,
            "attachmentCount": 0,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "groupCount": 0,
            "groupFirst": False,
            "groupCollapsed": False,
            "selected": True,
            "checked": False,
            "dirty": True,
            "loading": False,
            "conflict": False,
        })
        record.update(self._snapshot_summary_for(target, process))
        return record

    def _advanced_group_key_for_record(self, record):
        key_by_mode = {
            "status": str(record.get("status") or "__none__"),
            "user": str(record.get("assigned") or "__unassigned__"),
            "object": str(
                record.get("parentKey") or record.get("parentCode") or ""
            ),
            "project": str(record.get("project") or "__none__"),
            "search_type": str(
                record.get("parentSearchType") or "__none__"
            ),
            "process": str(record.get("process") or "__none__"),
        }
        return key_by_mode.get(self._group_mode, "")

    @Slot(result=bool)
    def create_advanced_task_draft(self):
        if self._advanced_busy or self._advanced_saving:
            return False
        target = self._advanced_creation_target()
        process_choices = self._process_choices_for(target)
        if target is None or not process_choices:
            self._advanced_error = (
                "Select an sObject with an available task process first."
            )
            self.advancedChanged.emit()
            return False
        code = "__new_task__{}".format(uuid.uuid4().hex)
        record = self._new_advanced_task_record(
            code, target, process_choices
        )
        self._advanced_inserts[code] = target
        self._advanced_drafts[code] = {"__create__": True}
        self._advanced_raw.insert(0, record)
        group_key = self._advanced_group_key_for_record(record)
        if group_key:
            self._collapsed_groups.discard(
                "{}\x1f{}".format(self._group_mode, group_key)
            )
        self._selected_advanced_code = code
        self._advanced_error = ""
        self._rebuild_advanced_models()
        self.taskDraftCreated.emit(code)
        return True

    @Slot()
    def begin_create(self):
        target = self._workspace._selected_sobject
        processes = self._processes or self._process_choices_for(target)
        process = str(processes[0]["value"]) if processes else ""
        self._begin_create(target, process)

    def _begin_create(self, target, process):
        self._open_task_sobject_editor(target, process)

    @Slot(int)
    def begin_edit(self, row):
        if not 0 <= row < len(self._workspace._task_sobjects):
            return
        self._begin_edit_task(
            self._workspace._task_sobjects[row],
            self._workspace._selected_sobject,
            row,
        )

    @Slot(str)
    def begin_edit_code(self, task_code):
        task_code = str(task_code or "")
        task = self._advanced_tasks.get(task_code)
        target = self.task_store.parent_for_task(task) if task else None
        if task is None:
            task = next((
                item for item in self._workspace._task_sobjects
                if str((item.get_info() or {}).get("code") or "") == task_code
            ), None)
            target = self._workspace._selected_sobject if task else None
        if task:
            self._begin_edit_task(task, target, -1)

    def _begin_edit_task(self, task, target, row):
        info = dict(task.get_info() or {})
        process = str(info.get("process") or "")
        self._open_task_sobject_editor(target, process, task)

    @Slot(str, "QVariant")
    def set_value(self, key, value):
        if key not in {
            "process", "context", "status", "assigned", "start", "end",
            "progress", "description",
        }:
            return
        self._editor[key] = value
        if key == "process":
            process = str(value or "")
            self._statuses = self._status_choices_for(self._editor_target, process)
            self._users = self._user_choices_for(self._editor_target, process)
            available = {item["value"] for item in self._statuses}
            if self._editor.get("status") not in available:
                self._editor["status"] = self._statuses[0]["value"] if self._statuses else ""
        self.editorChanged.emit()

    @Slot()
    def cancel(self):
        self._mode = ""
        self._row = -1
        self._editor = {}
        self._editor_task = None
        self._editor_target = None
        self._error = ""
        self.editorChanged.emit()
        self.stateChanged.emit()

    @staticmethod
    def _date(value):
        value = str(value or "").strip()
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

    def _validation_error(self):
        process = str(self._editor.get("process") or "")
        if not process:
            return "Process is required."
        try:
            progress = int(self._editor.get("progress") or 0)
        except (TypeError, ValueError):
            return "Progress must be a number from 0 to 100."
        if not 0 <= progress <= 100:
            return "Progress must be between 0 and 100."
        start_value = str(self._editor.get("start") or "").strip()
        end_value = str(self._editor.get("end") or "").strip()
        start = self._date(start_value)
        end = self._date(end_value)
        if start_value and not start:
            return "Start must use YYYY-MM-DD HH:MM:SS."
        if end_value and not end:
            return "End must use YYYY-MM-DD HH:MM:SS."
        if start and end and end < start:
            return "End cannot be earlier than start."
        return ""

    def _task_data(self):
        data = {
            "process": str(self._editor.get("process") or ""),
            "context": str(self._editor.get("context") or ""),
            "status": str(self._editor.get("status") or ""),
            "assigned": str(self._editor.get("assigned") or ""),
            "bid_start_date": str(self._editor.get("start") or ""),
            "bid_end_date": str(self._editor.get("end") or ""),
            "description": str(self._editor.get("description") or ""),
        }
        progress_column = self._progress_column()
        if progress_column:
            data[progress_column] = int(self._editor.get("progress") or 0)
        return data

    @staticmethod
    def _progress_column():
        from thlib.environment import env_inst
        try:
            stype = env_inst.get_stype_by_code("sthpw/task")
            columns = stype.get_columns_info() or {}
        except (AttributeError, KeyError, TypeError):
            return ""
        if "progress" in columns:
            return "progress"
        if "completion" in columns:
            return "completion"
        return ""

    @Slot(result=bool)
    def save(self):
        if self._busy:
            return False
        error = self._validation_error()
        if error:
            self._set_error(error)
            return False
        target = self._editor_target
        if not target:
            self._set_error("The target sObject is no longer available.")
            return False
        data = self._task_data()
        mode = self._mode
        task = self._editor_task
        if mode == "edit" and task is None:
            self._set_error("The task is no longer available.")
            return False

        def operation():
            if mode == "edit":
                for key, value in data.items():
                    task.set_value(key, value)
                return task.commit(triggers=True)
            import thlib.tactic_classes as tc
            return tc.insert_sobjects(
                "sthpw/task", target.get_project().get_code(), data,
                parent_key=target.get_search_key(), triggers=True,
            )

        self._run("Saving task", operation, target, data["process"], True)
        return True

    @Slot(int)
    def remove(self, row):
        if self._busy or not 0 <= row < len(self._workspace._task_sobjects):
            return
        task = self._workspace._task_sobjects[row]
        info = dict(task.get_info() or {})
        self._run(
            "Deleting task",
            lambda: task.delete_sobject(include_dependencies=True),
            self._workspace._selected_sobject,
            str(info.get("process") or ""),
            True,
        )

    @Slot(str)
    def remove_code(self, task_code):
        task = self._advanced_tasks.get(str(task_code or ""))
        if self._busy or not task:
            return
        info = dict(task.get_info() or {})
        target = self.task_store.parent_for_task_info(info)
        self._run(
            "Deleting task", lambda: task.delete_sobject(include_dependencies=True),
            target, str(info.get("process") or ""), True,
        )

    @Slot()
    def remove_current(self):
        if self._editor_task:
            code = str((self._editor_task.get_info() or {}).get("code") or "")
            if code in self._advanced_tasks:
                self.remove_code(code)
                return
        self.remove(self._row)

    @Slot(int, str)
    def set_status(self, row, status):
        if not 0 <= row < len(self._workspace._task_sobjects):
            return
        self._set_task_status(
            self._workspace._task_sobjects[row], status,
            self._workspace._selected_sobject,
        )

    @Slot(str, str)
    def set_status_code(self, task_code, status):
        task = self._advanced_tasks.get(str(task_code or ""))
        if not task:
            return
        target = self.task_store.parent_for_task(task)
        self._set_task_status(task, status, target)

    def _set_task_status(self, task, status, target):
        if self._busy or not task:
            return
        process = str((task.get_info() or {}).get("process") or "")
        def operation():
            task.set_value("status", str(status or ""))
            return task.commit(triggers=True)
        self._run("Updating task status", operation, target, process, False)

    @Slot(int, str)
    def set_process_status(self, row, status):
        if not 0 <= row < len(self.process_model._records):
            return
        self.set_process_draft(row, "status", status)

    @Slot()
    def refresh(self):
        target = self._workspace._selected_sobject
        if self._busy or not target:
            return
        self._busy = True
        self._error = ""
        request_id = uuid.uuid4().hex
        self._request_id = request_id
        target_key = str(target.get_search_key() or "")
        self.stateChanged.emit()
        self._query_target_tasks(target, request_id, target_key, False)

    def _query_target_tasks(self, target, request_id, target_key, close_after):
        from thlib.environment import env_inst
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(
            target.get_tasks_sobjects, include_status_log=False
        )
        if worker is None:
            self._operation_failed("Server worker pool is unavailable")
            return
        self._worker = worker
        worker.result.connect(
            lambda result: self._tasks_reloaded(
                request_id, target_key, result, close_after
            ),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            self._operation_failed, Qt.ConnectionType.QueuedConnection
        )
        worker.start()

    def _run(
        self, title, callback, target, process, close_after,
        on_success=None,
    ):
        from thlib.environment import env_inst
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        self._busy = True
        self._error = ""
        request_id = uuid.uuid4().hex
        self._request_id = request_id
        self.stateChanged.emit()
        worker = env_inst.server_pool.add_task(callback)
        if worker is None:
            self._operation_failed("Server worker pool is unavailable")
            return
        self._worker = worker
        worker.result.connect(
            lambda _result: self._operation_finished_with_callback(
                request_id, target, process, close_after, on_success
            ),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            self._operation_failed, Qt.ConnectionType.QueuedConnection
        )
        worker.start()

    def _operation_finished_with_callback(
        self, request_id, target, process, close_after, on_success,
    ):
        if request_id != self._request_id:
            return
        if on_success:
            on_success()
        self._operation_finished(request_id, target, process, close_after)

    def _operation_finished(self, request_id, target, _process, close_after):
        if request_id != self._request_id:
            return
        if close_after:
            self._mode = ""
            self._row = -1
            self._editor = {}
            self._editor_task = None
            self._editor_target = None
            self.editorChanged.emit()
        if not target:
            self._finish_busy()
            self.refresh_advanced()
            return
        target_key = str(target.get_search_key() or "")
        self._query_target_tasks(target, request_id, target_key, close_after)

    def _tasks_reloaded(self, request_id, target_key, result, _close_after):
        if request_id != self._request_id:
            return
        values = result[0] if isinstance(result, tuple) else result
        tasks = list((values or {}).values()) if isinstance(values, dict) else list(values or [])
        if target_key == self.targetSearchKey:
            self._workspace.replace_tasks(tasks)
            self._full_target_key = target_key
            self._processes = self._process_choices_for(
                self._workspace._selected_sobject
            )
            self._rebuild_process_model()
            self.editorChanged.emit()
        self._finish_busy()
        if self._advanced_visible:
            self.refresh_advanced()

    def _operation_failed(self, error):
        payload = error[0] if isinstance(error, tuple) and error else error
        stacktrace = ""
        if isinstance(payload, dict):
            stacktrace = str(payload.get("stacktrace") or "")
            payload = payload.get("exception") or payload.get("message") or payload
        self._error = str(payload or "Task operation failed")
        if self._application.debug_log:
            self._application.debug_log.raise_error(
                payload, stacktrace=stacktrace, group="tasks"
            )
        self._finish_busy()

    def _finish_busy(self):
        self._busy = False
        self._worker = None
        self.stateChanged.emit()

    def _set_error(self, value):
        self._error = str(value or "")
        self.stateChanged.emit()

    @Slot()
    def open_workspace(self):
        self._show_workspace_surface("browser")
        if not self._advanced_raw and not self._advanced_busy:
            self.use_current_object()

    @Slot()
    def open_quick_workspace(self):
        self._show_workspace_surface("quick")

    def _show_workspace_surface(self, surface):
        surface = str(surface or "quick")
        if surface not in {"quick", "browser"}:
            return
        if surface != self._workspace_surface:
            self._workspace_surface = surface
            self._store_workspace_preferences()
            self.stateChanged.emit()
        self._application.dock_model.show_panel("tasks")

    @Slot()
    def open_calendar(self):
        if not self._advanced_raw and not self._advanced_busy:
            self.use_current_object()
        self._application.dock_model.show_panel("task_calendar")

    def _reset_advanced_interaction(self):
        self._advanced_checked.clear()
        self._advanced_selection_anchor = ""
        self._advanced_drafts.clear()
        self._advanced_inserts.clear()
        self._advanced_row_errors.clear()
        self._advanced_conflicts.clear()
        self._selected_advanced_code = ""
        self._bulk = {}
        self.bulkChanged.emit()

    def _scope_will_change(self, scope, user="", target_key="", targets=None):
        target_tokens = []
        for target in targets or []:
            try:
                target_tokens.append(str(target.get_search_key() or ""))
            except AttributeError:
                target_tokens.append("")
        current_tokens = []
        for target in self._multiple_targets:
            try:
                current_tokens.append(str(target.get_search_key() or ""))
            except AttributeError:
                current_tokens.append("")
        current_key = self._advanced_target_key
        return (
            self._advanced_scope != scope
            or self._advanced_user != str(user or "")
            or (target_key and current_key != str(target_key))
            or target_tokens != current_tokens
        )

    @Slot(bool)
    def set_advanced_visible(self, value):
        value = bool(value)
        changed = self._advanced_visible != value
        self._advanced_visible = value
        if changed:
            self.advancedVisibilityChanged.emit(value)
        if not self._advanced_visible:
            self._live_timer.stop()
            self._live_task_codes.clear()
            self._live_request_id = uuid.uuid4().hex
            for worker in (self._live_worker, self._advanced_worker):
                cancel = getattr(worker, "cancel", None)
                if callable(cancel):
                    cancel()
            self._live_worker = None
            self._advanced_worker = None
            self.task_store.invalidate_requests()
            return
        if self._advanced_visible and not self._advanced_busy:
            if self._milestone_controller is not None:
                self._milestone_controller.ensure_loaded()
            if self._advanced_scope == "search_type":
                self.use_current_search_type()
            elif self._advanced_scope in {"object", "multiple"}:
                self.use_current_object()

    def _selected_workspace_targets(self):
        current_tab = getattr(self._application, "_current_tab", None)
        workspace_model = getattr(self._application, "workspace_model", None)
        if not callable(current_tab) or workspace_model is None:
            return []
        tab = current_tab()
        targets = []
        seen = set()
        for node_id in list(tab.selected_node_ids if tab else []):
            node = workspace_model.node_for(node_id)
            while node and node.node_type != "sobject" and node.parent_id:
                node = workspace_model.node_for(node.parent_id)
            target = node.source if node and node.node_type == "sobject" else None
            try:
                key = str(target.get_search_key() or "")
            except AttributeError:
                key = ""
            if key and key not in seen:
                targets.append(target)
                seen.add(key)
        return targets

    def _selected_object_process(self, target_key):
        current_tab = getattr(self._application, "_current_tab", None)
        workspace_model = getattr(self._application, "workspace_model", None)
        if not callable(current_tab) or workspace_model is None:
            return ""
        tab = current_tab()
        node = (
            workspace_model.node_for(tab.selected_node_id)
            if tab and tab.selected_node_id else None
        )
        if node is None or node.node_type != "process":
            return ""
        root = node
        while root and root.node_type != "sobject" and root.parent_id:
            root = workspace_model.node_for(root.parent_id)
        if root is None or str(root.search_key or "") != str(target_key or ""):
            return ""
        return str(node.process or node.context or "")

    def _sync_current_object_scope(self):
        target = self._workspace._selected_sobject
        if not target:
            if self._advanced_drafts:
                self._advanced_error = (
                    "Save or discard task changes before clearing the selection."
                )
                self.advancedChanged.emit()
                return
            self._reset_advanced_interaction()
            self._advanced_object_process = ""
            self.task_store.set_scope("object")
            self.task_store.clear()
            self._advanced_error = ""
            self._rebuild_advanced_models()
            return
        target_key = str(target.get_search_key() or "")
        process = self._selected_object_process(target_key)
        source_tasks = list(self._workspace._task_sobjects or [])
        if process:
            source_tasks = [
                task for task in source_tasks
                if str((task.get_info() or {}).get("process") or "") == process
            ]
        source_changed = (
            self._advanced_scope != "object"
            or self._advanced_target_key != target_key
            or self._advanced_object_process != process
        )
        if source_changed and self._advanced_drafts:
            self._advanced_error = (
                "Save or discard task changes before changing the selected object."
            )
            self.advancedChanged.emit()
            return
        if source_changed:
            self._reset_advanced_interaction()
        self._advanced_object_process = process
        self.task_store.set_scope(
            "object", target=target,
            target_key=target_key,
            target_title=str(target.get_title() or target.get_code() or "sObject"),
        )
        self.task_store.apply_source(
            source_tasks, [target],
            page={
                "loaded": len(source_tasks), "hasMore": False,
                "total": len(source_tasks),
            },
        )
        self._advanced_raw = self._task_records(source_tasks)
        if self._advanced_checked:
            self._sync_bulk_selection(preserve=True)
        self._rebuild_advanced_models()
        project_code = str(self._application._current_project_code or "")
        if (
                self._advanced_visible
                and project_code
                and not self._task_field_catalog_ready(project_code)):
            self._ensure_task_field_catalog(project_code)

    @Slot()
    def use_current_object(self):
        targets = self._selected_workspace_targets()
        if len(targets) > 1:
            self._use_multiple_targets(targets)
            return
        self._sync_current_object_scope()

    def _use_multiple_targets(self, targets):
        targets = list(targets or [])
        if len(targets) < 2:
            self._sync_current_object_scope()
            return
        if self._scope_will_change("multiple", targets=targets):
            if self._advanced_drafts:
                self._advanced_error = (
                    "Save or discard task changes before changing the "
                    "selected objects."
                )
                self.advancedChanged.emit()
                return
            self._reset_advanced_interaction()
        self.task_store.set_scope("multiple", targets=targets)
        self.refresh_advanced()

    @Slot(str)
    def use_object(self, search_key):
        search_key = str(search_key or "").strip()
        if not search_key:
            return
        if self._scope_will_change("object", target_key=search_key):
            self._reset_advanced_interaction()
        self.task_store.set_scope(
            "object", target_key=search_key, target_title=search_key,
        )
        self.refresh_advanced()

    @Slot(str)
    def open_for_user(self, login):
        self._open_user_scope(login, show_window=True)

    def prepare_user_scope(self, login):
        return self._open_user_scope(login, show_window=False)

    def _open_user_scope(self, login, show_window):
        login = str(login or self._current_login())
        if not login:
            return False
        scope_changed = self._scope_will_change("user", user=login)
        if scope_changed and self._advanced_drafts:
            self._advanced_error = (
                "Save or discard task changes before changing the task scope."
            )
            self.advancedChanged.emit()
            return False
        if scope_changed:
            self._reset_advanced_interaction()
            self.task_store.set_scope("user", user=login)
            self.task_store.apply_source(
                [], [], page={"loaded": 0, "hasMore": False, "total": 0},
            )
            self._advanced_raw = []
            self._rebuild_advanced_models()
        if show_window:
            self._show_workspace_surface("browser")
        if scope_changed or (
                not self._advanced_raw and not self._advanced_busy):
            self.refresh_advanced()
        return True

    @Slot(str)
    def open_for_team(self, group_code):
        group_code = str(group_code or "")
        available = {
            option["value"] for option in self._team_options()
        }
        if not group_code or group_code not in available:
            self._advanced_error = (
                "This team is not available through your TACTIC login groups."
            )
            self.advancedChanged.emit()
            return
        if self._scope_will_change("team", user=group_code):
            self._reset_advanced_interaction()
        self.task_store.set_scope("team", user=group_code)
        self._show_workspace_surface("browser")
        self.refresh_advanced()

    @Slot()
    def use_current_search_type(self):
        search_type, name = self._selected_search_type_scope()
        if not search_type:
            self._advanced_error = (
                "Select an sObject to view tasks for its search type."
            )
            self.advancedChanged.emit()
            return
        if self._scope_will_change("search_type", target_key=search_type):
            if self._advanced_drafts:
                self._advanced_error = (
                    "Save or discard task changes before changing the task scope."
                )
                self.advancedChanged.emit()
                return
            self._reset_advanced_interaction()
        self.task_store.set_scope(
            "search_type", target_key=search_type,
            target_title=("All {}".format(name) if name else "Search Type"),
        )
        self.refresh_advanced()

    @Slot()
    def use_project(self):
        if self._scope_will_change("project"):
            self._reset_advanced_interaction()
        self.task_store.set_scope("project")
        self.refresh_advanced()

    @Slot()
    def use_selected_objects(self):
        self.use_current_object()

    @Slot()
    def refresh_advanced(self):
        if self._advanced_drafts:
            self._advanced_error = "Save or discard task changes before refreshing."
            self.advancedChanged.emit()
            return
        self._start_advanced_load(False)

    @Slot()
    def load_more_advanced(self):
        if self.task_store.has_more:
            self._start_advanced_load(True)

    @Slot()
    def cancel_advanced_load(self):
        if not self._advanced_busy:
            return
        worker = self._advanced_worker
        if worker is not None:
            cancel = getattr(worker, "cancel", None)
            if callable(cancel):
                cancel()
        self.task_store.invalidate_requests()
        self.advancedChanged.emit()

    def _start_advanced_load(self, append):
        if self._advanced_busy:
            return
        project_code = str(self._application._current_project_code or "")
        if not project_code:
            return
        request_id = self.task_store.begin_load(append)
        if not request_id:
            return
        offset = self.task_store.offset if append else 0
        self.advancedChanged.emit()
        from thlib.environment import env_inst
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(
            self._load_advanced_scope,
            self._advanced_scope,
            self._advanced_user,
            project_code,
            self._advanced_target,
            self._advanced_target_key,
            list(self._multiple_targets),
            offset,
            self.task_store.page_size,
            not self._task_field_catalog_ready(project_code),
        )
        if worker is None:
            self._advanced_failed(request_id, "Server worker pool is unavailable")
            return
        self._advanced_worker = worker
        worker.result.connect(
            lambda result: self._advanced_loaded(request_id, result, append),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._advanced_failed(request_id, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    def _task_field_catalog_ready(self, project_code):
        """Only cache a priority catalog that contains a real choice.

        A failed or prematurely resolved edit-widget request still contains the
        empty `No priority` option.  Treating that fallback as a complete
        project catalog made the editor stay empty for the controller lifetime.
        """
        catalog = dict(
            self._task_field_catalogs.get(str(project_code or "")) or {}
        )
        return any(
            str(item.get("value") or "")
            for item in catalog.get("priorityChoices") or []
            if isinstance(item, dict)
        )

    @staticmethod
    def _objects(result):
        values = result[0] if isinstance(result, tuple) else result
        if isinstance(values, dict):
            return list(values.values())
        return list(values or [])

    @classmethod
    def _load_advanced_scope(
            cls, scope, login, project_code, target, target_key, targets,
            offset=0, limit=500, include_field_catalog=False):
        result = TaskWorkspaceStore.load_scope(
            scope, login, project_code, target, target_key, targets,
            offset=offset, limit=limit,
        )
        if include_field_catalog:
            result["fieldCatalog"] = load_task_field_catalog(
                project_code, target_key, include_milestones=False
            )
        return result

    def _advanced_loaded(self, request_id, result, append=False):
        if request_id != self._advanced_request_id:
            return
        values = result[0] if isinstance(result, tuple) else result
        values = dict(values or {})
        project_code = str(self._application._current_project_code or "")
        if "fieldCatalog" in values and project_code:
            self._task_field_catalogs[project_code] = dict(
                values.get("fieldCatalog") or {}
            )
            errors = list(
                self._task_field_catalogs[project_code].get("errors") or []
            )
            if errors and self._application.debug_log:
                self._application.debug_log.log(
                    "WARNING", "; ".join(str(item) for item in errors),
                    group="tasks/field-catalog", source="Tasks",
                    stacktrace="\n".join(
                        str(item) for item in self._task_field_catalogs[
                            project_code
                        ].get("tracebacks") or []
                    ),
                )
        tasks = list(values.get("tasks") or [])
        parents = list(values.get("parents") or [])
        target = values.get("target")
        if target:
            self._advanced_target = target
            self._advanced_target_key = str(target.get_search_key() or "")
            self._advanced_target_title = str(target.get_title() or target.get_code() or "sObject")
        self.task_store.apply_source(
            tasks, parents, page=values.get("page"), append=append,
        )
        self._increment_performance_metric(
            "serverQueries",
            int(dict(values.get("page") or {}).get("queryCount") or 0),
        )
        self._advanced_raw = self._task_records(
            self.task_store.task_objects()
        )
        self.task_store.finish_load()
        if self._advanced_checked:
            self._sync_bulk_selection(preserve=True)
        self._rebuild_advanced_models()
        self.bulkChanged.emit()
        if (
                project_code
                and "fieldCatalog" in values
                and not self._task_field_catalog_ready(project_code)):
            self._task_field_catalog_attempts[project_code] = max(
                1, self._task_field_catalog_attempts.get(project_code, 0)
            )
            QTimer.singleShot(
                250,
                lambda code=project_code: self._ensure_task_field_catalog(code),
            )

    def _ensure_task_field_catalog(self, project_code):
        project_code = str(project_code or "")
        attempts = int(self._task_field_catalog_attempts.get(project_code, 0))
        if (
                not project_code
                or self._task_field_catalog_ready(project_code)
                or self._task_field_catalog_worker is not None
                or attempts >= 2):
            return
        self._task_field_catalog_attempts[project_code] = attempts + 1
        from thlib.environment import env_inst
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(
            load_task_field_catalog,
            project_code,
            self._advanced_target_key,
            False,
        )
        if worker is None:
            return
        self._task_field_catalog_worker = worker
        worker.result.connect(
            lambda result, code=project_code: self._task_field_catalog_reloaded(
                code, result
            ),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda _error, code=project_code:
                self._task_field_catalog_failed(code),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    @Slot()
    def reload_task_field_catalog(self):
        """Reload project-owned task choices after an editor changes them."""
        project_code = str(self._application._current_project_code or "")
        if not project_code:
            return
        self._task_field_catalogs.pop(project_code, None)
        self._task_field_catalog_attempts.pop(project_code, None)
        if self._advanced_visible:
            self._ensure_task_field_catalog(project_code)

    def attach_milestone_controller(self, controller):
        """Use one project milestone source for task choices and Gantt."""
        if self._milestone_controller is controller:
            return
        self._milestone_controller = controller
        controller.milestonesChanged.connect(self._milestones_changed)
        self._milestones_changed()

    def _milestones_changed(self):
        controller = self._milestone_controller
        if controller is None:
            return
        project_code = str(self._application._current_project_code or "")
        markers = list(controller.ganttMarkers or [])
        if project_code and controller.projectCode == project_code:
            catalog = dict(self._task_field_catalogs.get(project_code) or {})
            catalog["milestoneChoices"] = [
                {"value": "", "label": "No milestone", "dueDate": ""}
            ] + [
                {
                    "value": str(marker.get("code") or ""),
                    "label": str(marker.get("label") or "Milestone"),
                    "dueDate": str(marker.get("dueDate") or ""),
                }
                for marker in markers
            ]
            self._task_field_catalogs[project_code] = catalog
        if self._advanced_visible:
            self._refresh_advanced_raw_preserving_inserts()
            self._rebuild_advanced_models()
        self.bulkChanged.emit()

    def _refresh_advanced_raw_preserving_inserts(self):
        """Refresh server tasks without dropping unsaved virtual tasks."""
        pending_inserts = [
            dict(record) for record in self._advanced_raw
            if str(record.get("taskCode") or "") in self._advanced_inserts
        ]
        project_code = str(self._application._current_project_code or "")
        field_catalog = dict(
            self._task_field_catalogs.get(project_code) or {}
        )
        priority_choices = list(
            field_catalog.get("priorityChoices") or []
        )
        milestone_choices = list(
            field_catalog.get("milestoneChoices") or []
        )
        for record in pending_inserts:
            record["priorityChoices"] = [
                dict(item) for item in priority_choices
            ]
            record["milestoneChoices"] = [
                dict(item) for item in milestone_choices
            ]
            code = str(record.get("taskCode") or "")
            target = self._advanced_inserts.get(code)
            draft = dict(self._advanced_drafts.get(code) or {})
            process = str(draft.get("process") or record.get("process") or "")
            defaults = self._process_task_defaults(target, process)
            for key in (
                    "status", "assigned", "supervisor", "start", "end",
                    "progress", "plannedHours", "taskPipeline"):
                if key not in draft:
                    record[key] = defaults.get(key, record.get(key))
            planned_hours = max(
                0.0, self._number(record.get("plannedHours"))
            )
            record["plannedHours"] = planned_hours
            record["remainingHours"] = max(
                0.0,
                planned_hours - self._number(record.get("loggedHours")),
            )
            record["hoursLabel"] = format_hours_label(
                self._number(record.get("loggedHours")), planned_hours
            )
            supervisor_choices = self._supervisor_choices_for(
                target, process,
                include_login=record.get("supervisor"),
            )
            record["supervisorChoices"] = [
                dict(item) for item in supervisor_choices
            ]
        self._advanced_raw = self._task_records(
            self.task_store.task_objects()
        ) + pending_inserts

    def _shared_milestone_choices(self):
        controller = self._milestone_controller
        project_code = str(self._application._current_project_code or "")
        if (
                controller is None
                or controller.projectCode != project_code
                or not controller.loaded):
            return None
        return [
            {"value": "", "label": "No milestone", "dueDate": ""}
        ] + [
            {
                "value": str(marker.get("code") or ""),
                "label": str(marker.get("label") or "Milestone"),
                "dueDate": str(marker.get("dueDate") or ""),
            }
            for marker in list(controller.ganttMarkers or [])
        ]

    def _task_field_catalog_failed(self, project_code):
        self._task_field_catalog_worker = None
        if int(self._task_field_catalog_attempts.get(project_code, 0)) < 2:
            QTimer.singleShot(
                250,
                lambda code=project_code: self._ensure_task_field_catalog(code),
            )

    def _task_field_catalog_reloaded(self, project_code, result):
        self._task_field_catalog_worker = None
        if str(self._application._current_project_code or "") != project_code:
            return
        values = result[0] if isinstance(result, tuple) else result
        self._task_field_catalogs[project_code] = dict(values or {})
        shared_milestones = self._shared_milestone_choices()
        if shared_milestones is not None:
            self._task_field_catalogs[project_code][
                "milestoneChoices"
            ] = shared_milestones
        if not self._task_field_catalog_ready(project_code):
            if int(self._task_field_catalog_attempts.get(project_code, 0)) < 2:
                QTimer.singleShot(
                    250,
                    lambda code=project_code:
                        self._ensure_task_field_catalog(code),
                )
            return
        self._task_field_catalog_attempts.pop(project_code, None)
        self._refresh_advanced_raw_preserving_inserts()
        self._rebuild_advanced_models()
        self.bulkChanged.emit()

    def _task_records(self, tasks):
        records = []
        catalogs = {}
        status_catalogs = {}
        user_catalogs = {}
        supervisor_catalogs = {}
        snapshot_catalogs = {}
        project_code = str(self._application._current_project_code or "")
        field_catalog = dict(self._task_field_catalogs.get(project_code) or {})
        priority_choices = list(field_catalog.get("priorityChoices") or [])
        milestone_choices = list(field_catalog.get("milestoneChoices") or [])
        for task in tasks:
            info = dict(task.get_info() or {})
            parent = self.task_store.parent_for_task_info(info)
            parent_key = str(parent.get_search_key() or "") if parent else parent_search_key(info)
            parent_title = ""
            if parent:
                try:
                    parent_title = str(parent.get_title() or parent.get_code() or "")
                except AttributeError:
                    pass
            catalog_key = parent_key
            if catalog_key not in catalogs:
                catalogs[catalog_key] = {
                    item["value"]: item for item in self._process_choices_for(parent)
                }
            process = str(info.get("process") or "")
            process_info = catalogs[catalog_key].get(process, {
                "label": process or "Task", "color": "#607d8b",
                "type": "", "taskPipeline": "",
            })
            choice_key = (catalog_key, process)
            if choice_key not in status_catalogs:
                status_catalogs[choice_key] = self._status_choices_for(
                    parent, process
                )
            statuses = self._with_current_status(
                status_catalogs[choice_key], info.get("status"),
                process_info["color"],
            )
            assigned = self.task_store.assignee_for_task_info(info)
            user_choice_key = (catalog_key, process, assigned)
            if user_choice_key not in user_catalogs:
                user_catalogs[user_choice_key] = self._user_choices_for(
                    parent, process, include_login=assigned
                )
            users = user_catalogs[user_choice_key]
            if choice_key not in supervisor_catalogs:
                supervisor_catalogs[choice_key] = (
                    self._supervisor_choices_for(parent, process)
                )
            supervisor_choices = [
                dict(item) for item in supervisor_catalogs[choice_key]
            ]
            selected_user_index = next((
                index for index, item in enumerate(users)
                if str(item.get("value") or "") == assigned
            ), -1)
            selected_user = (
                users[selected_user_index]
                if selected_user_index >= 0 else {}
            )
            status_color = next((
                item["color"] for item in statuses
                if item["value"] == str(info.get("status") or "")
            ), process_info["color"])
            record = task_record(
                task, parent_title, parent_key,
                process_info["label"], process_info["color"], status_color,
                self._login_label(assigned), assigned_override=assigned,
            )
            record.update({
                "processType": process_info.get("type", ""),
                "taskPipeline": process_info.get("taskPipeline", ""),
                "processChoices": [
                    dict(item) for item in catalogs[catalog_key].values()
                ],
                "isNew": False,
                "statusChoices": statuses,
                "userChoices": users,
                "assignedAvatar": selected_user.get("avatarUrl", ""),
                "assignedChoiceIndex": selected_user_index,
            })
            priority = str(record.get("priority") or "")
            row_priority_choices = [dict(item) for item in priority_choices]
            if priority and not any(
                    str(item.get("value") or "") == priority
                    for item in row_priority_choices):
                row_priority_choices.append({
                    "value": priority,
                    "label": "{} (unavailable)".format(priority),
                    "color": "",
                })
            priority_choice = next((
                item for item in row_priority_choices
                if str(item.get("value") or "") == priority
            ), {})
            supervisor = str(record.get("supervisor") or "")
            if supervisor and not any(
                    str(item.get("value") or "") == supervisor
                    for item in supervisor_choices):
                supervisor_choices.append({
                    "value": supervisor,
                    "label": self._login_label(supervisor) or supervisor,
                    "avatarUrl": "",
                })
            supervisor_choice = next((
                item for item in supervisor_choices
                if str(item.get("value") or "") == supervisor
            ), {})
            milestone_code = str(record.get("milestoneCode") or "")
            row_milestone_choices = [dict(item) for item in milestone_choices]
            if milestone_code and not any(
                    str(item.get("value") or "") == milestone_code
                    for item in row_milestone_choices):
                row_milestone_choices.append({
                    "value": milestone_code,
                    "label": "{} (unavailable)".format(milestone_code),
                    "dueDate": "",
                })
            milestone_choice = next((
                item for item in row_milestone_choices
                if str(item.get("value") or "") == milestone_code
            ), {})
            record.update({
                "priorityChoices": row_priority_choices,
                "priorityLabel": str(
                    priority_choice.get("label") or priority or "No priority"
                ),
                "priorityColor": str(priority_choice.get("color") or ""),
                "supervisorChoices": supervisor_choices,
                "supervisorLabel": str(
                    supervisor_choice.get("label") or supervisor
                    or "No supervisor"
                ),
                "supervisorAvatar": str(
                    supervisor_choice.get("avatarUrl") or ""
                ),
                "milestoneChoices": row_milestone_choices,
                "milestoneLabel": str(
                    milestone_choice.get("label") or milestone_code
                    or "No milestone"
                ),
                "milestoneDueDate": str(
                    milestone_choice.get("dueDate") or ""
                ),
            })
            if choice_key not in snapshot_catalogs:
                snapshot_catalogs[choice_key] = self._snapshot_summary_for(
                    parent, process
                )
            record.update(snapshot_catalogs[choice_key])
            records.append(record)
        return records

    @Slot(str, str)
    def _snapshot_data_changed(self, parent_key, process):
        parent_key = str(parent_key or "")
        process = str(process or "")
        parent = next((
            value for value in self.task_store.parents.values()
            if self.task_store._target_token(value) == parent_key
        ), None)
        if parent is None:
            return
        summary = self._snapshot_summary_for(parent, process)
        changed = False
        for record in self._advanced_raw:
            if (
                str(record.get("parentKey") or "") == parent_key
                and str(record.get("process") or "") == process
            ):
                record.update(summary)
                changed = True
        if changed:
            self._update_presented_values(
                parent_key, process, summary
            )

    def _update_presented_values(self, parent_key, process, values):
        changed = False
        for model in (self.advanced_model, self.table_model, self.gantt_model):
            for row, record in enumerate(model._records):
                if (
                    str(record.get("parentKey") or "") == parent_key
                    and str(record.get("process") or "") == process
                ):
                    changed = model.update_record(row, values) or changed
        if changed:
            self.advancedChanged.emit()

    @Slot(str, str, int, object)
    def update_note_count(self, parent_key, process, count, note_codes=None):
        parent_key = str(parent_key or "")
        process = str(process or "")
        for code in note_codes or []:
            if code:
                self._remember_note_event(code)
        changed = False
        for record in self._advanced_raw:
            if (
                str(record.get("parentKey") or "") == parent_key
                and str(record.get("process") or "") == process
                and int(record.get("notes") or 0) != int(count or 0)
            ):
                record["notes"] = int(count or 0)
                changed = True
        if changed:
            if self._filters.get("hasNotes"):
                self._rebuild_advanced_models()
                return
            self._update_presented_values(
                parent_key, process, {"notes": int(count or 0)}
            )

    @Slot(object)
    def apply_server_batch(self, batch):
        if not self._advanced_visible:
            return
        batch = dict(batch or {})
        self._increment_performance_metric("liveBatches")
        if batch.get("initialActivity"):
            return
        for event in batch.get("activity") or []:
            event = dict(event or {})
            kind = str(event.get("__kind__") or "")
            if kind == "status":
                code = str(event.get("search_code") or "")
                if code in self._advanced_tasks:
                    self._live_task_codes.add(code)
            elif kind == "change":
                search_type = str(event.get("search_type") or "").split("?", 1)[0]
                code = str(event.get("search_code") or "")
                if search_type == "sthpw/task" and code in self._advanced_tasks:
                    self._live_task_codes.add(code)
            elif kind == "note":
                self._apply_note_event(event)
            elif kind == "publication":
                self._apply_publication_event(event)
        if self._live_task_codes and not self._live_timer.isActive():
            self._live_timer.start()

    def _matching_parent_key(self, event):
        search_type = str(event.get("search_type") or "").split("?", 1)[0]
        search_code = str(event.get("search_code") or "")
        for record in self._advanced_raw:
            if (
                str(record.get("parentCode") or "") == search_code
                and (
                    not search_type
                    or str(record.get("parentSearchType") or "").split("?", 1)[0]
                    == search_type
                )
            ):
                return str(record.get("parentKey") or "")
        return ""

    def _apply_note_event(self, event):
        code = str(event.get("code") or "")
        if code and code in self._seen_note_events:
            return
        parent_key = self._matching_parent_key(event)
        process = str(event.get("process") or "")
        if not parent_key or not process:
            return
        if code:
            self._remember_note_event(code)
        changed = False
        count = 0
        for record in self._advanced_raw:
            if (
                str(record.get("parentKey") or "") == parent_key
                and str(record.get("process") or "") == process
            ):
                count = int(record.get("notes") or 0) + 1
                record["notes"] = count
                changed = True
        if changed:
            self._update_presented_values(parent_key, process, {"notes": count})

    def _remember_note_event(self, code):
        code = str(code or "")
        if not code or code in self._seen_note_events:
            return
        self._seen_note_events.add(code)
        self._seen_note_event_order.append(code)
        if len(self._seen_note_event_order) > 2048:
            expired = self._seen_note_event_order[:512]
            del self._seen_note_event_order[:512]
            self._seen_note_events.difference_update(expired)

    def _apply_publication_event(self, event):
        parent_key = self._matching_parent_key(event)
        process = str(event.get("process") or "")
        if parent_key and process:
            self._queue_snapshot_refresh(parent_key, process)

    def _queue_snapshot_refresh(self, parent_key, process):
        parent = next((
            value for value in self.task_store.parents.values()
            if self.task_store._target_token(value) == parent_key
        ), None)
        if parent is None:
            return
        request_id = uuid.uuid4().hex
        token = (parent_key, process)
        if token in self._snapshot_refresh_requests:
            return
        self._snapshot_refresh_requests[token] = request_id
        from thlib.environment import env_inst
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(
            parent.update_snapshots, order_bys=["timestamp desc"]
        )
        if worker is None:
            return
        worker.result.connect(
            lambda _result: self._snapshot_summary_refresh_ready(
                token, request_id
            ),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._snapshot_summary_refresh_failed(
                token, request_id, error
            ),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    @Slot()
    def _flush_live_task_updates(self):
        if self._live_worker is not None or not self._live_task_codes:
            return
        codes = sorted(self._live_task_codes)
        self._live_task_codes.clear()
        request_id = uuid.uuid4().hex
        self._live_request_id = request_id
        project_code = str(
            getattr(
                self._application, "current_project_code",
                getattr(self._application, "_current_project_code", ""),
            ) or ""
        )

        def operation():
            import thlib.tactic_classes as tc
            return tc.get_sobjects(
                "sthpw/task",
                filters=[("code", "in", "|".join(codes))],
                project_code=project_code,
                include_snapshots=False,
                include_info=False,
                include_status_log=False,
            )

        from thlib.environment import env_inst
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            self._live_task_codes.update(codes)
            return
        self._live_worker = worker
        self._live_inflight_codes = set(codes)
        self._increment_performance_metric("serverQueries")
        worker.result.connect(
            lambda result: self._live_tasks_ready(request_id, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._live_tasks_failed(request_id, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    def _live_tasks_ready(self, request_id, result):
        if request_id != self._live_request_id:
            return
        self._live_worker = None
        self._live_inflight_codes.clear()
        changed = False
        for task in self._objects(result):
            info = dict(task.get_info() or {})
            code = str(info.get("code") or "")
            current = self._advanced_tasks.get(code)
            if current is None:
                continue
            if code in self._advanced_drafts:
                current_info = dict(current.get_info() or {})
                if (
                    str(info.get("timestamp") or "")
                    != str(current_info.get("timestamp") or "")
                    or any(
                        info.get(self._advanced_task_field(key))
                        != current_info.get(self._advanced_task_field(key))
                        for key in self._advanced_drafts[code]
                    )
                ):
                    self._advanced_conflicts[code] = task
                    self._advanced_row_errors[code] = (
                        "This task changed on the server. Choose which version to keep."
                    )
                    changed = True
                continue
            self.task_store.replace_task(task)
            self._replace_workspace_task(task)
            replacement = self._task_records([task])
            if not replacement:
                continue
            for row, record in enumerate(self._advanced_raw):
                if str(record.get("taskCode") or "") == code:
                    self._advanced_raw[row] = replacement[0]
                    changed = True
                    break
        if changed:
            self._rebuild_advanced_models()
        if self._live_task_codes:
            self._live_timer.start()

    def _replace_workspace_task(self, task):
        parent = self.task_store.parent_for_task(task)
        selected = self._workspace._selected_sobject
        if parent is None or selected is None:
            return
        try:
            if parent.get_search_key() != selected.get_search_key():
                return
        except AttributeError:
            return
        code = str((task.get_info() or {}).get("code") or "")
        tasks = list(self._workspace._task_sobjects or [])
        replace_tasks = getattr(self._workspace, "replace_tasks", None)
        if not callable(replace_tasks):
            return
        for row, current in enumerate(tasks):
            if str((current.get_info() or {}).get("code") or "") == code:
                tasks[row] = task
                replace_tasks(tasks)
                self._rebuild_process_model()
                return

    def _live_tasks_failed(self, request_id, error):
        if request_id != self._live_request_id:
            return
        self._live_worker = None
        self._live_task_codes.update(self._live_inflight_codes)
        self._live_inflight_codes.clear()
        payload = error[0] if isinstance(error, tuple) and error else error
        if self._application.debug_log:
            self._application.debug_log.log(
                "WARNING", str(payload or "Unable to update changed tasks"),
                group="tasks/live-updates", source="Tasks",
            )
        if self._live_task_codes:
            self._live_timer.start(1000)

    @Slot()
    def shutdown(self):
        self._live_timer.stop()
        self._live_task_codes.clear()
        self._snapshot_refresh_requests.clear()
        for worker in (
            self._live_worker, self._advanced_worker,
            self._advanced_save_worker, self._bulk_worker,
        ):
            cancel = getattr(worker, "cancel", None)
            if callable(cancel):
                cancel()
        self._live_worker = None
        self._advanced_worker = None
        self._advanced_save_worker = None
        self._bulk_worker = None

    @Slot(str, bool)
    def _dock_visibility_changed(self, panel_id, visible):
        if panel_id == "snapshot" and visible:
            self._sync_snapshot_context(self._selected_advanced_code)

    def _sync_snapshot_context(self, task_code):
        task = self._advanced_tasks.get(str(task_code or ""))
        loader = getattr(
            self._application, "load_task_snapshot_context", None
        )
        if not task or not callable(loader):
            return
        parent = self.task_store.parent_for_task(task)
        if parent is None:
            return
        info = dict(task.get_info() or {})
        loader(
            parent,
            str(parent.get_search_key() or ""),
            str(info.get("process") or ""),
            str(info.get("context") or ""),
        )

    def _advanced_failed(self, request_id, error):
        if request_id != self._advanced_request_id:
            return
        payload = error[0] if isinstance(error, tuple) and error else error
        stacktrace = ""
        if isinstance(payload, dict):
            stacktrace = str(payload.get("stacktrace") or "")
            payload = payload.get("exception") or payload.get("message") or payload
        self.task_store.fail_load(
            request_id, str(payload or "Unable to load tasks")
        )
        if self._application.debug_log:
            self._application.debug_log.raise_error(
                payload, stacktrace=stacktrace, group="tasks/advanced"
            )
        self.advancedChanged.emit()

    def _filter_options(self, value_key, label_key, first_label):
        values = {}
        for record in self._advanced_raw:
            value = str(record.get(value_key) or "")
            if value:
                values[value] = str(record.get(label_key) or value)
        return [{"label": first_label, "value": ""}] + [
            {"label": values[value], "value": value}
            for value in sorted(values, key=lambda item: values[item].lower())
        ]

    def _quick_filter_source(self):
        return [
            self._advanced_record_with_draft(record)
            for record in self._advanced_raw
        ]

    @staticmethod
    def _catalog_options(records, value_key, label_key, color_key=""):
        catalog = {}
        for record in records:
            value = str(record.get(value_key) or "")
            if not value:
                continue
            item = catalog.setdefault(value, {
                "key": value,
                "title": str(record.get(label_key) or value),
                "count": 0,
                "accent": str(record.get(color_key) or "") if color_key else "",
            })
            item["count"] += 1
            if not item["accent"] and color_key:
                item["accent"] = str(record.get(color_key) or "")
        return [
            catalog[key]
            for key in sorted(
                catalog, key=lambda value: catalog[value]["title"].casefold()
            )
        ]

    def _quick_filter_group(self, key, title, options):
        selected = self._quick_filters.get(key, set())
        known = {str(option.get("key") or "") for option in options}
        options = [dict(option) for option in options]
        options.extend({
            "key": value,
            "title": value.replace("_", " ").title(),
            "count": 0,
            "accent": "",
        } for value in sorted(selected.difference(known)))
        for option in options:
            option["selected"] = option["key"] in selected
        return {
            "key": key,
            "title": title,
            "allSelected": not selected,
            "options": options,
        }

    def _quick_filter_groups(self):
        records = self._quick_filter_source()
        login = self._current_login()
        preset_counts = {
            "mine": sum(
                1 for record in records
                if login and str(record.get("assigned") or "") == login
            ),
            "unassigned": sum(
                1 for record in records if not record.get("assigned")
            ),
            "overdue": sum(
                1 for record in records if record.get("dueState") == "overdue"
            ),
            "today": sum(
                1 for record in records if record.get("dueState") == "today"
            ),
            "review": sum(1 for record in records if is_review_record(record)),
            "recent": sum(1 for record in records if is_recent_record(record)),
        }
        preset_labels = {
            "mine": "My Tasks",
            "unassigned": "Unassigned",
            "overdue": "Overdue",
            "today": "Today",
            "review": "Review",
            "recent": "Recently Updated",
        }
        preset_keys = ["unassigned", "overdue", "today", "recent"]
        if login:
            preset_keys.insert(0, "mine")
        if preset_counts["review"] or "review" in self._quick_filters["preset"]:
            preset_keys.append("review")
        groups = [self._quick_filter_group(
            "preset", "QUICK VIEW", [
                {
                    "key": key, "title": preset_labels[key],
                    "count": preset_counts[key], "accent": "",
                }
                for key in preset_keys
            ],
        )]

        process_options = self._catalog_options(
            records, "process", "processLabel", "processColor"
        )
        status_options = self._catalog_options(
            records, "status", "status", "statusColor"
        )
        if process_options or self._quick_filters["process"]:
            groups.append(self._quick_filter_group(
                "process", "PROCESSES", process_options
            ))
        if status_options or self._quick_filters["status"]:
            groups.append(self._quick_filter_group(
                "status", "STATUSES", status_options
            ))
        for key, title, value_key, label_key, color_key in (
            ("priority", "PRIORITIES", "priority", "priorityLabel", "priorityColor"),
            ("milestone", "MILESTONES", "milestoneCode", "milestoneLabel", ""),
            ("supervisor", "SUPERVISORS", "supervisor", "supervisorLabel", ""),
        ):
            options = self._catalog_options(
                records, value_key, label_key, color_key
            )
            if options or self._quick_filters[key]:
                groups.append(self._quick_filter_group(key, title, options))
        if self._advanced_scope in {"team", "project", "multiple"}:
            user_options = self._catalog_options(
                records, "assigned", "assignedLabel"
            )
            if user_options or self._quick_filters["assigned"]:
                groups.append(self._quick_filter_group(
                    "assigned", "ASSIGNEES", user_options
                ))
        return groups

    def _collapsed_group_keys(self):
        prefix = "{}\x1f".format(self._group_mode)
        return {
            token[len(prefix):]
            for token in self._collapsed_groups if token.startswith(prefix)
        }

    @staticmethod
    def _table_projection(records):
        """Keep one lightweight header row for every collapsed group."""
        return [
            dict(record) for record in records
            if not record.get("groupCollapsed") or record.get("groupFirst")
        ]

    def _replace_table_projection(self, records, reset=False):
        projected = self._table_projection(records)
        if reset:
            self.table_model.reset_records(projected)
        else:
            self.table_model.replace(projected)

    def _rebuild_advanced_models(self):
        self._increment_performance_metric("projectionRebuilds")
        source_records = [
            self._advanced_record_with_draft(record)
            for record in self._advanced_raw
        ]
        base_filters = dict(self._filters)
        base_filters["day"] = ""
        current_login = self._current_login()
        calendar_source = filtered_records(
            source_records, base_filters, self._quick_filters, current_login
        )
        for record in calendar_source:
            record["selected"] = (
                record.get("taskCode") == self._selected_advanced_code
            )
        visible = filtered_records(
            source_records, self._filters, self._quick_filters, current_login
        )
        visible_codes = {
            str(record.get("taskCode") or "") for record in visible
        }
        visible.extend(
            record for record in source_records
            if record.get("isNew")
            and str(record.get("taskCode") or "") not in visible_codes
        )
        visible = sort_and_group(
            visible, self._sort_mode, self._group_mode,
            self._collapsed_group_keys(),
        )
        visible_task_codes = frozenset(
            str(record.get("taskCode") or "")
            for record in visible if record.get("taskCode")
        )
        visible_task_set_changed = (
            visible_task_codes != self._visible_work_hour_task_codes
        )
        self._visible_work_hour_task_codes = visible_task_codes
        for record in visible:
            record["selected"] = record.get("taskCode") == self._selected_advanced_code
            record["checked"] = record.get("taskCode") in self._advanced_checked
        self.advanced_model.replace(visible)
        self._replace_table_projection(visible)
        project_code = str(self._application._current_project_code or "")
        field_catalog = dict(self._task_field_catalogs.get(project_code) or {})
        milestone_markers = field_catalog.get("milestoneChoices") or []
        if (
                self._milestone_controller is not None
                and self._milestone_controller.projectCode == project_code):
            milestone_markers = list(
                self._milestone_controller.ganttMarkers or []
            )
        self._gantt = gantt_layout(
            visible, milestones=milestone_markers
        )
        self.gantt_model.replace(self._gantt["records"])
        cells = calendar_cells(
            self._calendar_year, self._calendar_month, calendar_source,
            milestones=milestone_markers,
        )
        selected_day = str(self._filters.get("day") or "")
        for cell in cells:
            cell["selected"] = cell["date"] == selected_day
        self.calendar_model.replace(cells)
        if (
                self._selected_advanced_code
                and self._selected_advanced_code not in self._advanced_tasks
                and self._selected_advanced_code not in self._advanced_inserts):
            self._selected_advanced_code = ""
            self.history_model.clear()
        self.advancedChanged.emit()
        if visible_task_set_changed:
            self.visibleTaskSetChanged.emit()

    def _advanced_record_with_draft(self, source):
        record = dict(source)
        code = str(record.get("taskCode") or "")
        draft = dict(self._advanced_drafts.get(code) or {})
        record.update(draft)
        if "process" in draft and code in self._advanced_inserts:
            target = self._advanced_inserts[code]
            process = str(draft.get("process") or "")
            choice = next((
                item for item in record.get("processChoices") or []
                if str(item.get("value") or "") == process
            ), {})
            record.update({
                "processLabel": str(choice.get("label") or process or "Task"),
                "processColor": str(
                    choice.get("color") or record.get("processColor")
                    or "#607d8b"
                ),
                "processType": str(choice.get("type") or ""),
                "taskPipeline": str(choice.get("taskPipeline") or ""),
                "statusChoices": self._status_choices_for(target, process),
                "userChoices": self._user_choices_for(
                    target, process, include_login=record.get("assigned")
                ),
                "supervisorChoices": self._supervisor_choices_for(
                    target, process, include_login=record.get("supervisor")
                ),
            })
        if "status" in draft:
            record["statusColor"] = next((
                str(item.get("color") or record.get("processColor") or "#607d8b")
                for item in record.get("statusChoices") or []
                if str(item.get("value") or "") == str(draft["status"] or "")
            ), str(record.get("processColor") or "#607d8b"))
        if "assigned" in draft:
            user_choices = record.get("userChoices") or []
            selected_user_index = next((
                index for index, item in enumerate(user_choices)
                if str(item.get("value") or "") == str(draft["assigned"] or "")
            ), -1)
            selected_user = (
                user_choices[selected_user_index]
                if selected_user_index >= 0 else {}
            )
            record["assignedLabel"] = str(
                selected_user.get("label") or draft["assigned"] or "Not assigned"
            )
            record["assignedAvatar"] = str(
                selected_user.get("avatarUrl") or ""
            )
            record["assignedChoiceIndex"] = selected_user_index
        if "supervisor" in draft:
            choice = next((
                item for item in record.get("supervisorChoices") or []
                if str(item.get("value") or "")
                == str(draft.get("supervisor") or "")
            ), {})
            record["supervisorLabel"] = str(
                choice.get("label") or draft.get("supervisor")
                or "No supervisor"
            )
            record["supervisorAvatar"] = str(choice.get("avatarUrl") or "")
        if "priority" in draft:
            choice = next((
                item for item in record.get("priorityChoices") or []
                if str(item.get("value") or "")
                == str(draft.get("priority") or "")
            ), {})
            record["priorityLabel"] = str(
                choice.get("label") or draft.get("priority") or "No priority"
            )
            record["priorityColor"] = str(choice.get("color") or "")
        if "milestoneCode" in draft:
            choice = next((
                item for item in record.get("milestoneChoices") or []
                if str(item.get("value") or "")
                == str(draft.get("milestoneCode") or "")
            ), {})
            record["milestoneLabel"] = str(
                choice.get("label") or draft.get("milestoneCode")
                or "No milestone"
            )
            record["milestoneDueDate"] = str(choice.get("dueDate") or "")
        if "end" in draft:
            record["dueState"] = due_state(record.get("end"))
        if "progress" in draft:
            try:
                record["progress"] = max(
                    0, min(100, int(float(str(draft["progress"]))))
                )
            except (TypeError, ValueError):
                record["progress"] = int(source.get("progress") or 0)
        if "plannedHours" in draft:
            planned_hours = max(
                0.0, self._number(draft.get("plannedHours"))
            )
            logged_hours = max(
                0.0, self._number(record.get("loggedHours"))
            )
            record["plannedHours"] = planned_hours
            record["remainingHours"] = max(
                0.0, planned_hours - logged_hours
            )
            record["overPlanHours"] = max(
                0.0, logged_hours - planned_hours
            )
            record["hoursLabel"] = format_hours_label(
                logged_hours, planned_hours
            )
        record["dirty"] = bool(draft)
        record["loading"] = self._advanced_saving and bool(draft)
        record["error"] = str(self._advanced_row_errors.get(code) or "")
        record["conflict"] = code in self._advanced_conflicts
        return record

    @staticmethod
    def _advanced_task_field(key):
        return {
            "start": "bid_start_date",
            "end": "bid_end_date",
            "milestoneCode": "milestone_code",
            "plannedHours": "bid_duration",
        }.get(str(key or ""), str(key or ""))

    def _stage_advanced_values(self, task_code, values, rebuild=True):
        task_code = str(task_code or "")
        if self._advanced_saving:
            return False
        source = next((
            record for record in self._advanced_raw
            if str(record.get("taskCode") or "") == task_code
        ), None)
        if source is None:
            return False
        before = dict(self._advanced_drafts.get(task_code) or {})
        draft = self._advanced_drafts.setdefault(task_code, {})
        for key, value in values.items():
            value = str(value or "")
            if value == str(source.get(key) or ""):
                draft.pop(key, None)
            else:
                draft[key] = value
        if not draft:
            self._advanced_drafts.pop(task_code, None)
        self._advanced_row_errors.pop(task_code, None)
        self._advanced_error = ""
        if rebuild:
            self._rebuild_advanced_models()
        return before != dict(self._advanced_drafts.get(task_code) or {})

    @Slot(str, str, "QVariant")
    def stage_advanced_value(self, task_code, key, value):
        task_code = str(task_code or "")
        key = str(key or "")
        if key not in {
                "process", "context", "status", "assigned", "start", "end", "progress",
                "priority", "milestoneCode", "supervisor", "description",
                "plannedHours",
        }:
            return
        if key == "progress" and not self._progress_column():
            return
        self._stage_advanced_values(task_code, {key: value})

    @Slot(str, str)
    def stage_advanced_process(self, task_code, process):
        task_code = str(task_code or "")
        if task_code not in self._advanced_inserts:
            return
        process = str(process or "")
        if self._group_mode == "process":
            self._collapsed_groups.discard(
                "process\x1f{}".format(process or "__none__")
            )
        target = self._advanced_inserts[task_code]
        defaults = self._process_task_defaults(target, process)
        values = {
            "process": process,
            "context": process,
            "status": str(defaults.get("status") or ""),
            "assigned": str(defaults.get("assigned") or ""),
            "supervisor": str(defaults.get("supervisor") or ""),
            "start": str(defaults.get("start") or ""),
            "end": str(defaults.get("end") or ""),
            "progress": int(defaults.get("progress") or 0),
            "plannedHours": float(
                defaults.get("plannedHours") or 0.0
            ),
        }
        self._stage_advanced_values(task_code, values)

    @staticmethod
    def _gantt_date_value(original, target):
        parsed = parse_datetime(original)
        if parsed is None:
            return datetime.combine(target, datetime.min.time()).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        return datetime.combine(target, parsed.time()).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    def _gantt_schedule_snapshot(self):
        return {
            code: {
                key: copy.deepcopy(value)
                for key, value in draft.items()
                if key in {"start", "end", "progress"}
            }
            for code, draft in self._advanced_drafts.items()
            if any(key in draft for key in {"start", "end", "progress"})
        }

    def _restore_gantt_schedule_snapshot(self, snapshot):
        for code in list(self._advanced_drafts):
            draft = self._advanced_drafts[code]
            draft.pop("start", None)
            draft.pop("end", None)
            draft.pop("progress", None)
            if not draft:
                self._advanced_drafts.pop(code, None)
        for code, values in (snapshot or {}).items():
            if values:
                self._advanced_drafts.setdefault(code, {}).update(
                    copy.deepcopy(values)
                )
        self._advanced_row_errors.clear()
        self._advanced_error = ""
        self._rebuild_advanced_models()

    def _push_gantt_history(self):
        snapshot = self._gantt_schedule_snapshot()
        if not self._gantt_undo or self._gantt_undo[-1] != snapshot:
            self._gantt_undo.append(snapshot)
            del self._gantt_undo[:-50]
        self._gantt_redo.clear()

    def _clear_gantt_history(self):
        self._gantt_undo.clear()
        self._gantt_redo.clear()

    @staticmethod
    def _next_workday(value, direction=1):
        direction = 1 if direction >= 0 else -1
        while value.weekday() >= 5:
            value += timedelta(days=direction)
        return value

    @classmethod
    def _add_workdays(cls, value, amount):
        value = cls._next_workday(value, 1 if amount >= 0 else -1)
        direction = 1 if amount >= 0 else -1
        for _index in range(abs(int(amount))):
            value += timedelta(days=direction)
            value = cls._next_workday(value, direction)
        return value

    @staticmethod
    def _workday_duration(start_value, end_value):
        if end_value < start_value:
            return 1
        return max(1, sum(
            1 for offset in range((end_value - start_value).days + 1)
            if (start_value + timedelta(days=offset)).weekday() < 5
        ))

    def _gantt_dates(self, record, start_day, duration_days):
        range_start = parse_datetime(self._gantt.get("rangeStart")).date()
        start_date = range_start + timedelta(days=int(start_day))
        duration_days = max(1, int(duration_days))
        if self._gantt_working_days:
            start_date = self._next_workday(start_date)
            end_date = self._add_workdays(start_date, duration_days - 1)
        else:
            end_date = start_date + timedelta(days=duration_days - 1)
        return {
            "start": self._gantt_date_value(record.get("start"), start_date),
            "end": self._gantt_date_value(record.get("end"), end_date),
        }

    def _apply_gantt_edits(self, edits):
        if not edits or self._advanced_saving:
            return False
        self._push_gantt_history()
        changed = False
        for code, values in edits.items():
            changed = self._stage_advanced_values(
                code, values, rebuild=False
            ) or changed
        if changed:
            self._rebuild_advanced_models()
            return True
        self._gantt_undo.pop()
        return False

    @Slot(str, int, int, result=bool)
    @Slot(str, int, int, str, result=bool)
    def stage_gantt_schedule(
            self, task_code, start_day, duration_days, edit_mode=""):
        task_code = str(task_code or "")
        source = next((
            record for record in self._advanced_raw
            if str(record.get("taskCode") or "") == task_code
        ), None)
        range_start = parse_datetime(self._gantt.get("rangeStart"))
        if source is None or range_start is None or self._advanced_saving:
            return False
        try:
            start_day = int(start_day)
            duration_days = max(1, int(duration_days))
        except (TypeError, ValueError):
            return False
        current = self._advanced_record_with_draft(source)
        edits = {
            task_code: self._gantt_dates(
                current, start_day, duration_days
            )
        }
        selected = set(self._advanced_checked)
        if edit_mode == "move" and task_code in selected and len(selected) > 1:
            original_start = parse_datetime(current.get("start"))
            if original_start:
                desired_start = parse_datetime(edits[task_code]["start"])
                delta = desired_start.date() - original_start.date()
                for code in selected - {task_code}:
                    other = next((
                        record for record in self._advanced_raw
                        if str(record.get("taskCode") or "") == code
                    ), None)
                    if not other:
                        continue
                    other = self._advanced_record_with_draft(other)
                    other_start = parse_datetime(other.get("start"))
                    other_end = parse_datetime(other.get("end"))
                    if not other_start or not other_end:
                        continue
                    start_date = other_start.date() + delta
                    if self._gantt_working_days:
                        start_date = self._next_workday(
                            start_date, 1 if delta.days >= 0 else -1
                        )
                        workdays = self._workday_duration(
                            other_start.date(), other_end.date()
                        )
                        end_date = self._add_workdays(
                            start_date, workdays - 1
                        )
                    else:
                        end_date = other_end.date() + delta
                    edits[code] = {
                        "start": self._gantt_date_value(
                            other.get("start"), start_date
                        ),
                        "end": self._gantt_date_value(
                            other.get("end"), end_date
                        ),
                    }
        return self._apply_gantt_edits(edits)

    @Slot(str, int, result=bool)
    def stage_gantt_progress(self, task_code, progress):
        if not self._progress_column():
            return False
        try:
            progress = max(0, min(100, int(progress)))
        except (TypeError, ValueError):
            return False
        return self._apply_gantt_edits({
            str(task_code or ""): {"progress": str(progress)}
        })

    @Slot(str, int, result=bool)
    def apply_gantt_batch(self, action, amount=1):
        action = str(action or "")
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            amount = 1
        records = []
        for source in self._advanced_raw:
            code = str(source.get("taskCode") or "")
            if code not in self._advanced_checked:
                continue
            record = self._advanced_record_with_draft(source)
            start_value = parse_datetime(record.get("start"))
            end_value = parse_datetime(record.get("end"))
            if start_value and end_value:
                records.append((code, record, start_value.date(), end_value.date()))
        if not records:
            return False
        edits = {}
        anchor_start = min(item[2] for item in records)
        anchor_end = max(item[3] for item in records)
        sequence_cursor = anchor_start
        for code, record, start_date, end_date in records:
            if action == "shift":
                if self._gantt_working_days:
                    next_start = self._add_workdays(start_date, amount)
                    next_end = self._add_workdays(end_date, amount)
                else:
                    delta = timedelta(days=amount)
                    next_start, next_end = start_date + delta, end_date + delta
            elif action == "align-start":
                next_start, next_end = anchor_start, end_date
            elif action == "align-end":
                next_start, next_end = start_date, anchor_end
            elif action in {"extend", "shorten"}:
                delta = amount if action == "extend" else -amount
                if self._gantt_working_days:
                    next_start = start_date
                    next_end = self._add_workdays(end_date, delta)
                else:
                    next_start = start_date
                    next_end = end_date + timedelta(days=delta)
                if next_end < next_start:
                    next_end = next_start
            elif action == "sequence":
                duration = self._workday_duration(start_date, end_date)
                if self._gantt_working_days:
                    next_start = self._next_workday(sequence_cursor)
                    next_end = self._add_workdays(next_start, duration - 1)
                    sequence_cursor = self._add_workdays(next_end, 1)
                else:
                    duration = (end_date - start_date).days + 1
                    next_start = sequence_cursor
                    next_end = next_start + timedelta(days=duration - 1)
                    sequence_cursor = next_end + timedelta(days=1)
            else:
                return False
            edits[code] = {
                "start": self._gantt_date_value(record.get("start"), next_start),
                "end": self._gantt_date_value(record.get("end"), next_end),
            }
        return self._apply_gantt_edits(edits)

    @Slot()
    def undo_gantt_change(self):
        if not self._gantt_undo or self._advanced_saving:
            return
        self._gantt_redo.append(self._gantt_schedule_snapshot())
        self._restore_gantt_schedule_snapshot(self._gantt_undo.pop())

    @Slot()
    def redo_gantt_change(self):
        if not self._gantt_redo or self._advanced_saving:
            return
        self._gantt_undo.append(self._gantt_schedule_snapshot())
        self._restore_gantt_schedule_snapshot(self._gantt_redo.pop())

    @Slot(bool)
    def set_gantt_working_days(self, enabled):
        enabled = bool(enabled)
        if enabled != self._gantt_working_days:
            self._gantt_working_days = enabled
            self.advancedChanged.emit()

    @Slot(bool)
    def set_gantt_resource_mode(self, enabled):
        enabled = bool(enabled)
        if enabled == self._gantt_resource_mode:
            return
        if enabled:
            self._gantt_resource_previous = (
                self._sort_mode, self._group_mode
            )
            self._sort_mode = "user"
            self._group_mode = "user"
        else:
            previous = self._gantt_resource_previous
            if previous:
                self._sort_mode, self._group_mode = previous
            self._gantt_resource_previous = None
        self._gantt_resource_mode = enabled
        self._rebuild_advanced_models()

    @Slot()
    @Slot(str)
    def discard_advanced_changes(self, task_code=""):
        if self._advanced_saving:
            return
        task_code = str(task_code or "")
        if task_code:
            if task_code in self._advanced_inserts:
                self.taskDraftRemoved.emit(task_code)
                self._advanced_inserts.pop(task_code, None)
                self._advanced_raw = [
                    record for record in self._advanced_raw
                    if str(record.get("taskCode") or "") != task_code
                ]
                self._advanced_checked.discard(task_code)
                if self._selected_advanced_code == task_code:
                    self._selected_advanced_code = ""
            self._advanced_drafts.pop(task_code, None)
            self._advanced_row_errors.pop(task_code, None)
            self._advanced_conflicts.pop(task_code, None)
        else:
            virtual_codes = set(self._advanced_inserts)
            if virtual_codes:
                for code in virtual_codes:
                    self.taskDraftRemoved.emit(code)
                self._advanced_raw = [
                    record for record in self._advanced_raw
                    if str(record.get("taskCode") or "") not in virtual_codes
                ]
                self._advanced_checked.difference_update(virtual_codes)
                if self._selected_advanced_code in virtual_codes:
                    self._selected_advanced_code = ""
            self._advanced_inserts.clear()
            self._advanced_drafts.clear()
            self._advanced_row_errors.clear()
            self._advanced_conflicts.clear()
            self._clear_gantt_history()
        self._advanced_error = ""
        self._rebuild_advanced_models()

    @Slot(result=bool)
    def save_advanced_changes(self):
        if self._advanced_saving or not self._advanced_drafts:
            return False
        conflicted = set(self._advanced_drafts).intersection(
            self._advanced_conflicts
        )
        if conflicted:
            self._advanced_error = (
                "Resolve server conflicts before saving task changes."
            )
            self._rebuild_advanced_models()
            return False
        from thlib.environment import env_inst

        edits = []
        inserts = []
        for code, values in self._advanced_drafts.items():
            if code in self._advanced_inserts:
                source = next((
                    record for record in self._advanced_raw
                    if str(record.get("taskCode") or "") == code
                ), None)
                if source is None:
                    continue
                record = self._advanced_record_with_draft(source)
                process = str(record.get("process") or "")
                if not process:
                    self._advanced_row_errors[code] = "Process is required."
                    continue
                data = {
                    "process": process,
                    "context": str(record.get("context") or process),
                }
                task_pipeline = str(record.get("taskPipeline") or "")
                if task_pipeline:
                    data["pipeline_code"] = task_pipeline
                field_map = {
                    "status": "status",
                    "assigned": "assigned",
                    "start": "bid_start_date",
                    "end": "bid_end_date",
                    "description": "description",
                    "priority": "priority",
                    "milestoneCode": "milestone_code",
                    "supervisor": "supervisor",
                    "plannedHours": "bid_duration",
                }
                for source_key, target_key in field_map.items():
                    value = record.get(source_key)
                    if value not in (None, ""):
                        data[target_key] = value
                progress_field = self._progress_column()
                if progress_field:
                    data[progress_field] = int(record.get("progress") or 0)
                inserts.append((
                    code, self._advanced_inserts[code], data
                ))
                continue
            task = self._advanced_tasks.get(code)
            if task:
                prepared = {}
                for key, value in values.items():
                    field = self._advanced_task_field(key)
                    if key == "progress":
                        field = self._progress_column()
                        if not field:
                            continue
                        value = int(value)
                    prepared[field] = value
                if prepared:
                    edits.append((code, task, prepared))
        if not edits and not inserts:
            self._rebuild_advanced_models()
            return False

        def operation():
            import traceback
            import thlib.tactic_classes as tc

            completed = []
            created = []
            for code, target, values in inserts:
                try:
                    project_code = str(
                        target.get_project().get_code() or ""
                    )
                except AttributeError:
                    project_code = str(
                        self._application._current_project_code or ""
                    )
                try:
                    result = tc.insert_sobjects(
                        "sthpw/task", project_code, values,
                        parent_key=target.get_search_key(), triggers=True,
                    )
                    created.append({
                        "draftCode": code,
                        "value": result,
                    })
                except Exception as exc:
                    return {
                        "completed": completed,
                        "created": created,
                        "failed": code,
                        "error": str(exc),
                        "stacktrace": traceback.format_exc(),
                    }
                completed.append(code)
            for code, task, values in edits:
                info = task.get_info()
                previous = {key: info.get(key) for key in values}
                pending = dict(getattr(task, "update_dict", {}) or {})
                try:
                    for key, value in values.items():
                        task.set_value(key, value)
                    task.commit(triggers=True)
                except Exception as exc:
                    info.update(previous)
                    if hasattr(task, "update_dict"):
                        task.update_dict = pending
                    return {
                        "completed": completed,
                        "created": created,
                        "failed": code,
                        "error": str(exc),
                        "stacktrace": traceback.format_exc(),
                    }
                completed.append(code)
            return {"completed": completed, "created": created}

        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            self._advanced_error = "Server worker pool is unavailable."
            self.advancedChanged.emit()
            return False
        self._advanced_saving = True
        self._advanced_save_worker = worker
        self._advanced_row_errors.clear()
        self._advanced_error = ""
        self._rebuild_advanced_models()
        worker.result.connect(
            self._advanced_changes_saved, Qt.ConnectionType.QueuedConnection
        )
        worker.error.connect(
            self._advanced_changes_failed, Qt.ConnectionType.QueuedConnection
        )
        worker.start()
        return True

    @Slot(str, str)
    def resolve_advanced_conflict(self, task_code, strategy):
        if self._advanced_saving:
            return
        task_code = str(task_code or "")
        task = self._advanced_conflicts.pop(task_code, None)
        if task is None:
            return
        if strategy == "server":
            self._advanced_drafts.pop(task_code, None)
        elif strategy != "mine":
            self._advanced_conflicts[task_code] = task
            return
        self._advanced_row_errors.pop(task_code, None)
        self.task_store.replace_task(task)
        self._replace_workspace_task(task)
        replacement = self._task_records([task])
        if replacement:
            for row, record in enumerate(self._advanced_raw):
                if str(record.get("taskCode") or "") == task_code:
                    self._advanced_raw[row] = replacement[0]
                    break
        self._advanced_error = ""
        self._rebuild_advanced_models()

    def _advanced_changes_saved(self, result):
        result = dict(result or {})
        created_tasks = []
        created_values = list(result.get("created") or [])
        for item in created_values:
            item = dict(item or {})
            code = str(item.get("draftCode") or "")
            target = self._advanced_inserts.get(code)
            value = item.get("value")
            if hasattr(value, "get_info"):
                created_tasks.append(value)
                continue
            if not isinstance(value, dict) or target is None:
                continue
            try:
                project = target.get_project()
            except AttributeError:
                project = None
            import thlib.tactic_classes as tc
            created_tasks.append(tc.Task(dict(value), project=project))
        for code in result.get("completed") or []:
            target = self._advanced_inserts.pop(str(code), None)
            if target is not None:
                self.taskDraftRemoved.emit(str(code))
                self.task_store.set_parents([target], append=True)
            self._advanced_drafts.pop(str(code), None)
            self._advanced_row_errors.pop(str(code), None)
        for task in created_tasks:
            self.task_store.replace_task(task)
        self._advanced_saving = False
        self._advanced_save_worker = None
        error = str(result.get("error") or "")
        if error:
            self._advanced_error = error
            failed = str(result.get("failed") or "")
            for code in self._advanced_drafts:
                self._advanced_row_errors[code] = error
            if failed:
                self._advanced_row_errors[failed] = error
            if self._application.debug_log:
                self._application.debug_log.raise_error(
                    error,
                    stacktrace=str(result.get("stacktrace") or ""),
                    group="tasks/advanced",
                )
        else:
            self._advanced_error = ""
            self._clear_gantt_history()
        pending_virtual = [
            record for record in self._advanced_raw
            if str(record.get("taskCode") or "") in self._advanced_inserts
        ]
        self._advanced_raw = self._task_records(
            self.task_store.task_objects()
        ) + pending_virtual
        self._rebuild_advanced_models()

    def _advanced_changes_failed(self, error):
        payload = error[0] if isinstance(error, tuple) and error else error
        stacktrace = ""
        if isinstance(payload, dict):
            stacktrace = str(payload.get("stacktrace") or "")
            payload = payload.get("exception") or payload.get("message") or payload
        message = str(payload or "Unable to save task changes")
        self._advanced_saving = False
        self._advanced_save_worker = None
        self._advanced_error = message
        for code in self._advanced_drafts:
            self._advanced_row_errors[code] = message
        if self._application.debug_log:
            self._application.debug_log.raise_error(
                payload, stacktrace=stacktrace, group="tasks/advanced"
            )
        self._rebuild_advanced_models()

    @Slot(str, "QVariant")
    def set_filter(self, name, value):
        if name not in self._filters:
            return
        self._filters[name] = value
        self._rebuild_advanced_models()

    @Slot()
    def clear_filters(self):
        self._filters = {
            "text": "", "process": "", "status": "", "assigned": "",
            "due": "", "hasNotes": False, "day": "", "priority": "",
            "milestone": "", "supervisor": "",
        }
        for values in self._quick_filters.values():
            values.clear()
        self._rebuild_advanced_models()

    @Slot(str, str)
    def toggle_quick_filter(self, group, value):
        group = str(group or "")
        value = str(value or "")
        if group not in self._quick_filters:
            return
        if not value:
            self._quick_filters[group].clear()
        elif value in self._quick_filters[group]:
            self._quick_filters[group].remove(value)
        else:
            self._quick_filters[group].add(value)
        self._rebuild_advanced_models()

    @Slot(str)
    def clear_quick_filter_group(self, group):
        group = str(group or "")
        if group in self._quick_filters and self._quick_filters[group]:
            self._quick_filters[group].clear()
            self._rebuild_advanced_models()

    @Slot()
    def clear_quick_filters(self):
        if any(self._quick_filters.values()):
            for values in self._quick_filters.values():
                values.clear()
            self._rebuild_advanced_models()

    @Slot(str)
    def apply_workspace_preset(self, value):
        value = str(value or "")
        allowed = {
            "mine", "unassigned", "overdue", "today", "review", "recent",
        }
        for values in self._quick_filters.values():
            values.clear()
        if value in allowed:
            self._quick_filters["preset"].add(value)
        if value == "recent":
            self._sort_mode = "recent"
        self._rebuild_advanced_models()

    @Slot()
    def clear_advanced_error(self):
        if self._advanced_error:
            self._advanced_error = ""
            self.advancedChanged.emit()

    @Slot(str)
    def set_view_mode(self, value):
        if value in {"list", "gantt"} and value != self._view_mode:
            self._view_mode = value
            self._store_workspace_preferences()
            self.advancedChanged.emit()

    @Slot(str)
    def set_sort_mode(self, value):
        if value in {"due", "recent", "process", "user", "status", "object"}:
            self._gantt_resource_mode = False
            self._gantt_resource_previous = None
            self._sort_mode = value
            self._store_workspace_preferences()
            self._rebuild_advanced_models()

    @Slot(str)
    def set_group_mode(self, value):
        if value in {
                "process", "status", "user", "object", "project",
                "search_type", "none"}:
            self._gantt_resource_mode = False
            self._gantt_resource_previous = None
            self._group_mode = value
            self._store_workspace_preferences()
            self._rebuild_advanced_models()

    @Slot(str)
    def toggle_group_collapsed(self, group_key):
        group_key = str(group_key or "")
        if not group_key or self._group_mode == "none":
            return
        token = "{}\x1f{}".format(self._group_mode, group_key)
        if token in self._collapsed_groups:
            self._collapsed_groups.remove(token)
            collapsed = False
        else:
            self._collapsed_groups.add(token)
            collapsed = True

        group_rows = [
            row for row, record in enumerate(self.advanced_model._records)
            if str(record.get("groupKey") or "") == group_key
        ]
        if not self.advanced_model.set_role_for_rows(
                group_rows, "groupCollapsed", collapsed):
            return
        self._replace_table_projection(
            self.advanced_model._records, reset=True
        )

    @Slot(int)
    def change_calendar_month(self, offset):
        value = self._calendar_month - 1 + int(offset)
        self._calendar_year += value // 12
        self._calendar_month = value % 12 + 1
        self._filters["day"] = ""
        self._rebuild_advanced_models()

    @Slot()
    def calendar_today(self):
        today = date.today()
        self._calendar_year = today.year
        self._calendar_month = today.month
        self._filters["day"] = today.isoformat()
        self._rebuild_advanced_models()

    @Slot(str)
    def select_calendar_day(self, value):
        value = str(value or "")
        self._filters["day"] = (
            "" if value and value == self._filters.get("day") else value
        )
        self._rebuild_advanced_models()

    @Slot(str, str, str)
    def activate_calendar_task(self, task_code, parent_key, process):
        task_code = str(task_code or "")
        if task_code not in self._advanced_tasks:
            return
        self.activate_advanced_task(task_code, 0)
        self.open_notes(parent_key, process)

    @Slot(int)
    def select_advanced_task(self, row):
        if not 0 <= row < len(self.advanced_model._records):
            return
        code = str(self.advanced_model._records[row].get("taskCode") or "")
        self._selected_advanced_code = code
        task = self._advanced_tasks.get(code)
        self._history_request_id = uuid.uuid4().hex
        records = []
        if task:
            statuses = self._status_choices_for(
                self.task_store.parent_for_task(task),
                str((task.get_info() or {}).get("process") or ""),
            )
            colors = {item["value"]: item["color"] for item in statuses}
            for status in task.get_status_log() or []:
                info = dict(status.get_info() or {})
                to_status = str(info.get("to_status") or info.get("status") or "")
                records.append({
                    "timestamp": str(info.get("timestamp") or ""),
                    "fromStatus": str(info.get("from_status") or ""),
                    "toStatus": to_status,
                    "login": str(info.get("login") or ""),
                    "color": colors.get(to_status, "#607d8b"),
                })
        self.history_model.replace(records)
        self._rebuild_advanced_models()
        if task and not records and code not in self._history_loaded:
            self._load_task_history(task, self._history_request_id)

    @Slot(str, int)
    def activate_advanced_task(self, task_code, modifiers=0):
        task_code = str(task_code or "")
        if self._bulk_busy or task_code not in self._advanced_tasks:
            return
        modifiers = int(modifiers or 0)
        control = bool(
            modifiers & Qt.KeyboardModifier.ControlModifier.value
        )
        shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier.value)
        visible_codes = [
            str(record.get("taskCode") or "")
            for record in self.advanced_model._records
        ]
        if shift and self._advanced_selection_anchor in visible_codes:
            start = visible_codes.index(self._advanced_selection_anchor)
            end = visible_codes.index(task_code)
            if start > end:
                start, end = end, start
            self._advanced_checked.update(visible_codes[start:end + 1])
        elif control:
            if task_code in self._advanced_checked:
                self._advanced_checked.remove(task_code)
            else:
                self._advanced_checked.add(task_code)
            self._advanced_selection_anchor = task_code
        else:
            self._advanced_selection_anchor = task_code
        self._selected_advanced_code = task_code
        self._sync_bulk_selection()
        self._rebuild_advanced_models()
        record = next((
            item for item in self._advanced_raw
            if str(item.get("taskCode") or "") == task_code
        ), {})
        parent_key = str(record.get("parentKey") or "")
        process = str(record.get("process") or "")
        self.taskActivated.emit(task_code, parent_key, process)
        if parent_key and parent_key != self.targetSearchKey:
            self._application._selected_detail_process = process
            self._application.select_sobject(parent_key)
        self._sync_snapshot_context(task_code)

    @Slot(str)
    def toggle_advanced_checked(self, task_code):
        task_code = str(task_code or "")
        if self._bulk_busy or task_code not in self._advanced_tasks:
            return
        if task_code in self._advanced_checked:
            self._advanced_checked.remove(task_code)
        else:
            self._advanced_checked.add(task_code)
        self._advanced_selection_anchor = task_code
        self._sync_bulk_selection()
        self._rebuild_advanced_models()

    @Slot(bool)
    def set_all_advanced_checked(self, checked):
        if self._bulk_busy:
            return
        codes = {
            str(record.get("taskCode") or "")
            for record in self.advanced_model._records
            if record.get("taskCode")
        }
        if checked:
            self._advanced_checked.update(codes)
        else:
            self._advanced_checked.difference_update(codes)
        self._sync_bulk_selection()
        self._rebuild_advanced_models()

    @Slot()
    def clear_advanced_checked(self):
        if self._advanced_checked and not self._bulk_busy:
            self._advanced_checked.clear()
            self._sync_bulk_selection()
            self._rebuild_advanced_models()

    def _load_task_history(self, task, request_id):
        from thlib.environment import env_inst
        info = dict(task.get_info() or {})
        code = str(info.get("code") or "")
        project_code = str(info.get("project_code") or self._application._current_project_code or "")
        self._history_busy = True
        self.advancedChanged.emit()

        def operation():
            import thlib.tactic_classes as tc
            return tc.get_sobjects(
                "sthpw/task", filters=[("code", code)],
                project_code=project_code, limit=1,
                include_snapshots=False, include_info=False,
                include_status_log=True,
            )

        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            self._history_busy = False
            self.advancedChanged.emit()
            return
        worker.result.connect(
            lambda result: self._task_history_loaded(request_id, code, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda _error: self._task_history_failed(request_id),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    def _task_history_loaded(self, request_id, code, result):
        if request_id != self._history_request_id:
            return
        tasks = self._objects(result)
        if tasks:
            self._history_loaded.add(code)
            self.task_store.replace_task(tasks[0])
            row = next((
                index for index, record in enumerate(self.advanced_model._records)
                if record.get("taskCode") == code
            ), -1)
            self._history_busy = False
            if row >= 0:
                self.select_advanced_task(row)
                return
        self._history_busy = False
        self.advancedChanged.emit()

    def _task_history_failed(self, request_id):
        if request_id != self._history_request_id:
            return
        self._history_busy = False
        self.advancedChanged.emit()

    @Slot(str)
    def open_object(self, search_key):
        search_key = str(search_key or "")
        if search_key:
            self._application.open_search_key(search_key)

    @Slot(str, str)
    @Slot(str, str, str)
    def open_notes(self, parent_key, process, task_code=""):
        parent_key = str(parent_key or "")
        process = str(process or "publish")
        task_code = str(task_code or "")
        if task_code:
            self.taskActivated.emit(task_code, parent_key, process)
        self._application._selected_detail_process = process
        if parent_key and parent_key != self.targetSearchKey:
            self._application.open_search_key(parent_key)
        else:
            self._workspace.selection_changed.emit()
        self._application.dock_model.show_panel("notes")

    def _checked_bulk_records(self):
        by_code = {
            str(record.get("taskCode") or ""): record
            for record in self._advanced_raw
        }
        records = []
        for code in self.task_store.task_order:
            if code in self._advanced_checked and code in by_code:
                records.append(by_code[code])
        missing = self._advanced_checked.difference(by_code)
        return records, missing

    def _common_bulk_choices(self, role):
        records, _missing = self._checked_bulk_records()
        if not records:
            return []
        common = None
        first = []
        for index, record in enumerate(records):
            choices = [
                item for item in (record.get(role) or [])
                if item.get("available", True)
            ]
            values = {str(item.get("value") or "") for item in choices}
            common = values if common is None else common.intersection(values)
            if index == 0:
                first = choices
        return [
            dict(item) for item in first
            if str(item.get("value") or "") in (common or set())
        ]

    @staticmethod
    def _mixed_bulk_value(records, key, fallback):
        values = [record.get(key) for record in records]
        if not values:
            return fallback, False
        first = values[0]
        return (first, False) if all(value == first for value in values) else (
            fallback, True
        )

    def _bulk_defaults(self):
        records, _missing = self._checked_bulk_records()
        if not records:
            return {}
        status, status_mixed = self._mixed_bulk_value(records, "status", "")
        assigned, assigned_mixed = self._mixed_bulk_value(
            records, "assigned", ""
        )
        start, start_mixed = self._mixed_bulk_value(records, "start", "")
        end, end_mixed = self._mixed_bulk_value(records, "end", "")
        progress, progress_mixed = self._mixed_bulk_value(
            records, "progress", 0
        )
        description, description_mixed = self._mixed_bulk_value(
            records, "description", ""
        )
        priority, priority_mixed = self._mixed_bulk_value(
            records, "priority", ""
        )
        milestone, milestone_mixed = self._mixed_bulk_value(
            records, "milestoneCode", ""
        )
        supervisor, supervisor_mixed = self._mixed_bulk_value(
            records, "supervisor", ""
        )
        return {
            "status": str(status or ""),
            "statusEnabled": False,
            "statusMixed": status_mixed,
            "statusSet": not status_mixed,
            "assigned": str(assigned or ""),
            "assignedEnabled": False,
            "assignedMixed": assigned_mixed,
            "assignedSet": not assigned_mixed,
            "start": str(start or ""),
            "startEnabled": False,
            "startMixed": start_mixed,
            "startSet": not start_mixed,
            "end": str(end or ""),
            "endEnabled": False,
            "endMixed": end_mixed,
            "endSet": not end_mixed,
            "progress": int(progress or 0),
            "progressEnabled": False,
            "progressMixed": progress_mixed,
            "progressSet": not progress_mixed,
            "description": str(description or ""),
            "descriptionEnabled": False,
            "descriptionMixed": description_mixed,
            "descriptionSet": not description_mixed,
            "priority": str(priority or ""),
            "priorityEnabled": False,
            "priorityMixed": priority_mixed,
            "prioritySet": not priority_mixed,
            "milestoneCode": str(milestone or ""),
            "milestoneCodeEnabled": False,
            "milestoneCodeMixed": milestone_mixed,
            "milestoneCodeSet": not milestone_mixed,
            "supervisor": str(supervisor or ""),
            "supervisorEnabled": False,
            "supervisorMixed": supervisor_mixed,
            "supervisorSet": not supervisor_mixed,
        }

    def _sync_bulk_selection(self, preserve=False):
        previous = dict(self._bulk)
        self._advanced_row_errors.clear()
        self._bulk = self._bulk_defaults()
        if preserve and self._bulk:
            for key in (
                    "status", "assigned", "start", "end", "progress",
                    "description", "priority", "milestoneCode", "supervisor"):
                enabled = "{}Enabled".format(key)
                if previous.get(enabled):
                    self._bulk[key] = previous.get(key)
                    self._bulk[enabled] = True
                    self._bulk["{}Set".format(key)] = bool(
                        previous.get("{}Set".format(key))
                    )
        self.bulkChanged.emit()

    def _bulk_plan(self):
        records, missing = self._checked_bulk_records()
        preview = {
            "targets": len(self._advanced_checked),
            "eligible": 0,
            "updates": 0,
            "unchanged": 0,
            "invalid": 0,
            "skipped": len(missing),
            "creates": 0,
            "fields": 0,
        }
        if not self._bulk:
            return preview, [], {}

        field_map = {
            "status": "status",
            "assigned": "assigned",
            "start": "bid_start_date",
            "end": "bid_end_date",
            "description": "description",
            "priority": "priority",
            "milestoneCode": "milestone_code",
            "supervisor": "supervisor",
        }
        enabled = [
            key for key in field_map
            if self._bulk.get("{}Enabled".format(key))
        ]
        progress_column = self._progress_column()
        if self._bulk.get("progressEnabled"):
            enabled.append("progress")
        preview["fields"] = len(enabled)
        if not enabled:
            return preview, [], {}

        updates = []
        errors = {}
        for record in records:
            code = str(record.get("taskCode") or "")
            task = self._advanced_tasks.get(code)
            if task is None:
                preview["skipped"] += 1
                continue
            try:
                task_search_key = str(task.get_search_key() or "")
            except AttributeError:
                task_search_key = ""
            if not task_search_key:
                preview["skipped"] += 1
                continue
            error = ""
            unset = next((
                key for key in enabled
                if not self._bulk.get("{}Set".format(key))
            ), "")
            if unset:
                error = "Choose a {} value for the mixed selection.".format(
                    "deadline" if unset == "end" else unset
                )
            if "status" in enabled:
                available = {
                    str(item.get("value") or "")
                    for item in record.get("statusChoices") or []
                    if item.get("available", True)
                }
                if str(self._bulk.get("status") or "") not in available:
                    error = "Status is not available for this task pipeline."
            if not error and "assigned" in enabled:
                available = {
                    str(item.get("value") or "")
                    for item in record.get("userChoices") or []
                }
                if str(self._bulk.get("assigned") or "") not in available:
                    error = "Assignee is not available for this task process."
            for key, role, label in (
                ("priority", "priorityChoices", "Priority"),
                ("milestoneCode", "milestoneChoices", "Milestone"),
                ("supervisor", "supervisorChoices", "Supervisor"),
            ):
                if error or key not in enabled:
                    continue
                available = {
                    str(item.get("value") or "")
                    for item in record.get(role) or []
                }
                if str(self._bulk.get(key) or "") not in available:
                    error = "{} is not available for this task.".format(label)

            candidate_start = (
                str(self._bulk.get("start") or "")
                if "start" in enabled else str(record.get("start") or "")
            )
            candidate_end = (
                str(self._bulk.get("end") or "")
                if "end" in enabled else str(record.get("end") or "")
            )
            parsed_start = parse_datetime(candidate_start) if candidate_start else None
            parsed_end = parse_datetime(candidate_end) if candidate_end else None
            if not error and "start" in enabled and candidate_start and not parsed_start:
                error = "Start must use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS."
            if not error and "end" in enabled and candidate_end and not parsed_end:
                error = "Deadline must use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS."
            if not error and parsed_start and parsed_end and parsed_end < parsed_start:
                error = "Deadline cannot be earlier than start."

            progress = None
            if not error and "progress" in enabled:
                if not progress_column:
                    error = "Task progress is not available in this schema."
                else:
                    try:
                        progress = int(self._bulk.get("progress") or 0)
                    except (TypeError, ValueError):
                        error = "Progress must be a number from 0 to 100."
                    if not error and not 0 <= progress <= 100:
                        error = "Progress must be between 0 and 100."
            if error:
                errors[code] = error
                preview["invalid"] += 1
                continue

            changes = {}
            for key in enabled:
                if key == "progress":
                    column = progress_column
                    value = progress
                    current = int(record.get("progress") or 0)
                else:
                    column = field_map[key]
                    value = self._bulk.get(key)
                    current = record.get(key)
                if value != current:
                    changes[column] = value
            if not changes:
                preview["unchanged"] += 1
                continue
            updates.append((code, task, changes))
            preview["eligible"] += 1
        preview["updates"] = preview["eligible"]
        return preview, updates, errors

    @Slot()
    @Slot(str)
    def begin_bulk(self, _process=""):
        if self._bulk_busy or not self._advanced_checked:
            return
        if not self._bulk:
            self._sync_bulk_selection()

    @Slot(str, "QVariant")
    def set_bulk_value(self, key, value):
        if key in self._bulk:
            had_errors = bool(self._advanced_row_errors)
            self._bulk[key] = value
            flag = "{}Set".format(key)
            if flag in self._bulk:
                self._bulk[flag] = True
            self._advanced_error = ""
            self._advanced_row_errors.clear()
            self.bulkChanged.emit()
            if had_errors:
                self._rebuild_advanced_models()

    @Slot(str, bool)
    def set_bulk_enabled(self, key, enabled):
        flag = "{}Enabled".format(key)
        if flag in self._bulk:
            had_errors = bool(self._advanced_row_errors)
            self._bulk[flag] = bool(enabled)
            self._advanced_error = ""
            self._advanced_row_errors.clear()
            self.bulkChanged.emit()
            if had_errors:
                self._rebuild_advanced_models()

    @Slot()
    def cancel_bulk(self):
        if not self._bulk_busy:
            self.clear_advanced_checked()

    @Slot(result=bool)
    def apply_bulk(self):
        if self._bulk_busy or not self._bulk or not self._advanced_checked:
            return False
        if self._advanced_drafts:
            self._advanced_error = (
                "Save or discard row changes before applying a bulk edit."
            )
            self.advancedChanged.emit()
            return False
        preview, edits, errors = self._bulk_plan()
        self._advanced_row_errors.update(errors)
        if not preview["fields"]:
            self._advanced_error = "Enable at least one field to apply."
            self._rebuild_advanced_models()
            return False
        if errors:
            self._advanced_error = (
                "Bulk values are not valid for every checked task."
            )
            self._rebuild_advanced_models()
            return False
        if not edits:
            self._advanced_error = "Checked tasks already have these values."
            self._rebuild_advanced_models()
            return False

        project_code = str(self._application._current_project_code or "")
        request_id = uuid.uuid4().hex
        payload = {
            str(task.get_search_key() or ""): dict(changes)
            for _code, task, changes in edits
        }
        changes_by_code = {
            code: dict(changes) for code, _task, changes in edits
        }
        unchanged_codes = {
            code for code in self._advanced_checked
            if code in self._advanced_tasks and code not in changes_by_code
        }

        def operation():
            import thlib.tactic_classes as tc
            server = tc.server_start(project=project_code)
            server.update_multiple(data=payload, triggers=True)
            return {"completed": list(changes_by_code)}

        from thlib.environment import env_inst
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            self._advanced_error = "Server worker pool is unavailable."
            self.advancedChanged.emit()
            return False
        self._bulk_busy = True
        self._bulk_worker = worker
        self._bulk_request_id = request_id
        self._advanced_error = ""
        self._advanced_row_errors.clear()
        self.bulkChanged.emit()
        self._rebuild_advanced_models()
        worker.result.connect(
            lambda result: self._bulk_finished(
                request_id, result, changes_by_code, unchanged_codes
            ),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._bulk_failed(request_id, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()
        return True

    def _bulk_finished(
            self, request_id, result, changes_by_code, unchanged_codes):
        if request_id != self._bulk_request_id:
            return
        result = dict(result or {})
        completed = {
            str(code) for code in result.get("completed") or []
        }
        for code in completed:
            task = self._advanced_tasks.get(code)
            if task is None:
                continue
            info = task.get_info()
            info.update(changes_by_code.get(code) or {})
            pending = getattr(task, "update_dict", None)
            if isinstance(pending, dict):
                for key in changes_by_code.get(code) or {}:
                    pending.pop(key, None)
        self._advanced_checked.difference_update(completed.union(unchanged_codes))
        self._bulk_busy = False
        self._bulk_worker = None
        self._bulk_request_id = ""
        self._advanced_error = ""
        self._advanced_row_errors.clear()
        self._advanced_raw = self._task_records(
            self.task_store.task_objects()
        )
        self._sync_bulk_selection(preserve=True)
        self._rebuild_advanced_models()

    def _bulk_failed(self, request_id, error):
        if request_id != self._bulk_request_id:
            return
        payload = error[0] if isinstance(error, tuple) and error else error
        stacktrace = ""
        if isinstance(payload, dict):
            stacktrace = str(payload.get("stacktrace") or "")
            payload = payload.get("exception") or payload.get("message") or payload
        self._advanced_error = str(payload or "Bulk task edit failed")
        self._bulk_busy = False
        self._bulk_worker = None
        self._bulk_request_id = ""
        for code in self._advanced_checked:
            self._advanced_row_errors[code] = self._advanced_error
        if self._application.debug_log:
            self._application.debug_log.raise_error(
                payload, stacktrace=stacktrace, group="tasks/bulk"
            )
        self.bulkChanged.emit()
        self._rebuild_advanced_models()
