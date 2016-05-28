# -*- coding: utf-8 -*-
import sys
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt


# very testable class (hint: you can use mock.Mock for the signals)
class Worker(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    dataReady = QtCore.pyqtSignal(list, dict)

    @QtCore.pyqtSlot()
    def processA(self):
        print "Worker.processA()"
        self.finished.emit()

    @QtCore.pyqtSlot(str, list, list)
    def processB(self, foo, bar=None, baz=None):
        print "Worker.processB()"
        for thing in bar:
            # lots of processing...
            self.dataReady.emit(['dummy', 'data'], {'dummy': ['data']})
        self.finished.emit()


def onDataReady(aList, aDict):
    print 'onDataReady'
    print repr(aList)
    print repr(aDict)


app = QtGui.QApplication(sys.argv)

thread = QtCore.QThread()  # no parent!
obj = Worker()  # no parent!
obj.dataReady.connect(onDataReady)

obj.moveToThread(thread)

# if you want the thread to stop after the worker is done
# you can always call thread.start() again later
obj.finished.connect(thread.quit)

# one way to do it is to start processing as soon as the thread starts
# this is okay in some cases... but makes it harder to send data to
# the worker object from the main gui thread.  As you can see I'm calling
# processA() which takes no arguments
thread.started.connect(obj.processA)
thread.finished.connect(app.exit)

thread.start()

# another way to do it, which is a bit fancier, allows you to talk back and
# forth with the object in a thread safe way by communicating through signals
# and slots (now that the thread is running I can start calling methods on
# the worker object)
QtCore.QMetaObject.invokeMethod(obj, 'processB', Qt.QueuedConnection,
                                QtCore.Q_ARG(str, "Hello World!"),
                                QtCore.Q_ARG(list, ["args", 0, 1]),
                                QtCore.Q_ARG(list, []))

# that looks a bit scary, but its a totally ok thing to do in Qt,
# we're simply using the system that Signals and Slots are built on top of,
# the QMetaObject, to make it act like we safely emitted a signal for
# the worker thread to pick up when its event loop resumes (so if its doing
# a bunch of work you can call this method 10 times and it will just queue
# up the calls.  Note: PyQt > 4.6 will not allow you to pass in a None
# instead of an empty list, it has stricter type checking

app.exec_()