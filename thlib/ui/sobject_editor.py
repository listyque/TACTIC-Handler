from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import os
from pathlib import Path
import re

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
    DescriptionRole = Qt.UserRole + 11
    IconRole = Qt.UserRole + 12
    WidgetClassRole = Qt.UserRole + 13

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
        DescriptionRole: b"fieldDescription",
        IconRole: b"fieldIcon",
        WidgetClassRole: b"widgetClass",
    }
    _preview_extensions = {
        ".apng", ".avif", ".bmp", ".gif", ".ico", ".jpeg", ".jpg",
        ".png", ".svg", ".tga", ".tif", ".tiff", ".webp",
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
        if field["fieldType"] == "preview" and isinstance(
            value, (list, tuple)
        ):
            value = [self._local_path(item) for item in value if item]
        elif field["fieldType"] in {"file", "preview", "thumbnail"}:
            value = self._local_path(value)
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

    @Slot(int, "QVariantList", result=int)
    def add_preview_files(self, row: int, values) -> int:
        if not 0 <= row < len(self._fields):
            return 0
        field = self._fields[row]
        if field["fieldType"] != "preview" or field["fieldReadOnly"]:
            return 0
        paths = self._preview_values(field["fieldValue"])
        identities = {os.path.normcase(path) for path in paths}
        for value in values or []:
            path = self._local_path(value)
            identity = os.path.normcase(path)
            if (
                path and identity not in identities
                and Path(path).is_file()
                and Path(path).suffix.casefold() in self._preview_extensions
            ):
                paths.append(path)
                identities.add(identity)
        self.setValue(row, paths)
        return len(paths)

    @Slot(int, int)
    def remove_preview_file(self, row: int, index: int) -> None:
        if not 0 <= row < len(self._fields):
            return
        paths = self._preview_values(self._fields[row]["fieldValue"])
        if 0 <= index < len(paths):
            del paths[index]
            self.setValue(row, paths)

    @Slot(int)
    def clear_preview_files(self, row: int) -> None:
        self.setValue(row, [])

    @Slot("QVariant", result=QUrl)
    def preview_url(self, value) -> QUrl:
        path = self._local_path(value)
        return QUrl.fromLocalFile(path) if path else QUrl()

    @Slot("QVariant", result=str)
    def preview_name(self, value) -> str:
        return Path(self._local_path(value)).name

    @Slot(result="QVariantMap")
    def values(self) -> dict:
        return {
            field["fieldName"]: self._typed_value(field)
            for field in self._fields
            if field["fieldName"]
        }

    @Slot(int, result="QVariantMap")
    def get(self, row: int) -> dict:
        if not 0 <= row < len(self._fields):
            return {}
        return dict(self._fields[row])

    def records(self) -> list[dict]:
        return [dict(field) for field in self._fields]

    @classmethod
    def submission_for(cls, fields, mode: str) -> dict:
        values = {}
        for field in fields:
            if (
                field["fieldReadOnly"]
                or field["fieldType"] in {
                    "parent", "preview", "thumbnail", "unsupported",
                }
            ):
                continue
            if (
                field["fieldType"] == "password"
                and cls._empty(field["fieldValue"])
            ):
                continue
            if (
                mode == "edit"
                and field["fieldValue"] == field["defaultValue"]
            ):
                continue
            values[field.get("submitName") or field["fieldName"]] = (
                cls._typed_value(field)
            )
        return values

    def submission_values(self, mode: str) -> dict:
        return self.submission_for(self._fields, mode)

    @classmethod
    def preview_paths_for(cls, fields) -> list[str]:
        paths = []
        for field in fields:
            if field["fieldType"] == "preview":
                paths.extend(cls._preview_values(field["fieldValue"]))
        return paths

    def preview_paths(self) -> list[str]:
        return self.preview_paths_for(self._fields)

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
        ) or (isinstance(value, (list, tuple, set)) and not value)

    @staticmethod
    def _local_path(value) -> str:
        if isinstance(value, QUrl):
            return value.toLocalFile() or value.toString()
        text = str(value or "")
        if text.startswith("file:"):
            return QUrl(text).toLocalFile() or text
        return text

    @classmethod
    def _preview_values(cls, value) -> list[str]:
        values = value if isinstance(value, (list, tuple)) else [value]
        return [cls._local_path(item) for item in values if item]

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
                return int(bool(value))
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

    _field_icons = {
        "string": "type",
        "integer": "type",
        "float": "type",
        "multiline": "description",
        "bool": "task-alt",
        "enum": "view-list",
        "user": "person",
        "project": "workspaces",
        "process": "process",
        "pipeline": "workflow",
        "status": "status",
        "date": "calendar-month",
        "datetime": "calendar-month",
        "parent": "link",
        "preview": "image-edit",
        "thumbnail": "image",
        "password": "visibility-off",
        "unsupported": "warning",
    }
    _batch_number = re.compile(r"\{n(?::0([1-9]))?\}")

    def __init__(self, context, notify=None, checkin=None, parent=None) -> None:
        super().__init__(parent)
        self._context = context
        self._notify = notify or (lambda _message: None)
        self._checkin = checkin
        self._busy = False
        self._error = ""
        self._title = ""
        self._search_type = ""
        self._parent_title = ""
        self._mode = "insert"
        self._request_id = 0
        self._worker = None
        self._edit_widget = None
        self._context_data = {}
        self._script_triggers = None
        self._batch_enabled = False
        self._batch_count = 10
        self._batch_source_fields = []
        self._batch_drafts = []
        self._batch_index = -1
        self._submitted_values = None
        self._submitted_previews = []
        self._preview_uploads = []
        self._preview_upload_active = False
        self.model = SObjectFieldModel(self)
        self.model.valuesChanged.connect(self.stateChanged.emit)
        operation_finished = getattr(checkin, "operationFinished", None)
        if hasattr(operation_finished, "connect"):
            operation_finished.connect(self._preview_upload_finished)

    def attach_script_triggers(self, triggers) -> None:
        self._script_triggers = triggers

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
        self._search_type = search_type
        self._mode = (
            "edit"
            if (
                context.get("mode") == "edit"
                and context.get("sobject") is not None
            )
            else "insert"
        )
        self._reset_batch()
        sobject = context.get("sobject")
        parent_sobject = context.get("parent_sobject")
        try:
            self._parent_title = str(
                parent_sobject.get_title() if parent_sobject is not None else ""
            )
        except (AttributeError, TypeError):
            self._parent_title = ""
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
        from .ingest_relation import relation_job_metadata

        relation = relation_job_metadata(
            context.get("relation"), stype,
        )
        edit["instance_type"] = relation["instanceType"]
        edit["instance_path"] = relation["instancePath"]
        from thlib.tactic_widgets import TacticEditWdg
        self._edit_widget = TacticEditWdg(edit)
        self._edit_widget.set_stype(stype)
        fields = self.build_descriptors(
            stype,
            context,
            (result or {}).get("InputWidgets") or [],
            mode=self._mode,
        )
        self.model.replace(fields)
        self._busy = False
        self._error = "" if fields else "The edit view contains no supported fields"
        self._worker = None
        self.stateChanged.emit()

    def build_descriptors(
        self,
        stype,
        context: dict,
        sources,
        *,
        mode: str,
    ) -> list[dict]:
        """Translate one TACTIC Edit View through the shared field catalog."""
        return [
            descriptor
            for source in sources or []
            if (
                descriptor := self.describe_field(
                    stype, context, source, mode=mode
                )
            )
        ]

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
        return self.describe_field(
            stype, context, source, mode=self._mode
        )

    @classmethod
    def describe_field(
        cls,
        stype,
        context: dict,
        source,
        *,
        mode: str = "edit",
    ) -> dict | None:
        """Map one native TACTIC input widget to the shared editor contract."""
        source = dict(source or {})
        name = str(source.get("name") or "")
        class_name = str(source.get("class_name") or "")
        if not name:
            return None
        from thlib import tactic_widgets as tw

        widget_source = dict(source)
        widget_source.update({
            "stype": stype,
            "sobject": context.get("sobject"),
            "parent_sobject": context.get("parent_sobject"),
            "info_dict": context.get("info_dict"),
        })
        widget_class = tw.get_widget_class(class_name, "input")
        widget = widget_class(widget_source) if widget_class else None
        action = dict(source.get("action_options") or {})
        column = str(
            widget.get_submit_name() if widget is not None
            else action.get("column") or name
        )
        try:
            original_type = str(
                stype.get_column_data_type(column) or "text"
            )
        except (AttributeError, KeyError, TypeError):
            original_type = "text"
        field_type = (
            widget.get_editor_kind(original_type)
            if widget is not None else "unsupported"
        )
        if (
            class_name == "tactic.ui.widget.calendar_wdg.CalendarInputWdg"
            and original_type.lower() == "date"
        ):
            field_type = "date"
        options = widget.get_editor_options() if widget is not None else []
        options = cls._special_options(
            field_type,
            context,
            options,
            source,
        )
        default = (
            widget.get_default_values()
            if widget is not None else cls._default_value(source, field_type)
        )
        sobject = context.get("sobject")
        if (
            str(mode or "edit") == "edit"
            and sobject is not None
            and field_type not in {"password", "preview", "thumbnail"}
        ):
            try:
                info = sobject.get_info() or {}
                if column in info:
                    default = info.get(column)
                elif default is None or default == "":
                    default = sobject.get_value(column)
            except (AttributeError, KeyError, TypeError):
                pass
        elif str(mode or "edit") == "insert":
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
        default = cls._normalized_default(default, field_type)
        if (
            field_type in {
                "enum", "user", "project", "process", "pipeline", "status",
            }
            and default not in (None, "")
            and not any(
                str(option.get("value") or "") == str(default)
                for option in options
            )
        ):
            options.append({
                "label": str(default),
                "value": default,
                "color": "",
            })
        required = widget.get_required() if widget is not None else False
        read_only = widget.get_read_only() if widget is not None else True
        description = widget.get_description() if widget is not None else ""
        return {
            "fieldName": name,
            "submitName": column,
            "title": str(
                source.get("title") or source.get("label")
                or name
            ),
            "fieldType": field_type,
            "originalType": original_type,
            "fieldValue": default,
            "defaultValue": default,
            "fieldRequired": required,
            "fieldReadOnly": read_only,
            "fieldOptions": options,
            "fieldError": "",
            "fieldDescription": description,
            "fieldIcon": cls._field_icons.get(field_type, "type"),
            "widgetClass": class_name,
        }

    @classmethod
    def _special_options(
        cls,
        field_type: str,
        context: dict,
        options: list[dict],
        source: dict | None = None,
    ) -> list[dict]:
        if field_type == "user":
            return cls._user_options(context, options)
        if field_type == "status":
            return cls._status_options(context, source or {}) or options
        if field_type == "process":
            return cls._process_options(context) or options
        if field_type != "pipeline" or options:
            return options
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
                "icon": "workflow",
            })
        return sorted(result, key=lambda item: item["label"].casefold())

    @staticmethod
    def _workflow_target(context: dict):
        target = context.get("parent_sobject")
        if target is not None:
            return target
        candidate = context.get("sobject")
        try:
            if candidate.get_stype().get_code() != "sthpw/task":
                return candidate
        except (AttributeError, TypeError):
            pass
        return None

    @classmethod
    def _target_pipeline(cls, context: dict):
        target = cls._workflow_target(context)
        if target is None:
            return None, None, None
        try:
            stype = target.get_stype()
            pipelines = stype.get_pipeline() or {}
            pipeline = pipelines.get(target.get_pipeline_code())
        except (AttributeError, KeyError, TypeError):
            return target, None, None
        return target, stype, pipeline

    @staticmethod
    def _context_process(context: dict) -> str:
        info = dict(context.get("info_dict") or {})
        process = str(info.get("process") or "")
        if process:
            return process
        sobject = context.get("sobject")
        try:
            return str((sobject.get_info() or {}).get("process") or "")
        except (AttributeError, TypeError):
            return ""

    @classmethod
    def _process_options(cls, context: dict) -> list[dict]:
        _target, _stype, pipeline = cls._target_pipeline(context)
        if pipeline is None:
            return []
        try:
            processes = (pipeline.pipeline or {}).items()
        except AttributeError:
            return []
        return [{
            "label": str(process),
            "value": str(process),
            "color": str((info or {}).get("color") or ""),
            "icon": "process",
        } for process, info in processes]

    @classmethod
    def _status_options(
        cls,
        context: dict,
        source: dict,
    ) -> list[dict]:
        _target, stype, pipeline = cls._target_pipeline(context)
        process = cls._context_process(context)
        if stype is None or pipeline is None or not process:
            return []
        try:
            from thlib.ui.workflow_data import process_task_configuration

            configuration = process_task_configuration(pipeline, process)
            workflow = stype.get_workflow()
            pipeline_code = configuration.get("task_pipeline")
            if not pipeline_code:
                configured = list(source.get("task_pipelines") or [])
                pipeline_code = configured[0] if len(configured) == 1 else ""
            task_pipeline = (
                workflow.get_by_pipeline_code("sthpw/task", pipeline_code)
                if pipeline_code else workflow.get_by_process_node_type(
                    "sthpw/task", configuration.get("type")
                )
            )
            statuses = (task_pipeline.pipeline or {}).items()
        except (AttributeError, KeyError, TypeError):
            return []
        return [{
            "label": str(status),
            "value": str(status),
            "color": str((info or {}).get("color") or ""),
            "icon": "status",
        } for status, info in statuses]

    @classmethod
    def _user_options(
        cls,
        context: dict,
        server_options: list[dict],
    ) -> list[dict]:
        from thlib.environment import env_inst

        _target, _stype, pipeline = cls._target_pipeline(context)
        process = cls._context_process(context)
        logins = None
        if pipeline is not None and process:
            try:
                from thlib.ui.workflow_data import process_task_configuration

                configuration = process_task_configuration(pipeline, process)
                group_code = (
                    configuration.get("assigned_login_group")
                    or configuration.get("assigned_group")
                )
                current_login = env_inst.get_current_login_object()
                group = current_login.get_login_group(group_code) if (
                    current_login is not None and group_code
                ) else None
                logins = group.get_logins() if group is not None else None
            except (AttributeError, KeyError, TypeError):
                logins = None
        if not logins and server_options:
            return list(server_options)
        if not logins:
            try:
                logins = list((env_inst.get_all_logins() or {}).values())
            except (AttributeError, TypeError):
                logins = []
        result = [{"label": "", "value": "", "avatarUrl": ""}]
        seen = set()
        for login in logins:
            try:
                value = str(login.get_login() or "")
                label = str(login.get_display_name() or value)
            except AttributeError:
                continue
            if value and value not in seen:
                result.append({
                    "label": label,
                    "value": value,
                    "avatarUrl": "",
                })
                seen.add(value)
        result[1:] = sorted(
            result[1:], key=lambda item: item["label"].casefold()
        )
        return result

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

    @classmethod
    def _normalized_default(cls, value, field_type: str):
        if field_type == "bool":
            return cls._flag(value)
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

    def _reset_batch(self) -> None:
        self._batch_enabled = False
        self._batch_count = 10
        self._batch_source_fields = []
        self._batch_drafts = []
        self._batch_index = -1
        self._submitted_values = None
        self._submitted_previews = []

    def _batch_name_row(self, fields=None) -> int:
        records = fields if fields is not None else self.model._fields
        for target in ("name", "title", "code"):
            for row, field in enumerate(records):
                if (
                    not field.get("fieldReadOnly")
                    and field.get("fieldType") in {"string", "multiline"}
                    and target in {
                        str(field.get("fieldName") or "").lower(),
                        str(field.get("submitName") or "").lower(),
                    }
                ):
                    return row
        return -1

    @classmethod
    def _render_batch_name(cls, template: str, number: int) -> str:
        def replace(match) -> str:
            width = int(match.group(1) or 0)
            return str(number).zfill(width)

        return cls._batch_number.sub(replace, str(template or ""))

    def _batch_name_template(self) -> str:
        row = self._batch_name_row()
        return (
            str(self.model._fields[row].get("fieldValue") or "")
            if row >= 0 else ""
        )

    def _store_batch_draft(self) -> None:
        if 0 <= self._batch_index < len(self._batch_drafts):
            self._batch_drafts[self._batch_index] = self.model.records()

    @Slot(bool)
    def set_batch_enabled(self, enabled: bool) -> None:
        enabled = bool(enabled) and self._mode == "insert"
        if enabled == self._batch_enabled:
            return
        if self._batch_index >= 0:
            self.leave_batch_preview()
        self._batch_enabled = enabled
        self.stateChanged.emit()

    @Slot(int)
    def set_batch_count(self, count: int) -> None:
        count = max(2, min(100, int(count)))
        if count != self._batch_count:
            self._batch_count = count
            self.stateChanged.emit()

    @Slot()
    def preview_batch(self) -> None:
        if not self._batch_enabled or self._mode != "insert":
            return
        if not self.model.valid:
            self._error = self.tr("Correct the highlighted fields")
            self.stateChanged.emit()
            return
        source = self.model.records()
        drafts = []
        for number in range(1, self._batch_count + 1):
            draft = deepcopy(source)
            for field in draft:
                value = str(field.get("fieldValue") or "")
                if (
                    not field.get("fieldReadOnly")
                    and field.get("fieldType") in {"string", "multiline"}
                    and self._batch_number.search(value)
                ):
                    field["fieldValue"] = self._render_batch_name(
                        value, number
                    )
            drafts.append(draft)
        self._batch_source_fields = source
        self._batch_drafts = drafts
        self._batch_index = 0
        self._error = ""
        self.model.replace(drafts[0])
        self.stateChanged.emit()

    @Slot(int)
    def show_batch_item(self, row: int) -> None:
        row = int(row)
        if not 0 <= row < len(self._batch_drafts):
            return
        self._store_batch_draft()
        self._batch_index = row
        self.model.replace(self._batch_drafts[row])
        self.stateChanged.emit()

    @Slot()
    def leave_batch_preview(self) -> None:
        if self._batch_index < 0:
            return
        self._store_batch_draft()
        self._batch_index = -1
        self.model.replace(self._batch_source_fields)
        self.stateChanged.emit()

    def _batch_submission(self) -> tuple[list[dict], list[list[str]]] | None:
        self._store_batch_draft()
        for row, draft in enumerate(self._batch_drafts):
            if any(SObjectFieldModel._error_for(field) for field in draft):
                self.show_batch_item(row)
                self._error = self.tr("Correct the highlighted fields")
                self.stateChanged.emit()
                return None
        return (
            [
                SObjectFieldModel.submission_for(draft, "insert")
                for draft in self._batch_drafts
            ],
            [
                SObjectFieldModel.preview_paths_for(draft)
                for draft in self._batch_drafts
            ],
        )

    @Slot()
    def submit(self) -> None:
        if self._busy or not self._edit_widget:
            return
        if self._batch_enabled and self._batch_index < 0:
            self._error = self.tr("Preview the batch before creating it")
            self.stateChanged.emit()
            return
        if not self.model.valid:
            self._error = self.tr("Correct the highlighted fields")
            self.stateChanged.emit()
            return
        if self._batch_enabled:
            submission = self._batch_submission()
            if submission is None:
                return
            values, self._submitted_previews = submission
        else:
            values = self.model.submission_values(self._mode)
            self._submitted_previews = [self.model.preview_paths()]
        self._submitted_values = values
        self._busy = True
        self._error = ""
        self.stateChanged.emit()

        triggers = self._script_triggers
        if triggers is None:
            self._submit_values(values)
            return

        def start(success: bool, error: str) -> None:
            if not success:
                self._busy = False
                self._error = str(error or "Script trigger failed")
                self.stateChanged.emit()
                return
            self._submit_values(values)

        trigger_values = values[0] if isinstance(values, list) else values
        context = self._trigger_context(trigger_values)
        if isinstance(values, list):
            context["batch_values"] = [dict(item) for item in values]
            context["batch_count"] = len(values)
        triggers.run_before(self._trigger_event(), context, start)

    def _submit_values(self, values: dict | list[dict]) -> None:

        from thlib.environment import env_inst

        def operation():
            from thlib import server_cache

            result = self._edit_widget.commit(values)
            project_code = str(
                self._context_data.get("project_code") or ""
            )
            if not project_code:
                source = self._context_data.get("sobject")
                stype = self._context_data.get("stype")
                try:
                    project_code = str(
                        (source.get_project() if source else stype.get_project())
                        .get_code() or ""
                    )
                except AttributeError:
                    project_code = ""
            server_cache.invalidate_domains(
                (
                    "search", "snapshots", "relations", "tasks",
                    "notes", "activity", "work_hours",
                ),
                project_code,
            )
            return result

        worker = env_inst.server_pool.add_task(operation)
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
        results = list(result) if isinstance(result, (list, tuple)) else [result]
        search_keys = []
        for item in results:
            try:
                search_keys.append(str(
                    item.get("__search_key__")
                    or item.get("search_key")
                    or item.get("code")
                    or ""
                ))
            except AttributeError:
                search_keys.append("")
        search_key = search_keys[0] if search_keys else ""
        if not search_key and self._mode == "edit":
            sobject = self._context_data.get("sobject")
            if sobject is not None:
                search_key = str(sobject.get_search_key() or "")
        self._busy = False
        self._worker = None
        self._notify(
            self.tr("%1 sObjects created").replace("%1", str(len(results)))
            if len(results) > 1 else f"sObject {action}"
        )
        preview_errors = []
        for index, (item, item_key) in enumerate(zip(results, search_keys)):
            paths = (
                self._submitted_previews[index]
                if index < len(self._submitted_previews) else []
            )
            preview_error = self._queue_preview(item, item_key, paths=paths)
            if preview_error:
                preview_errors.append(preview_error)
        if preview_errors:
            self._notify(preview_errors[0])
        refresh = self._context_data.get("refresh")
        open_created = self._context_data.get("open_created")
        if (
            self._mode == "insert" and search_key and len(results) == 1
            and self._context_data.get("parent_sobject") is None
            and callable(open_created)
        ):
            open_created(search_key)
        elif callable(refresh):
            refresh()
        self.stateChanged.emit()
        self.saved.emit(search_key)
        if self._script_triggers is not None:
            values = self._submitted_values
            trigger_values = values[0] if isinstance(values, list) else values
            context = self._trigger_context(trigger_values or {}, search_key)
            if isinstance(values, list):
                context["batch_values"] = [dict(item) for item in values]
                context["batch_count"] = len(values)
                context["result_search_keys"] = search_keys
            self._script_triggers.run_after(self._trigger_event(), context)

    def _trigger_event(self) -> str:
        kind = "update" if self._mode == "edit" else "create"
        return ("task." if self._search_type == "sthpw/task" else "object.") + kind

    def _trigger_context(
        self, values: dict, search_key: str = "",
    ) -> dict:
        source = self._context_data.get("sobject")
        if not search_key and source is not None:
            try:
                search_key = str(source.get_search_key() or "")
            except (AttributeError, KeyError, TypeError):
                pass
        info = dict(self._context_data.get("info_dict") or {})
        return {
            "project_code": str(self._context_data.get("project_code") or ""),
            "search_key": search_key,
            "search_type": self._search_type,
            "process": str(values.get("process") or info.get("process") or ""),
            "context": str(values.get("context") or info.get("context") or ""),
            "values": dict(values),
        }

    def _queue_preview(self, result, search_key: str, *, paths=None) -> str:
        paths = self.model.preview_paths() if paths is None else list(paths)
        if not paths:
            return ""
        if self._checkin is None:
            return self.tr(
                "sObject saved, but its preview could not be checked in"
            )
        source = self._context_data.get("sobject")
        if source is None and isinstance(result, dict):
            try:
                from thlib.tactic_classes import SObject

                stype = self._context_data.get("stype")
                source = SObject(result, project=stype.get_project())
            except (AttributeError, KeyError, TypeError):
                source = None
        if source is None or not search_key:
            return self.tr(
                "sObject saved, but its preview could not be checked in"
            )
        try:
            title = str(source.get_title() or self._title)
        except (AttributeError, TypeError):
            title = self._title
        try:
            code = str(source.get_code() or "")
        except (AttributeError, TypeError):
            code = ""
        self._preview_uploads.append({
            "search_key": search_key,
            "source": source,
            "project_code": str(
                self._context_data.get("project_code") or ""
            ),
            "title": title,
            "code": code,
            "context": "icon",
            "description": "sObject preview",
            "paths": paths,
            "update_versionless": True,
            "queue_when_ready": False,
            "queue_before_naming": False,
            "start_when_ready": True,
        })
        self._start_next_preview_upload()
        return ""

    def _start_next_preview_upload(self) -> None:
        if (
            self._preview_upload_active or not self._preview_uploads
            or self._checkin is None
            or bool(getattr(self._checkin, "operationBusy", False))
            or bool(getattr(self._checkin, "namingBusy", False))
        ):
            return
        request = self._preview_uploads.pop(0)
        self._preview_upload_active = True
        try:
            self._checkin.prepare_external_checkin(**request)
        except (AttributeError, OSError, TypeError, ValueError) as error:
            self._preview_upload_active = False
            self._notify(self.tr(
                "sObject saved, but its preview could not be checked in"
            ) + f": {error}")
            self._start_next_preview_upload()

    @Slot(bool, str)
    def _preview_upload_finished(self, success: bool, error: str) -> None:
        if self._preview_upload_active:
            self._preview_upload_active = False
            if not success:
                self._notify(self.tr(
                    "sObject saved, but its preview could not be checked in"
                ) + (f": {error}" if error else ""))
        self._start_next_preview_upload()

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
    def searchType(self) -> str:
        return self._search_type

    @Property(str, notify=stateChanged)
    def parentTitle(self) -> str:
        return self._parent_title

    @Property(str, notify=stateChanged)
    def mode(self) -> str:
        return self._mode

    @Property(bool, notify=stateChanged)
    def batchEnabled(self) -> bool:
        return self._batch_enabled

    @Property(int, notify=stateChanged)
    def batchCount(self) -> int:
        return self._batch_count

    @Property(bool, notify=stateChanged)
    def batchPreview(self) -> bool:
        return self._batch_index >= 0

    @Property(int, notify=stateChanged)
    def batchIndex(self) -> int:
        return self._batch_index

    @Property(int, notify=stateChanged)
    def batchTotal(self) -> int:
        return len(self._batch_drafts) or self._batch_count

    @Property(str, notify=stateChanged)
    def batchExample(self) -> str:
        template = self._batch_name_template()
        if not self._batch_number.search(template):
            return ""
        return "{} … {}".format(
            self._render_batch_name(template, 1),
            self._render_batch_name(template, self._batch_count),
        )

    @Property(str, notify=stateChanged)
    def submitLabel(self) -> str:
        return "Save changes" if self._mode == "edit" else "Create"
