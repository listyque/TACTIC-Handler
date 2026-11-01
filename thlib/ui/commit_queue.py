from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import uuid
import threading
import time
from collections import Counter

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QObject,
    Property,
    Qt,
    QUrl,
    QTimer,
    Signal,
    Slot,
)

from thlib.environment import env_read_config, env_write_config
from thlib.checkin_operation import apply_checkin_type_options, versionless_allowed


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
        "versionLabel", "snapshotInfoChips", "versionlessAllowed",
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
        self.append_records([record])

    def append_records(self, records: list[dict]) -> None:
        if not records:
            return
        row = len(self._records)
        self.beginInsertRows(QModelIndex(), row, row + len(records) - 1)
        self._records.extend(dict(record) for record in records)
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
    progressChanged = Signal()
    operationCompleted = Signal("QVariantMap")
    presentationRefreshRequested = Signal("QVariantMap")

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
        self._pending_refreshes = {}
        self._dirty_projects = set()
        self._executor = None
        self._server_queue = False
        self._server_closed = False
        self._server_batches = env_read_config(filename="server_batches",unique_id="cache/commit_queue",long_abs_path=True) or {}
        if not isinstance(self._server_batches,dict):
            self._server_batches = {}
        for batch in self._server_batches.values():
            if not batch.get('submitted'):
                batch['uploadError'] = batch.get('uploadError') or 'Upload interrupted; resume the original batch'
        self._server_cursors = {}
        self._server_cleanup_ids = set()
        self._server_worker = None
        self._server_poll_worker = None
        self._server_uploading = False
        self._server_progress = {}
        self._server_progress_started = time.monotonic()
        self._server_last_activity = self._server_progress_started
        self._server_progress_error = ''
        self._server_progress_timer = QTimer(self)
        self._server_progress_timer.setInterval(1000)
        self._server_progress_timer.timeout.connect(self.progressChanged)
        self._server_cancel_event = threading.Event()
        self._server_timer = QTimer(self)
        self._server_timer.setSingleShot(True)
        self._server_timer.timeout.connect(self._poll_server_queue)
        self._apply_to_checked = False
        self._auto_clean = bool(
            self._settings.get("commitQueue/autoClean", True)
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
        try:
            splitter_ratio = float(self._settings.get("commitQueue/splitterRatio", 0.36))
        except (TypeError, ValueError):
            splitter_ratio = 0.36
        self._splitter_ratio = max(0.15, min(0.85, splitter_ratio))
        self._duplicate_pending = None
        self._duplicate_queue = []
        self._validation_generation = {}
        self._pending_validations = {}
        self._validation_inflight = set()
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(100)
        self._save_timer.timeout.connect(self._save)
        self._deferred_validation_ids = set()
        self.model.contentChanged.connect(self.stateChanged)
        self._restore()
        if self._server_batches and self.serverQueueAvailable:
            self._server_timer.start(1000)

    def attach_executor(self, executor) -> None:
        self._executor = executor
        executor.preparationChanged.connect(self._operation_changed)
        executor.operationFinished.connect(self._operation_finished)
        executor.operationResult.connect(self._operation_result)
        executor.preparedValidationFinished.connect(
            self._prepared_validation_finished
        )
        application = getattr(executor, "_application", None)
        if application is not None:
            application.server_state_changed.connect(
                self._validate_deferred_operations
            )
            if hasattr(application, 'authentication_changed'):
                application.authentication_changed.connect(self._server_api_changed)
        self._server_api_changed()
        for operation_id,payload in self._operations.items():
            if (payload.get('_serverQueue') or {}).get('state') == 'complete' and payload.get('mode') == 'move' and not payload.get('_serverMoveCleaned'):
                self._finish_server_move(operation_id)
        operation_ids = set(self._operations)
        if application is not None and application.server_state != "online":
            self._deferred_validation_ids.update(operation_ids)
        else:
            self._request_validations(operation_ids)

    @Slot()
    def _validate_deferred_operations(self) -> None:
        if not self._executor or not self._deferred_validation_ids:
            return
        application = getattr(self._executor, "_application", None)
        if application is not None and application.server_state != "online":
            return
        operation_ids = list(self._deferred_validation_ids)
        self._deferred_validation_ids.clear()
        self._request_validations(operation_ids)

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

    @Property(float, notify=stateChanged)
    def splitterRatio(self) -> float:
        return self._splitter_ratio

    @Slot(float)
    def set_splitter_ratio(self, value: float) -> None:
        value = max(0.15, min(0.85, float(value)))
        if abs(value - self._splitter_ratio) < 0.002:
            return
        self._splitter_ratio = value
        self._settings["commitQueue/splitterRatio"] = value
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

    @Slot(str, result=int)
    def row_for_id(self, operation_id: str) -> int:
        return self._row_for_id(operation_id)

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
            "versionlessAllowed": versionless_allowed(payload),
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
        return self.add_prepared_many([(payload, title)])[0]

    def add_prepared_many(self, entries: list[tuple[dict, str]]) -> list[str]:
        identities = {self._identity(payload): operation_id
                      for operation_id, payload in self._operations.items()}
        ids, records = [], []
        duplicate = False
        for payload, title in entries:
            safe_payload = deepcopy(payload)
            apply_checkin_type_options(safe_payload)
            self._assign_sole_repository(safe_payload)
            identity = self._identity(safe_payload)
            existing_id = identities.get(identity)
            if existing_id:
                pending = dict(existingId=existing_id, payload=safe_payload,
                               title=str(title or 'sObject'),
                               description='The same files are already prepared for this object and context.')
                if self._duplicate_pending is None:
                    self._duplicate_pending = pending
                else:
                    self._duplicate_queue.append(pending)
                ids.append(existing_id)
                duplicate = True
                continue
            operation_id = uuid.uuid4().hex
            identities[identity] = operation_id
            safe_payload["operation_id"] = operation_id
            self._operations[operation_id] = safe_payload
            self._current_session_ids.add(operation_id)
            records.append(self._record(operation_id, safe_payload, title))
            ids.append(operation_id)
        self.model.append_records(records)
        if ids:
            self._select_id(ids[-1])
        if records:
            self._save()
            self._request_validations([record['operationId'] for record in records])
        if duplicate:
            self.duplicateChanged.emit()
        return ids

    @Slot(str)
    def resolve_duplicate(self, decision: str) -> None:
        pending = self._duplicate_pending
        if not pending:
            return
        decision = str(decision or "ignore")
        if decision == "replace" and pending["existingId"] != self._active_id:
            operation_id = pending["existingId"]
            pending["payload"]["operation_id"] = operation_id
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
            pending["payload"]["operation_id"] = operation_id
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
        reference = self._operations.get(operation_id, {}).get("_serverQueue") or {}
        if operation_id == self._active_id or (reference and reference.get("state") not in ("complete", "error", "terminated")):
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
        self._save_timer.start()

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
        if not self.busy and not self._server_batches:
            self._server_progress.clear()
            self._server_progress_error = ''
            self._server_progress_timer.stop()
            self.progressChanged.emit()

    @Slot(int, int)
    def move_row(self, source: int, target: int) -> None:
        if self.busy:
            return
        if self.model.move_row(source, target):
            self._save()
            self.stateChanged.emit()

    @Slot(int)
    def move_selected(self, offset: int) -> None:
        if self.busy:
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
            apply_checkin_type_options(target_operation)
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
        return bool(self._active_id or self._batch_ids or self._server_uploading or self._server_cleanup_ids or self._server_pending())

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
        self._request_validations([operation_id])

    def _request_validations(self, operation_ids) -> None:
        if not self._executor or self._server_closed:
            return
        for operation_id in operation_ids:
            payload = self._operations.get(operation_id)
            if not payload or operation_id == self._active_id or payload.get('_serverQueue'):
                continue
            generation = self._validation_generation.get(operation_id, 0) + 1
            self._validation_generation[operation_id] = generation
            if self.serverQueue:
                self._pending_validations.pop(operation_id, None)
                supported = bool(payload.get('files')) and not bool(payload.get('dccScene'))
                self._set_record(operation_id, status='Prepared' if supported else 'Invalid', stage='server naming',
                                 canCommit=supported, error='' if supported else 'DCC scenes require the legacy mode')
                continue
            self._pending_validations[operation_id] = f'{operation_id}:{generation}'
            self._set_record(operation_id, status='Validating', stage='naming', error='', canCommit=False)
        self._start_validation_chunk()

    def _start_validation_chunk(self) -> None:
        if self._validation_inflight or not self._executor or self._server_closed:
            return
        operations = []
        for operation_id in list(self._pending_validations):
            request_id = self._pending_validations.pop(operation_id)
            payload = self._operations.get(operation_id)
            if payload and operation_id != self._active_id:
                operations.append((request_id, deepcopy(payload)))
                if len(operations) == 50:
                    break
        if not operations:
            return
        self._validation_inflight.update(request_id for request_id, payload in operations)
        if len(operations) == 1:
            self._executor.validate_prepared_operation(*operations[0])
        else:
            self._executor.validate_prepared_operations(operations)

    @Slot(str, bool, "QVariantMap", str)
    def _prepared_validation_finished(
        self, request_id: str, success: bool, result: dict, error: str
    ) -> None:
        self._validation_inflight.discard(request_id)
        if not self._validation_inflight:
            self._start_validation_chunk()
        if self._server_closed:
            return
        operation_id, separator, generation_text = request_id.rpartition(":")
        if not separator:
            return
        try:
            generation = int(generation_text)
        except ValueError:
            return
        if self.serverQueue or self._validation_generation.get(operation_id) != generation:
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
        self._save_timer.start()
        self.stateChanged.emit()

    def _start_ids(self, operation_ids: list[str]) -> None:
        if self.busy:
            return
        for operation_id in operation_ids:
            payload = self._operations.get(operation_id) or {}
            if self.serverQueueAvailable and (payload.get('_serverQueue') or {}).get('state') in ('error','terminated'):
                payload.pop('_serverQueue',None)
                self._set_record(operation_id,canCommit=True,canEdit=True)
        if self.serverQueue:
            self._start_server_ids(operation_ids)
            return
        if self._active_id or not self._executor:
            return
        self._batch_ids = [
            operation_id for operation_id in operation_ids
            if operation_id in self._operations
            and not self._operations[operation_id].get('_serverQueue')
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
            self._flush_refreshes()
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
        execution_payload["_refreshTreeOnComplete"] = False
        if not self._executor.start_prepared_operation(execution_payload):
            self._set_record(
                operation_id, status="Failed", stage="failed",
                error="Check-in engine is busy", canEdit=True,
            )
            self._active_id = ""
            self._batch_ids.clear()
            self._flush_refreshes()
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
        if self.serverResumeAvailable:
            reference = self._operations[self._selected_id]['_serverQueue']
            self._send_server_batches([self._server_batches[reference['batch_id']]])
            return
        row = self.selectedRow
        if row < 0 or self.model._records[row].get("status") != "Failed":
            return
        self._start_ids([self._selected_id])

    @Slot()
    def cancel(self) -> None:
        if self._server_batches:
            self._server_cancel_event.set()
            if not self._server_uploading:
                self._cancel_server_batches()
        self._batch_ids.clear()
        if self._active_id and self._executor:
            self._executor.cancel_checkin()
        self._flush_refreshes()
        self.stateChanged.emit()

    @Slot()
    def remove_completed(self) -> None:
        for row in range(len(self.model._records) - 1, -1, -1):
            if self.model._records[row].get("status") == "Completed":
                self.remove_row(row)
        if not self.count:
            self.clear()

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

    @Slot(object)
    def _operation_result(self, snapshot) -> None:
        payload = self._operations.get(self._active_id)
        if payload is not None:
            from thlib.tactic_classes import split_search_key

            project = split_search_key(payload['searchKey']).get('project_code') or ''
            self._remember_refresh(self._active_id, payload, snapshot, project)

    def _remember_refresh(self, operation_id, payload, snapshot, project) -> None:
        self._dirty_projects.add(project)
        key = (payload['searchKey'], payload['context'])
        previous = self._pending_refreshes.get(key)
        reveal = operation_id in self._current_session_ids or bool(previous and previous[2])
        self._pending_refreshes[key] = (deepcopy(payload), deepcopy(snapshot), reveal)

    def _flush_refreshes(self, *, force=False) -> None:
        if not force and self.busy:
            return
        from thlib import server_cache

        projects, self._dirty_projects = self._dirty_projects, set()
        refreshes, self._pending_refreshes = self._pending_refreshes, {}
        for project in projects:
            server_cache.invalidate_domains(
                ('snapshots', 'relations', 'search', 'activity'), project,
            )
        if self._server_closed:
            return
        application = getattr(self._executor, '_application', None)
        for payload, snapshot, reveal in refreshes.values():
            if application is not None and reveal:
                application.refresh_checkin_result(payload, snapshot)
            self.presentationRefreshRequested.emit(payload)

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
            self._flush_refreshes()
            self.stateChanged.emit()

    def _close_finished_auto_clean_queue(self) -> None:
        if (
                not self._auto_clean
                or self._active_id
                or self._server_uploading
                or self._batch_ids
                or self.model._records
                or self._window_model is None
                or not self._window_model.is_window_visible("commit_queue")):
            return
        self._window_model.close_window("commit_queue")

    def _save(self) -> None:
        self._save_timer.stop()
        env_write_config(self._server_batches,filename="server_batches",unique_id="cache/commit_queue",long_abs_path=True)
        entries = []
        for record in self.model._records:
            if record.get("status") == "Completed" and not (
                    self._operations.get(record['operationId'],{}).get('mode') == 'move'
                    and not self._operations.get(record['operationId'],{}).get('_serverMoveCleaned')):
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
            if not payload.get("_serverQueue"):
                apply_checkin_type_options(payload)
            repaired_repository = (
                self._assign_sole_repository(payload)
                or repaired_repository
            )
            operation_id = str(entry.get("id") or uuid.uuid4().hex)
            payload["operation_id"] = operation_id
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
            if payload.get('_serverQueue'):
                state = payload['_serverQueue'].get('state','pending')
                record.update(status={'complete':'Completed','error':'Failed','terminated':'Cancelled'}.get(state,'Queued'),
                              stage='server ' + state,canCommit=state in ('error','terminated'),canEdit=False)
            elif missing:
                record["status"] = "Missing files"
                record["error"] = f"Source file is unavailable: {missing}"
                record["canCommit"] = False
            self.model.append(record)
        if self.model._records:
            self._select_id(self.model._records[0]["operationId"])
        if repaired_repository:
            self._save()

    def shutdown(self) -> None:
        self._server_closed = True
        self._pending_validations.clear()
        self._save_timer.stop()
        self._server_timer.stop()
        self._server_progress_timer.stop()
        self._server_cancel_event.set()
        # Closing the client does not cancel accepted server work.
        self._flush_refreshes(force=True)
        self._batch_ids.clear()
        if self._active_id and self._executor:
            self._executor.cancel_checkin()
        self._save()
        self._write_settings()

    @Property('QVariantMap', notify=progressChanged)
    def serverProgress(self) -> dict:
        batches = list(self._server_progress.values())
        if not batches and not self._server_batches:
            return {}
        result = {key: sum(batch.get(key, 0) for batch in batches) for key in (
            'totalOperations', 'totalFiles', 'filesDone', 'totalBytes', 'bytesDone',
            'completed', 'failed', 'cancelled', 'running')}
        if not batches:
            result['totalOperations'] = sum(len(batch['operations']) for batch in self._server_batches.values())
        active = next((batch for batch in batches if batch.get('phase') != 'uploaded'), {})
        result['phase'] = active.get('phase', 'preparing') if self._server_uploading else (
            'committing' if self._server_pending() else 'finished')
        result['filename'] = active.get('filename', '') if self._server_uploading else ''
        result['totalsKnown'] = bool(batches) and all(batch.get('phase') in ('uploading', 'uploaded') for batch in batches)
        result['error'] = self._server_progress_error
        result['uploadInterrupted'] = any(batch.get('uploadError') for batch in self._server_batches.values())
        result['elapsed'] = int(time.monotonic() - self._server_progress_started)
        result['idleSeconds'] = int(time.monotonic() - self._server_last_activity)
        result['busy'] = self.busy
        return result

    @Property(bool, notify=stateChanged)
    def serverQueue(self) -> bool:
        return self._server_queue and self.serverQueueAvailable

    @Property(bool, notify=stateChanged)
    def serverQueueAvailable(self) -> bool:
        from thlib.environment import get_server_api
        return get_server_api() == 'stream'

    @Slot()
    def _server_api_changed(self) -> None:
        if not self.serverQueueAvailable:
            self._server_timer.stop()
        elif self._server_batches and not self._server_closed:
            self._server_timer.start(1000)
        self.stateChanged.emit()

    @Slot(bool)
    def set_server_queue(self, value: bool) -> None:
        if self.busy or (value and not self.serverQueueAvailable):
            return
        self._server_queue = bool(value)
        self._request_validations(list(self._operations))
        self.stateChanged.emit()

    @Property(bool, notify=stateChanged)
    def serverResumeAvailable(self) -> bool:
        payload = self._operations.get(self._selected_id) or {}
        reference = payload.get('_serverQueue') or {}
        batch = self._server_batches.get(reference.get('batch_id')) or {}
        return self.serverQueueAvailable and bool(batch.get('uploadError')) and not self._server_uploading

    def _server_pending(self) -> bool:
        return self.serverQueueAvailable and any(self._operations.get(row['operationId'], {}).get('_serverQueue')
                   and row.get('status') not in ('Completed','Failed','Cancelled')
                   for row in self.model._records)

    def _start_server_ids(self, operation_ids: list[str]) -> None:
        if self.busy or not self.serverQueueAvailable:
            return
        from thlib.environment import env_server
        from thlib.tactic_classes import split_search_key
        grouped = {}
        for operation_id in operation_ids:
            row = self._row_for_id(operation_id)
            if row < 0 or not self.model._records[row].get('canCommit'):
                continue
            payload = self.operation(operation_id)
            project = split_search_key(payload['searchKey'].removeprefix('skey://'))['project_code']
            grouped.setdefault(project, []).append(dict(operation_id=operation_id,payload=deepcopy(payload)))
        if not grouped:
            return
        self._server_progress = {}
        self._server_progress_started = time.monotonic()
        self._server_last_activity = self._server_progress_started
        batches = []
        for project, operations in grouped.items():
            batch_id = uuid.uuid4().hex
            batch = dict(batch_id=batch_id,project=project,operations=operations,
                         server=str(env_server.get_server()),user=str(env_server.get_user()),
                         submitted=False,uploadError='')
            self._server_batches[batch_id] = batch
            batches.append(batch)
            for operation in operations:
                operation_id = operation['operation_id']
                self._operations[operation_id]['_serverQueue'] = dict(batch_id=batch_id,project=project)
                self._set_record(operation_id,status='Queued',stage='uploading to server',canEdit=False,canCommit=False,error='')
        self._save()
        self._send_server_batches(batches)

    def _server_request(self, server, ticket, project, action, payload):
        from thlib.environment import env_server
        from thlib.server_checkin_queue import request
        if (not self.serverQueueAvailable or
                (server, ticket) != (str(env_server.get_server()), str(env_server.get_ticket()))):
            raise InterruptedError('The Stream check-in session changed')
        return request(server, ticket, project, action, payload)

    def _submit_server_batches(self, server, ticket, batches, cancel_event=None, progress_signal=None):
        from thlib.environment import env_server
        from thlib.server_checkin_queue import submit_batches
        if (not self.serverQueueAvailable or
                (server, ticket) != (str(env_server.get_server()), str(env_server.get_ticket()))):
            raise InterruptedError('The Stream check-in session changed')
        return submit_batches(server, ticket, batches, cancel_event=cancel_event, progress_signal=progress_signal)

    def _send_server_batches(self, batches: list[dict]) -> None:
        from thlib.environment import env_inst, env_server
        if self._server_closed or not self.serverQueueAvailable or not batches or any(batch['server'] != str(env_server.get_server()) or batch['user'] != str(env_server.get_user()) for batch in batches):
            return
        self._server_uploading = True
        self._server_cancel_event.clear()
        self._server_progress_error = ''
        self._server_progress_timer.start()
        for batch in batches:
            self._server_progress.setdefault(batch['batch_id'], {})['totalOperations'] = len(batch['operations'])
            self._server_progress[batch['batch_id']].update(phase='hooks', filename='')
            batch['uploadError'] = ''
        self.stateChanged.emit()
        hooks = getattr(self._executor,'_script_triggers',None)
        prepared = [operation for batch in batches for operation in batch['operations'] if not operation.get('before_hook_done')]

        def before_next(index=0):
            if self._server_closed:
                return
            if not self.serverQueueAvailable:
                self._server_submission_failed('The Stream check-in session changed')
                return
            if self._server_cancel_event.is_set():
                self._server_uploading = False
                self._cancel_server_batches()
                self.stateChanged.emit()
                return
            if index % 50 == 0:
                self._server_last_activity = time.monotonic()
                self.progressChanged.emit()
            if hooks is not None and index < len(prepared):
                def ready(success, error):
                    if self._server_closed:
                        return
                    if not success:
                        self._server_submission_failed(error or 'Before check-in hook failed')
                        return
                    prepared[index]['before_hook_done'] = True
                    self._save_timer.start()
                    QTimer.singleShot(0, lambda:before_next(index + 1))
                context = self._executor._trigger_context(prepared[index]['payload'])
                hooks.run_before('snapshot.save',context,ready)
                return
            for operation in prepared:
                operation['before_hook_done'] = True
            self._save()
            worker = env_inst.commit_pool.add_task(self._submit_server_batches,str(env_server.get_server()),str(env_server.get_ticket()),
                                                 deepcopy(batches),cancel_event=self._server_cancel_event)
            if worker is None:
                self._server_submission_failed('Check-in worker pool is unavailable')
                return
            self._server_worker = worker
            worker.result.connect(self._server_submitted,Qt.ConnectionType.QueuedConnection)
            worker.error.connect(self._server_submission_failed,Qt.ConnectionType.QueuedConnection)
            worker.connect_progress(self._server_chunk_progress)
            worker.start()
            self._server_timer.start(1)
            self.stateChanged.emit()
        before_next()

    @Slot(object)
    def _server_chunk_progress(self, value) -> None:
        if self._server_closed or not self.serverQueueAvailable:
            return
        _position, info = value
        batch_id = info.get('batch_id')
        if batch_id:
            self._server_progress.setdefault(batch_id, {}).update(info)
            self._server_last_activity = time.monotonic()
            self.progressChanged.emit()
        if not self._server_timer.isActive() and self._server_poll_worker is None:
            self._server_timer.start(1000)

    @Slot(object)
    def _server_submitted(self, result) -> None:
        if self._server_closed:
            return
        self._server_worker = None
        self._server_uploading = False
        self.progressChanged.emit()
        for value in result or []:
            batch = self._server_batches.get(value.get('batch_id'))
            if batch:
                batch['submitted'] = True
                batch['uploadError'] = ''
        self._save()
        self.stateChanged.emit()
        if not self.serverQueueAvailable:
            return
        if self._server_cancel_event.is_set():
            self._cancel_server_batches()
        else:
            self._server_timer.start(1)

    @Slot(object)
    def _server_submission_failed(self, error) -> None:
        if self._server_closed:
            return
        self._server_worker = None
        self._server_uploading = False
        message = self._executor._worker_error_text(error) if self._executor else str(error)
        self._server_progress_error = message
        self._flush_refreshes(force=True)
        self.progressChanged.emit()
        for batch in self._server_batches.values():
            if batch.get('submitted'):
                continue
            batch['uploadError'] = message
            for operation in batch['operations']:
                operation_id = operation['operation_id']
                row = self._row_for_id(operation_id)
                if row >= 0 and self.model._records[row]['status'] != 'Completed':
                    self._set_record(operation_id,status='Failed',stage='upload interrupted',error=message,canEdit=False,canCommit=False)
        self._save()
        self.stateChanged.emit()
        if not self.serverQueueAvailable:
            return
        if self._server_cancel_event.is_set():
            self._cancel_server_batches()
        else:
            self._server_timer.start(1000)

    @Slot()
    def _poll_server_queue(self) -> None:
        if self._server_closed or not self.serverQueueAvailable or self._server_poll_worker is not None or not self._server_batches:
            return
        from thlib.environment import env_inst, env_server
        batches = [dict(batch_id=batch['batch_id'],project=batch['project']) for batch in self._server_batches.values()
                   if batch['server'] == str(env_server.get_server()) and batch['user'] == str(env_server.get_user())]
        if not batches or not env_server.get_ticket():
            self._server_timer.start(3000)
            return
        worker = env_inst.server_pool.add_task(self._server_request,str(env_server.get_server()),str(env_server.get_ticket()),batches[0]['project'],
                                              'updates',dict(batches=batches,cursors=dict(self._server_cursors)))
        if worker is None:
            self._server_timer.start(3000)
            return
        self._server_poll_session = (str(env_server.get_server()),str(env_server.get_user()))
        self._server_poll_worker = worker
        worker.result.connect(self._server_updates,Qt.ConnectionType.QueuedConnection)
        worker.error.connect(self._server_updates_failed,Qt.ConnectionType.QueuedConnection)
        worker.start()

    @Slot(object)
    def _server_updates(self, result) -> None:
        if self._server_closed:
            return
        self._server_poll_worker = None
        if not self.serverQueueAvailable:
            return
        from thlib.environment import env_server
        if getattr(self,'_server_poll_session',None) not in (None,(str(env_server.get_server()),str(env_server.get_user()))):
            self._server_timer.start(3000)
            return
        if not isinstance(result,dict):
            self._server_timer.start(3000)
            return
        for row in self.model._records:
            payload = self._operations.get(row['operationId']) or {}
            reference = payload.get('_serverQueue') or {}
            if row.get('stage') == 'waiting for server' and reference.get('batch_id') in (result.get('checkinCursors') or {}):
                self._set_record(row['operationId'],stage='server ' + reference.get('state','pending'),error='')
        for event in result.get('checkins') or []:
            operation_id = event['operation_id']
            batch = self._server_batches.get(event['batch_id'])
            if batch:
                for operation in batch['operations']:
                    if operation['operation_id'] == operation_id:
                        operation['server_state'] = event['state']
                        break
            payload = self._operations.get(operation_id)
            if payload is None or (payload.get('_serverQueue') or {}).get('batch_id') != event['batch_id']:
                continue
            state = event['state']
            status = {'staging':'Queued','pending':'Queued','locked':'Running','complete':'Completed','error':'Failed','terminated':'Cancelled'}.get(state,'Queued')
            row = self._row_for_id(operation_id)
            was_complete = row >= 0 and self.model._records[row]['status'] == 'Completed'
            payload['_serverQueue']['state'] = state
            self._set_record(operation_id,status=status,stage='server ' + state,error=event.get('error',''),
                             progress=1.0 if state == 'complete' else 0.0,canCommit=state in ('error','terminated'),canEdit=False)
            if state == 'complete' and not was_complete:
                payload['_serverSnapshot'] = event['snapshot']
                payload['_serverSourceHashes'] = event.get('source_checksums') or {}
                self._remember_refresh(
                    operation_id, payload, event['snapshot'],
                    payload['_serverQueue']['project'],
                )
                hooks = getattr(self._executor,'_script_triggers',None)
                if hooks is not None:
                    hooks.run_after('snapshot.save',self._executor._trigger_context(payload))
                self.operationCompleted.emit(deepcopy(payload))
        self._server_cursors.update(result.get('checkinCursors') or {})
        for batch_id,batch in list(self._server_batches.items()):
            counts = Counter(operation.get('server_state', 'staging') for operation in batch['operations'])
            self._server_progress.setdefault(batch_id, {}).update(
                totalOperations=len(batch['operations']), completed=counts['complete'],
                failed=counts['error'], cancelled=counts['terminated'], running=counts['locked'])
            if not self._server_uploading and all(operation.get('server_state') in ('pending','locked','complete','error','terminated') for operation in batch['operations']):
                batch['submitted'] = True
                batch['uploadError'] = ''
            if batch.get('submitted') and not self._server_uploading:
                for operation in batch['operations']:
                    row = self._row_for_id(operation['operation_id'])
                    payload = self._operations.get(operation['operation_id']) or {}
                    if row >= 0 and self.model._records[row]['status'] == 'Completed':
                        if payload.get('mode') == 'move' and not payload.get('_serverMoveCleaned'):
                            self._finish_server_move(operation['operation_id'])
                        elif self._auto_clean:
                            self.remove_row(row)
                if all(self._row_for_id(operation['operation_id']) < 0 or self.model._records[self._row_for_id(operation['operation_id'])]['status'] in ('Completed','Failed','Cancelled') for operation in batch['operations']):
                    self._server_batches.pop(batch_id)
                    self._server_cursors.pop(batch_id,None)
        self._flush_refreshes()
        self._server_progress_error = ''
        if result.get('checkins'):
            self._server_last_activity = time.monotonic()
        self.progressChanged.emit()
        self._save()
        self.stateChanged.emit()
        if not self.busy:
            self._server_progress_timer.stop()
        if self._server_batches:
            self._server_timer.start(20 if result.get('checkinsHasMore') else 1000)
        self._close_finished_auto_clean_queue()

    @Slot(object)
    def _server_updates_failed(self, error, *, from_cancel=False) -> None:
        if self._server_closed:
            return
        if not from_cancel:
            self._server_poll_worker = None
        if not self.serverQueueAvailable:
            return
        # A failed status read says nothing about whether the server committed.
        self._server_progress_error = 'status unavailable'
        self._flush_refreshes(force=True)
        self.progressChanged.emit()
        message = self._executor._worker_error_text(error) if self._executor else str(error)
        for row in self.model._records:
            payload = self._operations.get(row['operationId']) or {}
            if payload.get('_serverQueue') and row['status'] in ('Queued','Running'):
                self._set_record(row['operationId'],stage='waiting for server',error=message)
        self.stateChanged.emit()
        self._server_timer.start(3000)

    def _cancel_server_batches(self) -> None:
        if not self.serverQueueAvailable:
            return
        from thlib.environment import env_inst, env_server
        for batch in self._server_batches.values():
            if batch['server'] != str(env_server.get_server()) or batch['user'] != str(env_server.get_user()):
                continue
            worker = env_inst.server_pool.add_task(self._server_request,batch['server'],str(env_server.get_ticket()),batch['project'],
                                                  'cancel',dict(batch_id=batch['batch_id']))
            if worker is not None:
                worker.result.connect(lambda result,b=batch:self._server_cancelled(b,result),Qt.ConnectionType.QueuedConnection)
                worker.error.connect(lambda error:self._server_updates_failed(error,from_cancel=True),Qt.ConnectionType.QueuedConnection)
                worker.start()

    def _server_cancelled(self, batch: dict, result: dict) -> None:
        if self._server_closed or not self.serverQueueAvailable:
            return
        batch['submitted'] = True
        batch['uploadError'] = ''
        for operation in batch['operations']:
            row = self._row_for_id(operation['operation_id'])
            state = (result.get('states') or {}).get(operation['operation_id'],'terminated')
            if row >= 0 and state == 'terminated':
                self._operations[operation['operation_id']]['_serverQueue']['state'] = state
                self._set_record(operation['operation_id'],status='Cancelled',stage='cancelled',error='',canCommit=True)
            elif row >= 0 and state == 'locked':
                self._set_record(operation['operation_id'],status='Running',stage='server locked',canCommit=False)
        self._save()
        self._server_timer.start(1)

    def _finish_server_move(self, operation_id: str) -> None:
        if not self.serverQueueAvailable:
            return
        if operation_id in self._server_cleanup_ids:
            return
        from thlib.environment import env_inst
        from thlib.server_checkin_queue import remove_committed_sources
        payload = self._operations[operation_id]
        worker = env_inst.commit_pool.add_task(remove_committed_sources,deepcopy(payload))
        if worker is None:
            return
        self._server_cleanup_ids.add(operation_id)
        self.stateChanged.emit()
        worker.result.connect(lambda _result:self._server_move_finished(operation_id),Qt.ConnectionType.QueuedConnection)
        worker.error.connect(lambda error:self._server_move_finished(operation_id,self._executor._worker_error_text(error)),Qt.ConnectionType.QueuedConnection)
        worker.start()

    def _server_move_finished(self, operation_id: str, error: str = '') -> None:
        self._server_cleanup_ids.discard(operation_id)
        payload = self._operations.get(operation_id)
        if payload:
            payload['_serverMoveCleaned'] = True
            self._set_record(operation_id,error=error)
            if self._auto_clean and not error:
                self.remove_row(self._row_for_id(operation_id))
        self._save()
        self.stateChanged.emit()
        if not self._server_closed:
            self._flush_refreshes()
            self._close_finished_auto_clean_queue()


    def _write_settings(self) -> None:
        env_write_config(
            self._settings,
            filename="ui_commit_queue",
            unique_id="ui_main",
            long_abs_path=True,
        )
