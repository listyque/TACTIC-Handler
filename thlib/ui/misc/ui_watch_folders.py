# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'misc\ui_watch_folders.ui'
#
# Created: Sat Oct  5 00:17:12 2019
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

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
        ProjectWatchFolder.setWindowTitle(QtGui.QApplication.translate("ProjectWatchFolder", "Watch Folder", None, QtGui.QApplication.UnicodeUTF8))
        self.watchEnabledCheckBox.setText(QtGui.QApplication.translate("ProjectWatchFolder", "Watch Folders Enabled", None, QtGui.QApplication.UnicodeUTF8))
        self.watchFoldersTreeWidget.headerItem().setText(0, QtGui.QApplication.translate("ProjectWatchFolder", "Status", None, QtGui.QApplication.UnicodeUTF8))
        self.watchFoldersTreeWidget.headerItem().setText(1, QtGui.QApplication.translate("ProjectWatchFolder", "SType", None, QtGui.QApplication.UnicodeUTF8))
        self.watchFoldersTreeWidget.headerItem().setText(2, QtGui.QApplication.translate("ProjectWatchFolder", "SObject", None, QtGui.QApplication.UnicodeUTF8))
        self.watchFoldersTreeWidget.headerItem().setText(3, QtGui.QApplication.translate("ProjectWatchFolder", "Repositories", None, QtGui.QApplication.UnicodeUTF8))

