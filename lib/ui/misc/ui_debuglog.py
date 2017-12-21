# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'misc/ui_debuglog.ui'
#
# Created: Wed Dec 20 18:56:55 2017
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtCore

class Ui_DebugLog(object):
    def setupUi(self, DebugLog):
        DebugLog.setObjectName("DebugLog")
        DebugLog.resize(908, 651)
        self.gridLayout = QtGui.QGridLayout(DebugLog)
        self.gridLayout.setContentsMargins(6, 6, 6, 6)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.debugLogTextEdit = QtGui.QTextEdit(DebugLog)
        self.debugLogTextEdit.setObjectName("debugLogTextEdit")
        self.gridLayout.addWidget(self.debugLogTextEdit, 0, 0, 1, 1)

        self.retranslateUi(DebugLog)
        QtCore.QMetaObject.connectSlotsByName(DebugLog)

    def retranslateUi(self, DebugLog):
        DebugLog.setWindowTitle(QtGui.QApplication.translate("DebugLog", "Debug Log", None))

