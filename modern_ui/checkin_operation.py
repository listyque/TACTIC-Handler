from __future__ import annotations

import os
from pathlib import Path
import shutil
import uuid


class CheckinCancelled(InterruptedError):
    """Raised when check-in stops before snapshot creation."""


def _check_cancel(cancel_event) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise CheckinCancelled("Check-in cancelled")


def _copy_file(source: Path, destination: Path, cancel_event) -> None:
    with source.open("rb") as input_stream, destination.open("wb") as output_stream:
        while True:
            _check_cancel(cancel_event)
            chunk = input_stream.read(4 * 1024 * 1024)
            if not chunk:
                break
            output_stream.write(chunk)
        output_stream.flush()
        os.fsync(output_stream.fileno())
    shutil.copystat(source, destination)


def prepare_checkin(payload: dict, progress_signal=None, cancel_event=None) -> dict:
    import thlib.global_functions as gf
    import thlib.tactic_classes as tc

    files_objects = []
    file_paths = []
    for record in payload["files"]:
        _check_cancel(cancel_event)
        source_paths = list(record.get("paths") or [record["path"]])
        resolved_paths = []
        for source_path in source_paths:
            _check_cancel(cancel_event)
            path = Path(source_path).resolve(strict=True)
            if not path.is_file():
                raise ValueError(f"File is unavailable: {path}")
            resolved_paths.append(str(path))
        template = str(record.get("template") or "$FILENAME.$EXT")
        grouped = gf.MatchTemplate(
            [template],
            padding=max(1, min(9, int(payload.get("sequencePadding") or 3))),
        ).get_files_objects(resolved_paths)
        objects = [item for group in (grouped or {}).values() for item in group]
        if not objects:
            raise ValueError(f"Files no longer match template: {template}")
        file_object = objects[0]
        files_objects.append(file_object)
        file_paths.append(file_object.get_all_files_list())
    _check_cancel(cancel_event)
    virtual_snapshot = tc.get_virtual_snapshot(
        payload["searchKey"],
        payload["context"],
        payload["filesDict"],
        snapshot_type=payload.get("snapshotType") or "file",
        is_revision=payload.get("isRevision", False),
        keep_file_name=payload.get("keepFileName", False),
        explicit_filename=payload.get("explicitFilename") or None,
        version=payload.get("version"),
        checkin_type=payload.get("checkinType") or "file",
        ignore_keep_file_name=payload.get("ignoreKeepFileName", False),
        progress_signal=progress_signal,
    )
    return {
        "payload": payload,
        "filesObjects": files_objects,
        "filePaths": file_paths,
        "filesDict": payload["filesDict"],
        "virtualSnapshot": virtual_snapshot,
    }


def stage_checkin(
    inputs: dict, repository: dict, progress_signal=None, cancel_event=None
) -> bool:
    import thlib.global_functions as gf
    import thlib.tactic_classes as tc

    payload = inputs["payload"]
    repository_values = repository.get("value") or []
    if not repository_values or not repository_values[0]:
        raise ValueError("The selected repository has no local path")
    repository_root = Path(str(repository_values[0])).resolve()
    versions = ["versioned"]
    if payload.get("updateVersionless"):
        versions.append("versionless")
    if payload.get("onlyVersionless"):
        versions = ["versionless"]
    mode = str(payload.get("mode") or "upload")
    move_sources = mode == "move"
    copied_destinations = set()
    source_paths = set()
    total = max(1, sum(len(paths) for paths in inputs["filePaths"]) * len(versions))
    completed = 0

    for index, (_key, snapshot) in enumerate(inputs["virtualSnapshot"]):
        _check_cancel(cancel_event)
        file_object = inputs["filesObjects"][index]
        sources = [Path(path).resolve(strict=True) for path in inputs["filePaths"][index]]
        source_paths.update(os.path.normcase(str(path)) for path in sources)
        for version_name in versions:
            _check_cancel(cancel_event)
            version = snapshot.get(version_name) or {}
            names = list(version.get("names") or [])
            paths = list(version.get("paths") or [])
            if not names or not paths:
                raise ValueError(f"TACTIC naming returned no {version_name} destination")
            destination_dir = repository_root / str(paths[0])
            destinations = [
                Path(path) for path in file_object.get_all_new_files_list(
                    names[0], str(destination_dir),
                    new_frame_padding=int(payload.get("sequencePadding") or 3),
                )
            ]
            if len(destinations) != len(sources):
                raise ValueError(
                    "TACTIC naming returned a different number of destination files"
                )
            destination_dir.mkdir(parents=True, exist_ok=True)
            for source, destination in zip(sources, destinations):
                _check_cancel(cancel_event)
                destination = destination.resolve()
                if os.path.normcase(str(source)) != os.path.normcase(str(destination)):
                    temporary = destination.with_name(
                        f"{destination.name}.{uuid.uuid4().hex}.part"
                    )
                    try:
                        _copy_file(source, temporary, cancel_event)
                        _check_cancel(cancel_event)
                        os.replace(temporary, destination)
                    finally:
                        if temporary.exists():
                            temporary.unlink()
                if not destination.is_file():
                    raise OSError(f"Repository file was not created: {destination}")
                copied_destinations.add(os.path.normcase(str(destination)))
                gf.emit_progress(completed, {
                    "status_text": source.name,
                    "total_count": total,
                }, progress_signal)
                completed += 1

            if payload.get("generatePreviews") and len(paths) > 2 and len(names) > 2:
                web_dir = repository_root / str(paths[1])
                icon_dir = repository_root / str(paths[2])
                web_dir.mkdir(parents=True, exist_ok=True)
                icon_dir.mkdir(parents=True, exist_ok=True)
                web_files = file_object.get_all_new_files_list(names[1], str(web_dir))
                icon_files = file_object.get_all_new_files_list(names[2], str(icon_dir))
                for source, web_file, icon_file in zip(sources, web_files, icon_files):
                    _check_cancel(cancel_event)
                    tc.generate_web_and_icon(
                        str(source), str(web_file), str(icon_file)
                    )

    if move_sources:
        for source in source_paths:
            _check_cancel(cancel_event)
            if source not in copied_destinations:
                try:
                    Path(source).unlink()
                except FileNotFoundError:
                    pass
    return True


def execute_checkin_payload(
    payload: dict, repository: dict, progress_signal=None, cancel_event=None
) -> dict:
    import thlib.tactic_classes as tc

    inputs = prepare_checkin(
        payload, progress_signal=progress_signal, cancel_event=cancel_event
    )
    copied = stage_checkin(
        inputs, repository, progress_signal=progress_signal,
        cancel_event=cancel_event,
    )
    if copied is False:
        raise OSError("One or more files could not be copied to repository")
    mode = str(payload.get("mode") or "upload")
    snapshot_mode = (
        "upload" if mode == "upload"
        else "preallocate" if mode == "preallocate"
        else "inplace"
    )
    _check_cancel(cancel_event)
    result = tc.checkin_snapshot(
        search_key=payload["searchKey"],
        context=payload["context"],
        snapshot_type=payload.get("snapshotType") or "file",
        is_revision=payload.get("isRevision", False),
        description=payload.get("description") or "",
        version=payload.get("version"),
        update_versionless=payload.get("updateVersionless", False),
        only_versionless=payload.get("onlyVersionless", False),
        keep_file_name=payload.get("keepFileName", False),
        repo_name=repository,
        virtual_snapshot=inputs["virtualSnapshot"],
        files_dict=inputs["filesDict"],
        mode=snapshot_mode,
        create_icon=payload.get("generatePreviews", True),
        files_objects=inputs["filesObjects"],
        progress_signal=progress_signal,
    )
    if not isinstance(result, dict) or not result.get("__search_key__"):
        raise RuntimeError("TACTIC did not return the created snapshot")
    return result
