"""Public DockPanelModel model."""

from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, Signal, Qt

from .docks_types import DockPanel
from .docks_records import RecordsMixin
from .docks_layout import LayoutMixin
from .docks_resizing import ResizingMixin
from .docks_placement import PlacementMixin
from .docks_tree import default_layout, layout_from_rectangles


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

    _settings_key = "workspace/dockLayoutV2"

    panelVisibilityChanged = Signal(str, bool)

    def __init__(self, settings: QSettings) -> None:
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
