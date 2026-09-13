"""Value objects for workspace models."""

from __future__ import annotations

from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True)
class DockPanel:
    panel_id: str
    title: str
    kind: str
    x: float
    y: float
    width: float
    height: float
    visible: bool = True
    closable: bool = True
    z: int = 0
    dock_area: str = "floating"
    detached: bool = False
    previous_dock_area: str = ""
