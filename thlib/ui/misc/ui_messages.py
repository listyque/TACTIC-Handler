# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'misc\ui_messages.ui'
#
# Created: Sat Oct  5 00:17:10 2019
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_messages(object):
    def setupUi(self, messages):
        messages.setObjectName("messages")
        messages.resize(848, 636)
        self.verticalLayout_2 = QtGui.QVBoxLayout(messages)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.splitter = QtGui.QSplitter(messages)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.usersTreeWidget = QtGui.QTreeWidget(self.splitter)
        self.usersTreeWidget.setMaximumSize(QtCore.QSize(400, 16777215))
        self.usersTreeWidget.setStyleSheet("QTreeView::item {padding: 2px;}")
        self.usersTreeWidget.setAlternatingRowColors(True)
        self.usersTreeWidget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.usersTreeWidget.setObjectName("usersTreeWidget")
        self.usersTreeWidget.headerItem().setText(0, "1")
        self.usersTreeWidget.header().setVisible(False)
        self.verticalLayoutWidget = QtGui.QWidget(self.splitter)
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.tabsVerticalLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.tabsVerticalLayout.setSpacing(0)
        self.tabsVerticalLayout.setContentsMargins(0, 0, 0, 0)
        self.tabsVerticalLayout.setObjectName("tabsVerticalLayout")
        self.verticalLayout_2.addWidget(self.splitter)

        self.retranslateUi(messages)
        QtCore.QMetaObject.connectSlotsByName(messages)

    def retranslateUi(self, messages):
        messages.setWindowTitle(QtGui.QApplication.translate("messages", "Form", None, QtGui.QApplication.UnicodeUTF8))

