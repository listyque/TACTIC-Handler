# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_menu.ui'
#
# Created: Fri Jan 22 19:36:30 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_menu(object):
    def setupUi(self, menu):
        menu.setObjectName("menu")
        menu.resize(30, 23)
        menu.setStyleSheet("QLabel {\n"
"    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(128, 128, 128, 96), stop: 1 rgba(32, 32, 32, 32));\n"
"    border-style: outset;\n"
"    border-width: 1px;\n"
"    border-color:  rgba(75, 75, 75, 128);\n"
"    border-radius: 0px;    \n"
"    padding: 4px;\n"
"}\n"
"QLabel:hover {\n"
"    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(52, 147, 241, 196), stop: 1 rgba(52, 147, 241, 96));\n"
"    \n"
"}")
        self.horizontalLayout = QtGui.QHBoxLayout(menu)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtGui.QLabel(menu)
        self.label.setTextFormat(QtCore.Qt.PlainText)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.buttonLabel = QtGui.QLabel(menu)
        self.buttonLabel.setStyleSheet("QLabel {\n"
"    padding: 0px;\n"
"}")
        self.buttonLabel.setObjectName("buttonLabel")
        self.horizontalLayout.addWidget(self.buttonLabel)
        self.horizontalLayout.setStretch(0, 1)

        self.retranslateUi(menu)
        QtCore.QMetaObject.connectSlotsByName(menu)

    def retranslateUi(self, menu):
        self.buttonLabel.setText(QtGui.QApplication.translate("menu", "    ", None, QtGui.QApplication.UnicodeUTF8))

