from __future__ import annotations

import re
from xml.etree import ElementTree

from PySide6.QtCore import QObject, Property, Signal, Slot

from .workspace import RecordListModel


class FilterEditorController(QObject):
    stateChanged = Signal()

    _numeric_types = {"integer", "float", "currency"}
    _boolean_values = {"true", "false", "1", "0", "yes", "no"}

    def __init__(
        self,
        source_records,
        column_records,
        relation_choices,
        apply_records,
        notify,
        can_apply=None,
        context=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._source_records = source_records
        self._column_records = column_records
        self._relation_choices = relation_choices
        self._apply_records = apply_records
        self._notify = notify
        self._can_apply = can_apply or (lambda: True)
        self._context = context or (lambda: {})
        self._original_records: list[dict] = []
        self._original_title = ""
        self._title = ""
        self._validation_error = ""
        self._preset_error = ""
        self._busy = False
        self._selected_preset = -1
        self._pending_view = ""
        self._context_key = ()
        self._workers = set()
        self.model = RecordListModel((
            "column", "relation", "value", "rowEnabled", "operator",
            "isDefault", "dataType",
        ))
        self.presets = RecordListModel((
            "code", "title", "view", "records",
        ))
        self.processes = RecordListModel((
            "key", "title", "kind", "group", "depth", "itemEnabled",
        ))

    def _columns(self) -> list[dict]:
        return [dict(record) for record in self._column_records()]

    def _data_type(self, column: str) -> str:
        return str(next(
            (
                record.get("dataType")
                for record in self._columns()
                if record.get("value") == column
            ),
            "_expression" if column == "_expression" else "all",
        ) or "all")

    def _new_record(self, is_default: bool) -> dict:
        columns = self._columns()
        preferred = next(
            (record for record in columns if record.get("value") == "name"),
            columns[0] if columns else {},
        )
        column = str(preferred.get("value") or "")
        relations = self._relation_choices(column)
        return {
            "column": column,
            "relation": (
                "EQI" if is_default
                else relations[0].get("value") if relations else "="
            ),
            "value": "",
            "rowEnabled": True,
            "operator": "begin" if is_default else "and",
            "isDefault": is_default,
            "dataType": self._data_type(column),
        }

    @staticmethod
    def _key(context: dict) -> tuple:
        return (
            str(context.get("project_code") or ""),
            str(context.get("search_type") or ""),
            str(context.get("tab_id") or ""),
        )

    def _current_context(self) -> dict:
        return dict(self._context() or {})

    def _context_is_current(self) -> bool:
        return self._context_key == self._key(self._current_context())

    @Slot()
    def begin_session(self) -> None:
        context = self._current_context()
        self._context_key = self._key(context)
        records = [dict(record) for record in self._source_records()]
        if not records:
            records = [self._new_record(True)]
        self._replace_records(records)
        self._original_records = [
            dict(record) for record in self.model._records
        ]
        self._title = str(context.get("tab_title") or "")
        self._original_title = self._title
        self._selected_preset = -1
        self._preset_error = ""
        self._build_process_model(context)
        self._validate()
        self.load_presets()
        self.stateChanged.emit()

    def _replace_records(self, records) -> None:
        normalized = []
        for index, source in enumerate(records or []):
            record = dict(source)
            record["isDefault"] = index == 0
            record["operator"] = (
                "begin" if index == 0
                else "or" if record.get("operator") == "or" else "and"
            )
            record["rowEnabled"] = bool(record.get("rowEnabled", True))
            record["dataType"] = self._data_type(
                str(record.get("column") or "")
            )
            normalized.append(record)
        if not normalized:
            normalized = [self._new_record(True)]
        self.model.replace(normalized)

    @Slot()
    def add_condition(self) -> None:
        records = [dict(record) for record in self.model._records]
        records.append(self._new_record(not records))
        self.model.replace(records)
        self._validate()

    @Slot(int)
    def remove_condition(self, row: int) -> None:
        if not 0 <= row < len(self.model._records):
            return
        records = [
            dict(record) for index, record in enumerate(self.model._records)
            if index != row
        ]
        self._replace_records(records)
        self._validate()

    @Slot(int, str)
    def set_column(self, row: int, column: str) -> None:
        if not 0 <= row < len(self.model._records):
            return
        relations = self._relation_choices(column)
        self.model.set_value(row, "column", column)
        self.model.set_value(row, "dataType", self._data_type(column))
        self.model.set_value(
            row,
            "relation",
            relations[0].get("value") if relations else "=",
        )
        self._validate()

    @Slot(int, str, "QVariant")
    def set_value(self, row: int, role: str, value) -> None:
        if role not in {"relation", "value", "rowEnabled", "operator"}:
            return
        if role == "operator":
            value = "or" if value == "or" else "and"
        self.model.set_value(row, role, value)
        self._validate()

    @Slot(str, result="QVariantList")
    def relations(self, column: str) -> list[dict]:
        return [dict(record) for record in self._relation_choices(column)]

    @Slot(str)
    def set_title(self, value: str) -> None:
        value = str(value or "")
        if self._title == value:
            return
        self._title = value
        self.stateChanged.emit()

    def _validate(self) -> bool:
        if not self._can_apply() or not self._context_is_current():
            self._set_validation_error(
                "The active project or search tab changed. Reopen the editor."
            )
            return False
        for index, record in enumerate(self.model._records):
            if not record.get("rowEnabled"):
                continue
            column = str(record.get("column") or "")
            if not column:
                self._set_validation_error(
                    f"Condition {index + 1}: select a column."
                )
                return False
            relation = record.get("relation")
            allowed = [
                choice.get("value")
                for choice in self._relation_choices(column)
            ]
            if relation not in allowed:
                self._set_validation_error(
                    f"Condition {index + 1}: select a valid operator."
                )
                return False
            value = str(record.get("value") or "").strip()
            if relation is not None and not value:
                enabled_count = sum(
                    bool(item.get("rowEnabled"))
                    for item in self.model._records
                )
                if enabled_count == 1:
                    continue
                self._set_validation_error(
                    f"Condition {index + 1}: enter a value."
                )
                return False
            data_type = str(record.get("dataType") or "")
            if data_type in self._numeric_types and value and relation not in {
                "in", "not in",
            }:
                try:
                    float(value)
                except ValueError:
                    self._set_validation_error(
                        f"Condition {index + 1}: enter a numeric value."
                    )
                    return False
            if (
                data_type == "boolean"
                and value
                and value.lower() not in self._boolean_values
            ):
                self._set_validation_error(
                    f"Condition {index + 1}: select true or false."
                )
                return False
        self._set_validation_error("")
        return True

    def _set_validation_error(self, message: str) -> None:
        if self._validation_error == message:
            return
        self._validation_error = message
        self.stateChanged.emit()

    @Property(str, notify=stateChanged)
    def validation_error(self) -> str:
        return self._validation_error

    @Property(str, notify=stateChanged)
    def preset_error(self) -> str:
        return self._preset_error

    @Property(str, notify=stateChanged)
    def tab_title(self) -> str:
        return self._title

    @Property(bool, notify=stateChanged)
    def valid(self) -> bool:
        return not self._validation_error

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(int, notify=stateChanged)
    def selected_preset(self) -> int:
        return self._selected_preset

    @Slot(result=bool)
    def apply(self) -> bool:
        if not self._validate():
            self._notify(self._validation_error)
            return False
        records = [dict(record) for record in self.model._records]
        self._save_process_settings()
        self._apply_records(records, self._title, self._process_ignore())
        self._original_records = records
        self._original_title = self._title
        return True

    @Slot()
    def cancel(self) -> None:
        self.model.replace([
            dict(record) for record in self._original_records
        ])
        self._title = self._original_title
        self._set_validation_error("")
        self.stateChanged.emit()

    @staticmethod
    def _preset_name(title: str) -> str:
        value = re.sub(r"[^a-z0-9_]+", "_", title.strip().lower())
        return value.strip("_") or "preset"

    @staticmethod
    def _records_state(records) -> list[tuple]:
        return [
            (
                bool(record.get("rowEnabled")),
                (
                    str(record.get("column") or ""),
                    record.get("relation"),
                    record.get("value"),
                ),
                "begin" if index == 0
                else "or" if record.get("operator") == "or" else "and",
            )
            for index, record in enumerate(records)
        ]

    @staticmethod
    def _records_from_config(config: str) -> list[dict]:
        import json

        root = ElementTree.fromstring(config)
        node = root.find("./filter/values")
        packed = json.loads(node.text or "[]") if node is not None else []
        main = [
            item for item in packed
            if isinstance(item, dict) and item.get("prefix") == "main_body"
        ]
        search_ops = next(
            (
                item for item in packed
                if isinstance(item, dict)
                and item.get("prefix") == "search_ops"
            ),
            {},
        )
        ops = search_ops.get("ops") or []
        records = []
        for index, item in enumerate(main):
            column = item.get("main_body_column")
            relation = item.get("main_body_relation")
            if relation == "expression":
                relation = item.get("main_body_op")
            records.append({
                "column": column,
                "relation": relation,
                "value": item.get("main_body_value"),
                "rowEnabled": item.get("main_body_enabled") == "on",
                "operator": (
                    "begin" if index == 0
                    else "or"
                    if index - 1 < len(ops) and ops[index - 1] == "or"
                    else "and"
                ),
                "isDefault": index == 0,
            })
        return records

    def _set_busy(self, value: bool, error: str = "") -> None:
        self._busy = value
        self._preset_error = error
        self.stateChanged.emit()

    def _run_server(self, callback, result_handler) -> None:
        try:
            from thlib.environment import env_inst
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            worker = env_inst.server_pool.add_task(callback)
            self._workers.add(worker)
            worker.result.connect(result_handler)
            worker.error.connect(self._preset_failed)
            worker.finished.connect(lambda: self._workers.discard(worker))
            worker.start()
            self._set_busy(True)
        except Exception as error:
            self._set_busy(False, str(error))
            self._notify(str(error))

    @Slot()
    def load_presets(self) -> None:
        context = self._current_context()
        key = self._key(context)
        if not all(key[:2]):
            self.presets.clear()
            return
        project_code = key[0]
        search_type = key[1]
        tab_id = key[2]
        tab_name = str(context.get("tab_name") or tab_id)

        def query():
            import thlib.tactic_classes as tc
            server = tc.server_start(project=project_code)
            rows = server.query(
                "config/widget_config",
                [
                    ("view", "like", f"%{tab_name}"),
                    ("search_type", search_type),
                    ("category", "search_filter"),
                ],
                ["code", "view", "title", "config"],
            )
            result = []
            for row in rows or []:
                try:
                    records = self._records_from_config(
                        str(row.get("config") or "")
                    )
                except (ElementTree.ParseError, ValueError, TypeError):
                    records = []
                result.append({
                    "code": str(row.get("code") or ""),
                    "view": str(row.get("view") or ""),
                    "title": str(
                        row.get("title") or row.get("view") or "Preset"
                    ),
                    "records": records,
                })
            return result, key

        self._run_server(query, self._presets_loaded)

    @Slot(object)
    def _presets_loaded(self, payload) -> None:
        records, key = payload
        if key != self._context_key:
            return
        self.presets.replace(records)
        pending_row = next(
            (
                index for index, preset in enumerate(records)
                if preset.get("view") == self._pending_view
            ),
            -1,
        )
        self._pending_view = ""
        if pending_row < 0 and self._selected_preset < 0:
            from thlib.environment import env_read_config
            saved = env_read_config(
                filename="ui_filter_editor",
                unique_id=self._editor_path(self._current_context()),
                long_abs_path=True,
            ) or {}
            try:
                pending_row = int(saved.get("presets_combo_box", -1))
            except (TypeError, ValueError):
                pending_row = -1
        self._selected_preset = min(
            max(pending_row, self._selected_preset),
            len(records) - 1,
        )
        self._set_busy(False)
        if 0 <= self._selected_preset < len(records):
            self.select_preset(self._selected_preset)

    @Slot(object)
    def _preset_failed(self, error) -> None:
        payload, worker = error
        self._workers.discard(worker)
        message = str(payload.get("exception") or error)
        self._set_busy(False, message)
        self._notify(message)

    @Slot(int)
    def select_preset(self, row: int) -> None:
        if not 0 <= row < len(self.presets._records):
            self._selected_preset = -1
            self.stateChanged.emit()
            return
        preset = self.presets._records[row]
        self._selected_preset = row
        self._replace_records(preset.get("records") or [])
        self._title = str(preset.get("title") or self._title)
        self._validate()
        from thlib.environment import env_write_config
        env_write_config(
            {"presets_combo_box": row},
            filename="ui_filter_editor",
            unique_id=self._editor_path(self._current_context()),
            long_abs_path=True,
        )
        self.stateChanged.emit()

    def _preset_data(self, title: str, view: str) -> dict:
        import thlib.tactic_classes as tc

        context = self._current_context()
        packed = tc.pack_tactic_search_view(
            self._records_state(self.model._records)
        )
        return {
            "description": {"data": ""},
            "view": view,
            "login": "",
            "category": "search_filter",
            "search_type": context.get("search_type"),
            "title": title,
            "config": (
                "<config>\n    <filter>\n"
                f'        <values type="json">{packed}</values>\n'
                "    </filter>\n</config>"
            ),
        }

    def _save_preset(self, title: str, view: str = "") -> None:
        title = str(title or "").strip()
        if not title or not self._validate():
            self._notify(self._validation_error or "Enter a preset name.")
            return
        context = self._current_context()
        key = self._key(context)
        if not view:
            view = (
                "link_search:{}:{}".format(
                    self._preset_name(title),
                    context.get("tab_name") or key[2],
                )
            )
        data = self._preset_data(title, view)

        def save():
            import thlib.tactic_classes as tc
            server = tc.server_start(project=key[0])
            current = server.query(
                "config/widget_config",
                [("view", view), ("search_type", key[1])],
                ["code"],
                single=True,
            )
            if current:
                search_key = server.build_search_key(
                    "config/widget_config",
                    current["code"],
                    project_code=key[0],
                )
                server.insert_update(search_key, data, triggers=False)
            else:
                server.insert("config/widget_config", data, triggers=False)
            return view, key

        self._run_server(save, self._preset_saved)

    @Slot(str)
    def save_as(self, title: str) -> None:
        self._save_preset(title)

    @Slot(str)
    def duplicate(self, title: str) -> None:
        self._save_preset(title)

    @Slot(str)
    def rename(self, title: str) -> None:
        if not 0 <= self._selected_preset < len(self.presets._records):
            self._notify("Select a preset first.")
            return
        view = self.presets._records[self._selected_preset].get("view") or ""
        self._save_preset(title, view)

    @Slot()
    def update_selected(self) -> None:
        if not 0 <= self._selected_preset < len(self.presets._records):
            self._notify("Select a preset first.")
            return
        preset = self.presets._records[self._selected_preset]
        self._save_preset(
            str(preset.get("title") or self._title),
            str(preset.get("view") or ""),
        )

    @Slot(object)
    def _preset_saved(self, payload) -> None:
        view, key = payload
        if key != self._context_key:
            return
        self._set_busy(False)
        self._pending_view = view
        self._selected_preset = -1
        self.load_presets()

    @Slot()
    def delete_selected(self) -> None:
        if not 0 <= self._selected_preset < len(self.presets._records):
            self._notify("Select a preset first.")
            return
        preset = dict(self.presets._records[self._selected_preset])
        context = self._current_context()
        key = self._key(context)

        def remove():
            import thlib.tactic_classes as tc
            server = tc.server_start(project=key[0])
            current = server.query(
                "config/widget_config",
                [("code", preset.get("code"))],
                single=True,
            )
            if current:
                server.delete_sobject(current["__search_key__"])
            return key

        self._run_server(remove, self._preset_deleted)

    @Slot(object)
    def _preset_deleted(self, key) -> None:
        if key != self._context_key:
            return
        self._selected_preset = -1
        self._set_busy(False)
        self.load_presets()

    @staticmethod
    def _pipeline_values(stype) -> list:
        pipelines = getattr(stype, "pipeline", None) or {}
        return list(
            pipelines.values()
            if hasattr(pipelines, "values") else pipelines.itervalues()
        )

    def _process_path(self, context: dict) -> str:
        return "ui_search/checkin_out/{}/{}/{}".format(
            context.get("project_type") or "",
            context.get("project_code") or "",
            context.get("tab_name") or context.get("tab_id") or "",
        )

    def _editor_path(self, context: dict) -> str:
        return "ui_search/{}/{}/{}".format(
            context.get("project_type") or "",
            context.get("project_code") or "",
            context.get("tab_name") or context.get("tab_id") or "",
        )

    def _build_process_model(self, context: dict) -> None:
        stype = context.get("stype")
        project = context.get("project")
        if not stype or not project:
            self.processes.clear()
            return
        records = []
        schema = getattr(stype, "schema", None)
        for child in getattr(schema, "children", []) or []:
            child_stype = (project.stypes or {}).get(child.get("from"))
            if not child_stype:
                continue
            code = str(child_stype.info.get("code") or "")
            title = str(
                child_stype.info.get("title")
                or child_stype.info.get("name")
                or code
            )
            records.append({
                "key": code, "title": title, "kind": "child",
                "group": "", "depth": 0, "itemEnabled": True,
            })
            self._append_pipeline_records(records, child_stype, 1)
        self._append_pipeline_records(records, stype, 0)
        for key in ("publish", "attachment", "icon"):
            records.append({
                "key": key, "title": key.title(), "kind": "builtin",
                "group": "", "depth": 0, "itemEnabled": True,
            })
        self.processes.replace(records)
        self._load_process_settings(context)

    def _append_pipeline_records(self, records: list, stype, depth: int) -> None:
        for pipeline in self._pipeline_values(stype):
            info = getattr(pipeline, "info", {}) or {}
            group = str(info.get("code") or "")
            processes = (
                getattr(pipeline, "process", None)
                or getattr(pipeline, "pipeline", None)
                or {}
            )
            for key in processes:
                records.append({
                    "key": str(key),
                    "title": str(key).replace("_", " ").title(),
                    "kind": "process",
                    "group": group,
                    "depth": depth,
                    "itemEnabled": True,
                })

    def _load_process_settings(self, context: dict) -> None:
        from thlib.environment import env_read_config

        ignore = env_read_config(
            filename="process_ignore_dict",
            unique_id=self._process_path(context),
            long_abs_path=True,
        ) or {}
        for index, record in enumerate(self.processes._records):
            ignored = (
                record["key"] in (ignore.get("children") or [])
                if record["kind"] == "child"
                else record["key"] in (ignore.get("builtins") or [])
                if record["kind"] == "builtin"
                else record["key"] in (
                    (ignore.get("processes") or {}).get(record["group"]) or []
                )
            )
            if ignored:
                self.processes.set_value(index, "itemEnabled", False)

    @Slot(int, bool)
    def set_process_enabled(self, row: int, enabled: bool) -> None:
        self.processes.set_value(row, "itemEnabled", enabled)

    @Slot(str)
    def toggle_process_kind(self, kind: str) -> None:
        rows = [
            (index, record)
            for index, record in enumerate(self.processes._records)
            if kind == "all" or record.get("kind") == kind
        ]
        enabled = any(
            not record.get("itemEnabled") for _, record in rows
        )
        for index, _record in rows:
            self.processes.set_value(index, "itemEnabled", enabled)

    def _process_ignore(self) -> dict:
        ignore = {
            "children": [],
            "processes": {},
            "builtins": [],
            "show_builtins": False,
        }
        for record in self.processes._records:
            if record.get("kind") == "process":
                ignore["processes"].setdefault(record.get("group"), [])
            if record.get("itemEnabled"):
                continue
            if record.get("kind") == "child":
                ignore["children"].append(record.get("key"))
            elif record.get("kind") == "builtin":
                ignore["builtins"].append(record.get("key"))
            else:
                ignore["processes"][record.get("group")].append(
                    record.get("key")
                )
        if not any((
            ignore["children"], ignore["builtins"],
            any(ignore["processes"].values()),
        )):
            return {}
        return ignore

    def _save_process_settings(self) -> None:
        from thlib.environment import env_write_config

        context = self._current_context()
        env_write_config(
            self._process_ignore(),
            filename="process_ignore_dict",
            unique_id=self._process_path(context),
            long_abs_path=True,
        )
