# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_item_task_detail.ui'
#
# Created: Wed Feb 10 16:53:13 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_taskDetailItem(object):
    def setupUi(self, taskDetailItem):
        taskDetailItem.setObjectName("taskDetailItem")
        taskDetailItem.resize(240, 40)
        taskDetailItem.setWindowTitle("")
        taskDetailItem.setStyleSheet("QLabel {\n"
"    border: 0px;\n"
"    background: background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 0, 0, 0), stop:1 rgba(255, 255, 255, 40));\n"
"    padding: 3px;\n"
"}")
        self.gridLayout = QtGui.QGridLayout(taskDetailItem)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.dateFromLabel = QtGui.QLabel(taskDetailItem)
        self.dateFromLabel.setAccessibleDescription("")
        self.dateFromLabel.setStyleSheet("QLabel {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(64, 64, 64, 175));\n"
"    border-bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(128, 128, 128, 175));\n"
"    padding: 0px;\n"
"}")
        self.dateFromLabel.setTextFormat(QtCore.Qt.PlainText)
        self.dateFromLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.dateFromLabel.setObjectName("dateFromLabel")
        self.gridLayout.addWidget(self.dateFromLabel, 0, 1, 1, 1)
        self.dateToLabel = QtGui.QLabel(taskDetailItem)
        self.dateToLabel.setAccessibleDescription("")
        self.dateToLabel.setStyleSheet("QLabel {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(64, 64, 64, 175));\n"
"    border-bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(128, 128, 128, 175));\n"
"    padding: 0px;\n"
"}")
        self.dateToLabel.setTextFormat(QtCore.Qt.PlainText)
        self.dateToLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.dateToLabel.setObjectName("dateToLabel")
        self.gridLayout.addWidget(self.dateToLabel, 1, 1, 1, 1)
        self.stautsLabel = QtGui.QLabel(taskDetailItem)
        self.stautsLabel.setMinimumSize(QtCore.QSize(0, 20))
        self.stautsLabel.setStyleSheet("QLabel {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(125, 45, 192, 175), stop:1 rgba(64, 64,64, 0));\n"
"    border-bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(64, 64, 64, 175), stop:1 rgba(255, 255,255, 0));\n"
"}")
        self.stautsLabel.setTextFormat(QtCore.Qt.PlainText)
        self.stautsLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.stautsLabel.setMargin(2)
        self.stautsLabel.setObjectName("stautsLabel")
        self.gridLayout.addWidget(self.stautsLabel, 0, 0, 1, 1)
        self.priorityLabel = QtGui.QLabel(taskDetailItem)
        self.priorityLabel.setMinimumSize(QtCore.QSize(0, 20))
        self.priorityLabel.setStyleSheet("QLabel {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 0, 0, 175), stop:1 rgba(64, 64,64, 0));\n"
"    border-bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(64, 64, 64, 175), stop:1 rgba(255, 255,255, 0));\n"
"}")
        self.priorityLabel.setTextFormat(QtCore.Qt.PlainText)
        self.priorityLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.priorityLabel.setMargin(2)
        self.priorityLabel.setObjectName("priorityLabel")
        self.gridLayout.addWidget(self.priorityLabel, 1, 0, 1, 1)

        self.retranslateUi(taskDetailItem)
        QtCore.QMetaObject.connectSlotsByName(taskDetailItem)

    def retranslateUi(self, taskDetailItem):
        self.dateFromLabel.setText(QtGui.QApplication.translate("taskDetailItem", "From: 2016.02.07. 16:21:57", None, QtGui.QApplication.UnicodeUTF8))
        self.dateToLabel.setText(QtGui.QApplication.translate("taskDetailItem", "To: 2016.02.09. 16:21:57", None, QtGui.QApplication.UnicodeUTF8))
        self.stautsLabel.setText(QtGui.QApplication.translate("taskDetailItem", "Status: Assignment", None, QtGui.QApplication.UnicodeUTF8))
        self.priorityLabel.setText(QtGui.QApplication.translate("taskDetailItem", "Priority: 5 - Critical", None, QtGui.QApplication.UnicodeUTF8))

