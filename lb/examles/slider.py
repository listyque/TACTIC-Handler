from PySide.QtCore import *
from PySide.QtGui import *
import sys

class MySlider(QSlider):
    def __init__(self):
        QSlider.__init__(self, Qt.Horizontal)

    def setValue(self, int):
        QSlider.setValue(self, 99-int)

class MyMainWindow(QWidget):
 def __init__(self):
  QWidget.__init__(self, None)

  vbox = QVBoxLayout()

  sone = QSlider(Qt.Horizontal)
  sone.setRange(0,99)
  sone.setValue(0)
  vbox.addWidget(sone)

  stwo = MySlider()
  stwo.setRange(0,99)
  stwo.setValue(0)
  vbox.addWidget(stwo)

  sone.valueChanged.connect(stwo.setValue)

  self.setLayout(vbox)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MyMainWindow()
    w.show()
    sys.exit(app.exec_())