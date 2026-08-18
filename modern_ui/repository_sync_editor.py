from __future__ import annotations

from copy import deepcopy
import re

from PySide6.QtCore import QObject, Property, Qt, Signal, Slot

from .workspace import RecordListModel


class RepositorySyncEditorController(QObject):
    """Legacy-compatible editor for Repository Sync server presets."""

    stateChanged = Signal()
    presetsChanged = Signal()

    _KINDS = {
        "builtin": ":{b}",
        "pipeline": ":{pp}",
        "process": ":{pr}",
        "child": ":{s}",
    }

    def __init__(
        self, context, repository_sync, notify, debug_log=None, parent=None
    ) -> None:
        super().__init__(parent)
        self._context_provider = context
        self._repository_sync = repository_sync
        self._notify = notify
        self._debug_log = debug_log
        self._context: dict = {}
        self._workers: set = set()
        self._session_generation = 0
        self._busy = False
        self._error = ""
        self._title = ""
        self._selected_preset = -1
        self._full_sync = False
        self._only_updates = False
        self._scope_mode = "full"
        self._partial_chunk_size = 10
        self._original_state: dict = {}
        self._togglers = {
            "all": False,
            "process": False,
            "builtin": False,
            "child": False,
        }
        self.model = RecordListModel((
            "nodeId", "parentId", "dataKey", "title", "subtitle", "kind",
            "depth", "checkable", "checked", "expanded", "rowVisible",
            "selected", "accent",
        ))
        self.presets = RecordListModel((
            "name", "title", "getVersions", "onlyUpdates", "data", "code",
        ))

    @staticmethod
    def _info(source) -> dict:
        return dict(getattr(source, "info", None) or {})

    @staticmethod
    def _pipeline_values(stype) -> list:
        pipelines = getattr(stype, "pipeline", None) or {}
        if hasattr(pipelines, "values"):
            return list(pipelines.values())
        return list(pipelines.itervalues())

    @staticmethod
    def _pipeline_processes(pipeline) -> list[tuple[str, object]]:
        processes = (
            getattr(pipeline, "pipeline", None)
            or getattr(pipeline, "process", None)
            or {}
        )
        if hasattr(processes, "items"):
            return [(str(key), value) for key, value in processes.items()]
        return [(str(key), value) for key, value in processes.iteritems()]

    @staticmethod
    def _schema(stype):
        schema = getattr(stype, "schema", None)
        if schema is not None:
            return schema
        try:
            return stype.get_schema()
        except (AttributeError, KeyError, TypeError):
            return None

    @staticmethod
    def _stype_code(stype) -> str:
        try:
            return str(stype.get_code() or "")
        except (AttributeError, TypeError):
            return str(RepositorySyncEditorController._info(stype).get("code") or "")

    @staticmethod
    def _project(stype):
        try:
            return stype.get_project()
        except (AttributeError, KeyError, TypeError):
            return getattr(stype, "project", None)

    @staticmethod
    def _preset_code(title: str) -> str:
        value = re.sub(r"[^a-z0-9]+", "_", str(title).strip().lower())
        return value.strip("_") or "new_preset"

    @staticmethod
    def _preset_state(value) -> bool:
        if value is True:
            return True
        if value is False or value is None:
            return False
        if isinstance(value, (int, float)):
            return value > 0
        if isinstance(value, str):
            return value.strip().lower() in {
                "1", "2", "true", "on", "yes", "checked", "enabled",
            }
        return False

    def _saved_preset_index(self) -> int:
        return self._repository_sync.selected_preset_index(
            self._context.get("stype"),
            str(self._context.get("tab_name") or "default"),
        )

    def _saved_preset_name(self) -> str:
        getter = getattr(self._repository_sync, "selected_preset_name", None)
        if not callable(getter):
            return ""
        return str(getter(
            self._context.get("stype"),
            str(self._context.get("tab_name") or "default"),
        ) or "")

    def _store_preset_index(self) -> None:
        if self._selected_preset < 0:
            return
        source = self._context.get("stype")
        tab_name = str(self._context.get("tab_name") or "default")
        preset_name = str(
            self.presets._records[self._selected_preset].get("name") or ""
        )
        store = getattr(self._repository_sync, "store_selected_preset", None)
        if callable(store):
            store(source, tab_name, self._selected_preset, preset_name)
        else:
            self._repository_sync.store_selected_preset_index(
                source, tab_name, self._selected_preset,
            )

    def _set_busy(self, value: bool, error: str = "") -> None:
        changed = self._busy != bool(value) or self._error != str(error or "")
        self._busy = bool(value)
        self._error = str(error or "")
        if changed:
            self.stateChanged.emit()

    def _run_server(self, operation, callback) -> None:
        try:
            from thlib.environment import env_inst

            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            worker = env_inst.server_pool.add_task(operation)
            self._workers.add(worker)
            worker.result.connect(callback, Qt.ConnectionType.QueuedConnection)
            worker.error.connect(
                self._server_failed, Qt.ConnectionType.QueuedConnection
            )
            worker.finished.connect(lambda: self._workers.discard(worker))
            worker.start()
            self._set_busy(True)
        except Exception as error:
            self._set_busy(False, str(error))
            self._notify(str(error))

    @Slot()
    def begin_session(self) -> None:
        self._session_generation += 1
        self._context = dict(self._context_provider() or {})
        sobject = self._context.get("sobject")
        stype = self._context.get("stype")
        if stype is None and sobject is not None:
            try:
                stype = sobject.get_stype()
            except AttributeError:
                stype = None
        self._context["stype"] = stype
        if not stype:
            self._title = ""
            self.model.clear()
            self.presets.clear()
            self._selected_preset = -1
            self._set_busy(False, "Select an sObject or Search Type first")
            return
        if sobject is not None:
            try:
                self._title = str(sobject.get_title() or "")
            except AttributeError:
                self._title = ""
        if not self._title:
            try:
                self._title = str(stype.get_pretty_name() or "")
            except AttributeError:
                info = self._info(stype)
                self._title = str(
                    info.get("title") or info.get("name")
                    or info.get("code") or ""
                )
        self.model.replace(self._build_tree(stype))
        self._selected_preset = -1
        self._full_sync = False
        self._only_updates = False
        scope_provider = getattr(
            self._repository_sync, "configured_scope_mode", None
        )
        self._scope_mode = (
            scope_provider() if callable(scope_provider) else "full"
        )
        chunk_provider = getattr(
            self._repository_sync, "configured_partial_chunk_size", None
        )
        self._partial_chunk_size = max(
            1, min(250, int(
                chunk_provider() if callable(chunk_provider) else 10
            ))
        )
        self._original_state = {}
        self._togglers = {
            "all": False,
            "process": False,
            "builtin": False,
            "child": False,
        }
        self.stateChanged.emit()
        self.reload_presets()

    def _record(
        self, node_id: str, parent_id: str, data_key: str, title: str,
        subtitle: str, kind: str, depth: int, checkable: bool,
        checked: bool, accent: str = "",
    ) -> dict:
        return {
            "nodeId": node_id,
            "parentId": parent_id,
            "dataKey": data_key,
            "title": title,
            "subtitle": subtitle,
            "kind": kind,
            "depth": depth,
            "checkable": checkable,
            "checked": checked,
            "expanded": True,
            "rowVisible": True,
            "selected": False,
            "accent": accent,
        }

    def _build_tree(self, stype) -> list[dict]:
        records: list[dict] = []
        self._append_stype(records, stype, "", 0, ())
        return records

    def _append_stype(
        self, records: list[dict], stype, parent_id: str, depth: int,
        ancestors: tuple[str, ...],
    ) -> None:
        stype_code = self._stype_code(stype)
        for builtin in ("publish", "attachment", "icon"):
            node_id = f"{parent_id or 'root'}:builtin:{builtin}"
            records.append(self._record(
                node_id, parent_id, f"{builtin}:{{b}}", builtin.title(),
                "Built-in process", "builtin", depth, True, True,
            ))

        for pipeline_index, pipeline in enumerate(self._pipeline_values(stype)):
            info = self._info(pipeline)
            code = str(
                info.get("code") or info.get("name")
                or f"pipeline_{pipeline_index}"
            )
            title = str(info.get("name") or info.get("title") or code)
            pipeline_id = f"{parent_id or 'root'}:pipeline:{pipeline_index}:{code}"
            records.append(self._record(
                pipeline_id, parent_id, f"{code}:{{pp}}", title, "Pipeline",
                "pipeline", depth, False, False,
                str(info.get("color") or ""),
            ))
            for process_index, (process, process_data) in enumerate(
                self._pipeline_processes(pipeline)
            ):
                process_info = {}
                try:
                    process_info = dict(
                        pipeline.get_process_info(process) or {}
                    )
                except (AttributeError, KeyError, TypeError):
                    if isinstance(process_data, dict):
                        process_info = dict(process_data)
                try:
                    process_title = pipeline.get_process_label(process)
                except (AttributeError, KeyError, TypeError):
                    process_title = ""
                records.append(self._record(
                    f"{pipeline_id}:process:{process_index}:{process}",
                    pipeline_id, f"{process}:{{pr}}",
                    str(process_title or process),
                    str(process_info.get("type") or "Process"), "process",
                    depth + 1, True, False,
                    str(process_info.get("color") or info.get("color") or ""),
                ))

        schema = self._schema(stype)
        project = self._project(stype)
        stypes = getattr(project, "stypes", None) or {}
        next_ancestors = (*ancestors, stype_code)
        for relation_index, relation in enumerate(
            getattr(schema, "children", None) or []
        ):
            if relation.get("type") == "many_to_many":
                continue
            child_code = str(relation.get("from") or "")
            if not child_code or child_code in next_ancestors:
                continue
            child_stype = stypes.get(child_code)
            if not child_stype:
                continue
            info = self._info(child_stype)
            title = str(
                info.get("title") or info.get("name")
                or info.get("code") or child_code
            )
            child_id = (
                f"{parent_id or 'root'}:child:{relation_index}:{child_code}"
            )
            records.append(self._record(
                child_id, parent_id, f"{child_code}:{{s}}", title,
                "Child Search Type", "child", depth, True, False,
                str(info.get("color") or ""),
            ))
            self._append_stype(
                records, child_stype, child_id, depth + 1, next_ancestors
            )

    def _query_presets(self, stype=None):
        stype = stype or self._context.get("stype")
        project = self._project(stype)
        project_code = str(project.get_code() or "")
        stype_code = self._stype_code(stype)
        import thlib.global_functions as gf
        import thlib.tactic_classes as tc

        server = tc.server_start(project=project_code)
        rows = server.query(
            "sthpw/wdg_settings",
            [
                ("key", "like", f"search_type:{stype_code}:preset_name:%"),
                ("project_code", project_code),
            ],
            ["code", "key", "data", "project_code"],
        )
        result = []
        for row in rows or []:
            data = gf.from_json(row.get("data") or "")
            if not isinstance(data, dict):
                continue
            name = str(
                data.get("preset_name")
                or str(row.get("key") or "").partition(":preset_name:")[2]
                or "default"
            )
            result.append({
                "name": name,
                "title": str(
                    data.get("pretty_preset_name")
                    or name.replace("_", " ").title()
                ),
                "getVersions": bool(data.get("get_versions")),
                "onlyUpdates": bool(data.get("only_updates")),
                "data": data,
                "code": str(row.get("code") or ""),
            })
        if not result:
            default = {
                "preset_name": "default",
                "pretty_preset_name": "Default",
                "get_versions": False,
                "publish:{b}": {"state": True},
                "attachment:{b}": {"state": True},
                "icon:{b}": {"state": True},
            }
            result.append({
                "name": "default", "title": "Default",
                "getVersions": False, "onlyUpdates": False,
                "data": default, "code": "",
            })
        return result

    @Slot()
    def reload_presets(self) -> None:
        stype = self._context.get("stype")
        if not stype:
            return
        generation = self._session_generation
        stype_code = self._stype_code(stype)
        self._run_server(
            lambda: (
                generation, stype_code, self._query_presets(stype),
            ),
            self._presets_loaded,
        )

    @Slot(object)
    def _presets_loaded(self, payload) -> None:
        if (
            isinstance(payload, tuple) and len(payload) == 3
            and isinstance(payload[0], int)
        ):
            generation, stype_code, records = payload
            if (
                generation != self._session_generation
                or stype_code != self._stype_code(
                    self._context.get("stype")
                )
            ):
                return
        else:
            # Direct calls are retained for deterministic unit tests and
            # local model restoration; server workers always carry a token.
            records = payload
        pending = str(self._context.pop("pending_preset", "") or "")
        previous = ""
        if 0 <= self._selected_preset < len(self.presets._records):
            previous = str(
                self.presets._records[self._selected_preset].get("name") or ""
            )
        self.presets.replace(list(records or []))
        target = pending or previous or self._saved_preset_name()
        saved_row = min(
            max(0, self._saved_preset_index()),
            max(0, len(self.presets._records) - 1),
        )
        row = next((
            index for index, record in enumerate(self.presets._records)
            if record.get("name") == target
        ), saved_row if self.presets._records else -1)
        self._set_busy(False)
        self.select_preset(row)
        self.presetsChanged.emit()

    @Slot(object)
    def _server_failed(self, error) -> None:
        payload = error[0] if isinstance(error, tuple) else error
        if isinstance(payload, dict):
            payload = payload.get("exception") or payload
        message = str(payload)
        self._set_busy(False, message)
        self._notify(message)

    def _reset_tree_defaults(self) -> None:
        for row, record in enumerate(self.model._records):
            checked = record.get("kind") == "builtin"
            self.model.update_record(row, {
                "checked": checked,
                "selected": False,
            })

    @Slot(int)
    def select_preset(self, row: int) -> None:
        if not 0 <= row < len(self.presets._records):
            self._selected_preset = -1
            self.stateChanged.emit()
            return
        self._selected_preset = row
        preset = deepcopy(self.presets._records[row].get("data") or {})
        self._full_sync = bool(preset.get("get_versions"))
        self._only_updates = bool(preset.get("only_updates"))
        self._reset_tree_defaults()
        self._apply_level("", preset)
        self._original_state = self._state()
        self._store_preset_index()
        self.stateChanged.emit()

    def _apply_level(self, parent_id: str, level: dict) -> None:
        for row, record in enumerate(self.model._records):
            if record.get("parentId") != parent_id:
                continue
            entry = level.get(record.get("dataKey"))
            if isinstance(entry, dict):
                if record.get("checkable"):
                    self.model.set_value(
                        row, "checked", self._preset_state(entry.get("state"))
                    )
                self._apply_level(
                    str(record.get("nodeId") or ""),
                    dict(entry.get("sub") or {}),
                )

    def _serialize_level(self, parent_id: str) -> dict:
        result = {}
        for record in self.model._records:
            if record.get("parentId") != parent_id:
                continue
            entry = {"state": bool(record.get("checked"))}
            children = self._serialize_level(str(record.get("nodeId") or ""))
            if children:
                entry["sub"] = children
            result[str(record.get("dataKey") or "")] = entry
        return result

    def _preset_payload(self, name: str, title: str) -> dict:
        return {
            "preset_name": name,
            "pretty_preset_name": title,
            "get_versions": self._full_sync,
            "only_updates": self._only_updates,
            **self._serialize_level(""),
        }

    def _state(self) -> dict:
        return {
            "full": self._full_sync,
            "updates": self._only_updates,
            "tree": self._serialize_level(""),
        }

    @Property(str, notify=stateChanged)
    def contextTitle(self) -> str:
        return self._title

    @Property(bool, notify=stateChanged)
    def validContext(self) -> bool:
        return bool(self._context.get("stype"))

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error

    @Property(int, notify=stateChanged)
    def selectedPreset(self) -> int:
        return self._selected_preset

    @Property(bool, notify=stateChanged)
    def fullSync(self) -> bool:
        return self._full_sync

    @Property(bool, notify=stateChanged)
    def onlyUpdates(self) -> bool:
        return self._only_updates

    @Property(str, notify=stateChanged)
    def scopeMode(self) -> str:
        return self._scope_mode

    @Property(int, notify=stateChanged)
    def partialChunkSize(self) -> int:
        return self._partial_chunk_size

    @Property(bool, notify=stateChanged)
    def dirty(self) -> bool:
        return bool(self._original_state and self._state() != self._original_state)

    @Slot(bool)
    def set_full_sync(self, value: bool) -> None:
        self._full_sync = bool(value)
        self.stateChanged.emit()

    @Slot(bool)
    def set_only_updates(self, value: bool) -> None:
        self._only_updates = bool(value)
        self.stateChanged.emit()

    @Slot(str)
    def set_scope_mode(self, value: str) -> None:
        value = "partial" if str(value or "").lower() == "partial" else "full"
        if value == self._scope_mode:
            return
        self._scope_mode = value
        self.stateChanged.emit()

    @Slot(int)
    def set_partial_chunk_size(self, value: int) -> None:
        value = max(1, min(250, int(value or 10)))
        if value == self._partial_chunk_size:
            return
        self._partial_chunk_size = value
        setter = getattr(
            self._repository_sync, "set_partial_chunk_size", None
        )
        if callable(setter):
            setter(value)
        self.stateChanged.emit()

    @Slot(int, bool)
    def set_checked(self, row: int, checked: bool) -> None:
        if not 0 <= row < len(self.model._records):
            return
        source = self.model._records[row]
        if not source.get("checkable"):
            return
        selected = [
            index for index, record in enumerate(self.model._records)
            if record.get("selected") and record.get("checkable")
        ]
        rows = selected if source.get("selected") and len(selected) > 1 else [row]
        if self.model.set_role_for_rows(rows, "checked", bool(checked)):
            self.stateChanged.emit()

    @Slot(int, bool)
    def select_row(self, row: int, additive: bool) -> None:
        if not 0 <= row < len(self.model._records):
            return
        current = bool(self.model._records[row].get("selected"))
        changed = False
        for index, record in enumerate(self.model._records):
            value = (
                not current if index == row
                else bool(record.get("selected")) if additive else False
            )
            changed = self.model.update_record(
                index, {"selected": value}
            ) or changed
        if changed:
            self.stateChanged.emit()

    @Slot(int)
    def toggle_expanded(self, row: int) -> None:
        if not 0 <= row < len(self.model._records):
            return
        record = self.model._records[row]
        node_id = str(record.get("nodeId") or "")
        if not any(
            item.get("parentId") == node_id for item in self.model._records
        ):
            return
        self.model.set_value(row, "expanded", not record.get("expanded"))
        by_id = {
            item.get("nodeId"): item for item in self.model._records
        }
        for index, item in enumerate(self.model._records):
            parent_id = item.get("parentId")
            visible = True
            while parent_id:
                parent = by_id.get(parent_id)
                if not parent:
                    break
                if not parent.get("expanded"):
                    visible = False
                    break
                parent_id = parent.get("parentId")
            self.model.set_value(index, "rowVisible", visible)
        self.stateChanged.emit()

    @Slot(str)
    def toggle_kind(self, kind: str) -> None:
        if kind not in self._togglers:
            return
        rows = [
            index for index, record in enumerate(self.model._records)
            if record.get("checkable")
            and (kind == "all" or record.get("kind") == kind)
        ]
        checked = bool(self._togglers[kind])
        self._togglers[kind] = not checked
        if self.model.set_role_for_rows(rows, "checked", checked):
            self.stateChanged.emit()

    def _write_preset(self, name: str, title: str):
        stype = self._context.get("stype")
        project = self._project(stype)
        project_code = str(project.get_code() or "")
        stype_code = self._stype_code(stype)
        data = self._preset_payload(name, title)
        key = f"search_type:{stype_code}:preset_name:{name}"
        import thlib.global_functions as gf
        import thlib.tactic_classes as tc

        server = tc.server_start(project=project_code)
        current = server.query(
            "sthpw/wdg_settings",
            [("key", key), ("project_code", project_code)],
            ["code", "project"], single=True,
        )
        values = {
            "data": gf.to_json(data),
            "key": key,
            "login": "admin",
            "project_code": project_code,
        }
        if current:
            search_key = server.build_search_key(
                "sthpw/wdg_settings", current["code"], current.get("project")
            )
            server.insert_update(search_key, values, triggers=False)
        else:
            server.insert("sthpw/wdg_settings", values, triggers=False)
        return name

    @Slot(str)
    def save_as(self, title: str) -> None:
        title = str(title or "").strip()
        if not title or not self.validContext:
            self._notify("Enter a Repository Sync preset name")
            return
        name = self._preset_code(title)
        if any(record.get("name") == name for record in self.presets._records):
            self._notify("A Repository Sync preset with this name already exists")
            return
        self._run_server(
            lambda: self._write_preset(name, title), self._preset_saved
        )

    @Slot()
    def save_selected(self) -> None:
        if not 0 <= self._selected_preset < len(self.presets._records):
            self._notify("Select a Repository Sync preset first")
            return
        record = self.presets._records[self._selected_preset]
        name = str(record.get("name") or "default")
        title = str(record.get("title") or name.replace("_", " ").title())
        self._run_server(
            lambda: self._write_preset(name, title), self._preset_saved
        )

    @Slot(object)
    def _preset_saved(self, name) -> None:
        self._set_busy(False)
        self._context["pending_preset"] = str(name or "")
        self.reload_presets()

    @Slot()
    def delete_selected(self) -> None:
        if not 0 <= self._selected_preset < len(self.presets._records):
            return
        record = dict(self.presets._records[self._selected_preset])
        stype = self._context.get("stype")
        project = self._project(stype)
        project_code = str(project.get_code() or "")
        key = (
            f"search_type:{self._stype_code(stype)}:preset_name:"
            f"{record.get('name') or 'default'}"
        )

        def remove():
            import thlib.tactic_classes as tc
            server = tc.server_start(project=project_code)
            current = server.query(
                "sthpw/wdg_settings",
                [("key", key), ("project_code", project_code)], single=True,
            )
            if current:
                server.delete_sobject(current["__search_key__"])
            return True

        self._run_server(remove, self._preset_deleted)

    @Slot(object)
    def _preset_deleted(self, _result) -> None:
        self._selected_preset = -1
        self._set_busy(False)
        self.reload_presets()

    def _start_sync(self, partial_chunk_size: int | None = None) -> None:
        if not 0 <= self._selected_preset < len(self.presets._records):
            self._notify("Select a Repository Sync preset first")
            return
        chunk_size = max(1, min(250, int(
            self._partial_chunk_size
            if partial_chunk_size is None else partial_chunk_size
        )))
        self._partial_chunk_size = chunk_size
        preset = self.presets._records[self._selected_preset]
        name = str(preset.get("name") or "default")
        sobject = self._context.get("sobject")
        stype = self._context.get("stype")
        if sobject is not None:
            self._repository_sync.start_sobject_sync(
                sobject, name, self._only_updates,
                preset_data=self._preset_payload(
                    name, str(preset.get("title") or name)
                ),
                scope_mode=self._scope_mode,
                partial_chunk_size=chunk_size,
            )
        else:
            self._repository_sync.start_stype_sync(
                stype, name, self._only_updates,
                preset_data=self._preset_payload(
                    name, str(preset.get("title") or name)
                ),
                scope_mode=self._scope_mode,
                partial_chunk_size=chunk_size,
            )

    @Slot()
    def start_sync(self) -> None:
        self._start_sync()

    @Slot(int)
    def start_sync_with_chunk_size(self, value: int) -> None:
        self.set_partial_chunk_size(value)
        self._start_sync(value)

    @Slot()
    def cancel(self) -> None:
        if 0 <= self._selected_preset < len(self.presets._records):
            self.select_preset(self._selected_preset)


__all__ = ["RepositorySyncEditorController"]
