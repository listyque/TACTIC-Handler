import sys
from PySide import QtGui, QtCore
import os

class ms_ImageViewer(QtGui.QWidget):

    def __init__(self):
        super(ms_ImageViewer, self).__init__()
        self.initUI()

    def initUI(self):               

        main_layout = QtGui.QVBoxLayout()
        self.setLayout(main_layout)

        self.image = QtGui.QImage(100, 150, QtGui.QImage.Format_ARGB32)
        # intial_color = QtGui.qRgb(189, 149, 39)
        # self.image.fill(QtGui.qRgb(255,0,0))
        self.image.load('D:/APS/OneDrive/Exam_(work title)/root/exam/props/Mushroom/work/icon/Mushroom_mushroom_web_icon.jpg')
        # asd = QtGui.QLabel
        # asd.setPixmap.
        image_label = QtGui.QLabel(" ")
        image_label.setPixmap(QtGui.QPixmap.fromImage(self.image))
        button = QtGui.QPushButton('select file', self)
        main_layout.addWidget(button)
        main_layout.addWidget(image_label)

        self.setGeometry(300, 300, 600, 30)
        self.setWindowTitle('ms_image_viewer')    
        self.show()

def main():

    app = QtGui.QApplication(sys.argv)
    ex = ms_ImageViewer()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()