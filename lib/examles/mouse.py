from PySide import QtCore, QtGui

class MyLabel(QtGui.QLabel):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.installEventFilter(self)
        self.single_click_timer = QtCore.QTimer()
        self.single_click_timer.setInterval(200)
        self.single_click_timer.timeout.connect(self.single_click)

    def single_click(self):
        self.single_click_timer.stop()
        print('timeout, must be single click')

    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            self.single_click_timer.start()
            return True
        elif event.type() == QtCore.QEvent.MouseButtonDblClick:
            self.single_click_timer.stop()
            print('double click')
            return True

        return False


window = MyLabel('Click me')
window.resize(200, 200)
window.show()

