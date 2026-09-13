"""DockPanelModel: placement."""

from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import Slot

from .docks_tree import (
    default_layout,
    insert_at_root,
    insert_relative,
    panel_ids,
    reorder_stack_panel as reorder_panel_in_stack,
    set_active_panel,
    swap_panels,
    tabify,
)


class PlacementMixin:
    @Slot(str)
    def activate_stack_panel(self, panel_id: str) -> None:
        row = self._index_for(panel_id)
        if row is None:
            return
        panel = self._panels[row]
        if (
            not panel.visible
            or panel.detached
            or panel.dock_area == "floating"
        ):
            return
        updated_root = set_active_panel(self._layout_root, panel_id)
        if updated_root == self._layout_root:
            return
        self._layout_root = updated_root
        self._z_counter += 1
        self._panels[row] = replace(panel, z=self._z_counter)
        self._notify_layout_structure_changed()
        self._save()

    @Slot(str, int)
    def reorder_stack_panel(self, panel_id: str, target_index: int) -> None:
        updated_root = reorder_panel_in_stack(
            self._layout_root, panel_id, target_index
        )
        if updated_root == self._layout_root:
            return
        self._layout_root = updated_root
        self._notify_layout_structure_changed()
        self._save()

    @Slot(str, str, str)
    def place_panel(
            self, panel_id: str, target_panel_id: str, side: str,
    ) -> None:
        """Move a dock relative to a concrete visible target dock."""
        if panel_id == target_panel_id:
            return
        row = self._index_for(panel_id)
        target_row = self._index_for(target_panel_id)
        if row is None or target_row is None:
            return
        target = self._panels[target_row]
        if (
            not target.visible
            or target.detached
            or target.dock_area == "floating"
        ):
            return
        source_in_layout = panel_id in panel_ids(self._layout_root)
        if side == "center":
            updated_root = tabify(
                self._layout_root, target_panel_id, panel_id
            )
        elif side == "swap" and source_in_layout:
            updated_root = swap_panels(
                self._layout_root, panel_id, target_panel_id
            )
        else:
            fallback_side = "right" if side == "swap" else side
            updated_root = insert_relative(
                self._layout_root,
                target_panel_id,
                panel_id,
                fallback_side,
            )
        if updated_root is None or updated_root == self._layout_root:
            return
        self._layout_root = updated_root
        self._z_counter += 1
        self._panels[row] = replace(
            self._panels[row],
            visible=True,
            detached=False,
            dock_area="docked",
            previous_dock_area="docked",
            z=self._z_counter,
        )
        index = self.index(row, 0)
        self.dataChanged.emit(index, index)
        self._reflow_workspace()
        self._notify_layout_structure_changed()
        self._save()

    @Slot(str, str)
    def snap_panel(self, panel_id: str, dock_area: str) -> None:
        """Dock a panel into one of the five visual drop zones."""
        if dock_area not in {"left", "right", "top", "bottom", "center"}:
            return
        row = self._index_for(panel_id)
        if row is None:
            return
        self._z_counter += 1
        self._panels[row] = replace(
            self._panels[row],
            visible=True,
            dock_area=dock_area,
            detached=False,
            previous_dock_area=dock_area,
            z=self._z_counter,
        )
        index = self.index(row, 0)
        self.dataChanged.emit(index, index)
        self._layout_root = insert_at_root(
            self._layout_root, panel_id, dock_area
        )
        self._reflow_workspace()
        self._notify_layout_structure_changed()
        self._save()

    @Slot(str, float, float, float, float)
    def float_panel(self, panel_id: str, x: float, y: float, width: float, height: float) -> None:
        """Undock a panel and preserve its released floating rectangle."""
        row = self._index_for(panel_id)
        if row is None:
            return
        was_docked = self._panels[row].dock_area != "floating"
        x = max(0.0, min(0.96, x))
        y = max(0.0, min(0.96, y))
        width = max(0.20, min(1.0 - x, width))
        height = max(0.16, min(1.0 - y, height))
        self._z_counter += 1
        self._panels[row] = replace(
            self._panels[row],
            x=x,
            y=y,
            width=width,
            height=height,
            visible=True,
            dock_area="floating",
            detached=False,
            previous_dock_area=(
                self._panels[row].dock_area
                if was_docked else self._panels[row].previous_dock_area
            ),
            z=self._z_counter,
        )
        index = self.index(row, 0)
        self.dataChanged.emit(index, index)
        self._save()
        if was_docked:
            self._reflow_workspace()
            self._notify_layout_structure_changed()

    @Slot(str)
    def float_panel_inside(self, panel_id: str) -> None:
        if panel_id == "results":
            return
        row = self._index_for(panel_id)
        if row is None:
            return
        panel = self._panels[row]
        if panel.detached or panel.dock_area == "floating":
            return
        width = max(0.32, min(0.68, panel.width))
        height = max(0.26, min(0.72, panel.height))
        self.float_panel(
            panel_id,
            max(0.04, (1.0 - width) / 2),
            max(0.04, (1.0 - height) / 2),
            width,
            height,
        )

    @Slot(str)
    def detach_panel(self, panel_id: str) -> None:
        if panel_id == "results":
            return
        row = self._index_for(panel_id)
        if row is None:
            return
        panel = self._panels[row]
        if panel.detached:
            return
        previous_area = panel.dock_area
        self._z_counter += 1
        self._panels[row] = replace(
            panel,
            visible=True,
            detached=True,
            previous_dock_area=previous_area,
            z=self._z_counter,
        )
        index = self.index(row, 0)
        self.dataChanged.emit(index, index)
        self.minimumHostSizeChanged.emit()
        self._save()
        if previous_area != "floating":
            self._reflow_workspace()
            self._notify_layout_structure_changed()

    @Slot(str)
    def attach_panel(self, panel_id: str) -> None:
        self.dock_panel(panel_id)

    @Slot(str)
    def dock_panel(self, panel_id: str) -> None:
        row = self._index_for(panel_id)
        if row is None:
            return
        panel = self._panels[row]
        if panel.panel_id == "results":
            return
        target_area = panel.previous_dock_area
        if not target_area or target_area == "floating":
            target_area = self._default_dock_area(panel_id)
        self._panels[row] = replace(
            panel,
            detached=False,
            visible=True,
            dock_area=target_area,
        )
        index = self.index(row, 0)
        self.dataChanged.emit(index, index)
        if panel_id not in panel_ids(self._layout_root):
            self._layout_root = insert_at_root(
                self._layout_root, panel_id, target_area
            )
        self._reflow_workspace()
        self._layout_root = set_active_panel(self._layout_root, panel_id)
        self._notify_layout_structure_changed()
        self._save()

    @Slot(str)
    def attach_panel_floating(self, panel_id: str) -> None:
        row = self._index_for(panel_id)
        if row is None or panel_id == "results":
            return
        panel = self._panels[row]
        if not panel.detached:
            return
        width = max(0.20, min(0.80, panel.width))
        height = max(0.16, min(0.80, panel.height))
        x = max(0.0, min(1.0 - width, panel.x))
        y = max(0.0, min(1.0 - height, panel.y))
        self._z_counter += 1
        self._panels[row] = replace(
            panel,
            x=x,
            y=y,
            width=width,
            height=height,
            detached=False,
            visible=True,
            dock_area="floating",
            z=self._z_counter,
        )
        index = self.index(row, 0)
        self.dataChanged.emit(index, index)
        self.minimumHostSizeChanged.emit()
        self._save()

    @Slot()
    def reset_layout(self) -> None:
        previous_visibility = {
            panel.panel_id: panel.visible for panel in self._panels
        }
        self.beginResetModel()
        self._panels = self._defaults()
        self._layout_root = default_layout()
        self._z_counter = max(panel.z for panel in self._panels)
        self.endResetModel()
        self.minimumHostSizeChanged.emit()
        self._save()
        for panel in self._panels:
            if previous_visibility.get(panel.panel_id) != panel.visible:
                self.panelVisibilityChanged.emit(
                    panel.panel_id, panel.visible
                )
