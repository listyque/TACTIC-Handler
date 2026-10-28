"""Measure native Qt renderer/GPU time: python -m tests.profile_table_render.

The capture runs in a separate Windows/OpenGL process. Qt's native logger owns
the timestamps; Python callbacks never run in the render thread. GPU timestamps
arrive asynchronously, so discard the first three reports of each steady phase.
"""

import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys


def summarize(values):
    if not values:
        return None
    ordered = sorted(values)
    return {"samples": len(values), "medianMs": round(statistics.median(values), 4),
            "maxMs": round(ordered[-1], 4)}


def parse_timings(log):
    phases = {}
    phase = None
    for line in log.splitlines():
        if line.startswith("TABLE_RENDER_PHASE "):
            phase = line.split()[-1]
            phases.setdefault(phase, {name: [] for name in (
                "rendererCpu", "drawCommandsCpu", "syncCpu", "polishCpu",
                "presentWait", "gpu")})
        if phase not in {"initial", "scroll", "refresh", "state"}:
            continue
        record = phases[phase]
        renderer = re.search(r"time in renderer: total=(\d+)ms, preprocess=\d+, updates=\d+, rendering=(\d+)", line)
        if renderer:
            record["rendererCpu"].append(int(renderer[1]))
            record["drawCommandsCpu"].append(int(renderer[2]))
        loop = re.search(r"frame rendered in \d+ms, sync=(\d+), render=\d+, swap=(\d+)", line)
        if loop:
            record["syncCpu"].append(int(loop[1]))
            record["presentWait"].append(int(loop[2]))
        polish = re.search(r"Frame prepared, polish=(\d+) ms", line)
        if polish:
            record["polishCpu"].append(int(polish[1]))
        gpu = re.search(r"last retrieved GPU frame time was ([\d.]+) ms", line)
        if gpu:
            record["gpu"].append(float(gpu[1]))
    return {
        name: {key: summarize(values[3:] if key == "gpu" else values)
               for key, values in record.items() if key != "gpu" or name != "initial"}
        for name, record in phases.items()
        if name in {"initial", "scroll", "refresh", "state"}
    }


def capture():
    from tests.profile_result_table import (
        benchmark, env_mode, gui_test_application, patch, TemporaryDirectory,
    )

    app = gui_test_application()
    with TemporaryDirectory(prefix="render-only-") as directory, patch.object(
        env_mode, "current_path", directory,
    ):
        print(json.dumps(benchmark(app, surface=True)))


def main():
    environment = dict(os.environ, QT_QPA_PLATFORM="windows", QT_QUICK_BACKEND="rhi",
                       QSG_RHI_BACKEND="opengl", QSG_RENDER_LOOP="threaded",
                       QSG_RHI_PROFILE="1", QT_FORCE_STDERR_LOGGING="1",
                       QT_LOGGING_RULES="qt.scenegraph.time.*=true",
                       TH_TABLE_RENDER_TIMING="1")
    completed = subprocess.run(
        [sys.executable, "-m", "tests.profile_table_render", "--capture"],
        cwd=Path(__file__).resolve().parents[1], env=environment,
        capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr + completed.stdout)
    fixture = json.loads(completed.stdout)
    phases = parse_timings(completed.stderr)
    if not phases.get("scroll", {}).get("rendererCpu"):
        raise RuntimeError("Qt did not provide renderer timing logs")
    print(json.dumps({
        "graphicsApi": fixture["graphicsApi"],
        "fixture": {"records": 500, "taskCards": fixture["taskCards"],
                    "viewport": [1600, 900], "rowHeight": 58},
        "cpuResolutionMs": 1,
        "cpuNote": "Native integer-ms logging: 0 means below logging resolution, not zero cost.",
        "gpuNote": "Asynchronous GPU timestamps, first three reports per phase discarded; not frame-aligned with CPU samples.",
        "phases": phases,
    }, indent=2))


if __name__ == "__main__":
    capture() if "--capture" in sys.argv else main()
