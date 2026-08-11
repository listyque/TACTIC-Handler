from __future__ import annotations

from pathlib import Path
import re
import threading
import uuid

from PySide6.QtCore import QObject, Property, QTimer, QUrl, Qt, Signal, Slot

from .workspace_models.records import RecordListModel


class AttachmentUploadController(QObject):
    stateChanged = Signal()
    uploaded = Signal(object)
    failed = Signal(str, str)

    def __init__(self, application, parent=None) -> None:
        super().__init__(parent or application)
        self._application = application
        self.model = RecordListModel((
            "token", "title", "path", "size", "fileType", "previewUrl",
            "status", "progress", "error", "snapshotKey", "uploadTarget",
        ))
        self._busy = False
        self._progress = 0.0
        self._error = ""
        self._worker = None
        self._cancel = threading.Event()

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(float, notify=stateChanged)
    def progress(self) -> float:
        return self._progress

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error

    @Slot()
    def dismiss_error(self) -> None:
        if self._error:
            self._error = ""
            self.stateChanged.emit()

    @Property(int, notify=stateChanged)
    def count(self) -> int:
        return len(self.model._records)

    @staticmethod
    def _pretty_size(value: int) -> str:
        size = float(value or 0)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024
        return ""

    @staticmethod
    def _file_type(path: Path) -> str:
        try:
            import thlib.global_functions as gf

            return str(gf.file_format(path.suffix.lstrip("."))[3] or "file")
        except (AttributeError, IndexError, TypeError):
            return "file"

    @Slot("QVariantList")
    def add_files(self, values: list) -> None:
        if self._busy:
            return
        records = list(self.model._records)
        known = {str(record.get("path") or "").casefold() for record in records}
        errors = []
        for value in values or []:
            url = value if isinstance(value, QUrl) else QUrl(str(value))
            path = Path(url.toLocalFile() if url.isLocalFile() else str(value))
            try:
                path = path.resolve(strict=True)
                if not path.is_file():
                    raise ValueError("Directories are not supported")
                stat = path.stat()
            except (OSError, ValueError) as error:
                errors.append(f"{path.name or path}: {error}")
                continue
            key = str(path).casefold()
            if key in known:
                continue
            file_type = self._file_type(path)
            records.append({
                "token": uuid.uuid4().hex,
                "title": path.name,
                "path": str(path),
                "size": self._pretty_size(stat.st_size),
                "fileType": file_type,
                "previewUrl": (
                    QUrl.fromLocalFile(str(path)).toString()
                    if file_type == "preview" else ""
                ),
                "status": "ready",
                "progress": 0.0,
                "error": "",
                "snapshotKey": "",
                "uploadTarget": "",
            })
            known.add(key)
        self.model.replace(records)
        self._error = "; ".join(errors)
        self.stateChanged.emit()

    @Slot(result=bool)
    def add_clipboard_image(self) -> bool:
        if self._busy:
            return False
        from PySide6.QtGui import QGuiApplication
        from thlib.environment import env_tactic
        import thlib.tactic_classes as tc

        image = QGuiApplication.clipboard().image()
        if image.isNull():
            self._error = "The clipboard does not contain an image"
            self.stateChanged.emit()
            return False
        repository_path = str(env_tactic.get_current_repo("path") or "")
        if not repository_path:
            self._error = "No active repository is configured"
            self.stateChanged.emit()
            return False
        target = Path(repository_path) / "temp" / (
            "attachment_clipboard_{0}.png".format(uuid.uuid4().hex)
        )
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            path = tc.generate_image(image, str(target), scaled=False)
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            self._error = str(error)
            self.stateChanged.emit()
            return False
        self.add_files([QUrl.fromLocalFile(str(path))])
        return True

    @Slot(result=bool)
    def clipboard_has_image(self) -> bool:
        from PySide6.QtGui import QGuiApplication
        return QGuiApplication.clipboard().mimeData().hasImage()

    @Slot(result=bool)
    def clipboard_has_text(self) -> bool:
        from PySide6.QtGui import QGuiApplication
        return QGuiApplication.clipboard().mimeData().hasText()

    @Slot(int)
    def remove(self, row: int) -> None:
        if not self._busy:
            self.model.remove(row)
            self.stateChanged.emit()

    @Slot()
    def clear(self) -> None:
        if not self._busy:
            self.model.clear()
            self._progress = 0.0
            self._error = ""
            self.stateChanged.emit()

    @staticmethod
    def _checkin_mode() -> str:
        try:
            import thlib.global_functions as gf
            from thlib.environment import cfg_controls

            index = gf.get_value_from_config(
                cfg_controls.get_checkin() or {}, "checkinMethodComboBox"
            )
            return {
                0: "preallocate", 1: "inplace", 2: "copy",
                3: "move", 4: "upload",
            }.get(int(index), "upload")
        except (AttributeError, TypeError, ValueError):
            return "upload"

    @staticmethod
    def _target_payload(
            search_key: str, context_root: str, description: str,
            record: dict) -> dict:
        path = Path(record["path"])
        extension = path.suffix.lstrip(".").lower()
        file_type = str(record.get("fileType") or "file")
        values = {
            "t": [file_type], "s": [""], "e": [extension],
            "p": [""], "m": None,
        }
        if file_type == "preview":
            values["t"].extend(("web", "icon"))
            values["s"].extend(("", ""))
            values["e"].extend(("jpg", "png"))
            values["p"].extend(("", ""))
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", path.stem).strip("_")
        return {
            "searchKey": search_key,
            "context": "{0}/{1}".format(
                context_root.strip("/"), safe_name or "file"
            ),
            "description": description,
            "version": None,
            "isRevision": False,
            "updateVersionless": False,
            "keepFileName": False,
            "generatePreviews": file_type == "preview",
            "mode": AttachmentUploadController._checkin_mode(),
            "sequencePadding": 3,
            "filesDict": [(path.stem, values)],
            "files": [{
                "path": str(path),
                "type": file_type,
                "extension": extension,
            }],
        }

    @staticmethod
    def _payload(conversation_code: str, record: dict, _request_id: str) -> dict:
        return AttachmentUploadController._target_payload(
            "sthpw/message?code={0}".format(conversation_code),
            "attachment/chat",
            "Chat attachment",
            record,
        )

    @Slot(str, result=bool)
    def begin(self, conversation_code: str) -> bool:
        conversation_code = str(conversation_code or "")
        return self.begin_target(
            "sthpw/message?code={0}".format(conversation_code),
            "attachment/chat",
            "Chat attachment",
        )

    @Slot(str, str, str, result=bool)
    def begin_target(
            self, search_key: str, context_root: str,
            description: str = "Attachment") -> bool:
        search_key = str(search_key or "").strip()
        context_root = str(context_root or "").strip("/")
        if self._busy or not search_key or not context_root or not self.model._records:
            return False
        from thlib.environment import env_inst, env_tactic

        repository = env_tactic.get_current_repo() or {}
        values = repository.get("value") or []
        if len(values) < 4 or not values[0]:
            self._error = "No active repository is configured"
            self.stateChanged.emit()
            return False
        if env_inst.commit_pool.is_stopped:
            env_inst.commit_pool.start()
        target = "{0}\n{1}".format(search_key, context_root)
        records = []
        pending = []
        uploaded = {}
        for source in self.model._records:
            record = dict(source)
            token = str(record.get("token") or "")
            snapshot_key = str(record.get("snapshotKey") or "")
            if snapshot_key and record.get("uploadTarget") == target:
                record.update(status="uploaded", progress=1.0, error="")
                uploaded[token] = snapshot_key
            else:
                record.update(
                    status="queued", progress=0.0, error="",
                    snapshotKey="", uploadTarget="",
                )
                pending.append(dict(record))
            records.append(record)
        self._cancel.clear()
        self._busy = True
        self._progress = 0.0
        self._error = ""
        self.model.replace(records)
        self.stateChanged.emit()
        if not pending:
            QTimer.singleShot(0, lambda: self._ready({
                "snapshots": dict(uploaded), "target": target,
            }))
            return True
        worker = env_inst.commit_pool.add_task(
            self._upload_all,
            search_key,
            context_root,
            str(description or "Attachment"),
            pending,
            repository,
            target,
            uploaded,
        )
        if worker is None:
            self._busy = False
            self._error = "Check-in worker pool is unavailable"
            self.stateChanged.emit()
            return False
        self._worker = worker
        worker.result.connect(self._ready, Qt.ConnectionType.QueuedConnection)
        worker.error.connect(self._failed, Qt.ConnectionType.QueuedConnection)
        worker.connect_progress(self._progressed)
        worker.start()
        return True

    def _upload_all(
        self, search_key, context_root, description, records,
        repository, target, uploaded,
        progress_signal=None,
    ):
        from .checkin_operation import execute_checkin_payload

        snapshots = dict(uploaded)
        total = len(records)
        for index, record in enumerate(records):
            if self._cancel.is_set():
                raise InterruptedError("Attachment upload cancelled")
            payload = self._target_payload(
                search_key, context_root, description, record,
            )
            collision_retries = 0
            while True:
                try:
                    result = execute_checkin_payload(
                        payload, repository, progress_signal=progress_signal,
                        cancel_event=self._cancel,
                    )
                    break
                except Exception as error:
                    match = re.search(
                        r"_v(\d+)(?=\.[^./\\]+(?:\]|$))", str(error), re.I
                    )
                    if (
                        not match
                        or "already exists" not in str(error).casefold()
                        or collision_retries >= 3
                    ):
                        raise
                    payload["version"] = int(match.group(1)) + 1
                    collision_retries += 1
            token = str(record.get("token") or "")
            snapshots[token] = result["__search_key__"]
            if progress_signal:
                progress_signal.emit({
                    "attachmentToken": token,
                    "snapshotKey": snapshots[token],
                    "uploadTarget": target,
                })
                progress_signal.emit((
                    index,
                    {"status_text": record["title"], "total_count": total},
                ))
        return {"snapshots": snapshots, "target": target}

    @Slot(object)
    def _progressed(self, value) -> None:
        if isinstance(value, dict) and value.get("attachmentToken"):
            token = str(value["attachmentToken"])
            for row, record in enumerate(self.model._records):
                if record.get("token") != token:
                    continue
                self.model.set_value(row, "snapshotKey", value["snapshotKey"])
                self.model.set_value(row, "uploadTarget", value["uploadTarget"])
                self.model.set_value(row, "status", "uploaded")
                self.model.set_value(row, "progress", 1.0)
                break
            return
        try:
            current, info = value
            total = max(1, int(info.get("total_count") or 1))
            self._progress = min(1.0, max(0.0, (int(current) + 1) / total))
        except (AttributeError, TypeError, ValueError):
            return
        self.stateChanged.emit()

    @Slot(object)
    def _ready(self, result) -> None:
        value = result[0] if isinstance(result, tuple) and len(result) == 1 else result
        target = str(value.get("target") or "") if isinstance(value, dict) else ""
        snapshot_value = value.get("snapshots") if target else value
        snapshots = dict(snapshot_value or {}) if isinstance(snapshot_value, dict) else {
            str(record.get("token") or ""): snapshot
            for record, snapshot in zip(self.model._records, snapshot_value or [])
        }
        self._worker = None
        self._busy = False
        self._progress = 1.0
        self.model.replace([
            dict(
                record,
                status="uploaded" if snapshots.get(record.get("token")) else "failed",
                progress=1.0 if snapshots.get(record.get("token")) else 0.0,
                snapshotKey=snapshots.get(record.get("token"), ""),
                uploadTarget=(
                    target if snapshots.get(record.get("token"))
                    else record.get("uploadTarget", "")
                ),
            )
            for record in self.model._records
        ])
        self.stateChanged.emit()
        self.uploaded.emit([
            snapshots.get(record.get("token"))
            for record in self.model._records
            if snapshots.get(record.get("token"))
        ])

    @Slot(object)
    def _failed(self, error) -> None:
        payload = error[0] if isinstance(error, tuple) and error else error
        stacktrace = ""
        if isinstance(payload, dict):
            stacktrace = str(payload.get("stacktrace") or "")
            payload = payload.get("exception") or payload.get("message") or payload
        cancelled = isinstance(payload, InterruptedError)
        self._worker = None
        self._busy = False
        self._error = str(
            "Attachment upload cancelled" if cancelled
            else payload or "Attachment upload failed"
        )
        self.model.replace([
            dict(
                record,
                status=(
                    "uploaded" if record.get("snapshotKey")
                    else "cancelled" if cancelled else "failed"
                ),
                error="" if record.get("snapshotKey") else self._error,
            )
            for record in self.model._records
        ])
        self.stateChanged.emit()
        if not cancelled:
            self.failed.emit(self._error, stacktrace)

    @Slot()
    def cancel(self) -> None:
        if self._busy:
            self._cancel.set()

    @Slot()
    def shutdown(self) -> None:
        self._cancel.set()


ChatAttachmentController = AttachmentUploadController
