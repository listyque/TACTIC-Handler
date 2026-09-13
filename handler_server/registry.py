from __future__ import annotations

from collections.abc import Callable


class CommandRegistry:
    def __init__(self):
        self._actions: dict[str, Callable] = {}

    def register(self, name: str, callback: Callable) -> None:
        name = str(name or "").strip()
        if not name or name in self._actions:
            raise ValueError(f"Action is already registered or invalid: {name}")
        if not callable(callback):
            raise TypeError("Command callback must be callable")
        self._actions[name] = callback

    def unregister(self, name: str) -> None:
        self._actions.pop(str(name or ""), None)

    def capabilities(self) -> list[str]:
        return sorted(self._actions)

    def execute(self, name: str, payload: dict):
        callback = self._actions.get(str(name or ""))
        if callback is None:
            raise LookupError(f"Action is not registered: {name}")
        return callback(dict(payload or {}))
