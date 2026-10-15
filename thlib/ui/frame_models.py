"""Qt table adapter for Frame's virtualized row records; no domain operations."""
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Slot


class FrameTableModel(QAbstractTableModel):
    CELL = Qt.UserRole + 1

    def __init__(self, rows, columns, parent=None):
        super().__init__(parent)
        self._records = rows
        self._columns = columns
        self._rows = list(rows())
        self._size = (len(self._rows), columns())

    def roleNames(self):
        return {self.CELL: b'cell'}

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else self._size[0]

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else self._size[1]

    def data(self, index, role=Qt.DisplayRole):
        if role == self.CELL and index.isValid() and 0 <= index.row() < self._size[0] and 0 <= index.column() < self._size[1]:
            return self._rows[index.row()]
        return None

    @Slot()
    def refresh(self):
        records = list(self._records())
        size = (len(records), self._columns())
        if size != self._size:
            self.beginResetModel()
            self._rows = records
            self._size = size
            self.endResetModel()
        else:
            self._rows = records
            if not size[0] or not size[1]:
                return
            self.dataChanged.emit(self.index(0, 0), self.index(size[0] - 1, size[1] - 1), [self.CELL])
