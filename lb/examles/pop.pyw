from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys

class popup(QWidget):
    def __init__(self, parent = None, widget=None):
        QWidget.__init__(self, parent)
        layout = QGridLayout(self)
        button = QPushButton("Very Interesting Text Popup. Here's an arrow   ^")
        layout.addWidget(button)

        # adjust the margins or you will get an invisible, unintended border
        layout.setContentsMargins(0, 0, 0, 0)

        # need to set the layout
        self.setLayout(layout)
        self.adjustSize()

        # tag this widget as a popup
        self.setWindowFlags(Qt.Popup)

        # calculate the botoom right point from the parents rectangle
        point        = widget.rect().bottomRight()

        # map that point as a global position
        global_point = widget.mapToGlobal(point)

        # by default, a widget will be placed from its top-left corner, so
        # we need to move it to the left based on the widgets width
        self.move(global_point - QPoint(self.width(), 0))

class Window(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.button = QPushButton('Hit this button to show a popup', self)
        self.button.clicked.connect(self.handleOpenDialog)
        self.button.move(250, 50)
        self.resize(600, 200)

    def handleOpenDialog(self):
        self.popup = popup(self, self.button)
        self.popup.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())