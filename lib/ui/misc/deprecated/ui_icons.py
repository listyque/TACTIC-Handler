# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_icons.ui'
#
# Created: Sat Dec 26 16:05:44 2015
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_icons(object):
    def setupUi(self, icons):
        icons.setObjectName("icons")
        icons.resize(531, 494)
        self.gridLayout = QtGui.QGridLayout(icons)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.imagesSlider = QtGui.QSlider(icons)
        self.imagesSlider.setStyleSheet("QSlider::groove:horizontal {\n"
"    border: 1px solid rgba(128, 128, 128, 40);\n"
"    height: 8px;\n"
"    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(128, 128, 128, 75), stop:1  rgba(128, 128, 128, 40));\n"
"    margin: 2px 0;\n"
"}\n"
"\n"
"QSlider::handle:horizontal {\n"
"    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(128, 128, 128, 40), stop:1 rgba(128, 128, 128, 175));\n"
"    border: 1px solid rgba(128, 128, 128, 40);\n"
"    width: 18px;\n"
"    margin: -2px 0;\n"
"    border-radius: 3px;\n"
"}")
        self.imagesSlider.setMaximum(1)
        self.imagesSlider.setPageStep(1)
        self.imagesSlider.setTracking(True)
        self.imagesSlider.setOrientation(QtCore.Qt.Horizontal)
        self.imagesSlider.setTickPosition(QtGui.QSlider.TicksAbove)
        self.imagesSlider.setObjectName("imagesSlider")
        self.gridLayout.addWidget(self.imagesSlider, 0, 0, 1, 1)
        self.spinBox = QtGui.QSpinBox(icons)
        self.spinBox.setMaximum(1)
        self.spinBox.setObjectName("spinBox")
        self.gridLayout.addWidget(self.spinBox, 0, 1, 1, 1)
        self.previewGraphicsView = QtGui.QGraphicsView(icons)
        self.previewGraphicsView.setFrameShape(QtGui.QFrame.NoFrame)
        self.previewGraphicsView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.previewGraphicsView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.previewGraphicsView.setOptimizationFlags(QtGui.QGraphicsView.DontAdjustForAntialiasing|QtGui.QGraphicsView.DontSavePainterState)
        self.previewGraphicsView.setObjectName("previewGraphicsView")
        self.gridLayout.addWidget(self.previewGraphicsView, 1, 0, 1, 2)

        self.retranslateUi(icons)
        QtCore.QObject.connect(self.imagesSlider, QtCore.SIGNAL("valueChanged(int)"), self.spinBox.setValue)
        QtCore.QObject.connect(self.spinBox, QtCore.SIGNAL("valueChanged(int)"), self.imagesSlider.setValue)
        QtCore.QMetaObject.connectSlotsByName(icons)
        icons.setTabOrder(self.imagesSlider, self.spinBox)

    def retranslateUi(self, icons):
        icons.setWindowTitle(QtGui.QApplication.translate("icons", "Form", None))

