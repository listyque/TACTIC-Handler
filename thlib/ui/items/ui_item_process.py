# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'items\ui_item_process.ui'
#
# Created: Sat Oct  5 00:17:14 2019
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

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

