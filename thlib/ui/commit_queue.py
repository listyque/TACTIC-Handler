from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import uuid

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

from thlib.environment import env_read_config, env_write_config


class CommitQueueModel(QAbstractListModel):
    contentChanged = Signal()

    _roles = (
        "operationId", "title", "objectTitle", "fileCount", "context",
        "contextBranch", "process", "repository", "description", "version",
        "updateVersionless", "onlyVersionless", "keepFileName",
        "generatePreviews", "explicitFilename", "contextAsFilename",
        "mode", "sourceFiles", "versionedPaths", "versionlessPaths",
        "previewFiles", "previewUrls", "previewCount", "previewUrl",
        "futureFileName", "previewExtension", "fileSummary",
        "versionLabel", "snapshotInfoChips",
        "status", "selected", "error", "canEdit", "summary",
        "checked", "progress", "stage", "canCommit",
    )

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._role_ids = {
            name: Qt.UserRole + index + 1
            for index, name in enumerate(self._roles)
        }
        self._records: list[dict] = []

    def roleNames(self) -> dict[int, bytes]:
        return {
            role_id: name.encode("utf-8")
            for name, role_id in self._role_ids.items()
        }

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._records)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._records):
            return None
        name = next(
            (
                role_name for role_name, role_id in self._role_ids.items()
                if role_id == role
            ),
            None,
        )
        return self._records[index.row()].get(name) if name else None

    def append(self, record: dict) -> None:
        row = len(self._records)
        self.beginInsertRows(QModelIndex(), row, row)
        self._records.append(dict(record))
        self.endInsertRows()
        self.contentChanged.emit()

    def replace_row(self, row: int, record: dict) -> None:
        if not 0 <= row < len(self._records):
            return
        self._records[row] = dict(record)
        index = self.index(row, 0)
        self.dataChanged.emit(
            index, index, list(self._role_ids.values())
        )
        self.contentChanged.emit()

    def remove_row(self, row: int) -> None:
        if not 0 <= row < len(self._records):
            return
        self.beginRemoveRows(QModelIndex(), row, row)
        self._records.pop(row)
        self.endRemoveRows()
        self.contentChanged.emit()

    def move_row(self, source: int, target: int) -> bool:
        if (
            source == target
            or not 0 <= source < len(self._records)
            or not 0 <= target < len(self._records)
        ):
            return False
        destination = target + 1 if target > source else target
        self.beginMoveRows(
            QModelIndex(), source, source, QModelIndex(), destination
        )
        record = self._records.pop(source)
        self._records.insert(target, record)
        self.endMoveRows()
        self.contentChanged.emit()
        return True


class CommitQueueController(QObject):
    stateChanged = Signal()
    duplicateChanged = Signal()
    operationCompleted = Signal("QVariantMap")

    _editable = {
        "context", "description", "version", "repository", "mode",
        "updateVersionless", "onlyVersionless", "keepFileName",
        "generatePreviews", "explicitFilename", "contextAsFilename",
    }
    _naming_fields = {
        "context", "version", "repository", "mode", "updateVersionless",
        "onlyVersionless", "keepFileName", "explicitFilename",
        "contextAsFilename",
    }
    _preview_extensions = {
        ".apng", ".avif", ".bmp", ".gif", ".ico", ".jpg", ".jpeg",
        ".png", ".svg", ".tga", ".tif", ".tiff", ".webp",
    }

    def __init__(self, parent=None, *, window_model=None) -> None:
        super().__init__(parent)
        self._window_model = window_model
        self.model = CommitQueueModel(self)
        self._settings = dict(env_read_config(
            filename="ui_commit_queue",
            unique_id="ui_main",
            long_abs_path=True,
        ) or {})
        self._operations: dict[str, dict] = {}
        # Restored operations belong to an earlier UI session. They may still
        # finish normally, but must not navigate or repaint whatever the user
        # is looking at now. Only ids added during this process lifetime are
        # eligible for the post-check-in tree reveal.
        self._current_session_ids: set[str] = set()
        self._selected_id = ""
        self._active_id = ""
        self._batch_ids: list[str] = []
        self._executor = None
        self._apply_to_checked = False
        self._auto_clean = bool(
            self._settings.get("commitQueue/autoClean", False)
        )
        self._advanced_options_expanded = bool(self._settings.get(
            "commitQueue/advancedOptionsExpanded", False
        ))
        try:
            files_panel_height = float(
                self._settings.get("commitQueue/filesPanelHeight", 142.0)
            )
        except (TypeError, ValueError):
            files_panel_height = 142.0
        self._files_panel_height = max(
            100.0, min(360.0, files_panel_height)
        )
        self._duplicate_pending = None
        self._duplicate_queue = []
        self._validation_generation = {}
        self._deferred_validation_ids = set()
        self.model.contentChanged.connect(self.stateChanged)
        self._restore()

    def attach_executor(self, executor) -> None:
        self._executor = executor
        executor.preparationChanged.connect(self._operation_changed)
        executor.operationFinished.connect(self._operation_finished)
        executor.preparedValidationFinished.connect(
            self._prepared_validation_finished
        )
        application = getattr(executor, "_application", None)
        if application is not None:
            application.server_state_changed.connect(
                self._validate_deferred_operations
            )
        operation_ids = set(self._operations)
        if application is not None and application.server_state != "online":
            self._deferred_validation_ids.update(operation_ids)
        else:
            for operation_id in operation_ids:
                self._request_validation(operation_id)

    @Slot()
    def _validate_deferred_operations(self) -> None:
        if not self._executor or not self._deferred_validation_ids:
            return
        application = getattr(self._executor, "_application", None)
        if application is not None and application.server_state != "online":
            return
        operation_ids = list(self._deferred_validation_ids)
        self._deferred_validation_ids.clear()
        for operation_id in operation_ids:
            self._request_validation(operation_id)

    @Property(int, notify=stateChanged)
    def count(self) -> int:
        return len(self.model._records)

    @Property(int, notify=stateChanged)
    def unfinishedCount(self) -> int:
        return sum(
            1 for record in self.model._records
            if record.get("status") != "Completed"
        )

    @Property(str, notify=stateChanged)
    def selectedId(self) -> str:
        return self._selected_id

    @Property(int, notify=stateChanged)
    def selectedRow(self) -> int:
        return self._row_for_id(self._selected_id)

    @Property("QVariantMap", notify=stateChanged)
    def selectedRecord(self) -> dict:
        row = self._row_for_id(self._selected_id)
        record = dict(self.model._records[row]) if row >= 0 else {}
        record["error"] = str(record.get("error") or "")
        record["stage"] = str(record.get("stage") or "")
        return record

    @Property(bool, notify=stateChanged)
    def applyToChecked(self) -> bool:
        return self._apply_to_checked

    @Slot(bool)
    def set_apply_to_checked(self, value: bool) -> None:
        value = bool(value)
        if value == self._apply_to_checked:
            return
        self._apply_to_checked = value
        self.stateChanged.emit()

    @Property(bool, notify=stateChanged)
    def autoClean(self) -> bool:
        return self._auto_clean

    @Slot(bool)
    def set_auto_clean(self, value: bool) -> None:
        value = bool(value)
        if value == self._auto_clean:
            return
        self._auto_clean = value
        self._settings["commitQueue/autoClean"] = value
        self._write_settings()
        self.stateChanged.emit()

    @Property(bool, notify=stateChanged)
    def advancedOptionsExpanded(self) -> bool:
        return self._advanced_options_expanded

    @Slot(bool)
    def set_advanced_options_expanded(self, value: bool) -> None:
        value = bool(value)
        if value == self._advanced_options_expanded:
            return
        self._advanced_options_expanded = value
        self._settings["commitQueue/advancedOptionsExpanded"] = value
        self._write_settings()
        self.stateChanged.emit()

    @Property(float, notify=stateChanged)
    def filesPanelHeight(self) -> float:
        return self._files_panel_height

    @Slot(float)
    def set_files_panel_height(self, value: float) -> None:
        value = max(100.0, min(360.0, float(value)))
        if abs(value - self._files_panel_height) < 1.0:
            return
        self._files_panel_height = value
        self._settings["commitQueue/filesPanelHeight"] = value
        self._write_settings()
        self.stateChanged.emit()

    @Property(int, notify=stateChanged)
    def checkedCount(self) -> int:
        return sum(
            1 for record in self.model._records if record.get("checked")
        )

    @Property(bool, notify=duplicateChanged)
    def duplicatePending(self) -> bool:
        return self._duplicate_pending is not None

    @Property(str, notify=duplicateChanged)
    def duplicateDescription(self) -> str:
        pending = self._duplicate_pending or {}
        return str(pending.get("description") or "")

    @Property("QVariantList", notify=stateChanged)
    def repositories(self) -> list[dict]:
        result = []
        try:
            from thlib.environment import env_tactic

            for _key, repository in env_tactic.get_all_base_dirs():
                values = repository.get("value") or []
                if len(values) > 4 and values[4] and values[3]:
                    code = str(values[3])
                    if any(record["code"] == code for record in result):
                        continue
                    result.append({
                        "title": str(values[1] or code),
                        "code": code,
                    })
        except (AttributeError, IndexError, TypeError):
            pass
        return result

    def _assign_sole_repository(self, payload: dict) -> bool:
        if str(payload.get("repository") or "").strip():
            return False
        repositories = self.repositories
        if len(repositories) != 1:
            return False
        code = str(repositories[0].get("code") or "").strip()
        if not code:
            return False
        payload["repository"] = code
        return True

    @Slot()
    def reload_repository_configuration(self) -> None:
        changed_ids = []
        for operation_id, operation in self._operations.items():
            if self._assign_sole_repository(operation):
                changed_ids.append(operation_id)
        for operation_id in changed_ids:
            self._refresh_record(operation_id)
            self._request_validation(operation_id)
        if changed_ids:
            self._save()
        self.stateChanged.emit()

    def _row_for_id(self, operation_id: str) -> int:
        return next(
            (
                row for row, record in enumerate(self.model._records)
                if record["operationId"] == operation_id
            ),
            -1,
        )

    @staticmethod
    def _identity(payload: dict) -> tuple:
        return (
            str(payload.get("searchKey") or ""),
            str(payload.get("context") or ""),
            bool(payload.get("isRevision")),
            int(payload.get("version") or 0),
            tuple(sorted(
                str(Path(str(file_record.get("path") or ""))).casefold()
                for file_record in payload.get("files") or []
            )),
        )

    @staticmethod
    def _context_branch(process: str, context: str) -> str:
        process = str(process or "").strip().strip("/")
        context = str(context or "").strip().strip("/")
        if not context or context == process:
            return ""
        prefix = f"{process}/" if process else ""
        if prefix and context.startswith(prefix):
            return context[len(prefix):]
        return context

    @classmethod
    def _context_from_branch(cls, operation: dict, branch: str) -> str:
        process = str(operation.get("process") or "").strip().strip("/")
        current = str(operation.get("context") or "").strip().strip("/")
        base = process or current.split("/", 1)[0]
        branch = str(branch or "").strip().replace(" ", "_").strip("/")
        if base and branch.startswith(f"{base}/"):
            branch = branch[len(base) + 1:]
        if not branch:
            return base
        return f"{base}/{branch}" if base else branch

    @staticmethod
    def _record(operation_id: str, payload: dict, title: str) -> dict:
        files = list(payload.get("files") or [])
        context = str(payload.get("context") or "")
        process = str(payload.get("process") or "")
        context_branch = CommitQueueController._context_branch(process, context)
        repository = str(payload.get("repository") or "")
        versioned_paths = [
            str(record.get("versioned") or "") for record in files
        ]
        versionless_paths = [
            str(record.get("versionless") or "") for record in files
        ]
        preview_files = [
            str(path or "") for path in payload.get("previewFiles") or []
            if str(path or "")
        ]
        preview_urls = [
            QUrl.fromLocalFile(path).toString() for path in preview_files
        ]
        preview_path = next((
            str(record.get("path") or "") for record in files
            if Path(str(record.get("path") or "")).suffix.lower()
            in CommitQueueController._preview_extensions
        ), "")
        future_path = next((path for path in versioned_paths if path), "")
        source_path = str(files[0].get("path") or "") if files else ""
        future_file_name = Path(
            future_path
            or str(payload.get("explicitFilename") or "")
            or source_path
        ).name
        preview_extension = (
            Path(future_file_name or source_path).suffix.lstrip(".").upper()
            or "FILE"
        )
        version = int(payload.get("version") or 0)
        snapshot_info_chips = []
        if context_branch:
            snapshot_info_chips.append({
                "label": "Context", "value": context_branch,
            })
        if process:
            snapshot_info_chips.append({
                "label": "Process", "value": process,
            })
        return {
            "operationId": operation_id,
            "title": files[0].get("path", "").replace("\\", "/").rsplit(
                "/", 1
            )[-1] if files else title,
            "objectTitle": title,
            "fileCount": len(files),
            "context": context,
            "contextBranch": context_branch,
            "process": process,
            "repository": repository,
            "description": str(payload.get("description") or ""),
            "version": version,
            "updateVersionless": bool(payload.get("updateVersionless")),
            "onlyVersionless": bool(payload.get("onlyVersionless")),
            "keepFileName": bool(payload.get("keepFileName")),
            "generatePreviews": bool(payload.get("generatePreviews")),
            "explicitFilename": str(payload.get("explicitFilename") or ""),
            "contextAsFilename": bool(payload.get("contextAsFilename")),
            "mode": str(payload.get("mode") or "upload"),
            "sourceFiles": [str(record.get("path") or "") for record in files],
            "versionedPaths": versioned_paths,
            "versionlessPaths": versionless_paths,
            "previewFiles": preview_files,
            "previewUrls": preview_urls,
            "previewCount": len(preview_files),
            "previewUrl": (
                preview_urls[0] if preview_urls else
                QUrl.fromLocalFile(preview_path).toString()
                if preview_path else ""
            ),
            "futureFileName": future_file_name or title,
            "previewExtension": preview_extension[:8],
            "fileSummary": (
                f"{len(files)} file{'s' if len(files) != 1 else ''}"
            ),
            "versionLabel": f"v{version:03d}" if version else "",
            "snapshotInfoChips": snapshot_info_chips,
            "status": "Prepared",
            "selected": False,
            "error": "",
            "canEdit": True,
            "canCommit": True,
            "checked": True,
            "progress": 0.0,
            "stage": "prepared",
            "summary": (
                f"{len(files)} file{'s' if len(files) != 1 else ''}"
                f" • {context or process} • {repository}"
            ),
        }

    def _refresh_record(self, operation_id: str) -> None:
        row = self._row_for_id(operation_id)
        operation = self._operations.get(operation_id)
        if row < 0 or operation is None:
            return
        previous = self.model._records[row]
        record = self._record(
            operation_id, operation,
            str(previous.get("objectTitle") or "sObject"),
        )
        for key in (
            "status", "selected", "error", "canEdit", "canCommit",
            "checked", "progress", "stage",
        ):
            record[key] = previous.get(key, record.get(key))
        self.model.replace_row(row, record)

    @staticmethod
    def _local_path(value) -> str:
        url = value if isinstance(value, QUrl) else QUrl(str(value or ""))
        path = url.toLocalFile() if url.isLocalFile() else str(value or "")
        return str(Path(path).resolve()) if path else ""

    @Slot("QVariantList")
    def add_selected_previews(self, values: list) -> None:
        self.add_preview_paths(self._selected_id, values)

    def add_preview_paths(self, operation_id: str, values: list) -> bool:
        operation = self._operations.get(str(operation_id or ""))
        row = self._row_for_id(str(operation_id or ""))
        if (
            operation is None or row < 0
            or not self.model._records[row].get("canEdit", False)
        ):
            return False
        previews = list(operation.get("previewFiles") or [])
        known = {os.path.normcase(path) for path in previews}
        added = False
        for value in values or []:
            try:
                path = self._local_path(value)
            except (OSError, RuntimeError, ValueError):
                continue
            if (
                not path or not Path(path).is_file()
                or Path(path).suffix.lower() not in self._preview_extensions
                or os.path.normcase(path) in known
            ):
                continue
            previews.append(path)
            known.add(os.path.normcase(path))
            added = True
        if not added:
            return False
        operation["previewFiles"] = previews
        self._refresh_record(operation_id)
        self._save()
        self.stateChanged.emit()
        return True

    @Slot(int)
    def remove_selected_preview(self, row: int) -> None:
        operation = self._operations.get(self._selected_id)
        if operation is None:
            return
        previews = list(operation.get("previewFiles") or [])
        if not 0 <= row < len(previews):
            return
        previews.pop(row)
        operation["previewFiles"] = previews
        self._refresh_record(self._selected_id)
        self._save()
        self.stateChanged.emit()

    @Slot()
    def clear_selected_previews(self) -> None:
        operation = self._operations.get(self._selected_id)
        if operation is None or not operation.get("previewFiles"):
            return
        operation["previewFiles"] = []
        self._refresh_record(self._selected_id)
        self._save()
        self.stateChanged.emit()

    def add_prepared(self, payload: dict, title: str) -> str:
        safe_payload = deepcopy(payload)
        self._assign_sole_repository(safe_payload)
        identity = self._identity(safe_payload)
        existing_id = next(
            (
                operation_id
                for operation_id, operation in self._operations.items()
                if self._identity(operation) == identity
            ),
            "",
        )
        if existing_id:
            pending = {
                "existingId": existing_id,
                "payload": safe_payload,
                "title": str(title or "sObject"),
                "description": (
                    "The same files are already prepared for this object "
                    "and context."
                ),
            }
            if self._duplicate_pending is None:
                self._duplicate_pending = pending
            else:
                self._duplicate_queue.append(pending)
            self._select_id(existing_id)
            self.duplicateChanged.emit()
            return existing_id
        operation_id = uuid.uuid4().hex
        self._operations[operation_id] = safe_payload
        self._current_session_ids.add(operation_id)
        record = self._record(operation_id, safe_payload, title)
        row = self._row_for_id(operation_id)
        if row >= 0:
            old = self.model._records[row]
            record["checked"] = old.get("checked", True)
            self.model.replace_row(row, record)
        else:
            self.model.append(record)
        self._select_id(operation_id)
        self._save()
        self._request_validation(operation_id)
        return operation_id

    @Slot(str)
    def resolve_duplicate(self, decision: str) -> None:
        pending = self._duplicate_pending
        if not pending:
            return
        decision = str(decision or "ignore")
        if decision == "replace" and pending["existingId"] != self._active_id:
            operation_id = pending["existingId"]
            self._operations[operation_id] = pending["payload"]
            self._current_session_ids.add(operation_id)
            row = self._row_for_id(operation_id)
            if row >= 0:
                checked = self.model._records[row].get("checked", True)
                record = self._record(
                    operation_id, pending["payload"], pending["title"]
                )
                record["checked"] = checked
                self.model.replace_row(row, record)
            self._select_id(operation_id)
            self._save()
            self._request_validation(operation_id)
        elif decision == "add":
            operation_id = uuid.uuid4().hex
            self._operations[operation_id] = pending["payload"]
            self._current_session_ids.add(operation_id)
            self.model.append(self._record(
                operation_id, pending["payload"], pending["title"]
            ))
            self._select_id(operation_id)
            self._save()
            self._request_validation(operation_id)
        self._duplicate_pending = (
            self._duplicate_queue.pop(0) if self._duplicate_queue else None
        )
        self.duplicateChanged.emit()

    def operation(self, operation_id: str) -> dict | None:
        operation = self._operations.get(operation_id)
        return deepcopy(operation) if operation is not None else None

    def update_operation_description(self, operation_id: str, text: str) -> None:
        """Edit one explicit API target, independent of selected/checked rows."""
        row = self._row_for_id(operation_id)
        if row < 0:
            raise ValueError("Queue item is unavailable")
        if not self.model._records[row].get("canEdit", False):
            raise ValueError("Queue item is not editable")
        self._operations[operation_id]["description"] = str(text)
        self._set_record(operation_id, description=str(text))
        self._save()
        self.stateChanged.emit()

    def _select_id(self, operation_id: str) -> None:
        self._selected_id = operation_id
        for row, record in enumerate(self.model._records):
            selected = record["operationId"] == operation_id
            if record.get("selected") == selected:
                continue
            record["selected"] = selected
            index = self.model.index(row, 0)
            self.model.dataChanged.emit(
                index, index, [self.model._role_ids["selected"]]
            )
        self.stateChanged.emit()

    @Slot(int)
    def select_row(self, row: int) -> None:
        if 0 <= row < len(self.model._records):
            self._select_id(self.model._records[row]["operationId"])

    @Slot(int)
    def remove_row(self, row: int) -> None:
        if not 0 <= row < len(self.model._records):
            return
        operation_id = self.model._records[row]["operationId"]
        if operation_id == self._active_id:
            return
        self._operations.pop(operation_id, None)
        self._current_session_ids.discard(operation_id)
        self._discard_duplicate_references(operation_id)
        self.model.remove_row(row)
        if operation_id == self._selected_id:
            next_row = min(row, len(self.model._records) - 1)
            self._selected_id = ""
            if next_row >= 0:
                self._select_id(
                    self.model._records[next_row]["operationId"]
                )
            else:
                self.stateChanged.emit()
        self._save()

    def _discard_duplicate_references(self, operation_id: str) -> None:
        changed = False
        if (
            self._duplicate_pending
            and self._duplicate_pending.get("existingId") == operation_id
        ):
            self._duplicate_pending = None
            changed = True
        filtered = [
            pending for pending in self._duplicate_queue
            if pending.get("existingId") != operation_id
        ]
        if len(filtered) != len(self._duplicate_queue):
            self._duplicate_queue = filtered
            changed = True
        if self._duplicate_pending is None and self._duplicate_queue:
            self._duplicate_pending = self._duplicate_queue.pop(0)
        if changed:
            self.duplicateChanged.emit()

    @Slot()
    def clear(self) -> None:
        for row in range(len(self.model._records) - 1, -1, -1):
            if self.model._records[row]["operationId"] != self._active_id:
                self.remove_row(row)

    @Slot(int, int)
    def move_row(self, source: int, target: int) -> None:
        if self._active_id:
            return
        if self.model.move_row(source, target):
            self._save()
            self.stateChanged.emit()

    @Slot(int)
    def move_selected(self, offset: int) -> None:
        if self._active_id:
            return
        source = self.selectedRow
        target = source + int(offset)
        if self.model.move_row(source, target):
            self._save()
            self.stateChanged.emit()

    @Slot(int)
    def toggle_checked(self, row: int) -> None:
        if not 0 <= row < len(self.model._records):
            return
        record = dict(self.model._records[row])
        if record["operationId"] == self._active_id:
            return
        record["checked"] = not record.get("checked", True)
        self.model.replace_row(row, record)
        self._save()

    @Slot(int)
    def remove_selected_file(self, file_row: int) -> None:
        row = self.selectedRow
        operation = self._operations.get(self._selected_id)
        if (
            row < 0 or operation is None
            or not self.model._records[row].get("canEdit", False)
        ):
            return
        files = list(operation.get("files") or [])
        if not 0 <= file_row < len(files):
            return
        if operation.get("dccScene") and file_row == 0:
            return
        files.pop(file_row)
        if not files:
            self.remove_row(row)
            return
        operation["files"] = files
        for key in ("filesDict", "dropPlateGroupIds"):
            values = list(operation.get(key) or [])
            if len(values) > file_row:
                values.pop(file_row)
                operation[key] = values
        title = self.model._records[row].get("objectTitle", "sObject")
        checked = self.model._records[row].get("checked", True)
        record = self._record(self._selected_id, operation, title)
        record["checked"] = checked
        record["selected"] = True
        self.model.replace_row(row, record)
        self._save()
        self._request_validation(self._selected_id)

    @Slot(str, "QVariant")
    def update_selected(self, field: str, value) -> None:
        if field not in self._editable:
            return
        row = self.selectedRow
        operation = self._operations.get(self._selected_id)
        if (
            row < 0 or operation is None
            or not self.model._records[row].get("canEdit", False)
        ):
            return
        if field == "version":
            try:
                value = max(0, int(value or 0))
            except (TypeError, ValueError):
                return
        elif field in {
            "updateVersionless", "onlyVersionless", "keepFileName",
            "generatePreviews", "contextAsFilename",
        }:
            value = bool(value)
        else:
            value = str(value or "")
            if field == "explicitFilename":
                value = value.strip().replace(" ", "_")
        if operation.get(field) == value and not self._apply_to_checked:
            return
        self._update_selected_value(field, value)

    @Slot(str)
    def update_selected_context_branch(self, branch: str) -> None:
        row = self.selectedRow
        operation = self._operations.get(self._selected_id)
        if (
            row < 0 or operation is None
            or not self.model._records[row].get("canEdit", False)
        ):
            return
        full_context = self._context_from_branch(operation, branch)
        if (
            operation.get("context") == full_context
            and not self._apply_to_checked
        ):
            return
        self._update_selected_value(
            "context",
            str(branch or ""),
            self._context_from_branch,
        )

    def _update_selected_value(
        self,
        field: str,
        value,
        value_for_operation=None,
    ) -> None:
        target_ids = [self._selected_id]
        if self._apply_to_checked:
            target_ids.extend(
                record["operationId"] for record in self.model._records
                if record.get("checked") and record.get("canEdit")
            )
        for operation_id in dict.fromkeys(target_ids):
            target_operation = self._operations.get(operation_id)
            target_row = self._row_for_id(operation_id)
            if (
                target_operation is None or target_row < 0
                or not self.model._records[target_row].get("canEdit", False)
            ):
                continue
            target_value = (
                value_for_operation(target_operation, value)
                if value_for_operation else value
            )
            target_operation[field] = target_value
            if field == "keepFileName" and value:
                target_operation["updateVersionless"] = False
            if field == "onlyVersionless" and value:
                target_operation["updateVersionless"] = True
            if field == "contextAsFilename" and value:
                context_branch = self._context_branch(
                    str(target_operation.get("process") or ""),
                    str(target_operation.get("context") or ""),
                )
                if context_branch:
                    target_operation["explicitFilename"] = context_branch
                elif target_operation.get("explicitFilename"):
                    target_operation["context"] = self._context_from_branch(
                        target_operation,
                        str(target_operation["explicitFilename"]),
                    )
                else:
                    target_operation["explicitFilename"] = ""
            if field == "context" and target_operation.get("contextAsFilename"):
                target_operation["explicitFilename"] = target_value.split("/")[-1]
            if (
                field == "explicitFilename"
                and target_operation.get("contextAsFilename")
            ):
                target_operation["context"] = self._context_from_branch(
                    target_operation, target_value
                )
            if target_operation.get("dccScene"):
                target_operation["ignoreKeepFileName"] = not bool(
                    target_operation.get("explicitFilename")
                )
            record = self._record(
                operation_id,
                target_operation,
                self.model._records[target_row]["objectTitle"],
            )
            record["status"] = self.model._records[target_row]["status"]
            if field in self._naming_fields:
                target_operation.pop("virtualSnapshot", None)
                record["status"] = "Needs validation"
                record["canCommit"] = False
            self.model.replace_row(target_row, record)
            if field in self._naming_fields:
                self._request_validation(operation_id)
        self._select_id(self._selected_id)
        self._save()

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return bool(self._active_id)

    @Property(bool, notify=stateChanged)
    def hasCompleted(self) -> bool:
        return any(
            record.get("status") == "Completed"
            for record in self.model._records
        )

    @Property(bool, notify=stateChanged)
    def hasReady(self) -> bool:
        return any(record.get("canCommit") for record in self.model._records)

    @Property(bool, notify=stateChanged)
    def hasCheckedReady(self) -> bool:
        return any(
            record.get("checked") and record.get("canCommit")
            for record in self.model._records
        )

    def _set_record(self, operation_id: str, **values) -> None:
        row = self._row_for_id(operation_id)
        if row < 0:
            return
        record = dict(self.model._records[row])
        record.update(values)
        self.model.replace_row(row, record)

    def _request_validation(self, operation_id: str) -> None:
        if not self._executor or operation_id == self._active_id:
            return
        payload = self._operations.get(operation_id)
        row = self._row_for_id(operation_id)
        if not payload or row < 0:
            return
        generation = self._validation_generation.get(operation_id, 0) + 1
        self._validation_generation[operation_id] = generation
        request_id = f"{operation_id}:{generation}"
        self._set_record(
            operation_id, status="Validating", stage="naming",
            error="", canCommit=False,
        )
        self._executor.validate_prepared_operation(request_id, payload)

    @Slot(str, bool, "QVariantMap", str)
    def _prepared_validation_finished(
        self, request_id: str, success: bool, result: dict, error: str
    ) -> None:
        operation_id, separator, generation_text = request_id.rpartition(":")
        if not separator:
            return
        try:
            generation = int(generation_text)
        except ValueError:
            return
        if self._validation_generation.get(operation_id) != generation:
            return
        row = self._row_for_id(operation_id)
        if row < 0 or operation_id == self._active_id:
            return
        if success:
            payload = self._operations.get(operation_id)
            if payload is not None:
                payload["virtualSnapshot"] = result.get("virtualSnapshot")
                files = list(payload.get("files") or [])
                versioned = list(result.get("versionedPaths") or [])
                versionless = list(result.get("versionlessPaths") or [])
                for index, file_record in enumerate(files):
                    if index < len(versioned):
                        file_record["versioned"] = versioned[index]
                    if index < len(versionless):
                        file_record["versionless"] = versionless[index]
                payload["files"] = files
                record = self._record(
                    operation_id, payload,
                    self.model._records[row]["objectTitle"],
                )
                record["checked"] = self.model._records[row].get("checked", True)
                record["selected"] = operation_id == self._selected_id
                record["status"] = "Prepared"
                record["stage"] = "prepared"
                record["canCommit"] = True
                self.model.replace_row(row, record)
        else:
            self._set_record(
                operation_id, status="Invalid", stage="validation failed",
                error=str(error or "Naming validation failed"),
                canCommit=False, canEdit=True,
            )
        self._save()
        self.stateChanged.emit()

    def _start_ids(self, operation_ids: list[str]) -> None:
        if self._active_id or not self._executor:
            return
        self._batch_ids = [
            operation_id for operation_id in operation_ids
            if operation_id in self._operations
            and self.model._records[self._row_for_id(operation_id)].get(
                "status"
            ) not in {"Running", "Completed"}
            and self.model._records[self._row_for_id(operation_id)].get(
                "canCommit", False
            )
        ]
        self._start_next()

    def _start_next(self) -> None:
        if self._active_id or not self._batch_ids:
            self._save()
            self.stateChanged.emit()
            return
        operation_id = self._batch_ids.pop(0)
        payload = self.operation(operation_id)
        if not payload:
            self._start_next()
            return
        self._active_id = operation_id
        self._select_id(operation_id)
        self._set_record(
            operation_id, status="Queued", stage="preparing",
            progress=0.0, error="", canEdit=False,
        )
        execution_payload = deepcopy(payload)
        execution_payload["_refreshTreeOnComplete"] = (
            operation_id in self._current_session_ids
        )
        if not self._executor.start_prepared_operation(execution_payload):
            self._set_record(
                operation_id, status="Failed", stage="failed",
                error="Check-in engine is busy", canEdit=True,
            )
            self._active_id = ""
            self._batch_ids.clear()
        self._save()
        self.stateChanged.emit()

    @Slot()
    def commit_current(self) -> None:
        if self._selected_id:
            self._start_ids([self._selected_id])

    @Slot()
    def commit_selected(self) -> None:
        self._start_ids([
            record["operationId"] for record in self.model._records
            if record.get("checked")
        ])

    @Slot()
    def commit_all(self) -> None:
        self._start_ids([
            record["operationId"] for record in self.model._records
        ])

    @Slot()
    def retry_current(self) -> None:
        row = self.selectedRow
        if row < 0 or self.model._records[row].get("status") != "Failed":
            return
        self._start_ids([self._selected_id])

    @Slot()
    def cancel(self) -> None:
        self._batch_ids.clear()
        if self._active_id and self._executor:
            self._executor.cancel_checkin()
        self.stateChanged.emit()

    @Slot()
    def remove_completed(self) -> None:
        for row in range(len(self.model._records) - 1, -1, -1):
            if self.model._records[row].get("status") == "Completed":
                self.remove_row(row)

    @Slot()
    def _operation_changed(self) -> None:
        if not self._active_id or not self._executor:
            return
        status = {
            "queued": "Queued",
            "running": "Running",
            "failed": "Failed",
            "completed": "Completed",
            "cancelled": "Cancelled",
        }.get(self._executor.operationState, "Running")
        self._set_record(
            self._active_id,
            status=status,
            stage=self._executor.operationStage,
            progress=self._executor.operationProgress,
            error=self._executor.operationError,
            canEdit=status in {"Failed", "Cancelled"},
        )

    @Slot(bool, str)
    def _operation_finished(self, succeeded: bool, error: str) -> None:
        operation_id = self._active_id
        if not operation_id:
            return
        status = "Completed" if succeeded else (
            "Cancelled" if self._executor.operationState == "cancelled"
            else "Failed"
        )
        self._set_record(
            operation_id, status=status,
            stage=status.lower(), progress=1.0 if succeeded else 0.0,
            error=str(error or ""), canEdit=not succeeded,
        )
        self._active_id = ""
        self._save()
        if succeeded:
            payload = self._operations.get(operation_id)
            if payload:
                self.operationCompleted.emit(deepcopy(payload))
            if self._auto_clean:
                row = self._row_for_id(operation_id)
                if row >= 0:
                    self.remove_row(row)
            self._start_next()
            self._close_finished_auto_clean_queue()
        else:
            self._batch_ids.clear()
            self.stateChanged.emit()

    def _close_finished_auto_clean_queue(self) -> None:
        if (
                not self._auto_clean
                or self._active_id
                or self._batch_ids
                or self.model._records
                or self._window_model is None
                or not self._window_model.is_window_visible("commit_queue")):
            return
        self._window_model.close_window("commit_queue")

    def _save(self) -> None:
        entries = []
        for record in self.model._records:
            if record.get("status") == "Completed":
                continue
            operation_id = record["operationId"]
            payload = self._operations.get(operation_id)
            if payload:
                entries.append({
                    "id": operation_id,
                    "title": record.get("objectTitle", ""),
                    "checked": record.get("checked", True),
                    "payload": payload,
                })
        try:
            json.dumps(entries, ensure_ascii=False)
        except (TypeError, ValueError):
            return
        env_write_config(
            entries,
            filename="pending",
            unique_id="cache/commit_queue",
            long_abs_path=True,
        )

    def _restore(self) -> None:
        entries = env_read_config(
            filename="pending",
            unique_id="cache/commit_queue",
            long_abs_path=True,
        ) or []
        repaired_repository = False
        for entry in entries if isinstance(entries, list) else []:
            payload = entry.get("payload") if isinstance(entry, dict) else None
            if not isinstance(payload, dict):
                continue
            repaired_repository = (
                self._assign_sole_repository(payload)
                or repaired_repository
            )
            operation_id = str(entry.get("id") or uuid.uuid4().hex)
            self._operations[operation_id] = payload
            record = self._record(
                operation_id, payload, str(entry.get("title") or "sObject")
            )
            record["checked"] = bool(entry.get("checked", True))
            record["status"] = "Prepared"
            missing = next((
                str(file_record.get("path") or "")
                for file_record in payload.get("files") or []
                if file_record.get("path")
                and not Path(str(file_record["path"])).is_file()
            ), "")
            if missing:
                record["status"] = "Missing files"
                record["error"] = f"Source file is unavailable: {missing}"
                record["canCommit"] = False
            self.model.append(record)
        if self.model._records:
            self._select_id(self.model._records[0]["operationId"])
        if repaired_repository:
            self._save()

    def shutdown(self) -> None:
        self._batch_ids.clear()
        if self._active_id and self._executor:
            self._executor.cancel_checkin()
        self._save()
        self._write_settings()

    def _write_settings(self) -> None:
        env_write_config(
            self._settings,
            filename="ui_commit_queue",
            unique_id="ui_main",
            long_abs_path=True,
        )
