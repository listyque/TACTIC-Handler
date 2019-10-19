#!/usr/bin/env python

from Qt import QtWidgets as QtGui
from Qt import QtCore


# ------------------------------------------------------------------------
class FlowLayout(QtGui.QGridLayout):
    """
    Standard PyQt examples FlowLayout modified to work with a scollable parent
    MODIFIED FOR TACTIC HANDLER
    """

    def __init__(self, parent=None):
        super(FlowLayout, self).__init__(parent)

        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def clear_items(self):
        for i in range(self.count()):
            item = self.itemAt(i)
            if item:
                widget = self.itemAt(i).widget()
                widget.close()
                widget.deleteLater()

        self.itemList = []

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientations(QtCore.Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QtCore.QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()
        widths = []
        heights = []
        for item in self.itemList:
            widths.append(item.minimumSize().width())
            heights.append(item.minimumSize().height())

        for item in self.itemList:
            widget = item.widget()
            widget.resize(max(widths), max(heights))

            minimum_size = QtCore.QSize(max(widths), max(heights))
            size = size.expandedTo(minimum_size)

        return size

    def doLayout(self, rect, testOnly=True):
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            spacing = self.spacing()
            nextX = x + self.sizeHint().width() + spacing

            if nextX - spacing > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spacing
                nextX = x + self.sizeHint().width() + spacing
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), self.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, self.sizeHint().height())

        return y + lineHeight - rect.y()
