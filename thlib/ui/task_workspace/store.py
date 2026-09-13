from __future__ import annotations

import copy
import json
import uuid

from PySide6.QtCore import QObject, Signal

from thlib.ui.workspace_models.records import RecordListModel


TASK_ROLES = (
    "taskCode", "searchKey", "parentKey", "parentTitle", "parentSearchType",
    "parentSearchTypeLabel", "parentCode", "parentPreviewUrl", "project",
    "process", "processLabel",
    "processChoices", "isNew",
    "processColor", "processType", "taskPipeline", "context", "status",
    "statusLabel", "statusColor",
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


def _resolve_target_from_search_key(tc, target_key, project_code):
    """Resolve either TACTIC search-key format to its native sObject."""
    target_key = str(target_key or "").strip()
    if not target_key:
        return None
    if target_key.startswith("skey://"):
        parsed = tc.parce_skey(target_key)
        if not isinstance(parsed, tuple) or len(parsed) != 2:
            return None
        return parsed[1]
    if "?" not in target_key or not (
            "code=" in target_key or "id=" in target_key):
        return None

    try:
        parsed = tc.split_search_key(target_key)
    except (AssertionError, TypeError, ValueError):
        return None
    if not isinstance(parsed, dict):
        return None
    identifier_value = parsed.get("asset_code")
    if identifier_value in (None, ""):
        return None
    identifier = (
        "id" if "?id=" in target_key or "&id=" in target_key else "code"
    )
    values = _object_values(tc.get_sobjects(
        target_key.partition("?")[0],
        filters=[(identifier, "=", identifier_value)],
        project_code=parsed.get("project_code") or project_code,
        limit=1,
    ))
    return values[0] if values else None


class TaskWorkspaceStore(QObject):
    """Canonical Python-owned state shared by detailed task presentations."""

    changed = Signal()
    sourceChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = RecordListModel(TASK_ROLES, identity_role="taskCode")
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
        self.facets = {}
        self.page_codes = set()
        self.server_filtered = False

    @staticmethod
    def _target_token(target, fallback=""):
        if target is None:
            return str(fallback or "")
        if isinstance(target, str):
            return target
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
            self.facets = {}
            self.page_codes.clear()
            self.server_filtered = False
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
        self.facets = {}
        self.page_codes.clear()
        self.server_filtered = False
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

    def remove_tasks(self, task_codes):
        codes = {str(code or "") for code in task_codes if code}
        removed = codes.intersection(self.tasks)
        if not removed:
            return set()
        for code in removed:
            self.tasks.pop(code, None)
            self.assignee_hints.pop(code, None)
        self.task_order = [
            code for code in self.task_order if code not in removed
        ]
        self.records = [
            record for record in self.records
            if str(record.get("taskCode") or "") not in removed
        ]
        self.offset = max(0, self.offset - len(removed))
        if self.total_count >= 0:
            self.total_count = max(0, self.total_count - len(removed))
        self.sourceChanged.emit()
        self.changed.emit()
        return removed

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
        self.server_filtered = bool(page.get("serverFiltered"))
        codes = {_task_code(task) for task in tasks or []}
        self.page_codes = self.page_codes.union(codes) if append else codes
        self.facets = dict(page.get("facets") or {})
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
            offset=0, limit=500, bypass_cache=False, query=None):
        from thlib import server_cache

        target_identity = cls._target_token(target, target_key)
        target_identities = sorted(
            cls._target_token(item) for item in (targets or [])
        )
        cache_key = json.dumps(
            {
                "scope": str(scope or "object"),
                "login": str(login or ""),
                "target": target_identity,
                "targets": target_identities,
                "offset": int(offset or 0),
                "limit": int(limit or 500),
                "query": dict(query or {}),
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        if bypass_cache:
            server_cache.invalidate_domains(("tasks",), project_code)
        cache_project = cls._cache_project(project_code)
        cache_token = (
            server_cache.token("tasks", project_code)
            if cache_project is not None else None
        )
        cached = (
            server_cache.read_entry(
                "tasks", cache_key, project_code,
            )
            if cache_token is not None and not bypass_cache else None
        )
        if isinstance(cached, dict):
            result = cls._hydrate_cache_payload(cached, cache_project)
            result.setdefault("page", {})["queryCount"] = 0
            result["page"]["cacheHit"] = True
            return result

        result = cls._load_scope_server(
            scope, login, project_code, target, target_key, targets,
            offset=offset, limit=limit, query=query,
        )
        if cache_token is not None:
            server_cache.write_entry(
                "tasks", cache_key, cls._cache_payload(result), project_code,
                expected_token=cache_token,
            )
        result.setdefault("page", {})["cacheHit"] = False
        return result

    @staticmethod
    def _object_info(value):
        if value is None:
            return None
        try:
            return copy.deepcopy(dict(value.get_info() or {}))
        except (AttributeError, TypeError, ValueError):
            return None

    @classmethod
    def _cache_payload(cls, result):
        result = dict(result or {})
        return {
            "tasks": [
                info for info in (
                    cls._object_info(item) for item in result.get("tasks") or []
                ) if info is not None
            ],
            "parents": [
                info for info in (
                    cls._object_info(item) for item in result.get("parents") or []
                ) if info is not None
            ],
            "target": cls._object_info(result.get("target")),
            "page": copy.deepcopy(dict(result.get("page") or {})),
        }

    @staticmethod
    def _cache_project(project_code):
        from thlib.environment import env_inst

        try:
            return env_inst.get_project_by_code(project_code)
        except (AttributeError, TypeError):
            return None

    @staticmethod
    def _hydrate_cache_payload(payload, project):
        import thlib.tactic_classes as tc

        tasks = []
        for info in copy.deepcopy(list(payload.get("tasks") or [])):
            task = tc.Task(info, project)
            task.set_notes_count(
                str(info.get("process") or "publish"),
                int(info.get("__notes_count__") or 0),
            )
            tasks.append(task)
        parents = [
            tc.SObject(info, project)
            for info in copy.deepcopy(list(payload.get("parents") or []))
        ]
        target_info = copy.deepcopy(payload.get("target"))
        target = tc.SObject(target_info, project) if target_info else None
        return {
            "tasks": tasks,
            "parents": parents,
            "target": target,
            "page": copy.deepcopy(dict(payload.get("page") or {})),
        }

    @classmethod
    def _load_scope_server(
            cls, scope, login, project_code, target, target_key, targets,
            offset=0, limit=500, query=None):
        import thlib.tactic_classes as tc

        filters = [("project_code", project_code)]
        if scope == "object" and (query or {}).get("scopeProcess"):
            filters.append(("process", query["scopeProcess"]))
        resolved_targets = []
        if scope == "object":
            if target is None:
                if not str(target_key or "").strip():
                    return {
                        "tasks": [], "parents": [], "target": None,
                        "page": {
                            "offset": 0, "loaded": 0, "hasMore": False,
                            "total": 0, "queryCount": 0,
                        },
                    }
                target = _resolve_target_from_search_key(
                    tc, target_key, project_code
                )
                if target is None:
                    raise ValueError(
                        "Unable to resolve the selected sObject search key."
                    )
            resolved_targets = [target]
        elif scope == "multiple":
            for item in targets or []:
                if isinstance(item, str):
                    item = _resolve_target_from_search_key(
                        tc, item, project_code
                    )
                if item is not None:
                    resolved_targets.append(item)
        if scope in {"object", "multiple"}:
            if not resolved_targets:
                return {
                    "tasks": [], "parents": [], "target": None,
                    "page": {"offset": 0, "loaded": 0, "hasMore": False,
                             "total": 0, "queryCount": 0},
                }
            server = tc.server_start(project=project_code)
            filters.append("begin")
            for item in resolved_targets:
                filters.extend([
                    "begin",
                    ("search_type", server.build_search_type(
                        item.get_stype().get_code(), project_code)),
                    ("search_code", item.get_code()),
                    "and",
                ])
            filters.append("or")
        elif scope == "user" and login:
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
            limit=limit, offset=offset, **({"query": query} if query else {}),
        )
        tasks = list(result.get("tasks") or [])
        parents = resolved_targets or list(result.get("parents") or [])
        total = result.get("total")
        return {
            "tasks": tasks, "parents": parents,
            "target": target if scope == "object" else None,
            "page": {
                "offset": int(offset or 0),
                "loaded": len(tasks),
                "hasMore": bool(
                    int(offset or 0) + len(tasks) < int(total)
                    if total not in (None, "")
                    else limit and len(tasks) >= limit
                ),
                "total": total,
                "facets": dict(result.get("facets") or {}),
                "queryCount": 1,
            },
        }
