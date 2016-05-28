
import sys, time
from PySide import QtCore, QtGui


class MyApp(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.setGeometry(300, 300, 280, 600)
        self.setWindowTitle('threads')

        self.layout = QtGui.QVBoxLayout(self)

        self.testButton = QtGui.QPushButton("test")
        self.connect(self.testButton, QtCore.SIGNAL("released()"), self.test)
        self.listwidget = QtGui.QListWidget(self)

        self.layout.addWidget(self.testButton)
        self.layout.addWidget(self.listwidget)

        self.threadPool = []

    def add(self, text):
        """ Add item to list widget """
        print "Add: " + text
        self.listwidget.addItem(text)
        self.listwidget.sortItems()

    def add_diff(self, text):
        """ Add item to list widget """
        print "Add: " + text
        self.listwidget.addItem(text)
        self.wdg = QtGui.QPushButton(text)
        self.listwidget.setItemWidget(self.listwidget.item(self.listwidget.count()-1), self.wdg)
        self.listwidget.sortItems()

    def addBatch(self, text="test", iters=6, delay=0.3):
        """ Add several items to list widget """
        for i in range(iters):
            time.sleep(delay)  # artificial time delay
            self.add(text + " " + str(i))

    def addBatch2(self, text="test", iters=6, delay=0.3):
        for i in range(iters):
            time.sleep(delay)  # artificial time delay
            self.emit(QtCore.SIGNAL('add(QString)'), text + " " + str(i))

    def test(self):
        self.listwidget.clear()
        # adding in main application: locks ui
        # self.addBatch("_non_thread",iters=6,delay=0.3)

        # adding by emitting signal in different thread
        self.threadPool.append(WorkThread())
        self.connect(self.threadPool[len(self.threadPool) - 1], QtCore.SIGNAL("update(QString)"), self.add)
        self.threadPool[len(self.threadPool) - 1].start()

        # generic thread using signal
        self.threadPool.append(GenericThread(self.addBatch2, "from generic thread using signal ", delay=0.3))
        self.disconnect(self, QtCore.SIGNAL("add(QString)"), self.add)
        self.connect(self, QtCore.SIGNAL("add(QString)"), self.add)
        self.threadPool[len(self.threadPool) - 1].start()


class WorkThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        for i in range(6):
            time.sleep(0.3)  # artificial time delay
            self.emit(QtCore.SIGNAL('update(QString)'), "from work thread " + str(i))
        return


class GenericThread(QtCore.QThread):
    def __init__(self, function, *args, **kwargs):
        QtCore.QThread.__init__(self)
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def __del__(self):
        self.wait()

    def run(self):
        self.function(*self.args, **self.kwargs)
        return


# run
app = QtGui.QApplication(sys.argv)
test = MyApp()
test.show()
app.exec_()
