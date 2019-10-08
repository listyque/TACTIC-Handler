# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'misc\ui_debuglog.ui'
#
# Created: Sat Oct  5 00:17:09 2019
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

class Ui_DebugLog(object):
    def setupUi(self, DebugLog):
        DebugLog.setObjectName("DebugLog")
        DebugLog.resize(1195, 933)
        self.gridLayout = QtGui.QGridLayout(DebugLog)
        self.gridLayout.setObjectName("gridLayout")
        self.splitter = QtGui.QSplitter(DebugLog)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.treeWidget = QtGui.QTreeWidget(self.splitter)
        self.treeWidget.setMaximumSize(QtCore.QSize(320, 16777215))
        self.treeWidget.setStyleSheet("QTreeView::item {padding: 2px;}")
        self.treeWidget.setAlternatingRowColors(True)
        self.treeWidget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(0, "1")
        self.treeWidget.header().setVisible(False)
        self.debugLogTextEdit = QtGui.QTextEdit(self.splitter)
        self.debugLogTextEdit.setObjectName("debugLogTextEdit")
        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.logCheckBox = QtGui.QCheckBox(DebugLog)
        self.logCheckBox.setObjectName("logCheckBox")
        self.horizontalLayout.addWidget(self.logCheckBox)
        self.infoCheckBox = QtGui.QCheckBox(DebugLog)
        self.infoCheckBox.setObjectName("infoCheckBox")
        self.horizontalLayout.addWidget(self.infoCheckBox)
        self.warningCheckBox = QtGui.QCheckBox(DebugLog)
        self.warningCheckBox.setObjectName("warningCheckBox")
        self.horizontalLayout.addWidget(self.warningCheckBox)
        self.exceptionCheckBox = QtGui.QCheckBox(DebugLog)
        self.exceptionCheckBox.setObjectName("exceptionCheckBox")
        self.horizontalLayout.addWidget(self.exceptionCheckBox)
        self.errorCheckBox = QtGui.QCheckBox(DebugLog)
        self.errorCheckBox.setObjectName("errorCheckBox")
        self.horizontalLayout.addWidget(self.errorCheckBox)
        self.criticalCheckBox = QtGui.QCheckBox(DebugLog)
        self.criticalCheckBox.setObjectName("criticalCheckBox")
        self.horizontalLayout.addWidget(self.criticalCheckBox)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)
        self.gridLayout.setRowMinimumHeight(0, 1)

        self.retranslateUi(DebugLog)
        QtCore.QMetaObject.connectSlotsByName(DebugLog)

    def retranslateUi(self, DebugLog):
        DebugLog.setWindowTitle(u"Debug Log")
        self.logCheckBox.setText(u"Log")
        self.infoCheckBox.setText(u"Info")
        self.warningCheckBox.setText(u"Warning")
        self.exceptionCheckBox.setText(u"Exception")
        self.errorCheckBox.setText(u"Error")
        self.criticalCheckBox.setText(u"Critical")

