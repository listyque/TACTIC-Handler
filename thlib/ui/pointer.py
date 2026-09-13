"""Read-only native pointer and screen information for QML popup placement."""

from __future__ import annotations

from PySide6.QtCore import QObject, QPoint, Slot
from PySide6.QtGui import QCursor, QGuiApplication


class PointerController(QObject):
    @Slot(result="QVariantMap")
    def global_position(self):
        position = QCursor.pos()
        return {"x": float(position.x()), "y": float(position.y())}

    @Slot(float, float, result="QVariantMap")
    def available_geometry_at(self, x, y):
        """Return the available geometry of the screen containing a point."""
        point = QPoint(round(float(x)), round(float(y)))
        screen = QGuiApplication.screenAt(point)
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is None:
            return {}
        geometry = screen.availableGeometry()
        return {
            "x": float(geometry.x()),
            "y": float(geometry.y()),
            "width": float(geometry.width()),
            "height": float(geometry.height()),
        }
