"""Out-of-band diagnostics for a blocked Qt event loop."""

from __future__ import annotations

from datetime import datetime
import faulthandler
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

from PySide6.QtCore import QObject, QTimer


class UiHangWatchdog(QObject):
    """Write Python and native process dumps when the UI stops ticking."""

    def __init__(
        self,
        diagnostics_root: Path,
        *,
        timeout_seconds: float = 15.0,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._log_dir = Path(diagnostics_root) / "log"
        self._timeout_seconds = max(1.0, float(timeout_seconds))
        self._last_tick = time.monotonic()
        self._tick_generation = 0
        self._reported_generation = -1
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:
        if self._thread is not None:
            return
        self._last_tick = time.monotonic()
        self._timer.start()
        self._thread = threading.Thread(
            target=self._monitor,
            name="tactic-ui-watchdog",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._timer.stop()
        self._stop.set()
        thread = self._thread
        self._thread = None
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=2.0)

    def _tick(self) -> None:
        self._last_tick = time.monotonic()
        self._tick_generation += 1

    def _monitor(self) -> None:
        interval = min(1.0, self._timeout_seconds / 2.0)
        while not self._stop.wait(interval):
            blocked_for = time.monotonic() - self._last_tick
            if blocked_for < self._timeout_seconds:
                continue
            generation = self._tick_generation
            if generation == self._reported_generation:
                continue
            self._reported_generation = generation
            trace_path, dump_path = self._write_dump(blocked_for)
            if not self._stop.is_set():
                self._terminate_after_hang(trace_path, dump_path)

    def _terminate_after_hang(
        self,
        trace_path: Path,
        dump_path: Path | None,
    ) -> None:
        report_path = dump_path or trace_path
        message = self.tr(
            "TACTIC-Handler stopped responding and will close.\n\n"
            "A crash dump was written to:\n%1"
        ).replace("%1", str(report_path))
        if sys.platform == "win32":
            helper = (
                "import ctypes,sys;"
                "ctypes.windll.user32.MessageBoxW("
                "None,sys.argv[1],sys.argv[2],0x00041010)"
            )
            try:
                subprocess.Popen(
                    [sys.executable, "-I", "-c", helper,
                     message, "TACTIC-Handler"],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True,
                    creationflags=sum(
                        getattr(subprocess, name, 0)
                        for name in (
                            "CREATE_NEW_PROCESS_GROUP",
                            "DETACHED_PROCESS",
                            "CREATE_NO_WINDOW",
                        )
                    ),
                )
            except OSError:
                import ctypes

                ctypes.windll.user32.MessageBoxW(
                    None, message, "TACTIC-Handler", 0x00041010
                )
        else:
            sys.stderr.write(message + "\n")
        os._exit(70)

    def _write_dump(self, blocked_for: float) -> tuple[Path, Path | None]:
        self._log_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        base_path = self._log_dir / f"ui_hang_{stamp}_{os.getpid()}"
        trace_path = base_path.with_suffix(".txt")
        with trace_path.open("w", encoding="utf-8") as stream:
            stream.write(
                "TACTIC-Handler UI hang\n"
                f"timestamp={datetime.now().astimezone().isoformat()}\n"
                f"pid={os.getpid()}\n"
                f"blocked_seconds={blocked_for:.3f}\n\n"
            )
            faulthandler.dump_traceback(file=stream, all_threads=True)
        try:
            dump_path = self._write_windows_minidump(
                base_path.with_suffix(".dmp")
            )
        except OSError as error:
            dump_path = None
            with trace_path.open("a", encoding="utf-8") as stream:
                stream.write(f"\nNative minidump failed: {error}\n")
        return trace_path, dump_path

    @staticmethod
    def _write_windows_minidump(path: Path) -> Path | None:
        if sys.platform != "win32":
            return None
        import ctypes
        from ctypes import wintypes
        import msvcrt

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        dbghelp = ctypes.WinDLL("dbghelp", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        kernel32.GetCurrentProcessId.restype = wintypes.DWORD
        writer = dbghelp.MiniDumpWriteDump
        writer.argtypes = (
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.HANDLE,
            wintypes.DWORD,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
        )
        writer.restype = wintypes.BOOL
        with path.open("w+b") as stream:
            written = writer(
                kernel32.GetCurrentProcess(),
                kernel32.GetCurrentProcessId(),
                wintypes.HANDLE(msvcrt.get_osfhandle(stream.fileno())),
                0x1000,  # MiniDumpWithThreadInfo
                None,
                None,
                None,
            )
            if not written:
                raise ctypes.WinError(ctypes.get_last_error())
        return path
