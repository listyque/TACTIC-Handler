"""Qt Quick rendering backend policy."""

from __future__ import annotations

from collections.abc import MutableMapping
import sys


AUTOMATIC_RENDER_BACKEND = "automatic"
SUPPORTED_RENDER_BACKENDS = frozenset({
    AUTOMATIC_RENDER_BACKEND,
    "opengl",
    "d3d11",
    "d3d12",
    "vulkan",
    "software",
})


def normalize_render_backend(value: object) -> str:
    backend = str(value or AUTOMATIC_RENDER_BACKEND).strip().lower()
    if backend not in SUPPORTED_RENDER_BACKENDS:
        return AUTOMATIC_RENDER_BACKEND
    return backend


def effective_render_backend(
    value: object,
    *,
    platform_name: str | None = None,
) -> str:
    """Return the QSG backend, or an empty value for Qt's native default."""

    backend = normalize_render_backend(value)
    if backend != AUTOMATIC_RENDER_BACKEND:
        return backend
    platform_name = platform_name or sys.platform
    # Qt's Direct3D swapchain can trigger full-display DWM/MPO/HDR flicker
    # on a small scene repaint. OpenGL keeps GPU rendering without that DXGI
    # presentation path and is therefore the safe Windows automatic choice.
    return "opengl" if platform_name == "win32" else ""


def apply_render_backend(
    value: object,
    *,
    environment: MutableMapping[str, str],
    platform_name: str | None = None,
) -> str:
    """Apply the preference before QApplication owns a scene graph."""

    selected = normalize_render_backend(value)
    if (
        environment.get("QT_QUICK_BACKEND")
        or environment.get("QSG_RHI_BACKEND")
    ):
        return selected
    backend = effective_render_backend(
        selected,
        platform_name=platform_name,
    )
    if backend == "software":
        # Software is a Qt Quick scene-graph adaptation, not an RHI backend.
        # Passing it through QSG_RHI_BACKEND makes Qt reject the value and
        # silently fall back to a hardware backend.
        environment["QT_QUICK_BACKEND"] = "software"
    elif backend:
        environment["QSG_RHI_BACKEND"] = backend
    return selected
