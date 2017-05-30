# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'items/ui_item_task.ui'
#
# Created: Thu Apr 27 14:15:16 2017
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtCore


class Ui_taskItem(object):
    def setupUi(self, taskItem):
        taskItem.setObjectName("taskItem")
        taskItem.resize(108, 20)
        taskItem.setWindowTitle("")
        self.versionlessLayout = QtGui.QGridLayout(taskItem)
        self.versionlessLayout.setContentsMargins(0, 0, 0, 0)
        self.versionlessLayout.setSpacing(0)
        self.versionlessLayout.setObjectName("versionlessLayout")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.versionlessLayout.addItem(spacerItem, 0, 0, 1, 1)
        self.addToolButton = QtGui.QToolButton(taskItem)
        self.addToolButton.setMaximumSize(QtCore.QSize(75, 20))
        self.addToolButton.setIconSize(QtCore.QSize(12, 12))
        self.addToolButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.addToolButton.setAutoRaise(True)
        self.addToolButton.setArrowType(QtCore.Qt.DownArrow)
        self.addToolButton.setObjectName("addToolButton")
        self.versionlessLayout.addWidget(self.addToolButton, 0, 1, 1, 1)

        self.retranslateUi(taskItem)
        QtCore.QMetaObject.connectSlotsByName(taskItem)

    def retranslateUi(self, taskItem):
        self.addToolButton.setText(QtGui.QApplication.translate("taskItem", "Add", None))

