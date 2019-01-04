# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'misc/ui_horizontal_collapsable.ui'
#
# Created: Thu Apr 27 14:15:16 2017
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore


class Ui_horizontalCollapsableWidget(object):
    def setupUi(self, horizontalCollapsableWidget):
        horizontalCollapsableWidget.setObjectName("horizontalCollapsableWidget")
        self.horizontalLayout = QtGui.QHBoxLayout(horizontalCollapsableWidget)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.widget = QtGui.QWidget(horizontalCollapsableWidget)
        self.widget.setObjectName("widget")
        self.horizontalLayout.addWidget(self.widget)
        self.collapseToolButton = QtGui.QToolButton(horizontalCollapsableWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.collapseToolButton.sizePolicy().hasHeightForWidth())
        self.collapseToolButton.setSizePolicy(sizePolicy)
        self.collapseToolButton.setMaximumSize(QtCore.QSize(12, 22))
        self.collapseToolButton.setAutoRaise(True)
        self.collapseToolButton.setObjectName("collapseToolButton")
        self.horizontalLayout.addWidget(self.collapseToolButton)
        self.horizontalLayout.setStretch(1, 1)

        self.retranslateUi(horizontalCollapsableWidget)
        QtCore.QMetaObject.connectSlotsByName(horizontalCollapsableWidget)

    def retranslateUi(self, horizontalCollapsableWidget):
        pass

