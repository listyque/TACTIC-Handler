from __future__ import annotations

import os
import time
from pathlib import Path

from .registry import CommandRegistry


class DemoDocumentAdapter:
    def __init__(self):
        self.current_path = ""
        self.content = ""
        self.modified = False

    def registry(self) -> CommandRegistry:
        registry = CommandRegistry()
        registry.register("ping", self.ping)
        registry.register("get_application_info", self.get_application_info)
        registry.register("open_file", self.open_file)
        registry.register("save_current_file", self.save_current_file)
        registry.register("get_current_file", self.get_current_file)
        registry.register("fail", self.fail)
        registry.register("sleep", self.sleep)
        return registry

    @staticmethod
    def ping(payload):
        return {"pong": True, "echo": payload}

    @staticmethod
    def get_application_info(_payload):
        return {
            "application": "thin-client-demo",
            "process_id": os.getpid(),
            "document_type": "text",
        }

    def open_file(self, payload):
        path = Path(str(payload.get("path") or "")).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Document does not exist: {path}")
        self.current_path = str(path)
        self.content = path.read_text(encoding="utf-8")
        self.modified = False
        return {"success": True, "cancelled": False, "opened_path": str(path)}

    def save_current_file(self, payload):
        path_value = payload.get("path") or self.current_path
        if not path_value:
            raise ValueError("No current document or destination path")
        path = Path(str(path_value)).expanduser().resolve()
        if "content" in payload:
            self.content = str(payload["content"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.content, encoding="utf-8")
        self.current_path = str(path)
        self.modified = False
        return {"success": True, "cancelled": False, "path": str(path)}

    def get_current_file(self, _payload):
        return {
            "path": self.current_path,
            "modified": self.modified,
            "scene_type": "text",
            "project": str(Path(self.current_path).parent) if self.current_path else "",
            "workspace": str(Path.cwd()),
        }

    @staticmethod
    def fail(payload):
        raise RuntimeError(str(payload.get("message") or "Demo action failed"))

    @staticmethod
    def sleep(payload):
        time.sleep(max(0.0, min(float(payload.get("seconds") or 0), 60.0)))
        return {"completed": True}
