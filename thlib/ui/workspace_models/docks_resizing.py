"""DockPanelModel: tree-based resizing."""

from __future__ import annotations

from PySide6.QtCore import Slot

from .docks_tree import (
    clamp_layout_ratios,
    resize_split_for_edge,
    subtree_minimum_size,
)
from .docks_types import DockPanel
from .docks_projection import runtime


class ResizingMixin:
    @Slot(str)
    def begin_resize(self, panel_id: str) -> None:
        if self._index_for(panel_id) is not None and self._resize_restore is None:
            self._resize_restore = (panel_id, self._layout_root)

    @Slot(str)
    def cancel_resize(self, panel_id: str) -> None:
        if self._resize_restore is None or self._resize_restore[0] != panel_id:
            return
        self._layout_root = self._resize_restore[1]
        self._resize_restore = None
        self._reflow_workspace(save=False)

    @staticmethod
    def _minimum_panel_pixel_size(panel: DockPanel) -> tuple[int, int]:
        return tuple(runtime().call("minimum", panel.kind))

    @classmethod
    def _minimum_panel_size(
            cls, panel: DockPanel, host_width: float, host_height: float,
    ) -> tuple[float, float]:
        minimum_width, minimum_height = cls._minimum_panel_pixel_size(
            panel
        )
        if host_width <= 1.0 or host_height <= 1.0:
            return {
                "results": (0.22, 0.20),
                "snapshot": (0.28, 0.20),
                "tasks": (0.28, 0.18),
                "description": (0.28, 0.18),
                "notes": (0.30, 0.20),
                "task_calendar": (0.30, 0.20),
            }.get(panel.kind, (0.24, 0.16))
        return (
            min(1.0, minimum_width / max(1.0, host_width)),
            min(1.0, minimum_height / max(1.0, host_height)),
        )

    def _minimum_host_pixel_size(self) -> tuple[float, float]:
        """Return the space required by the current visible dock tree."""
        if self._maximized_panel:
            return self._minimum_panel_pixel_size(self._panels[self._index_for(self._maximized_panel)])
        visible = [
            panel for panel in self._panels
            if panel.visible and not panel.detached
        ]
        docked = {
            panel.panel_id for panel in visible
            if panel.dock_area != "floating"
        }
        minimum_sizes = {
            panel.panel_id: self._minimum_panel_pixel_size(panel)
            for panel in visible
        }
        tree_width, tree_height = subtree_minimum_size(
            self._layout_root, docked, minimum_sizes
        )
        floating_sizes = [
            minimum_sizes[panel.panel_id] for panel in visible
            if panel.dock_area == "floating"
        ]
        if floating_sizes:
            tree_width = max(
                tree_width, max(value[0] for value in floating_sizes)
            )
            tree_height = max(
                tree_height, max(value[1] for value in floating_sizes)
            )
        return tree_width, tree_height

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
        self._resize_restore = None
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
        """Preview one ratio without writing config during pointer motion."""
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
        minimum_sizes = self._tree_minimum_sizes(host_width, host_height)
        updated_root, found = resize_split_for_edge(
            self._layout_root,
            panel_id,
            edge,
            boundary,
            available,
            minimum_sizes,
        )
        if found:
            # Moving an outer divider changes the available rectangle of every
            # nested split below it.  Clamping only that outer split preserves
            # enough aggregate space but can still leave one nested panel below
            # its own minimum.  Re-clamp the complete projected tree so every
            # visible leaf remains usable while an adjacent dock is dragged.
            updated_root = clamp_layout_ratios(
                updated_root,
                available,
                minimum_sizes,
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
        if self._maximized_panel:
            return
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
