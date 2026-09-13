"""Screen-aware persistence helpers for the main application window."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QGuiApplication, QScreen


MAIN_WINDOW_MINIMUM_WIDTH = 760
MAIN_WINDOW_MINIMUM_HEIGHT = 640


@dataclass(frozen=True)
class ScreenGeometry:
    """Stable screen identity and its logical-pixel work area."""

    identity: str
    name: str
    x: int
    y: int
    width: int
    height: int

    @property
    def rect(self) -> QRect:
        return QRect(self.x, self.y, self.width, self.height)


def _screen_identity(screen: QScreen) -> str:
    parts = (
        screen.name(),
        screen.manufacturer(),
        screen.model(),
        screen.serialNumber(),
    )
    return "|".join(str(part or "").strip() for part in parts)


def describe_screen(screen: QScreen) -> ScreenGeometry:
    area = screen.availableGeometry()
    return ScreenGeometry(
        identity=_screen_identity(screen),
        name=screen.name(),
        x=area.x(),
        y=area.y(),
        width=area.width(),
        height=area.height(),
    )


def current_screens() -> tuple[list[ScreenGeometry], str]:
    screens = [describe_screen(screen) for screen in QGuiApplication.screens()]
    primary = QGuiApplication.primaryScreen()
    primary_identity = _screen_identity(primary) if primary is not None else ""
    return screens, primary_identity


def _intersection_area(left: QRect, right: QRect) -> int:
    intersection = left.intersected(right)
    return max(0, intersection.width()) * max(0, intersection.height())


def _pick_screen(
    saved: Mapping[str, Any],
    screens: list[ScreenGeometry],
    primary_identity: str,
) -> tuple[ScreenGeometry, bool]:
    saved_identity = str(saved.get("screen_identity", "") or "")
    saved_name = str(saved.get("screen_name", "") or "")
    for screen in screens:
        if saved_identity and screen.identity == saved_identity:
            return screen, True
    for screen in screens:
        if saved_name and screen.name == saved_name:
            return screen, True

    saved_rect = QRect(
        int(saved.get("x", 80)),
        int(saved.get("y", 60)),
        max(1, int(saved.get("width", 1280))),
        max(1, int(saved.get("height", 820))),
    )
    intersecting = max(
        screens,
        key=lambda screen: _intersection_area(saved_rect, screen.rect),
    )
    if _intersection_area(saved_rect, intersecting.rect) > 0:
        return intersecting, False
    for screen in screens:
        if screen.identity == primary_identity:
            return screen, False
    return screens[0], False


def _map_from_saved_screen(
    saved: Mapping[str, Any],
    target: ScreenGeometry,
) -> tuple[int, int]:
    old_width = int(saved.get("screen_width", 0) or 0)
    old_height = int(saved.get("screen_height", 0) or 0)
    if old_width <= 0 or old_height <= 0:
        return target.x, target.y
    old_x = int(saved.get("screen_x", 0) or 0)
    old_y = int(saved.get("screen_y", 0) or 0)
    relative_x = (int(saved.get("x", old_x)) - old_x) / old_width
    relative_y = (int(saved.get("y", old_y)) - old_y) / old_height
    return (
        target.x + round(relative_x * target.width),
        target.y + round(relative_y * target.height),
    )


def resolve_window_state(
    saved: Mapping[str, Any],
    screens: Iterable[ScreenGeometry],
    primary_identity: str = "",
) -> dict[str, Any]:
    """Resolve a saved logical geometry against the current monitor layout."""

    available = [screen for screen in screens if screen.width > 0 and screen.height > 0]
    if not available:
        return {
            "x": int(saved.get("x", 80)),
            "y": int(saved.get("y", 60)),
            "width": max(MAIN_WINDOW_MINIMUM_WIDTH, int(saved.get("width", 1280))),
            "height": max(MAIN_WINDOW_MINIMUM_HEIGHT, int(saved.get("height", 820))),
            "maximized": bool(saved.get("maximized", False)),
        }

    target, exact_screen = _pick_screen(saved, available, primary_identity)
    width = min(
        target.width,
        max(MAIN_WINDOW_MINIMUM_WIDTH, int(saved.get("width", 1280))),
    )
    height = min(
        target.height,
        max(MAIN_WINDOW_MINIMUM_HEIGHT, int(saved.get("height", 820))),
    )
    saved_rect = QRect(
        int(saved.get("x", 80)),
        int(saved.get("y", 60)),
        width,
        height,
    )
    if exact_screen or _intersection_area(saved_rect, target.rect) > 0:
        x = int(saved.get("x", target.x))
        y = int(saved.get("y", target.y))
    else:
        x, y = _map_from_saved_screen(saved, target)

    # Negative desktop coordinates are valid for monitors left of the primary.
    x = min(max(x, target.x), target.x + target.width - width)
    y = min(max(y, target.y), target.y + target.height - height)
    return {
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "maximized": bool(saved.get("maximized", False)),
        "screen_identity": target.identity,
        "screen_name": target.name,
        "screen_x": target.x,
        "screen_y": target.y,
        "screen_width": target.width,
        "screen_height": target.height,
    }


def load_main_window_state(settings: Mapping[str, Any]) -> dict[str, Any]:
    saved = {
        "x": int(settings.get("window/x", 80) or 80),
        "y": int(settings.get("window/y", 60) or 60),
        "width": int(settings.get("window/width", 1280) or 1280),
        "height": int(settings.get("window/height", 820) or 820),
        "maximized": bool(settings.get("window/maximized", False)),
        "screen_identity": str(settings.get("window/screen_identity", "") or ""),
        "screen_name": str(settings.get("window/screen_name", "") or ""),
        "screen_x": int(settings.get("window/screen_x", 0) or 0),
        "screen_y": int(settings.get("window/screen_y", 0) or 0),
        "screen_width": int(settings.get("window/screen_width", 0) or 0),
        "screen_height": int(settings.get("window/screen_height", 0) or 0),
    }
    screens, primary_identity = current_screens()
    return resolve_window_state(saved, screens, primary_identity)


def screen_for_window_rect(x: int, y: int, width: int, height: int) -> ScreenGeometry | None:
    screens = QGuiApplication.screens()
    if not screens:
        return None
    rect = QRect(x, y, max(1, width), max(1, height))
    screen = max(
        screens,
        key=lambda item: _intersection_area(rect, item.availableGeometry()),
    )
    if _intersection_area(rect, screen.availableGeometry()) == 0:
        screen = (
            QGuiApplication.screenAt(QPoint(rect.center()))
            or QGuiApplication.primaryScreen()
        )
    return describe_screen(screen) if screen is not None else None
