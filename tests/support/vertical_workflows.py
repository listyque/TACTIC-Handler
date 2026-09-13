"""Shared manifest and runner helpers for end-to-end workflow stabilization."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "tests" / "contracts" / "vertical_workflows.json"


def load_vertical_manifest() -> dict:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if set(payload) != {"sharedModules", "verticals"}:
        raise ValueError("Invalid vertical workflow manifest")
    verticals = payload.get("verticals")
    if not isinstance(verticals, dict) or not verticals:
        raise ValueError("Vertical workflow manifest has no workflows")
    return payload


def vertical_names() -> tuple[str, ...]:
    return tuple(load_vertical_manifest()["verticals"])


def modules_for(vertical: str) -> list[str]:
    payload = load_vertical_manifest()
    manifest = payload["verticals"]
    modules = list(payload.get("sharedModules", ()))
    if vertical == "all":
        for record in manifest.values():
            for module in record["modules"]:
                if module not in modules:
                    modules.append(module)
        return modules
    if vertical not in manifest:
        raise KeyError(f"Unknown vertical workflow: {vertical}")
    for module in manifest[vertical]["modules"]:
        if module not in modules:
            modules.append(module)
    return modules


def missing_modules() -> list[str]:
    missing = []
    for module in modules_for("all"):
        if importlib.util.find_spec(module) is None:
            missing.append(module)
    return missing
