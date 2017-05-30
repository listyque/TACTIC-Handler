# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'items/ui_item_process.ui'
#
# Created: Thu Apr 27 14:15:16 2017
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtCore


class Ui_processItem(object):
    def setupUi(self, processItem):
        processItem.setObjectName("processItem")
        processItem.setWindowTitle("")
        self.versionlessLayout = QtGui.QGridLayout(processItem)
        self.versionlessLayout.setContentsMargins(0, 0, 0, 0)
        self.versionlessLayout.setSpacing(0)
        self.versionlessLayout.setObjectName("versionlessLayout")
        self.notesToolButton = QtGui.QToolButton(processItem)
        self.notesToolButton.setMinimumSize(QtCore.QSize(0, 20))
        self.notesToolButton.setMaximumSize(QtCore.QSize(16777215, 20))
        self.notesToolButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.notesToolButton.setAutoRaise(True)
        self.notesToolButton.setArrowType(QtCore.Qt.NoArrow)
        self.notesToolButton.setObjectName("notesToolButton")
        self.versionlessLayout.addWidget(self.notesToolButton, 0, 1, 1, 1)
        self.label = QtGui.QLabel(processItem)
        self.label.setMinimumSize(QtCore.QSize(0, 24))
        self.label.setMaximumSize(QtCore.QSize(16777215, 24))
        self.label.setStyleSheet("QLabel {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:.4, stop:0 rgba(128, 128, 128, 75), stop:1 rgba(64, 64,64, 0));\n"
"    padding: 0px;\n"
"}")
        self.label.setTextFormat(QtCore.Qt.PlainText)
        self.label.setObjectName("label")
        self.versionlessLayout.addWidget(self.label, 0, 0, 1, 1)
        self.versionlessLayout.setColumnStretch(0, 1)

        self.retranslateUi(processItem)
        QtCore.QMetaObject.connectSlotsByName(processItem)

    def retranslateUi(self, processItem):
        pass

