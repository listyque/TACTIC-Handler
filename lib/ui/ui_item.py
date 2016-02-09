# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_item.ui'
#
# Created: Sun Feb 07 23:52:36 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_item(object):
    def setupUi(self, item):
        item.setObjectName("item")
        item.setWindowTitle("")
        item.setStyleSheet("QLabel {\n"
"    border: 0px;\n"
"    background: background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 0, 0, 0), stop:1 rgba(255, 255, 255, 40));\n"
"    padding: 3px;\n"
"}")
        self.gridLayout = QtGui.QGridLayout(item)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.dateLabel = QtGui.QLabel(item)
        self.dateLabel.setMinimumSize(QtCore.QSize(0, 25))
        self.dateLabel.setAccessibleDescription("")
        self.dateLabel.setStyleSheet("QLabel {\n"
"    padding: 4px;\n"
"}")
        self.dateLabel.setTextFormat(QtCore.Qt.PlainText)
        self.dateLabel.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing)
        self.dateLabel.setObjectName("dateLabel")
        self.gridLayout.addWidget(self.dateLabel, 1, 1, 1, 1)
        self.fileNameLabel = QtGui.QLabel(item)
        self.fileNameLabel.setStyleSheet("QLabel {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(128, 128, 128, 75), stop:1 rgba(64, 64,64, 0));\n"
"    border-bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(64, 64, 64, 75), stop:1 rgba(255, 255,255, 0));\n"
"    padding: 0px;\n"
"}")
        self.fileNameLabel.setTextFormat(QtCore.Qt.PlainText)
        self.fileNameLabel.setObjectName("fileNameLabel")
        self.gridLayout.addWidget(self.fileNameLabel, 0, 0, 1, 1)
        self.commentLabel = QtGui.QLabel(item)
        self.commentLabel.setMinimumSize(QtCore.QSize(0, 25))
        self.commentLabel.setTextFormat(QtCore.Qt.PlainText)
        self.commentLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.commentLabel.setWordWrap(True)
        self.commentLabel.setMargin(2)
        self.commentLabel.setObjectName("commentLabel")
        self.gridLayout.addWidget(self.commentLabel, 1, 0, 1, 1)
        self.tasksToolButton = QtGui.QToolButton(item)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tasksToolButton.sizePolicy().hasHeightForWidth())
        self.tasksToolButton.setSizePolicy(sizePolicy)
        self.tasksToolButton.setMaximumSize(QtCore.QSize(60, 20))
        self.tasksToolButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.tasksToolButton.setAutoRaise(True)
        self.tasksToolButton.setArrowType(QtCore.Qt.UpArrow)
        self.tasksToolButton.setObjectName("tasksToolButton")
        self.gridLayout.addWidget(self.tasksToolButton, 0, 1, 1, 1)

        self.retranslateUi(item)
        QtCore.QMetaObject.connectSlotsByName(item)

    def retranslateUi(self, item):
        self.tasksToolButton.setText(QtGui.QApplication.translate("item", "Tastks", None, QtGui.QApplication.UnicodeUTF8))

