from __future__ import annotations

import traceback
import uuid
from datetime import datetime

from PySide6.QtCore import QObject, Property, Signal, Slot

from thlib.ui.workspace_models.records import RecordListModel


class UpdateController(QObject):
    stateChanged = Signal()

    def __init__(self, debug_log, parent=None):
        super().__init__(parent)
        self._debug_log = debug_log
        self.model = RecordListModel((
            "version", "date", "changes", "misc", "archive", "selected",
        ))
        self._busy = False
        self._progress = 0.0
        self._stage = ""
        self._error = ""
        self._current_version = ""
        self._request_id = ""
        self._worker = None

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
    def load(self):
        self._start(self._load_updates, stage="Reading update history")

    @staticmethod
    def _load_updates():
        import thlib.update_functions as uf
        current = uf.get_current_version()
        records = []
        for update in uf.get_info_from_updates_folder() or []:
            version = dict(update.get("version") or {})
            records.append({
                "version": uf.get_version(string=True, **version).replace("_", "."),
                "date": str(update.get("date") or ""),
                "changes": str(update.get("changes") or ""),
                "misc": str(update.get("misc") or ""),
                "archive": str(update.get("update_archive") or ""),
                "selected": False,
                "_sort": uf.get_version(sort_sum=True, **version),
            })
        records.sort(key=lambda row: row["_sort"], reverse=True)
        for record in records:
            record.pop("_sort", None)
        return ({
            "kind": "load",
            "current": uf.get_version(string=True, **current).replace("_", "."),
            "records": records,
        },)

    @Slot()
    def refresh_remote(self):
        self._start(self._refresh_remote, stage="Checking update source")

    @staticmethod
    def _refresh_remote():
        import thlib.update_functions as uf
        uf.get_updates_from_server()
        result = UpdateController._load_updates()[0]
        result["kind"] = "refresh"
        return (result,)

    @Slot()
    def cancel(self):
        if not self._busy:
            return
        self._request_id = ""
        self._worker = None
        self._busy = False
        self._stage = "Cancelled"
        self._progress = 0.0
        self.stateChanged.emit()

    @Slot(int)
    def select(self, row):
        for index, record in enumerate(self.model._records):
            selected = index == row
            if bool(record.get("selected")) != selected:
                record["selected"] = selected
                model_index = self.model.index(index, 0)
                self.model.dataChanged.emit(model_index, model_index)

    @Slot()
    def restart_to_update(self):
        if self._busy:
            return
        from thlib.environment import env_inst
        import thlib.global_functions as gf
        main = env_inst.ui_main
        if main and hasattr(main, "restart_for_update_ui_main"):
            main.restart_for_update_ui_main()
        else:
            gf.restart_app()

    @Slot(int, int, int, int, str, str, result=bool)
    def create_update(self, major, minor, build, revision, changes, misc):
        if min(major, minor, build, revision) < 0:
            self._error = "Version values must be non-negative"
            self.stateChanged.emit()
            return False
        data = {
            "version": {
                "major": major, "minor": minor,
                "build": build, "revision": revision,
            },
            "date": datetime.now().isoformat(sep=" ", timespec="minutes"),
            "changes": str(changes or ""),
            "misc": str(misc or ""),
        }
        return self._start(
            self._create_update, data, stage="Creating update archive"
        )

    @staticmethod
    def _create_update(data):
        import thlib.update_functions as uf
        from thlib.environment import env_mode
        version = data["version"]
        version_key = uf.get_version(string=True, **version)
        data = dict(data)
        data["remove_list"] = []
        data["update_archive"] = f"{version_key}.zip"
        root = env_mode.get_current_path()
        uf.save_json_to_path(f"{root}/updates/{version_key}.json", data)
        uf.create_updates_list()
        uf.save_current_version(version)
        uf.create_update_archive(f"{root}/updates/{version_key}.zip")
        return ({"kind": "created"},)

    @Slot(object)
    def _finished(self, payload):
        result, request_id = payload
        if request_id != self._request_id:
            return
        self._busy = False
        self._progress = 1.0
        kind = result.get("kind")
        if kind in {"load", "refresh"}:
            self._current_version = result["current"]
            self.model.replace(result["records"])
            self._stage = "Update history loaded"
        elif kind == "created":
            self._stage = "Update archive created"
            self.load()
            return
        self.stateChanged.emit()

    @Slot(object)
    def _failed(self, payload):
        details = payload[0] if isinstance(payload, tuple) else payload
        worker = payload[1] if isinstance(payload, tuple) and len(payload) > 1 \
            else None
        if worker is not None and worker is not self._worker:
            return
        error = details.get("exception") if isinstance(details, dict) else details
        stack = details.get("stacktrace") if isinstance(details, dict) \
            else traceback.format_exc()
        self._busy = False
        self._progress = 0.0
        self._stage = "Failed"
        self._error = str(error)
        self._debug_log.raise_error(
            error, stacktrace=str(stack), group="update"
        )
        self.stateChanged.emit()
