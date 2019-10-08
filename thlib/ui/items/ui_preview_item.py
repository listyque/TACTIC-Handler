# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'items/ui_preview_item.ui'
#
# Created: Wed May 23 15:57:42 2018
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

class Ui_previewItem(object):
    def setupUi(self, previewItem):
        previewItem.setObjectName("previewItem")
        previewItem.resize(382, 64)
        self.gridLayout = QtGui.QGridLayout(previewItem)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.previewLabel = QtGui.QLabel(previewItem)
        self.previewLabel.setMinimumSize(QtCore.QSize(64, 64))
        self.previewLabel.setMaximumSize(QtCore.QSize(64, 64))
        self.previewLabel.setStyleSheet("QLabel {\n"
"    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(175, 175, 175, 16), stop: 1 rgba(0, 0, 0, 0));\n"
"    border: 0px;\n"
"    border-radius: 4px;\n"
"    padding: 0px 0px;\n"
"}")
        self.previewLabel.setTextFormat(QtCore.Qt.RichText)
        self.previewLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.previewLabel.setObjectName("previewLabel")
        self.gridLayout.addWidget(self.previewLabel, 0, 0, 1, 1)
        self.fileNameLabel = QtGui.QLabel(previewItem)
        self.fileNameLabel.setMinimumSize(QtCore.QSize(0, 20))
        self.fileNameLabel.setMaximumSize(QtCore.QSize(16777215, 24))
        font = Qt4Gui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.fileNameLabel.setFont(font)
        self.fileNameLabel.setStyleSheet("QLabel {\n"
"    background-color: transparent;\n"
"    border-bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(128, 128, 128, 64), stop:1 rgba(128, 128,128, 0));\n"
"}")
        self.fileNameLabel.setTextFormat(QtCore.Qt.PlainText)
        self.fileNameLabel.setObjectName("fileNameLabel")
        self.gridLayout.addWidget(self.fileNameLabel, 0, 1, 1, 1)

        self.retranslateUi(previewItem)
        QtCore.QMetaObject.connectSlotsByName(previewItem)

    def retranslateUi(self, previewItem):
        previewItem.setWindowTitle(u"Form")

