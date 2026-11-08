from __future__ import annotations

from contextlib import ExitStack
from copy import deepcopy
import os
from pathlib import Path
import shutil
from urllib.parse import parse_qs
import uuid

from thlib.repository_download import publish_without_replacement


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


def _discard_staged_file(path: Path, staged: os.stat_result) -> None:
    try:
        current = path.lstat()
        if (os.path.samestat(current, staged)
                and current.st_size == staged.st_size
                and current.st_mtime_ns == staged.st_mtime_ns):
            path.unlink()
    except FileNotFoundError:
        pass


def _publish_staged_file(temporary: Path, destination: Path,
                         rollback: ExitStack | None) -> None:
    if rollback is None:
        os.replace(temporary, destination)
        return
    staged = temporary.stat()
    try:
        publish_without_replacement(temporary, destination)
    except FileExistsError as error:
        raise FileExistsError(
            f"Numbered check-in file already exists: {destination}"
        ) from error
    rollback.callback(_discard_staged_file, destination, staged)


def _copy_file_atomically(source: Path, destination: Path, cancel_event,
                          mode: str = "copy", *, rollback: ExitStack | None) -> None:
    if os.path.normcase(str(source)) == os.path.normcase(str(destination)):
        return
    temporary = destination.with_name(
        f"{destination.name}.{uuid.uuid4().hex}.part"
    )
    try:
        if mode == "symlink":
            os.symlink(os.path.relpath(source, destination.parent), temporary)
        elif mode == "hardlink":
            os.link(source, temporary)
        elif mode == "copy":
            _copy_file(source, temporary, cancel_event)
        else:
            raise ValueError("Versionless files must use copy, symlink or hardlink")
        _check_cancel(cancel_event)
        _publish_staged_file(temporary, destination, rollback)
    finally:
        if os.path.lexists(temporary):
            temporary.unlink()


def _preview_temporary_path(destination: Path) -> Path:
    return destination.with_name(
        f".{destination.stem}.{uuid.uuid4().hex}.part{destination.suffix}"
    )


def _generate_previews_atomically(
    source: Path,
    web_destination: Path,
    icon_destination: Path,
    cancel_event,
    *,
    rollback: ExitStack | None,
) -> None:
    import thlib.tactic_classes as tc

    web_temporary = _preview_temporary_path(web_destination)
    icon_temporary = _preview_temporary_path(icon_destination)
    try:
        tc.generate_web_and_icon(
            str(source), str(web_temporary), str(icon_temporary)
        )
        _check_cancel(cancel_event)
        for kind, temporary in (
            ("web", web_temporary), ("icon", icon_temporary)
        ):
            if not temporary.is_file() or temporary.stat().st_size <= 0:
                raise OSError(
                    f"TACTIC could not generate the {kind} preview for "
                    f"{source.name}"
                )
        _publish_staged_file(web_temporary, web_destination, rollback)
        _publish_staged_file(icon_temporary, icon_destination, rollback)
    finally:
        for temporary in (web_temporary, icon_temporary):
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def versionless_allowed(payload: dict) -> bool:
    return (payload.get('checkinType') not in {'multi_file', 'dir', 'sequence'}
            and not payload.get('groupCheckin'))


def apply_checkin_type_options(payload: dict) -> None:
    # Resumed uploads must keep the manifest already accepted by the server.
    if payload.get('_serverQueue'):
        return
    if not versionless_allowed(payload):
        payload['updateVersionless'] = False
        payload['onlyVersionless'] = False


def _naming_options(payload: dict) -> dict:
    return dict(snapshot_type=payload.get('snapshotType') or 'file',
                is_revision=payload.get('isRevision', False),
                keep_file_name=payload.get('keepFileName', False),
                explicit_filename=payload.get('explicitFilename') or None,
                version=payload.get('version'), checkin_type=payload.get('checkinType') or 'file',
                ignore_keep_file_name=payload.get('ignoreKeepFileName', False))


def prepare_checkins(payloads: list[dict]) -> list[dict]:
    import traceback
    import thlib.tactic_classes as tc

    if not 1 <= len(payloads) <= 50:
        raise ValueError('Naming preview requires between 1 and 50 operations')
    results = [None] * len(payloads)
    prepared = []
    for index, payload in enumerate(payloads):
        try:
            inputs = prepare_checkin(payload, resolve_naming=False)
            prepared.append((index, inputs))
        except Exception as error:
            results[index] = {'result': None, 'error': str(error), 'stacktrace': traceback.format_exc()}
    if prepared:
        arguments = [dict(_naming_options(inputs['payload']), search_key=inputs['payload']['searchKey'],
                          context=inputs['payload']['context'], files_dict=inputs['filesDict'])
                     for index, inputs in prepared]
        values = tc.get_virtual_snapshots(arguments)
        for (index, inputs), value in zip(prepared, values):
            results[index] = value
    return results


def prepare_checkin(payload: dict, progress_signal=None, cancel_event=None,
                    refresh_naming: bool = False, resolve_naming: bool = True) -> dict:
    import thlib.global_functions as gf
    import thlib.tactic_classes as tc

    payload = dict(payload or {})
    apply_checkin_type_options(payload)
    search_key = str(payload.get("searchKey") or "").strip()
    if search_key.startswith("skey://"):
        search_key = search_key[len("skey://"):]
    if not search_key or "://" in search_key:
        raise ValueError("Check-in requires a TACTIC Search Object key")
    payload["searchKey"] = search_key
    if "versionlessMode" not in payload:
        from thlib.environment import cfg_controls
        index = int(gf.get_value_from_config(
            cfg_controls.get_checkin() or {}, "versionlessModeComboBox", 0
        ) or 0)
        if index not in (0, 1, 2):
            raise ValueError("Invalid versionless file preference")
        payload["versionlessMode"] = ("copy", "symlink", "hardlink")[index]
    files_objects = []
    file_paths = []
    files_dict = deepcopy(list(payload["filesDict"]))
    application_info = payload.get("applicationInfo") or {}
    if not isinstance(application_info, dict):
        raise ValueError("DCC application metadata must be a JSON object")
    for index, record in enumerate(payload["files"]):
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
        if application_info:
            file_object.set_app_info(application_info)
        files_objects.append(file_object)
        file_paths.append(file_object.get_all_files_list())
        if index < len(files_dict):
            key, values = files_dict[index]
            values = dict(values or {})
            if values.get("m") is None:
                try:
                    metadata = dict(file_object.get_metadata() or {})
                    metadata["name_part"] = file_object.get_name_part()
                except (AttributeError, KeyError, TypeError):
                    metadata = None
                values["m"] = metadata
            files_dict[index] = (key, values)
    _check_cancel(cancel_event)
    # Queue previews can predate an earlier check-in to the same context.
    prepared_naming = None if refresh_naming else payload.get("virtualSnapshot")
    virtual_snapshot = deepcopy(prepared_naming)
    if prepared_naming is None and resolve_naming:
        virtual_snapshot = tc.get_virtual_snapshot(
            payload["searchKey"],
            payload["context"],
            files_dict,
            **_naming_options(payload),
            progress_signal=progress_signal,
        )
    elif prepared_naming is not None and (
        not isinstance(virtual_snapshot, (list, tuple))
        or len(virtual_snapshot) != len(files_objects)
        or any(
            not isinstance(item, (list, tuple)) or len(item) != 2
            or not isinstance(item[1], dict)
            for item in virtual_snapshot
        )
    ):
        raise ValueError("Prepared TACTIC naming does not match the files")
    return {
        "payload": payload,
        "filesObjects": files_objects,
        "filePaths": file_paths,
        "filesDict": files_dict,
        "virtualSnapshot": virtual_snapshot,
    }


def stage_checkin(
    inputs: dict, repository: dict, progress_signal=None, cancel_event=None,
    *, rollback: ExitStack,
) -> dict[Path, os.stat_result]:
    import thlib.global_functions as gf

    payload = inputs["payload"]
    link_mode = str(payload.get("versionlessMode") or "copy")
    if link_mode not in ("copy", "symlink", "hardlink"):
        raise ValueError("Versionless files must use copy, symlink or hardlink")
    repository_values = repository.get("value") or []
    if not repository_values or not repository_values[0]:
        raise ValueError("The selected repository has no local path")
    repository_root = Path(str(repository_values[0])).resolve()
    versions = ["versioned"]
    if payload.get("updateVersionless"):
        versions.append("versionless")
    if payload.get("onlyVersionless"):
        versions = ["versionless"]
    _check_cancel(cancel_event)
    sources_by_file = [
        [Path(path).resolve(strict=True) for path in paths]
        for paths in inputs["filePaths"]
    ]
    move_sources = (
        {source: source.stat() for sources in sources_by_file for source in sources}
        if payload.get("mode") == "move" else {}
    )
    copied_destinations = set()
    preview_cache = {}
    versioned_files = {}
    total = max(1, sum(len(paths) for paths in inputs["filePaths"]) * len(versions))
    completed = 0

    # A collision in any numbered file must be detected before changing latest aliases.
    for version_name in versions:
        if version_name == "versionless":
            # A latest alias may now point to a numbered file. Keep its target.
            rollback.pop_all()
        numbered_rollback = (
            rollback if version_name == "versioned" and not payload.get("isRevision") else None
        )
        for index, (_key, snapshot) in enumerate(inputs["virtualSnapshot"]):
            _check_cancel(cancel_event)
            file_object = inputs["filesObjects"][index]
            sources = sources_by_file[index]
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
            numbered = versioned_files.get(index)
            alias_mode = link_mode if version_name == "versionless" and numbered else "copy"
            file_sources = numbered if alias_mode != "copy" else sources
            for source, destination in zip(file_sources, destinations):
                _check_cancel(cancel_event)
                # Resolve the parent only: following yesterday's alias would
                # overwrite the numbered version instead of replacing its link.
                destination = destination.parent.resolve() / destination.name
                if os.path.normcase(str(source)) != os.path.normcase(str(destination)):
                    _copy_file_atomically(
                        source, destination, cancel_event, alias_mode, rollback=numbered_rollback
                    )
                if not destination.is_file():
                    raise OSError(f"Repository file was not created: {destination}")
                copied_destinations.add(os.path.normcase(str(destination)))
                gf.emit_progress(completed, {
                    "status_text": source.name,
                    "total_count": total,
                }, progress_signal)
                completed += 1
            if version_name == "versioned":
                versioned_files[index] = [
                    path.parent.resolve() / path.name for path in destinations
                ]

            if payload.get("generatePreviews") and len(paths) > 2 and len(names) > 2:
                web_dir = repository_root / str(paths[1])
                icon_dir = repository_root / str(paths[2])
                web_dir.mkdir(parents=True, exist_ok=True)
                icon_dir.mkdir(parents=True, exist_ok=True)
                web_files = file_object.get_all_new_files_list(names[1], str(web_dir))
                icon_files = file_object.get_all_new_files_list(names[2], str(icon_dir))
                for source, web_file, icon_file in zip(sources, web_files, icon_files):
                    _check_cancel(cancel_event)
                    source_key = os.path.normcase(str(source))
                    web_file = Path(web_file).parent.resolve() / Path(web_file).name
                    icon_file = Path(icon_file).parent.resolve() / Path(icon_file).name
                    copied_destinations.update(
                        os.path.normcase(str(path)) for path in (web_file, icon_file)
                    )
                    cached = preview_cache.get(source_key)
                    if cached:
                        _copy_file_atomically(
                            cached[0], web_file, cancel_event, alias_mode, rollback=numbered_rollback
                        )
                        _copy_file_atomically(
                            cached[1], icon_file, cancel_event, alias_mode, rollback=numbered_rollback
                        )
                    else:
                        _generate_previews_atomically(
                            source, web_file, icon_file, cancel_event,
                            rollback=numbered_rollback,
                        )
                        preview_cache[source_key] = (web_file, icon_file)

    return {
        source: original for source, original in move_sources.items()
        if os.path.normcase(str(source)) not in copied_destinations
    }


def _remove_confirmed_move_sources(sources: dict[Path, os.stat_result]) -> None:
    from thlib.environment import dl

    for source, original in sources.items():
        try:
            current = source.lstat()
            if (
                os.path.samestat(current, original)
                and current.st_mtime_ns == original.st_mtime_ns
                and current.st_ctime_ns == original.st_ctime_ns
                and current.st_size == original.st_size
            ):
                source.unlink()
            else:
                dl.warning(f"Check-in succeeded. Changed source kept: {source}",
                           group_id="checkin/move")
        except FileNotFoundError:
            pass
        except OSError as error:
            dl.warning(f"Check-in succeeded. Could not remove source {source}: {error}",
                       group_id="checkin/move")


def execute_checkin_payload(
    payload: dict, repository: dict, progress_signal=None, cancel_event=None
) -> dict:
    inputs = prepare_checkin(
        payload, progress_signal=progress_signal, cancel_event=cancel_event,
        refresh_naming=not bool(payload.get("dccScene")),
    )
    return execute_prepared_checkin(inputs, repository, progress_signal, cancel_event)


def execute_prepared_checkin(
    inputs: dict, repository: dict, progress_signal=None, cancel_event=None,
) -> dict:
    import thlib.global_functions as gf
    import thlib.tactic_classes as tc

    payload = inputs["payload"]
    mode = str(payload.get("mode") or "upload")
    snapshot_mode = (
        "upload" if mode == "upload"
        else "preallocate" if mode == "preallocate"
        else "inplace"
    )
    with ExitStack() as rollback:
        move_sources = stage_checkin(
            inputs, repository, progress_signal=progress_signal,
            cancel_event=cancel_event, rollback=rollback,
        )
        _check_cancel(cancel_event)
        gf.emit_progress(-1, {"snapshot_mode": snapshot_mode}, progress_signal)
        _check_cancel(cancel_event)
        # Once submitted, a lost reply can mean the files are registered.
        rollback.pop_all()
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
    search_key = result.get("__search_key__") if isinstance(result, dict) else None
    if not isinstance(search_key, str):
        raise RuntimeError("TACTIC did not return the created snapshot")
    search_type, _, locator = search_key.removeprefix("skey://").partition("?")
    identity = parse_qs(locator)
    if search_type != "sthpw/snapshot" or not (identity.get("code") or identity.get("id")):
        raise RuntimeError("TACTIC did not return the created snapshot")
    if move_sources and (cancel_event is None or not cancel_event.is_set()):
        _remove_confirmed_move_sources(move_sources)
    return result
