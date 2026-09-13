"""Check-in queue commands independent of presentation and execution threads."""

from __future__ import annotations

from copy import deepcopy
import threading
import uuid

from .errors import ConcurrentEdit, NotFound
from .identity import SearchKey
from .operations import check_blocking_call, report_progress


def validate_payload(payload):
    """Validate the public queue boundary before it reaches either queue owner."""
    if not isinstance(payload, dict):
        raise TypeError("A check-in payload must be a mapping")
    SearchKey.parse(payload.get("searchKey"))
    for name in ("context", "repository"):
        if not isinstance(payload.get(name), str) or not payload[name].strip():
            raise ValueError(f"Check-in {name} is required")
    files, names = payload.get("files"), payload.get("filesDict")
    if (
        not isinstance(files, list)
        or not files
        or not isinstance(names, list)
        or len(files) != len(names)
    ):
        raise ValueError("Check-in files and naming records must match")
    for record, naming in zip(files, names):
        if (
            not isinstance(record, dict)
            or not isinstance(record.get("path"), str)
            or not record["path"]
        ):
            raise ValueError("Each check-in file needs a source path")
        if (
            not isinstance(naming, (tuple, list))
            or len(naming) != 2
            or not isinstance(naming[1], dict)
        ):
            raise ValueError("Invalid TACTIC file naming record")


class _ProgressSignal:
    def emit(self, value):
        report_progress(value)


class HeadlessQueue:
    """One queue owner; execution reuses the desktop's native check-in functions."""

    def __init__(self, repositories):
        self._repositories = repositories
        self._lock = threading.RLock()
        self._execute_lock = threading.Lock()
        self._entries = {}

    def add(self, payload, title):
        validate_payload(payload)
        with self._lock:
            if len(self._entries) >= 1000:
                raise ValueError("Commit queue is full; remove completed entries")
            for entry in self._entries.values():
                existing = entry["payload"]
                if (
                    entry["state"] in {"prepared", "running", "uncertain"}
                    and existing["searchKey"] == payload["searchKey"]
                    and existing["context"] == payload["context"]
                    and existing["files"] == payload["files"]
                ):
                    raise ValueError(f"This check-in already exists as {entry['id']}")
            identity = uuid.uuid4().hex
            self._entries[identity] = {
                "id": identity,
                "title": title,
                "payload": deepcopy(payload),
                "state": "prepared",
                "result": None,
            }
            return identity

    def get(self, identity):
        with self._lock:
            if identity not in self._entries:
                raise NotFound(f"Queue item {identity!r} is unavailable")
            return deepcopy(self._entries[identity])

    def items(self):
        with self._lock:
            return list(deepcopy(self._entries).values())

    def update(self, identity, values):
        with self._lock:
            record = self._entries[identity]
            if record["state"] != "prepared":
                raise ConcurrentEdit("Only a prepared queue item can be edited")
            if set(values) - {"description", "context"}:
                raise ValueError("Unsupported queue edit")
            record["payload"].update(deepcopy(values))

    def remove(self, identity):
        with self._lock:
            record = self._entries[identity]
            if record["state"] in {"running", "uncertain"}:
                raise ConcurrentEdit("Cannot remove an active or unresolved check-in")
            del self._entries[identity]

    def commit(self, identity):
        check_blocking_call()
        from thlib.checkin_operation import execute_checkin_payload

        with self._execute_lock:
            record = self.get(identity)
            if record["state"] == "finished":
                return record["result"]
            if record["state"] != "prepared":
                raise ConcurrentEdit(
                    f"Check-in is {record['state']}; no automatic write retry"
                )
            repository = next(
                (
                    repo
                    for repo in self._repositories()
                    if repo["value"][3] == record["payload"]["repository"]
                ),
                None,
            )
            if repository is None:
                raise NotFound("The selected repository is no longer available")
            with self._lock:
                # Repository discovery can block. Capture any edits made while
                # it ran, then lock this entry against further edits/removal.
                payload = self.get(identity)["payload"]
                self._entries[identity]["state"] = "running"
            try:
                result = execute_checkin_payload(
                    payload, repository, progress_signal=_ProgressSignal()
                )
            except Exception as error:
                with self._lock:
                    # A transport failure may occur after server-side commit. The
                    # queue never retries a write merely because its reply was lost.
                    self._entries[identity]["state"] = "uncertain"
                    self._entries[identity]["error_type"] = type(error).__name__
                raise
            with self._lock:
                self._entries[identity].update(
                    state="finished", result=deepcopy(result)
                )
            return result


class CommitQueue:
    def __init__(self, api, gateway, project_code=None):
        self._api = api
        self._gateway = gateway
        self.project_code = project_code

    def _record(self, identity):
        self._api._check()
        record = self._gateway.get(identity)
        project = SearchKey.parse(record["payload"]["searchKey"]).project_code
        if self.project_code is not None and project != self.project_code:
            raise ValueError("This queue item belongs to another project")
        return record

    def get(self, operation_id):
        self._record(operation_id)
        return QueueItem(self, operation_id)

    def items(self, *, search_key=None, state=None):
        self._api._check()
        target = self._api._key(search_key) if search_key else None
        result = []
        for record in self._gateway.items():
            identity = SearchKey.parse(record["payload"]["searchKey"])
            if self.project_code and identity.project_code != self.project_code:
                continue
            if target is not None and identity != target:
                continue
            if state is not None and record["state"] != state:
                continue
            result.append(QueueItem(self, record["id"]))
        return result

    def add(
        self,
        target,
        *,
        context: str,
        files,
        repository: str,
        description="",
        file_type="file",
        version=None,
        is_revision=False,
        update_versionless=False,
        keep_file_name=False,
        generate_previews=True,
        mode="upload",
    ):
        self._api._check()
        identity = self._api._key(target)
        if self.project_code and identity.project_code != self.project_code:
            raise ValueError("Target belongs to another project")
        if not context or not isinstance(context, str):
            raise ValueError("An explicit TACTIC context is required")
        if mode not in {"upload", "copy", "preallocate"}:
            raise ValueError("mode must be upload, copy or preallocate")
        if version is not None and (
            isinstance(version, bool) or not isinstance(version, int) or version < 1
        ):
            raise ValueError("version must be a positive integer or None")
        repo = self._api.repositories.get(repository)
        grouped = self._api.files.match(files)
        if not grouped:
            raise ValueError("At least one source file is required")
        records, files_dict = [], []
        for file in grouped:
            paths = list(file.get_all_files_list())
            path = paths[0]
            extension = str(file.get_file_ext() or "").lstrip(".").lower()
            values = {
                "t": [file_type],
                "s": [""],
                "e": [extension],
                "p": [""],
                "m": None,
            }
            if generate_previews and file.is_previewable():
                values["t"].extend(["web", "icon"])
                values["s"].extend(["", ""])
                values["e"].extend(["jpg", "png"])
                values["p"].extend(["", ""])
            records.append(
                {
                    "path": path,
                    "paths": paths,
                    "template": "$FILENAME.$EXT" if extension else "$FILENAME",
                    "type": file_type,
                    "extension": extension,
                }
            )
            files_dict.append((file.get_name_part(), values))
        payload = {
            "searchKey": str(identity),
            "context": context,
            "process": context.split("/", 1)[0],
            "description": description,
            "version": version,
            "isRevision": bool(is_revision),
            "updateVersionless": bool(update_versionless),
            "onlyVersionless": False,
            "keepFileName": bool(keep_file_name),
            "generatePreviews": bool(generate_previews),
            "snapshotType": "file",
            "checkinType": "file",
            "mode": mode,
            "sequencePadding": 3,
            "repository": repo["value"][3],
            "files": records,
            "filesDict": files_dict,
        }
        sobject = self._api.sobject(str(identity))
        title = sobject.get_value("name") or sobject.get_code() or str(identity)
        return QueueItem(self, self._gateway.add(payload, title))

    def remove_completed(self):
        items = self.items(state="finished")
        for item in items:
            item.remove()
        return len(items)


class QueueItem:
    def __init__(self, queue, identity):
        self._queue = queue
        self.id = identity

    @property
    def state(self):
        return self._queue._record(self.id)["state"]

    def set_description(self, text):
        self._queue._record(self.id)
        self._queue._gateway.update(self.id, {"description": str(text)})

    def commit(self):
        from .objects import Snapshot

        self._queue._record(self.id)
        result = self._queue._gateway.commit(self.id)
        self._queue._api._invalidate(
            SearchKey.parse(
                self._queue._record(self.id)["payload"]["searchKey"]
            ).project_code,
        )
        api = self._queue._api
        if "__files__" not in result:
            return api.snapshot(result["__search_key__"])
        return Snapshot(api, api._core.Snapshot(deepcopy(result)))

    def submit(self):
        return self._queue._api.submit(self.commit)

    def remove(self):
        self._queue._record(self.id)
        self._queue._gateway.remove(self.id)
