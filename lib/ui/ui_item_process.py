# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_item_process.ui'
#
# Created: Tue Feb 09 14:42:40 2016
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
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.versionlessLayout.addItem(spacerItem, 0, 0, 1, 1)
        self.notesToolButton = QtGui.QToolButton(processItem)
        self.notesToolButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.notesToolButton.setAutoRaise(True)
        self.notesToolButton.setArrowType(QtCore.Qt.UpArrow)
        self.notesToolButton.setObjectName("notesToolButton")
        self.versionlessLayout.addWidget(self.notesToolButton, 0, 1, 1, 1)

        self.retranslateUi(processItem)
        QtCore.QMetaObject.connectSlotsByName(processItem)

    def retranslateUi(self, processItem):
        self.notesToolButton.setText(QtGui.QApplication.translate("processItem", "Notes", None, QtGui.QApplication.UnicodeUTF8))

