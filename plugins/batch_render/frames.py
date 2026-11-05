"""Batch frames functions."""
from __future__ import annotations
import re
import time
import uuid


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
        "startRequested": origin != "manual",
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
