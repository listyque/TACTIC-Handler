from __future__ import annotations

from PySide6.QtCore import QObject, Property, Signal, Slot

from .workspace import RecordListModel


class ProcessFilterEditorController(QObject):
    """Modern counterpart of legacy ``Ui_processFilterDialog``.

    The editor owns only the local tree-visibility preference. Search
    conditions and server-side Saved Searches remain in Advanced Search.
    """

    stateChanged = Signal()

    def __init__(self, context, apply_settings, notify, parent=None) -> None:
        super().__init__(parent)
        self._context = context
        self._apply_settings = apply_settings
        self._notify = notify
        self._context_key: tuple[str, str, str] = ("", "", "")
        self._title = ""
        self._original_ignore: dict = {}
        self.model = RecordListModel((
            "nodeId", "parentId", "key", "title", "subtitle", "kind",
            "group", "depth", "checkable", "checked", "expanded",
            "rowVisible", "selected", "accent",
        ))

    @staticmethod
    def _key(context: dict) -> tuple[str, str, str]:
        return (
            str(context.get("project_code") or ""),
            str(context.get("search_type") or ""),
            str(context.get("tab_name") or context.get("tab_id") or ""),
        )

    @staticmethod
    def _pipeline_values(stype) -> list:
        pipelines = getattr(stype, "pipeline", None)
        if pipelines is None:
            try:
                pipelines = stype.get_pipeline()
            except (AttributeError, KeyError, TypeError):
                pipelines = None
        pipelines = pipelines or {}
        if hasattr(pipelines, "values"):
            return list(pipelines.values())
        return list(pipelines.itervalues())

    @staticmethod
    def _pipeline_processes(pipeline) -> list[tuple[str, object]]:
        # Current native Pipeline stores process nodes in ``pipeline``;
        # older Handler objects exposed the same mapping as ``process``.
        # Preserve both native contracts instead of adapting process names.
        processes = (
            getattr(pipeline, "pipeline", None)
            or getattr(pipeline, "process", None)
            or {}
        )
        if hasattr(processes, "items"):
            return [(str(key), value) for key, value in processes.items()]
        return [(str(key), value) for key, value in processes.iteritems()]

    @staticmethod
    def _info(source) -> dict:
        return dict(getattr(source, "info", None) or {})

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
    def _project(context: dict, stype):
        project = context.get("project")
        if project is not None:
            return project
        try:
            return stype.get_project()
        except (AttributeError, KeyError, TypeError):
            return None

    def _settings_path(self, context: dict) -> str:
        return "ui_search/checkin_out/{}/{}/{}".format(
            context.get("project_type") or "",
            context.get("project_code") or "",
            context.get("tab_name") or context.get("tab_id") or "",
        )

    @Slot()
    def begin_session(self) -> None:
        context = dict(self._context() or {})
        self._context_key = self._key(context)
        stype = context.get("stype")
        project = self._project(context, stype) if stype else None
        info = self._info(stype)
        self._title = str(
            info.get("title") or info.get("name")
            or info.get("code") or context.get("search_type") or ""
        )
        if not stype or not project or not all(self._context_key[:2]):
            self.model.clear()
            self._original_ignore = {}
            self.stateChanged.emit()
            return

        records = self._build_records(stype, project)
        ignore = self._read_settings(context)
        self._apply_ignore(records, ignore)
        self.model.reset_records(records)
        self._original_ignore = self._ignore_dict()
        self.stateChanged.emit()

    def _build_records(self, stype, project) -> list[dict]:
        records: list[dict] = []
        schema = self._schema(stype)
        project_stypes = getattr(project, "stypes", None) or {}
        for relation in getattr(schema, "children", None) or []:
            child_code = str(relation.get("from") or "")
            child_stype = project_stypes.get(child_code)
            if not child_stype:
                continue
            info = self._info(child_stype)
            child_title = str(
                info.get("title") or info.get("name")
                or info.get("code") or child_code
            )
            child_id = f"child:{child_code}"
            records.append(self._record(
                child_id, "", child_code, child_title, "Child Search Type",
                "child", "", 0, True,
                str(info.get("color") or ""),
            ))
            self._append_pipelines(
                records, child_stype, child_id, 1, f"{child_id}:pipeline"
            )

        self._append_pipelines(records, stype, "", 0, "pipeline")
        for key, title in (
            ("publish", "Publish"),
            ("attachment", "Attachment"),
            ("icon", "Icon"),
        ):
            records.append(self._record(
                f"builtin:{key}", "", key, title, "Built-in process",
                "builtin", "", 0, True, "",
            ))
        return records

    @staticmethod
    def _record(
        node_id: str,
        parent_id: str,
        key: str,
        title: str,
        subtitle: str,
        kind: str,
        group: str,
        depth: int,
        checkable: bool,
        accent: str,
    ) -> dict:
        return {
            "nodeId": node_id,
            "parentId": parent_id,
            "key": key,
            "title": title,
            "subtitle": subtitle,
            "kind": kind,
            "group": group,
            "depth": depth,
            "checkable": checkable,
            "checked": True,
            "expanded": True,
            "rowVisible": True,
            "selected": False,
            "accent": accent,
        }

    def _append_pipelines(
        self,
        records: list[dict],
        stype,
        parent_id: str,
        depth: int,
        id_prefix: str,
    ) -> None:
        for pipeline_index, pipeline in enumerate(self._pipeline_values(stype)):
            info = self._info(pipeline)
            pipeline_code = str(
                info.get("code") or info.get("name")
                or f"pipeline_{pipeline_index}"
            )
            pipeline_title = str(
                info.get("name") or info.get("title") or pipeline_code
            )
            pipeline_id = f"{id_prefix}:{pipeline_index}:{pipeline_code}"
            records.append(self._record(
                pipeline_id, parent_id, pipeline_code, pipeline_title,
                "Pipeline", "pipeline", pipeline_code, depth, False,
                str(info.get("color") or ""),
            ))
            for process_index, (process_code, process_data) in enumerate(
                self._pipeline_processes(pipeline)
            ):
                process_info = {}
                try:
                    process_info = dict(
                        pipeline.get_process_info(process_code) or {}
                    )
                except (AttributeError, KeyError, TypeError):
                    if isinstance(process_data, dict):
                        process_info = dict(process_data)
                try:
                    process_title = pipeline.get_process_label(process_code)
                except (AttributeError, KeyError, TypeError):
                    process_title = ""
                records.append(self._record(
                    f"{pipeline_id}:process:{process_index}:{process_code}",
                    pipeline_id,
                    process_code,
                    str(process_title or process_code),
                    str(process_info.get("type") or "Process"),
                    "process",
                    pipeline_code,
                    depth + 1,
                    True,
                    str(process_info.get("color") or info.get("color") or ""),
                ))

    def _read_settings(self, context: dict) -> dict:
        from thlib.environment import env_read_config

        return dict(env_read_config(
            filename="process_ignore_dict",
            unique_id=self._settings_path(context),
            long_abs_path=True,
        ) or {})

    @staticmethod
    def _apply_ignore(records: list[dict], ignore: dict) -> None:
        children = set(ignore.get("children") or [])
        builtins = set(ignore.get("builtins") or [])
        processes = dict(ignore.get("processes") or {})
        for record in records:
            kind = record.get("kind")
            if kind == "child":
                record["checked"] = record.get("key") not in children
            elif kind == "builtin":
                record["checked"] = record.get("key") not in builtins
            elif kind == "process":
                record["checked"] = record.get("key") not in set(
                    processes.get(record.get("group")) or []
                )

    @Property(str, notify=stateChanged)
    def context_title(self) -> str:
        return self._title

    @Property(bool, notify=stateChanged)
    def valid_context(self) -> bool:
        return bool(self.model._records and all(self._context_key[:2]))

    @Property(bool, notify=stateChanged)
    def dirty(self) -> bool:
        return self._ignore_dict() != self._original_ignore

    @Slot(int, bool)
    def select_row(self, row: int, additive: bool) -> None:
        if not 0 <= row < len(self.model._records):
            return
        current = bool(self.model._records[row].get("selected"))
        changed = False
        for index, record in enumerate(self.model._records):
            selected = (not current) if index == row else (
                bool(record.get("selected")) if additive else False
            )
            changed = self.model.update_record(
                index, {"selected": selected}
            ) or changed
        if changed:
            self.stateChanged.emit()

    @Slot(int, bool)
    def set_checked(self, row: int, checked: bool) -> None:
        if not 0 <= row < len(self.model._records):
            return
        source = self.model._records[row]
        if not source.get("checkable"):
            return
        selected_rows = [
            index for index, record in enumerate(self.model._records)
            if record.get("selected") and record.get("checkable")
        ]
        rows = selected_rows if source.get("selected") and len(selected_rows) > 1 else [row]
        changed = self.model.set_role_for_rows(rows, "checked", bool(checked))
        if changed:
            self.stateChanged.emit()

    @Slot(int)
    def toggle_expanded(self, row: int) -> None:
        if not 0 <= row < len(self.model._records):
            return
        record = self.model._records[row]
        if record.get("kind") not in {"child", "pipeline"}:
            return
        self.model.set_value(row, "expanded", not record.get("expanded"))
        self._update_visibility()

    def _update_visibility(self) -> None:
        by_id = {
            record.get("nodeId"): record for record in self.model._records
        }
        for index, record in enumerate(self.model._records):
            parent_id = record.get("parentId")
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
        rows = [
            index for index, record in enumerate(self.model._records)
            if record.get("checkable")
            and (kind == "all" or record.get("kind") == kind)
        ]
        checked = any(
            not self.model._records[index].get("checked") for index in rows
        )
        if self.model.set_role_for_rows(rows, "checked", checked):
            self.stateChanged.emit()

    def _ignore_dict(self) -> dict:
        ignore = {
            "children": [],
            "processes": {},
            "builtins": [],
            "show_builtins": False,
        }
        for record in self.model._records:
            kind = record.get("kind")
            if kind == "process":
                ignore["processes"].setdefault(record.get("group"), [])
            if record.get("checked") or not record.get("checkable"):
                continue
            if kind == "child":
                ignore["children"].append(record.get("key"))
            elif kind == "builtin":
                ignore["builtins"].append(record.get("key"))
            elif kind == "process":
                ignore["processes"][record.get("group")].append(
                    record.get("key")
                )
        if not any((
            ignore["children"], ignore["builtins"],
            any(ignore["processes"].values()),
        )):
            return {}
        return ignore

    @Slot(result=bool)
    def save(self) -> bool:
        context = dict(self._context() or {})
        if self._key(context) != self._context_key or not self.valid_context:
            self._notify(
                "The active project or search tab changed. Reopen the editor."
            )
            return False
        ignore = self._ignore_dict()
        from thlib.environment import env_write_config

        env_write_config(
            ignore,
            filename="process_ignore_dict",
            unique_id=self._settings_path(context),
            long_abs_path=True,
        )
        self._original_ignore = dict(ignore)
        self._apply_settings(ignore)
        self.stateChanged.emit()
        return True

    @Slot()
    def cancel(self) -> None:
        records = [dict(record) for record in self.model._records]
        self._apply_ignore(records, self._original_ignore)
        for record in records:
            record["selected"] = False
        self.model.replace(records)
        self.stateChanged.emit()
