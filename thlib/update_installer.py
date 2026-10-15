"""Independent portable updater. Run with the bundled pythonw.exe."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import traceback
import uuid
from pathlib import Path


USER_DIRECTORIES = (
    "settings", "custom_scripts", "temp_custom_scripts", "log", "updates",
    "backup", "_tmp", ".cache", ".release",
)


def wait_for_parent(pid: int, timeout: int = 120,
                    tick=lambda: None) -> None:
    if sys.platform == "win32":
        import ctypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = (ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong)
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.WaitForSingleObject.argtypes = (ctypes.c_void_p, ctypes.c_ulong)
        kernel.WaitForSingleObject.restype = ctypes.c_ulong
        kernel.CloseHandle.argtypes = (ctypes.c_void_p,)
        handle = kernel.OpenProcess(0x00100000, False, pid)
        if handle:
            try:
                for _ in range(timeout * 5):
                    if kernel.WaitForSingleObject(handle, 200) == 0:
                        return
                    tick()
                raise TimeoutError("TACTIC-Handler did not close")
            finally:
                kernel.CloseHandle(handle)
            return
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.2)
        tick()
    raise TimeoutError("TACTIC-Handler did not close")


def preserve_user_data(previous: Path, replacement: Path) -> None:
    for name in USER_DIRECTORIES:
        source = previous / name
        if source.is_dir():
            shutil.copytree(source, replacement / name, dirs_exist_ok=True)


def install(portable_root: Path, staged: Path, parent_pid: int,
            progress=lambda _message: None) -> None:
    portable_root = Path(portable_root).resolve()
    staged = Path(staged).resolve()
    update_root = portable_root / "_updates"
    if staged.parent != update_root or not staged.is_dir():
        raise ValueError("Staged update is outside the portable update directory")
    app = portable_root / "app"
    backups = update_root / "backups"
    backups.mkdir(parents=True, exist_ok=True)
    backup = backups / f"app-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    progress("Waiting for TACTIC-Handler to close")
    wait_for_parent(parent_pid, tick=lambda: progress("Waiting for TACTIC-Handler to close"))
    progress("Installing update")
    os.replace(app, backup)
    try:
        os.replace(staged, app)
        preserve_user_data(backup, app)
        progress("Starting TACTIC-Handler")
        ready = update_root / f"ready-{parent_pid}"
        ready.unlink(missing_ok=True)
        environment = os.environ.copy()
        environment["TACTIC_UPDATE_HEALTH_FILE"] = str(ready)
        child = subprocess.Popen(
            [str(portable_root / "_runtime" / "pythonw.exe"),
             str(portable_root / "_launcher.pyw")],
            cwd=portable_root, env=environment,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            progress("Starting TACTIC-Handler")
            if ready.is_file():
                ready.unlink(missing_ok=True)
                progress("Update installed")
                return
            if child.poll() is not None:
                break
            time.sleep(0.2)
        child.terminate()
        child.wait(timeout=10)
        raise RuntimeError("Updated application did not reach its first frame")
    except Exception:
        progress("Restoring previous version")
        if 'child' in locals() and child.poll() is None:
            try:
                child.terminate()
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=10)
        if app.exists():
            if 'child' in locals():
                try:
                    preserve_user_data(app, backup)
                except OSError as data_error:
                    progress(f"Could not preserve latest settings: {data_error}")
            failed = update_root / f"failed-{uuid.uuid4().hex}"
            os.replace(app, failed)
        os.replace(backup, app)
        subprocess.Popen(
            [str(portable_root / "_runtime" / "pythonw.exe"),
             str(portable_root / "_launcher.pyw")], cwd=portable_root,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        raise


def main() -> int:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QMessageBox, QProgressDialog

    app = QApplication(sys.argv)
    dialog = QProgressDialog("Preparing update", "", 0, 4)
    dialog.setWindowTitle("TACTIC-Handler update")
    dialog.setCancelButton(None)
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    dialog.show()

    def progress(message: str) -> None:
        dialog.setLabelText(message)
        if message == "Installing update":
            dialog.setValue(1)
        elif message == "Starting TACTIC-Handler":
            dialog.setValue(3)
        elif message == "Update installed":
            dialog.setValue(4)
        app.processEvents()

    try:
        install(Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]), progress)
    except Exception as error:
        log_error = ""
        try:
            (Path(sys.argv[1]) / "_updates" / "last-error.log").write_text(
                traceback.format_exc(), encoding="utf-8",
            )
        except OSError as logging_error:
            log_error = f"\nCould not save error log: {logging_error}"
        QMessageBox.critical(None, "TACTIC-Handler update", str(error) + log_error)
        return 1
    finally:
        dialog.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
