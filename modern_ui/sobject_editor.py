from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QObject,
    Property,
    Qt,
    QUrl,
    Signal,
    Slot,
)


class SObjectFieldModel(QAbstractListModel):
    FieldNameRole = Qt.UserRole + 1
    TitleRole = Qt.UserRole + 2
    FieldTypeRole = Qt.UserRole + 3
    OriginalTypeRole = Qt.UserRole + 4
    FieldValueRole = Qt.UserRole + 5
    DefaultValueRole = Qt.UserRole + 6
    RequiredRole = Qt.UserRole + 7
    ReadOnlyRole = Qt.UserRole + 8
    OptionsRole = Qt.UserRole + 9
    ErrorRole = Qt.UserRole + 10

    validationChanged = Signal()
    valuesChanged = Signal()
    countChanged = Signal()

    _roles = {
        FieldNameRole: b"fieldName",
        TitleRole: b"title",
        FieldTypeRole: b"fieldType",
        OriginalTypeRole: b"originalType",
        FieldValueRole: b"fieldValue",
        DefaultValueRole: b"defaultValue",
        RequiredRole: b"fieldRequired",
        ReadOnlyRole: b"fieldReadOnly",
        OptionsRole: b"fieldOptions",
        ErrorRole: b"fieldError",
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._fields: list[dict] = []

    def roleNames(self) -> dict[int, bytes]:
        return self._roles

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._fields)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._fields):
            return None
        field = self._fields[index.row()]
        key = self._roles.get(role)
        return field.get(key.decode()) if key else None

    def replace(self, fields) -> None:
        self.beginResetModel()
        self._fields = [dict(field) for field in fields]
        self.endResetModel()
        self.countChanged.emit()
        self._validate_all()
        self.valuesChanged.emit()

    def clear(self) -> None:
        self.replace([])

    @Slot(int, "QVariant")
    def setValue(self, row: int, value) -> None:
        if not 0 <= row < len(self._fields):
            return
        field = self._fields[row]
        if field["fieldType"] in {"file", "preview", "thumbnail"}:
            if isinstance(value, QUrl):
                value = value.toLocalFile() or value.toString()
            elif str(value or "").startswith("file:"):
                url = QUrl(str(value))
                value = url.toLocalFile() or str(value)
        if field["fieldReadOnly"] or field["fieldValue"] == value:
            return
        field["fieldValue"] = value
        self._validate_row(row)
        index = self.index(row)
        self.dataChanged.emit(
            index,
            index,
            [self.FieldValueRole, self.ErrorRole],
        )
        self.valuesChanged.emit()

    @Slot(result="QVariantMap")
    def values(self) -> dict:
        return {
            field["fieldName"]: self._typed_value(field)
            for field in self._fields
            if field["fieldName"]
        }

    def submission_values(self, mode: str) -> dict:
        values = {}
        for field in self._fields:
            if (
                field["fieldReadOnly"]
                or field["fieldType"] in {
                    "parent", "preview", "thumbnail",
                }
            ):
                continue
            if (
                mode == "edit"
                and field["fieldValue"] == field["defaultValue"]
            ):
                continue
            values[field.get("submitName") or field["fieldName"]] = (
                self._typed_value(field)
            )
        return values

    def preview_paths(self) -> list[str]:
        return [
            str(field["fieldValue"])
            for field in self._fields
            if field["fieldType"] == "preview" and field["fieldValue"]
        ]

    @Property(bool, notify=validationChanged)
    def valid(self) -> bool:
        return not any(field["fieldError"] for field in self._fields)

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return len(self._fields)

    @staticmethod
    def _empty(value) -> bool:
        return value is None or (
            isinstance(value, str) and not value.strip()
        )

    @classmethod
    def _error_for(cls, field: dict) -> str:
        value = field["fieldValue"]
        if field["fieldRequired"] and cls._empty(value):
            return "This field is required"
        if cls._empty(value):
            return ""
        try:
            if field["fieldType"] == "integer":
                int(str(value))
            elif field["fieldType"] == "float":
                float(str(value).replace(",", "."))
            elif field["fieldType"] == "date":
                datetime.strptime(str(value), "%Y-%m-%d")
            elif field["fieldType"] == "datetime":
                datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            if field["fieldType"] in {"date", "datetime"}:
                return (
                    "Use YYYY-MM-DD"
                    if field["fieldType"] == "date"
                    else "Use YYYY-MM-DD HH:MM:SS"
                )
            return (
                "Enter a whole number"
                if field["fieldType"] == "integer"
                else "Enter a number"
            )
        return ""

    @staticmethod
    def _typed_value(field: dict):
        value = field["fieldValue"]
        if value is None or value == "":
            return value
        try:
            if field["fieldType"] == "integer":
                return int(str(value))
            if field["fieldType"] == "float":
                return float(str(value).replace(",", "."))
            if field["fieldType"] == "bool":
                return bool(value)
        except (TypeError, ValueError):
            pass
        return value

    def _validate_row(self, row: int) -> None:
        field = self._fields[row]
        previous = field["fieldError"]
        field["fieldError"] = self._error_for(field)
        if previous != field["fieldError"]:
            self.validationChanged.emit()

    def _validate_all(self) -> None:
        for field in self._fields:
            field["fieldError"] = self._error_for(field)
        self.validationChanged.emit()


class SObjectEditorController(QObject):
    stateChanged = Signal()
    saved = Signal(str)

    _widget_types = {
        "pyasm.widget.input_wdg.TextAreaWdg": "multiline",
        "pyasm.widget.input_wdg.CheckboxWdg": "bool",
        "pyasm.prod.web.prod_input_wdg.CurrentCheckboxWdg": "bool",
        "tactic.ui.widget.calendar_wdg.CalendarInputWdg": "datetime",
        "pyasm.widget.input_wdg.SelectWdg": "enum",
        "tactic.ui.input.process_group_select_wdg.ProcessGroupSelectWdg": "user",
        "pyasm.prod.web.prod_input_wdg.ProjectSelectWdg": "project",
        "tactic.ui.input.process_context_wdg.ProcessInputWdg": "process",
        "tactic.ui.input.process_context_wdg.SubContextInputWdg": "string",
        "tactic.ui.widget.misc_input_wdg.TaskStatusSelectWdg": "enum",
        "tactic.ui.input.pipeline_input_wdg.PipelineInputWdg": "process",
        "tactic.ui.input.task_input_wdg.TaskSObjectInputWdg": "parent",
        "tactic.ui.widget.upload_wdg.SimpleUploadWdg": "preview",
        "pyasm.widget.input_wdg.ThumbInputWdg": "thumbnail",
    }
    _basic_widgets = {
        "pyasm.widget.input_wdg.TextWdg",
        *_widget_types,
    }
    _data_types = {
        "integer": "integer",
        "int": "integer",
        "serial": "integer",
        "float": "float",
        "double": "float",
        "decimal": "float",
        "numeric": "float",
        "boolean": "bool",
        "bool": "bool",
        "date": "date",
        "datetime": "datetime",
        "timestamp": "datetime",
        "text": "multiline",
    }

    def __init__(self, context, notify=None, parent=None) -> None:
        super().__init__(parent)
        self._context = context
        self._notify = notify or (lambda _message: None)
        self._busy = False
        self._error = ""
        self._title = ""
        self._mode = "insert"
        self._request_id = 0
        self._worker = None
        self._edit_widget = None
        self._context_data = {}
        self.model = SObjectFieldModel(self)

    @Slot()
    def begin_session(self) -> None:
        context = dict(self._context() or {})
        stype = context.get("stype")
        project_code = str(context.get("project_code") or "")
        search_type = str(context.get("search_type") or "")
        if stype is None or not project_code or not search_type:
            self._set_error("Select a project and search type first")
            self.model.clear()
            return
        self._context_data = context
        self._mode = (
            "edit"
            if (
                context.get("mode") == "edit"
                and context.get("sobject") is not None
            )
            else "insert"
        )
        sobject = context.get("sobject")
        parent_sobject = context.get("parent_sobject")
        search_key = (
            sobject.get_search_key()
            if self._mode == "edit" and sobject is not None else ""
        )
        parent_key = (
            parent_sobject.get_search_key()
            if parent_sobject is not None else None
        )
        self._title = str(
            getattr(stype, "get_pretty_name", lambda: search_type)()
            or search_type
        )
        self._request_id += 1
        request_id = self._request_id
        self._busy = True
        self._error = ""
        self._edit_widget = None
        self.stateChanged.emit()

        from thlib import tactic_classes as tc
        from thlib import tactic_query as tq
        from thlib.environment import env_inst

        worker = env_inst.server_pool.add_task(
            tc.execute_procedure_serverside,
            tq.query_EditWdg,
            {
                "args": {
                    "mode": self._mode,
                    "input_prefix": self._mode,
                    "search_key": search_key,
                    "parent_key": parent_key,
                    "search_type": search_type,
                    "view": self._mode,
                },
                "search_type": search_type,
            },
            project=project_code,
        )
        self._worker = worker
        worker.result.connect(
            lambda result: self._schema_loaded(
                request_id, stype, context, result
            )
        )
        worker.error.connect(
            lambda error: self._schema_failed(request_id, error)
        )
        worker.start()

    def _schema_loaded(
        self,
        request_id: int,
        stype,
        context: dict,
        result,
    ) -> None:
        if request_id != self._request_id:
            return
        edit = dict((result or {}).get("EditWdg") or {})
        if edit.get("security_denied"):
            self._set_error("Access to this edit view is denied")
            self.model.clear()
            return
        edit["stype"] = stype
        edit["sobject"] = (
            context.get("sobject")
            if context.get("sobject") is not None
            else (
                context.get("parent_sobject")
                if self._mode == "insert" else None
            )
        )
        edit["parent_sobject"] = context.get("parent_sobject")
        edit["info_dict"] = context.get("info_dict")
        from thlib.tactic_widgets import TacticEditWdg
        self._edit_widget = TacticEditWdg(edit)
        self._edit_widget.set_stype(stype)
        fields = [
            field
            for source in (result or {}).get("InputWidgets") or []
            if (
                field := self._field_descriptor(
                    stype,
                    context,
                    source,
                )
            )
        ]
        self.model.replace(fields)
        self._busy = False
        self._error = "" if fields else "The edit view contains no supported fields"
        self._worker = None
        self.stateChanged.emit()

    def _schema_failed(self, request_id: int, error) -> None:
        if request_id != self._request_id:
            return
        message = str(error[0] if isinstance(error, (tuple, list)) else error)
        self.model.clear()
        self._set_error(message or "Could not load the edit view")
        self._notify(self._error)

    def _field_descriptor(
        self,
        stype,
        context: dict,
        source,
    ) -> dict | None:
        source = dict(source or {})
        name = str(source.get("name") or "")
        class_name = str(source.get("class_name") or "")
        if not name or class_name not in self._basic_widgets:
            return None
        action = dict(source.get("action_options") or {})
        column = str(action.get("column") or name)
        original_type = str(stype.get_column_data_type(column) or "text")
        field_type = self._widget_types.get(
            class_name,
            self._data_types.get(original_type.lower(), "string"),
        )
        if (
            class_name == "tactic.ui.widget.calendar_wdg.CalendarInputWdg"
            and original_type.lower() == "date"
        ):
            field_type = "date"
        display = source.get("__display_values__")
        values = list(source.get("values") or [])
        labels = list(source.get("labels") or [])
        if isinstance(display, dict):
            if not values:
                values = list(display.get("values") or [])
            if not labels:
                labels = list(display.get("labels") or [])
        options = [
            {
                "label": str(labels[index] if index < len(labels) else value),
                "value": value,
            }
            for index, value in enumerate(values)
        ]
        options = self._special_options(
            field_type,
            context,
            options,
            class_name,
        )
        default = self._default_value(source, field_type)
        sobject = context.get("sobject")
        if self._mode == "edit" and sobject is not None:
            try:
                info = sobject.get_info() or {}
                if column in info:
                    default = info.get(column)
                elif default is None or default == "":
                    default = sobject.get_value(column)
            except (AttributeError, KeyError, TypeError):
                pass
        elif self._mode == "insert":
            info = dict(context.get("info_dict") or {})
            if column in info:
                default = info[column]
        if field_type == "parent":
            parent = context.get("parent_sobject")
            default = (
                parent.get_title()
                if parent is not None else str(default or "")
            )
        elif field_type in {"preview", "thumbnail"}:
            default = ""
        kwargs = dict(source.get("kwargs") or {})
        required = self._flag(
            source.get("required")
            or kwargs.get("required")
            or action.get("required")
        )
        return {
            "fieldName": name,
            "submitName": column,
            "title": str(source.get("title") or name.replace("_", " ").title()),
            "fieldType": field_type,
            "originalType": original_type,
            "fieldValue": default,
            "defaultValue": default,
            "fieldRequired": required,
            "fieldReadOnly": self._flag(
                source.get("read_only")
                or kwargs.get("read_only")
                or action.get("read_only")
            ) or field_type in {"parent", "thumbnail"},
            "fieldOptions": options,
            "fieldError": "",
        }

    @staticmethod
    def _special_options(
        field_type: str,
        context: dict,
        options: list[dict],
        class_name: str = "",
    ) -> list[dict]:
        if options or field_type not in {"user", "process"}:
            return options
        if field_type == "user":
            try:
                from thlib.environment import env_inst
                logins = (env_inst.get_all_logins() or {}).values()
                return [
                    {
                        "label": str(login.get_display_name()),
                        "value": str(login.get_login()),
                    }
                    for login in logins
                ]
            except (AttributeError, KeyError, TypeError):
                return []
        if class_name == "tactic.ui.input.pipeline_input_wdg.PipelineInputWdg":
            stype = context.get("stype")
            try:
                pipelines = stype.get_pipeline() or {}
            except (AttributeError, KeyError, TypeError):
                pipelines = {}
            result = []
            for code, pipeline in pipelines.items():
                try:
                    info = dict(pipeline.get_info() or {})
                except (AttributeError, TypeError):
                    info = {}
                result.append({
                    "label": str(
                        info.get("name") or info.get("label") or code
                    ),
                    "value": str(code),
                })
            return sorted(result, key=lambda item: item["label"].casefold())
        parent = context.get("parent_sobject")
        if parent is None:
            return []
        try:
            pipelines = parent.get_stype().get_pipeline() or {}
            pipeline = pipelines.get(parent.get_pipeline_code())
            names = pipeline.get_all_pipeline_names() if pipeline else []
        except (AttributeError, KeyError, TypeError):
            names = []
        return [
            {"label": str(name).replace("_", " ").title(), "value": name}
            for name in names
        ]

    @staticmethod
    def _default_value(source: dict, field_type: str):
        display = source.get("__display_values__")
        if isinstance(display, (list, tuple)) and display:
            value = display[0]
        elif isinstance(display, dict):
            values = display.get("values") or display.get("labels") or []
            value = values[0] if values else None
        else:
            kwargs = dict(source.get("kwargs") or {})
            value = kwargs.get("default")
        if field_type == "bool":
            return value in (True, 1, "1", "true", "True", "on")
        return "" if value is None else value

    @staticmethod
    def _flag(value) -> bool:
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    def _set_error(self, message: str) -> None:
        self._busy = False
        self._error = str(message)
        self._worker = None
        self.stateChanged.emit()

    @Slot()
    def submit(self) -> None:
        if self._busy or not self._edit_widget:
            return
        if not self.model.valid:
            self._error = "Correct the highlighted fields"
            self.stateChanged.emit()
            return
        values = self.model.submission_values(self._mode)
        self._busy = True
        self._error = ""
        self.stateChanged.emit()

        from thlib.environment import env_inst
        worker = env_inst.server_pool.add_task(
            self._edit_widget.commit,
            values,
        )
        request_id = self._request_id
        self._worker = worker
        worker.result.connect(
            lambda result: self._save_finished(request_id, result)
        )
        worker.error.connect(
            lambda error: self._save_failed(request_id, error)
        )
        worker.start()

    def _save_finished(self, request_id: int, result) -> None:
        if request_id != self._request_id:
            return
        action = "updated" if self._mode == "edit" else "created"
        try:
            search_key = str(
                result.get("__search_key__")
                or result.get("search_key")
                or result.get("code")
                or ""
            )
        except AttributeError:
            search_key = ""
        if not search_key and self._mode == "edit":
            sobject = self._context_data.get("sobject")
            if sobject is not None:
                search_key = str(sobject.get_search_key() or "")
        self._busy = False
        self._worker = None
        self._notify(f"sObject {action}")
        refresh = self._context_data.get("refresh")
        if callable(refresh):
            refresh()
        self.stateChanged.emit()
        self.saved.emit(search_key)

    def _save_failed(self, request_id: int, error) -> None:
        if request_id != self._request_id:
            return
        payload = error[0] if isinstance(error, (tuple, list)) else error
        if isinstance(payload, dict):
            message = str(
                payload.get("exception")
                or payload.get("message")
                or payload.get("traceback")
                or payload
            )
        else:
            message = str(payload)
        self._set_error(message or "The server rejected the changes")
        self._notify(self._error)

    @Slot(result="QVariantMap")
    def values(self) -> dict:
        return self.model.values()

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error

    @Property(str, notify=stateChanged)
    def title(self) -> str:
        return self._title

    @Property(str, notify=stateChanged)
    def mode(self) -> str:
        return self._mode

    @Property(str, notify=stateChanged)
    def submitLabel(self) -> str:
        return "Save changes" if self._mode == "edit" else "Create"
