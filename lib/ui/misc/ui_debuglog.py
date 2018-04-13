# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'misc\ui_debuglog.ui'
#
# Created: Mon Dec 25 21:38:17 2017
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtCore

class Ui_DebugLog(object):
    def setupUi(self, DebugLog):
        DebugLog.setObjectName("DebugLog")
        DebugLog.resize(862, 665)
        self.gridLayout = QtGui.QGridLayout(DebugLog)
        self.gridLayout.setObjectName("gridLayout")
        self.splitter = QtGui.QSplitter(DebugLog)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.treeWidget = QtGui.QTreeWidget(self.splitter)
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(0, "1")
        self.treeWidget.header().setVisible(False)
        self.debugLogTextEdit = QtGui.QTextEdit(self.splitter)
        self.debugLogTextEdit.setObjectName("debugLogTextEdit")
        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.checkBox_4 = QtGui.QCheckBox(DebugLog)
        self.checkBox_4.setObjectName("checkBox_4")
        self.horizontalLayout.addWidget(self.checkBox_4)
        self.checkBox_3 = QtGui.QCheckBox(DebugLog)
        self.checkBox_3.setObjectName("checkBox_3")
        self.horizontalLayout.addWidget(self.checkBox_3)
        self.checkBox_2 = QtGui.QCheckBox(DebugLog)
        self.checkBox_2.setObjectName("checkBox_2")
        self.horizontalLayout.addWidget(self.checkBox_2)
        self.checkBox = QtGui.QCheckBox(DebugLog)
        self.checkBox.setObjectName("checkBox")
        self.horizontalLayout.addWidget(self.checkBox)
        self.checkBox_5 = QtGui.QCheckBox(DebugLog)
        self.checkBox_5.setObjectName("checkBox_5")
        self.horizontalLayout.addWidget(self.checkBox_5)
        self.checkBox_6 = QtGui.QCheckBox(DebugLog)
        self.checkBox_6.setObjectName("checkBox_6")
        self.horizontalLayout.addWidget(self.checkBox_6)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)
        self.gridLayout.setRowMinimumHeight(0, 1)

        self.retranslateUi(DebugLog)
        QtCore.QMetaObject.connectSlotsByName(DebugLog)

    def retranslateUi(self, DebugLog):
        DebugLog.setWindowTitle(QtGui.QApplication.translate("DebugLog", "Debug Log", None))
        self.checkBox_4.setText(QtGui.QApplication.translate("DebugLog", "Info", None))
        self.checkBox_3.setText(QtGui.QApplication.translate("DebugLog", "Warning", None))
        self.checkBox_2.setText(QtGui.QApplication.translate("DebugLog", "Error", None))
        self.checkBox.setText(QtGui.QApplication.translate("DebugLog", "Critical", None))
        self.checkBox_5.setText(QtGui.QApplication.translate("DebugLog", "Log", None))
        self.checkBox_6.setText(QtGui.QApplication.translate("DebugLog", "Exception", None))

