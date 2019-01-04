# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'misc/ui_watch_folders.ui'
#
# Created: Mon May  7 14:55:31 2018
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore

class Ui_ProjectWatchFolder(object):
    def setupUi(self, ProjectWatchFolder):
        ProjectWatchFolder.setObjectName("ProjectWatchFolder")
        ProjectWatchFolder.resize(716, 555)
        self.gridLayout = QtGui.QGridLayout(ProjectWatchFolder)
        self.gridLayout.setObjectName("gridLayout")
        self.watchEnabledCheckBox = QtGui.QCheckBox(ProjectWatchFolder)
        self.watchEnabledCheckBox.setChecked(True)
        self.watchEnabledCheckBox.setObjectName("watchEnabledCheckBox")
        self.gridLayout.addWidget(self.watchEnabledCheckBox, 1, 0, 1, 2)
        self.watchFoldersTreeWidget = QtGui.QTreeWidget(ProjectWatchFolder)
        self.watchFoldersTreeWidget.setAlternatingRowColors(True)
        self.watchFoldersTreeWidget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.watchFoldersTreeWidget.setRootIsDecorated(False)
        self.watchFoldersTreeWidget.setUniformRowHeights(False)
        self.watchFoldersTreeWidget.setObjectName("watchFoldersTreeWidget")
        self.gridLayout.addWidget(self.watchFoldersTreeWidget, 0, 0, 1, 2)

        self.retranslateUi(ProjectWatchFolder)
        QtCore.QMetaObject.connectSlotsByName(ProjectWatchFolder)

    def retranslateUi(self, ProjectWatchFolder):
        ProjectWatchFolder.setWindowTitle(QtGui.QApplication.translate("ProjectWatchFolder", "Watch Folder", None))
        self.watchEnabledCheckBox.setText(QtGui.QApplication.translate("ProjectWatchFolder", "Watch Folders Enabled", None))
        self.watchFoldersTreeWidget.headerItem().setText(0, QtGui.QApplication.translate("ProjectWatchFolder", "Status", None))
        self.watchFoldersTreeWidget.headerItem().setText(1, QtGui.QApplication.translate("ProjectWatchFolder", "SType", None))
        self.watchFoldersTreeWidget.headerItem().setText(2, QtGui.QApplication.translate("ProjectWatchFolder", "SObject", None))
        self.watchFoldersTreeWidget.headerItem().setText(3, QtGui.QApplication.translate("ProjectWatchFolder", "Repositories", None))

