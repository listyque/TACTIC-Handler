from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QObject, Property, Qt, Signal, Slot

from .workspace_models.records import RecordListModel


_DATA_FIELDS = (
    "search_type", "dir_naming", "file_naming", "sandbox_dir_naming",
    "snapshot_type", "context", "latest_versionless",
    "current_versionless", "manual_version", "ingest_rule_code",
    "condition", "class_name", "script_path", "checkin_type",
    "base_dir_alias", "sandbox_dir_alias",
)

_BOOLEAN_FIELDS = {
    "latest_versionless", "current_versionless", "manual_version",
}


def _error_text(error) -> str:
    payload = error[0] if isinstance(error, (tuple, list)) and error else error
    if isinstance(payload, dict):
        return str(
            payload.get("exception") or payload.get("message") or payload
        )
    return str(payload or "Unknown naming editor error")


class NamingEditorController(QObject):
    stateChanged = Signal()
    saved = Signal(str)

    _roles = (
        "code", "title", "summary", "searchType", "context",
        "fileNaming", "dirNaming", "checkinType", "scripted",
        "versionless", "selected",
    )

    def __init__(
        self, application, checkin_controller, commit_queue, parent=None
    ) -> None:
        super().__init__(parent)
        self._application = application
        self._checkin = checkin_controller
        self._commit_queue = commit_queue
        self.model = RecordListModel(self._roles)
        self._records: list[dict] = []
        self._selected_row = -1
        self._editor: dict = {}
        self._original: dict = {}
        self._is_new = False
        self._busy = False
        self._error = ""
        self._message = ""
        self._worker = None
        self._worker_callbacks = None
        self._generation = 0
        self._closed = False
        self._server_identity = (getattr(application, 'server_url', ''),
                                 getattr(application, 'server_user', ''))
        self._requested_operation_id = ""
        self._type_mode = False
        self._target: dict = {}
        self._object_data: dict = {}
        self._project_data: dict = {}
        self._processes: list[str] = []
        self._contexts: list[str] = []
        self._preview_process = ""
        self._preview_context = ""
        self._sample_file = "example.ma"
        self._sample_version = 1
        self._sample_file_type = "main"
        self._preview_dir = ""
        self._preview_file = ""
        self._preview_status = ""
        self._pending_code = ""

    @Property(QObject, constant=True)
    def rulesModel(self):
        return self.model

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error

    @Property(str, notify=stateChanged)
    def message(self) -> str:
        return self._message

    @Property(int, notify=stateChanged)
    def selectedRow(self) -> int:
        return self._selected_row

    @Property("QVariantMap", notify=stateChanged)
    def selectedRule(self) -> dict:
        return dict(self._editor)

    @Property(bool, notify=stateChanged)
    def isNew(self) -> bool:
        return self._is_new

    @Property(bool, notify=stateChanged)
    def dirty(self) -> bool:
        return bool(self._editor) and self._editable(self._editor) != self._original

    @Property("QVariantMap", notify=stateChanged)
    def currentObject(self) -> dict:
        return dict(self._target)

    @Property(bool, notify=stateChanged)
    def typeMode(self) -> bool:
        return self._type_mode

    @Property("QVariantList", notify=stateChanged)
    def processes(self) -> list[str]:
        return list(self._processes)

    @Property("QVariantList", notify=stateChanged)
    def contexts(self) -> list[str]:
        return list(self._contexts)

    @Property(str, notify=stateChanged)
    def previewProcess(self) -> str:
        return self._preview_process

    @Property(str, notify=stateChanged)
    def previewContext(self) -> str:
        return self._preview_context

    @Property(str, notify=stateChanged)
    def sampleFile(self) -> str:
        return self._sample_file

    @Property(int, notify=stateChanged)
    def sampleVersion(self) -> int:
        return self._sample_version

    @Property(str, notify=stateChanged)
    def sampleFileType(self) -> str:
        return self._sample_file_type

    @Property(str, notify=stateChanged)
    def previewDirectory(self) -> str:
        return self._preview_dir

    @Property(str, notify=stateChanged)
    def previewFilename(self) -> str:
        return self._preview_file

    @Property(str, notify=stateChanged)
    def previewPath(self) -> str:
        if self._preview_dir and self._preview_file:
            return f"{self._preview_dir.rstrip('/')}/{self._preview_file}"
        return self._preview_file or self._preview_dir

    @Property(str, notify=stateChanged)
    def previewStatus(self) -> str:
        return self._preview_status

    @staticmethod
    def _editable(record: dict) -> dict:
        return {field: record.get(field) for field in _DATA_FIELDS}

    @staticmethod
    def _target_from_search_key(search_key: str, title: str = "") -> dict:
        import thlib.tactic_classes as tc

        parts = tc.split_search_key(str(search_key or ""))
        return {
            "searchKey": str(search_key or ""),
            "searchType": str(parts.get("pipeline_code") or ""),
            "projectCode": str(parts.get("project_code") or ""),
            "code": str(parts.get("asset_code") or ""),
            "title": str(title or parts.get("asset_code") or "sObject"),
        }

    @Slot(str)
    def prepare_operation(self, operation_id: str) -> None:
        self._requested_operation_id = str(operation_id or "")

    @Slot(str, bool)
    def window_visibility_changed(self, window_id: str, visible: bool) -> None:
        if window_id == 'naming_editor' and visible:
            self.begin()

    @Slot(str, str, str, result=bool)
    def begin_search_type(self, project_code: str, search_type: str, title: str) -> bool:
        """Use the selected Search Type as the naming owner, even without rules."""
        if (self._closed or not project_code or not search_type
                or not self._application.can_administer):
            return False
        if (self._type_mode and self._target.get('projectCode') == project_code
                and self._target.get('searchType') == search_type):
            self._application.window_model.close_window('naming_editor')
            return True
        if self.busy or self.dirty:
            self._application._notify(self.tr(
                'Finish the current naming edit before opening another context'))
            return False
        self._application.window_model.close_window('naming_editor')
        self._requested_operation_id = ""
        self._type_mode = True
        self._target = {'projectCode': project_code, 'searchType': search_type,
                        'title': title or search_type}
        self._object_data = self._project_data = {}
        self._processes = self._contexts = []
        self._preview_process = self._preview_context = ""
        self._pending_code = self._message = ""
        self._records = []
        self.model.clear()
        self._selected_row = -1
        self._editor = self._original = {}
        self._update_preview()
        self.reload()
        return True

    @Slot()
    def begin(self) -> None:
        # A retained draft belongs to its original project, never the latest
        # workspace selection or a newly requested Administration project.
        if self._closed or self.busy or self.dirty:
            return
        self._type_mode = False
        self._object_data = {}
        self._project_data = {}
        self._pending_code = ""
        self._message = ""
        operation = None
        if self._requested_operation_id:
            operation = self._commit_queue.operation(
                self._requested_operation_id
            )
            self._requested_operation_id = ""
        if operation:
            self._target = self._target_from_search_key(
                operation.get("searchKey"), operation.get("objectTitle")
            )
            self._preview_process = str(
                operation.get("process") or "publish"
            )
            self._preview_context = str(
                operation.get("context") or self._preview_process
            )
            source_files = list(operation.get("files") or [])
            if source_files:
                self._sample_file = Path(
                    str(source_files[0].get("path") or "example.ma")
                ).name
            version = operation.get("version")
            if version:
                self._sample_version = max(1, int(version))
        else:
            current = self._checkin.currentObject
            search_key = str(current.get("searchKey") or "")
            self._target = self._target_from_search_key(
                search_key, current.get("title")
            ) if search_key else {}
            self._preview_process = str(
                self._checkin.process or "publish"
            )
            self._preview_context = str(
                self._checkin.context or self._preview_process
            )
        self._sync_processes()
        if not self._target.get("searchKey"):
            self.model.clear()
            self._records = []
            self._selected_row = -1
            self._editor = {}
            self._original = {}
            self._error = "Select an sObject before opening Naming Editor."
            self.stateChanged.emit()
            return
        self.reload()

    def _sync_processes(self) -> None:
        current = self._checkin.currentObject
        same_object = (
            str(current.get("searchKey") or "")
            == str(self._target.get("searchKey") or "")
        )
        if same_object:
            self._processes = list(self._checkin.processes)
            self._contexts = list(self._checkin.contexts)
        else:
            self._processes = [self._preview_process]
            self._contexts = [self._preview_context]
        self._processes = list(dict.fromkeys(
            value for value in self._processes if value
        ))
        self._contexts = list(dict.fromkeys(
            value for value in self._contexts if value
        ))
        if self._preview_process not in self._processes:
            self._processes.append(self._preview_process)
        if self._preview_context not in self._contexts:
            self._contexts.append(self._preview_context)

    def _start_worker(self, callback, result_handler) -> None:
        from thlib.environment import env_inst

        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(callback)
        if worker is None:
            self._worker_failed(self.tr('Server worker pool is unavailable'))
            return
        self._worker = worker
        generation = self._generation

        def completed(result):
            if not self._closed and generation == self._generation:
                self._release_worker()
                result_handler(result)

        def failed(error):
            if not self._closed and generation == self._generation:
                self._release_worker()
                self._worker_failed(error)

        self._worker_callbacks = completed, failed
        worker.result.connect(completed, Qt.ConnectionType.QueuedConnection)
        worker.error.connect(failed, Qt.ConnectionType.QueuedConnection)
        self._busy = True
        self._error = ""
        self.stateChanged.emit()
        worker.start()

    def _release_worker(self, cancel=False) -> None:
        if self._worker:
            if self._worker_callbacks:
                self._worker.result.disconnect(self._worker_callbacks[0])
                self._worker.error.disconnect(self._worker_callbacks[1])
            if cancel:
                self._worker.cancel()
        self._worker = self._worker_callbacks = None

    @Slot()
    def server_changed(self) -> None:
        identity = (self._application.server_url, self._application.server_user)
        if identity == self._server_identity and (
                not self._type_mode or self._application.can_administer):
            return
        self._server_identity = identity
        self._generation += 1
        self._release_worker(cancel=True)
        self._busy = False
        self._requested_operation_id = ""
        self._target = self._editor = self._original = {}
        self._object_data = self._project_data = {}
        self._records = []
        self._type_mode = False
        self._selected_row = -1
        self._is_new = False
        self._error = self._message = ""
        self._processes = self._contexts = []
        self.model.clear()
        self._update_preview()
        self.stateChanged.emit()
        self._application.window_model.close_window('naming_editor')

    def shutdown(self) -> None:
        self._closed = True
        self._generation += 1
        self._release_worker(cancel=True)

    @Slot()
    def reload(self) -> None:
        if self._closed or self._busy or not self._target.get("projectCode"):
            return
        target = dict(self._target)
        type_mode = self._type_mode
        self._generation += 1
        generation = self._generation

        def load():
            import thlib.tactic_classes as tc

            server = tc.server_start(project=target["projectCode"])
            records = server.query(
                "config/naming",
                [("search_type", target["searchType"])],
                order_bys=["context", "code"],
            ) or []
            object_row = {}
            if not type_mode:
                object_row = server.query(
                    target["searchType"], [("code", target["code"])], single=True,
                ) or {}
            project_row = tc.server_start(project="sthpw").query(
                "sthpw/project",
                [("code", target["projectCode"])],
                single=True,
            ) or {}
            return {
                "generation": generation,
                "records": records,
                "object": object_row,
                "project": project_row,
            }

        self._start_worker(load, self._rules_loaded)

    @Slot(object)
    def _rules_loaded(self, payload) -> None:
        if int(payload.get("generation") or -1) != self._generation:
            return
        self._worker = None
        self._busy = False
        self._object_data = dict(payload.get("object") or {})
        self._project_data = dict(payload.get("project") or {})
        self._records = [
            self._normalize_record(record)
            for record in payload.get("records") or []
        ]
        if self._type_mode:
            self._contexts = list(dict.fromkeys(
                record['context'] for record in self._records if record['context']))
        self.model.replace([
            self._presentation(record, index)
            for index, record in enumerate(self._records)
        ])
        if self._records:
            row = next((
                index for index, record in enumerate(self._records)
                if record.get("code") == self._pending_code
            ), -1)
            self._pending_code = ""
            if row < 0:
                row = self._best_rule_row()
            self._select(row)
        else:
            self._selected_row = -1
            self._editor = {}
            self._original = {}
            self._is_new = False
            self._update_preview()
            self.stateChanged.emit()

    @Slot(object)
    def _worker_failed(self, error) -> None:
        self._worker = None
        self._busy = False
        self._error = _error_text(error)
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.raise_error(
                self._error, group="naming/editor"
            )
        self.stateChanged.emit()

    def _normalize_record(self, record: dict) -> dict:
        normalized = {
            field: (
                bool(record.get(field)) if field in _BOOLEAN_FIELDS
                else str(record.get(field) or "")
            )
            for field in _DATA_FIELDS
        }
        normalized.update({
            "code": str(record.get("code") or ""),
            "searchKey": str(record.get("__search_key__") or ""),
        })
        return normalized

    def _rule_title(self, record: dict) -> str:
        if record.get("context"):
            return str(record["context"])
        condition = str(record.get("condition") or "")
        match = re.search(
            r"snapshot\.context\)\s*==\s*['\"]?([\w/.-]+)",
            condition,
        )
        if match:
            return match.group(1)
        if record.get("script_path"):
            return str(record["script_path"])
        if record.get("latest_versionless"):
            return "Versionless"
        return "Default"

    def _presentation(self, record: dict, row: int) -> dict:
        file_naming = str(record.get("file_naming") or "")
        dir_naming = str(record.get("dir_naming") or "")
        return {
            "code": str(record.get("code") or "New rule"),
            "title": self._rule_title(record),
            "summary": file_naming or record.get("script_path")
                or "Directory rule",
            "searchType": str(record.get("search_type") or ""),
            "context": str(record.get("context") or ""),
            "fileNaming": file_naming,
            "dirNaming": dir_naming,
            "checkinType": str(record.get("checkin_type") or "auto"),
            "scripted": bool(record.get("script_path")),
            "versionless": bool(
                record.get("latest_versionless")
                or record.get("current_versionless")
            ),
            "selected": row == self._selected_row,
        }

    def _best_rule_row(self) -> int:
        context = self._preview_context

        def score(record: dict) -> int:
            value = str(record.get("context") or "")
            condition = str(record.get("condition") or "")
            if value == context:
                return 30
            if context and context in condition:
                return 20
            if not value and not condition:
                return 10
            return 0

        return max(range(len(self._records)), key=lambda row: score(
            self._records[row]
        ))

    def _replace_model(self) -> None:
        self.model.replace([
            self._presentation(record, index)
            for index, record in enumerate(self._records)
        ])

    def _select(self, row: int) -> None:
        if not 0 <= row < len(self._records):
            return
        self._selected_row = row
        self._editor = dict(self._records[row])
        if self._type_mode:
            self._preview_context = str(self._editor.get('context') or '')
        self._original = self._editable(self._editor)
        self._is_new = False
        self._message = ""
        self._replace_model()
        self._update_preview()
        self.stateChanged.emit()

    @Slot(int)
    def select_rule(self, row: int) -> None:
        if not self._busy:
            self._select(row)

    @Slot()
    def create_rule(self) -> None:
        self._selected_row = -1
        self._editor = {
            field: False if field in _BOOLEAN_FIELDS else ""
            for field in _DATA_FIELDS
        }
        self._editor.update({
            "search_type": self._target.get('searchType', ''),
            "context": self._preview_context,
            "checkin_type": "strict",
            "dir_naming": "{project.code}/{search_type.table_name}/{sobject.code}/{snapshot.context}/versions",
            "file_naming": "{sobject.name}_v{version}.{ext}",
            "code": "",
            "searchKey": "",
        })
        self._original = {}
        self._is_new = True
        self._message = self.tr("New rule is local until Save is pressed.")
        self._replace_model()
        self._update_preview()
        self.stateChanged.emit()

    @Slot()
    def duplicate_rule(self) -> None:
        if not self._editor:
            self.create_rule()
            return
        self._editor = dict(self._editor)
        self._editor["code"] = ""
        self._editor["searchKey"] = ""
        self._selected_row = -1
        self._original = {}
        self._is_new = True
        self._message = self.tr("Duplicated rule is local until Save is pressed.")
        self._replace_model()
        self._update_preview()
        self.stateChanged.emit()

    @Slot()
    def reset(self) -> None:
        if self._is_new:
            if self._records:
                self._select(self._best_rule_row())
            else:
                self._editor = self._original = {}
                self._is_new = False
                self._message = ""
                self._update_preview()
                self.stateChanged.emit()
        elif 0 <= self._selected_row < len(self._records):
            self._select(self._selected_row)

    @Slot(str, "QVariant")
    def set_field(self, field: str, value) -> None:
        if field not in _DATA_FIELDS or not self._editor:
            return
        if field == 'search_type' and value != self._target.get('searchType'):
            return
        if field in _BOOLEAN_FIELDS:
            value = bool(value)
        else:
            value = str(value or "")
        if self._editor.get(field) == value:
            return
        self._editor[field] = value
        self._message = ""
        self._update_preview()
        self.stateChanged.emit()

    @Slot(str)
    def set_preview_process(self, process: str) -> None:
        process = str(process or "")
        if not process or process == self._preview_process:
            return
        current = self._checkin.currentObject
        if str(current.get("searchKey") or "") == self._target.get("searchKey"):
            self._contexts = list(
                self._checkin.contexts_for_process(process)
            )
        self._preview_process = process
        if self._preview_context not in self._contexts:
            self._preview_context = (
                self._contexts[0] if self._contexts else process
            )
        self._update_preview()
        self.stateChanged.emit()

    @Slot(str)
    def set_preview_context(self, context: str) -> None:
        context = str(context or "")
        if not context or context == self._preview_context:
            return
        self._preview_context = context
        self._update_preview()
        self.stateChanged.emit()

    @Slot(str)
    def set_sample_file(self, value: str) -> None:
        value = Path(str(value or "example.ma")).name or "example.ma"
        if value == self._sample_file:
            return
        self._sample_file = value
        self._update_preview()
        self.stateChanged.emit()

    @Slot(int)
    def set_sample_version(self, value: int) -> None:
        value = max(1, min(9999, int(value)))
        if value == self._sample_version:
            return
        self._sample_version = value
        self._update_preview()
        self.stateChanged.emit()

    @Slot(str)
    def set_sample_file_type(self, value: str) -> None:
        value = str(value or "main")
        if value == self._sample_file_type:
            return
        self._sample_file_type = value
        self._update_preview()
        self.stateChanged.emit()

    def _values(self) -> dict[str, str]:
        sample = Path(self._sample_file)
        object_code = str(
            self._object_data.get("code") or self._target.get("code") or "SOBJECT"
        )
        object_name = str(
            self._object_data.get("name")
            or self._object_data.get("title") or object_code
        )
        parent_code = str(
            self._object_data.get("parent_code")
            or next((
                value for key, value in self._object_data.items()
                if key.endswith("_code") and key not in {
                    "pipeline_code", "project_code", "code"
                } and value
            ), "PARENT")
        )
        return {
            "project.code": str(
                self._project_data.get("code")
                or self._target.get("projectCode") or "PROJECT"
            ),
            "project.category": str(
                self._project_data.get("category") or "project"
            ),
            "search_type.table_name": str(
                self._editor.get('search_type') or self._target.get("searchType") or "sobject"
            ).split("/")[-1],
            "sobject.code": object_code,
            "sobject.name": object_name,
            "sobject.relative_dir": str(
                self._object_data.get("relative_dir")
                or f"{self._target.get('projectCode', 'project')}/{object_code}"
            ),
            "parent.code": parent_code,
            "snapshot.context": self._preview_context or "publish",
            "snapshot.process": self._preview_process or "publish",
            "snapshot.version": str(self._sample_version),
            "version": str(self._sample_version),
            "ext": sample.suffix.lstrip(".") or "dat",
            "basefile": sample.stem or "example",
            "file.name": sample.name,
            "file.type": self._sample_file_type,
        }

    @staticmethod
    def _case_value(expression: str, file_type: str) -> str:
        pairs = re.findall(
            r"@GET\(file\.type\)\s*==\s*['\"]([^'\"]+)['\"]\s*,\s*"
            r"((?:['\"][^'\"]*['\"]\s*\+?\s*)+)",
            expression,
        )
        for expected, value_expression in pairs:
            if expected == file_type:
                return "".join(re.findall(
                    r"['\"]([^'\"]*)['\"]", value_expression
                ))
        return ""

    @classmethod
    def _render_expression(
        cls, expression: str, values: dict[str, str]
    ) -> str:
        expression = str(expression or "")
        expression = re.sub(
            r"\{@CASE\(([^{}]*)\)\}",
            lambda match: cls._case_value(
                match.group(1), values.get("file.type", "main")
            ),
            expression,
        )

        def replace(match):
            token = match.group(1)
            return values.get(token, f"<{token}>")

        return re.sub(r"\{([A-Za-z_][\w.]*)\}", replace, expression)

    def _update_preview(self) -> None:
        if not self._editor:
            self._preview_dir = ""
            self._preview_file = ""
            self._preview_status = self.tr("No naming rule selected.")
            return
        values = self._values()
        self._preview_dir = self._render_expression(
            self._editor.get("dir_naming"), values
        ).replace("\\", "/").strip("/")
        self._preview_file = self._render_expression(
            self._editor.get("file_naming"), values
        ).replace("\\", "/").rsplit("/", 1)[-1]
        statuses = []
        if self._editor.get("script_path"):
            statuses.append(
                "Script-based naming is resolved by TACTIC after the rule is saved."
            )
        condition = str(self._editor.get("condition") or "")
        if condition and self._preview_context not in condition:
            statuses.append("The current preview context may not match this condition.")
        if "<" in self._preview_dir or "<" in self._preview_file:
            statuses.append("Unknown expression tokens are shown between < >.")
        self._preview_status = " ".join(statuses) or self.tr("Local rule simulation")

    def _validation_error(self) -> str:
        if not self._editor.get("search_type"):
            return "Search type is required."
        if not any(
            self._editor.get(field)
            for field in ("dir_naming", "file_naming", "script_path", "class_name")
        ):
            return "Enter directory/file naming or a script/class override."
        if self._editor.get("checkin_type") not in {"", "auto", "strict"}:
            return "Check-in type must be Auto, Strict or empty."
        return ""

    @Slot(result=bool)
    def save(self) -> bool:
        if self._closed or self._busy or not self._editor:
            return False
        if self._type_mode and not self._application.can_administer:
            return False
        error = self._validation_error()
        if error:
            self._error = error
            self.stateChanged.emit()
            return False
        project_code = str(self._target.get("projectCode") or "")
        data = self._editable(self._editor)
        search_key = str(self._editor.get("searchKey") or "")
        self._generation += 1
        generation = self._generation

        def operation():
            import thlib.tactic_classes as tc

            server = tc.server_start(project=project_code)
            if search_key:
                result = server.insert_update(
                    search_key, data, triggers=True
                )
            else:
                result = server.insert(
                    "config/naming", data, triggers=True
                )
            code = str(
                (result or {}).get("code")
                if isinstance(result, dict) else ""
            )
            return {"generation": generation, "code": code}

        self._start_worker(operation, self._rule_saved)
        return True

    @Slot(object)
    def _rule_saved(self, payload) -> None:
        if int(payload.get("generation") or -1) != self._generation:
            return
        code = str(payload.get("code") or self._editor.get("code") or "")
        self._worker = None
        self._busy = False
        self._message = self.tr("Naming rule saved.")
        self._original = self._editable(self._editor)
        self._is_new = False
        self._pending_code = code
        self.saved.emit(code)
        self.stateChanged.emit()
        self.reload()


__all__ = ["NamingEditorController"]
