# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'misc/ui_serverside.ui'
#
# Created: Thu Apr 27 14:15:15 2017
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtCore


class Ui_scriptEditForm(object):
    def setupUi(self, scriptEditForm):
        scriptEditForm.setObjectName("scriptEditForm")
        scriptEditForm.resize(707, 541)
        self.verticalLayout = QtGui.QVBoxLayout(scriptEditForm)
        self.verticalLayout.setObjectName("verticalLayout")
        self.splitter = QtGui.QSplitter(scriptEditForm)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")
        self.stackTraceTextEdit = QtGui.QTextEdit(self.splitter)
        self.stackTraceTextEdit.setObjectName("stackTraceTextEdit")
        self.scriptTextEdit = QtGui.QTextEdit(self.splitter)
        self.scriptTextEdit.setAcceptRichText(False)
        self.scriptTextEdit.setObjectName("scriptTextEdit")
        self.verticalLayout.addWidget(self.splitter)
        self.runScriptPushButton = QtGui.QPushButton(scriptEditForm)
        self.runScriptPushButton.setObjectName("runScriptPushButton")
        self.verticalLayout.addWidget(self.runScriptPushButton)

        self.retranslateUi(scriptEditForm)
        QtCore.QMetaObject.connectSlotsByName(scriptEditForm)

    def retranslateUi(self, scriptEditForm):
        scriptEditForm.setWindowTitle(QtGui.QApplication.translate("scriptEditForm", "Server-side Script editor", None))
        self.runScriptPushButton.setText(QtGui.QApplication.translate("scriptEditForm", "Run Script", None))

