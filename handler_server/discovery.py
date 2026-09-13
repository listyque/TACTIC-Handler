from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

from .protocol import PROTOCOL_VERSION


_DISCOVERY_ENV = "TACTIC_HANDLER_DISCOVERY_DIR"


def discovery_directory() -> Path:
    override = os.environ.get(_DISCOVERY_ENV, "").strip()
    if override:
        return Path(override).expanduser()
    local_data = os.environ.get("LOCALAPPDATA", "").strip()
    root = Path(local_data) if local_data else Path(tempfile.gettempdir())
    return root / "TACTIC-Handler" / "handler-server"


def publish_session(host: str, port: int, token: str) -> Path:
    host = str(host or "")
    port = int(port)
    token = str(token or "")
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("Only localhost Handler Server sessions can be published")
    if not 0 < port <= 65535 or not token:
        raise ValueError("A running port and session token are required")

    directory = discovery_directory()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"session-{os.getpid()}.json"
    temporary = directory / f".{path.name}.{os.getpid()}.tmp"
    record = {
        "protocol_version": PROTOCOL_VERSION,
        "host": "127.0.0.1" if host == "localhost" else host,
        "port": port,
        "token": token,
        "process_id": os.getpid(),
        "started_at": time.time(),
    }
    temporary.write_text(
        json.dumps(record, ensure_ascii=False), encoding="utf-8"
    )
    try:
        os.chmod(temporary, 0o600)
    except OSError:
        pass
    os.replace(temporary, path)
    return path


def remove_session(path: Path | str | None) -> None:
    if not path:
        return
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass


def available_sessions() -> list[dict]:
    directory = discovery_directory()
    if not directory.is_dir():
        return []
    records = []
    for path in directory.glob("session-*.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            record = _validated_record(record)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            remove_session(path)
            continue
        if not _process_is_running(record["process_id"]):
            remove_session(path)
            continue
        record["discovery_path"] = str(path)
        records.append(record)
    return sorted(
        records, key=lambda item: item["started_at"], reverse=True
    )


def current_session() -> dict | None:
    records = available_sessions()
    return records[0] if records else None


def _validated_record(value) -> dict:
    if not isinstance(value, dict):
        raise ValueError("Invalid Handler Server discovery record")
    host = str(value.get("host") or "")
    port = int(value.get("port") or 0)
    token = str(value.get("token") or "")
    process_id = int(value.get("process_id") or 0)
    started_at = float(value.get("started_at") or 0.0)
    protocol_version = int(value.get("protocol_version") or 0)
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("Discovery record is not localhost")
    if not 0 < port <= 65535 or not token or process_id <= 0:
        raise ValueError("Discovery record is incomplete")
    if protocol_version != PROTOCOL_VERSION:
        raise ValueError("Discovery protocol version is unsupported")
    return {
        "protocol_version": protocol_version,
        "host": "127.0.0.1" if host == "localhost" else host,
        "port": port,
        "token": token,
        "process_id": process_id,
        "started_at": started_at,
    }


def _process_is_running(process_id: int) -> bool:
    if process_id == os.getpid():
        return True
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.windll.kernel32
            kernel32.OpenProcess.argtypes = (
                wintypes.DWORD, wintypes.BOOL, wintypes.DWORD
            )
            kernel32.OpenProcess.restype = wintypes.HANDLE
            kernel32.GetExitCodeProcess.argtypes = (
                wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)
            )
            kernel32.GetExitCodeProcess.restype = wintypes.BOOL
            kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
            handle = kernel32.OpenProcess(0x1000, False, process_id)
            if not handle:
                return False
            try:
                exit_code = wintypes.DWORD()
                if not kernel32.GetExitCodeProcess(
                    handle, ctypes.byref(exit_code)
                ):
                    return False
                return exit_code.value == 259
            finally:
                kernel32.CloseHandle(handle)
        except (AttributeError, OSError):
            return True
    try:
        os.kill(process_id, 0)
    except PermissionError:
        return True
    except OSError:
        return False
    return True
