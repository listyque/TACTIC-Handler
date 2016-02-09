import sys
from PySide import QtGui
import child

class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.do_something() #sanity check
        self.cw = child.ChildWidget(self)
        self.setCentralWidget(self.cw)
        self.show()

    def do_something(self):

        print 'doing something!'


def main():
    app = QtGui.QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()