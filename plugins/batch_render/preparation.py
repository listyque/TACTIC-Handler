"""Batch preparation functions."""
from __future__ import annotations
import json
import subprocess
import zipfile
from pathlib import Path
from tactic_handler_api.operations import report_progress
from .catalog import _main_file, _preferred_snapshots, _preview_url, _query_shots, _title
from .project_config import _preset_state, _preset_items
from .frames import _format_frame_ranges, _job_ranges


def _repository_preset(api, project_code: str, search_type: str, name: str) -> dict:
    key = f"search_type:{search_type}:preset_name:{name}"
    settings = (
        api.project(project_code)
        .stype("sthpw/wdg_settings")
        .query(
            filters=[("key", key), ("project_code", project_code)],
            limit=2,
        )
        .items
    )
    if settings:
        data = json.loads(str(settings[0].get_value("data") or "{}"))
        if isinstance(data, dict):
            return data
    return {
        "preset_name": "default",
        "get_versions": False,
        "publish:{b}": {"state": True},
        "attachment:{b}": {"state": True},
        "icon:{b}": {"state": True},
    }


def _collect_preset_files(
    sobject,
    preset: dict,
    files: dict,
    visited: set[str],
    cancel,
) -> None:
    _check_cancel(cancel)
    key = sobject.get_search_key()
    if key in visited:
        return
    visited.add(key)
    enabled = set(_preset_items(preset, ":{b}", True))
    for pipeline in _preset_items(preset, ":{pp}").values():
        enabled.update(_preset_items(pipeline.get("sub") or {}, ":{pr}", True))
    snapshots = sobject.snapshots()
    for process in enabled:
        for snapshot in _preferred_snapshots(
            snapshots, process, preset.get("get_versions")
        ):
            for file in snapshot.get_files_objects():
                files[file.get_full_abs_path()] = file
    for child_type, child_preset in _preset_items(
        preset,
        ":{s}",
        True,
    ).items():
        for child in sobject.related(search_type=child_type):
            _collect_preset_files(
                child,
                child_preset.get("sub") or {},
                files,
                visited,
                cancel,
            )


def _check_cancel(cancel) -> None:
    if cancel.is_set():
        raise InterruptedError("Cancelled by user")


def _safe_extract(archive_path: Path, destination: Path, cancel=None) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            target = (root / member.filename).resolve()
            if not target.is_relative_to(root):
                raise ValueError(f"Unsafe cache archive member: {member.filename}")
        for member in archive.infolist():
            if cancel is not None:
                _check_cancel(cancel)
            archive.extract(member, root)


def _set_episode_task_status(episode, process: str, status: str) -> None:
    for task in episode.tasks(process):
        task.set_value("status", status)
        task.commit()


def _discover_queue(api, episode_key, config, test_render, queued_status):
    episode = api.sobject(episode_key)
    records = _query_shots(episode, config)
    if not records:
        raise ValueError(f"No shots to render for {_title(episode)}")
    if queued_status and not test_render:
        _set_episode_task_status(episode, config["render_process"], queued_status)
    return records


def _download_dependency(api, file, skip_errors: bool, errors: list[str]):
    try:
        return api.files.ensure_local(file, overwrite="overwrite")
    except InterruptedError:
        raise
    except (OSError, RuntimeError) as error:
        if not skip_errors:
            raise
        message = f"Пропущена зависимость {file.get_filename_with_ext()}: {error}"
        errors.append(message)
        report_progress({"text": message, "preparationError": message})
        return None


def _sync_episode_files(api, episode, preset, config, cancel, errors) -> None:
    report_progress({"stage": "Collecting dependencies"})
    files = {}
    _collect_preset_files(episode, preset, files, set(), cancel)
    for index, file in enumerate(files.values(), start=1):
        _check_cancel(cancel)
        report_progress(
            {
                "stage": "Synchronizing dependencies",
                "detail": f"{index}/{len(files)} · {file.get_filename_with_ext()}",
            }
        )
        _download_dependency(
            api, file, config.get("skip_dependency_errors", False), errors
        )


def _sync_alembic_caches(api, episode, config, cancel, errors) -> None:
    asset_type = config.get("asset_search_type")
    if not asset_type:
        return
    report_progress({"stage": "Collecting Alembic caches"})
    caches = {}
    # Same two levels as the original: direct cache assets and cache children.
    for asset in episode.related(search_type=asset_type):
        _check_cancel(cancel)
        if asset.get_value("assets_category_code") == config["alembic_category"]:
            caches[asset.get_search_key()] = asset
        for cache in asset.related(
            search_type=asset_type,
            filters=[("assets_category_code", config["alembic_category"])],
        ):
            caches[cache.get_search_key()] = cache

    for cache in caches.values():
        _check_cancel(cancel)
        file = _main_file(cache.snapshots(), config["scene_process"])
        if file is None or str(file.get_ext()).lower() != "zip":
            continue
        report_progress({"stage": "Extracting Alembic", "detail": _title(cache)})
        archive = _download_dependency(
            api, file, config.get("skip_dependency_errors", False), errors
        )
        if archive is None:
            continue
        _safe_extract(
            archive,
            Path(file.get_repo_path()) / config["alembic_cache_path"],
            cancel,
        )


def _prepare_episode(api, entry: dict, config: dict, cancel) -> dict:
    _check_cancel(cancel)
    api.repositories.list()
    episode = api.sobject(entry["episodeKey"])
    if not entry["test"] and not entry.get("singleShot"):
        _set_episode_task_status(
            episode, config["render_process"], config["running_status"]
        )
    preset = _repository_preset(
        api,
        episode.get_project().get_code(),
        episode.get_stype().get_code(),
        config["render_sync_preset"],
    )
    _check_cancel(cancel)
    errors = []
    _sync_episode_files(api, episode, preset, config, cancel, errors)
    _sync_alembic_caches(api, episode, config, cancel, errors)
    return {"preparationErrors": errors}


def _sync_shot_cache(api, snapshots, entry, job, config, cancel, errors) -> None:
    cache = _main_file(snapshots, config["cache_process"])
    if cache is None:
        return
    report_progress({"stage": "Downloading shot cache"})
    archive = _download_dependency(
        api, cache, config.get("skip_dependency_errors", False), errors
    )
    if archive is None:
        return
    _check_cancel(cancel)
    if not zipfile.is_zipfile(archive):
        return
    report_progress({"stage": "Extracting shot cache"})
    cache_root = (Path(cache.get_repo_path()) / config["cache_path"]).resolve()
    destination = (cache_root / entry["title"] / job["title"]).resolve()
    if not destination.is_relative_to(cache_root):
        raise ValueError(f"Cache destination is outside its root: {destination}")
    _safe_extract(archive, destination, cancel)


def _maya_batch_executable(render_executable: Path) -> Path:
    name = "mayabatch.exe" if render_executable.suffix.lower() == ".exe" else "mayabatch"
    executable = render_executable.with_name(name)
    if not executable.is_file():
        raise FileNotFoundError(f"Maya batch executable not found: {executable}")
    return executable


def _prepare_shot(api, entry: dict, job: dict, config: dict, cancel) -> dict:
    _check_cancel(cancel)
    executable = Path(config["maya_render_executable"])
    if not executable.is_file():
        raise FileNotFoundError(f"Maya Render executable not found: {executable}")
    maya_batch = _maya_batch_executable(executable)
    shot = api.sobject(job["shotKey"])
    snapshots = shot.snapshots()
    errors = []
    _sync_shot_cache(api, snapshots, entry, job, config, cancel, errors)
    file = _main_file(snapshots, config["scene_process"])
    if file is None:
        raise RuntimeError(f"No {config['scene_process']} scene for {job['title']}")
    if str(file.get_ext()).lower() not in {"ma", "mb"}:
        raise ValueError(f"Not a Maya scene: {file.get_filename_with_ext()}")
    report_progress(
        {"stage": "Preparing scene", "detail": file.get_filename_with_ext()}
    )
    scene = api.files.ensure_local(file, overwrite="overwrite")
    _check_cancel(cancel)
    output = Path(config["output_directory"]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    from thlib.environment import env_mode

    log_path = (
        Path(env_mode.get_current_path())
        / "log"
        / "batch_dispatcher"
        / entry["id"]
        / (job["id"] + ".log")
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    ranges = _job_ranges(job)
    return {
        "scene": str(scene),
        "output": str(output),
        "camera": config.get("camera") or "",
        "logPath": str(log_path),
        "mayaBatch": str(maya_batch),
        "command": "{}\nFrames: {}".format(
            subprocess.list2cmdline(
                [str(maya_batch), "-command", "<temporary batch runner>"]
            ),
            _format_frame_ranges(ranges),
        ),
        "previewUrl": _preview_url(snapshots),
        "preparationErrors": errors,
    }


def _repository_code(api) -> str:
    for repository in api.repositories.list():
        values = repository.get("value") or []
        if len(values) > 4 and values[4]:
            return str(values[3])
    raise RuntimeError("No active repository is configured")


def _write_preparation_log(entry: dict, identity: str, errors) -> str:
    from thlib.environment import env_mode

    path = (
        Path(env_mode.get_current_path())
        / "log"
        / "batch_dispatcher"
        / entry["id"]
        / f"{identity}.log"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "Preparation errors:\n" + "\n\n".join(map(str, errors)) + "\n",
        encoding="utf-8",
    )
    return str(path)


def _checkin_log(
    api,
    entry: dict,
    path: str,
    context: str,
    description: str,
    config: dict,
    failed: bool,
) -> None:
    mode = config.get("log_checkin", "always")
    if mode not in {"always", "failed"}:
        return
    if mode == "failed" and not failed:
        return
    if not path or not Path(path).is_file():
        return
    episode = api.sobject(entry["episodeKey"])
    item = api.commit_queue(episode.get_project().get_code()).add(
        episode,
        context=context,
        files=[Path(path)],
        repository=_repository_code(api),
        description=description,
        generate_previews=False,
    )
    item.commit()


def _finalize_preparation_log(api, entry: dict, config: dict) -> str:
    errors = entry.get("preparationErrors") or []
    if not errors:
        return ""
    path = _write_preparation_log(entry, "preparation", errors)
    _checkin_log(
        api,
        entry,
        path,
        f"{config['render_process']}/preparation",
        f"Preparation log for Episode {entry['title']}",
        config,
        True,
    )
    return path


def _finalize_shot(api, entry: dict, job: dict, config: dict) -> str:
    errors = job.get("preparationErrors") or []
    if errors and not job.get("logPath"):
        job["logPath"] = _write_preparation_log(entry, job["id"], errors)
    shot = api.sobject(job["shotKey"])
    if job["result"] != "cancelled":
        shot.set_value(config["rendered_field"], job["result"] == "completed")
        shot.commit()
    _checkin_log(
        api,
        entry,
        job.get("logPath", ""),
        f"{config['render_process']}/{job['title']}",
        f"Log file for Shot {job['title']}",
        config,
        job["result"] == "failed" or bool(errors),
    )
    return job.get("logPath", "")
