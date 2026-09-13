"""Native repository download execution shared by UI and headless API."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import os
from pathlib import Path
import threading
import time
import traceback
import urllib.request
import urllib.parse
import uuid

FILE_TIME_TOLERANCE_SECONDS = 2.0


@dataclass
class SyncTask:
    task_id: str
    key: str
    file_object: object
    title: str
    process: str
    local_path: str
    web_path: str
    expected_size: int
    expected_md5: str = ""
    expected_mtime: float = 0.0
    is_ui_preview: bool = False
    verify_md5: bool = False
    state: str = "waiting"
    handle: object = None
    signals: object = None
    cancel: threading.Event = field(default_factory=threading.Event)
    started_at: float = 0.0
    overwrite_policy: str = "overwrite"


@dataclass(frozen=True)
class PreparedSyncEntry:
    """Native ``File`` data resolved before the GUI model is touched."""

    file_object: object
    process: str
    local_path: str
    web_path: str
    title: str
    expected_size: int
    expected_md5: str
    expected_mtime: float = 0.0
    unique_id: object = None
    is_ui_preview: bool = False

    @property
    def key(self) -> str:
        return f"{self.local_path}|{self.web_path}"


class DownloadOperation:
    def __init__(
        self,
        task: SyncTask,
        signals,
        retries: int = 2,
        chunk_size: int = 256 * 1024,
    ) -> None:
        self.task = task
        self.signals = signals
        self.retries = retries
        self.chunk_size = chunk_size

    def run(self) -> None:
        task = self.task
        partial = None
        try:
            # Resolve freshness entirely from the native TACTIC File metadata
            # before preparing a destination or constructing an HTTP request.
            # Repository storage may be slow or network-mounted, so all local
            # stat work remains in this runnable rather than the UI.  MD5 is
            # optional for explicit Repository Sync and never used by UI
            # previews, where reading every image twice would be too costly.
            destination = Path(task.local_path)
            native_exists = bool(task.file_object.is_exists())

            if native_exists:
                try:
                    local_stat = destination.stat()
                except OSError:
                    native_exists = False
            if native_exists:
                current_size = local_stat.st_size
                size_matches = (
                    task.expected_size <= 0 or current_size == task.expected_size
                )
                time_matches = (
                    task.expected_mtime <= 0
                    or abs(local_stat.st_mtime - task.expected_mtime)
                    <= FILE_TIME_TOLERANCE_SECONDS
                )
                checksum_matches = True
                if (
                    size_matches and time_matches
                    and task.verify_md5 and task.expected_md5
                ):
                    checksum = hashlib.md5()
                    with destination.open("rb") as stream:
                        while True:
                            if task.cancel.is_set():
                                raise InterruptedError("Download cancelled")
                            chunk = stream.read(self.chunk_size)
                            if not chunk:
                                break
                            checksum.update(chunk)
                    checksum_matches = (
                        checksum.hexdigest().lower() == task.expected_md5
                    )
                if size_matches and time_matches and checksum_matches:
                    self.signals.finished.emit(task.task_id, {
                        "path": str(destination),
                        "bytes": current_size,
                        "elapsed": 0.0,
                        "exists": True,
                    })
                    return
                if task.overwrite_policy == "skip":
                    self.signals.finished.emit(task.task_id, {
                        "path": str(destination),
                        "bytes": current_size,
                        "elapsed": 0.0,
                        "exists": True,
                        "skipped": True,
                    })
                    return
                if task.overwrite_policy == "cancel":
                    self.signals.cancelled.emit(task.task_id)
                    return

            destination = Path(task.file_object.prepare_repo())
            # UI and independent headless runtimes may transfer the same File.
            # Each operation owns its staging file and must not unlink another's.
            partial = destination.with_name(destination.name + "." + uuid.uuid4().hex + ".part")
            destination.parent.mkdir(parents=True, exist_ok=True)

            last_error = None
            last_traceback = ""
            for attempt in range(1, self.retries + 2):
                if task.cancel.is_set():
                    self.signals.cancelled.emit(task.task_id)
                    return
                started = time.perf_counter()
                downloaded = 0
                # A small file often finishes before the first useful visual
                # refresh. Starting this clock at the transfer start avoids
                # emitting both a progress event and a completion event for
                # every tiny file in a large repository batch.
                last_emit = started
                try:
                    checksum = hashlib.md5() if (
                        task.verify_md5 and task.expected_md5
                    ) else None
                    request = urllib.request.Request(
                        urllib.parse.quote(
                            task.web_path, safe=":/?&=%#"
                        ),
                        headers={"User-Agent": "TACTIC-Handler/RepositorySync"},
                    )
                    with urllib.request.urlopen(request, timeout=15) as response:
                        header_size = int(
                            response.headers.get("Content-Length") or 0
                        )
                        total = header_size or task.expected_size
                        with partial.open("wb") as stream:
                            while True:
                                if task.cancel.is_set():
                                    raise InterruptedError("Download cancelled")
                                chunk = response.read(self.chunk_size)
                                if not chunk:
                                    break
                                stream.write(chunk)
                                if checksum is not None:
                                    checksum.update(chunk)
                                downloaded += len(chunk)
                                now = time.perf_counter()
                                if now - last_emit >= 0.12:
                                    speed = downloaded / max(now - started, 0.001)
                                    self.signals.progress.emit(
                                        task.task_id, downloaded, total, speed
                                    )
                                    last_emit = now
                            stream.flush()
                            os.fsync(stream.fileno())
                    if header_size > 0 and downloaded != header_size:
                        raise IOError(
                            f"Incomplete file: {downloaded} of {header_size} bytes"
                        )
                    if checksum is not None:
                        downloaded_md5 = checksum.hexdigest().lower()
                        if downloaded_md5 != task.expected_md5:
                            raise IOError(
                                "Checksum mismatch: expected "
                                f"{task.expected_md5}, received {downloaded_md5}"
                            )
                    os.replace(partial, destination)
                    if task.expected_mtime > 0:
                        try:
                            os.utime(
                                destination,
                                (task.expected_mtime, task.expected_mtime),
                            )
                        except OSError:
                            # The downloaded bytes are still valid; leave the
                            # filesystem timestamp supplied by the OS.
                            pass
                    elapsed = time.perf_counter() - started
                    self.signals.finished.emit(task.task_id, {
                        "path": str(destination),
                        "bytes": downloaded,
                        "elapsed": elapsed,
                        "exists": False,
                        "attempt": attempt,
                    })
                    return
                except InterruptedError:
                    try:
                        partial.unlink(missing_ok=True)
                    except OSError:
                        pass
                    self.signals.cancelled.emit(task.task_id)
                    return
                except Exception as error:
                    last_error = error
                    last_traceback = traceback.format_exc()
                    try:
                        partial.unlink(missing_ok=True)
                    except OSError:
                        pass
                    if attempt <= self.retries:
                        time.sleep(min(0.35 * 2 ** (attempt - 1), 1.5))
            self.signals.failed.emit(
                task.task_id,
                str(last_error or "Download failed"),
                last_traceback,
            )
        except Exception as error:
            if partial is not None:
                try:
                    partial.unlink(missing_ok=True)
                except OSError:
                    pass
            self.signals.failed.emit(
                task.task_id, str(error), traceback.format_exc()
            )
