"""Public deployment defaults and a compiler-free TH installer composer."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import struct
import tempfile
from urllib.parse import urlparse

from .server_address import is_valid_tactic_server_url, normalize_tactic_server_url

MAGIC = b"TH_SETUP_CFG_001"
MAX_CONFIG = 65536
DEFAULTS = {
    "server": "",
    "project": "",
    "install_folder": "",
    "repository_name": "repo",
    "plugins": None,
    "shelf": "",
    "shortcuts": True,
    "language": "",
    "dark_theme": True,
    "close_to_tray": True,
}


def validate_defaults(values: dict) -> dict:
    if not isinstance(values, dict) or set(values) - set(DEFAULTS):
        raise ValueError(
            "Setup presets may contain only public deployment settings; credentials are not allowed"
        )
    result = {**DEFAULTS, **values}
    for key in (
        "server",
        "project",
        "install_folder",
        "repository_name",
        "shelf",
        "language",
    ):
        value = result[key]
        if (
            not isinstance(value, str)
            or len(value) > 2048
            or any(ord(char) < 32 for char in value)
        ):
            raise ValueError("Invalid setup preset: " + key)
        result[key] = value.strip()
    result["language"] = result["language"].lower()
    if result["language"] not in {"", "en", "ru"}:
        raise ValueError("Invalid language preset")
    server = normalize_tactic_server_url(result["server"])
    parsed = urlparse(server)
    if server and (
        not is_valid_tactic_server_url(server) or parsed.username or parsed.password
    ):
        raise ValueError("Enter a server root URL without embedded credentials")
    result["server"] = server
    name = result["repository_name"]
    reserved = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *("COM" + str(i) for i in range(1, 10)),
        *("LPT" + str(i) for i in range(1, 10)),
    }
    if (
        not name
        or name in {".", ".."}
        or name.endswith((".", " "))
        or re.search(r'[<>:"/\\|?*]', name)
        or name.split(".")[0].upper() in reserved
    ):
        raise ValueError(
            "Enter a single valid repository folder name, for example repo"
        )
    if name.casefold() in {
        "runtime",
        "tactic-handler",
        "build.json",
        "sha256sums",
        "setup-defaults.json",
        "setup-template.bin",
    }:
        raise ValueError(
            "Choose a repository folder name that does not belong to the application"
        )
    if not isinstance(result["shortcuts"], bool):
        raise ValueError("Invalid desktop shortcut preset")
    if not isinstance(result["dark_theme"], bool) or not isinstance(
        result["close_to_tray"], bool
    ):
        raise ValueError("Invalid appearance or tray preset")
    plugins = result["plugins"]
    if plugins is not None and (
        not isinstance(plugins, list)
        or len(plugins) > 64
        or any(
            not isinstance(item, str) or not re.fullmatch(r"[A-Za-z]\w*", item)
            for item in plugins
        )
    ):
        raise ValueError("Invalid DCC plugin preset")
    if plugins is not None:
        result["plugins"] = sorted(set(plugins))
    return result


def read_installer(path: Path) -> tuple[dict, int]:
    """Return bounded public metadata and the original executable length."""
    with path.open("rb") as stream:
        if stream.read(2) != b"MZ":
            raise ValueError("Choose a compatible TH setup executable")
        stream.seek(0, 2)
        size = stream.tell()
        if size < len(MAGIC) + 8:
            raise ValueError("Choose a compatible TH setup executable")
        stream.seek(-len(MAGIC) - 8, 2)
        length = struct.unpack("<Q", stream.read(8))[0]
        if stream.read(len(MAGIC)) != MAGIC or not 0 < length <= min(
            MAX_CONFIG, size - len(MAGIC) - 8
        ):
            raise ValueError(
                "Choose a compatible TH setup executable (version 0.6.0.375 or later)"
            )
        base_size = size - len(MAGIC) - 8 - length
        stream.seek(base_size)
        value = json.loads(stream.read(length))
    if (
        not isinstance(value, dict)
        or set(value) != {"format", "version", "defaults"}
        or type(value["format"]) is not int
        or value["format"] != 1
        or not isinstance(value["version"], str)
        or not re.fullmatch(r"\d+\.\d+\.\d+\.\d+", value["version"])
    ):
        raise ValueError("Invalid TH installer metadata")
    value["defaults"] = validate_defaults(value["defaults"])
    return value, base_size


def _write_footer(stream, version: str, defaults: dict) -> None:
    value = {"format": 1, "version": version, "defaults": validate_defaults(defaults)}
    data = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(data) > MAX_CONFIG:
        raise ValueError("Setup presets are too large")
    stream.write(data + struct.pack("<Q", len(data)) + MAGIC)


def initialize_installer(path: Path, version: str) -> None:
    """Finalize the newly compiled base installer; used by release packaging."""
    with path.open("ab") as stream:
        _write_footer(stream, version, {})


def build_installer(template: Path, output: Path, defaults: dict) -> dict:
    template, output = template.resolve(), output.resolve()
    if template == output or output.suffix.lower() != ".exe":
        raise ValueError("Choose a separate EXE output file")
    values = validate_defaults(defaults)
    metadata, base_size = read_installer(template)
    sidecar = template.with_name(template.name + ".sha256")
    if sidecar.is_file():
        with template.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != sidecar.read_text(encoding="utf-8-sig").split()[0]:
            raise ValueError("The base installer checksum does not match")
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=".th-setup-", suffix=".tmp", dir=output.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as target, template.open("rb") as source:
            remaining = base_size
            while remaining:
                block = source.read(min(1024 * 1024, remaining))
                if not block:
                    raise ValueError("The base installer was truncated")
                target.write(block)
                remaining -= len(block)
            _write_footer(target, metadata["version"], values)
            target.flush()
            os.fsync(target.fileno())
        with open(temporary, "rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        os.replace(temporary, output)
        output.with_name(output.name + ".sha256").write_text(
            digest + "  " + output.name + "\n", encoding="utf-8"
        )
    finally:
        Path(temporary).unlink(missing_ok=True)
    return {"path": str(output), "version": metadata["version"], "sha256": digest}


def read_setup_defaults(root: Path) -> dict:
    path = root.parent / "setup-defaults.json"
    if not path.is_file():
        return validate_defaults({})
    if path.stat().st_size > MAX_CONFIG:
        raise ValueError("Setup presets are too large")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if (
        not isinstance(value, dict)
        or type(value.get("format")) is not int
        or value.get("format") != 1
        or not isinstance(value.get("defaults"), dict)
    ):
        raise ValueError("Invalid setup deployment presets")
    return validate_defaults(value["defaults"])


def default_repository(root: Path) -> Path:
    return root.parent / read_setup_defaults(root)["repository_name"]
