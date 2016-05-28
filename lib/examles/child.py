from PySide import QtGui

class ChildWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(ChildWidget, self).__init__(parent=parent)

        self.button1 = QtGui.QPushButton()
        self.button1.clicked.connect(self.do_something_else)

        self.button2 = QtGui.QPushButton()
        self.button2.clicked.connect(self.parent().do_something)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.button1)
        self.layout.addWidget(self.button2)
        self.setLayout(self.layout)
        #self.show()

    def do_something_else(self):

        print 'doing something else!'