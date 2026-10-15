"""TACTIC snapshot discovery and portable update hand-off."""

from __future__ import annotations

import os
import shutil
import subprocess
import traceback
import uuid
from pathlib import Path

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot
from PySide6.QtWidgets import QApplication

from thlib import update_functions as releases
from thlib.environment import env_read_config, env_write_config
from thlib.ui.activity import activity_timestamp_labels
from thlib.ui.workspace_models.records import RecordListModel


class UpdateController(QObject):
    stateChanged = Signal()
    updateAvailable = Signal(str)

    def __init__(self, application, debug_log, parent=None):
        super().__init__(parent)
        self._application = application
        self._debug_log = debug_log
        self.model = RecordListModel((
            "version", "date", "changes", "misc", "archive", "selected", "kind",
        ))
        self._source = str((env_read_config(
            filename="ui_settings", unique_id="ui_updates", long_abs_path=True,
        ) or {}).get("searchKey") or "")
        self._busy = False
        self._progress = 0.0
        self._stage = ""
        self._error = ""
        version = releases.current_version()
        self._current_version = releases.version_text(version)
        self._changelog = releases.read_changelog()
        self._current_changes = releases.release_notes(self._changelog, version)
        self._request_id = ""
        self._worker = None
        self._snapshots = {}
        self._announced = ""
        self._poll_identity = None
        self._handle = None
        self._download_token = ""
        self._timer = QTimer(self)
        self._timer.setInterval(24 * 60 * 60 * 1000)
        self._timer.timeout.connect(self.refresh_remote)

    @Property(bool, notify=stateChanged)
    def busy(self): return self._busy

    @Property(float, notify=stateChanged)
    def progress(self): return self._progress

    @Property(str, notify=stateChanged)
    def stage(self): return self._stage

    @Property(str, notify=stateChanged)
    def error(self): return self._error

    @Property(str, notify=stateChanged)
    def currentVersion(self): return self._current_version

    @Property(str, constant=True)
    def changelog(self) -> str:
        return self._changelog

    @Property(str, constant=True)
    def currentChanges(self) -> str:
        return self._current_changes

    @Property(str, notify=stateChanged)
    def sourceSearchKey(self): return self._source

    @Property(bool, constant=True)
    def portable(self): return releases.portable_root() is not None

    @Property(bool, notify=stateChanged)
    def cancelable(self):
        return self._busy and self._stage in {
            "Checking TACTIC snapshots", "Downloading release ZIP",
        }

    @Property(bool, notify=stateChanged)
    def canInstall(self):
        return bool(releases.portable_root()) and not self._busy and any(
            record.get("selected") for record in self.model._records
        )

    def set_source(self, search_key: str) -> None:
        search_key = str(search_key or "").strip()
        if search_key == self._source:
            return
        self._source = search_key
        self._timer.stop()
        self._download_token = ""
        self._request_id = ""
        self._busy = False
        self._worker = None
        env_write_config(
            {"searchKey": search_key}, filename="ui_settings",
            unique_id="ui_updates", long_abs_path=True,
        )
        self._snapshots = {}
        self.model.replace([])
        self._announced = ""
        self.stateChanged.emit()
        self.sync_authentication()

    def _start(self, callback, *args, stage):
        if self._busy:
            return False
        from thlib.environment import env_inst
        if env_inst.local_pool.is_stopped:
            env_inst.local_pool.start()
        self._request_id = uuid.uuid4().hex
        self._busy = True
        self._progress = 0.0
        self._stage = stage
        self._error = ""
        self.stateChanged.emit()
        worker = env_inst.local_pool.add_task(callback, *args)
        worker.add_result_data(self._request_id)
        worker.result.connect(self._finished)
        worker.error.connect(self._failed)
        self._worker = worker
        worker.start()
        return True

    @Slot()
    def sync_authentication(self):
        from thlib.environment import env_server
        identity = (env_server.get_cur_srv_preset(), self._application.login_name)
        if (self._timer.isActive() and identity == self._poll_identity
                and env_server.get_ticket()
                and not self._application.authentication_required
                and self._application.server_state == "online"):
            return
        configured = str((env_read_config(
            filename="ui_settings", unique_id="ui_updates", long_abs_path=True,
        ) or {}).get("searchKey") or "")
        if configured != self._source:
            self._source = configured
            self._timer.stop()
            self._download_token = ""
            self._request_id = ""
            self._busy = False
            self._worker = None
            self._snapshots = {}
            self.model.replace([])
            self._announced = ""
            self.stateChanged.emit()
        if (not self._source or not env_server.get_ticket()
                or self._application.authentication_required
                or not self._application.login_name
                or self._application.server_state != "online"):
            self._timer.stop()
            self._poll_identity = None
            self._request_id = ""
            self._download_token = ""
            self._snapshots = {}
            self.model.replace([])
            self._busy = False
            self._worker = None
            self.stateChanged.emit()
            return
        if identity != self._poll_identity:
            self._timer.stop()
            self._poll_identity = identity
            self._announced = ""
        if self._timer.isActive():
            return
        self._timer.start()
        self.refresh_remote()

    @Slot()
    def load(self):
        if not self._source:
            self._show_releases([])
        self.refresh_remote()

    @Slot()
    def refresh_remote(self):
        from thlib.environment import env_server
        if (not self._source or not env_server.get_ticket()
                or self._application.authentication_required
                or not self._application.login_name
                or self._application.server_state != "online"):
            self._show_releases([])
            self._stage = "Configure an update sObject search key and sign in"
            self.stateChanged.emit()
            return
        self._start(self._query, self._source, stage="Checking TACTIC snapshots")

    @staticmethod
    def _query(search_key):
        from thlib import tactic_classes as tc
        return ({"kind": "refresh", "snapshots":
                 tc.get_application_update_snapshots(search_key) or []},)

    @Slot(int)
    def select(self, row):
        for index, record in enumerate(self.model._records):
            selected = index == row
            if bool(record.get("selected")) != selected:
                record["selected"] = selected
                model_index = self.model.index(index, 0)
                self.model.dataChanged.emit(model_index, model_index)
        self.stateChanged.emit()

    @Slot()
    def cancel(self):
        if not self.cancelable:
            return
        self._request_id = ""
        self._download_token = ""
        self._worker = None
        self._busy = False
        self._stage = "Cancelled"
        self._progress = 0.0
        self.stateChanged.emit()

    @Slot()
    def install_selected(self):
        if self._busy:
            return
        root = releases.portable_root()
        if root is None:
            self._error = "Automatic installation requires a portable build"
            self.stateChanged.emit()
            return
        record = next((row for row in self.model._records
                       if row.get("selected")), None)
        if record is None:
            return
        if record["kind"] == "backup":
            backup = Path(record["archive"])
            self._start(self._stage_backup, backup, root,
                        stage="Preparing previous version")
            return
        release = self._snapshots.get(record["archive"])
        if release is None:
            self._error = "Selected release is no longer available"
            self.stateChanged.emit()
            return
        from thlib import tactic_classes as tc
        snapshot, filename = release
        files = tc.Snapshot(dict(snapshot)).get_files_objects()
        file_object = next((item for item in files
                            if item.get_filename_with_ext() == filename), None)
        if file_object is None:
            self._error = "Release ZIP is missing from the snapshot"
            self.stateChanged.emit()
            return
        self._busy = True
        self._download_token = uuid.uuid4().hex
        token = self._download_token
        self._stage = "Downloading release ZIP"
        self._error = ""
        self.stateChanged.emit()
        try:
            self._handle = self._application.repository_sync.schedule_file_object(
                file_object, process="application-update", auto_start=False,
            )
            self._handle.downloaded.connect(
                lambda ready: self._downloaded(ready, record["version"], token)
            )
            self._handle.failed.connect(
                lambda failed: self._download_failed(failed, token)
            )
            self._handle.download()
        except (OSError, RuntimeError, TimeoutError, ValueError, KeyError) as error:
            self._download_token = ""
            self._busy = False
            self._error = str(error)
            self._debug_log.raise_error(
                error, stacktrace=traceback.format_exc(), group="update/download"
            )
            self.stateChanged.emit()

    def _downloaded(self, file_object, version, token):
        if token != self._download_token:
            return
        self._download_token = ""
        self._busy = False
        root = releases.portable_root()
        self._start(self._stage_zip, Path(file_object.get_full_abs_path()), root,
                    tuple(map(int, version.split("."))), stage="Validating release ZIP")

    def _download_failed(self, _file_object, token):
        if token != self._download_token:
            return
        self._download_token = ""
        self._busy = False
        self._error = "Release download failed; see Repository Sync"
        self.stateChanged.emit()

    @staticmethod
    def _stage_zip(archive, root, version):
        destination = root / "_updates" / f"stage-{uuid.uuid4().hex}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        releases.stage_archive(archive, destination, version)
        return ({"kind": "staged", "path": str(destination)},)

    @staticmethod
    def _stage_backup(backup, root):
        update_root = root / "_updates"
        if backup.parent.resolve() != (update_root / "backups").resolve():
            raise ValueError("Invalid rollback directory")
        destination = update_root / f"stage-{uuid.uuid4().hex}"
        shutil.copytree(backup, destination)
        return ({"kind": "staged", "path": str(destination)},)

    @Slot(int, int, int, int, str, str, result=bool)
    def create_update(self, major, minor, build, revision, changes, misc):
        if not self._application.can_manage_tools:
            return False
        version = (major, minor, build, revision)
        if min(version) < 0:
            self._error = "Version values must be non-negative"
            self.stateChanged.emit()
            return False
        return self._start(self._create_archive, version, str(changes or ""),
                           str(misc or ""),
                           stage="Creating update archive")

    @Slot()
    def open_generator(self):
        if self._application.can_manage_tools:
            self._application.open_window("create_update")

    @staticmethod
    def _create_archive(version, changes, misc):
        app_dir = Path(__file__).resolve().parents[2]
        archive = app_dir / "updates" / (releases.version_text(version).replace(".", "_") + ".zip")
        releases.create_update_archive(app_dir, archive, version, changes, misc)
        return ({"kind": "created", "path": str(archive)},)

    @Slot(object)
    def _finished(self, payload):
        result, request_id = payload
        if request_id != self._request_id:
            if result.get("kind") == "staged":
                root = releases.portable_root()
                staged = Path(result["path"])
                if (root and staged.name.startswith("stage-")
                        and staged.parent.resolve() == (root / "_updates").resolve()):
                    from thlib.environment import env_inst
                    if not env_inst.local_pool.is_stopped:
                        env_inst.local_pool.add_task(shutil.rmtree, staged).start()
            return
        self._busy = False
        self._progress = 1.0
        kind = result.get("kind")
        if kind == "refresh":
            self._show_releases(result["snapshots"])
            self._stage = "Update history loaded"
        elif kind == "staged":
            self._launch_installer(Path(result["path"]))
            return
        elif kind == "created":
            self._stage = "Archive created: " + result["path"]
        self.stateChanged.emit()

    def _show_releases(self, snapshots):
        selected = next((row["archive"] for row in self.model._records
                         if row.get("selected")), "")
        self._snapshots = {}
        records = []
        for snapshot in snapshots:
            for file_data in snapshot.get("__files__", []):
                filename = str(file_data.get("file_name") or "")
                version = releases.version_from_filename(filename)
                if version is None:
                    continue
                release_id = str(snapshot.get("code") or "") + ":" + str(file_data.get("code") or filename)
                self._snapshots[release_id] = (snapshot, filename)
                raw_date = str(snapshot.get("timestamp") or "")
                records.append({
                    "version": releases.version_text(version),
                    "date": activity_timestamp_labels(raw_date)[0],
                    "changes": str(snapshot.get("description") or ""),
                    "misc": "", "archive": release_id,
                    "selected": release_id == selected, "kind": "release",
                    "_version": version, "_date": raw_date,
                })
        records.sort(key=lambda row: (row["_version"], row["_date"]), reverse=True)
        latest = next((row for row in records
                       if row["_version"] > releases.current_version()), None)
        if latest and latest["version"] != self._announced:
            self._announced = latest["version"]
            for row in records:
                row["selected"] = row is latest
            if releases.portable_root():
                self.updateAvailable.emit(latest["version"])
        root = releases.portable_root()
        if root:
            for backup in (root / "_updates" / "backups").glob("app-*"):
                try:
                    version = releases.current_version(backup)
                except (OSError, ValueError, KeyError):
                    continue
                records.append({
                    "version": releases.version_text(version), "date": "",
                    "changes": "Previous installation", "misc": "",
                    "archive": str(backup), "selected": str(backup) == selected,
                    "kind": "backup", "_version": version,
                })
        for row in records:
            row.pop("_version", None)
            row.pop("_date", None)
        self.model.replace(records)

    def _launch_installer(self, staged):
        root = releases.portable_root()
        if root is None:
            self._error = "Portable installation is unavailable"
            self.stateChanged.emit()
            return
        helper = root / "_updates" / "update_installer.pyw"
        try:
            shutil.copy2(Path(__file__).resolve().parents[1] / "update_installer.py", helper)
            subprocess.Popen(
                [str(root / "_runtime" / "pythonw.exe"), str(helper),
                 str(root), str(staged), str(os.getpid())], cwd=root,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except OSError as error:
            self._error = str(error)
            self.stateChanged.emit()
            return
        self._stage = "Closing TACTIC-Handler for installation"
        self.stateChanged.emit()
        from thlib.environment import env_inst
        from shiboken6 import isValid
        window = env_inst.ui_main
        try:
            if window is not None and isValid(window):
                self._application.save_window_state(
                    window.x(), window.y(), window.width(), window.height(),
                    int(window.visibility()),
                )
        finally:
            QApplication.instance().quit()

    @Slot(object)
    def _failed(self, payload):
        details = payload[0] if isinstance(payload, tuple) else payload
        worker = payload[1] if isinstance(payload, tuple) and len(payload) > 1 else None
        if worker is not None and worker is not self._worker:
            return
        error = details.get("exception") if isinstance(details, dict) else details
        stack = details.get("stacktrace") if isinstance(details, dict) else traceback.format_exc()
        background_check = self._stage == "Checking TACTIC snapshots"
        self._busy = False
        self._progress = 0.0
        self._stage = "Failed"
        self._error = str(error)
        if background_check:
            if not self.model._records:
                self._show_releases([])
            self._debug_log.log(
                "WARNING", str(error), group="update/check",
                stacktrace=str(stack),
            )
        else:
            self._debug_log.raise_error(
                error, stacktrace=str(stack), group="update",
            )
        self.stateChanged.emit()
