"""Batch catalog functions."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from .frames import _frame_number
from .project_config import _preset_state


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
                "",
            ]
        )
    )


def _query_all(stype, **kwargs):
    page = stype.query(limit=1000, **kwargs)
    while True:
        yield from page.items
        if page.has_more is not True:
            break
        page = page.next()


def _query_episodes(api, project_code: str, config: dict) -> dict:
    api.repositories.list()
    project = api.project(project_code)
    workflow = project.workflow()
    tasks = _query_all(
        project.stype('sthpw/task'),
        filters=[('search_type', f"{config['episode_search_type']}?project={project_code}"),
                 ('process', config['render_process'])],
        order_by=['search_code', 'timestamp', 'id'],
    )
    # Filter after selecting the latest task, including empty and project-specific statuses.
    tasks_by_episode = {str(task.get_value('search_code')): task for task in tasks
                        if task.get_value('search_code')}
    records = []
    for episode in _query_all(project.stype(config['episode_search_type']),
                              order_by=['name'], include_snapshots=True):
        task = tasks_by_episode.get(str(episode.get_code()))
        status = str(task.get_value('status') or '') if task else ''
        records.append({
            'title': _title(episode), 'searchKey': episode.get_search_key(),
            'code': str(episode.get_code() or ''),
            'subtitle': str(episode.get_value('description') or ''),
            'previewUrl': _preview_url(episode.snapshots(prefetched=True)),
            'renderStatus': status,
            'statusColor': _task_status_color(workflow, task, status),
            'statusChoices': [{'title': value, 'accent': _task_status_color(workflow, task, value),
                              'checked': status == value} for value in config['status_options']],
            'serverQueued': status in config['queue_statuses'],
        })
    counts = Counter(row['renderStatus'] for row in records)
    statuses = list(dict.fromkeys([*_episode_filter_statuses(config), *counts]))
    colors = {row['renderStatus']: row['statusColor'] for row in records}
    return {
        'episodes': records,
        'queuedEpisodes': [row for row in records if row['serverQueued']],
        'filters': [{'value': status, 'title': status, 'count': counts[status],
                     'statusAccent': colors.get(status, '')} for status in statuses],
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
