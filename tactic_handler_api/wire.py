"""Lossless domain values; ordinary mappings cannot forge remote handles."""

import base64
from collections.abc import Mapping
from datetime import date, datetime
from pathlib import Path


def encode(value, reference, seen=None):
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, Path):
        return {"kind": "path", "value": str(value)}
    if isinstance(value, (datetime, date)):
        return {"kind": type(value).__name__, "value": value.isoformat()}
    if isinstance(value, bytes):
        return {"kind": "bytes", "value": base64.b64encode(value).decode("ascii")}
    if isinstance(value, (Mapping, list, tuple)):
        seen = set() if seen is None else seen
        if id(value) in seen:
            raise ValueError("Cyclic API value cannot cross the transport")
        seen.add(id(value))
        try:
            if isinstance(value, Mapping):
                return {
                    "kind": "mapping",
                    "items": [
                        [encode(key, reference, seen), encode(item, reference, seen)]
                        for key, item in value.items()
                    ],
                }
            return {
                "kind": "tuple" if isinstance(value, tuple) else "list",
                "items": [encode(item, reference, seen) for item in value],
            }
        finally:
            seen.remove(id(value))
    return reference(value)


def decode(value, reference):
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if not isinstance(value, dict):
        raise ValueError("Invalid domain API value")
    kind = value.get("kind")
    if kind == "ref":
        return reference(value)
    if kind in ("list", "tuple"):
        items = [decode(item, reference) for item in value["items"]]
        return tuple(items) if kind == "tuple" else items
    if kind == "mapping":
        return {
            decode(key, reference): decode(item, reference)
            for key, item in value["items"]
        }
    if kind == "path":
        return Path(value["value"])
    if kind == "datetime":
        return datetime.fromisoformat(value["value"])
    if kind == "date":
        return date.fromisoformat(value["value"])
    if kind == "bytes":
        return base64.b64decode(value["value"], validate=True)
    raise ValueError("Unsupported domain API value kind")
