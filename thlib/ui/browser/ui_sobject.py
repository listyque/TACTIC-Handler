# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'browser/ui_sobject.ui'
#
# Created: Thu Apr 27 14:15:17 2017
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore


class Ui_sobjectGroupBox(object):
    def setupUi(self, sobjectGroupBox):
        sobjectGroupBox.setObjectName("sobjectGroupBox")
        sobjectGroupBox.resize(150, 150)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(sobjectGroupBox.sizePolicy().hasHeightForWidth())
        sobjectGroupBox.setSizePolicy(sizePolicy)
        sobjectGroupBox.setMinimumSize(QtCore.QSize(150, 150))
        sobjectGroupBox.setFocusPolicy(QtCore.Qt.ClickFocus)
        sobjectGroupBox.setStyleSheet("#sobjectGroupBox {\n"
"    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(175, 175, 175, 75), stop: 1 rgba(0, 0, 0, 30));\n"
"    border: 1px solid rgb(96, 96, 96);\n"
"    border-radius: 1px;\n"
"    padding: 0px 0px;\n"
"    margin-top: 5ex;\n"
"}\n"
"\n"
"#sobjectGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"    subcontrol-position: top center;\n"
"    padding: 0 3px;\n"
"    background-color: transparent;\n"
"}")
        sobjectGroupBox.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.vboxlayout = QtGui.QVBoxLayout(sobjectGroupBox)
        self.vboxlayout.setSpacing(0)
        self.vboxlayout.setContentsMargins(0, 0, 0, 0)
        self.vboxlayout.setObjectName("vboxlayout")
        self.picLabel = QtGui.QLabel(sobjectGroupBox)
        self.picLabel.setTextFormat(QtCore.Qt.RichText)
        self.picLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.picLabel.setObjectName("picLabel")
        self.vboxlayout.addWidget(self.picLabel)
        self.vboxlayout.setStretch(0, 1)

        self.retranslateUi(sobjectGroupBox)
        QtCore.QMetaObject.connectSlotsByName(sobjectGroupBox)

    def retranslateUi(self, sobjectGroupBox):
        self.picLabel.setText(u"PIC")

