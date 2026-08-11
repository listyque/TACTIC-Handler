from __future__ import annotations

import json

from PySide6.QtCore import QObject, Property, QSettings, Signal, Slot

from .workspace_models.records import RecordListModel


class ColumnsEditorController(QObject):
    stateChanged = Signal()
    applied = Signal()

    _hidden = {
        "__search_key__", "__search_type__", "__tasks_count__",
        "__notes_count__", "__snapshots__",
    }

    def __init__(self, application, parent=None):
        super().__init__(parent)
        self._application = application
        self._settings = QSettings("TACTIC-Handler", "modern-qml")
        self.model = RecordListModel((
            "name", "label", "dataType", "displayVisible", "displayWidth", "order",
            "readOnly",
        ))
        self._source_records = []
        self._stype_code = ""
        self._title = "Columns"
        self._dirty = False
        self._error = ""
        application.selected_node_changed.connect(self.reload)
        application.project_changed.connect(lambda *_args: self.reload())
        self.reload()

    @Property(str, notify=stateChanged)
    def title(self):
        return self._title

    @Property(bool, notify=stateChanged)
    def dirty(self):
        return self._dirty

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Property(bool, notify=stateChanged)
    def hasColumns(self):
        return bool(self.model._records)

    def _current_stype(self):
        node = self._application.workspace_model.node_for(
            self._application.selected_node_id
        )
        if node and node.source:
            try:
                return node.source.get_stype()
            except (AttributeError, TypeError):
                node = None
        tab = self._application._current_tab()
        return tab.stype if tab else None

    @staticmethod
    def _column_label(name, info):
        return str(
            info.get("label")
            or info.get("title")
            or str(name).replace("_", " ").title()
        )

    def _settings_key(self):
        project = self._application._current_project_code or "default"
        return f"columns/{project}/{self._stype_code}"

    def _stored_options(self):
        raw = self._settings.value(self._settings_key(), "", type=str)
        try:
            values = json.loads(raw) if raw else []
        except (TypeError, ValueError):
            return []
        return values if isinstance(values, list) else []

    @Slot()
    def reload(self):
        stype = self._current_stype()
        if not stype:
            self._stype_code = ""
            self._title = "Columns"
            self._source_records = []
            self.model.clear()
            self._dirty = False
            self._error = ""
            self.stateChanged.emit()
            return
        try:
            columns_info = dict(stype.get_columns_info() or {})
            stype_code = str(stype.get_code() or "")
            if self._dirty and stype_code == self._stype_code:
                return
            self._stype_code = stype_code
            self._title = str(
                stype.get_pretty_name() or self._stype_code or "Columns"
            )
        except (AttributeError, TypeError, ValueError):
            columns_info = {}
        stored = {
            str(record.get("name") or ""): record
            for record in self._stored_options()
            if isinstance(record, dict)
        }
        records = []
        for fallback_order, (name, info) in enumerate(columns_info.items()):
            if name in self._hidden or str(name).startswith("__"):
                continue
            info = dict(info or {})
            option = stored.get(str(name), {})
            records.append({
                "name": str(name),
                "label": str(
                    option.get("label")
                    or self._column_label(name, info)
                ),
                "dataType": str(info.get("data_type") or "text"),
                "displayVisible": bool(
                    option.get("displayVisible", option.get("visible", True))
                ),
                "displayWidth": max(48, min(
                    640, int(
                        option.get("displayWidth", option.get("width", 160))
                    )
                )),
                "order": int(option.get("order", fallback_order)),
                "readOnly": str(name) in {
                    "id", "code", "project_code", "timestamp", "login",
                },
            })
        records.sort(key=lambda record: (record["order"], record["name"]))
        for order, record in enumerate(records):
            record["order"] = order
        self._source_records = [dict(record) for record in records]
        self.model.replace(records)
        self._dirty = False
        self._error = ""
        self.stateChanged.emit()

    def _set_record(self, row, **values):
        if not 0 <= row < len(self.model._records):
            return
        record = dict(self.model._records[row])
        record.update(values)
        self.model._records[row] = record
        index = self.model.index(row, 0)
        self.model.dataChanged.emit(
            index, index, list(self.model._role_ids.values())
        )
        self._dirty = self.model._records != self._source_records
        self._error = ""
        self.stateChanged.emit()

    @Slot(int, bool)
    def set_visible(self, row, visible):
        self._set_record(row, displayVisible=bool(visible))

    @Slot(int, int)
    def set_width(self, row, width):
        self._set_record(
            row, displayWidth=max(48, min(640, int(width)))
        )

    @Slot(int, str)
    def set_label(self, row, label):
        label = str(label or "").strip()
        if not label:
            self._error = "Column label cannot be empty."
            self.stateChanged.emit()
            return
        self._set_record(row, label=label)

    @Slot(int, int)
    def move(self, row, offset):
        target = row + int(offset)
        if not 0 <= row < len(self.model._records) or not 0 <= target < len(
            self.model._records
        ):
            return
        records = [dict(record) for record in self.model._records]
        records.insert(target, records.pop(row))
        for order, record in enumerate(records):
            record["order"] = order
        self.model.replace(records)
        self._dirty = records != self._source_records
        self.stateChanged.emit()

    def _validation_error(self):
        if not self.model._records:
            return "No columns are available for this search type."
        if not any(
            record["displayVisible"] for record in self.model._records
        ):
            return "At least one column must remain visible."
        labels = [record["label"].strip() for record in self.model._records]
        if any(not label for label in labels):
            return "Column labels cannot be empty."
        return ""

    @Slot(result=bool)
    def apply(self):
        error = self._validation_error()
        if error:
            self._error = error
            self.stateChanged.emit()
            return False
        records = [dict(record) for record in self.model._records]
        self._settings.setValue(
            self._settings_key(), json.dumps(records, ensure_ascii=False)
        )
        self._settings.sync()
        self._source_records = records
        self._dirty = False
        self._error = ""
        self._application.workspace_state.columns_model.replace([
            {
                "title": record["label"],
                "checked": record["displayVisible"],
            }
            for record in records
        ])
        self._application.results_view_changed.emit()
        self.applied.emit()
        self.stateChanged.emit()
        return True

    @Slot()
    def cancel(self):
        self.model.replace(self._source_records)
        self._dirty = False
        self._error = ""
        self.stateChanged.emit()

    @Slot()
    def reset(self):
        records = []
        for order, record in enumerate(self.model._records):
            info = dict(record)
            info.update({
                "label": record["name"].replace("_", " ").title(),
                "displayVisible": True,
                "displayWidth": 160,
                "order": order,
            })
            records.append(info)
        self.model.replace(records)
        self._dirty = records != self._source_records
        self.stateChanged.emit()

    @Slot("QVariantList", result="QVariantList")
    def order_field_records(self, values):
        by_name = {
            str(value.get("fieldName") or ""): dict(value)
            for value in (values or [])
        }
        result = []
        configured = set()
        for option in self._source_records:
            name = option["name"]
            configured.add(name)
            if option["displayVisible"] and name in by_name:
                value = by_name[name]
                value["fieldLabel"] = option["label"]
                value["displayWidth"] = option["displayWidth"]
                result.append(value)
        result.extend(
            value for name, value in by_name.items()
            if name not in configured
        )
        return result

    @Slot(str, str, result=bool)
    def save_column_value(self, column, value):
        column = str(column or "")
        record = next(
            (
                record for record in self.model._records
                if record["name"] == column
            ),
            None,
        )
        if not record or record["readOnly"]:
            self._error = "This column is read-only."
            self.stateChanged.emit()
            return False
        value = str(value or "")
        try:
            if record["dataType"] in {"integer", "int", "serial"}:
                int(value)
            elif record["dataType"] in {
                "float", "double", "decimal", "numeric",
            }:
                float(value)
        except ValueError:
            self._error = (
                f"Invalid {record['dataType']} value for {record['label']}."
            )
            self.stateChanged.emit()
            return False
        node_id = self._application.selected_node_id
        self._application.update_selected_item_fields(
            node_id, {column: value}
        )
        self._error = ""
        self.stateChanged.emit()
        return True
