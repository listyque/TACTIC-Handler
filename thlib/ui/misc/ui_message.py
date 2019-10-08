# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'misc\ui_message.ui'
#
# Created: Sat Oct  5 00:17:10 2019
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

class Ui_messages(object):
    def setupUi(self, messages):
        messages.setObjectName("messages")
        messages.resize(671, 497)
        self.gridLayout_2 = QtGui.QGridLayout(messages)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.splitter_2 = QtGui.QSplitter(messages)
        self.splitter_2.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_2.setObjectName("splitter_2")
        self.usersTreeWidget = QtGui.QTreeWidget(self.splitter_2)
        self.usersTreeWidget.setMaximumSize(QtCore.QSize(400, 16777215))
        self.usersTreeWidget.setStyleSheet("QTreeView::item {padding: 2px;}")
        self.usersTreeWidget.setAlternatingRowColors(True)
        self.usersTreeWidget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.usersTreeWidget.setObjectName("usersTreeWidget")
        self.usersTreeWidget.headerItem().setText(0, "1")
        self.usersTreeWidget.header().setVisible(False)
        self.splitter = QtGui.QSplitter(self.splitter_2)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")
        self.conversationScrollArea = QtGui.QScrollArea(self.splitter)
        self.conversationScrollArea.setWidgetResizable(True)
        self.conversationScrollArea.setObjectName("conversationScrollArea")
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 323, 69))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.conversationScrollArea.setWidget(self.scrollAreaWidgetContents)
        self.gridLayoutWidget = QtGui.QWidget(self.splitter)
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtGui.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.replyPushButton = QtGui.QPushButton(self.gridLayoutWidget)
        self.replyPushButton.setMinimumSize(QtCore.QSize(80, 0))
        self.replyPushButton.setMaximumSize(QtCore.QSize(80, 16777215))
        self.replyPushButton.setObjectName("replyPushButton")
        self.gridLayout.addWidget(self.replyPushButton, 3, 2, 1, 1)
        self.replyTextEdit = QtGui.QTextEdit(self.gridLayoutWidget)
        self.replyTextEdit.setMaximumSize(QtCore.QSize(16777215, 200))
        self.replyTextEdit.setStyleSheet("")
        self.replyTextEdit.setObjectName("replyTextEdit")
        self.gridLayout.addWidget(self.replyTextEdit, 1, 0, 1, 3)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 3, 1, 1, 1)
        self.editorLayout = QtGui.QVBoxLayout()
        self.editorLayout.setSpacing(0)
        self.editorLayout.setContentsMargins(0, 0, 0, 0)
        self.editorLayout.setObjectName("editorLayout")
        self.gridLayout.addLayout(self.editorLayout, 0, 0, 1, 3)
        self.gridLayout_2.addWidget(self.splitter_2, 0, 0, 1, 1)

        self.retranslateUi(messages)
        QtCore.QMetaObject.connectSlotsByName(messages)

    def retranslateUi(self, messages):
        messages.setWindowTitle(u"Form")
        self.replyPushButton.setText(u"Reply")

