import sys
import math
from PySide2 import QtWidgets, QtCore


class FlowLayout(QtWidgets.QLayout):

    def __init__(self, parent=None):
        super(FlowLayout, self).__init__(parent)
        self.itemList = []
        self.m_hSpace = 0
        self.m_vSpace = 0
        self.m_minSize = QtCore.QSize(192, 192)
        self.m_maxSize = QtCore.QSize(1024, 1024)
        self.m_maxItemPerLine = 24

    def minimumItemSize(self):
        return self.m_minSize

    def setMinimumSize(self, size):
        self.m_minSize = size

    def maximumItemSize(self):
        return self.m_maxSize

    def setMaximumSize(self, size):
        self.m_maxSize = size

    def addItem(self, item):
        self.itemList.append(item)

    def horizontalSpacing(self):
        if self.m_hSpace > 0:
            return self.m_hSpace
        else:
            return self.smartSpacing(QtWidgets.QStyle.PM_LayoutHorizontalSpacing)

    def verticalSpacing(self):
        if self.m_vSpace > 0:
            return self.m_vSpace
        else:
            return self.smartSpacing(QtWidgets.QStyle.PM_LayoutVerticalSpacing)

    def expandingDirections(self):
        return QtCore.Qt.Horizontal | QtCore.Qt.Vertical

    def hasHeightForWidth(self):
        return True

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None

    def minimumSize(self):
        size = QtCore.QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
            break
        margins = self.contentsMargins()
        size += QtCore.QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def setGeometry(self, rect):
        QtWidgets.QLayout.setGeometry(self, rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def doLayout(self, rect, testOnly=False):
        left, top, right, bottom = self.getContentsMargins()
        effectiveRect = rect
        x = effectiveRect.x()
        y = effectiveRect.y()
        lineHeight = 0
        itemSize = self.m_minSize
        if self.itemList:
            itemSize = QtCore.QSize(
                max([self.m_minSize.width(), min([self.m_maxSize.width(), self.itemList[0].sizeHint().width()])]),
                max([self.m_minSize.height(), min([self.m_maxSize.height(), self.itemList[0].sizeHint().height()])])
            )
        lineItemCount = min([(effectiveRect.width() + self.spacing()) // (itemSize.width() + self.spacing()), self.count()])
        if lineItemCount < 1:
            lineItemCount = 1
        if lineItemCount > self.m_maxItemPerLine:
            lineItemCount = self.m_maxItemPerLine
        lineCount = math.ceil(len(self.itemList) / lineItemCount)
        freeWidth = effectiveRect.width() - (itemSize.width() + self.spacing()) * lineItemCount
        itemSize = QtCore.QSize(
            max([self.m_minSize.width(), min([self.m_maxSize.width(), itemSize.width() + freeWidth/lineItemCount])]),
            max([self.m_minSize.height(), min([self.m_maxSize.height(), itemSize.height() + freeWidth/lineItemCount])])
        )
        itemIndex = 0
        for line in range(lineCount):
            lineX = x
            for lineItem in range(lineItemCount):
                item = self.itemAt(itemIndex)
                if not item:
                    break

                itemIndex += 1
                itemWidget = item.widget()
                if not testOnly:
                    pos = QtCore.QPoint(lineX, y)
                    lineX += itemSize.width() + self.spacing()
                    itemGeometry = QtCore.QRect(pos, itemSize)

                    itemWidget.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
                    itemWidget.setMinimumSize(self.m_minSize)
                    itemWidget.setMaximumSize(self.m_maxSize)
                    item.setGeometry(itemGeometry)

            y += itemSize.height() + self.spacing()

        return y + lineHeight - rect.y() + bottom

    def smartSpacing(self, pm):
        parent = self.parent()
        if not parent:
            return -1
        elif parent.isWidgetType():
            pw = parent
            return pw.style().pixelMetric(pm, None, pw)
        else:
            pl = parent
            return pl.spacing()


if __name__ == "__main__":
    found_app = QtWidgets.QApplication.instance()
    if not found_app:
        app = QtWidgets.QApplication(sys.argv)

    else:
        app = found_app

    window = QtWidgets.QWidget()
    window.setWindowTitle("client")
    layout = QtWidgets.QVBoxLayout()
    window.setLayout(layout)

    flow_widget = QtWidgets.QWidget()
    flow_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
    flow_widget.setMinimumWidth(256)
    flow_widget.setMinimumHeight(256)
    flow_layout = FlowLayout()
    flow_widget.setLayout(flow_layout)

    scroll_area = QtWidgets.QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setWidget(flow_widget)

    layout.addWidget(scroll_area)

    for x in range(30):
        for y in range(30):
            button = QtWidgets.QPushButton(str(x) + "/" + str(y))
            button.setFixedSize(256, 256)
            print(str(x) + "/" + str(y))
            flow_layout.addWidget(button)

    window.show()

    if not found_app:
        sys.exit(app.exec_())
