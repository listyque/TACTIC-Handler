from __future__ import annotations

import os
import re

from PySide6.QtCore import Qt


def _split_patterns(value: str) -> list[str]:
    return [
        part.strip() for part in str(value or "").split(",")
        if part.strip()
    ]


def _path_allowed(path: str, options: dict) -> bool:
    name = os.path.basename(path)
    if any(
        name.casefold().endswith(value.casefold())
        for value in _split_patterns(options.get("ignore", ""))
    ):
        return False
    filters = _split_patterns(options.get("filter", ""))
    if not filters:
        return True
    for value in filters:
        if value.startswith("/") and value.endswith("/"):
            try:
                if re.search(value[1:-1], name):
                    return True
            except re.error:
                continue
        elif value.casefold() in name.casefold():
            return True
    return False


def _rule_tags(path: str, pattern: str) -> tuple[dict, dict] | None:
    pattern = str(pattern or "").replace("\\", "/")
    if not pattern:
        return {}, {}
    token_re = re.compile(r"\{(?:(sobject|snapshot)\.)?([A-Za-z_]\w*)\}")
    parts = []
    tokens = []
    cursor = 0
    for index, match in enumerate(token_re.finditer(pattern)):
        parts.append(re.escape(pattern[cursor:match.start()]))
        group = f"ingest_{index}"
        parts.append(f"(?P<{group}>.+)")
        tokens.append((group, match.group(1) or "sobject", match.group(2)))
        cursor = match.end()
    if not tokens:
        normalized = path.replace("\\", "/")
        return ({}, {}) if pattern in {
            normalized, os.path.basename(normalized),
        } else None
    parts.append(re.escape(pattern[cursor:]))
    expression = re.compile("^" + "".join(parts) + "$", re.IGNORECASE)
    normalized = path.replace("\\", "/")
    candidates = (
        (normalized, os.path.basename(normalized))
        if "/" in pattern
        else (os.path.basename(normalized), normalized)
    )
    match = expression.match(candidates[0]) or expression.match(candidates[1])
    if not match:
        return None
    sobject_values = {}
    snapshot_values = {}
    for group, owner, name in tokens:
        target = snapshot_values if owner == "snapshot" else sobject_values
        target[name] = match.group(group)
    return sobject_values, snapshot_values


def prepare_ingest_path(path: str, options: dict) -> dict:
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    if not _path_allowed(path, options):
        return {"accepted": False, "reason": "Filtered by ingest rule"}
    extra_data = dict(options.get("extraData") or {})
    context = str(options.get("context") or "publish")
    if options.get("usePattern") and options.get("pattern"):
        tags = _rule_tags(path, str(options["pattern"]))
        if tags is None:
            return {
                "accepted": False,
                "reason": "Does not match ingest rule",
            }
        sobject_values, snapshot_values = tags
        extra_data.update(sobject_values)
        context = str(snapshot_values.get("context") or context)
    return {
        "accepted": True,
        "extraData": extra_data,
        "context": context,
    }


def find_ingest_conflicts(job: dict) -> dict:
    """Find existing relation children before upload or mutation."""
    from thlib import tactic_classes as tc
    from thlib import tactic_query as tq

    options = dict(job["options"])
    column = str(options.get("column") or "name")
    prepared_by_path = {}
    paths_by_identity: dict[str, list[str]] = {}
    display_by_identity = {}
    for path in job["paths"]:
        prepared = prepare_ingest_path(path, options)
        prepared_by_path[path] = prepared
        if not prepared.get("accepted"):
            continue
        extra_data = dict(prepared.get("extraData") or {})
        mapped_name = extra_data.get(column)
        if mapped_name in (None, ""):
            mapped_name = os.path.basename(path)
            if options.get("ignoreExtension"):
                mapped_name = os.path.splitext(mapped_name)[0]
        mapped_name = str(mapped_name)
        identity = mapped_name.casefold()
        paths_by_identity.setdefault(identity, []).append(path)
        display_by_identity[identity] = mapped_name

    server = tc.server_start(project=str(job["projectCode"]))
    names = list(display_by_identity.values())
    relation = dict(job.get("relation") or {})
    existing = list(tc.execute_procedure_serverside(
        tq.query_ingest_relation_matches,
        {
            "project_code": str(job["projectCode"]),
            "search_type": str(job["searchType"]),
            "parent_key": str(job["parentKey"]),
            "column": column,
            "names": names,
            "instance_path": relation.get("instancePath"),
        },
        project=str(job["projectCode"]),
        server=server,
    ) or []) if names else []
    existing_by_identity: dict[str, list[str]] = {}
    for record in existing:
        mapped_name = str(record.get(column) or "")
        if not mapped_name:
            continue
        search_key = str(
            record.get("__search_key__")
            or record.get("search_key") or ""
        )
        if not search_key:
            code = record.get("code")
            if code not in (None, ""):
                search_key = server.build_search_key(
                    str(job["searchType"]), str(code),
                    project_code=str(job["projectCode"]),
                )
            elif record.get("id") not in (None, ""):
                search_key = server.build_search_key(
                    str(job["searchType"]), str(record["id"]),
                    project_code=str(job["projectCode"]), column="id",
                )
        if search_key:
            existing_by_identity.setdefault(
                mapped_name.casefold(), []
            ).append(search_key)

    conflicts = []
    existing_by_path = {}
    for identity, paths in paths_by_identity.items():
        search_keys = list(dict.fromkeys(
            existing_by_identity.get(identity, [])
        ))
        batch_duplicate = len(paths) > 1
        if not search_keys and not batch_duplicate:
            continue
        for path in paths:
            existing_by_path[path] = search_keys
            conflicts.append({
                "path": path,
                "name": display_by_identity[identity],
                "searchKeys": search_keys,
                "batchDuplicate": batch_duplicate,
            })
    return {
        "conflicts": conflicts,
        "existingByPath": existing_by_path,
        "preparedByPath": prepared_by_path,
    }


class IngestPreflightCoordinator:
    """Own collision request lifetime and the pending user decision."""

    def __init__(self, owner) -> None:
        self._owner = owner
        self.worker = None
        self.pending: dict = {}

    def reset(self) -> None:
        self.worker = None
        self.pending = {}

    def begin(self, generation: int, job: dict) -> None:
        from thlib.environment import env_inst

        worker = env_inst.server_pool.add_task(find_ingest_conflicts, job)
        self.worker = worker
        worker.result.connect(
            lambda result: self._ready(generation, job, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._failed(generation, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    def _ready(self, generation: int, job: dict, result) -> None:
        owner = self._owner
        if generation != owner._generation:
            return
        self.worker = None
        if owner._cancel_event.is_set():
            owner._busy = False
            owner._message = owner.tr("Ingest cancelled")
            owner.files.replace([
                {**record, "status": "Ready", "error": ""}
                for record in owner.files._records
            ])
            owner.stateChanged.emit()
            return
        payload = dict(result or {})
        conflicts = list(payload.get("conflicts") or [])
        if not conflicts:
            job["preparedByPath"] = dict(
                payload.get("preparedByPath") or {}
            )
            owner._start_batch(generation, job)
            return

        existing_by_path = dict(payload.get("existingByPath") or {})
        can_update = all(
            len(existing_by_path.get(str(row.get("path") or ""), [])) == 1
            for row in conflicts
        )
        if job["options"].get("updateMode") == "update" and can_update:
            job["existingByPath"] = existing_by_path
            job["preparedByPath"] = dict(
                payload.get("preparedByPath") or {}
            )
            owner._start_batch(generation, job)
            return

        owner._busy = False
        owner._message = owner.tr("Existing items need a decision")
        self.pending = {
            "generation": generation,
            "job": job,
            "conflicts": conflicts,
            "existingByPath": existing_by_path,
            "preparedByPath": dict(payload.get("preparedByPath") or {}),
            "canUpdate": can_update,
        }
        owner.files.replace([
            {
                **record,
                "status": (
                    "Conflict" if str(record.get("path") or "")
                    in existing_by_path else "Ready"
                ),
                "error": "",
            }
            for record in owner.files._records
        ])
        if owner._silent:
            owner._application.window_model.show_window("ingest_files")
        owner.stateChanged.emit()

    def _failed(self, generation: int, error) -> None:
        owner = self._owner
        if generation != owner._generation:
            return
        payload = error[0] if isinstance(error, (tuple, list)) and error else error
        message = payload.get("exception") if isinstance(payload, dict) else payload
        stacktrace = (
            str(payload.get("stacktrace") or "")
            if isinstance(payload, dict) else ""
        )
        self.worker = None
        owner._busy = False
        owner._error = str(
            message or owner.tr("Could not check for existing items")
        )
        owner.files.replace([
            {**record, "status": "Ready", "error": ""}
            for record in owner.files._records
        ])
        if owner._debug_log:
            owner._debug_log.raise_error(
                message, stacktrace=stacktrace, group="ingest/files",
            )
        owner.stateChanged.emit()

    def resolve(self, action: str) -> None:
        owner = self._owner
        pending = dict(self.pending)
        if not pending:
            return
        action = str(action or "cancel")
        generation = int(pending["generation"])
        if generation != owner._generation:
            self.pending = {}
            owner.stateChanged.emit()
            return
        if action == "cancel":
            self.pending = {}
            owner._message = owner.tr("Ingest cancelled")
            owner.files.replace([
                {**record, "status": "Ready", "error": ""}
                for record in owner.files._records
            ])
            owner.stateChanged.emit()
            return

        job = dict(pending["job"])
        conflict_paths = {
            str(row.get("path") or "")
            for row in pending.get("conflicts", [])
        }
        if action == "update":
            if not pending.get("canUpdate"):
                return
            job["existingByPath"] = dict(pending["existingByPath"])
        elif action == "skip":
            job["skipPaths"] = conflict_paths
        elif action != "duplicates":
            return
        job["preparedByPath"] = dict(pending.get("preparedByPath") or {})
        self.pending = {}
        owner._busy = True
        owner._start_batch(generation, job)
