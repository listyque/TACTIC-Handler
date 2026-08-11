from __future__ import annotations

import uuid

from PySide6.QtCore import QObject, Signal

from modern_ui.workspace_models.records import RecordListModel


TASK_ROLES = (
    "taskCode", "searchKey", "parentKey", "parentTitle", "parentSearchType",
    "parentCode", "parentPreviewUrl", "project", "process", "processLabel",
    "processChoices", "isNew",
    "processColor", "processType", "taskPipeline", "context", "status", "statusColor",
    "statusChoices", "assigned", "assignedLabel", "assignedAvatar",
    "assignedChoiceIndex",
    "supervisor", "supervisorLabel", "supervisorAvatar", "supervisorChoices",
    "priority", "priorityLabel", "priorityColor", "priorityChoices",
    "milestoneCode", "milestoneLabel", "milestoneDueDate", "milestoneChoices",
    "dependencyId", "userChoices", "start", "end", "actualStart",
    "actualEnd", "dueState", "progress", "description",
    "plannedHours", "loggedHours", "approvedHours", "pendingHours",
    "remainingHours", "overPlanHours", "hoursLabel",
    "notes", "snapshotCount", "snapshotFileCount", "latestVersion",
    "attachmentCount",
    "timestamp", "group", "groupKey", "groupCount", "groupFirst",
    "groupCollapsed", "groupColor", "selected", "checked", "dirty",
    "loading", "error", "conflict",
)


def _plain_search_type(value):
    return str(value or "").removeprefix("skey://").split("?", 1)[0]


def _task_code(task):
    try:
        info = task.get_info() or {}
    except AttributeError:
        return ""
    return str(info.get("code") or "")


def _object_values(result):
    values = result[0] if isinstance(result, tuple) else result
    if isinstance(values, dict):
        return list(values.values())
    return list(values or [])


class TaskWorkspaceStore(QObject):
    """Canonical Python-owned state shared by detailed task presentations."""

    changed = Signal()
    sourceChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = RecordListModel(TASK_ROLES)
        self.scope = "object"
        self.user = ""
        self.target = None
        self.target_key = ""
        self.target_title = ""
        self.targets = []
        self.visible = False
        self.busy = False
        self.error = ""
        self.request_id = ""
        self.worker = None
        self.request_append = False

        self.tasks = {}
        self.task_order = []
        self.assignee_hints = {}
        self.parents = {}
        self._parents_by_code = {}
        self.records = []

        self.page_size = 500
        self.offset = 0
        self.has_more = False
        self.total_count = -1

    @staticmethod
    def _target_token(target, fallback=""):
        if target is None:
            return str(fallback or "")
        try:
            return str(target.get_search_key() or fallback or "")
        except AttributeError:
            return str(fallback or "")

    @staticmethod
    def parent_identity_from_task_info(info):
        return (
            _plain_search_type(info.get("search_type")),
            str(info.get("project_code") or ""),
            str(info.get("search_code") or ""),
        )

    @staticmethod
    def parent_identity(parent):
        try:
            info = dict(parent.get_info() or {})
        except AttributeError:
            info = {}
        try:
            search_type = parent.get_plain_search_type()
        except AttributeError:
            try:
                search_type = parent.get_search_key()
            except AttributeError:
                search_type = info.get("__search_type__") or info.get("search_type")
        try:
            code = parent.get_code()
        except AttributeError:
            code = info.get("code")
        project = str(info.get("project_code") or "")
        if not project:
            try:
                project = str(parent.get_project().get_code() or "")
            except AttributeError:
                project = ""
        return _plain_search_type(search_type), project, str(code or "")

    def set_scope(
            self, scope, user="", target=None, target_key="",
            target_title="", targets=None):
        scope = str(scope or "object")
        user = str(user or "")
        target_key = str(target_key or "")
        targets = list(targets or [])
        old_identity = (
            self.scope, self.user,
            self._target_token(self.target, self.target_key),
            tuple(self._target_token(item) for item in self.targets),
        )
        new_identity = (
            scope, user, self._target_token(target, target_key),
            tuple(self._target_token(item) for item in targets),
        )
        if old_identity != new_identity:
            self.invalidate_requests()
        self.scope = scope
        self.user = user
        self.target = target
        self.target_key = target_key
        self.target_title = str(target_title or "")
        self.targets = targets
        self.changed.emit()

    def begin_load(self, append=False):
        if self.busy:
            return ""
        self.request_id = uuid.uuid4().hex
        self.request_append = bool(append)
        self.busy = True
        self.error = ""
        self.changed.emit()
        return self.request_id

    def accepts(self, request_id):
        return bool(request_id) and request_id == self.request_id

    def finish_load(self):
        self.busy = False
        self.worker = None
        self.request_append = False
        self.changed.emit()

    def fail_load(self, request_id, message):
        if not self.accepts(request_id):
            return False
        self.error = str(message or "Unable to load tasks")
        self.finish_load()
        return True

    def invalidate_requests(self):
        self.request_id = uuid.uuid4().hex
        self.busy = False
        self.worker = None
        self.request_append = False

    def clear(self):
        self.invalidate_requests()
        self.tasks.clear()
        self.task_order.clear()
        self.assignee_hints.clear()
        self.parents.clear()
        self._parents_by_code.clear()
        self.records.clear()
        self.model.clear()
        self.offset = 0
        self.has_more = False
        self.total_count = -1
        self.error = ""
        self.sourceChanged.emit()
        self.changed.emit()

    def set_tasks(self, tasks, append=False):
        if not append:
            self.tasks.clear()
            self.task_order.clear()
        for task in tasks or []:
            code = _task_code(task)
            if not code:
                continue
            if code not in self.tasks:
                self.task_order.append(code)
            self.tasks[code] = task

    def replace_task(self, task):
        code = _task_code(task)
        if not code:
            return False
        if code not in self.tasks:
            self.task_order.append(code)
        self.tasks[code] = task
        return True

    def task_objects(self):
        return [self.tasks[code] for code in self.task_order if code in self.tasks]

    def assignee_for_task_info(self, info):
        """Return the task assignee, including a query-scope identity hint.

        A user-scope query is filtered by ``sthpw/task.assigned`` on the
        server.  Some TACTIC responses omit that column from the serialized
        row even though the row matched the filter.  Keep that proven query
        identity outside the native task object instead of presenting the
        task as unassigned.
        """
        info = dict(info or {})
        assigned = str(info.get("assigned") or "").strip()
        if assigned:
            return assigned
        return str(
            self.assignee_hints.get(str(info.get("code") or ""))
            or info.get("login") or ""
        ).strip()

    def set_parents(self, parents, append=False):
        if isinstance(parents, dict):
            parents = list(parents.values())
        if not append:
            self.parents.clear()
            self._parents_by_code.clear()
        for parent in parents or []:
            identity = self.parent_identity(parent)
            if not identity[2]:
                continue
            self.parents[identity] = parent
            self._parents_by_code.setdefault(identity[2], [])
            values = self._parents_by_code[identity[2]]
            if parent not in values:
                values.append(parent)

    def parent_for_task(self, task):
        try:
            info = dict(task.get_info() or {})
        except AttributeError:
            return None
        return self.parent_for_task_info(info)

    def parent_for_task_info(self, info):
        identity = self.parent_identity_from_task_info(info)
        parent = self.parents.get(identity)
        if parent is not None:
            return parent

        search_type, project, code = identity
        candidates = list(self._parents_by_code.get(code) or [])
        if search_type:
            typed = [
                item for item in candidates
                if self.parent_identity(item)[0] == search_type
            ]
            if project:
                project_matches = [
                    item for item in typed
                    if self.parent_identity(item)[1] in {"", project}
                ]
                if len(project_matches) == 1:
                    return project_matches[0]
            if len(typed) == 1:
                return typed[0]
        return candidates[0] if len(candidates) == 1 else None

    def set_records(self, records):
        self.records = [dict(record) for record in records]
        self.sourceChanged.emit()

    def apply_source(self, tasks, parents, page=None, append=False):
        if not append:
            self.assignee_hints.clear()
        if self.scope == "user" and self.user:
            for task in tasks or []:
                try:
                    info = dict(task.get_info() or {})
                except AttributeError:
                    info = {}
                code = str(info.get("code") or "")
                if code and not str(info.get("assigned") or "").strip():
                    self.assignee_hints[code] = self.user
        self.set_tasks(tasks, append=append)
        self.set_parents(parents, append=append)
        page = dict(page or {})
        loaded = int(page.get("loaded") or len(tasks or []))
        if append:
            self.offset += loaded
        else:
            self.offset = loaded
        self.has_more = bool(page.get("hasMore", False))
        total = page.get("total")
        self.total_count = int(total) if total not in (None, "") else -1

    @classmethod
    def load_scope(
            cls, scope, login, project_code, target, target_key, targets,
            offset=0, limit=500):
        import thlib.tactic_classes as tc

        if scope == "object":
            if target is None:
                _data, target = tc.parce_skey(target_key)
            tasks = _object_values(
                target.get_tasks_sobjects(include_status_log=False)
            )
            return {
                "tasks": tasks, "parents": [target], "target": target,
                "page": {
                    "offset": 0, "loaded": len(tasks), "hasMore": False,
                    "total": len(tasks), "queryCount": 1,
                },
            }
        if scope == "multiple":
            grouped = tc.SObject.get_multiple_tasks_sobjects(targets) or {}
            tasks = []
            seen = set()
            for values in grouped.values():
                for task in values:
                    code = _task_code(task)
                    if code and code not in seen:
                        tasks.append(task)
                        seen.add(code)
            return {
                "tasks": tasks, "parents": list(targets), "target": None,
                "page": {
                    "offset": 0, "loaded": len(tasks), "hasMore": False,
                    "total": len(tasks), "queryCount": 1,
                },
            }

        filters = [("project_code", project_code)]
        if scope == "user" and login:
            filters.append(("assigned", login))
        elif scope == "search_type" and target_key:
            parent_search_type = tc.server_start(
                project=project_code
            ).build_search_type(
                _plain_search_type(target_key), project_code
            )
            filters.append(("search_type", parent_search_type))
        elif scope == "team":
            from thlib.environment import env_inst

            current_login = env_inst.get_current_login_object()
            getter = getattr(current_login, "get_all_login_groups", None)
            if not callable(getter):
                getter = getattr(current_login, "get_login_groups", None)
            groups = getter() or [] if callable(getter) else []
            group = next((
                item for item in groups
                if login in {
                    str(item.get_code() or ""),
                    str(item.get_login_group() or ""),
                }
            ), None)
            members = group.get_logins() if group else []
            logins = sorted({
                str(item.get_login() or "") for item in members
                if item.get_login()
            })
            if not logins:
                return {
                    "tasks": [], "parents": [], "target": None,
                    "page": {
                        "offset": int(offset or 0), "loaded": 0,
                        "hasMore": False, "total": 0, "queryCount": 1,
                    },
                }
            filters.append(("assigned", "in", "|".join(logins)))
        result = tc.get_task_workspace_page(
            filters, ["bid_end_date", "timestamp desc"], project_code,
            limit=limit, offset=offset,
        )
        tasks = list(result.get("tasks") or [])
        parents = list(result.get("parents") or [])
        total = result.get("total")
        return {
            "tasks": tasks, "parents": parents, "target": None,
            "page": {
                "offset": int(offset or 0),
                "loaded": len(tasks),
                "hasMore": bool(
                    int(offset or 0) + len(tasks) < int(total)
                    if total not in (None, "")
                    else limit and len(tasks) >= limit
                ),
                "total": total,
                "queryCount": 1,
            },
        }
