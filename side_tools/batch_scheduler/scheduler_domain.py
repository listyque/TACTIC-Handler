"""Batch discovery, frame selection, and Maya render process."""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import threading
import time
import uuid
import zipfile
from collections import Counter
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from tactic_handler_api.operations import report_progress

BATCH_DISPATCHER_CONFIG = {
    "project_config": {
        "episode_search_type": "complex/scenes",
        "shot_search_type": "complex/shot",
        "scene_process": "publish",
        "cache_process": "cache",
        "render_process": "render",
        "render_sync_preset": "render_sync",
        "rendered_field": "rendered",
        "cache_path": "niki_friends/cache/nCache",
        "asset_search_type": "dolly3d/assets",
        "alembic_category": "cache/abc",
        "alembic_cache_path": "cache/alembic",
        "queue_statuses": ["Рендер", "В очереди"],
        "status_options": ["Подготовлен", "Рендер", "В очереди", "Проверен"],
        "running_status": "Рендерится",
        "complete_status": "Готов",
        "failed_status": "Ошибки",
        "terminal_status": "Проверен",
        "maya_render_executable": "C:/Program Files/Autodesk/Maya2022/bin/Render.exe",
        "output_directory": "D:/sequences_path",
        "camera": "ubercam",
        "update_interval": 10,
        "stop_on_error": False,
        "skip_dependency_errors": False,
        "render_timeout_minutes": 0,
        "log_checkin": "always",
        "web_enabled": True,
        "web_port": 92,
        "web_security": False,
    },
}

_UI_TEXT = {
    "Cancelled": "Отменено",
    "Collecting Alembic caches": "Поиск Alembic-кэшей",
    "Collecting dependencies": "Поиск зависимостей",
    "Completed": "Завершено",
    "Contains held shots": "Есть удержанные шоты",
    "Could not save episode status": "Не удалось сохранить статус эпизода",
    "Discovery failed": "Не удалось загрузить шоты",
    "Downloading shot cache": "Загрузка кэша шота",
    "Episode already queued": "Эпизод уже в очереди",
    "Excluded": "Исключён",
    "Extracting Alembic": "Распаковка Alembic",
    "Extracting shot cache": "Распаковка кэша шота",
    "Failed": "Ошибка",
    "Held": "Удержано",
    "Interrupted session": "Прерванный сеанс",
    "Loading queued shots": "Загрузка шотов очереди",
    "Loading shot list": "Загрузка списка шотов",
    "Pause after current shot": "Пауза после текущего шота",
    "Render pause requested": "Пауза запрошена · текущий кадр будет завершён",
    "Render paused": "Рендер на паузе",
    "Resuming render": "Продолжение рендера",
    "Preparing scene": "Подготовка сцены",
    "Preparing shot": "Подготовка шота",
    "Queue finished": "Очередь завершена",
    "Queue paused": "Очередь на паузе",
    "Queue running": "Очередь запущена",
    "Queue stopped": "Очередь остановлена",
    "Ready to render": "Готово к рендеру",
    "Ready · queue paused": "Готово · очередь на паузе",
    "Rendering shot": "Рендеринг шота",
    "Render failed · stopping process": "Ошибка рендера · остановка процесса",
    "Render failed": "Ошибка рендера",
    "Render log is available after the shot starts": "Лог появится после запуска шота",
    "Restored · resume or retry explicitly": "Восстановлено · запустите вручную",
    "Retry queued": "Повтор добавлен в очередь",
    "Saving episode status": "Сохранение статуса эпизода",
    "Saving result and render log": "Сохранение результата и лога",
    "Selected work finished · queue paused": "Выбранная задача завершена · очередь на паузе",
    "Stopping queue": "Остановка очереди",
    "Stopping renderer / finishing current transfer": "Остановка рендера / завершение передачи",
    "Stopping · waiting for active operation": "Остановка · ожидание активной операции",
    "Synchronizing dependencies": "Синхронизация зависимостей",
    "Synchronizing episode": "Синхронизация эпизода",
    "Select a shot to open its render log": "Выберите шот, чтобы открыть его лог",
    "See details": "Смотрите параметры",
    "Use + to add this episode to the queue": "Добавьте эпизод в очередь кнопкой +",
    "Waiting": "Ожидание",
    "Waiting for jobs": "Ожидание задач",
    "Waiting for next shot": "Ожидание следующего шота",
    "Waiting · held jobs remain": "Ожидание · остались удержанные задачи",
}


def _ui_text(value) -> str:
    value = str(value or "")
    return "\n".join(_UI_TEXT.get(line, line) for line in value.split("\n"))


# TACTIC discovery


def _title(sobject) -> str:
    return str(
        sobject.get_value("name")
        or sobject.get_value("title")
        or sobject.get_code()
        or ""
    )


def _preferred_snapshots(snapshots, process: str, all_versions=False) -> list:
    matches = [
        snapshot
        for snapshot in snapshots
        if str(snapshot.get_info().get("process") or "") == process
    ]
    if all_versions:
        return matches
    versionless = [snapshot for snapshot in matches if snapshot.is_versionless()]
    return (
        versionless
        or sorted(
            matches,
            key=lambda snapshot: int(snapshot.get_version() or 0),
            reverse=True,
        )[:1]
    )


def _main_file(snapshots, process: str):
    for snapshot in _preferred_snapshots(snapshots, process):
        files = snapshot.get_files_objects()
        return next(
            (file for file in files if str(file.get_type() or "") == "main"),
            files[0] if files else None,
        )
    return None


def _preview_url(snapshots) -> str:
    processes = [
        str(snapshot.get_info().get("process") or "") for snapshot in snapshots
    ]
    for process in dict.fromkeys(("icon", "publish", *processes)):
        for snapshot in _preferred_snapshots(snapshots, process):
            files = sorted(
                snapshot.get_files_objects(),
                key=lambda file: {"icon": 0, "web": 1}.get(file.get_type(), 2),
            )
            for file in files:
                if not file.is_previewable():
                    continue
                file = file.get_icon_preview() or file.get_web_preview() or file
                if str(file.get_ext()).lower() not in {
                    "png",
                    "jpg",
                    "jpeg",
                    "gif",
                    "bmp",
                    "webp",
                    "tif",
                    "tiff",
                }:
                    continue
                web_path = str(file.get_full_web_path() or "")
                if web_path.startswith(("http://", "https://")):
                    return web_path
                local_path = str(file.get_full_abs_path() or "")
                if local_path and Path(local_path).is_file():
                    return Path(local_path).resolve().as_uri()
    return ""


def _task_status_color(workflow, task, status: str) -> str:
    pipeline_code = str(task.get_value("pipeline_code") or "") if task else ""
    if not pipeline_code or not status:
        return "#ffffff"
    pipelines = workflow.get_by_stype_code("sthpw/task") or {}
    pipeline = pipelines.get(pipeline_code)
    if pipeline is None:
        return "#ffffff"
    process = pipeline.get_pipeline_process(status) or {}
    return str(process.get("color") or "#ffffff")


def _episode_filter_statuses(config: dict) -> list[str]:
    return list(
        dict.fromkeys(
            [
                *config["status_options"],
                config["running_status"],
                config["failed_status"],
                config["complete_status"],
            ]
        )
    )


def _query_episodes(
    api,
    project_code: str,
    config: dict,
    visible_statuses: tuple[str, ...],
    watch_server: bool,
) -> dict:
    api.repositories.list()
    project = api.project(project_code)
    stype = project.stype(config["episode_search_type"])
    workflow = project.workflow()
    statuses = _episode_filter_statuses(config)
    task_type = project.stype("sthpw/task")
    tasks = task_type.query(
        filters=[
            (
                "search_type",
                f"{config['episode_search_type']}?project={project_code}",
            ),
            ("process", config["render_process"]),
            ("status", "in", "|".join(statuses)),
        ],
        order_by=["search_code", "timestamp"],
        limit=1000,
    ).items
    tasks_by_episode = {
        str(task.get_value("search_code") or ""): task
        for task in tasks
        if task.get_value("search_code") and task.get_value("status")
    }
    counts = Counter(
        str(task.get_value("status") or "") for task in tasks_by_episode.values()
    )
    color_source = next(iter(tasks_by_episode.values()), None)
    filters = [
        {
            "value": status,
            "title": status,
            "statusAccent": (
                _task_status_color(workflow, color_source, status)
                if color_source
                else ""
            ),
            "count": counts[status],
        }
        for status in statuses
    ]

    required_statuses = set(visible_statuses)
    if watch_server:
        required_statuses.update(config["queue_statuses"])
    episode_codes = [
        code
        for code, task in tasks_by_episode.items()
        if str(task.get_value("status") or "") in required_statuses
    ]
    episodes = (
        stype.query(
            filters=[("code", "in", "|".join(episode_codes))],
            order_by=["name"],
            limit=1000,
        ).items
        if episode_codes
        else ()
    )
    records = []
    for episode in episodes:
        task = tasks_by_episode[str(episode.get_code() or "")]
        status = str(task.get_value("status") or "")
        snapshots = episode.snapshots()
        key = episode.get_search_key()
        records.append(
            {
                "title": _title(episode),
                "searchKey": key,
                "code": str(episode.get_code() or ""),
                "subtitle": str(episode.get_value("description") or ""),
                "previewUrl": _preview_url(snapshots),
                "renderStatus": status,
                "statusColor": _task_status_color(workflow, task, status),
                "statusChoices": [
                    {
                        "title": value,
                        "accent": _task_status_color(workflow, task, value),
                        "checked": status == value,
                    }
                    for value in config["status_options"]
                ],
                "serverQueued": status in set(config["queue_statuses"]),
            }
        )
    return {
        "episodes": [
            record for record in records if record["renderStatus"] in visible_statuses
        ],
        "queuedEpisodes": [record for record in records if record["serverQueued"]],
        "filters": filters,
    }


def _query_shots(episode, config: dict) -> list[dict]:
    shots = episode.related(search_type=config["shot_search_type"])
    records = []
    for shot in shots:
        snapshots = shot.snapshots()
        scene_file = _main_file(snapshots, config["scene_process"])
        start = _frame_number(shot.get_value("start_frame"), 1, _title(shot))
        end = _frame_number(shot.get_value("end_frame"), start, _title(shot))
        if end < start:
            raise ValueError(f"Invalid frame range for {_title(shot)}: {start}–{end}")
        scene_path = str(scene_file.get_full_abs_path() or "") if scene_file else ""
        rendered = _preset_state(shot.get_value(config["rendered_field"]))
        records.append(
            {
                "title": _title(shot),
                "searchKey": shot.get_search_key(),
                "previewUrl": _preview_url(snapshots),
                "excluded": rendered,
                "start": start,
                "end": end,
                "scenePath": scene_path,
            }
        )
    return records


# Queue records and frame selection


def _frame_number(value, default: int, title: str) -> int:
    if value is None or value == "":
        return default
    try:
        number = float(value)
        if number.is_integer():
            return int(number)
    except (ValueError, TypeError, OverflowError):
        pass
    raise ValueError(f"Invalid frame number for {title}: {value!r}")


def _parse_frame_spec(value: str, first: int, last: int) -> list[tuple[int, int]]:
    ranges = []
    for part in value.split(","):
        match = re.fullmatch(r"\s*(-?\d+)\s*(?:-\s*(-?\d+))?\s*", part)
        if not match:
            raise ValueError(f"Invalid frame range: {value!r}")
        start = int(match.group(1))
        end = int(match.group(2) or start)
        if start > end:
            raise ValueError(f"Frame range starts after it ends: {part.strip()}")
        if start < first or end > last:
            raise ValueError(f"Frames must stay inside {first}-{last}: {part.strip()}")
        ranges.append((start, end))
    merged = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _format_frame_ranges(ranges) -> str:
    return ", ".join(
        str(start) if start == end else f"{start}-{end}" for start, end in ranges
    )


def _job_ranges(job: dict) -> list[tuple[int, int]]:
    return [
        tuple(pair) for pair in job.get("frameRanges") or [(job["start"], job["end"])]
    ]


def _job_frame_count(job: dict) -> int:
    return sum(end - start + 1 for start, end in _job_ranges(job))


def _queue_entry(key: str, episode: dict, test_render: bool, origin: str) -> dict:
    return {
        "id": uuid.uuid4().hex,
        "episodeKey": key,
        "title": episode.get("title") or key,
        "previewUrl": episode.get("previewUrl", ""),
        "test": test_render,
        "state": "discovering",
        "stage": "Loading shot list",
        "error": "",
        "elapsed": 0.0,
        "expanded": False,
        "prepared": False,
        "preparationErrors": [],
        "created": time.time(),
        "jobs": [],
        "origin": origin,
    }


def _shot_job(row: dict, test_render: bool) -> dict:
    start, end = (1, 1) if test_render else (row["start"], row["end"])
    if end < start:
        raise ValueError(f"Invalid frame range for {row['title']}: {start}–{end}")
    excluded = row["excluded"] and not test_render
    return {
        "id": uuid.uuid4().hex,
        "shotKey": row["searchKey"],
        "title": row["title"],
        "start": start,
        "end": end,
        "frameSpec": _format_frame_ranges([(start, end)]),
        "frameRanges": [[start, end]],
        "state": "skipped" if excluded else "waiting",
        "stage": "Excluded" if excluded else "Waiting",
        "error": "",
        "progress": 0.0,
        "elapsed": 0.0,
        "renderElapsed": 0.0,
        "frame": "",
        "framesDone": 0,
        "attempt": 1,
        "scene": row["scenePath"],
        "logPath": "",
        "renderOutput": "",
        "renderFiles": [],
        "preparationErrors": [],
        "pid": "",
        "previewUrl": row.get("previewUrl", ""),
    }


def _preset_state(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {
            "1",
            "2",
            "true",
            "on",
            "yes",
            "checked",
            "enabled",
        }
    return bool(value)


def _preset_items(mapping: dict, suffix: str, enabled=False) -> dict:
    return {
        str(key).removesuffix(suffix): value
        for key, value in (mapping or {}).items()
        if str(key).endswith(suffix)
        and isinstance(value, dict)
        and (not enabled or _preset_state(value.get("state")))
    }


# Repository synchronization and scene preparation


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


# Maya renderer process


_RENDER_EVENT_PREFIX = "TH_BATCH_EVENT "
_MAYA_RUNNER_BODY = r'''
import json
import traceback

from maya import cmds, mel

EVENT_PREFIX = "TH_BATCH_EVENT "


def emit(kind, **values):
    print(
        EVENT_PREFIX + json.dumps({"type": kind, **values}, separators=(",", ":")),
        flush=True,
    )


def set_render_attribute(name, value):
    cmds.select("defaultRenderGlobals")
    mel.eval("removeRenderLayerAdjustmentAndUnlock .{}".format(name))
    cmds.setAttr("defaultRenderGlobals." + name, value)


def frame_hook():
    pause_file = repr(PAUSE_FILE)
    code = (
        "import json, os, time\n"
        "from maya import cmds\n"
        "frame = int(cmds.currentTime(query=True))\n"
        "padding = int(cmds.getAttr("
        "'defaultRenderGlobals.extensionPadding') or 1)\n"
        "try:\n"
        "    files = cmds.renderSettings("
        "genericFrameImageName=str(frame).zfill(padding), fullPath=True) or []\n"
        "except Exception:\n"
        "    files = []\n"
        "if isinstance(files, str):\n"
        "    files = [files]\n"
        "files = [os.path.normpath(path) for path in files "
        "if os.path.isfile(path)]\n"
        "print('TH_BATCH_EVENT ' + json.dumps({"
        "'type': 'frame', 'frame': frame, 'files': files}), flush=True)\n"
        "paused = os.path.exists(" + pause_file + ")\n"
        "if paused:\n"
        "    print('TH_BATCH_EVENT {\"type\":\"paused\"}', flush=True)\n"
        "while os.path.exists(" + pause_file + "):\n"
        "    time.sleep(0.2)\n"
        "if paused:\n"
        "    print('TH_BATCH_EVENT {\"type\":\"resumed\"}', flush=True)\n"
    )
    return "python({})".format(json.dumps(code))


emit("started")
try:
    cmds.file(SCENE, open=True, force=True, prompt=False)
    cmds.workspace(fileRule=("images", OUTPUT))
    cmds.workspace(fileRule=("depth", OUTPUT))
    if CAMERA:
        mel.eval("makeCameraRenderable({})".format(json.dumps(CAMERA)))

    hook_attribute = (
        "redshiftOptions.postRenderFrameMel"
        if cmds.getAttr("defaultRenderGlobals.currentRenderer") == "redshift"
        else "defaultRenderGlobals.postRenderMel"
    )
    old_hook = cmds.getAttr(hook_attribute) or ""
    old_hook = old_hook.rstrip("; \t\r\n")
    cmds.setAttr(
        hook_attribute,
        old_hook + (";\n" if old_hook else "") + frame_hook(),
        type="string",
    )
    cmds.setAttr("defaultRenderGlobals.renderAll", 1)
    set_render_attribute("animation", 1)
    set_render_attribute("byFrameStep", 1)

    for start, end in RANGES:
        set_render_attribute("startFrame", start)
        set_render_attribute("endFrame", end)
        emit("range_started", start=start, end=end)
        mel.eval('setMayaSoftwareLayers("", "")')
        mel.eval("setImageSizePercent(-1)")
        mel.eval('mayaBatchRenderProcedure(0, "", "", "", "")')
        emit("range_completed", start=start, end=end)

    emit("completed")
    mel.eval("quit -abort -force -exitCode 0")
except Exception as error:
    emit(
        "failed",
        error="{}: {}".format(type(error).__name__, error),
        traceback=traceback.format_exc(),
    )
    mel.eval("quit -abort -force -exitCode 210")
'''


def _maya_runner_source(scene, output, camera, ranges, pause_file="") -> str:
    settings = (
        f"SCENE = {str(scene)!r}\n"
        f"OUTPUT = {str(output)!r}\n"
        f"CAMERA = {str(camera)!r}\n"
        f"RANGES = {list(map(tuple, ranges))!r}\n"
        f"PAUSE_FILE = {str(pause_file)!r}\n"
    )
    return settings + _MAYA_RUNNER_BODY


@contextmanager
def _render_invocation(job: dict, ranges):
    if not job.get("mayaBatch"):
        yield job["args"], None
        return

    with TemporaryDirectory(prefix="th_batch_") as directory:
        runner = Path(directory) / "runner.py"
        pause_file = Path(directory) / "paused"
        runner.write_text(
            _maya_runner_source(
                job["scene"],
                job["output"],
                job.get("camera", ""),
                ranges,
                pause_file,
            ),
            encoding="utf-8",
        )
        python = "import runpy; _result = runpy.run_path({!r}, run_name='__main__')".format(
            runner.as_posix()
        )
        args = [job["mayaBatch"], "-command", f"python({json.dumps(python)})"]
        yield args, pause_file


def _sync_pause_file(pause, pause_file) -> None:
    if pause_file is None:
        return
    if pause.is_set():
        if not pause_file.exists():
            pause_file.touch()
    elif pause_file.exists():
        pause_file.unlink()


class RenderProgress:
    """Track stable events emitted by our Maya runner."""

    def __init__(self, start: int, end: int, ranges=None):
        self.ranges = list(map(tuple, ranges or [(start, end)]))
        self.frame = None
        self.completed = 0
        self.fraction = 0.0
        self.error = ""
        self.wrapper_completed = False
        self.pause_state = ""
        self.files = []

    def feed(self, text: str) -> dict:
        previous_files = tuple(self.files)
        for line in text.splitlines():
            if line.startswith(_RENDER_EVENT_PREFIX):
                self._feed_event(line)
        progress = {
            "frame": self.frame if self.frame is not None else "",
            "framesDone": self.completed,
            "progress": min(0.99, self.fraction),
        }
        if self.pause_state:
            progress["pauseState"] = self.pause_state
        if tuple(self.files) != previous_files:
            progress.update(
                renderOutput=str(Path(self.files[-1]).parent),
                renderFiles=list(self.files),
            )
        return progress

    def _feed_event(self, line: str) -> None:
        try:
            event = json.loads(line.split(_RENDER_EVENT_PREFIX, 1)[1])
        except (json.JSONDecodeError, TypeError) as error:
            self.error = f"Invalid Maya batch event: {error}"
            return

        kind = event.get("type")
        if kind == "failed":
            self.error = event.get("error") or "Maya batch runner failed"
        elif kind == "completed":
            self.completed = self.total
            self.fraction = 1.0
            self.wrapper_completed = True
        elif kind in {"paused", "resumed"}:
            self.pause_state = kind
        elif kind in {"frame", "range_completed"}:
            value = event.get("frame", event.get("end"))
            try:
                frame = int(float(value))
            except (TypeError, ValueError, OverflowError):
                return
            position = self._frame_position(frame)
            if position is not None:
                self.frame = frame
                self.completed = max(self.completed, position + 1)
                self.fraction = max(self.fraction, self.completed / self.total)
            files = event.get("files")
            if isinstance(files, list):
                for path in map(str, files):
                    if not path:
                        continue
                    if path in self.files:
                        self.files.remove(path)
                    self.files.append(path)

    def _frame_position(self, frame):
        if frame is None:
            return None
        offset = 0
        for start, end in self.ranges:
            if start <= frame <= end:
                return offset + frame - start
            offset += end - start + 1
        return None

    @property
    def total(self):
        return max(1, sum(end - start + 1 for start, end in self.ranges))


def _stop_process_tree(process) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        result = subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=15,
            check=False,
        )
        if result.returncode:
            if process.poll() is None:
                process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)


def _report_render_progress(
    tracker,
    parsed_text: str,
    log_text: str,
    elapsed: float,
    pid: int,
) -> None:
    progress = tracker.feed(parsed_text)
    report_progress(
        {
            **progress,
            "text": log_text,
            "pid": pid,
            "elapsed": elapsed,
            "renderError": tracker.error,
        }
    )


def _render_result(
    exit_code,
    started,
    cancel,
    *,
    timed_out=False,
    error="",
    cancelled=None,
) -> dict:
    return {
        "exitCode": exit_code,
        "elapsed": time.monotonic() - started,
        "cancelled": cancel.is_set() if cancelled is None else cancelled,
        "timedOut": timed_out,
        "error": error,
    }


def _run_render_command(
    args,
    ranges,
    output,
    reader,
    cancel,
    timeout_minutes,
    render_started,
    require_completion,
    pause,
    pause_file,
):
    tracker = RenderProgress(ranges[0][0], ranges[-1][1], ranges)
    if os.name == "nt":
        options = {"creationflags": subprocess.CREATE_NO_WINDOW}
        if Path(args[0]).name.lower() == "mayabatch.exe":
            mayapy = Path(args[0]).with_name("mayapy.exe")
            handler = Path(__file__).with_name("scheduler_cer.py")
            options["env"] = {
                **os.environ,
                "MAYA_DEBUG_ENABLE_CRASH_REPORTING": "1",
                "MAYA_USER_CER_APP": subprocess.list2cmdline(
                    [str(mayapy), str(handler)]
                ),
            }
    else:
        options = {"start_new_session": True}
    _sync_pause_file(pause, pause_file)
    with subprocess.Popen(
        args,
        stdout=output,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        **options,
    ) as process:
        pending = ""
        timed_out = False
        elapsed = 0.0
        paused_at = None
        paused_for = 0.0
        try:
            while process.poll() is None:
                now = time.monotonic()
                if pause.is_set() and paused_at is None:
                    paused_at = now
                elif not pause.is_set() and paused_at is not None:
                    paused_for += now - paused_at
                    paused_at = None
                current_pause = now - paused_at if paused_at is not None else 0.0
                elapsed = now - render_started - paused_for - current_pause
                timed_out = bool(timeout_minutes and elapsed > timeout_minutes * 60)
                if cancel.is_set() or timed_out:
                    _stop_process_tree(process)
                _sync_pause_file(pause, pause_file)

                chunk = reader.read()
                pending += chunk
                lines = pending.split("\n")
                pending = lines.pop()
                _report_render_progress(
                    tracker,
                    "\n".join(lines),
                    chunk,
                    elapsed,
                    process.pid,
                )
                if tracker.wrapper_completed:
                    process.kill()
                elif tracker.error:
                    _stop_process_tree(process)
                cancel.wait(0.25)

            remainder = reader.read()
            tail = pending + remainder
            if tail:
                _report_render_progress(
                    tracker,
                    tail,
                    remainder,
                    elapsed,
                    process.pid,
                )
        finally:
            _stop_process_tree(process)
    code = 0 if tracker.wrapper_completed and not tracker.error else process.returncode
    if (
        require_completion
        and not cancel.is_set()
        and not timed_out
        and not tracker.error
        and not tracker.wrapper_completed
    ):
        code = code or -1
        tracker.error = "Maya batch runner exited without a completion event"
    return code, timed_out, tracker.error, elapsed


def _render_native(job: dict, timeout_minutes: int, cancel, pause=None) -> dict:
    """Run one owned Maya process for the shot and keep its complete output."""
    _check_cancel(cancel)
    pause = pause or threading.Event()
    ranges = _job_ranges(job)
    with open(job["logPath"], "wb") as output:
        started = time.monotonic()
        with _render_invocation(job, ranges) as (args, pause_file):
            header = "Command: " + subprocess.list2cmdline(args)
            preparation_errors = "\n".join(job.get("preparationErrors") or [])
            if preparation_errors:
                header += "\nPreparation errors:\n" + preparation_errors
            output.write(
                f"Started: {datetime.now().isoformat()}\n{header}\n\n".encode()
            )
            output.flush()
            with open(
                job["logPath"], "r", encoding="utf-8", errors="replace"
            ) as reader:
                reader.seek(0, os.SEEK_END)
                code, timed_out, error, _elapsed = _run_render_command(
                    args,
                    ranges,
                    output,
                    reader,
                    cancel,
                    timeout_minutes,
                    started,
                    bool(job.get("mayaBatch")),
                    pause,
                    pause_file,
                )
            if code or cancel.is_set() or timed_out or error:
                return _render_result(
                    code,
                    started,
                    cancel,
                    timed_out=timed_out,
                    error=error,
                )
    return _render_result(0, started, cancel, cancelled=False)




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


def _duration(seconds) -> str:
    if seconds is None:
        return "—"
    seconds = max(0, int(seconds))
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return (
        f"{hours:d}:{minutes:02d}:{seconds:02d}"
        if hours
        else f"{minutes:d}:{seconds:02d}"
    )


def _total_eta(estimates):
    if not estimates or any(value is None for value in estimates):
        return None
    return sum(estimates)
