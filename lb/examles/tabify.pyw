from PyQt4 import QtCore, QtGui

class Window(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle('Dock Widgets')
        self.button = QtGui.QPushButton('Raise Next Tab', self)
        self.button.clicked.connect(self.handleButton)
        self.setCentralWidget(self.button)
        self.dockList = []
        approvedAdded = False
        for dockName in 'Red Green Yellow Blue'.split():
            dock = QtGui.QDockWidget(dockName)
            dock.setWidget(QtGui.QListWidget())
            dock.setAllowedAreas(QtCore.Qt.TopDockWidgetArea)
            dock.setFeatures(QtGui.QDockWidget.DockWidgetMovable |
                             QtGui.QDockWidget.DockWidgetFloatable)
            self.addDockWidget(QtCore.Qt.TopDockWidgetArea, dock)
            insertIndex = len(self.dockList) - 1
            if dockName == 'Green':
                insertIndex = 0
                approvedAdded = True
            elif dockName == 'Yellow':
                if not approvedAdded:
                    insertIndex = 0
                else:
                    insertIndex = 1
            self.dockList.insert(insertIndex, dock)
        if len(self.dockList) > 1:
            for index in range(0, len(self.dockList) - 1):
                self.tabifyDockWidget(self.dockList[index],
                                      self.dockList[index + 1])
        self.dockList[0].raise_()
        self.nextindex = 1

    def handleButton(self):
        self.dockList[self.nextindex].raise_()
        self.nextindex += 1
        if self.nextindex > len(self.dockList) - 1:
            self.nextindex = 0

if __name__ == '__main__':

    import sys
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())