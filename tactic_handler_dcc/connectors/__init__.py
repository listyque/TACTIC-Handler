"""Native DCC integrations for the TACTIC-Handler client SDK."""

from __future__ import annotations

from importlib import import_module
from pkgutil import iter_modules
import re


STANDARD_ITEM_ACTIONS = (
    {
        "id": "open",
        "capability": "open_scene",
        "title": "Open scene",
        "icon": "folder_open",
        "target": "file",
        "scopes": ("sobject", "snapshot", "file"),
        "requires_snapshot": True,
        "allow_multiple": False,
        "quick": True,
        "quick_order": 20,
        "replaces": "open",
        "trigger": "scene.open",
    },
    {
        "id": "save",
        "capability": "prepare_checkin",
        "title": "Save scene",
        "icon": "save",
        "target": "scene_checkin",
        "scopes": ("sobject", "snapshot", "process"),
        "quick": True,
        "quick_order": 10,
        "replaces": "save",
        "trigger": "scene.save",
    },
    {
        "id": "import",
        "capability": "import_file",
        "title": "Import",
        "icon": "input",
        "target": "file",
        "scopes": ("sobject", "snapshot", "file"),
        "requires_snapshot": True,
        "allow_multiple": False,
        "quick": True,
        "quick_order": 30,
        "trigger": "scene.import",
    },
    {
        "id": "reference",
        "capability": "reference_file",
        "title": "Create Reference",
        "icon": "link",
        "target": "file",
        "scopes": ("sobject", "snapshot", "file"),
        "requires_snapshot": True,
        "allow_multiple": False,
        "quick": True,
        "quick_order": 40,
        "trigger": "scene.reference",
    },
)


def _identifier(value, label: str) -> str:
    result = re.sub(r"[^a-z0-9_]+", "_", str(value or "").lower()).strip("_")
    if not result:
        raise ValueError(f"A DCC {label} is required")
    return result


def _field(field: dict) -> dict:
    result = dict(field or {})
    result["key"] = _identifier(result.get("key"), "setting key")
    result["type"] = str(result.get("type") or "text")
    if result["type"] not in {"boolean", "choice", "integer", "text"}:
        raise ValueError(
            f"Unsupported DCC setting type: {result['type']!r}"
        )
    if result["type"] == "choice":
        result["choices"] = [
            dict(choice) for choice in result.get("choices") or ()
        ]
    return result


def _item_action(action: dict) -> dict:
    result = dict(action or {})
    result["id"] = _identifier(result.get("id"), "action id")
    result["capability"] = str(result.get("capability") or result["id"])
    result["title"] = str(result.get("title") or result["id"].replace("_", " ").title())
    result["icon"] = str(result.get("icon") or "deployed_code")
    result["target"] = str(result.get("target") or "item")
    if result["target"] not in {"file", "item", "scene_checkin"}:
        raise ValueError(f"Unsupported DCC action target: {result['target']!r}")
    result["scopes"] = list(
        result.get("scopes") or ("sobject", "snapshot")
    )
    result["options"] = [
        _field(field) for field in result.get("options") or ()
    ]
    return result


def _configuration(application: str, source: dict | None) -> dict:
    if not source:
        return {}
    result = dict(source)
    result["id"] = f"dcc.{application}"
    result["application"] = application
    sections = []
    for section in result.get("sections") or ():
        normalized = dict(section)
        normalized["fields"] = [
            _field(field) for field in normalized.get("fields") or ()
        ]
        sections.append(normalized)
    result["sections"] = sections
    return result

def dcc_trigger_event(application: str, event: str) -> str:
    application = _identifier(application, "application type")
    return f"dcc.{application}.{str(event).strip('.')}"


def dcc_manifest(module) -> dict:
    manifest = getattr(module, "DCC_MANIFEST", None)
    if not isinstance(manifest, dict):
        raise ValueError(f"{module.__name__} must define DCC_MANIFEST")
    application = _identifier(manifest.get("application"), "application id")
    ui = dict(manifest.get("ui") or {})
    item_actions = [
        _item_action(action)
        for action in (
            ui.get("item_actions")
            if "item_actions" in ui
            else STANDARD_ITEM_ACTIONS
        ) or ()
    ]
    tool_actions = [
        _item_action({**action, "target": "item", "scopes": ()})
        for action in ui.get("tool_actions") or ()
    ]
    return {
        **manifest,
        "application": application,
        "title": str(manifest.get("title") or application.title()),
        "ui": {
            **ui,
            "item_actions": item_actions,
            "tool_actions": tool_actions,
            "configuration": _configuration(
                application, ui.get("configuration")
            ),
            "focus_preferences": dict(ui.get("focus_preferences") or {}),
        },
    }


def dcc_manifests() -> tuple[dict, ...]:
    manifests = []
    for module_info in sorted(iter_modules(__path__), key=lambda item: item.name):
        if module_info.name.startswith("_"):
            continue
        module = import_module(f"{__name__}.{module_info.name}")
        manifests.append(dcc_manifest(module))
    return tuple(manifests)


def dcc_trigger_actions() -> tuple[tuple[str, str, str, bool], ...]:
    actions = []
    for manifest in dcc_manifests():
        application = manifest["application"]
        title = manifest["title"]
        for event, label, icon in manifest.get("script_triggers") or ():
            actions.append((
                dcc_trigger_event(application, event),
                f"{title} · {label}",
                str(icon),
                True,
            ))
    return tuple(actions)


def dcc_manifest_for(application: str) -> dict:
    if not str(application or "").strip():
        return {}
    application = _identifier(application, "application id")
    return next((
        manifest for manifest in dcc_manifests()
        if manifest["application"] == application
    ), {})


def dcc_item_actions(application: str) -> tuple[dict, ...]:
    return tuple(
        dict(action)
        for action in dcc_manifest_for(application).get("ui", {}).get(
            "item_actions", ()
        )
    )


def dcc_item_action(application: str, action_id: str) -> dict:
    action_id = _identifier(action_id, "action id")
    return next((
        action for action in dcc_item_actions(application)
        if action["id"] == action_id
    ), {})


def dcc_tool_actions(application: str) -> tuple[dict, ...]:
    return tuple(
        dict(action)
        for action in dcc_manifest_for(application).get("ui", {}).get(
            "tool_actions", ()
        )
    )


def dcc_configuration_pages() -> tuple[dict, ...]:
    return tuple(
        dict(configuration)
        for manifest in dcc_manifests()
        if (configuration := manifest.get("ui", {}).get("configuration"))
    )


def dcc_configuration(page_id: str) -> dict:
    return next((
        page for page in dcc_configuration_pages()
        if page["id"] == str(page_id or "")
    ), {})


def dcc_configuration_fields(application: str) -> tuple[dict, ...]:
    schema = dcc_configuration(f"dcc.{str(application or '').lower()}")
    return tuple(
        dict(field)
        for section in schema.get("sections") or ()
        for field in section.get("fields") or ()
    )


def normalize_dcc_values(fields, values: dict) -> dict:
    normalized = {}
    for field in fields:
        key = field["key"]
        value = values.get(key, field.get("default"))
        field_type = field["type"]
        if field_type == "boolean":
            value = bool(value)
        elif field_type == "integer":
            minimum = int(field.get("minimum", -2147483648))
            maximum = int(field.get("maximum", 2147483647))
            try:
                value = int(value)
            except (TypeError, ValueError):
                value = int(field.get("default", minimum))
            value = max(minimum, min(value, maximum))
        elif field_type == "choice":
            choices = [
                choice.get("value") for choice in field.get("choices") or ()
            ]
            if value not in choices:
                value = field.get("default")
        else:
            value = str(value or "")
        normalized[key] = value
    return normalized


def dcc_focus_preference(application: str, capability: str) -> str:
    return str(
        dcc_manifest_for(application).get("ui", {}).get(
            "focus_preferences", {}
        ).get(str(capability or "")) or ""
    )


__all__ = [
    "STANDARD_ITEM_ACTIONS", "dcc_configuration", "dcc_configuration_fields",
    "dcc_configuration_pages",
    "dcc_focus_preference", "dcc_item_action", "dcc_item_actions",
    "dcc_manifest", "dcc_manifest_for", "dcc_manifests", "dcc_tool_actions",
    "dcc_trigger_actions", "dcc_trigger_event", "normalize_dcc_values",
]
