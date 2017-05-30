# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'misc/ui_collapsable.ui'
#
# Created: Thu Apr 27 14:15:15 2017
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtCore


class Ui_collapsableWidget(object):
    def setupUi(self, collapsableWidget):
        collapsableWidget.setObjectName("collapsableWidget")
        self.verticalLayout = QtGui.QVBoxLayout(collapsableWidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.collapseToolButton = QtGui.QToolButton(collapsableWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.collapseToolButton.sizePolicy().hasHeightForWidth())
        self.collapseToolButton.setSizePolicy(sizePolicy)
        self.collapseToolButton.setMinimumSize(QtCore.QSize(0, 25))
        self.collapseToolButton.setCheckable(True)
        self.collapseToolButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.collapseToolButton.setAutoRaise(True)
        self.collapseToolButton.setObjectName("collapseToolButton")
        self.verticalLayout.addWidget(self.collapseToolButton)
        self.widget = QtGui.QWidget(collapsableWidget)
        self.widget.setObjectName("widget")
        self.verticalLayout.addWidget(self.widget)
        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(collapsableWidget)
        QtCore.QMetaObject.connectSlotsByName(collapsableWidget)

    def retranslateUi(self, collapsableWidget):
        pass

