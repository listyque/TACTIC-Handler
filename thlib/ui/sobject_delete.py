"""Dependency-aware sObject deletion workflow."""

from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import parse_qsl, urlparse

from PySide6.QtCore import QObject, Property, Signal, Slot

from thlib.ui.workspace_models.records import RecordListModel


DEFAULT_DEPENDENCY_TYPES = frozenset({
    "sthpw/snapshot",
    "sthpw/file",
    "sthpw/note",
    "sthpw/task",
    "sthpw/status_log",
})

DEPENDENCY_ROLES = (
    "searchType", "searchTypeTitle", "iconName", "count",
    "checked", "defaultChecked", "expanded", "items",
)


class _SearchKeyDeleteTarget:
    """QML-safe reference that enters the native sObject delete workflow."""

    def __init__(
            self,
            search_key: str,
            title: str = "",
            project_code: str = "",
            search_type: str = "",
    ) -> None:
        value = str(search_key or "").strip()
        if value.startswith("skey://"):
            value = value[len("skey://"):]
        parsed = urlparse(value)
        query = dict(parse_qsl(parsed.query))
        self._search_key = value
        self._search_type = str(
            search_type or parsed.path or value.split("?", 1)[0]
        ).strip("/")
        self._project_code = str(
            project_code or query.get("project") or ""
        )
        fallback = (
            query.get("code") or query.get("id")
            or self._search_type or value
        )
        self._title = str(title or fallback)
        self.info = {
            "title": self._title,
            "name": self._title,
            "code": str(query.get("code") or query.get("id") or ""),
            "project_code": self._project_code,
        }

    def get_search_key(self) -> str:
        return self._search_key

    def get_title(self, pretty=False) -> str:
        return self._title

    def get_info(self) -> dict:
        return dict(self.info)

    def get_plain_search_type(self) -> str:
        return self._search_type

    def get_stype(self):
        from thlib.environment import env_inst

        if not self._search_type:
            return None
        return env_inst.get_stype_by_code(
            self._search_type,
            project_code=self._project_code,
        )


def _search_key(source) -> str:
    try:
        return str(source.get_search_key() or "")
    except (AttributeError, KeyError, TypeError):
        return ""


def _title(source) -> str:
    try:
        value = source.get_title()
    except (AttributeError, KeyError, TypeError):
        value = ""
    if value:
        return str(value)
    info = dict(getattr(source, "info", None) or {})
    return str(
        info.get("name") or info.get("title")
        or info.get("code") or _search_key(source)
    )


def _source_info(source) -> dict:
    try:
        info = source.get_info()
    except (AttributeError, KeyError, TypeError):
        info = getattr(source, "info", None)
    return dict(info or {})


def _status_log_transition(info: Mapping) -> str:
    from_status = str(info.get("from_status") or "").strip()
    to_status = str(info.get("to_status") or "").strip()
    if from_status and to_status and from_status != to_status:
        return f"{from_status} → {to_status}"
    return to_status or from_status or str(info.get("status") or "").strip()


def _dependency_title(source) -> str:
    info = _source_info(source)
    if _plain_search_type(source).removeprefix("skey://") == "sthpw/status_log":
        transition = _status_log_transition(info)
        if transition:
            return transition
    for key in (
        "file_name", "filename", "name", "title",
        "description", "note", "process", "context", "status",
    ):
        value = str(info.get(key) or "").strip()
        if value:
            return value
    try:
        value = source.get_title(pretty=True)
    except TypeError:
        try:
            value = source.get_title()
        except (AttributeError, KeyError, TypeError):
            value = ""
    except (AttributeError, KeyError):
        value = ""
    if value:
        return str(value)
    return str(
        info.get("name") or info.get("title")
        or info.get("code") or _search_key(source)
    )


def _dependency_details(source, title: str) -> str:
    info = _source_info(source)
    if _plain_search_type(source).removeprefix("skey://") == "sthpw/status_log":
        details = []
        for key in ("process", "context", "login", "timestamp"):
            value = str(info.get(key) or "").strip()
            if value and value != title and value not in details:
                details.append(value)
        return " · ".join(details)
    details = []
    for key in (
        "description", "note", "context", "process",
        "status", "assigned", "login", "timestamp",
    ):
        value = str(info.get(key) or "").strip()
        if value and value != title and value not in details:
            details.append(value)
        if len(details) == 2:
            break
    return " · ".join(details)


def _stype_title(stype, search_type: str) -> str:
    try:
        value = stype.get_pretty_name()
    except (AttributeError, KeyError, TypeError):
        value = ""
    return str(value or search_type)


def _dependency_icon(search_type: str) -> str:
    return {
        "sthpw/file": "file",
        "sthpw/snapshot": "snapshot",
        "sthpw/note": "notes",
        "sthpw/task": "tasks",
        "sthpw/status_log": "history",
    }.get(search_type, "sobject")


def _plain_search_type(source) -> str:
    try:
        value = source.get_plain_search_type()
    except (AttributeError, KeyError, TypeError):
        value = ""
    if value:
        return str(value)
    return _search_key(source).split("?", 1)[0]


def _dependency_values(value) -> list:
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, (list, tuple)):
        result = []
        for item in value:
            if isinstance(item, Mapping):
                result.extend(item.values())
            elif isinstance(item, (list, tuple)):
                result.extend(item)
            else:
                result.append(item)
        return result
    return []


def _result_sobjects(result) -> list:
    values = result[0] if isinstance(result, tuple) else result
    if isinstance(values, Mapping):
        return list(values.values())
    return list(values or [])


def _task_parent_identity(source) -> tuple[str, str, str]:
    info = _source_info(source)
    search_type = str(info.get("search_type") or "")
    search_type = search_type.removeprefix("skey://").split("?", 1)[0]
    return (
        search_type,
        str(info.get("project_code") or ""),
        str(info.get("search_code") or ""),
    )


def _task_note_dependencies(sources, parent_sources=None) -> dict:
    """Find process Notes through each Task's native parent SObject."""
    import thlib.tactic_classes as tc

    provided = dict(parent_sources or {})
    parent_cache = {}
    notes_cache = {}
    result = {}

    for source in sources or []:
        if _plain_search_type(source).removeprefix("skey://") != "sthpw/task":
            continue
        info = _source_info(source)
        process = str(info.get("process") or "")
        if not process:
            continue
        identity = _task_parent_identity(source)
        parent = provided.get(_search_key(source))
        if parent is None and not all(identity):
            continue

        if parent is None:
            if identity not in parent_cache:
                search_type, project_code, search_code = identity
                queried = tc.get_sobjects(
                    search_type,
                    filters=[("code", search_code)],
                    project_code=project_code,
                    limit=1,
                    include_snapshots=False,
                    include_info=False,
                )
                values = _result_sobjects(queried)
                parent_cache[identity] = values[0] if values else None
            parent = parent_cache.get(identity)
        if parent is None:
            continue

        parent_key = _search_key(parent) or "|".join(identity)
        cache_key = (parent_key, process)
        if cache_key not in notes_cache:
            notes_cache[cache_key] = _result_sobjects(
                parent.get_notes_sobjects(process)
            )
        for note in notes_cache[cache_key]:
            search_key = _search_key(note)
            if search_key:
                result[search_key] = note
    return result


def dependency_records(
        sources,
        dependencies,
        stype_resolver,
) -> list[dict]:
    """Build the same groups and default checks as deleteSobjectWidget."""
    roots = [source for source in sources or [] if _search_key(source)]
    if not roots:
        return []
    root_keys = {_search_key(source) for source in roots}
    default_types = set(DEFAULT_DEPENDENCY_TYPES)
    try:
        parent_stype = roots[0].get_stype()
    except (AttributeError, KeyError, TypeError):
        parent_stype = None
    try:
        schema = parent_stype.get_schema() if parent_stype else None
    except (AttributeError, KeyError, TypeError):
        schema = None
    try:
        parent_code = str(parent_stype.get_code() or "")
    except (AttributeError, KeyError, TypeError):
        parent_code = ""

    records = []
    for raw_search_type, raw_values in (dependencies or {}).items():
        search_type = str(raw_search_type or "")
        if not search_type:
            continue
        try:
            stype = stype_resolver(search_type)
        except (AttributeError, KeyError, TypeError):
            stype = None
        if schema is not None and stype is not None and parent_code:
            try:
                child = schema.get_child(stype.get_code(), parent_code)
            except (AttributeError, KeyError, TypeError):
                child = None
            if child and child.get("relationship") == "instance":
                instance_type = str(child.get("instance_type") or "")
                if instance_type:
                    default_types.add(instance_type)

        items = []
        seen = set()
        for source in _dependency_values(raw_values):
            search_key = _search_key(source)
            if not search_key or search_key in root_keys or search_key in seen:
                continue
            seen.add(search_key)
            title = _dependency_title(source)
            items.append({
                "title": title,
                "details": _dependency_details(source, title),
                "searchKey": search_key,
            })
        if not items:
            continue
        checked = search_type in default_types
        records.append({
            "searchType": search_type,
            "searchTypeTitle": _stype_title(stype, search_type),
            "iconName": _dependency_icon(search_type),
            "count": len(items),
            "checked": checked,
            "defaultChecked": checked,
            # Ui_collapsableWidget(state=True) starts collapsed in legacy.
            "expanded": False,
            "items": items,
        })
    return records


class SObjectDeleteController(QObject):
    """Own dependency discovery and deletion outside the QML UI thread."""

    stateChanged = Signal()
    deletionFinished = Signal(str)

    def __init__(self, application, debug_log=None, parent=None):
        super().__init__(parent)
        self._application = application
        self._debug_log = debug_log
        self.model = RecordListModel(DEPENDENCY_ROLES)
        self._sources = []
        self._parent_sources = {}
        self._context = "items"
        self._busy = False
        self._deleting = False
        self._ready = False
        self._error = ""
        self._generation = 0
        self._worker = None
        self._script_triggers = None
        self._trigger_payload = {}

    def attach_script_triggers(self, triggers) -> None:
        self._script_triggers = triggers

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(bool, notify=stateChanged)
    def deleting(self) -> bool:
        return self._deleting

    @Property(bool, notify=stateChanged)
    def ready(self) -> bool:
        return self._ready

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error

    @Property(int, notify=stateChanged)
    def targetCount(self) -> int:
        return len(self._sources)

    @Property("QVariantList", notify=stateChanged)
    def targets(self) -> list[dict]:
        return [
            {"title": _title(source), "searchKey": _search_key(source)}
            for source in self._sources[:16]
        ]

    @Property(int, notify=stateChanged)
    def remainingTargetCount(self) -> int:
        return max(0, len(self._sources) - 16)

    @Property(int, notify=stateChanged)
    def dependencyCount(self) -> int:
        return sum(
            int(record.get("count") or 0)
            for record in self.model._records
        )

    @Property(int, notify=stateChanged)
    def selectedDependencyCount(self) -> int:
        return sum(
            int(record.get("count") or 0)
            for record in self.model._records
            if record.get("checked")
        )

    def begin(
            self, sources, context="items", parent_sources=None) -> bool:
        unique = []
        seen = set()
        for source in sources or []:
            search_key = _search_key(source)
            if not search_key or search_key in seen:
                continue
            seen.add(search_key)
            unique.append(source)
        if not unique:
            self._application._notify("Selected item is no longer available")
            return False
        self._generation += 1
        generation = self._generation
        self._sources = unique
        self._parent_sources = {
            str(search_key or ""): parent
            for search_key, parent in dict(parent_sources or {}).items()
            if search_key and parent is not None
        }
        self._context = str(context or "items")
        self._busy = True
        self._deleting = False
        self._ready = False
        self._error = ""
        self.model.clear()
        self.stateChanged.emit()
        self._application.window_model.show_window("delete_sobject")
        try:
            from thlib.environment import env_inst
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            worker = env_inst.server_pool.add_task(
                self._discover_dependencies, tuple(unique),
                dict(self._parent_sources)
            )
            self._worker = worker
            worker.result.connect(
                lambda result, current=generation:
                self._dependencies_ready(current, result)
            )
            worker.error.connect(
                lambda error, current=generation:
                self._operation_failed(current, error, "discover")
            )
            worker.start()
        except Exception as error:
            self._operation_failed(generation, error, "discover")
        return True

    def begin_search_keys(self, targets, context="items") -> bool:
        """Open the same dependency review for records outside Search views."""
        sources = []
        for target in targets or []:
            if isinstance(target, Mapping):
                search_key = str(target.get("searchKey") or "")
                title = str(target.get("title") or "")
                project_code = str(target.get("projectCode") or "")
                search_type = str(target.get("searchType") or "")
            else:
                search_key = str(target or "")
                title = ""
                project_code = ""
                search_type = ""
            if not search_key.strip():
                continue
            sources.append(_SearchKeyDeleteTarget(
                search_key,
                title=title,
                project_code=project_code,
                search_type=search_type,
            ))
        return self.begin(sources, context)

    @staticmethod
    def _discover_dependencies(sources, parent_sources=None) -> list[dict]:
        import thlib.tactic_classes as tc
        from thlib.environment import env_inst

        search_keys = [_search_key(source) for source in sources]
        dependencies = dict(tc.get_all_dependency(search_keys) or {})
        task_notes = _task_note_dependencies(sources, parent_sources)
        if task_notes:
            notes = {
                _search_key(note): note
                for note in _dependency_values(
                    dependencies.get("sthpw/note")
                )
                if _search_key(note)
            }
            notes.update(task_notes)
            dependencies["sthpw/note"] = notes
        try:
            parent_stype = sources[0].get_stype()
            project = parent_stype.get_project()
            project_code = str(project.get_code() or "")
        except (AttributeError, KeyError, TypeError):
            project_code = ""

        def resolve(search_type):
            if search_type.startswith("sthpw"):
                return env_inst.get_stype_by_code(search_type)
            return env_inst.get_stype_by_code(
                search_type, project_code=project_code
            )

        records = dependency_records(sources, dependencies, resolve)
        explicit_note_keys = set(task_notes)
        for record in records:
            if record.get("searchType") == "sthpw/note":
                record["explicitSearchKeys"] = [
                    item["searchKey"] for item in record.get("items") or []
                    if item.get("searchKey") in explicit_note_keys
                ]
        return records

    def _dependencies_ready(self, generation: int, records) -> None:
        if generation != self._generation:
            return
        self._worker = None
        self.model.reset_records(records or [])
        self._busy = False
        self._ready = True
        self._error = ""
        self.stateChanged.emit()

    @Slot(int, bool)
    def set_group_checked(self, row: int, checked: bool) -> None:
        if self.model.update_record(row, {"checked": bool(checked)}):
            self.stateChanged.emit()

    @Slot(int)
    def toggle_group(self, row: int) -> None:
        record = self.model.get(row)
        if not record:
            return
        self.model.update_record(
            row, {"expanded": not bool(record.get("expanded"))}
        )

    def _selected_search_types(self) -> list[str]:
        selected = [
            str(record.get("searchType") or "")
            for record in self.model._records
            if record.get("checked") and record.get("searchType")
        ]
        if not selected and self._sources:
            selected.append(_plain_search_type(self._sources[0]))
        return selected

    def _selected_explicit_search_keys(self) -> list[str]:
        selected = []
        seen = set()
        for record in self.model._records:
            if not record.get("checked"):
                continue
            for search_key in record.get("explicitSearchKeys") or []:
                search_key = str(search_key or "")
                if search_key and search_key not in seen:
                    selected.append(search_key)
                    seen.add(search_key)
        return selected

    @Slot()
    def confirm_delete(self) -> None:
        if self._busy or self._deleting or not self._ready:
            return
        search_keys = [_search_key(source) for source in self._sources]
        for search_key in self._selected_explicit_search_keys():
            if search_key not in search_keys:
                search_keys.append(search_key)
        dependency_data = {
            "search_types": self._selected_search_types(),
        }
        event = (
            "task.delete"
            if self._sources and all(
                _plain_search_type(source) == "sthpw/task"
                for source in self._sources
            )
            else "object.delete"
        )
        self._trigger_payload = {
            "targets": [{
                "search_key": search_key,
                "search_type": search_key.removeprefix("skey://").split("?", 1)[0],
            } for search_key in search_keys],
            "dependency_search_types": list(dependency_data["search_types"]),
        }
        triggers = self._script_triggers
        if triggers is not None:
            self._deleting = True
            self._error = ""
            self.stateChanged.emit()

            def start(success: bool, error: str) -> None:
                if not success:
                    self._deleting = False
                    self._error = str(error or "Script trigger failed")
                    self.stateChanged.emit()
                    return
                self._confirm_delete_now(search_keys, dependency_data)

            triggers.run_before(event, self._trigger_payload, start)
            return
        self._confirm_delete_now(search_keys, dependency_data)

    def _confirm_delete_now(
        self, search_keys: list[str], dependency_data: dict,
    ) -> None:
        self._generation += 1
        generation = self._generation
        self._deleting = True
        self._error = ""
        self.stateChanged.emit()
        try:
            import thlib.tactic_classes as tc
            from thlib.environment import env_inst
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            def operation():
                from thlib import server_cache

                result = tc.delete_sobjects(search_keys, dependency_data)
                project_codes = set()
                for search_key in search_keys:
                    try:
                        project_codes.add(str(
                            tc.split_search_key(search_key).get(
                                "project_code"
                            ) or ""
                        ))
                    except (AttributeError, KeyError, TypeError, ValueError):
                        project_codes.add("")
                for project_code in project_codes:
                    server_cache.invalidate_domains(
                        (
                            "reference", "search", "snapshots",
                            "relations", "tasks", "notes", "messages",
                            "activity", "work_hours",
                        ),
                        project_code,
                    )
                return result

            worker = env_inst.server_pool.add_task(operation)
            self._worker = worker
            worker.result.connect(
                lambda result, current=generation:
                self._delete_finished(current, result)
            )
            worker.error.connect(
                lambda error, current=generation:
                self._operation_failed(current, error, "delete")
            )
            worker.start()
        except Exception as error:
            self._operation_failed(generation, error, "delete")

    def _delete_finished(self, generation: int, _result) -> None:
        if generation != self._generation:
            return
        context = self._context
        count = len(self._sources)
        self._worker = None
        self._busy = False
        self._deleting = False
        self._ready = False
        self._error = ""
        self.stateChanged.emit()
        self._application.window_model.close_window("delete_sobject")
        self._application._notify(
            "Item deleted" if count == 1 else f"{count} items deleted"
        )
        if context == "snapshot_file":
            self._application.refresh_snapshot_browser()
        elif context != "knowledge":
            self._application.refresh_current()
        self.deletionFinished.emit(context)
        if self._script_triggers is not None:
            event = (
                "task.delete"
                if self._sources and all(
                    _plain_search_type(source) == "sthpw/task"
                    for source in self._sources
                )
                else "object.delete"
            )
            self._script_triggers.run_after(event, self._trigger_payload)

    def _operation_failed(self, generation: int, error, phase: str) -> None:
        if generation != self._generation:
            return
        self._worker = None
        payload = error[0] if isinstance(error, tuple) else error
        if isinstance(payload, dict):
            exception = payload.get("exception") or payload
            stacktrace = payload.get("stacktrace") or ""
        else:
            exception = payload
            stacktrace = ""
        self._busy = False
        self._deleting = False
        self._ready = phase == "delete"
        self._error = str(exception or error)
        self.stateChanged.emit()
        if self._debug_log:
            self._debug_log.raise_error(
                exception,
                stacktrace=stacktrace,
                group=f"sobject-delete/{phase}",
            )

    @Slot()
    def retry(self) -> None:
        if self._busy or self._deleting or not self._sources:
            return
        self.begin(
            list(self._sources), self._context,
            parent_sources=dict(self._parent_sources))

    @Slot()
    def cancel(self) -> None:
        self._generation += 1
        worker = self._worker
        self._worker = None
        if worker is not None:
            try:
                worker.cancel()
            except (AttributeError, RuntimeError):
                pass
        self._busy = False
        self._deleting = False
        self._ready = False
        self.stateChanged.emit()
        self._application.window_model.close_window("delete_sobject")
