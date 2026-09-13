"""DockPanelModel: records."""

from __future__ import annotations

import json
from dataclasses import asdict, replace
from math import isfinite

from PySide6.QtCore import QModelIndex, QSignalBlocker, Qt, Slot

from .docks_types import DockPanel
from .docks_tree import (
    deserialize_layout,
    has_resizable_edge,
    serialize_layout,
    stack_for_panel,
)


class RecordsMixin:
    @staticmethod
    def _default_dock_area(panel_id: str) -> str:
        return {
            "results": "center",
            "snapshot": "right",
            "tasks": "center",
            "description": "right",
            "notes": "right",
            "knowledge": "right",
            "task_calendar": "right",
            "timesheet": "right",
            "work_reports": "right",
            "cost_reports": "right",
            "drop_plate": "center",
            "advanced_search": "center",
            "db_table": "center",
        }.get(panel_id, "right")

    @staticmethod
    def _default_stack_target(panel_id: str) -> str:
        """Return the existing dock whose tab stack owns a new panel."""
        return {
            "advanced_search": "results",
            "drop_plate": "tasks",
            "db_table": "tasks",
            "snapshot": "notes",
            "description": "notes",
            "task_calendar": "notes",
            "timesheet": "notes",
            "work_reports": "notes",
            "cost_reports": "notes",
            "knowledge": "notes",
        }.get(panel_id, "")

    @staticmethod
    def _defaults() -> list[DockPanel]:
        return [
            DockPanel("results", "Results", "results", 0.0000, 0.00, 0.2244, 1.00, True, False, 1, "center"),
            DockPanel("snapshot", "Snapshot Browser", "snapshot", 0.6600, 0.00, 0.3400, 1.00, True, True, 2, "right"),
            DockPanel("tasks", "Tasks", "tasks", 0.2244, 0.00, 0.4356, 1.00, True, True, 3, "center"),
            DockPanel("description", "Description", "description", 0.6600, 0.00, 0.3400, 1.00, False, True, 4, "right"),
            DockPanel("notes", "Task Inspector", "notes", 0.6600, 0.00, 0.3400, 1.00, True, True, 5, "right"),
            DockPanel("task_calendar", "Task Calendar", "task_calendar", 0.6600, 0.00, 0.3400, 1.00, True, True, 8, "right"),
            DockPanel("timesheet", "Timesheet", "timesheet", 0.6600, 0.00, 0.3400, 1.00, False, True, 14, "right"),
            DockPanel("work_reports", "Work Reports", "work_reports", 0.6600, 0.00, 0.3400, 1.00, False, True, 15, "right"),
            DockPanel("cost_reports", "Cost Reports", "cost_reports", 0.6600, 0.00, 0.3400, 1.00, False, True, 16, "right"),
            DockPanel("knowledge", "Knowledge Base", "knowledge", 0.6600, 0.00, 0.3400, 1.00, False, True, 17, "right"),
            DockPanel("drop_plate", "Drop Plate", "drop_plate", 0.2244, 0.00, 0.4356, 1.00, False, True, 6, "center"),
            DockPanel("advanced_search", "Advanced Search", "advanced_search", 0.0000, 0.00, 0.2244, 1.00, False, True, 7, "center"),
            DockPanel("db_table", "Database Editor", "db_table", 0.2244, 0.00, 0.4356, 1.00, False, True, 13, "center"),
        ]

    def _decode_panels(self, values) -> list[DockPanel] | None:
        if not isinstance(values, list):
            return None
        defaults = {panel.panel_id: panel for panel in self._defaults()}
        restored = {}
        for value in values:
            if not isinstance(value, dict):
                continue
            panel_id = value.get("panel_id")
            default = defaults.get(panel_id)
            if default is None:
                continue
            detached = value.get("detached")
            detached = detached if isinstance(detached, bool) else default.detached
            if panel_id == "results":
                detached = False
            dock_area = value.get("dock_area")
            if dock_area not in {
                "left", "right", "top", "bottom", "center",
                "docked", "floating",
            }:
                dock_area = self._default_dock_area(panel_id)
            previous_area = value.get("previous_dock_area")
            if not isinstance(previous_area, str):
                previous_area = default.previous_dock_area
            def number(name: str, fallback: float) -> float:
                try:
                    result = float(value.get(name, fallback))
                except (TypeError, ValueError):
                    return fallback
                return result if isfinite(result) else fallback

            x = number("x", default.x)
            y = number("y", default.y)
            width = number("width", default.width)
            height = number("height", default.height)
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
            visible = value.get("visible")
            visible = visible if isinstance(visible, bool) else default.visible
            try:
                z = int(value.get("z", default.z))
            except (TypeError, ValueError):
                z = default.z
            title = value.get("title")
            title = title if isinstance(title, str) else default.title
            if panel_id == "notes":
                title = default.title
            restored[panel_id] = DockPanel(
                panel_id,
                title,
                default.kind,
                x,
                y,
                width,
                height,
                visible,
                default.closable,
                z,
                dock_area,
                detached,
                previous_area,
            )
        if not restored:
            return None
        return [restored.get(panel.panel_id, panel) for panel in self._defaults()]

    def _restore(self):
        raw = self._settings.get(self._settings_key, "")
        invalid = bool(raw)
        if raw:
            try:
                decoded = json.loads(raw)
            except (TypeError, ValueError):
                decoded = None
            if isinstance(decoded, dict):
                unexpected = set(decoded) - {"panels", "layout"}
                if unexpected:
                    return None, None, invalid
                panels = self._decode_panels(decoded.get("panels"))
                if panels:
                    layout = deserialize_layout(
                        decoded.get("layout"),
                        {panel.panel_id for panel in panels},
                    )
                    return panels, layout, layout is None
        return None, None, invalid

    def capture_layout(self) -> dict:
        """Return the canonical workspace layout document.

        Local persistence and shared server presets intentionally use this
        exact unversioned shape.  The panel model remains the sole owner of
        validation and normalization for both paths.
        """
        return {
            "panels": [asdict(panel) for panel in self._panels],
            "layout": serialize_layout(self._layout_root),
        }

    def apply_layout(self, value: object) -> bool:
        """Validate and apply a captured workspace layout atomically."""
        if not isinstance(value, dict) or set(value) != {"panels", "layout"}:
            return False
        panels = self._decode_panels(value.get("panels"))
        if not panels:
            return False
        layout = deserialize_layout(
            value.get("layout"),
            {panel.panel_id for panel in panels},
        )
        if layout is None:
            return False

        if panels == self._panels and layout == self._layout_root:
            return True

        role_ids = tuple(self.roleNames())
        previous_role_values = [
            {
                role: self.data(self.index(row, 0), role)
                for role in role_ids
            }
            for row in range(len(self._panels))
        ]
        previous_panels = self._panels
        previous_layout = self._layout_root
        previous_z_counter = self._z_counter
        previous_visibility = {
            panel.panel_id: panel.visible for panel in self._panels
        }

        try:
            # The application owns one fixed row for each known dock.
            # Updating those rows in place lets QML keep the DockPanel and
            # its loaded content alive while a Search Tab layout is exchanged.
            with QSignalBlocker(self):
                self._panels = panels
                self._layout_root = layout
                self._z_counter = max(
                    (panel.z for panel in panels), default=0
                )
                # Newly introduced application docks are supplied by
                # _decode_panels; place visible additions without changing
                # the stored format.
                self._reflow_workspace(save=False)
        except Exception:
            self._panels = previous_panels
            self._layout_root = previous_layout
            self._z_counter = previous_z_counter
            raise

        changed_rows: list[tuple[int, list[int]]] = []
        for row in range(len(self._panels)):
            model_index = self.index(row, 0)
            changed_roles = [
                role
                for role in role_ids
                if previous_role_values[row][role]
                != self.data(model_index, role)
            ]
            if changed_roles:
                changed_rows.append((row, changed_roles))

        self.minimumHostSizeChanged.emit()
        self._save()
        for row, changed_roles in changed_rows:
            model_index = self.index(row, 0)
            self.dataChanged.emit(
                model_index, model_index, changed_roles
            )
        for panel in self._panels:
            if previous_visibility.get(panel.panel_id) != panel.visible:
                self.panelVisibilityChanged.emit(
                    panel.panel_id, panel.visible
                )
        return True

    def _save(self) -> None:
        self._settings[self._settings_key] = json.dumps(
            self.capture_layout(), separators=(",", ":")
        )

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.IdRole: b"panelId", self.TitleRole: b"title", self.KindRole: b"kind",
            self.XRole: b"panelX", self.YRole: b"panelY", self.WidthRole: b"panelWidth",
            self.HeightRole: b"panelHeight", self.VisibleRole: b"panelVisible",
            self.ClosableRole: b"closable", self.ZRole: b"stackOrder",
            self.DockAreaRole: b"dockArea",
            self.CanResizeLeftRole: b"canResizeLeft",
            self.CanResizeRightRole: b"canResizeRight",
            self.CanResizeTopRole: b"canResizeTop",
            self.CanResizeBottomRole: b"canResizeBottom",
            self.DetachedRole: b"detached",
            self.PanelTitleRole: b"panelTitle",
            self.StackActiveRole: b"stackActive",
            self.StackPanelsRole: b"stackPanels",
            self.StackSizeRole: b"stackSize",
        }

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._panels)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._panels):
            return None
        panel = self._panels[index.row()]
        stack = None
        if not panel.detached and panel.dock_area != "floating":
            stack = stack_for_panel(self._layout_root, panel.panel_id)
        stack_members = []
        if stack is not None:
            for panel_id in stack.panel_ids:
                member_row = self._index_for(panel_id)
                if member_row is None:
                    continue
                member = self._panels[member_row]
                if (
                    not member.visible
                    or member.detached
                    or member.dock_area == "floating"
                ):
                    continue
                stack_members.append({
                    "panelId": member.panel_id,
                    "title": self._stack_panel_title(member),
                    "kind": member.kind,
                    "closable": member.closable,
                    "active": stack.active_panel_id == member.panel_id,
                })
        stack_active = (
            not stack_members
            or stack is None
            or stack.active_panel_id == panel.panel_id
        )
        return {
            self.IdRole: panel.panel_id, self.TitleRole: panel.title, self.KindRole: panel.kind,
            self.XRole: panel.x, self.YRole: panel.y, self.WidthRole: panel.width,
            self.HeightRole: panel.height, self.VisibleRole: panel.visible,
            self.ClosableRole: panel.closable, self.ZRole: panel.z,
            self.DockAreaRole: panel.dock_area,
            self.CanResizeLeftRole: self._can_resize_edge(panel, "left"),
            self.CanResizeRightRole: self._can_resize_edge(panel, "right"),
            self.CanResizeTopRole: self._can_resize_edge(panel, "top"),
            self.CanResizeBottomRole: self._can_resize_edge(panel, "bottom"),
            self.DetachedRole: panel.detached,
            self.PanelTitleRole: panel.title,
            self.StackActiveRole: stack_active,
            self.StackPanelsRole: stack_members,
            self.StackSizeRole: len(stack_members),
        }.get(role)

    @staticmethod
    def _stack_panel_title(panel: DockPanel) -> str:
        return {
            "snapshot": "Snapshots",
            "tasks": "Tasks",
            "task_calendar": "Calendar",
            "timesheet": "Timesheet",
            "work_reports": "Work Reports",
            "cost_reports": "Cost Reports",
            "notes": "Task Inspector",
            "knowledge": "Knowledge Base",
            "description": "Description",
            "results": "Search",
        }.get(panel.kind, panel.title)

    def _index_for(self, panel_id: str) -> int | None:
        return next((index for index, panel in enumerate(self._panels) if panel.panel_id == panel_id), None)

    @Slot(str, result=bool)
    def is_panel_visible(self, panel_id: str) -> bool:
        row = self._index_for(str(panel_id or ""))
        return row is not None and bool(self._panels[row].visible)

    @Slot(str, result=bool)
    def is_panel_presented(self, panel_id: str) -> bool:
        row = self._index_for(str(panel_id or ""))
        if row is None:
            return False
        panel = self._panels[row]
        if not panel.visible:
            return False
        if panel.detached or panel.dock_area == "floating":
            return True
        stack = stack_for_panel(self._layout_root, panel.panel_id)
        return stack is None or stack.active_panel_id == panel.panel_id

    def _can_resize_edge(self, panel: DockPanel, edge: str) -> bool:
        """Return whether a visible split node owns this panel edge."""
        if not panel.visible or panel.detached or panel.dock_area == "floating":
            return False
        available = {
            value.panel_id for value in self._panels
            if value.visible and not value.detached
            and value.dock_area != "floating"
        }
        return has_resizable_edge(
            self._layout_root, panel.panel_id, edge, available
        )

    def _replace(self, panel_id: str, **changes) -> None:
        row = self._index_for(panel_id)
        if row is None:
            return
        previous = self._panels[row]
        updated = replace(previous, **changes)
        self._panels[row] = updated
        index = self.index(row, 0)
        self.dataChanged.emit(index, index)
        if (
            previous.visible,
            previous.detached,
            previous.dock_area,
        ) != (
            updated.visible,
            updated.detached,
            updated.dock_area,
        ):
            self.minimumHostSizeChanged.emit()
        self._save()
