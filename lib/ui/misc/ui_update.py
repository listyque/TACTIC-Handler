# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'misc/ui_update.ui'
#
# Created: Thu Apr 27 14:15:15 2017
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtCore


class Ui_updateDialog(object):
    def setupUi(self, updateDialog):
        updateDialog.setObjectName("updateDialog")
        updateDialog.resize(580, 400)
        updateDialog.setMinimumSize(QtCore.QSize(580, 400))
        updateDialog.setSizeGripEnabled(True)
        updateDialog.setModal(True)
        self.gridLayout = QtGui.QGridLayout(updateDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.versionLabel = QtGui.QLabel(updateDialog)
        self.versionLabel.setObjectName("versionLabel")
        self.gridLayout.addWidget(self.versionLabel, 0, 0, 1, 1)
        self.versionsTreeWidget = QtGui.QTreeWidget(updateDialog)
        self.versionsTreeWidget.setStyleSheet("QTreeView::item {\n"
"    padding: 2px;\n"
"}")
        self.versionsTreeWidget.setAlternatingRowColors(True)
        self.versionsTreeWidget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.versionsTreeWidget.setWordWrap(True)
        self.versionsTreeWidget.setHeaderHidden(False)
        self.versionsTreeWidget.setObjectName("versionsTreeWidget")
        self.versionsTreeWidget.header().setDefaultSectionSize(130)
        self.versionsTreeWidget.header().setMinimumSectionSize(130)
        self.gridLayout.addWidget(self.versionsTreeWidget, 1, 0, 1, 5)
        self.updateToLastPushButton = QtGui.QPushButton(updateDialog)
        self.updateToLastPushButton.setObjectName("updateToLastPushButton")
        self.gridLayout.addWidget(self.updateToLastPushButton, 2, 0, 1, 4)
        self.updateToSelectedPushButton = QtGui.QPushButton(updateDialog)
        self.updateToSelectedPushButton.setObjectName("updateToSelectedPushButton")
        self.gridLayout.addWidget(self.updateToSelectedPushButton, 2, 4, 1, 1)
        self.currentVersionlabel = QtGui.QLabel(updateDialog)
        self.currentVersionlabel.setObjectName("currentVersionlabel")
        self.gridLayout.addWidget(self.currentVersionlabel, 0, 1, 1, 3)
        self.commitPushButton = QtGui.QPushButton(updateDialog)
        self.commitPushButton.setObjectName("commitPushButton")
        self.gridLayout.addWidget(self.commitPushButton, 0, 4, 1, 1)
        self.gridLayout.setColumnStretch(1, 1)

        self.retranslateUi(updateDialog)
        QtCore.QMetaObject.connectSlotsByName(updateDialog)

    def retranslateUi(self, updateDialog):
        updateDialog.setWindowTitle(QtGui.QApplication.translate("updateDialog", "Update TACTIC-Handler", None))
        self.versionLabel.setText(QtGui.QApplication.translate("updateDialog", "Current Version:", None))
        self.versionsTreeWidget.headerItem().setText(0, QtGui.QApplication.translate("updateDialog", "Available Versions", None))
        self.versionsTreeWidget.headerItem().setText(1, QtGui.QApplication.translate("updateDialog", "Date", None))
        self.versionsTreeWidget.headerItem().setText(2, QtGui.QApplication.translate("updateDialog", "Changes", None))
        self.versionsTreeWidget.headerItem().setText(3, QtGui.QApplication.translate("updateDialog", "Misc", None))
        self.updateToLastPushButton.setText(QtGui.QApplication.translate("updateDialog", "Update to last", None))
        self.updateToSelectedPushButton.setText(QtGui.QApplication.translate("updateDialog", "Update to selected", None))
        self.currentVersionlabel.setText(QtGui.QApplication.translate("updateDialog", " ", None))
        self.commitPushButton.setText(QtGui.QApplication.translate("updateDialog", "Create update", None))

