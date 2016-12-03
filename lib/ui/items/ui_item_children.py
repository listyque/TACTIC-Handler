# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'items/ui_item_children.ui'
#
# Created: Thu Dec  1 18:35:07 2016
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_childrenItem(object):
    def setupUi(self, childrenItem):
        childrenItem.setObjectName("childrenItem")
        childrenItem.setWindowTitle("")
        childrenItem.setStyleSheet("QTreeView::item {border-width: 0px;    border-radius: 0px;padding: 0px;}\n"
"")
        self.horizontalLayout = QtGui.QHBoxLayout(childrenItem)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.childrenToolButton = QtGui.QToolButton(childrenItem)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.childrenToolButton.sizePolicy().hasHeightForWidth())
        self.childrenToolButton.setSizePolicy(sizePolicy)
        self.childrenToolButton.setMinimumSize(QtCore.QSize(0, 24))
        self.childrenToolButton.setMaximumSize(QtCore.QSize(16777215, 24))
        self.childrenToolButton.setCheckable(True)
        self.childrenToolButton.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.childrenToolButton.setObjectName("childrenToolButton")
        self.horizontalLayout.addWidget(self.childrenToolButton)
        self.addNewSObjectToolButton = QtGui.QToolButton(childrenItem)
        self.addNewSObjectToolButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.addNewSObjectToolButton.setAutoRaise(True)
        self.addNewSObjectToolButton.setObjectName("addNewSObjectToolButton")
        self.horizontalLayout.addWidget(self.addNewSObjectToolButton)

        self.retranslateUi(childrenItem)
        QtCore.QMetaObject.connectSlotsByName(childrenItem)

    def retranslateUi(self, childrenItem):
        pass

