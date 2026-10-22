"""A table snapshot session using the existing native file-transfer queue."""

from copy import deepcopy

from PySide6.QtCore import QObject, Property, Signal, Slot, Qt
from thlib.ui.workspace_models.records import RecordListModel


class SnapshotCheckoutController(QObject):
    changed = Signal()

    def __init__(self, application, parent=None):
        super().__init__(parent)
        self._application = application
        self._queue = application.repository_sync
        self._queue.task_updated.connect(self._task_updated)
        self._queue.task_finished.connect(self._task_finished)
        self._queue.task_failed.connect(self._task_failed)
        self._generation = 0
        self._workers = set()
        self._open = False
        self._files = {}
        self._members = {}
        self._records = []
        self._selected = ""
        self._task_id = ""
        self._task_ids = []
        self._completed_tasks = set()
        self._snapshot = {}
        self._state = self._empty_state()
        self.files = RecordListModel(("token", "title", "fileType", "bytes", "selected", "enabled"))
        self.files.setParent(self)

    @staticmethod
    def _empty_state() -> dict:
        return dict(
            loading=False, ready=False, busy=False, error="", message="", conflict=False, progress=0
        )

    @Property(QObject, constant=True)
    def fileModel(self) -> QObject:
        return self.files

    @Property(bool, notify=changed)
    def isOpen(self) -> bool:
        return self._open

    @Property(bool, notify=changed)
    def busy(self) -> bool:
        return self._state["busy"]

    @Property("QVariantMap", notify=changed)
    def model(self) -> dict:
        return dict(
            self._state,
            count=self.files.rowCount(),
            context=self._snapshot.get("context") or "",
            title=self._snapshot.get("code") or "",
            version=self._snapshot.get("version"),
            error=self.tr(self._state["error"]),
            message=self.tr(self._state["message"]),
        )

    def open(self, key: str, project: str) -> None:
        from thlib import tactic_classes as tc
        from .requests import read_snapshot_files

        if self._open:
            self._state["error"] = "Close the current checkout before selecting another snapshot"
            self.changed.emit()
            return
        server = tc.server_start(project=project)
        self._generation += 1
        self._open = True
        self._state = dict(self._empty_state(), loading=True)
        self._application.window_model.show_window("snapshot_checkout")

        def prepare():
            snapshot = tc.execute_procedure_serverside(
                read_snapshot_files, dict(search_key=key), project=project, server=server
            )
            snap = tc.Snapshot(deepcopy(snapshot))
            objects = snap.get_files_objects()
            by_code = {str(item.get("code") or ""): item for item in snapshot.get("__files__") or []}
            rows = []
            for index, file in enumerate(objects):
                token = str(file.get_code() or index)
                raw = by_code.get(token) or {}
                member_rows = raw.get("__member_files__") or []
                members = (
                    [
                        tc.File(
                            dict(
                                raw,
                                file_name=member["file_name"],
                                st_size=member.get("st_size") or 0,
                                metadata={},
                            ),
                            snapshot=snap,
                        )
                        for member in member_rows
                    ]
                    if member_rows
                    else [file]
                )
                rows.append(
                    dict(
                        token=token,
                        title=file.get_filename_with_ext(),
                        fileType=file.get_type() or "",
                        bytes=file.get_file_size() or 0,
                        file=file,
                        members=members,
                    )
                )
            # Use browser string ordering, including filenames outside the BMP.
            rows.sort(
                key=lambda row: (
                    row["fileType"] != "main",
                    *(
                        row[field].encode("utf-16-be", "surrogatepass")
                        for field in ("title", "fileType", "token")
                    ),
                )
            )
            return snapshot, rows

        def loaded(result):
            self._snapshot, records = result
            self._files = {row["token"]: row.pop("file") for row in records}
            self._members = {row["token"]: row.pop("members") for row in records}
            self._selected = records[0]["token"] if records else ""
            self._records = records
            self._state.update(loading=False, ready=True)
            self._rebuild()

        self._run(prepare, loaded)

    def _rebuild(self):
        self.files.replace(
            [
                dict(
                    row,
                    selected=row["token"] == self._selected,
                    enabled=not self.busy and not self._state["conflict"],
                )
                for row in self._records
            ]
        )
        self.changed.emit()

    @Slot("QVariantMap", "QVariant")
    def activate(self, action: dict, value=None) -> None:
        kind = action.get("type")
        if kind == "close":
            self.request_close()
            return
        if kind == "cancelTransfer":
            if self._task_ids:
                for tid in tuple(self._task_ids):
                    if tid not in self._completed_tasks:
                        self._queue.cancel_task(tid)
            elif self._task_id:
                self._queue.cancel_task(self._task_id)
            elif self.busy:
                self._generation += 1
                for worker in tuple(self._workers):
                    worker.cancel()
                self._state.update(busy=False, message="Download cancelled")
                self._rebuild()
            return
        if self.busy or not self._state["ready"]:
            return
        if self._state["conflict"]:
            if kind == "accept":
                self._state["conflict"] = False
                self._download("overwrite")
            elif kind == "reject":
                self._state["conflict"] = False
                self._rebuild()
            return
        if kind == "select" and action.get("token") in self._files:
            self._selected = action["token"]
            self._state.update(error="", message="", progress=0)
            self._rebuild()
        elif kind == "checkout":
            file = self._files.get(self._selected)
            if file is None:
                return
            members = self._members.get(self._selected) or [file]
            if len(members) == 1:
                members = [file]
            self._state.update(busy=True, error="", message="", progress=0)
            self._rebuild()

            def checked(conflict):
                self._state["busy"] = False
                if conflict:
                    self._state["conflict"] = True
                    self._rebuild()
                else:
                    self._download("cancel")

            self._run(
                lambda: any(member.is_exists() and not member.is_local_current() for member in members),
                checked,
            )

    def _download(self, policy):
        file = self._files.get(self._selected)
        if file is None:
            return
        members = self._members.get(self._selected) or [file]
        if len(members) == 1:
            members = [file]
        try:
            handles = []
            for member in members:
                handle = self._queue.schedule_file_object(
                    member, process="checkout", auto_start=False, overwrite_policy=policy
                )
                if handle.is_download_in_progress():
                    raise ValueError("This file already has an active transfer")
                handles.append(handle)
            self._task_ids = [handle.task_id for handle in handles]
            self._completed_tasks = set()
            self._task_id = self._task_ids[0]
            self._state.update(busy=True, error="", message="", progress=0)
            self._rebuild()
            for handle in handles:
                handle.download()
        except (OSError, ValueError, RuntimeError) as error:
            self._state.update(busy=False, error=str(error))
            self._rebuild()

    @Slot(str)
    @Slot(str, str)
    def _task_updated(self, task_id, *_args):
        if task_id not in self._task_ids:
            return
        total = max(1, len(self._task_ids))
        value = sum(
            1.0 if tid in self._completed_tasks else float(self._queue.model.record(tid).get("progressValue") or 0)
            for tid in self._task_ids
        )
        self._state["progress"] = value / total
        self.changed.emit()

    @Slot(str)
    def _task_finished(self, task_id):
        if task_id not in self._task_ids:
            return
        self._completed_tasks.add(task_id)
        if len(self._completed_tasks) < len(self._task_ids):
            self._task_updated(task_id)
            return
        self._task_id = ""
        self._task_ids = []
        self._completed_tasks.clear()
        self._state.update(busy=False, progress=1, message="Check out completed")
        self._application.refresh_snapshot_browser()
        self._rebuild()

    @Slot(str)
    def _task_failed(self, task_id):
        if task_id not in self._task_ids:
            return
        record = self._queue.model.record(task_id)
        active = [tid for tid in self._task_ids if tid != task_id and tid not in self._completed_tasks]
        self._task_id = ""
        self._task_ids = []
        self._completed_tasks.clear()
        for tid in active:
            self._queue.cancel_task(tid)
        cancelled = record.get("status") == "cancelled"
        self._state.update(
            busy=False,
            error="" if cancelled else str(record.get("error") or "Download failed"),
            message="Download cancelled" if cancelled else "",
        )
        self._rebuild()

    def _run(self, operation, accept):
        from thlib.environment import env_inst

        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            self._state.update(loading=False, busy=False, error="Server worker is unavailable")
            self._rebuild()
            return
        generation = self._generation
        self._workers.add(worker)

        def loaded(result):
            if generation != self._generation:
                return
            try:
                accept(result)
            except (KeyError, TypeError, ValueError, OSError) as error:
                self._state.update(loading=False, busy=False, error=str(error))
                self._rebuild()

        def failed(payload):
            if generation != self._generation:
                return
            error = payload[0].get("exception") or "Snapshot is no longer available"
            self._state.update(loading=False, busy=False, error=str(error))
            if self._application.debug_log:
                self._application.debug_log.raise_error(
                    error, stacktrace=payload[0].get("stacktrace", ""), group="table/checkout"
                )
            self._rebuild()

        worker.result.connect(loaded, Qt.QueuedConnection)
        worker.error.connect(failed, Qt.QueuedConnection)
        worker.settled.connect(lambda _worker: self._workers.discard(worker), Qt.QueuedConnection)
        worker.start()
        self.changed.emit()

    @Slot()
    def request_close(self) -> None:
        self.shutdown()

    @Slot()
    def shutdown(self) -> None:
        self._generation += 1
        task_ids = [tid for tid in self._task_ids if tid not in self._completed_tasks]
        task_id, self._task_id = self._task_id, ""
        self._task_ids = []
        self._completed_tasks.clear()
        for tid in task_ids or ([task_id] if task_id else []):
            self._queue.cancel_task(tid)
        for worker in tuple(self._workers):
            worker.cancel()
        self._open = False
        self._files = {}
        self._members = {}
        self._selected = ""
        self._snapshot = {}
        self._records = []
        self._state = self._empty_state()
        self.files.clear()
        self._application.window_model.close_window("snapshot_checkout")
        self.changed.emit()
