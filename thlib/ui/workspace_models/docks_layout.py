"""DockPanelModel: layout."""

from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import Slot

from .docks_tree import (
    insert_at_root,
    layout_rectangles,
    normalize_active_panels,
    panel_ids,
    set_active_panel,
    stack_for_panel,
    tabify,
)


class LayoutMixin:
    def _reflow_workspace(
            self, *, save: bool = True, projected_root=None,
    ) -> None:
        """Project the structural split tree into normalized panel geometry."""
        available = {
            panel.panel_id for panel in self._panels
            if panel.visible and not panel.detached
            and panel.dock_area != "floating"
        }
        missing = available - set(panel_ids(self._layout_root))
        for panel_id in sorted(missing):
            target_id = self._default_stack_target(panel_id)
            if target_id and target_id in panel_ids(self._layout_root):
                target_stack = stack_for_panel(
                    self._layout_root, target_id
                )
                previous_active = (
                    target_stack.active_panel_id if target_stack else ""
                )
                self._layout_root = tabify(
                    self._layout_root, target_id, panel_id
                )
                if previous_active:
                    self._layout_root = set_active_panel(
                        self._layout_root, previous_active
                    )
            else:
                self._layout_root = insert_at_root(
                    self._layout_root,
                    panel_id,
                    self._default_dock_area(panel_id),
                )
        self._layout_root = normalize_active_panels(
            self._layout_root, available
        )
        layout_root = (
            projected_root if projected_root is not None
            else self._layout_root
        )
        geometries = layout_rectangles(layout_root, available)
        changed_rows: list[int] = []
        for panel_id, (x, y, width, height) in geometries.items():
            row = self._index_for(panel_id)
            if row is None:
                continue
            panel = self._panels[row]
            updated = replace(panel, x=x, y=y, width=width, height=height)
            if updated != panel:
                self._panels[row] = updated
                if row not in changed_rows:
                    changed_rows.append(row)
        for row in changed_rows:
            model_index = self.index(row, 0)
            self.dataChanged.emit(model_index, model_index)
        if changed_rows and save:
            self._save()

    def _notify_layout_structure_changed(self) -> None:
        if not self._panels:
            return
        self.minimumHostSizeChanged.emit()
        self.dataChanged.emit(
            self.index(0, 0), self.index(len(self._panels) - 1, 0)
        )

    @Slot(str)
    def close_panel(self, panel_id: str) -> None:
        row = self._index_for(panel_id)
        if row is not None and self._panels[row].closable:
            was_docked = (
                not self._panels[row].detached
                and self._panels[row].dock_area != "floating"
            )
            self._replace(panel_id, visible=False, detached=False)
            self.panelVisibilityChanged.emit(panel_id, False)
            if was_docked:
                self._reflow_workspace()
                self._notify_layout_structure_changed()

    @Slot(str)
    def close_detached_panel(self, panel_id: str) -> None:
        row = self._index_for(panel_id)
        if row is None or panel_id == "results":
            return
        panel = self._panels[row]
        if not panel.detached:
            return
        index = self.index(row, 0)
        self._panels[row] = replace(panel, visible=False)
        self.dataChanged.emit(index, index)
        self._panels[row] = replace(self._panels[row], detached=False)
        self.dataChanged.emit(index, index)
        self.minimumHostSizeChanged.emit()
        self._save()
        self.panelVisibilityChanged.emit(panel_id, False)

    @Slot(str)
    def show_panel(self, panel_id: str) -> None:
        row = self._index_for(panel_id)
        if row is None:
            return
        panel = self._panels[row]
        if self.is_panel_presented(panel_id):
            if panel.detached or panel.dock_area == "floating":
                self.raise_panel(panel_id)
            return
        self._z_counter += 1
        self._replace(panel_id, visible=True, z=self._z_counter)
        self.panelVisibilityChanged.emit(panel_id, True)
        if self._panels[row].dock_area != "floating":
            self._layout_root = set_active_panel(
                self._layout_root, panel_id
            )
            self._reflow_workspace()
            self._layout_root = set_active_panel(
                self._layout_root, panel_id
            )
            self._notify_layout_structure_changed()

    @Slot(str)
    def toggle_panel(self, panel_id: str) -> None:
        """Apply a dock visibility toggle from the workspace menu."""
        row = self._index_for(panel_id)
        if row is None:
            return
        panel = self._panels[row]
        if panel.visible:
            self.close_panel(panel_id)
        else:
            self.show_panel(panel_id)

    @Slot(str)
    def raise_panel(self, panel_id: str) -> None:
        self._z_counter += 1
        self._replace(panel_id, z=self._z_counter)

    @Slot(str, float, float, float, float)
    def set_geometry(self, panel_id: str, x: float, y: float, width: float, height: float) -> None:
        row = self._index_for(panel_id)
        detached = row is not None and self._panels[row].detached
        if detached:
            x = max(-3.0, min(3.0, x))
            y = max(-3.0, min(3.0, y))
            width = max(0.20, min(3.0, width))
            height = max(0.16, min(3.0, height))
        else:
            x = max(0.0, min(0.96, x))
            y = max(0.0, min(0.96, y))
            width = max(0.20, min(1.0 - x, width))
            height = max(0.16, min(1.0 - y, height))
        self._replace(panel_id, x=x, y=y, width=width, height=height)
