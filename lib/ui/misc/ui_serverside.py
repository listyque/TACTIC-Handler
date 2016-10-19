# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'misc\ui_serverside.ui'
#
# Created: Thu Sep 22 00:04:23 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

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
        self.scriptTextEdit.setObjectName("scriptTextEdit")
        self.verticalLayout.addWidget(self.splitter)
        self.runScriptPushButton = QtGui.QPushButton(scriptEditForm)
        self.runScriptPushButton.setObjectName("runScriptPushButton")
        self.verticalLayout.addWidget(self.runScriptPushButton)

        self.retranslateUi(scriptEditForm)
        QtCore.QMetaObject.connectSlotsByName(scriptEditForm)

    def retranslateUi(self, scriptEditForm):
        scriptEditForm.setWindowTitle(QtGui.QApplication.translate("scriptEditForm", "Server-side Script editor", None, QtGui.QApplication.UnicodeUTF8))
        self.runScriptPushButton.setText(QtGui.QApplication.translate("scriptEditForm", "Run Script", None, QtGui.QApplication.UnicodeUTF8))

