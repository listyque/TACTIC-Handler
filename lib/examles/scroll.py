import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *


class CustomScroll(QScrollArea):
    def __init__(self):
        QScrollArea.__init__(self)


class Widget(QWidget):

    def __init__(self, parent= None):
        super(Widget, self).__init__()

        btn_new = QPushButton("Append new label")
        self.connect(btn_new, SIGNAL('clicked()'), self.add_new_label)

        #Container Widget
        self.widget = QWidget()
        #Layout of Container Widget
        layout = QVBoxLayout(self)
        for _ in range(20):
            label = QLabel("test")
            layout.addWidget(label)
        self.widget.setLayout(layout)

        #Scroll Area Properties
        scroll = CustomScroll()
        print(scroll.verticalScrollBar())
        scroll.verticalScrollBar().wheelEvent = self.wheelEvent
        # scroll.verticalScrollBar().dragEnterEvent = self.wheelEvent
        # QScrollBar.dragEnterEvent()
        # scroll.wheelEvent = self.wheelEvent
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.widget)

        #Scroll Area Layer add
        vLayout = QVBoxLayout(self)
        # QVBoxLayout.count()
        vLayout.addWidget(btn_new)
        vLayout.addWidget(scroll)
        self.setLayout(vLayout)

    def wheelEvent(self, QWheelEvent):
        self.add_new_label()

    def add_new_label(self):
        # QVBoxLayout.itemAt()
        label = QLabel("new"+str(self.widget.layout().count()))
        self.widget.layout().addWidget(label)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    dialog = Widget()
    dialog.show()

    app.exec_()