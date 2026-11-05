"""Self-contained Niki Friends batch scheduler using the public Handler API."""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import threading
import time
import traceback
import uuid
import zipfile
from concurrent.futures import Future
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import (
    Property,
    QObject,
    Qt,
    QTimer,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QAction, QDesktopServices, QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine, qmlEngine

from tactic_handler_api import get_api
from tactic_handler_api.operations import Operation, report_progress
from thlib.ui.workspace_models.records import RecordListModel

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
        "render_timeout_minutes": 0,
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


def _query_episodes(api, project_code: str, config: dict) -> list[dict]:
    api.repositories.list()
    project = api.project(project_code)
    stype = project.stype(config["episode_search_type"])
    workflow = project.workflow()
    episodes = list(
        stype.query(
            order_by=["name"],
            limit=1000,
        ).items
    )
    records = []
    for episode in episodes:
        tasks = episode.tasks(config["render_process"])
        task = tasks[-1] if tasks else None
        status = str(task.get_value("status") or "") if task else ""
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
                "queued": status in set(config["queue_statuses"]),
            }
        )
    return records


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


def _sync_episode_files(api, episode, preset, cancel) -> None:
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
        api.files.ensure_local(file, overwrite="overwrite")


def _sync_alembic_caches(api, episode, config, cancel) -> None:
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
        archive = api.files.ensure_local(file, overwrite="overwrite")
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
    _sync_episode_files(api, episode, preset, cancel)
    _sync_alembic_caches(api, episode, config, cancel)
    return {}


def _sync_shot_cache(api, snapshots, entry, job, config, cancel) -> None:
    cache = _main_file(snapshots, config["cache_process"])
    if cache is None:
        return
    report_progress({"stage": "Downloading shot cache"})
    archive = api.files.ensure_local(cache, overwrite="overwrite")
    _check_cancel(cancel)
    if not zipfile.is_zipfile(archive):
        return
    report_progress({"stage": "Extracting shot cache"})
    cache_root = (Path(cache.get_repo_path()) / config["cache_path"]).resolve()
    destination = (cache_root / entry["title"] / job["title"]).resolve()
    if not destination.is_relative_to(cache_root):
        raise ValueError(f"Cache destination is outside its root: {destination}")
    _safe_extract(archive, destination, cancel)


def _render_commands(executable, scene, output, camera, ranges):
    commands = []
    for start, end in ranges:
        args = [
            str(executable),
            "-renderer",
            "file",
            "-s",
            str(start),
            "-e",
            str(end),
        ]
        if camera:
            args.extend(("-cam", camera))
        args.extend(("-rd", str(output), str(scene)))
        commands.append(args)
    return commands


def _prepare_shot(api, entry: dict, job: dict, config: dict, cancel) -> dict:
    _check_cancel(cancel)
    executable = Path(config["maya_render_executable"])
    if not executable.is_file():
        raise FileNotFoundError(f"Maya Render executable not found: {executable}")
    shot = api.sobject(job["shotKey"])
    snapshots = shot.snapshots()
    _sync_shot_cache(api, snapshots, entry, job, config, cancel)
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
    range_args = _render_commands(
        executable,
        scene,
        output,
        config.get("camera"),
        _job_ranges(job),
    )
    return {
        "scene": str(scene),
        "output": str(output),
        "logPath": str(log_path),
        "args": range_args[0],
        "rangeArgs": range_args,
        "command": "\n".join(map(subprocess.list2cmdline, range_args)),
        "previewUrl": _preview_url(snapshots),
    }


# Maya renderer process


class RenderProgress:
    """Frame-aware estimates; percentages are never treated as whole-job completion."""

    def __init__(self, start: int, end: int):
        self.start, self.end = start, end
        self.frame = None
        self.completed = 0
        self.fraction = 0.0
        self.error = ""

    def feed(self, text: str) -> dict:
        for line in text.splitlines():
            # Maya can report final failure while Render.exe remains alive.
            if re.search(r"\bScene\s+.+\s+failed to render\.?\s*$", line, re.I):
                self.error = line.strip()
            match = re.search(
                r"(?:rendering\s+(?:frame\s*)?|frame\s*[=:]?\s*)(-?\d+)\b",
                line,
                re.I,
            )
            if match:
                frame = int(match.group(1))
                if self.start <= frame <= self.end:
                    self.frame = frame
                    done = frame - self.start
                    if re.search(r"finished|completed|done", line, re.I):
                        done += 1
                    self.completed = max(self.completed, done)
                    self.fraction = max(self.fraction, done / self.total)
            percent = re.search(
                r"\b(\d+(?:\.\d+)?)\s*%\s*(?:done|rendered|complete)", line, re.I
            )
            if percent and self.frame is not None:
                fraction = (
                    self.frame - self.start + min(100, float(percent.group(1))) / 100
                ) / self.total
                self.fraction = max(self.fraction, min(1.0, fraction))
        return {
            "frame": self.frame if self.frame is not None else "",
            "framesDone": self.completed,
            "progress": min(0.99, self.fraction),
        }

    @property
    def total(self):
        return max(1, self.end - self.start + 1)


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
    completed_frames: int,
    total_frames: int,
    elapsed: float,
    pid: int,
) -> None:
    progress = tracker.feed(parsed_text)
    overall = completed_frames + progress["progress"] * tracker.total
    report_progress(
        {
            **progress,
            "text": log_text,
            "pid": pid,
            "elapsed": elapsed,
            "renderError": tracker.error,
            "framesDone": completed_frames + progress["framesDone"],
            "progress": min(0.99, overall / total_frames),
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
    frame_range,
    output,
    reader,
    cancel,
    timeout_minutes,
    render_started,
    completed_frames,
    total_frames,
):
    start, end = frame_range
    tracker = RenderProgress(start, end)
    options = (
        {"creationflags": subprocess.CREATE_NO_WINDOW}
        if os.name == "nt"
        else {"start_new_session": True}
    )
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
        try:
            while process.poll() is None:
                elapsed = time.monotonic() - render_started
                timed_out = bool(timeout_minutes and elapsed > timeout_minutes * 60)
                if cancel.is_set() or timed_out:
                    _stop_process_tree(process)

                chunk = reader.read()
                pending += chunk
                lines = pending.split("\n")
                pending = lines.pop()
                _report_render_progress(
                    tracker,
                    "\n".join(lines),
                    chunk,
                    completed_frames,
                    total_frames,
                    elapsed,
                    process.pid,
                )
                if tracker.error:
                    _stop_process_tree(process)
                cancel.wait(0.25)

            remainder = reader.read()
            tail = pending + remainder
            if tail:
                _report_render_progress(
                    tracker,
                    tail,
                    remainder,
                    completed_frames,
                    total_frames,
                    elapsed,
                    process.pid,
                )
        finally:
            _stop_process_tree(process)
    return process.returncode, timed_out, tracker.error, elapsed


def _render_native(job: dict, timeout_minutes: int, cancel) -> dict:
    """Run only this Render process tree, keeping its complete output on disk."""
    _check_cancel(cancel)
    ranges = _job_ranges(job)
    commands = job.get("rangeArgs") or [job["args"]]
    if len(commands) != len(ranges):
        raise ValueError("Render command count does not match frame ranges")

    total_frames = _job_frame_count(job)
    completed_frames = 0
    started = time.monotonic()
    with open(job["logPath"], "wb") as output:
        header = "\n".join(
            f"Command {index + 1}/{len(commands)}: {subprocess.list2cmdline(args)}"
            for index, args in enumerate(commands)
        )
        output.write(f"Started: {datetime.now().isoformat()}\n{header}\n\n".encode())
        output.flush()
        with open(job["logPath"], "r", encoding="utf-8", errors="replace") as reader:
            for frame_range, args in zip(ranges, commands):
                if cancel.is_set():
                    return _render_result(-1, started, cancel)
                code, timed_out, error, elapsed = _run_render_command(
                    args,
                    frame_range,
                    output,
                    reader,
                    cancel,
                    timeout_minutes,
                    started,
                    completed_frames,
                    total_frames,
                )
                if code or cancel.is_set() or timed_out or error:
                    return _render_result(
                        code,
                        started,
                        cancel,
                        timed_out=timed_out,
                        error=error,
                    )
                completed_frames += frame_range[1] - frame_range[0] + 1
                report_progress(
                    {
                        "frame": frame_range[1],
                        "framesDone": completed_frames,
                        "progress": min(0.99, completed_frames / total_frames),
                        "elapsed": elapsed,
                    }
                )
    return _render_result(0, started, cancel, cancelled=False)


def _repository_code(api) -> str:
    for repository in api.repositories.list():
        values = repository.get("value") or []
        if len(values) > 4 and values[4]:
            return str(values[3])
    raise RuntimeError("No active repository is configured")


def _finalize_shot(api, entry: dict, job: dict, config: dict) -> None:
    shot = api.sobject(job["shotKey"])
    if job["result"] != "cancelled":
        shot.set_value(config["rendered_field"], job["result"] == "completed")
        shot.commit()
    if job.get("logPath") and Path(job["logPath"]).is_file():
        item = api.commit_queue(shot.get_project().get_code()).add(
            api.sobject(entry["episodeKey"]),
            context=f"{config['render_process']}/{job['title']}",
            files=[Path(job["logPath"])],
            repository=_repository_code(api),
            description=f"Log file for Shot {job['title']}",
            generate_previews=False,
        )
        item.commit()


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


# Queue controller


_TERMINAL = {"completed", "failed", "cancelled", "skipped"}
_ACTIVE = {"preparing", "rendering", "saving", "stopping"}
_IDLE = {"waiting", "held"}
_RETRYABLE = {"failed", "cancelled"}
_RUNNABLE = _IDLE | _RETRYABLE


class BatchDispatcherController(QObject):
    stateChanged = Signal()
    settingsChanged = Signal()
    queueChanged = Signal()
    episodeFiltersChanged = Signal()
    queueSelected = Signal(int, bool)
    episodeSelected = Signal(int)
    logChanged = Signal()
    logScopeChanged = Signal()
    windowCloseRequested = Signal()
    _dispatchRequested = Signal(object)

    def __init__(
        self,
        api,
        project_code: str,
        manifest: dict | None = None,
        *,
        settings: dict | None = None,
        offline: bool = False,
    ):
        super().__init__()
        self._api = api
        self._project_code = project_code
        self._config = deepcopy((manifest or BATCH_DISPATCHER_CONFIG)["project_config"])
        self._config.update(settings or {})
        self._offline = offline
        self._ready = offline
        self._closing = False
        self._close_requested = False
        self._operations = {}
        self._entries = []
        self._events = []
        self._selected_episode = ""
        self._selected_queue = ""
        self._run_only = ""
        self._active_entry = None
        self._active_job = None
        self._discovery_entry = None
        self._stage_operation = None
        self._cancel = threading.Event()
        self._cancel_job_only = False
        self._paused = True
        self._auto_clear_finished = False
        self._watch_server = False
        self._server_seen = set()
        self._generation = 0
        self._busy = False
        self._status = "Queue paused"
        self._error = ""
        self._window = None
        self._tray = None
        self._last_tick = time.monotonic()
        self._pending_save = None
        self._saving = False
        self._write_blocked = False
        self.episodes = RecordListModel(
            (
                "title",
                "searchKey",
                "code",
                "selected",
                "subtitle",
                "previewUrl",
                "renderStatus",
                "statusColor",
                "statusChoices",
                "queued",
            ),
            identity_role="searchKey",
        )
        self.queue = RecordListModel(
            (
                "jobId",
                "parentId",
                "title",
                "subtitle",
                "state",
                "stage",
                "selected",
                "expanded",
                "progress",
                "frames",
                "elapsed",
                "eta",
                "depth",
                "test",
                "attempt",
                "pid",
                "error",
                "indeterminate",
                "previewUrl",
                "included",
                "actions",
            ),
            identity_role="jobId",
        )
        self.episode_filters = RecordListModel(
            ("value", "title", "statusAccent", "count", "active")
        )
        self._refresh_episode_filters()
        self.episodes.contentReplaced.connect(self._refresh_episode_filters)
        self._dispatchRequested.connect(
            self._invoke, Qt.ConnectionType.QueuedConnection
        )
        self._poll_timer = QTimer(self)
        self._poll_timer.setSingleShot(True)
        self._poll_timer.timeout.connect(self.refresh)
        self._clock = QTimer(self)
        self._clock.setInterval(1000)
        self._clock.timeout.connect(self._tick)
        self._clock.start()

    @Slot(object)
    def _invoke(self, callback):
        if not self._closing:
            callback()

    def _submit(self, function, done, failed=None, progress=None):
        try:
            operation = self._api.submit(function)
        except Exception as error:
            future = Future()
            future.set_exception(error)
            operation = Operation(future)
        subscriptions = []
        self._operations[operation.id] = (operation, subscriptions)

        def finish(callback, value):
            entry = self._operations.pop(operation.id, None)
            if entry:
                for subscription in entry[1]:
                    subscription.close()
            if self._closing:
                return
            try:
                callback(value)
            except Exception as error:
                if callback is done and failed is not None:
                    failed(error)
                else:
                    self._error_message(error)
            self._maybe_close()

        subscriptions.append(
            operation.on_done(
                lambda value: finish(done, value),
                dispatch=self._dispatchRequested.emit,
            )
        )
        subscriptions.append(
            operation.on_error(
                lambda error: finish(failed or self._error_message, error),
                dispatch=self._dispatchRequested.emit,
            )
        )
        if progress:
            # Capture progress before Operation closes its subscriptions on
            # completion. Already-posted final output must still reach Qt.
            def received(value):
                self._dispatchRequested.emit(
                    lambda: (
                        progress(value) if operation.id in self._operations else None
                    )
                )

            subscriptions.append(operation.on_progress(received))
        return operation

    # QML state

    @Property(QObject, constant=True)
    def episodesModel(self):
        return self.episodes

    @Property(QObject, constant=True)
    def queueModel(self):
        return self.queue

    @Property(bool, notify=stateChanged)
    def ready(self):
        return self._ready

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._busy

    @Property(bool, notify=stateChanged)
    def running(self):
        return self._stage_operation is not None

    @Property(bool, notify=stateChanged)
    def paused(self):
        return self._paused

    @Property(bool, notify=stateChanged)
    def schedulerRunning(self):
        return self._watch_server

    @Property(bool, notify=stateChanged)
    def autoClearFinished(self):
        return self._auto_clear_finished

    @Property(QObject, constant=True)
    def episodeFiltersModel(self):
        return self.episode_filters

    @Property("QVariantList", notify=episodeFiltersChanged)
    def visibleEpisodeStatuses(self):
        return [
            row["value"]
            for row in self.episode_filters.records()
            if row["active"]
        ]

    def _refresh_episode_filters(self):
        records = self.episodes.records()
        statuses = list(self._config["status_options"])
        for row in records:
            status = row.get("renderStatus", "")
            if status not in statuses:
                statuses.append(status)

        current = {
            row["value"]: row["active"]
            for row in self.episode_filters.records()
        }
        colors = {
            choice["title"]: choice.get("accent", "")
            for row in records
            for choice in row.get("statusChoices", [])
        }
        self.episode_filters.replace(
            [
                {
                    "value": status,
                    "title": status or "Без задачи",
                    "statusAccent": colors.get(status, ""),
                    "count": sum(
                        row.get("renderStatus", "") == status for row in records
                    ),
                    "active": current.get(
                        status, status != self._config["terminal_status"]
                    ),
                }
                for status in statuses
            ]
        )
        self.episodeFiltersChanged.emit()

    @Slot(str)
    def toggleEpisodeStatusFilter(self, status):
        records = self.episode_filters.records()
        row = next(
            (index for index, value in enumerate(records) if value["value"] == status),
            -1,
        )
        if row < 0:
            return
        self.episode_filters.set_value(row, "active", not records[row]["active"])
        self.episodeFiltersChanged.emit()

    @Slot(bool)
    def setAutoClearFinished(self, enabled):
        self._auto_clear_finished = bool(enabled)
        if enabled:
            self.clearCompleted()
        self.stateChanged.emit()

    @Property(str, notify=stateChanged)
    def statusText(self):
        return _ui_text(self._status)

    @Property(str, notify=stateChanged)
    def errorText(self):
        return self._error

    @Property(bool, notify=stateChanged)
    def closePending(self):
        return self._close_requested

    @Slot(int, result="QVariantList")
    def episodeStatusChoices(self, row):
        return self.episodes.get(row).get("statusChoices") or [
            {"title": value} for value in self._config["status_options"]
        ]

    @Property("QVariantMap", notify=settingsChanged)
    def settings(self):
        return {
            "mayaPath": self._config["maya_render_executable"],
            "savePath": self._config["output_directory"],
            "camera": self._config["camera"],
            "stopOnError": self._config.get("stop_on_error", False),
            "timeout": self._config.get("render_timeout_minutes", 0),
        }

    @Property("QVariantMap", notify=queueChanged)
    def summary(self):
        jobs = [job for entry in self._entries for job in entry["jobs"]]
        pending = sum(job["state"] not in _TERMINAL for job in jobs)
        completed = sum(job["state"] == "completed" for job in jobs)
        failed = sum(job["state"] == "failed" for job in jobs)
        total = sum(_job_frame_count(job) for job in jobs if job["state"] != "skipped")
        done = sum(
            _job_frame_count(job) * self._job_fraction(job)
            for job in jobs
            if job["state"] != "skipped"
        )
        frame_seconds = self._frame_seconds()
        estimates = [
            self._job_eta(job, frame_seconds)
            for job in jobs
            if job["state"] not in _TERMINAL
        ]
        eta = _total_eta(estimates)
        return {
            "episodes": len(self._entries),
            "shots": len(jobs),
            "pending": pending,
            "completed": completed,
            "failed": failed,
            "progress": done / total if total else 0,
            "elapsed": _duration(
                sum(entry.get("elapsed", 0) for entry in self._entries)
            ),
            "eta": ("~" + _duration(eta)) if eta is not None else "—",
        }

    def _find(self, identity):
        for entry in self._entries:
            if entry["id"] == identity:
                return entry, None
            for job in entry["jobs"]:
                if job["id"] == identity:
                    return entry, job
        return None, None

    @Property("QVariantMap", notify=queueChanged)
    def selectedDetail(self):
        entry, job = self._find(self._selected_queue)
        if entry is None:
            return {}
        row = job or entry
        frame_spec = (
            row.get("frameSpec") or _format_frame_ranges(_job_ranges(row))
            if job
            else ""
        )
        return {
            "id": row["id"],
            "title": row["title"],
            "state": row["state"],
            "stage": _ui_text(row.get("stage", "")),
            "error": row.get("error", ""),
            "command": row.get("command", ""),
            "scene": row.get("scene", ""),
            "output": row.get("output", self._config["output_directory"]),
            "logPath": row.get("logPath", ""),
            "exitCode": row.get("exitCode", ""),
            "pid": row.get("pid", ""),
            "attempt": row.get("attempt", 1),
            "elapsed": _duration(row.get("elapsed", 0)),
            "frameSpec": frame_spec,
            "frames": f"{row.get('frame', '—')} / {frame_spec}" if job else "",
            "test": entry["test"],
            "child": bool(job),
            "actions": self._allowed_actions(entry, job),
        }

    def _allowed_actions(self, entry, job=None):
        if not self._ready or self._close_requested:
            return []

        row = job or entry
        state = row["state"]
        targets = [job] if job else entry["jobs"]
        entry_busy = entry["state"] in _ACTIVE | {"discovering"}
        allowed = set()

        if state in _IDLE:
            allowed.add("hold")
            if (job is None and entry["state"] not in _ACTIVE) or (
                job is not None and job is not self._active_job
            ):
                allowed.add("move")
        if state not in _TERMINAL:
            allowed.add("cancel")
        if job is not None and state in _IDLE | {"skipped"}:
            include_locked = entry["state"] == "saving" or entry.get("saveFailed")
            if not include_locked:
                allowed.add("include")

        if job is None and self._entry_is_removable(entry):
            allowed.add("remove")

        save_failed = entry.get("saveFailed") or any(
            target.get("saveFailed") for target in targets
        )
        if not save_failed and not entry_busy:
            allowed.update(self._rerun_actions(entry, job, targets))
        return sorted(allowed)

    def _rerun_actions(self, entry, job, targets):
        state = (job or entry)["state"]
        allowed = set()
        retryable = state in _RETRYABLE
        if job is None:
            retryable |= any(target["state"] in _RETRYABLE for target in targets)
        if retryable:
            allowed.add("retry")

        if job is not None and not entry["test"] and state in _RUNNABLE | {"skipped"}:
            allowed.add("frames")

        runnable = any(target["state"] in _RUNNABLE for target in targets)
        runnable |= job is not None and state == "skipped"
        if not self.running and runnable:
            allowed.add("only")
        return allowed

    def _entry_is_removable(self, entry):
        if entry["state"] in _ACTIVE | {"discovering"}:
            return False
        if entry is self._active_entry or entry is self._discovery_entry:
            return False
        identities = {entry["id"]}
        identities.update(job["id"] for job in entry["jobs"])
        return self._run_only not in identities

    @Property(str, notify=logChanged)
    def logText(self):
        entry, job = self._find(self._selected_queue)
        return "\n".join(
            text
            for entry_id, job_id, text in self._events
            if entry is None
            or (entry_id == entry["id"] and (job is None or job_id == job["id"]))
        )

    def _log(self, text, entry=None, job=None):
        text = str(text).rstrip()
        if not text:
            return
        self._events.append(
            (
                (entry or {}).get("id", ""),
                (job or {}).get("id", ""),
                f"[{datetime.now().strftime('%H:%M:%S')}] {text}",
            )
        )
        # The UI retains complete events; renderer output is also kept on disk.
        self._events = self._events[-1000:]
        self.logChanged.emit()

    def _error_message(self, error):
        self._error = str(error)
        self._log(
            "".join(traceback.format_exception(error)).strip(),
            self._active_entry,
            self._active_job,
        )
        self.stateChanged.emit()

    # Persistence and TACTIC discovery

    def initialize(self):
        if self._offline:
            self.stateChanged.emit()
            return
        self._submit(
            self._load_saved_state,
            self._state_loaded,
            self._state_load_failed,
        )

    def _load_saved_state(self):
        # Scope durable work to the same endpoint and project.
        import hashlib

        from thlib.environment import env_read_config, env_server
        from thlib.ui.server_address import normalize_tactic_server_url

        endpoint = normalize_tactic_server_url(env_server.get_server())
        scope = (
            hashlib.sha256(endpoint.encode()).hexdigest()[:16]
            + "/"
            + self._project_code
        )
        settings = (
            env_read_config(
                filename="ui_batch_dispatcher",
                unique_id=self._project_code,
                long_abs_path=True,
            )
            or {}
        )
        queue = (
            env_read_config(
                filename="batch_queue",
                unique_id="cache/" + scope,
                long_abs_path=True,
            )
            or {}
        )
        return settings, queue, scope

    def _state_loaded(self, payload):
        settings, queue, self._scope = payload
        self._config.update(
            {key: value for key, value in settings.items() if key in self._config}
        )
        if queue and queue.get("version") != 1:
            raise ValueError(
                "Unknown batch queue format; saved queue has not been overwritten"
            )
        self._entries = queue.get("entries", [])
        for entry in self._entries:
            if entry["state"] not in _TERMINAL:
                entry.update(
                    state="held",
                    restored=True,
                    stage="Restored · resume or retry explicitly",
                )
            for job in entry["jobs"]:
                if job["state"] in _ACTIVE:
                    job.update(
                        state="failed",
                        stage="Interrupted session",
                        pid="",
                        error="Interrupted session; verify output before retrying",
                    )
            entry["prepared"] = False
        self._server_seen = set(queue.get("serverSeen", []))
        self._ready = True
        self._publish_queue()
        self.settingsChanged.emit()
        self.stateChanged.emit()
        self.refresh()

    def _state_load_failed(self, error):
        self._write_blocked = True
        self._error_message(error)

    def _persist(self):
        if self._offline or not self._ready or self._write_blocked:
            return
        self._pending_save = {
            "version": 1,
            "entries": deepcopy(self._entries),
            "serverSeen": sorted(self._server_seen),
        }
        self._save_next()

    def _flush_queue(self):
        self._publish_queue()
        self._persist()

    def _save_next(self):
        if self._saving or self._pending_save is None:
            return
        from thlib.environment import env_write_config

        payload, self._pending_save = self._pending_save, None
        self._saving = True
        self._submit(
            lambda: env_write_config(
                payload,
                filename="batch_queue",
                unique_id="cache/" + self._scope,
                long_abs_path=True,
            ),
            self._queue_saved,
            self._queue_save_failed,
        )

    def _queue_saved(self, _value):
        self._saving = False
        self._save_next()
        self._maybe_close()

    def _queue_save_failed(self, error):
        self._saving = False
        self._paused = True
        self._error_message(error)
        self._maybe_close()

    @Slot()
    def refresh(self):
        if self._offline or self._busy or not self._ready or self._close_requested:
            return
        self._poll_timer.stop()
        self._generation += 1
        generation = self._generation
        self._busy = True
        self.stateChanged.emit()
        config = dict(self._config)
        self._submit(
            lambda: _query_episodes(self._api, self._project_code, config),
            lambda payload: self._episodes_ready(generation, payload),
            lambda error: self._refresh_failed(generation, error),
        )

    def _refresh_failed(self, generation, error):
        if generation != self._generation:
            return
        self._busy = False
        self._error_message(error)
        self._schedule_poll()

    def _schedule_poll(self):
        if self._watch_server and not self._close_requested:
            self._poll_timer.start(max(5, int(self._config["update_interval"])) * 1000)

    def _episodes_ready(self, generation, records):
        if generation != self._generation:
            return
        for row in records:
            row["selected"] = row["searchKey"] == self._selected_episode
        previews = {row["searchKey"]: row.get("previewUrl", "") for row in records}
        for entry in self._entries:
            if entry["episodeKey"] in previews:
                entry["previewUrl"] = previews[entry["episodeKey"]]
        if self._entries:
            self._publish_queue()
        self.episodes.replace(records)
        self._busy = False
        previous_seen = set(self._server_seen)
        queued = {row["searchKey"] for row in records if row["queued"]}
        self._server_seen.intersection_update(
            queued
            | {
                entry["episodeKey"]
                for entry in self._entries
                if entry["state"] not in _TERMINAL
            }
        )
        if self._watch_server:
            for row in records:
                if row["queued"] and row["searchKey"] not in self._server_seen:
                    self._server_seen.add(row["searchKey"])
                    self._enqueue(row["searchKey"], False, origin="server")
        if self._server_seen != previous_seen:
            self._persist()
        self.stateChanged.emit()
        self._schedule_poll()

    @Slot(int)
    def selectEpisode(self, row):
        key = self.episodes.get(row).get("searchKey")
        if not key:
            return
        entry = next(
            (entry for entry in reversed(self._entries) if entry["episodeKey"] == key),
            None,
        )
        if entry:
            entry["expanded"] = True
            self.selectQueue(entry["id"], True)
        else:
            self._selected_queue = ""
            self._select_episode(key)
            self._publish_queue()
            self.queueSelected.emit(-1, False)
            self.logScopeChanged.emit()
            self.logChanged.emit()
            self._status = "Use + to add this episode to the queue"
            self.stateChanged.emit()

    @Slot(int, bool)
    def renderEpisode(self, row, test_render=False):
        key = self.episodes.get(row).get("searchKey")
        if key:
            self._enqueue(key, bool(test_render))

    def _enqueue(self, key, test_render, origin="manual"):
        if not self._ready or self._close_requested:
            return
        existing = next(
            (
                entry
                for entry in self._entries
                if entry["episodeKey"] == key and entry["state"] not in _TERMINAL
            ),
            None,
        )
        if existing:
            self.selectQueue(existing["id"])
            self._status = "Episode already queued"
            self.stateChanged.emit()
            return
        if len(self._entries) >= 200:
            self._error_message(
                ValueError("Queue history is full; clear completed entries")
            )
            return
        episode = self.episodes.lookup("searchKey", key)
        entry = _queue_entry(key, episode, test_render, origin)
        self._entries.append(entry)
        if not test_render:
            self._server_seen.add(key)
        self.selectQueue(entry["id"])
        self._discover_entry(entry)

    def _discover_entry(self, entry):
        config = dict(self._config)
        entry.update(state="discovering", stage="Loading shot list", error="")
        self._flush_queue()
        if self._discovery_entry is not None:
            return
        self._discovery_entry = entry
        status = config["queue_statuses"][-1] if (entry["origin"] == "manual") else ""
        self._submit(
            lambda: _discover_queue(
                self._api, entry["episodeKey"], config, entry["test"], status
            ),
            lambda records: self._discovery_finished(entry, records),
            lambda error: self._discovery_failed(entry, error),
        )

    def _discovery_finished(self, entry, records):
        try:
            if entry not in self._entries or entry["state"] == "cancelled":
                return
            jobs = [_shot_job(row, entry["test"]) for row in records]
            if not jobs:
                raise ValueError("No shots to render")
            entry.update(jobs=jobs, state="waiting", stage="Waiting")
            self._log(f"{entry['title']}: {len(jobs)} shots queued", entry)
            self._flush_queue()
            self._pump()
        except Exception as error:
            self._mark_discovery_failed(entry, error)
        finally:
            self._continue_discovery(entry)

    def _discovery_failed(self, entry, error):
        try:
            self._mark_discovery_failed(entry, error)
        finally:
            self._continue_discovery(entry)

    def _mark_discovery_failed(self, entry, error):
        if entry not in self._entries or entry["state"] == "cancelled":
            return
        entry.update(state="failed", stage="Discovery failed", error=str(error))
        self._error_message(error)
        self._flush_queue()
        self._pump()

    def _continue_discovery(self, entry):
        if self._discovery_entry is entry:
            self._discovery_entry = None
        pending = next(
            (row for row in self._entries if row["state"] == "discovering"),
            None,
        )
        if pending is not None and not self._close_requested:
            self._discover_entry(pending)

    # Queue execution

    @Slot()
    def startScheduler(self):
        if not self._ready or self._close_requested:
            return
        self._run_only = ""
        self._paused = False
        self._status = "Queue running"
        self._error = ""
        for entry in self._entries:
            if entry["state"] == "held" and entry.pop("restored", False):
                entry["state"] = "waiting"
        self.stateChanged.emit()
        self._publish_queue()
        self._pump()

    @Slot()
    def stopScheduler(self):
        self._paused = True
        self._status = "Pause after current shot" if self.running else "Queue paused"
        self.stateChanged.emit()

    @Slot()
    def toggleScheduler(self):
        self.startScheduler() if self._paused else self.stopScheduler()

    @Slot(str)
    def runOnly(self, identity):
        entry, job = self._find(identity)
        if entry is None or "only" not in self._allowed_actions(entry, job):
            return
        self.stopScheduler()
        self._run_only = ""
        self._active_entry = None
        self.retryQueue(identity)
        row = job or entry
        if job and job["state"] == "skipped":
            self.toggleIncluded(job["id"])
        for target in [job] if job else entry["jobs"]:
            if target["state"] == "held":
                self.holdQueue(target["id"])
        if entry["state"] == "held":
            self.holdQueue(entry["id"])
        if entry["state"] in _TERMINAL:
            entry.update(state="waiting", stage="Waiting", prepared=False, error="")
        self._run_only = row["id"]
        self._paused = False
        self._status = f"Запуск только: {row['title']}"
        self._error = ""
        self.selectQueue(row["id"])
        self.stateChanged.emit()
        self._pump()

    @Slot(bool)
    def watchServer(self, enabled):
        self._watch_server = bool(enabled)
        self.stateChanged.emit()
        if enabled:
            self.refresh()
        else:
            self._poll_timer.stop()

    def _pause_finished_run_only(self, entry, job) -> bool:
        if not self._run_only:
            return False
        unfinished = (
            entry is not None
            and entry["state"] not in _TERMINAL | {"held"}
            and (job is None or job["state"] not in _TERMINAL | {"held"})
        )
        if unfinished:
            return False
        self._run_only = ""
        if entry is not None and job is not None:
            entry["prepared"] = False
        self._active_entry = None
        self._paused = True
        self._status = "Selected work finished · queue paused"
        self._flush_queue()
        self.stateChanged.emit()
        return True

    def _start_episode_preparation(self, entry, single_shot: bool) -> None:
        entry.update(state="preparing", stage="Synchronizing episode")
        config = dict(self._config)
        saved = deepcopy(entry)
        saved["singleShot"] = single_shot
        self._run_stage(
            lambda: _prepare_episode(self._api, saved, config, self._cancel),
            self._episode_prepared,
        )

    def _start_shot_preparation(self, entry, job) -> None:
        self._active_job = job
        job.update(state="preparing", stage="Preparing shot", error="")
        entry.update(
            state="preparing",
            stage=f"Подготовка: {job['title']}",
        )
        config = dict(self._config)
        saved_entry = deepcopy(entry)
        saved_job = deepcopy(job)
        self._run_stage(
            lambda: _prepare_shot(
                self._api, saved_entry, saved_job, config, self._cancel
            ),
            self._shot_prepared,
        )

    def _next_entry(self, preferred):
        entry = preferred or next(
            (row for row in self._entries if row["state"] == "waiting"), None
        )
        if entry is None:
            self._show_idle_status()
            return None
        self._active_entry = entry
        self._cancel = threading.Event()
        self._cancel_job_only = False
        return entry

    def _show_idle_status(self):
        states = {entry["state"] for entry in self._entries}
        if "discovering" in states:
            self._status = "Loading queued shots"
        elif "held" in states:
            self._status = "Waiting · held jobs remain"
        elif self._watch_server:
            self._status = "Waiting for jobs"
        else:
            self._status = "Queue finished"
        self.stateChanged.emit()

    def _finish_or_hold_entry(self, entry):
        if any(job["state"] == "held" for job in entry["jobs"]):
            entry.update(state="held", stage="Contains held shots")
            self._active_entry = None
            self._flush_queue()
            self._pump()
            return
        self._finish_entry()

    def _run_scope(self):
        if not self._run_only:
            return None, None
        return self._find(self._run_only)

    @staticmethod
    def _entry_finished(entry):
        return (
            entry is not None
            and bool(entry["jobs"])
            and all(job["state"] in _TERMINAL for job in entry["jobs"])
        )

    @staticmethod
    def _next_job(entry, preferred):
        if preferred is not None:
            return preferred
        return next((job for job in entry["jobs"] if job["state"] == "waiting"), None)

    def _pump(self):
        if self._stage_operation is not None:
            return
        scope_entry, scope_job = self._run_scope()
        if self._pause_finished_run_only(scope_entry, scope_job):
            return

        entry = self._active_entry
        # Pausing prevents the next shot, not finalizing work already finished.
        if self._entry_finished(entry):
            self._finish_entry()
            return
        if entry is not None and entry["state"] == "held":
            self._active_entry = entry = None
        if self._paused or self._close_requested:
            return
        if entry is None:
            entry = self._next_entry(scope_entry)
            if entry is None:
                return
        if not entry["jobs"]:
            self._active_entry = None
            self._discover_entry(entry)
            return
        pending = self._next_job(entry, scope_job)
        if pending is None:
            self._finish_or_hold_entry(entry)
            return
        if not entry["prepared"]:
            self._start_episode_preparation(entry, scope_job is not None)
            return
        self._start_shot_preparation(entry, pending)

    def _run_stage(self, function, done):
        self._last_tick = time.monotonic()
        self._flush_queue()

        def execute():
            try:
                return function()
            except InterruptedError as cancellation:
                return cancellation

        def completed(value):
            self._tick()
            self._stage_operation = None
            try:
                if isinstance(value, InterruptedError):
                    self._stage_failed(value)
                else:
                    done(value)
            except Exception as error:
                self._stage_failed(error)
            self.stateChanged.emit()
            self._maybe_close()

        def failed(error):
            self._tick()
            self._stage_operation = None
            self._stage_failed(error)
            self._maybe_close()

        self._stage_operation = self._submit(
            execute, completed, failed, self._stage_progress
        )
        self.stateChanged.emit()

    def _stage_progress(self, payload):
        entry, job = self._active_entry, self._active_job
        if entry is None:
            return
        row = job or entry
        if "stage" in payload and not self._cancel.is_set():
            row["stage"] = _ui_text(payload["stage"]) + (
                " · " + payload["detail"] if payload.get("detail") else ""
            )
        if job is not None:
            self._update_job_progress(job, payload)
        if payload.get("text"):
            if job is not None:
                job["lastOutput"] = time.time()
            self._log(payload["text"], entry, job)
        if payload.get("file"):
            self._show_transfer_progress(row, payload)
        self._publish_queue()

    def _update_job_progress(self, job, payload):
        for key in ("pid", "frame", "framesDone", "progress"):
            if key in payload:
                job[key] = payload[key]
        if "elapsed" in payload:
            job["renderElapsed"] = payload["elapsed"]
        if payload.get("renderError"):
            job.update(
                state="stopping",
                stage="Render failed · stopping process",
                error=payload["renderError"],
            )
            return
        if job["state"] != "rendering" or self._cancel.is_set():
            return
        last_output = job.get("lastOutput", job.get("started", time.time()))
        silence = max(0, int(time.time() - last_output))
        phase = (
            "Рендеринг шота"
            if job.get("frame") not in (None, "")
            else "Рендер запущен · ожидание Maya"
        )
        job["stage"] = (
            f"{phase} · PID {job.get('pid') or 'запуск'} · нет вывода {silence} с"
        )

    def _show_transfer_progress(self, row, payload):
        row["stage"] = f"Загрузка: {Path(payload['file']).name}"
        total = payload.get("bytes_total", 0)
        if total:
            row["stage"] += f" · {payload.get('bytes_done', 0) / total:.0%}"

    def _episode_prepared(self, _payload):
        entry = self._active_entry
        entry["prepared"] = True
        entry.update(state="waiting", stage="Ready to render")
        if self._cancel.is_set():
            self._after_cancel()
        else:
            self._publish_queue()
            self._pump()

    def _shot_prepared(self, payload):
        job = self._active_job
        job.update(payload)
        if self._cancel.is_set():
            job.update(state="cancelled", stage="Cancelled")
            self._active_job = None
            self._after_cancel()
            return
        # Pause requested during download/preparation must also prevent launch.
        if self._paused:
            job.update(state="waiting", stage="Ready · queue paused")
            self._active_job = None
            self._flush_queue()
            return
        job.update(state="rendering", stage="Rendering shot", started=time.time())
        self._active_entry.update(state="rendering", stage=job["title"])
        self._log(job["command"], self._active_entry, job)
        saved = deepcopy(job)
        self._run_stage(
            lambda: _render_native(
                saved, int(self._config.get("render_timeout_minutes", 0)), self._cancel
            ),
            self._render_done,
        )

    def _render_done(self, result):
        entry, job = self._active_entry, self._active_job
        error = result.get("error", "")
        if result["cancelled"]:
            state = "cancelled"
        elif result["exitCode"] == 0 and not result["timedOut"] and not error:
            state = "completed"
        else:
            state = "failed"

        if result["timedOut"]:
            error = "Render timeout"
        elif state == "failed" and not error:
            error = f"Render exited with code {result['exitCode']}"
        job.update(
            result=state,
            exitCode=result["exitCode"],
            renderElapsed=result["elapsed"],
            pid="",
            finished=time.time(),
            error=error,
        )
        if state == "completed":
            job.update(progress=1.0, framesDone=_job_frame_count(job))
        self._log(f"{job['title']}: {state}, exit {job['exitCode']}", entry, job)
        if entry["test"]:
            self._shot_saved(None)
            return
        job.update(state="saving", stage="Saving result and render log")
        entry.update(state="saving", stage=job["stage"])
        config, saved, rendered = dict(self._config), deepcopy(entry), deepcopy(job)
        self._run_stage(
            lambda: _finalize_shot(self._api, saved, rendered, config),
            self._shot_saved,
        )

    def _shot_saved(self, _value):
        entry, job = self._active_entry, self._active_job
        job.update(state=job["result"], stage=job["result"].capitalize())
        entry.update(state="waiting", stage="Waiting for next shot")
        self._active_job = None
        if job["state"] == "failed" and self._config.get("stop_on_error"):
            self._paused = True
        self._flush_queue()
        if self._cancel.is_set():
            self._after_cancel()
        else:
            self._pump()

    def _stage_failed(self, error):
        entry, job = self._active_entry, self._active_job
        if entry is None:
            self._error_message(error)
            return
        cancelled = isinstance(error, InterruptedError) or self._cancel.is_set()
        if not cancelled:
            self._error_message(error)
        if job is None and self._run_only:
            _scope_entry, job = self._find(self._run_only)
        if job is not None:
            self._fail_job(entry, job, error, cancelled)
        else:
            self._fail_episode(entry, error, cancelled)

    def _fail_job(self, entry, job, error, cancelled):
        saving = job["state"] == "saving"
        job.update(
            state="cancelled" if cancelled else "failed",
            stage="Cancelled" if cancelled else "Failed",
            error=str(error),
            pid="",
            saveFailed=saving,
        )
        self._active_job = None
        entry.update(state="waiting", stage="Waiting for next shot")
        if saving:
            # A write may have reached TACTIC. Never automatically retry it.
            self._paused = True
        if cancelled:
            self._after_cancel()
            return
        if self._config.get("stop_on_error"):
            self._paused = True
        self._flush_queue()
        self._pump()

    def _fail_episode(self, entry, error, cancelled):
        entry["error"] = str(error)
        state = "cancelled" if cancelled else "failed"
        stage = "Cancelled" if cancelled else "Episode preparation failed"
        for job in entry["jobs"]:
            if job["state"] not in _TERMINAL:
                job.update(state=state, stage=stage)
                if not cancelled:
                    job["error"] = str(error)
        if not cancelled and self._config.get("stop_on_error"):
            self._paused = True
        self._finish_entry()

    def _finish_entry(self):
        entry = self._active_entry
        states = {job["state"] for job in entry["jobs"]}
        if "failed" in states:
            result = "failed"
        elif "cancelled" in states:
            result = "cancelled"
        else:
            result = "completed"
        entry["result"] = result
        if entry["test"]:
            self._entry_saved(None)
            return

        entry.update(state="saving", stage="Saving episode status")
        key = entry["episodeKey"]
        status_key = "complete_status" if result == "completed" else "failed_status"
        status = self._config[status_key]
        process = self._config["render_process"]
        self._flush_queue()
        self._stage_operation = self._submit(
            lambda: _set_episode_task_status(self._api.sobject(key), process, status),
            self._entry_saved,
            lambda error: self._entry_save_failed(entry, error),
        )

    def _entry_save_failed(self, entry, error):
        self._stage_operation = None
        entry.update(
            state="failed",
            stage="Could not save episode status",
            error=str(error),
            saveFailed=True,
        )
        self._paused = True
        self._error_message(error)
        self._active_entry = None
        self._flush_queue()
        self._maybe_close()

    def _entry_saved(self, _value):
        self._stage_operation = None
        entry = self._active_entry
        entry.update(
            state=entry["result"],
            stage=entry["result"].capitalize(),
            finished=time.time(),
        )
        self._log(f"Episode {entry['title']}: {entry['state']}", entry)
        self._active_entry = None
        if self._auto_clear_finished and entry["state"] in {"completed", "cancelled"}:
            self._remove_entries([entry])
        else:
            self._flush_queue()
        self.stateChanged.emit()
        self.refresh()
        self._pump()
        self._maybe_close()

    def _cancel_remainder(self):
        entry = self._active_entry
        if entry is None:
            return
        for job in entry["jobs"]:
            if job["state"] not in _TERMINAL:
                job.update(state="cancelled", stage="Cancelled", pid="")
        self._active_job = None
        self._finish_entry()

    def _after_cancel(self):
        if self._cancel_job_only:
            self._cancel_job_only = False
            self._cancel = threading.Event()
            self._flush_queue()
            self._pump()
        else:
            self._cancel_remainder()

    # Queue commands

    @Slot(str)
    def cancelQueue(self, identity):
        entry, job = self._find(identity)
        if entry is None:
            return
        if entry is self._active_entry and (
            job is None or job is self._active_job or job["id"] == self._run_only
        ):
            self._cancel_job_only = job is not None
            self._cancel.set()
            entry.update(stage="Stopping · waiting for active operation")
            if self._active_job:
                self._active_job["stage"] = (
                    "Stopping renderer / finishing current transfer"
                )
            elif job:
                job.update(state="cancelled", stage="Cancelled")
            if self._stage_operation is None:
                self._cancel_remainder()
        else:
            for row in [job] if job else [entry, *entry["jobs"]]:
                if row["state"] not in _TERMINAL:
                    row.update(state="cancelled", stage="Cancelled")
        self._flush_queue()

    @Slot()
    def interruptRender(self):
        self._paused = True
        self._run_only = ""
        self._status = "Stopping queue" if self._active_entry else "Queue stopped"
        if self._active_entry:
            self.cancelQueue(self._active_entry["id"])
        else:
            self.stateChanged.emit()

    @Slot(str)
    def retryQueue(self, identity):
        entry, job = self._find(identity)
        if entry is None or entry["state"] in _ACTIVE:
            return
        if entry is self._active_entry and self._stage_operation is not None:
            return
        if entry.get("saveFailed") or any(
            row.get("saveFailed") for row in ([job] if job else entry["jobs"])
        ):
            self._error_message(
                ValueError(
                    "Server save was not confirmed. Check TACTIC before rerendering; add a new run explicitly."
                )
            )
            return
        if not entry["jobs"]:
            self._discover_entry(entry)
            return
        targets = [
            row
            for row in ([job] if job else entry["jobs"])
            if row["state"] in {"failed", "cancelled"}
        ]
        if not targets:
            return
        for row in targets:
            self._reset_for_retry(row)
        entry.update(state="waiting", stage="Retry queued", prepared=False, error="")
        self.selectQueue(entry["id"])
        self._persist()
        self._pump()

    @staticmethod
    def _reset_for_retry(job):
        job.update(
            id=uuid.uuid4().hex,  # Keep the previous attempt's log file.
            state="waiting",
            stage="Waiting",
            progress=0.0,
            error="",
            frame="",
            framesDone=0,
            renderElapsed=0.0,
            pid="",
            logPath="",
            command="",
            exitCode="",
            attempt=job.get("attempt", 1) + 1,
        )

    @Slot(str)
    def holdQueue(self, identity):
        entry, job = self._find(identity)
        if entry is None:
            return
        row = job or entry
        if row["state"] not in {"waiting", "held"}:
            return
        row["state"] = "waiting" if row["state"] == "held" else "held"
        row["stage"] = row["state"].capitalize()
        if job is not None and entry["state"] == "held" and row["state"] == "waiting":
            entry.update(state="waiting", stage="Waiting")
        self._flush_queue()
        self._pump()

    @Slot(str, int)
    def moveQueue(self, identity, delta):
        movable = self._movable_queue_row(identity)
        if movable is None:
            return
        values, row = movable
        index = values.index(row)
        destination = max(0, min(len(values) - 1, index + delta))
        values.insert(destination, values.pop(index))
        self._flush_queue()

    @Slot(str, str)
    def moveQueueTo(self, identity, target_identity):
        movable = self._movable_queue_row(identity)
        _target_entry, target_job = self._find(target_identity)
        if movable is None:
            return
        values, row = movable
        target = _target_entry if values is self._entries else target_job
        if target not in values or target is row:
            return
        destination = values.index(target)
        values.insert(destination, values.pop(values.index(row)))
        self._flush_queue()

    def _movable_queue_row(self, identity):
        entry, job = self._find(identity)
        if entry is None:
            return None
        row = job or entry
        if "move" not in self._allowed_actions(entry, job):
            return None
        return (entry["jobs"] if job else self._entries), row

    def _remove_entries(self, entries):
        if not entries:
            return
        identities = {
            identity
            for entry in entries
            for identity in [entry["id"], *(job["id"] for job in entry["jobs"])]
        }
        discarded = {id(entry) for entry in entries}
        self._entries = [entry for entry in self._entries if id(entry) not in discarded]
        self._events = [event for event in self._events if event[0] not in identities]
        if self._selected_queue in identities:
            self._selected_queue = ""
            self.logScopeChanged.emit()
            self.logChanged.emit()
        self._flush_queue()

    @Slot()
    def clearCompleted(self):
        self._remove_entries(
            [
                entry
                for entry in self._entries
                if entry["state"] in {"completed", "cancelled"}
            ]
        )

    @Slot(str, result=bool)
    def removeEpisode(self, identity):
        entry, job = self._find(identity)
        if (
            entry is None
            or job is not None
            or "remove" not in self._allowed_actions(entry)
        ):
            return False
        self._remove_entries([entry])
        self._status = f"Удалено из очереди: {entry['title']}"
        self.stateChanged.emit()
        self._pump()
        return True

    @Slot(str)
    def selectQueue(self, identity, align_top=False):
        self._selected_queue = identity
        entry, _job = self._find(identity)
        self._select_episode(entry["episodeKey"] if entry else "")
        self._publish_queue()
        self.queueSelected.emit(
            next(
                (
                    index
                    for index, row in enumerate(self.queue.records())
                    if row["jobId"] == identity
                ),
                -1,
            ),
            align_top,
        )
        self.logScopeChanged.emit()
        self.logChanged.emit()

    def _select_episode(self, key):
        self._selected_episode = key
        episode_index = -1
        for index, row in enumerate(self.episodes.records()):
            selected = row["searchKey"] == key
            self.episodes.set_value(index, "selected", selected)
            if selected:
                episode_index = index
        self.episodeSelected.emit(episode_index)

    @Slot(str)
    def toggleExpanded(self, identity):
        entry, job = self._find(identity)
        if entry is not None and job is None:
            entry["expanded"] = not entry["expanded"]
            self._publish_queue()

    @Slot(str)
    def toggleIncluded(self, identity):
        entry, job = self._find(identity)
        if entry is None or "include" not in self._allowed_actions(entry, job):
            return
        state = "waiting" if job["state"] == "skipped" else "skipped"
        job.update(state=state, stage="Waiting" if state == "waiting" else "Excluded")
        if state == "waiting" and entry["state"] in _TERMINAL:
            entry.update(state="waiting", stage="Waiting", prepared=False, error="")
        self._flush_queue()
        self._pump()

    @Slot(str, str, result=bool)
    def setFrameSpec(self, identity, value):
        entry, job = self._find(identity)
        if entry is None or "frames" not in self._allowed_actions(entry, job):
            return False
        try:
            ranges = _parse_frame_spec(value, job["start"], job["end"])
        except ValueError as error:
            self._error_message(error)
            return False
        job["frameRanges"] = [list(pair) for pair in ranges]
        job["frameSpec"] = _format_frame_ranges(ranges)
        self._error = ""
        self._flush_queue()
        self.stateChanged.emit()
        return True

    # Queue presentation

    def _job_fraction(self, job):
        if job["state"] == "skipped":
            return 0.0
        return 1.0 if job["state"] == "completed" else job.get("progress", 0.0)

    def _job_eta(self, job, frame_seconds=None):
        if job["state"] in _TERMINAL:
            return 0
        progress = job.get("progress", 0)
        if job["state"] == "rendering" and progress > 0:
            return job.get("renderElapsed", 0) * (1 - progress) / progress
        if frame_seconds is None:
            return None
        return frame_seconds * _job_frame_count(job) * (1 - progress)

    def _frame_seconds(self):
        # ponytail: recent mean estimates render time only, not downloads or
        # per-scene complexity; replace with scene-specific samples if needed.
        samples = [
            row["renderElapsed"] / _job_frame_count(row)
            for entry in self._entries
            for row in entry["jobs"]
            if row["state"] == "completed" and row.get("renderElapsed", 0) > 0
        ]
        if not samples:
            return None
        return sum(samples[-20:]) / len(samples[-20:])

    def _episode_record(self, entry, frame_seconds):
        jobs = entry["jobs"]
        included = [job for job in jobs if job["state"] != "skipped"]
        total = sum(_job_frame_count(job) for job in included)
        done = sum(self._job_fraction(job) * _job_frame_count(job) for job in included)
        estimates = [self._job_eta(job, frame_seconds) for job in jobs]
        eta = _total_eta(estimates)
        return {
            "jobId": entry["id"],
            "parentId": "",
            "title": entry["title"],
            "previewUrl": entry.get("previewUrl", ""),
            "subtitle": (
                f"{len(jobs)} шотов · завершено "
                f"{sum(job['state'] == 'completed' for job in jobs)}"
            ),
            "state": entry["state"],
            "stage": _ui_text(entry["stage"]),
            "selected": entry["id"] == self._selected_queue,
            "expanded": entry["expanded"],
            "progress": done / total if total else 0,
            "frames": f"{int(done)}/{total}",
            "elapsed": _duration(entry["elapsed"]),
            "eta": "~" + _duration(eta) if eta is not None else "—",
            "depth": 0,
            "test": entry["test"],
            "attempt": 0,
            "pid": "",
            "included": False,
            "actions": self._allowed_actions(entry),
            "error": entry["error"],
            "indeterminate": entry["state"] in {"discovering", "preparing", "saving"},
        }

    def _shot_record(self, entry, job, frame_seconds):
        eta = self._job_eta(job, frame_seconds)
        frame_spec = job.get("frameSpec") or _format_frame_ranges(_job_ranges(job))
        return {
            "jobId": job["id"],
            "parentId": entry["id"],
            "title": job["title"],
            "previewUrl": job.get("previewUrl", ""),
            "subtitle": f"{frame_spec} · попытка {job['attempt']}",
            "state": job["state"],
            "stage": _ui_text(job["stage"]),
            "selected": job["id"] == self._selected_queue,
            "expanded": False,
            "progress": self._job_fraction(job),
            "frames": f"{job.get('framesDone', 0)}/{_job_frame_count(job)}",
            "elapsed": _duration(job["elapsed"]),
            "eta": "~" + _duration(eta) if eta is not None else "—",
            "depth": 1,
            "test": entry["test"],
            "attempt": job["attempt"],
            "included": job["state"] != "skipped",
            "actions": self._allowed_actions(entry, job),
            "pid": job.get("pid", ""),
            "error": job["error"],
            "indeterminate": job["state"] in {"preparing", "saving"}
            or (job["state"] == "rendering" and not job.get("progress")),
        }

    def _publish_queue(self):
        records = []
        frame_seconds = self._frame_seconds()
        for entry in self._entries:
            records.append(self._episode_record(entry, frame_seconds))
            if entry["expanded"]:
                records.extend(
                    self._shot_record(entry, job, frame_seconds)
                    for job in entry["jobs"]
                )
        self.queue.replace(records)
        self.queueChanged.emit()

    def _tick(self):
        now = time.monotonic()
        delta, self._last_tick = now - self._last_tick, now
        if self._stage_operation is not None and self._active_entry:
            self._active_entry["elapsed"] += delta
            if self._active_job:
                self._active_job["elapsed"] += delta
            self._publish_queue()

    @Slot(int, str)
    def setEpisodeStatus(self, row, status):
        key = self.episodes.get(row).get("searchKey")
        if key:
            process = self._config["render_process"]
            self._submit(
                lambda: _set_episode_task_status(
                    self._api.sobject(key), process, status
                ),
                lambda _value: self.refresh(),
            )

    # Settings and window lifecycle

    @Slot(str, str, str, bool, int)
    def saveSettings(self, maya_path, save_path, camera, stop_on_error, timeout):
        if self.running:
            self._error_message(
                ValueError(
                    "Pause the queue and wait for the current shot before changing render settings"
                )
            )
            return
        values = {
            "maya_render_executable": maya_path.strip(),
            "output_directory": save_path.strip(),
            "camera": camera.strip(),
            "stop_on_error": bool(stop_on_error),
            "render_timeout_minutes": max(0, timeout),
        }
        if not values["maya_render_executable"] or not values["output_directory"]:
            self._error_message(
                ValueError("Render executable and output directory are required")
            )
            return
        from thlib.environment import env_write_config

        self._submit(
            lambda: env_write_config(
                values,
                filename="ui_batch_dispatcher",
                unique_id=self._project_code,
                long_abs_path=True,
            ),
            lambda _value: self._settings_saved(values),
        )

    def _settings_saved(self, values):
        self._config.update(values)
        self.settingsChanged.emit()

    @Slot(int)
    def openEpisode(self, row):
        self._open_sobject(self.episodes.get(row).get("searchKey"))

    @Slot(str)
    def openQueueObject(self, identity):
        entry, job = self._find(identity)
        if entry:
            self._open_sobject(job["shotKey"] if job else entry["episodeKey"])

    def _open_sobject(self, key):
        if key:
            operation = self._api.ui.sobject(key).show()
            operation.on_error(
                self._error_message, dispatch=self._dispatchRequested.emit
            )

    @Slot(str)
    def openPath(self, path):
        if path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    @Slot()
    def openSelectedLog(self):
        detail = self.selectedDetail
        if detail.get("logPath"):
            self.openPath(detail["logPath"])
            return
        self._status = (
            "Render log is available after the shot starts"
            if detail.get("child")
            else "Select a shot to open its render log"
        )
        self.stateChanged.emit()

    @Slot(QUrl, result=str)
    def localPath(self, url):
        return url.toLocalFile()

    @Slot()
    def showDestination(self):
        self.openPath(self._config["output_directory"])

    def attach_window(self, window) -> None:
        self._window = window
        self._create_tray()

    def _create_tray(self) -> None:
        try:
            from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

            if not isinstance(QApplication.instance(), QApplication):
                return
            tray = QSystemTrayIcon(QGuiApplication.windowIcon(), self)
            menu = QMenu()
            start = QAction("Start Scheduler", menu)
            stop = QAction("Stop Scheduler", menu)
            show = QAction("Show Dispatcher", menu)
            hide = QAction("Hide Dispatcher", menu)
            close = QAction("Exit", menu)
            start.triggered.connect(self.startScheduler)
            stop.triggered.connect(self.stopScheduler)
            show.triggered.connect(self.showWindow)
            hide.triggered.connect(self.hideWindow)
            close.triggered.connect(self.closeWindow)
            menu.addActions((start, stop))
            menu.addSeparator()
            menu.addActions((show, hide))
            menu.addSeparator()
            menu.addAction(close)
            tray.setContextMenu(menu)
            tray.activated.connect(
                lambda reason: (
                    self.showWindow()
                    if reason
                    in {
                        QSystemTrayIcon.ActivationReason.Trigger,
                        QSystemTrayIcon.ActivationReason.DoubleClick,
                    }
                    else None
                )
            )
            tray.show()
            self._tray = tray
            self._tray_menu = menu
        except (ImportError, RuntimeError):
            self._tray = None

    @Slot()
    def showWindow(self) -> None:
        if self._window:
            self._window.show()
            self._window.requestActivate()

    @Slot()
    def hideWindow(self) -> None:
        if self._window:
            self._window.hide()

    @Slot()
    def closeWindow(self):
        self._close_requested = True
        self._paused = True
        self._watch_server = False
        self._poll_timer.stop()
        if self._active_entry:
            self.interruptRender()
        self.stateChanged.emit()
        self._maybe_close()

    def _maybe_close(self):
        if (
            not self._close_requested
            or self._stage_operation is not None
            or self._saving
        ):
            return
        # Discovery may still carry an authorized status write. Wait for its
        # completion, then persist before disposing the QObject.
        if self._operations:
            return
        self.shutdown()
        self.windowCloseRequested.emit()

    def shutdown(self):
        if self._closing:
            return
        self._closing = True
        self._cancel.set()
        self._poll_timer.stop()
        self._clock.stop()
        for operation, subscriptions in self._operations.values():
            operation.cancel()
            for subscription in subscriptions:
                subscription.close()
        self._operations.clear()
        if self._tray:
            self._tray.hide()


# QML view


QML_SOURCE = r"""
import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window
import "__APP_QML_URL__" as App
import "__CONTROLS_URL__" as Controls

Window {
    id: root
    required property var applicationRoot
    required property var controller
    readonly property var theme: batchTheme
    readonly property bool narrow: width < 1200
    property string detailPage: "log"
    property bool followLog: true
    property bool freezeLog: false
    property bool updatingLog: false
    property bool logPanelVisible: true
    property int episodeContextRow: -1
    property string queueContextId: ""
    property string draggedQueueId: ""
    property string dragTargetQueueId: ""

    App.Theme {
        id: batchTheme
        dark: root.applicationRoot.dark
        styleName: root.applicationRoot.applicationThemeStyleName
        accentColor: root.applicationRoot.applicationThemeAccentColor
        baseColor: root.applicationRoot.applicationThemeBaseColor
    }
    component BatchCard: Controls.ItemSurface {
        railX: inset + 3; railWidth: 3
        railTopMargin: 12; railBottomMargin: 12
        inset: 4; cornerRadius: theme.surfaceRadius
        borderWidth: 1; borderColor: theme.outlineVariant
        elevated: true; shadowVerticalOffset: 3
        separatorVisible: false
        normalColor: theme.surfaceContainerLow
        selectedColor: theme.contentSelection
    }
    component BatchLabel: Label {
        color: root.theme.primaryText
        font.family: root.theme.fontFamily
    }
    component BatchButton: Controls.Button { theme: root.theme }
    component BatchIconButton: Controls.CompactIconButton { theme: root.theme }
    component BatchTextField: Controls.TextField { theme: root.theme }
    component BatchScrollBar: Controls.ScrollBar { theme: root.theme }
    function stateColor(state) {
        if (state === "failed") return theme.error
        if (state === "completed") return theme.green
        if (state === "rendering") return theme.action
        if (state === "preparing" || state === "saving") return theme.yellow
        return theme.secondaryText
    }
    function queueAction(command, identity) {
        if (command === "only") controller.runOnly(identity)
        else if (command === "hold") controller.holdQueue(identity)
        else if (command === "retry") controller.retryQueue(identity)
        else if (command === "cancel") controller.cancelQueue(identity)
        else if (command === "up") controller.moveQueue(identity, -1)
        else if (command === "down") controller.moveQueue(identity, 1)
        else if (command === "open") controller.openQueueObject(identity)
        else if (command === "frames") frameDialog.edit(identity)
        else if (command === "remove") controller.removeEpisode(identity)
        else if (command === "log") controller.openPath(controller.selectedDetail.logPath)
        else if (command === "output") controller.openPath(controller.selectedDetail.output)
    }
    function allows(actions, command) {
        return !!actions && actions.indexOf(command) >= 0
    }
    function updateLog() {
        if (root.freezeLog || root.updatingLog || logText.selectedText.length) return
        root.updatingLog = true
        const next = controller.logText
        if (next.indexOf(logText.text) === 0)
            logText.insert(logText.length, next.slice(logText.length))
        else if (!logText.selectedText.length)
            logText.text = next
        if (root.followLog && !logText.selectedText.length)
            logScroll.contentItem.contentY = Math.max(0, logText.height - logScroll.height)
        root.updatingLog = false
    }
    function episodeActions() {
        return [
            {"title": "Добавить эпизод в очередь", "translate": false,
             "icon": "playlist_add", "command": "add"},
            {"title": "Тестовый рендер · первый кадр", "translate": false,
             "icon": "science", "command": "test"},
            {"title": "Открыть sObject", "translate": false,
             "icon": "open_in_new", "command": "open"},
            {"title": "Установить статус", "translate": false,
             "icon": "flag", "children":
                controller.episodeStatusChoices(root.episodeContextRow).map(value => ({
                    "title": value.title, "translate": false, "command": "status:" + value.title,
                    "accent": value.accent, "compactAccent": true, "checked": value.checked
                }))}
        ]
    }
    function executionActions(allowed, state) {
        return [
            {title: "Запустить только это", translate: false,
             command: "only", icon: "play_arrow",
             enabled: root.allows(allowed, "only")},
            {title: "Удержать / продолжить", translate: false, command: "hold",
             icon: state === "held" ? "play_circle" : "pause",
             enabled: root.allows(allowed, "hold")},
            {title: "Повторить ошибочные / отменённые", translate: false,
             command: "retry", icon: "refresh",
             enabled: root.allows(allowed, "retry")},
            {title: "Отменить", translate: false,
             command: "cancel", icon: "stop",
             enabled: root.allows(allowed, "cancel")}
        ]
    }
    function queueActions() {
        const details = controller.selectedDetail
        const actions = root.executionActions(details.actions, details.state)
        actions.push(
            {title: "Открыть sObject", translate: false,
             command: "open", icon: "open_in_new"},
            {title: "Файлы", translate: false, icon: "folder", children: [
                {title: "Открыть лог рендера", translate: false,
                 command: "log", enabled: !!details.logPath},
                {title: "Показать папку вывода", translate: false,
                 command: "output"}
            ]}
        )
        if (details.child === false) {
            actions.push({separator: true})
            actions.push({title: "Удалить эпизод из очереди", translate: false,
                          command: "remove",
                          icon: "delete", enabled: root.allows(details.actions, "remove")})
        }
        return actions
    }
    title: qsTr("Диспетчер батч-рендера")
    width: 1440
    height: 920
    minimumWidth: 950
    minimumHeight: 650
    color: theme.workspace
    visible: false
    onClosing: close => {
        close.accepted = false
        if (controller.running)
            closeDialog.open()
        else
            controller.closeWindow()
    }

    Connections {
        target: controller
        function onLogChanged() { root.updateLog() }
        function onQueueSelected(index, alignTop) {
            if (index >= 0) queueList.positionViewAtIndex(
                index, alignTop ? ListView.Beginning : ListView.Contain)
        }
        function onEpisodeSelected(index) {
            if (index < 0) return
            episodeSearch.text = ""
            episodeList.positionViewAtIndex(index, ListView.Beginning)
        }
        function onLogScopeChanged() {
            root.updatingLog = true
            logText.deselect()
            logText.text = ""
            root.updatingLog = false
        }
    }

    // Header and summary
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            Controls.MaterialIcon { name: "view_list"; size: 24; color: theme.action }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                BatchLabel {
                    Layout.fillWidth: true
                    text: qsTr("Диспетчер батч-рендера")
                    color: theme.primaryText
                    font.pointSize: Controls.Typography.title
                    font.weight: Font.DemiBold
                }
                BatchLabel {
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                    text: controller.closePending ? qsTr("Остановка перед закрытием…")
                        : controller.paused ? qsTr("Пауза · текущий шот будет завершён")
                        : qsTr("Последовательная очередь · один рендер за раз")
                    color: theme.secondaryText
                    font.pointSize: Controls.Typography.label
                }
            }
            BatchButton {
                objectName: "batchStartQueue"
                text: controller.paused ? qsTr("Запустить очередь") : qsTr("Пауза после шота")
                icon.name: controller.paused ? "play_arrow" : "pause"
                enabled: controller.ready && !controller.closePending
                onClicked: controller.toggleScheduler()
            }
            BatchIconButton {
                iconName: "stop"; toolTip: qsTr("Остановить очередь сейчас")
                enabled: controller.running
                onClicked: controller.interruptRender()
            }
            BatchIconButton {
                objectName: "batchSettingsButton"
                iconName: "settings"; toolTip: qsTr("Настройки рендера")
                enabled: !controller.running
                onClicked: settingsDialog.open()
            }
            BatchIconButton {
                iconName: "window-minimize"; toolTip: qsTr("Свернуть")
                onClicked: root.showMinimized()
            }
        }

        Rectangle {
            objectName: "batchSummaryBar"
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            color: theme.surfaceContainer
            radius: theme.surfaceRadius
            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 12; anchors.rightMargin: 12
                spacing: 12
                Repeater {
                    model: [
                        {"label": qsTr("В ОЧЕРЕДИ"), "value": controller.summary.pending},
                        {"label": qsTr("ГОТОВО / ОШИБКИ"),
                         "value": controller.summary.completed + " / " + controller.summary.failed},
                        {"label": qsTr("ПРОШЛО"), "value": controller.summary.elapsed},
                        {"label": qsTr("ОСТАЛОСЬ"), "value": controller.summary.eta}
                    ]
                    delegate: RowLayout {
                        required property var modelData
                        required property int index
                        Layout.fillWidth: true; spacing: 6
                        BatchLabel {
                            Layout.fillWidth: true
                            text: modelData.label; color: theme.secondaryText; elide: Text.ElideRight
                            font.pointSize: Controls.Typography.micro
                        }
                        BatchLabel {
                            text: String(modelData.value); color: theme.primaryText
                            font.pointSize: Controls.Typography.label
                            font.weight: Font.DemiBold
                        }
                        Rectangle {
                            Layout.preferredWidth: 1; Layout.preferredHeight: 22
                            visible: index < 3; color: theme.outlineVariant
                        }
                    }
                }
                RowLayout {
                    Layout.preferredWidth: 230; spacing: 8
                    Rectangle {
                        Layout.fillWidth: true; Layout.preferredHeight: 4
                        radius: 2; color: theme.outlineVariant
                        Rectangle {
                            width: parent.width * controller.summary.progress
                            height: parent.height; radius: 2; color: theme.action
                        }
                    }
                    BatchLabel {
                        text: qsTr("Всего: %1%").arg(Math.floor(controller.summary.progress * 100))
                        color: theme.secondaryText
                        font.pointSize: Controls.Typography.micro
                    }
                }
            }
        }

        BatchLabel {
            Layout.fillWidth: true
            visible: controller.errorText.length > 0
            text: controller.errorText
            color: theme.error
            wrapMode: Text.WrapAnywhere
            maximumLineCount: 3
        }

        // Episode catalog and render queue
        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            handle: Rectangle {
                objectName: "batchDockSplitter"
                implicitWidth: 10
                color: "transparent"
                Rectangle {
                    anchors.centerIn: parent
                    width: 1
                    height: Math.max(0, parent.height - 18)
                    color: root.theme.outlineVariant
                }
            }

            Rectangle {
                objectName: "batchEpisodeDock"
                SplitView.preferredWidth: root.narrow ? 270 : 350
                SplitView.minimumWidth: 250
                color: theme.panelDeep
                border.width: 1
                border.color: theme.outlineVariant
                radius: theme.surfaceRadius
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 8; spacing: 6
                    RowLayout {
                        Layout.fillWidth: true
                        BatchLabel {
                            text: qsTr("ЭПИЗОДЫ"); color: theme.secondaryText
                            font.pointSize: Controls.Typography.label
                            Layout.fillWidth: true
                        }
                        BatchLabel {
                            text: episodeList.count; color: theme.secondaryText
                        }
                        BatchIconButton {
                            iconName: "refresh"
                            toolTip: controller.busy ? qsTr("Обновление…") : qsTr("Обновить список")
                            enabled: !controller.busy && controller.ready
                            onClicked: controller.refresh()
                        }
                    }
                    BatchTextField {
                        id: episodeSearch
                        Layout.fillWidth: true
                        placeholderText: qsTr("Найти эпизод")
                    }
                    Flow {
                        id: episodeStatusFilters
                        Layout.fillWidth: true
                        Layout.preferredHeight: childrenRect.height
                        spacing: 5
                        Repeater {
                            model: controller.episodeFiltersModel
                            delegate: App.QuickFilterChip {
                                required property int index
                                required property string value
                                required property string title
                                required property string statusAccent
                                required property int count
                                required property bool active
                                objectName: "batchEpisodeStatusFilter_" + index
                                theme: root.theme
                                implicitHeight: 28
                                text: title + " · " + count
                                checked: active
                                accent: statusAccent || theme.action
                                showAccentMarker: true
                                onClicked: controller.toggleEpisodeStatusFilter(value)
                            }
                        }
                    }
                    Controls.CheckBox {
                        theme: root.theme
                        text: qsTr("Следить за серверной очередью")
                        checked: controller.schedulerRunning
                        onClicked: controller.watchServer(checked)
                    }
                    ListView {
                        id: episodeList
                        objectName: "batchEpisodeList"
                        Layout.fillWidth: true; Layout.fillHeight: true
                        model: controller.episodesModel
                        spacing: 3; clip: true
                        delegate: Item {
                            id: episodeRow
                            required property int index
                            required property string title
                            required property string subtitle
                            required property string searchKey
                            required property bool selected
                            required property url previewUrl
                            required property string renderStatus
                            required property color statusColor
                            required property bool queued
                            objectName: "batchEpisodeRow_" + index
                            readonly property bool matchesName: !episodeSearch.text
                                || (title + " " + subtitle).toLowerCase().indexOf(episodeSearch.text.toLowerCase()) >= 0
                            readonly property bool matchesStatus:
                                controller.visibleEpisodeStatuses.indexOf(renderStatus) >= 0
                            readonly property bool matches: matchesName && matchesStatus
                            width: episodeList.width - episodeBar.reservedExtent - 4
                            height: matches ? 104 : 0
                            visible: matches
                            BatchCard {
                                objectName: "batchEpisodeSurface_" + episodeRow.index
                                anchors.fill: parent
                                theme: root.theme
                                selected: episodeRow.selected
                                hovered: episodeHover.hovered
                                pressed: episodeActivation.pressed
                                accent: episodeRow.statusColor
                                railWidth: 4
                            }
                            HoverHandler { id: episodeHover }
                            Controls.ActivationHandler {
                                id: episodeActivation
                                anchors.rightMargin: 44
                                onActivated: controller.selectEpisode(episodeRow.index)
                            }
                            TapHandler {
                                acceptedDevices: PointerDevice.Mouse
                                    | PointerDevice.TouchPad
                                acceptedButtons: Qt.LeftButton
                                gesturePolicy: TapHandler.DragThreshold
                                onDoubleTapped: controller.renderEpisode(
                                    episodeRow.index, false)
                            }
                            RowLayout {
                                anchors.fill: parent; anchors.margins: 12
                                anchors.leftMargin: 18; spacing: 10
                                Controls.ItemPreview {
                                    theme: root.theme
                                    Layout.preferredWidth: 58; Layout.preferredHeight: 58
                                    source: episodeRow.previewUrl
                                    fallbackIcon: "movie"
                                    fallbackText: episodeRow.title.slice(0, 2)
                                    animateAppearance: false
                                    selected: episodeRow.selected
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true; spacing: 2
                                    Layout.minimumWidth: 0
                                    clip: true
                                    BatchLabel {
                                        Layout.fillWidth: true; text: episodeRow.title
                                        textFormat: Text.PlainText; maximumLineCount: 1
                                        color: theme.primaryText; elide: Text.ElideRight
                                        font.pointSize: Controls.Typography.label
                                        font.weight: Font.DemiBold
                                    }
                                    BatchLabel {
                                        objectName: "batchEpisodeDescription_" + episodeRow.index
                                        Layout.fillWidth: true
                                        Layout.minimumWidth: 0
                                        text: episodeRow.subtitle.replace(/\s+/g, " ")
                                        textFormat: Text.PlainText; maximumLineCount: 1
                                        visible: text.length > 0
                                        color: theme.secondaryText; elide: Text.ElideRight
                                        font.pointSize: Controls.Typography.micro
                                    }
                                    BatchLabel {
                                        Layout.fillWidth: true
                                        text: episodeRow.renderStatus || qsTr("Нет задачи рендера")
                                        textFormat: Text.PlainText; maximumLineCount: 1
                                        color: episodeRow.statusColor
                                        elide: Text.ElideRight
                                        font.pointSize: Controls.Typography.micro
                                    }
                                }
                                BatchIconButton {
                                    objectName: "batchEpisodeAdd_" + episodeRow.index
                                    iconName: "add"
                                    toolTip: qsTr("Добавить эпизод в очередь")
                                    enabled: controller.ready
                                    onClicked: controller.renderEpisode(episodeRow.index, false)
                                }
                            }
                            MouseArea {
                                anchors.fill: parent; acceptedButtons: Qt.RightButton
                                onClicked: mouse => {
                                    root.episodeContextRow = episodeRow.index
                                    episodeMenu.openAt(episodeRow, mouse.x, mouse.y, true)
                                }
                            }
                        }
                        ScrollBar.vertical: BatchScrollBar { id: episodeBar }
                    }
                    BatchLabel {
                        text: controller.busy ? qsTr("Проверка сервера…")
                            : qsTr("Добавьте эпизод в очередь кнопкой +")
                        color: theme.secondaryText
                        font.pointSize: Controls.Typography.micro
                        Layout.fillWidth: true; wrapMode: Text.Wrap
                    }
                }
            }

            ColumnLayout {
                SplitView.fillWidth: true
                SplitView.minimumWidth: 620
                spacing: 8
                RowLayout {
                    Layout.fillWidth: true
                    BatchLabel {
                        text: qsTr("Очередь рендера"); color: theme.primaryText
                        font.weight: Font.DemiBold
                    }
                    Item { Layout.fillWidth: true }
                    BatchIconButton {
                        objectName: "batchMoveFirst"
                        iconName: "angle-double-up"
                        toolTip: qsTr("Переместить в начало")
                        enabled: root.allows(controller.selectedDetail.actions, "move")
                        onClicked: controller.moveQueue(
                            controller.selectedDetail.id, -1000000)
                    }
                    BatchIconButton {
                        objectName: "batchMoveUp"
                        iconName: "arrow_upward"
                        toolTip: qsTr("Переместить выше")
                        enabled: root.allows(controller.selectedDetail.actions, "move")
                        onClicked: controller.moveQueue(controller.selectedDetail.id, -1)
                    }
                    BatchIconButton {
                        objectName: "batchMoveDown"
                        iconName: "arrow_downward"
                        toolTip: qsTr("Переместить ниже")
                        enabled: root.allows(controller.selectedDetail.actions, "move")
                        onClicked: controller.moveQueue(controller.selectedDetail.id, 1)
                    }
                    BatchIconButton {
                        objectName: "batchMoveLast"
                        iconName: "angle-double-down"
                        toolTip: qsTr("Переместить в конец")
                        enabled: root.allows(controller.selectedDetail.actions, "move")
                        onClicked: controller.moveQueue(
                            controller.selectedDetail.id, 1000000)
                    }
                    Controls.CheckBox {
                        objectName: "batchAutoClear"
                        theme: root.theme
                        compact: true
                        text: qsTr("Автоочистка")
                        checked: controller.autoClearFinished
                        onClicked: controller.setAutoClearFinished(checked)
                    }
                    BatchIconButton {
                        objectName: "batchLogPanelShow"
                        iconName: "terminal"
                        iconColor: root.logPanelVisible
                            ? theme.action : theme.primaryText
                        backgroundColor: root.logPanelVisible
                            ? theme.secondaryContainer : "transparent"
                        toolTip: root.logPanelVisible
                            ? qsTr("Скрыть лог процесса")
                            : qsTr("Показать лог процесса")
                        onClicked: root.logPanelVisible = !root.logPanelVisible
                    }
                    BatchButton {
                        text: qsTr("Очистить завершённые")
                        icon.name: "delete_sweep"
                        onClicked: controller.clearCompleted()
                    }
                }

                Rectangle {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    color: theme.surfaceContainer
                    radius: theme.surfaceRadius
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 8
                        spacing: 6
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 20
                            clip: true
                            RowLayout {
                                x: 8 - queueList.contentX
                                width: queueList.contentWidth - queueBar.reservedExtent - 20
                                height: parent.height
                                spacing: 10
                                Item { Layout.preferredWidth: 28 }
                                Item { Layout.preferredWidth: 28 }
                                Item { Layout.preferredWidth: 44 }
                                BatchLabel {
                                    Layout.fillWidth: true
                                    text: qsTr("ЗАДАЧА / ЭТАП"); color: theme.secondaryText
                                    font.pointSize: Controls.Typography.micro
                                }
                                BatchLabel {
                                    Layout.preferredWidth: 112
                                    text: qsTr("ПРОГРЕСС"); color: theme.secondaryText
                                    font.pointSize: Controls.Typography.micro
                                }
                                BatchLabel {
                                    Layout.preferredWidth: 78
                                    text: qsTr("КАДРЫ"); color: theme.secondaryText
                                    font.pointSize: Controls.Typography.micro
                                }
                                BatchLabel {
                                    Layout.preferredWidth: 86
                                    text: qsTr("ПРОШЛО / ОСТАЛОСЬ"); color: theme.secondaryText
                                    font.pointSize: Controls.Typography.micro
                                }
                                Item { Layout.preferredWidth: 156 }
                            }
                        }
                        ListView {
                            id: queueList
                            objectName: "batchQueueList"
                            Layout.fillWidth: true; Layout.fillHeight: true
                            model: controller.queueModel
                            clip: true; spacing: 3
                            contentWidth: Math.max(width, 1020)
                            flickableDirection: Flickable.AutoFlickDirection
                            bottomMargin: queueHBar.reservedExtent + 4
                            delegate: Item {
                                id: queueRow
                                objectName: "batchQueueRow_" + index
                                required property int index
                                required property string jobId
                                required property string title
                                required property string subtitle
                                required property string state
                                required property string stage
                                required property bool selected
                                required property bool expanded
                                required property real progress
                                required property string frames
                                required property string elapsed
                                required property string eta
                                required property int depth
                                required property bool test
                                required property var pid
                                required property bool included
                                required property var actions
                                required property bool indeterminate
                                required property url previewUrl
                                width: queueList.contentWidth - queueBar.reservedExtent - 4
                                height: depth ? 80 : 88
                                clip: true
                                BatchCard {
                                    objectName: "batchQueueSurface_" + queueRow.index
                                    anchors.fill: parent
                                    anchors.leftMargin: queueRow.depth * 24
                                    theme: root.theme
                                    selected: queueRow.selected
                                        || root.dragTargetQueueId === queueRow.jobId
                                    hovered: queueHover.hovered
                                    pressed: queueActivation.pressed
                                    accent: root.stateColor(queueRow.state)

                                }
                                HoverHandler { id: queueHover }
                                Controls.ActivationHandler {
                                    id: queueActivation
                                    anchors.leftMargin: queueRow.depth * 24
                                    anchors.rightMargin: quickActions.width + 54
                                    onActivated: controller.selectQueue(queueRow.jobId)
                                }
                                TapHandler {
                                    acceptedDevices: PointerDevice.Mouse
                                        | PointerDevice.TouchPad
                                    acceptedButtons: Qt.LeftButton
                                    gesturePolicy: TapHandler.DragThreshold
                                    onDoubleTapped: {
                                        controller.selectQueue(queueRow.jobId)
                                        if (!queueRow.depth && !queueRow.expanded)
                                            controller.toggleExpanded(queueRow.jobId)
                                    }
                                }
                                RowLayout {
                                    anchors.fill: parent; anchors.margins: 12
                                    anchors.leftMargin: 16 + queueRow.depth * 24
                                    spacing: 10
                                    BatchIconButton {
                                        id: orderGrip
                                        objectName: "batchQueueGrip_" + queueRow.index
                                        iconName: "drag-handle"
                                        toolTip: qsTr("Перетащить в очереди")
                                        dragHandle: true
                                        enabled: root.allows(queueRow.actions, "move")
                                        onDragStarted: {
                                            controller.selectQueue(queueRow.jobId)
                                            root.draggedQueueId = queueRow.jobId
                                            root.dragTargetQueueId = queueRow.jobId
                                        }
                                        onDragMoved: (pointerX, pointerY) => {
                                            const point = orderGrip.mapToItem(
                                                queueList.contentItem,
                                                pointerX, pointerY)
                                            const targetIndex = queueList.indexAt(
                                                point.x, point.y)
                                            if (targetIndex >= 0)
                                                root.dragTargetQueueId =
                                                    controller.queueModel.get(
                                                        targetIndex).jobId || ""
                                        }
                                        onDragFinished: {
                                            controller.moveQueueTo(
                                                root.draggedQueueId,
                                                root.dragTargetQueueId)
                                            root.draggedQueueId = ""
                                            root.dragTargetQueueId = ""
                                        }
                                        onDragCanceled: {
                                            root.draggedQueueId = ""
                                            root.dragTargetQueueId = ""
                                        }
                                    }
                                    BatchIconButton {
                                        visible: !queueRow.depth
                                        iconName: queueRow.expanded ? "expand_more" : "chevron_right"
                                        toolTip: qsTr("Развернуть / свернуть")
                                        onClicked: controller.toggleExpanded(queueRow.jobId)
                                    }
                                    Controls.CheckBox {
                                        objectName: "batchInclude_" + queueRow.index
                                        theme: root.theme; compact: true
                                        Layout.preferredWidth: 28
                                        visible: queueRow.depth > 0
                                        checked: queueRow.included
                                        enabled: root.allows(queueRow.actions, "include")
                                        Accessible.name: qsTr("Включить шот") + " " + queueRow.title
                                        onClicked: controller.toggleIncluded(queueRow.jobId)
                                    }
                                    Controls.ItemPreview {
                                        objectName: "batchQueuePreview_" + queueRow.index
                                        theme: root.theme
                                        Layout.minimumWidth: 44; Layout.maximumWidth: 44
                                        Layout.preferredWidth: 44; Layout.preferredHeight: 44
                                        source: queueRow.previewUrl
                                        fallbackIcon: "movie"
                                        fallbackText: queueRow.title.slice(0, 2)
                                        selected: queueRow.selected
                                        animateAppearance: false
                                    }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        Layout.minimumWidth: 210
                                        spacing: 2
                                        BatchLabel {
                                            Layout.fillWidth: true
                                            text: queueRow.title + (queueRow.test ? " · TEST" : "")
                                            textFormat: Text.PlainText; maximumLineCount: 1
                                            color: theme.primaryText; elide: Text.ElideRight
                                            font.pointSize: Controls.Typography.label
                                            font.weight: queueRow.depth ? Font.Normal : Font.DemiBold
                                        }
                                        BatchLabel {
                                            Layout.fillWidth: true
                                            objectName: "batchQueueStage_" + queueRow.index
                                            text: queueRow.stage.replace(/\s+/g, " ")
                                            textFormat: Text.PlainText; maximumLineCount: 1
                                            color: root.stateColor(queueRow.state)
                                            elide: Text.ElideRight
                                            font.pointSize: Controls.Typography.micro
                                        }
                                        BatchLabel {
                                            Layout.fillWidth: true
                                            text: queueRow.subtitle + (queueRow.pid ? " · PID " + queueRow.pid : "")
                                            textFormat: Text.PlainText; maximumLineCount: 1
                                            color: theme.secondaryText; elide: Text.ElideRight
                                            font.pointSize: Controls.Typography.micro
                                        }
                                    }
                                    ColumnLayout {
                                        Layout.minimumWidth: 112; Layout.maximumWidth: 112
                                        Layout.preferredWidth: 112; spacing: 5
                                        BatchLabel {
                                            text: queueRow.indeterminate ? qsTr("Выполняется…")
                                                : Math.floor(queueRow.progress * 100) + "%"
                                            color: theme.primaryText
                                            font.pointSize: Controls.Typography.micro
                                        }
                                        Rectangle {
                                            Layout.fillWidth: true; Layout.preferredHeight: 4
                                            radius: 2; color: theme.outlineVariant
                                            Rectangle {
                                                width: parent.width * queueRow.progress
                                                height: parent.height; radius: 2
                                                color: root.stateColor(queueRow.state)
                                            }
                                        }
                                    }
                                    BatchLabel {
                                        Layout.minimumWidth: 78; Layout.maximumWidth: 78
                                        Layout.preferredWidth: 78; text: queueRow.frames
                                        color: theme.secondaryText
                                        font.pointSize: Controls.Typography.label
                                    }
                                    ColumnLayout {
                                        Layout.minimumWidth: 86; Layout.maximumWidth: 86
                                        Layout.preferredWidth: 86; spacing: 4
                                        BatchLabel {
                                            text: queueRow.elapsed; color: theme.primaryText
                                            font.pointSize: Controls.Typography.label
                                        }
                                        BatchLabel {
                                            text: queueRow.eta; color: theme.secondaryText
                                            font.pointSize: Controls.Typography.micro
                                        }
                                    }
                                    RowLayout {
                                        id: quickActions
                                        Layout.minimumWidth: queueRow.depth ? 146 : 118
                                        Layout.maximumWidth: Layout.minimumWidth
                                        spacing: 2
                                        Repeater {
                                            model: [{command: "frames", icon: "edit",
                                                     title: qsTr("Выбрать кадры"),
                                                     enabled: root.allows(queueRow.actions, "frames"),
                                                     visible: queueRow.depth > 0}
                                                   ].concat(root.executionActions(queueRow.actions,
                                                                                  queueRow.state))
                                            delegate: BatchIconButton {
                                                required property var modelData
                                                objectName: "batchQueueAction_" + modelData.command + "_" + queueRow.index
                                                iconName: modelData.icon; toolTip: modelData.title
                                                visible: modelData.visible !== false
                                                enabled: modelData.enabled && !controller.closePending
                                                Accessible.name: modelData.title
                                                onClicked: root.queueAction(modelData.command, queueRow.jobId)
                                            }
                                        }
                                    }
                                    BatchIconButton {
                                        iconName: "more_vert"; toolTip: qsTr("Действия задачи")
                                        onClicked: {
                                            root.queueContextId = queueRow.jobId
                                            controller.selectQueue(queueRow.jobId)
                                            queueMenu.openAt(this, 0, height, false)
                                        }
                                    }
                                }
                                MouseArea {
                                    anchors.fill: parent; acceptedButtons: Qt.RightButton
                                    onClicked: mouse => {
                                        root.queueContextId = queueRow.jobId
                                        controller.selectQueue(queueRow.jobId)
                                        queueMenu.openAt(queueRow, mouse.x, mouse.y, true)
                                    }
                                }
                            }
                            BatchLabel {
                                anchors.centerIn: parent
                                visible: queueList.count === 0
                                text: qsTr("Очередь рендера пуста\nДобавьте эпизод кнопкой + и запустите очередь")
                                horizontalAlignment: Text.AlignHCenter
                                color: theme.secondaryText
                            }
                            ScrollBar.vertical: BatchScrollBar { id: queueBar }
                            ScrollBar.horizontal: BatchScrollBar { id: queueHBar }
                        }
                    }

                }

                // Process log and selected job details
                Rectangle {
                    id: logPanel
                    objectName: "batchLogPanel"
                    Layout.fillWidth: true; Layout.preferredHeight: root.height < 760 ? 170 : 235
                    visible: root.logPanelVisible
                    color: theme.surfaceContainer; radius: theme.surfaceRadius
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 8; spacing: 6
                        RowLayout {
                            Layout.fillWidth: true
                            Controls.SegmentedButton {
                                theme: root.theme; currentValue: root.detailPage
                                model: [{"label": qsTr("Лог"), "value": "log"},
                                        {"label": qsTr("Параметры"), "value": "details"}]
                                onActivated: value => root.detailPage = value
                            }
                            BatchLabel {
                                Layout.fillWidth: true
                                text: controller.selectedDetail.title || qsTr("Все задачи")
                                color: theme.secondaryText; elide: Text.ElideRight
                            }
                            BatchIconButton {
                                iconName: "select_all"; toolTip: qsTr("Показать все логи")
                                onClicked: controller.selectQueue("")
                            }
                            BatchIconButton {
                                objectName: "batchOpenLog"
                                iconName: "open_in_new"
                                toolTip: controller.selectedDetail.logPath
                                    ? qsTr("Открыть лог рендера")
                                    : controller.selectedDetail.child
                                        ? qsTr("Лог появится после запуска шота")
                                        : qsTr("Выберите шот, чтобы открыть его лог")
                                onClicked: controller.openSelectedLog()
                            }
                            Controls.CheckBox {
                                theme: root.theme; text: qsTr("Следить"); checked: root.followLog
                                visible: root.detailPage === "log"
                                onClicked: { root.followLog = checked; root.updateLog() }
                            }
                            Controls.CheckBox {
                                theme: root.theme; text: qsTr("Зафиксировать"); checked: root.freezeLog
                                visible: root.detailPage === "log"
                                onClicked: { root.freezeLog = checked; root.updateLog() }
                            }
                        }
                        ScrollView {
                            id: logScroll
                            Layout.fillWidth: true; Layout.fillHeight: true
                            visible: root.detailPage === "log"
                            clip: true
                            rightPadding: logBar.reservedExtent + 4
                            contentWidth: availableWidth
                            Controls.TextArea {
                                id: logText
                                objectName: "batchLogText"
                                theme: root.theme
                                width: logScroll.availableWidth
                                readOnly: true
                                textFormat: TextEdit.PlainText
                                wrapMode: TextEdit.WrapAnywhere
                                font.pointSize: Controls.Typography.micro
                                background: Item {}
                                onSelectedTextChanged: if (!selectedText.length) root.updateLog()
                            }
                            ScrollBar.vertical: BatchScrollBar { id: logBar }
                        }
                        ScrollView {
                            id: detailScroll
                            Layout.fillWidth: true; Layout.fillHeight: true
                            visible: root.detailPage === "details"
                            clip: true; contentWidth: availableWidth
                            rightPadding: detailsBar.reservedExtent + 4
                            Controls.TextArea {
                                objectName: "batchDetailText"
                                theme: root.theme; width: detailScroll.availableWidth
                                readOnly: true; textFormat: TextEdit.PlainText
                                wrapMode: TextEdit.WrapAnywhere
                                background: Item {}
                                text: {
                                    const d = controller.selectedDetail
                                    if (!d.id) return qsTr("Выберите задачу, чтобы увидеть процесс и файлы")
                                    return qsTr("Этап: ") + d.stage
                                        + "\nPID: " + (d.pid || "—") + "    " + qsTr("Код выхода: ") + d.exitCode
                                        + "\n" + qsTr("Прошло: ") + d.elapsed + "    " + qsTr("Кадры: ") + d.frames
                                        + "\n" + qsTr("Сцена: ") + d.scene
                                        + "\n" + qsTr("Вывод: ") + d.output
                                        + "\n" + qsTr("Лог: ") + d.logPath
                                        + "\n\n" + d.command + (d.error ? "\n\n" + d.error : "")
                                }
                            }
                            ScrollBar.vertical: BatchScrollBar { id: detailsBar }
                        }
                    }
                }
            }
        }
        BatchLabel {
            Layout.fillWidth: true
            text: controller.statusText
            color: theme.secondaryText
            font.pointSize: Controls.Typography.label
        }
    }

    // Menus and dialogs
    App.ActionMenu {
        id: episodeMenu; parent: Overlay.overlay; theme: root.theme; compact: true
        objectName: "batchEpisodeMenu"
        actions: []
        onAboutToShow: actions = root.episodeActions()
        onTriggered: command => {
            if (command === "add" || command === "test") {
                controller.renderEpisode(root.episodeContextRow, command === "test")
            } else if (command === "open") controller.openEpisode(root.episodeContextRow)
            else if (command.indexOf("status:") === 0)
                controller.setEpisodeStatus(root.episodeContextRow, command.slice(7))
        }
    }
    App.ActionMenu {
        id: queueMenu; parent: Overlay.overlay; theme: root.theme; compact: true
        objectName: "batchQueueMenu"
        actions: []
        onAboutToShow: actions = root.queueActions()
        onTriggered: command => root.queueAction(command, root.queueContextId)
    }

    Controls.Dialog {
        id: frameDialog
        objectName: "batchFrameDialog"
        parent: Overlay.overlay; theme: root.theme
        title: qsTr("Кадры для рендера")
        width: Math.min(520, root.width - 40)
        modal: true; anchors.centerIn: parent
        property string jobId: ""
        function edit(identity) {
            jobId = identity
            controller.selectQueue(identity)
            frameInput.text = controller.selectedDetail.frameSpec
            open()
        }
        onOpened: {
            frameInput.forceActiveFocus()
            frameInput.selectAll()
        }
        contentItem: ColumnLayout {
            spacing: 8
            BatchTextField {
                id: frameInput
                objectName: "batchFrameInput"
                Layout.fillWidth: true
                placeholderText: qsTr("1-20, 50, 66, 68, 70-150")
                onAccepted: if (controller.setFrameSpec(frameDialog.jobId, text)) frameDialog.close()
            }
            BatchLabel {
                Layout.fillWidth: true
                text: qsTr("Разделяйте отдельные кадры и диапазоны запятыми. Кадры должны входить в диапазон шота.")
                color: theme.secondaryText
                font.pointSize: Controls.Typography.micro; wrapMode: Text.Wrap
            }
        }
        footer: Controls.DialogActions {
            theme: root.theme
            BatchButton {
                text: qsTr("Отмена")
                onClicked: frameDialog.close()
            }
            BatchButton {
                objectName: "batchFrameSave"
                text: qsTr("Применить"); highlighted: true
                enabled: frameInput.text.trim().length > 0
                onClicked: if (controller.setFrameSpec(frameDialog.jobId, frameInput.text)) frameDialog.close()
            }
        }
    }

    Controls.Dialog {
        id: closeDialog
        parent: Overlay.overlay; theme: root.theme
        title: qsTr("Остановить работу и закрыть?")
        modal: true; anchors.centerIn: parent
        contentItem: BatchLabel {
            text: qsTr("Активный рендер будет остановлен. Остальные задачи сохранятся на паузе.")
            color: theme.primaryText
        }
        footer: Controls.DialogActions {
            theme: root.theme
            BatchButton { text: qsTr("Продолжить работу"); onClicked: closeDialog.close() }
            BatchButton {
                text: qsTr("Остановить и закрыть")
                onClicked: { closeDialog.close(); controller.closeWindow() }
            }
        }
    }

    Controls.Dialog {
        id: settingsDialog
        objectName: "batchSettingsDialog"
        parent: Overlay.overlay; theme: root.theme
        title: qsTr("Настройки рендера")
        width: Math.min(680, root.width - 40)
        height: Math.min(720, root.height - 40)
        modal: true; anchors.centerIn: parent
        onAboutToShow: {
            mayaPath.text = controller.settings.mayaPath
            outputPath.text = controller.settings.savePath
            camera.text = controller.settings.camera
            timeout.value = controller.settings.timeout
            stopOnError.checked = controller.settings.stopOnError
        }
        contentItem: ScrollView {
            id: settingsScroll
            clip: true
            contentWidth: availableWidth
            rightPadding: settingsBar.reservedExtent + 4
            ColumnLayout {
                width: settingsScroll.availableWidth
                spacing: 18
                App.ConfigurationSection {
                    theme: root.theme; Layout.fillWidth: true
                    title: qsTr("Maya")
                    description: qsTr("Рендер, папка назначения и камера сцены")
                    ColumnLayout {
                        Layout.fillWidth: true; spacing: 10
                        BatchLabel { text: qsTr("Render.exe"); color: theme.secondaryText }
                        RowLayout {
                            Layout.fillWidth: true
                            BatchTextField { id: mayaPath; Layout.fillWidth: true }
                            BatchIconButton {
                                iconName: "folder"; toolTip: qsTr("Выбрать")
                                onClicked: mayaDialog.open()
                            }
                        }
                        BatchLabel { text: qsTr("Папка вывода"); color: theme.secondaryText }
                        RowLayout {
                            Layout.fillWidth: true
                            BatchTextField { id: outputPath; Layout.fillWidth: true }
                            BatchIconButton {
                                iconName: "folder"; toolTip: qsTr("Выбрать")
                                onClicked: outputDialog.open()
                            }
                        }
                        BatchLabel { text: qsTr("Камера"); color: theme.secondaryText }
                        BatchTextField {
                            id: camera; Layout.fillWidth: true
                            placeholderText: qsTr("Использовать настройки сцены")
                        }
                    }
                }
                App.ConfigurationSection {
                    theme: root.theme; Layout.fillWidth: true
                    title: qsTr("Выполнение очереди")
                    description: qsTr("Контроль зависших рендеров и обработка ошибок")
                    ColumnLayout {
                        Layout.fillWidth: true; spacing: 12
                        Controls.SettingsRow {
                            theme: root.theme
                            title: qsTr("Максимальное время одного шота, минуты")
                            description: qsTr("Если Maya зависнет или перестанет отвечать, диспетчер остановит шот по истечении этого времени. 0 — ждать без ограничения.")
                            Controls.SpinBox { id: timeout; theme: root.theme; from: 0; to: 10080 }
                        }
                        Controls.Switch {
                            id: stopOnError; theme: root.theme
                            text: qsTr("Ставить очередь на паузу после ошибки шота")
                        }
                    }
                }
            }
            ScrollBar.vertical: BatchScrollBar { id: settingsBar }
        }
        footer: Controls.DialogActions {
            objectName: "batchSettingsFooter"
            theme: root.theme
            BatchButton { text: qsTr("Отмена"); onClicked: settingsDialog.close() }
            BatchButton {
                text: qsTr("Сохранить"); highlighted: true; icon.name: "save"
                enabled: mayaPath.text.trim().length > 0 && outputPath.text.trim().length > 0
                onClicked: {
                    controller.saveSettings(mayaPath.text, outputPath.text, camera.text,
                                            stopOnError.checked, timeout.value)
                    settingsDialog.close()
                }
            }
        }
    }
    FileDialog {
        id: mayaDialog
        title: qsTr("Исполняемый файл Maya Render")
        onAccepted: mayaPath.text = root.controller.localPath(selectedFile)
    }
    FolderDialog {
        id: outputDialog
        title: qsTr("Папка вывода")
        onAccepted: outputPath.text = root.controller.localPath(selectedFolder)
    }
}
"""
# Window lifecycle


_RUNTIME_WINDOWS = globals().get("_RUNTIME_WINDOWS", [])


def _handler_context(parent):
    if parent is None:
        raise RuntimeError("TACTIC Handler main window is not available")
    engine = qmlEngine(parent)
    if engine is None:
        raise RuntimeError("TACTIC Handler QML engine is not available")
    application = engine.rootContext().contextProperty("appController")
    if application is None:
        raise RuntimeError("TACTIC Handler application controller is unavailable")
    return engine, application


def _create_window(engine, application_root, parent, controller):
    source = QML_SOURCE.replace(
        "__APP_QML_URL__",
        QUrl.fromLocalFile(str(application_root / "thlib/ui/qml")).toString(),
    ).replace(
        "__CONTROLS_URL__",
        QUrl.fromLocalFile(str(application_root / "thlib/ui/qml/controls")).toString(),
    )
    component = QQmlComponent(engine)
    component.setData(source.encode("utf-8"), QUrl.fromLocalFile(str(Path(__file__))))
    if component.isError():
        details = "\n".join(error.toString() for error in component.errors())
        component.deleteLater()
        raise RuntimeError(f"Cannot load Batch Dispatcher QML:\n{details}")
    window = component.createWithInitialProperties(
        {"applicationRoot": parent, "controller": controller}
    )
    if window is None:
        details = "\n".join(error.toString() for error in component.errors())
        component.deleteLater()
        raise RuntimeError(f"Cannot create Batch Dispatcher window:\n{details}")
    return component, window


def _windows_to_hide(parent, application, enabled):
    if not enabled:
        return [], []
    hidden_windows = [parent] if parent.isVisible() else []
    window_model = getattr(application, "window_model", None)
    hidden_ids = []
    if window_model is not None and window_model.is_window_visible("script_editor"):
        hidden_ids.append("script_editor")
    return hidden_windows, hidden_ids


def show(parent=None, project_code=None, *, hide_handler=True):
    """Show the local batch scheduler backed by the public Handler API."""
    from thlib.environment import env_inst, env_mode

    if _RUNTIME_WINDOWS:
        window = _RUNTIME_WINDOWS[0]["window"]
        window.showNormal()
        window.requestActivate()
        return window

    parent = parent or env_inst.ui_main
    engine, application = _handler_context(parent)
    project_code = str(
        project_code or getattr(application, "current_project_code", "") or ""
    )
    if not project_code:
        raise RuntimeError("Select a project before opening Batch Dispatcher")

    controller = BatchDispatcherController(
        get_api(),
        project_code,
        offline=os.environ.get("TACTIC_QML_SMOKE_OFFLINE", "") == "1",
    )
    application_root = Path(env_mode.get_current_path())
    component, window = _create_window(engine, application_root, parent, controller)

    QQmlEngine.setObjectOwnership(window, QQmlEngine.ObjectOwnership.CppOwnership)
    controller.setParent(window)
    hidden_windows, hidden_window_ids = _windows_to_hide(
        parent, application, hide_handler
    )
    entry = {
        "window": window,
        "component": component,
        "controller": controller,
        "application": application,
        "hidden_windows": hidden_windows,
        "hidden_window_ids": hidden_window_ids,
    }
    _RUNTIME_WINDOWS.append(entry)
    controller.windowCloseRequested.connect(lambda: _dispose_window(window))
    controller.attach_window(window)
    window.show()
    window.requestActivate()
    for hidden_window in hidden_windows:
        hidden_window.hide()
    for window_id in hidden_window_ids:
        application.window_model.close_window(window_id)
    controller.initialize()
    return window


def _dispose_window(window):
    entry = next((item for item in _RUNTIME_WINDOWS if item["window"] is window), None)
    if entry is None:
        return
    _RUNTIME_WINDOWS.remove(entry)
    entry["controller"].shutdown()
    window.hide()
    window.deleteLater()
    entry["component"].deleteLater()
    for hidden_window in entry["hidden_windows"]:
        hidden_window.show()
        hidden_window.raise_()
        hidden_window.requestActivate()
    for window_id in entry["hidden_window_ids"]:
        entry["application"].window_model.show_window(window_id)
