from __future__ import annotations

import os
import struct
import tempfile
import zlib
from pathlib import Path

from .registry import CommandRegistry


class DemoMayaAdapter:
    """Small Maya-shaped adapter used without importing Maya."""

    def __init__(self):
        workspace = Path(tempfile.gettempdir()) / "tactic_handler_demo_maya"
        workspace.mkdir(parents=True, exist_ok=True)
        self.workspace = workspace
        self.current_path = workspace / "demo_scene.ma"
        self.modified = True
        self.imported_files = []
        self.referenced_files = []

    def registry(self) -> CommandRegistry:
        registry = CommandRegistry()
        registry.register("ping", self.ping)
        registry.register("get_application_info", self.get_application_info)
        registry.register("get_current_scene", self.get_current_scene)
        registry.register("prepare_scene", self.prepare_scene)
        registry.register("validate_scene", self.validate_scene)
        registry.register("save_current_scene", self.save_current_scene)
        registry.register("prepare_checkin", self.prepare_checkin)
        registry.register("open_scene", self.open_scene)
        registry.register("import_file", self.import_file)
        registry.register("reference_file", self.reference_file)
        return registry

    @staticmethod
    def ping(payload):
        return {"pong": True, "echo": payload}

    @staticmethod
    def get_application_info(_payload):
        return {
            "application": "maya",
            "version": "Demo",
            "simulated": True,
            "process_id": os.getpid(),
        }

    def get_current_scene(self, payload):
        result = {
            "path": str(self.current_path),
            "modified": self.modified,
            "scene_type": "mayaAscii",
            "project": str(self.workspace),
            "workspace": str(self.workspace),
        }
        if payload.get("include_selection"):
            result["selection"] = []
        return result

    def prepare_scene(self, _payload):
        return {
            "ready": True,
            "path": str(self.current_path),
            "scene_type": "mayaAscii",
            "workspace": str(self.workspace),
        }

    def validate_scene(self, _payload):
        return {
            "valid": bool(self.current_path),
            "warnings": [] if self.current_path else ["Scene has no path"],
        }

    def save_current_scene(self, payload):
        path = Path(str(payload.get("path") or self.current_path)).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(
                "//Maya ASCII demo scene\nrequires maya \"Demo\";\n",
                encoding="utf-8",
            )
        self.current_path = path.resolve()
        self.modified = False
        return {
            "success": True,
            "cancelled": False,
            "path": str(self.current_path),
            "prepared": self.prepare_scene({}),
            "target": self._target_result(payload),
        }

    def prepare_checkin(self, payload):
        saved = self.save_current_scene(payload)
        previews = []
        if bool(payload.get("generate_previews", True)):
            preview_path = self.workspace / "demo_scene_playblast.png"
            self._write_demo_playblast(preview_path, 640, 360)
            previews.append({
                "path": str(preview_path.resolve()),
                "type": "playblast",
                "role": "preview",
            })
        return {
            **saved,
            "files": [{
                "path": str(self.current_path),
                "type": "maya",
                "role": "main",
            }],
            "previews": previews,
        }

    @staticmethod
    def _write_demo_playblast(path, width, height):
        rows = []
        for y in range(height):
            color = bytes((36 + y * 35 // height, 86, 122 + y * 55 // height))
            rows.append(b"\x00" + color * width)
        raw = b"".join(rows)

        def chunk(kind, data):
            return (
                struct.pack("!I", len(data)) + kind + data
                + struct.pack("!I", zlib.crc32(kind + data) & 0xffffffff)
            )

        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(raw, 6))
        png += chunk(b"IEND", b"")
        path.write_bytes(png)

    def open_scene(self, payload):
        path = self._existing_file(payload)
        self.current_path = path
        self.modified = False
        return {
            "success": True, "cancelled": False, "opened_path": str(path),
            "target": self._target_result(payload),
            "snapshot": dict(payload.get("snapshot") or {}),
        }

    def import_file(self, payload):
        path = self._existing_file(payload)
        self.imported_files.append(str(path))
        self.modified = True
        return {"success": True, "cancelled": False, "opened_path": str(path)}

    def reference_file(self, payload):
        path = self._existing_file(payload)
        self.referenced_files.append(str(path))
        self.modified = True
        return {"success": True, "cancelled": False, "opened_path": str(path)}

    @staticmethod
    def _existing_file(payload):
        path = Path(str(payload.get("path") or "")).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Scene file does not exist: {path}")
        return path.resolve()

    @staticmethod
    def _target_result(payload):
        return {
            key: payload.get(key)
            for key in ("project_code", "search_key", "code", "title", "process", "context")
            if payload.get(key) not in (None, "")
        }
