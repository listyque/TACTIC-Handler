#!/usr/bin/env python
#-*- coding:utf-8 -*-

from PyQt4 import QtCore, QtGui

class myWindow(QtGui.QWidget):  
    def __init__(self, parent=None):
        super(myWindow, self).__init__(parent)

        self.actionHello = QtGui.QAction(self)
        self.actionHello.setText("Hello")

        self.menu = QtGui.QMenu(self)
        self.menu.addAction(self.actionHello)

        self.buttonShow = QtGui.QPushButton(self)
        self.buttonShow.setText("Button with menu")
        self.buttonShow.setMenu(self.menu)

        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.buttonShow)


if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('myWindow')

    main = myWindow()
    main.show()

    sys.exit(app.exec_())