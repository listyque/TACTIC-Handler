"""Application composition primitives.

This module deliberately contains no feature construction.  It provides the two
small contracts needed by the composition root: one registry for the public QML
namespace and one ordered lifecycle for services that own background resources.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any


class QmlBindingRegistry:
    """Collect and validate the root QML context contract before publishing it."""

    def __init__(self) -> None:
        self._bindings: dict[str, Any] = {}
        self._owners: dict[str, str] = {}

    def add_group(self, owner: str, bindings: Mapping[str, Any]) -> None:
        owner_name = str(owner or "application").strip()
        for raw_name, value in bindings.items():
            name = str(raw_name or "").strip()
            if not name:
                raise ValueError(f"{owner_name} declared an empty QML binding name")
            if name in self._bindings:
                previous_owner = self._owners[name]
                raise ValueError(
                    f"QML binding {name!r} is owned by both "
                    f"{previous_owner!r} and {owner_name!r}"
                )
            self._bindings[name] = value
            self._owners[name] = owner_name

    def publish(self, context) -> None:
        for name, value in self._bindings.items():
            context.setContextProperty(name, value)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._bindings)


class LifecycleRegistry:
    """Run explicitly ordered shutdown hooks once."""

    def __init__(self) -> None:
        self._hooks: list[tuple[str, Any]] = []
        self._closed = False

    def add_services(self, services: Iterable[Any]) -> None:
        for service in services:
            shutdown = getattr(service, "shutdown", None)
            if not callable(shutdown):
                raise TypeError(
                    f"Managed service {type(service).__name__} has no shutdown()"
                )
            self._hooks.append((type(service).__name__, shutdown))

    def shutdown(self) -> None:
        if self._closed:
            return
        self._closed = True
        for _name, shutdown in self._hooks:
            shutdown()

    @property
    def service_names(self) -> tuple[str, ...]:
        return tuple(name for name, _shutdown in self._hooks)


@dataclass
class ApplicationRuntime:
    """Own the constructed feature bundles and their public application contracts."""

    controller: Any
    localization: Any
    debug_log: Any
    tray: Any
    handler_server: Any
    server_updates: Any
    watch_folders: Any
    script_editor: Any
    bindings: QmlBindingRegistry
    lifecycle: LifecycleRegistry
    bundles: tuple[Any, ...] = field(default_factory=tuple)

    def publish_qml_bindings(self, context) -> None:
        self.bindings.publish(context)

    def shutdown(self) -> None:
        self.lifecycle.shutdown()
