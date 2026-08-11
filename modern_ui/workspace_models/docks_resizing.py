"""DockPanelModel: tree-based resizing."""

from __future__ import annotations

from PySide6.QtCore import Slot

from .docks_tree import clamp_layout_ratios, resize_split_for_edge
from .docks_types import DockPanel


class ResizingMixin:
    @staticmethod
    def _minimum_panel_size(
            panel: DockPanel, host_width: float, host_height: float,
    ) -> tuple[float, float]:
        if host_width <= 1.0 or host_height <= 1.0:
            return {
                "results": (0.22, 0.20),
                "snapshot": (0.28, 0.20),
                "tasks": (0.28, 0.18),
                "description": (0.28, 0.18),
                "notes": (0.30, 0.20),
                "task_calendar": (0.30, 0.20),
            }.get(panel.kind, (0.24, 0.16))
        pixel_sizes = {
            # Docked workspace panels reflow into compact presentations. Their
            # tiled limits are intentionally smaller than detached-window
            # limits from WindowSizing.qml.
            "results": (220, 260),
            "snapshot": (280, 260),
            "tasks": (280, 220),
            "task_calendar": (300, 360),
            "description": (280, 220),
            "notes": (300, 300),
            "drop_plate": (480, 360),
            "advanced_search": (380, 320),
            "fast_controls": (360, 150),
            "watch_folders": (480, 360),
            "db_table": (620, 460),
            "commit_queue": (720, 480),
        }
        minimum_width, minimum_height = pixel_sizes.get(
            panel.kind, (320, 220)
        )
        return (
            min(1.0, minimum_width / max(1.0, host_width)),
            min(1.0, minimum_height / max(1.0, host_height)),
        )

    def _visible_docked_panels(self) -> list[DockPanel]:
        return [
            panel for panel in self._panels
            if panel.visible and not panel.detached
            and panel.dock_area != "floating"
        ]

    def _tree_minimum_sizes(
            self, host_width: float, host_height: float,
    ) -> dict[str, tuple[float, float]]:
        return {
            panel.panel_id: self._minimum_panel_size(
                panel, host_width, host_height
            )
            for panel in self._visible_docked_panels()
        }

    @Slot(str, str, float, float, float, float)
    @Slot(str, str, float, float, float, float, float, float)
    def resize_panel(
            self,
            panel_id: str,
            edge: str,
            x: float,
            y: float,
            width: float,
            height: float,
            host_width: float = 1.0,
            host_height: float = 1.0,
    ) -> None:
        """Commit one split ratio when the pointer is released."""
        row = self._index_for(panel_id)
        if row is None:
            return
        if self._panels[row].dock_area == "floating":
            self.set_geometry(panel_id, x, y, width, height)
            return
        self._resize_tree_boundary(
            panel_id,
            edge,
            x,
            y,
            width,
            height,
            host_width,
            host_height,
            save=True,
        )

    @Slot(str, str, float, float, float, float)
    @Slot(str, str, float, float, float, float, float, float)
    def preview_resize_panel(
            self,
            panel_id: str,
            edge: str,
            x: float,
            y: float,
            width: float,
            height: float,
            host_width: float = 1.0,
            host_height: float = 1.0,
    ) -> None:
        """Preview one ratio without writing QSettings during pointer motion."""
        row = self._index_for(panel_id)
        if row is None or self._panels[row].dock_area == "floating":
            return
        self._resize_tree_boundary(
            panel_id,
            edge,
            x,
            y,
            width,
            height,
            host_width,
            host_height,
            save=False,
        )

    def _resize_tree_boundary(
            self,
            panel_id: str,
            edge: str,
            x: float,
            y: float,
            width: float,
            height: float,
            host_width: float,
            host_height: float,
            *,
            save: bool,
    ) -> None:
        row = self._index_for(panel_id)
        if row is None or not self._can_resize_edge(self._panels[row], edge):
            return
        boundary = {
            "left": x,
            "right": x + width,
            "top": y,
            "bottom": y + height,
        }.get(edge)
        if boundary is None:
            return
        panels = self._visible_docked_panels()
        available = {panel.panel_id for panel in panels}
        updated_root, found = resize_split_for_edge(
            self._layout_root,
            panel_id,
            edge,
            boundary,
            available,
            self._tree_minimum_sizes(host_width, host_height),
        )
        if not found or updated_root == self._layout_root:
            if save:
                self._save()
            return
        self._layout_root = updated_root
        self._reflow_workspace(save=False)
        if save:
            self._save()

    @Slot(float, float)
    def ensure_minimum_sizes(
            self, host_width: float, host_height: float,
    ) -> None:
        """Project usable geometry without overwriting preferred ratios."""
        if host_width <= 1.0 or host_height <= 1.0:
            return
        panels = self._visible_docked_panels()
        available = {panel.panel_id for panel in panels}
        updated_root = clamp_layout_ratios(
            self._layout_root,
            available,
            self._tree_minimum_sizes(host_width, host_height),
        )
        self._reflow_workspace(
            save=False,
            projected_root=updated_root,
        )
