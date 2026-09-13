"""Copy this file to ``connectors/<dcc>.py`` and fill in the manifest/API."""

from __future__ import annotations

from . import STANDARD_ITEM_ACTIONS


DCC_MANIFEST = {
    "application": "template",
    "title": "Template DCC",
    "script_triggers": (
        ("scene.open", "Open scene", "folder_open"),
        ("scene.save", "Save scene", "save"),
    ),
    "ui": {
        # Keep only the standard actions supported by the connector and append
        # application-specific actions beside them.
        "item_actions": (
            *STANDARD_ITEM_ACTIONS,
            {
                "id": "inspect_item",
                "capability": "inspect_item",
                "title": "Inspect in Template DCC",
                "icon": "search",
                "target": "item",
                "scopes": ("sobject", "snapshot"),
            },
        ),
        "tool_actions": ({
            "id": "show_console",
            "capability": "show_console",
            "title": "Show Template DCC Console",
            "icon": "terminal",
        },),
        "configuration": {
            "title": "Template DCC",
            "description": "Template DCC integration settings",
            "icon": "deployed_code",
            "help_topic": "dcc_clients",
            "sections": ({
                "title": "Integration",
                "description": "Settings owned by this DCC connector.",
                "icon": "deployed_code",
                "fields": (
                    {
                        "key": "create_preview",
                        "type": "boolean",
                        "title": "Create preview",
                        "description": "Create a preview while preparing a check-in.",
                        "default": True,
                    },
                    {
                        "key": "script_format",
                        "type": "choice",
                        "title": "Scene format",
                        "description": "Default scene format for this connector.",
                        "default": "native",
                        "choices": ({
                            "label": "Native",
                            "value": "native",
                        },),
                    },
                    {
                        "key": "focus_after_open",
                        "type": "boolean",
                        "title": "Return focus after opening",
                        "description": "Bring this DCC forward after opening a scene.",
                        "default": True,
                    },
                    {
                        "key": "focus_after_save",
                        "type": "boolean",
                        "title": "Return focus after saving",
                        "description": "Bring this DCC forward after preparing a check-in.",
                        "default": True,
                    },
                ),
            },),
        },
        "focus_preferences": {
            "open_scene": "focus_after_open",
            "prepare_checkin": "focus_after_save",
        },
    },
}


class Connector:
    """Replace the method bodies with calls to the target application's API."""

    _instance = None

    def __init__(self, handler_path=None):
        self.handler_path = handler_path

    @classmethod
    def instance(cls, handler_path=None):
        if cls._instance is None:
            cls._instance = cls(handler_path)
        elif handler_path:
            cls._instance.handler_path = handler_path
        return cls._instance

    @staticmethod
    def dispatch(callback):
        # Replace with the DCC's native main-thread dispatcher when required.
        return callback()

    def register(self, registry):
        for name, handler in (
            ("get_application_info", self.get_application_info),
            ("open_scene", self.open_scene),
            ("prepare_checkin", self.prepare_checkin),
            ("inspect_item", self.inspect_item),
            ("show_console", self.show_console),
        ):
            registry.register(name, handler)
        return registry

    @staticmethod
    def get_application_info(_payload=None):
        return {"version": "replace-with-native-version"}

    @staticmethod
    def open_scene(payload):
        path = str(dict(payload or {}).get("path") or "")
        if not path:
            raise ValueError("A scene path is required")
        # Open ``path`` through the native DCC API.
        return {"success": True, "opened_path": path}

    @staticmethod
    def prepare_checkin(payload):
        # Save through the native DCC API and return local files. Handler owns
        # naming, repositories, transfer, Commit Queue, and TACTIC check-in.
        path = str(dict(payload or {}).get("path") or "")
        return {
            "success": True,
            "files": [{"path": path, "type": "main"}] if path else [],
            "previews": [],
        }

    @staticmethod
    def inspect_item(payload):
        return {"success": True, "search_key": payload.get("search_key", "")}

    @staticmethod
    def show_console(_payload=None):
        return {"success": True}
