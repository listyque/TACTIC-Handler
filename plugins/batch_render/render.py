"""Batch render functions."""
from __future__ import annotations
import json
import os
import signal
import subprocess
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from tactic_handler_api.operations import report_progress
from .frames import _job_ranges
from .preparation import _check_cancel


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
        self.file_versions = {}
        self.file_revision = 0

    def feed(self, text: str) -> dict:
        previous_revision = self.file_revision
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
        if self.file_revision != previous_revision:
            progress.update(
                renderOutput=str(Path(self.files[-1]).parent),
                renderFiles=list(self.files),
                renderFileVersions=dict(self.file_versions),
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
                    self.file_revision += 1
                    self.file_versions[path] = self.file_revision

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
