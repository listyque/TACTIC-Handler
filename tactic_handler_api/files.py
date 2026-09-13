"""Repository operations using the same native downloader as the desktop UI."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import uuid

from .operations import report_progress


class _Signal:
    def __init__(self, callback):
        self._callback = callback

    def emit(self, *args):
        self._callback(*args)


class FilesAPI:
    def __init__(self, api):
        self._api = api

    def match(self, paths, *, templates=None):
        self._api._check()
        if isinstance(paths, (str, bytes)):
            raise TypeError("paths must be a collection, not a single string")
        groups = self._api._file_module.MatchTemplate(
            list(templates or ["$FILENAME.$EXT"]),
        ).get_files_objects([str(path) for path in paths])
        return [item for values in groups.values() for item in values]

    def ensure_local(self, file, *, overwrite="cancel", verify_md5=False) -> Path:
        """Block until validated transfer completion; never open a conflict dialog."""
        self._api._check()
        if overwrite not in ("overwrite", "skip", "cancel"):
            raise ValueError("overwrite must be overwrite, skip or cancel")
        from thlib.repository_download import DownloadOperation, SyncTask

        native = file
        local_path = native.get_full_abs_path()
        web_path = native.get_full_web_path()
        if not local_path or not web_path.startswith(("http://", "https://")):
            raise ValueError(
                "A native file needs configured local and HTTP repository paths"
            )
        timestamp = native.get_timestamp(obj=True)
        task = SyncTask(
            task_id=uuid.uuid4().hex,
            key=str(native.get_unique_id()),
            file_object=native,
            title=native.get_filename_with_ext(),
            process="",
            local_path=local_path,
            web_path=web_path,
            expected_size=int(native.get_file_size() or 0),
            expected_md5=str(native.get_md5() or "").lower(),
            expected_mtime=timestamp.timestamp()
            if isinstance(timestamp, datetime)
            else 0.0,
            verify_md5=bool(verify_md5),
            overwrite_policy=overwrite,
        )
        result = {}

        def finished(_id, value):
            result["value"] = value

        def failed(_id, message, traceback):
            result["error"] = OSError(f"{message}\n{traceback}")

        def cancelled(_id):
            result["error"] = InterruptedError(
                "Repository transfer cancelled or requires overwrite permission"
            )

        signals = SimpleNamespace(
            finished=_Signal(finished),
            failed=_Signal(failed),
            cancelled=_Signal(cancelled),
            progress=_Signal(
                lambda _id, done, total, speed: report_progress(
                    {
                        "file": local_path,
                        "bytes_done": done,
                        "bytes_total": total,
                        "speed": speed,
                    }
                )
            ),
        )
        # ponytail: one transfer lock per API; use per-destination locks only if
        # measured multi-file throughput requires parallel transfers.
        with self._api._transfer_lock:
            DownloadOperation(task, signals).run()
        if "error" in result:
            raise result["error"]
        if "value" not in result:
            raise RuntimeError("Repository download did not report completion")
        return Path(result["value"]["path"])

    def open(self, file):
        path = self.ensure_local(file)
        file.open_file()
        return path

    def reveal(self, file):
        self._api._check()
        file.open_folder()
        return Path(file.get_full_abs_path())


class RepositoriesAPI:
    def __init__(self, api):
        self._api = api

    def list(self):
        self._api._check()
        return self._api._repositories()

    def get(self, repository_code):
        from .errors import NotFound

        for repository in self.list():
            values = repository.get("value") or []
            if repository.get("name") == repository_code or (
                len(values) > 3 and values[3] == repository_code
            ):
                return repository
        raise NotFound(f"Repository {repository_code!r} is unavailable")

    def sync(self, files, *, overwrite="cancel", verify_md5=False):
        """Synchronize explicitly selected native Files, preserving their repositories."""
        self._api._check()
        if hasattr(files, "get_files_objects"):
            files = files.get_files_objects()
        files = list(files)
        results = []
        for file in files:
            results.append(
                self._api.files.ensure_local(
                    file,
                    overwrite=overwrite,
                    verify_md5=verify_md5,
                )
            )
        return results
