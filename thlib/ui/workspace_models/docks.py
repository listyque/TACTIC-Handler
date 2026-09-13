"""Public DockPanelModel model."""

from __future__ import annotations

from dataclasses import replace
from math import ceil

from PySide6.QtCore import (
    QAbstractListModel,
    Property,
    QSortFilterProxyModel,
    QTimer,
    Signal,
    Qt,
)

from .docks_types import DockPanel
from .docks_records import RecordsMixin
from .docks_layout import LayoutMixin
from .docks_resizing import ResizingMixin
from .docks_placement import PlacementMixin
from .docks_tree import (
    default_layout,
    deserialize_layout,
    layout_from_rectangles,
    stack_for_panel,
)


class DockPanelModel(
        RecordsMixin,
        LayoutMixin,
        ResizingMixin,
        PlacementMixin,
        QAbstractListModel):
    IdRole = Qt.UserRole + 1

    TitleRole = Qt.UserRole + 2

    KindRole = Qt.UserRole + 3

    XRole = Qt.UserRole + 4

    YRole = Qt.UserRole + 5

    WidthRole = Qt.UserRole + 6

    HeightRole = Qt.UserRole + 7

    VisibleRole = Qt.UserRole + 8

    ClosableRole = Qt.UserRole + 9

    ZRole = Qt.UserRole + 10

    DockAreaRole = Qt.UserRole + 11

    CanResizeLeftRole = Qt.UserRole + 12

    CanResizeRightRole = Qt.UserRole + 13

    CanResizeTopRole = Qt.UserRole + 14

    CanResizeBottomRole = Qt.UserRole + 15

    DetachedRole = Qt.UserRole + 16

    PanelTitleRole = Qt.UserRole + 17

    StackActiveRole = Qt.UserRole + 18

    StackPanelsRole = Qt.UserRole + 19

    StackSizeRole = Qt.UserRole + 20

    _settings_key = "workspace/dockLayout"

    panelVisibilityChanged = Signal(str, bool)
    panelPresentationChanged = Signal(str, bool)
    minimumHostSizeChanged = Signal()
    @Property(int, notify=minimumHostSizeChanged)
    def minimumHostWidth(self) -> int:
        return ceil(self._minimum_host_pixel_size()[0])

    @Property(int, notify=minimumHostSizeChanged)
    def minimumHostHeight(self) -> int:
        return ceil(self._minimum_host_pixel_size()[1])

    def __init__(self, settings: dict) -> None:
        super().__init__()
        self._settings = settings
        restored, restored_layout, needs_save = self._restore()
        self._panels = restored or self._defaults()
        if restored and restored_layout is None:
            restored_layout = layout_from_rectangles({
                panel.panel_id: (panel.x, panel.y, panel.width, panel.height)
                for panel in self._panels
                if not panel.detached and panel.dock_area != "floating"
            })
        self._layout_root = restored_layout or default_layout()
        self._z_counter = max((panel.z for panel in self._panels), default=0)
        if restored:
            layout_before_reflow = self._layout_root
            self._reflow_workspace(save=False)
            needs_save = needs_save or self._layout_root != layout_before_reflow
        if needs_save:
            self._save()
        self._presented_panels = self._presentation_state()
        self.dataChanged.connect(self._sync_presentation_state)
        self.modelReset.connect(self._sync_presentation_state)

    def _presentation_state(self) -> dict[str, bool]:
        return {
            panel.panel_id: self.is_panel_presented(panel.panel_id)
            for panel in self._panels
        }

    def _sync_presentation_state(self, *_args) -> None:
        current = self._presentation_state()
        previous = self._presented_panels
        self._presented_panels = current
        for panel_id, presented in current.items():
            if previous.get(panel_id) != presented:
                self.panelPresentationChanged.emit(panel_id, presented)

    @staticmethod
    def _is_presented_in_layout(panel, layout_root) -> bool:
        if not panel.visible:
            return False
        if panel.detached or panel.dock_area == "floating":
            return True
        stack = stack_for_panel(layout_root, panel.panel_id)
        return stack is None or stack.active_panel_id == panel.panel_id

    def prehide_for_layout(self, value: object) -> bool:
        """Hide outgoing presenters absent from a validated target layout.

        Geometry and target-visible panels stay untouched.  Navigation can
        therefore restore the target selection while every dock that will be
        hidden is already non-presented, then atomically apply the full layout
        to expose target-visible docks from the restored state.
        """
        if not isinstance(value, dict) or set(value) != {"panels", "layout"}:
            return False
        panels = self._decode_panels(value.get("panels"))
        if not panels:
            return False
        layout_root = deserialize_layout(
            value.get("layout"),
            {panel.panel_id for panel in panels},
        )
        if layout_root is None:
            return False
        target_presented = {
            panel.panel_id: self._is_presented_in_layout(panel, layout_root)
            for panel in panels
        }
        hidden_rows = []
        for row, panel in enumerate(self._panels):
            if (
                self.is_panel_presented(panel.panel_id)
                and not target_presented.get(panel.panel_id, False)
            ):
                self._panels[row] = replace(panel, visible=False)
                hidden_rows.append(row)
        if not hidden_rows:
            return True
        self.minimumHostSizeChanged.emit()
        for row in hidden_rows:
            model_index = self.index(row, 0)
            self.dataChanged.emit(
                model_index, model_index, [self.VisibleRole]
            )
            self.panelVisibilityChanged.emit(
                self._panels[row].panel_id, False
            )
        return True


class _DockPanelFilterModel(QSortFilterProxyModel):
    def __init__(
        self,
        source: DockPanelModel,
        parent=None,
        *,
        retain_accepted_rows: bool = False,
    ) -> None:
        super().__init__(parent)
        self.setSourceModel(source)
        self.setDynamicSortFilter(False)
        self._retain_accepted_rows = retain_accepted_rows
        self._retained_rows: set[int] = set()
        self._removal_timer = QTimer(self)
        self._removal_timer.setSingleShot(True)
        self._removal_timer.setInterval(5000)
        self._removal_timer.timeout.connect(self._release_hidden_rows)
        source.dataChanged.connect(self._source_data_changed)

    def _apply_filter(self) -> None:
        self.beginFilterChange()
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def _source_data_changed(self, top_left, bottom_right, *_args) -> None:
        add_now = False
        remove_later = False
        source = self.sourceModel()
        for row in range(top_left.row(), bottom_right.row() + 1):
            source_index = source.index(row, 0)
            accepted = self._accepts_source_row(
                row, source_index.parent()
            )
            present = self.mapFromSource(source_index).isValid()
            if accepted:
                if self._retain_accepted_rows:
                    self._retained_rows.add(row)
                else:
                    self._retained_rows.discard(row)
            elif present:
                self._retained_rows.add(row)
            add_now = add_now or (accepted and not present)
            remove_later = remove_later or (
                not self._retain_accepted_rows
                and present
                and not accepted
            )
        if add_now:
            self._apply_filter()
        if remove_later:
            self._removal_timer.start()

    def _release_hidden_rows(self) -> None:
        self._retained_rows.clear()
        self._apply_filter()

    def filterAcceptsRow(self, source_row, source_parent) -> bool:
        return (
            self._accepts_source_row(source_row, source_parent)
            or source_row in self._retained_rows
        )

    def _panel_state(self, source_row, source_parent) -> tuple[bool, bool]:
        source = self.sourceModel()
        if source is None:
            return False, False
        index = source.index(source_row, 0, source_parent)
        return (
            bool(source.data(index, DockPanelModel.VisibleRole)),
            bool(source.data(index, DockPanelModel.DetachedRole)),
        )


class VisibleDockPanelModel(_DockPanelFilterModel):
    """Dock surfaces currently hosted by the main workspace."""

    def __init__(self, source: DockPanelModel, parent=None) -> None:
        # There are only a fixed, bounded number of workspace docks.  Once one
        # has been shown, retaining its proxy row preserves the QML delegate and
        # the UI state loaded beneath it across Search Tab layout switches.
        super().__init__(
            source,
            parent,
            retain_accepted_rows=True,
        )

    def _accepts_source_row(self, source_row, source_parent) -> bool:
        visible, detached = self._panel_state(source_row, source_parent)
        return visible and not detached


class DetachedDockPanelModel(_DockPanelFilterModel):
    """Detached native windows; normally this projection is empty."""

    def _accepts_source_row(self, source_row, source_parent) -> bool:
        visible, detached = self._panel_state(source_row, source_parent)
        return visible and detached
