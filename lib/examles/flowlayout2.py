#!/usr/bin/env python

"""PyQt4 port of the layouts/flowlayout example from Qt v4.x"""

from PyQt4 import QtCore, QtGui


# ------------------------------------------------------------------------
class FlowLayout(QtGui.QLayout):
    """
    Standard PyQt examples FlowLayout modified to work with a scollable parent
    """

    def __init__(self, parent=None, margin=0, spacing=-1):
        super(FlowLayout, self).__init__(parent)

        if parent is not None:
            self.setMargin(margin)

        self.setSpacing(spacing)

        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

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

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        size += QtCore.QSize(2 * self.margin(), 2 * self.margin())
        return size

    def minimumSize(self):
        w = self.geometry().width()
        h = self.doLayout(QtCore.QRect(0, 0, w, 0), True)
        return QtCore.QSize(w + 2 * self.margin(), h + 2 * self.margin())

    def doLayout(self, rect, testOnly=False):
        """
        """
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            wid = item.widget()
            spaceX = self.spacing() + wid.style().layoutSpacing(QtGui.QSizePolicy.PushButton,
                                                                QtGui.QSizePolicy.PushButton, QtCore.Qt.Horizontal)
            spaceY = self.spacing() + wid.style().layoutSpacing(QtGui.QSizePolicy.PushButton,
                                                                QtGui.QSizePolicy.PushButton, QtCore.Qt.Vertical)
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()


# ------------------------------------------------------------------------
class ResizeScrollArea(QtGui.QScrollArea):
    """
    A QScrollArea that propagates the resizing to any FlowLayout children.
    """

    def __init(self, parent=None):
        QtGui.QScrollArea.__init__(self, parent)

    def resizeEvent(self, event):
        wrapper = self.findChild(QtGui.QWidget)
        flow = wrapper.findChild(FlowLayout)

        if wrapper and flow:
            width = self.viewport().width()
            height = flow.heightForWidth(width)
            size = QtCore.QSize(width, height)
            point = self.viewport().rect().topLeft()
            flow.setGeometry(QtCore.QRect(point, size))
            self.viewport().update()

        super(ResizeScrollArea, self).resizeEvent(event)


# ------------------------------------------------------------------------
class ScrollingFlowWidget(QtGui.QWidget):
    """
    A resizable and scrollable widget that uses a flow layout.
    Use its addWidget() method to flow children into it.
    """

    def __init__(self, parent=None):
        super(ScrollingFlowWidget, self).__init__(parent)
        grid = QtGui.QGridLayout(self)
        scroll = ResizeScrollArea()
        self._wrapper = QtGui.QWidget(scroll)
        self.flowLayout = FlowLayout(self._wrapper)
        self._wrapper.setLayout(self.flowLayout)
        scroll.setWidget(self._wrapper)
        scroll.setWidgetResizable(True)
        grid.addWidget(scroll)

    def addWidget(self, widget):
        self.flowLayout.addWidget(widget)
        widget.setParent(self._wrapper)


# ------------------------------------------------------------------------
if __name__ == '__main__':

    import sys
    import random


    class ExampleScroller(ScrollingFlowWidget):
        def sizeHint(self):
            return QtCore.QSize(500, 300)


    class ExampleWindow(QtGui.QWidget):
        def __init__(self):
            super(ExampleWindow, self).__init__()

            self.scroller = ExampleScroller(self)
            self.setLayout(QtGui.QVBoxLayout(self))
            self.layout().addWidget(self.scroller)

            for w in range(random.randint(25, 50)):
                words = " ".join(["".join([chr(random.choice(range(ord('a'), ord('z'))))
                                           for x in range(random.randint(2, 9))])
                                  for n in range(random.randint(1, 5))]).title()
                widget = QtGui.QPushButton(words)
                self.scroller.addWidget(widget)

            self.setWindowTitle("Scrolling Flow Layout")


    app = QtGui.QApplication(sys.argv)
    mainWin = ExampleWindow()
    mainWin.show()
    sys.exit(app.exec_())
