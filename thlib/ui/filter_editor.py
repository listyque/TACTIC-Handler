from __future__ import annotations

import re

from PySide6.QtCore import QObject, Property, Signal, Slot

from .workspace import RecordListModel


class FilterEditorController(QObject):
    stateChanged = Signal()
    presetsChanged = Signal(str, str)

    _numeric_types = {"integer", "float", "currency"}
    _boolean_values = {"true", "false", "1", "0", "yes", "no"}

    def __init__(
        self,
        source_records,
        column_records,
        relation_choices,
        notify,
        can_apply=None,
        context=None,
        stage_records=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._source_records = source_records
        self._column_records = column_records
        self._relation_choices = relation_choices
        self._notify = notify
        self._can_apply = can_apply or (lambda: True)
        self._context = context or (lambda: {})
        self._stage_records = stage_records
        self._title = ""
        self._validation_error = ""
        self._preset_error = ""
        self._busy = False
        self._selected_preset = -1
        self._pending_view = ""
        self._explicit_preset_request = False
        self._search_type_library = False
        self._restore_saved_selection = True
        self._context_key = ()
        self._workers = set()
        self.model = RecordListModel((
            "column", "relation", "value", "rowEnabled", "operator",
            "isDefault", "dataType",
        ))
        self.presets = RecordListModel((
            "code", "title", "view", "description", "records",
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
            str(context.get("preset_scope") or ""),
        )

    def _current_context(self) -> dict:
        context = dict(self._context() or {})
        if self._search_type_library:
            search_type = str(context.get("search_type") or "").strip()
            context["preset_scope"] = ""
            context["preset_namespace"] = search_type
        return context

    def _context_is_current(self) -> bool:
        return self._context_key == self._key(self._current_context())

    @Slot()
    def begin_session(self) -> None:
        self._restore_saved_selection = not self._explicit_preset_request
        self._begin_session()

    @Slot(str)
    def prepare_search_type_library(self, view: str) -> None:
        """Open the complete Search Type library and select ``view``."""
        self._search_type_library = True
        self._pending_view = str(view or "").strip()
        self._explicit_preset_request = True

    @Slot()
    def end_search_type_library(self) -> None:
        """Return subsequent Advanced Search sessions to their tab scope."""
        self._search_type_library = False
        self._pending_view = ""
        self._explicit_preset_request = False
        # Closing the modal must not load another, now hidden preset list.
        # The next visible Advanced Search synchronizes its own tab context.
        self._context_key = ()
        self._set_busy(False)

    @Slot()
    def begin_search_session(self) -> None:
        """Open Advanced Search without replacing its live filters."""
        self._search_type_library = False
        self._restore_saved_selection = False
        self._begin_session()

    @Slot()
    def sync_search_session(self) -> None:
        """Follow Search Tab changes without reloading the same context."""
        context = self._current_context()
        key = self._key(context)
        if key == self._context_key and all(key[:2]):
            return
        self._restore_saved_selection = False
        self._begin_session()

    def _begin_session(self) -> None:
        context = self._current_context()
        self._context_key = self._key(context)
        records = [dict(record) for record in self._source_records()]
        if not records:
            records = [self._new_record(True)]
        self._replace_records(records)
        self._title = str(context.get("tab_title") or "")
        self._selected_preset = -1
        self._preset_error = ""
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
                # TACTIC Search Views deliberately keep blank conditions as
                # editable placeholders (most commonly the first Name /
                # Contains card before a fixed expression).  They are valid
                # even when the preset contains additional conditions.
                continue
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

    @Property(str, notify=stateChanged)
    def selected_preset_link(self) -> str:
        if not 0 <= self._selected_preset < len(self.presets._records):
            return ""
        from .search_links import build_saved_search_link

        context = self._current_context()
        preset = self.presets._records[self._selected_preset]
        return build_saved_search_link(
            context.get("project_code"),
            context.get("search_type"),
            preset.get("view"),
        )

    @Slot()
    def copy_selected_search_link(self) -> None:
        value = self.selected_preset_link
        if not value:
            self._notify("Select a saved search first.")
            return
        from PySide6.QtGui import QGuiApplication

        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            self._notify("The clipboard is not available.")
            return
        clipboard.setText(value)
        self._notify("Saved search link copied")

    @staticmethod
    def _preset_name(title: str) -> str:
        # Keep the original TACTIC convention (a readable name inside
        # ``link_search:<name>:<tab>``) while supporting non-Latin titles.
        value = re.sub(r"[^\w]+", "_", title.strip().lower(), flags=re.UNICODE)
        return value.strip("_") or "preset"

    def _capture_source_records(self) -> bool:
        """Refresh the preset payload from the live Advanced Search state."""
        context = self._current_context()
        self._context_key = self._key(context)
        records = [dict(record) for record in self._source_records()]
        if not records:
            records = [self._new_record(True)]
        self._replace_records(records)
        self._title = str(context.get("tab_title") or self._title)
        return self._validate()

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
        from .search_presets import records_from_config

        return records_from_config(config)

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
        preset_scope = str(context.get("preset_scope") or "").strip()
        if not all(key[:2]):
            self.presets.clear()
            return
        project_code = key[0]
        search_type = key[1]
        def query():
            from .search_presets import query_search_presets

            return query_search_presets(
                project_code,
                search_type,
                preset_scope,
            ), key

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
        if (
            self._restore_saved_selection
            and pending_row < 0
            and self._selected_preset < 0
        ):
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
        self._explicit_preset_request = False
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
        preset_scope = str(context.get("preset_scope") or "").strip()
        preset_namespace = str(
            context.get("preset_namespace")
            or (
                context.get("tab_name")
                if preset_scope else context.get("search_type")
            )
            or ""
        ).strip()
        if not preset_namespace:
            self._notify("The search tab is not ready yet.")
            return
        if not view:
            view = (
                "link_search:{}:{}".format(
                    self._preset_name(title),
                    preset_namespace,
                )
            )
        data = self._preset_data(title, view)

        def save():
            import thlib.tactic_classes as tc
            server = tc.server_start(project=key[0])
            current = server.query(
                "config/widget_config",
                [("view", view), ("search_type", key[1])],
                ["code", "description"],
                single=True,
            )
            if current:
                # The server description field is opaque metadata.
                # Renaming or updating a search must not replace server data
                # that this editor does not own.
                data.pop("description", None)
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
    def save_current_search_as(self, title: str) -> None:
        if self._capture_source_records():
            self._save_preset(title)

    @Slot(str)
    def duplicate(self, title: str) -> None:
        self._save_preset(title)

    @Slot(str)
    def duplicate_current_search(self, title: str) -> None:
        if self._capture_source_records():
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

    @Slot()
    def update_selected_from_current_search(self) -> None:
        if not 0 <= self._selected_preset < len(self.presets._records):
            self._notify("Select a preset first.")
            return
        preset = dict(self.presets._records[self._selected_preset])
        if not self._capture_source_records():
            return
        self._save_preset(
            str(preset.get("title") or self._title),
            str(preset.get("view") or ""),
        )

    @Slot(int)
    def select_preset_for_current_search(self, row: int) -> None:
        """Load a TACTIC Search View preset into visible search cards."""
        self.select_preset(row)
        if self._selected_preset != row:
            return
        records = [dict(record) for record in self.model._records]
        if self._stage_records is not None:
            self._stage_records(records, self._title)

    @Slot(object)
    def _preset_saved(self, payload) -> None:
        view, key = payload
        if key != self._context_key:
            return
        self.presetsChanged.emit(key[0], key[1])
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
        self.presetsChanged.emit(key[0], key[1])
        self._selected_preset = -1
        self._set_busy(False)
        self.load_presets()

    def _editor_path(self, context: dict) -> str:
        return "ui_search/{}/{}/{}".format(
            context.get("project_type") or "",
            context.get("project_code") or "",
            context.get("tab_name") or context.get("tab_id") or "",
        )
