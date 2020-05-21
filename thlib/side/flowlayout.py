#!/usr/bin/env python

from Qt import QtWidgets as QtGui
from Qt import QtCore

from thlib.global_functions import time_it


# ------------------------------------------------------------------------
class FlowLayout(QtGui.QLayout):
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

        # Considering all widgets are the same size
        if self.itemList:
            size = size.expandedTo(self.itemList[0].minimumSize())

        # uncomment if you want different sizes
        # for item in self.itemList:
        #     size = size.expandedTo(item.minimumSize())

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
