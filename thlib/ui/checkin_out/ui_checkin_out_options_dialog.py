# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'checkin_out\ui_checkin_out_options_dialog.ui'
#
# Created: Sat Oct  5 00:17:18 2019
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

class Ui_checkinOutOptions(object):
    def setupUi(self, checkinOutOptions):
        checkinOutOptions.setObjectName("checkinOutOptions")
        self.gridLayout = QtGui.QGridLayout(checkinOutOptions)
        self.gridLayout.setObjectName("gridLayout")
        self.settingsPerTabCheckBox = QtGui.QCheckBox(checkinOutOptions)
        self.settingsPerTabCheckBox.setObjectName("settingsPerTabCheckBox")
        self.gridLayout.addWidget(self.settingsPerTabCheckBox, 1, 0, 1, 1)
        self.settingsVerticalLayout = QtGui.QVBoxLayout()
        self.settingsVerticalLayout.setSpacing(0)
        self.settingsVerticalLayout.setObjectName("settingsVerticalLayout")
        self.gridLayout.addLayout(self.settingsVerticalLayout, 0, 0, 1, 4)
        self.applyToAllPushButton = QtGui.QPushButton(checkinOutOptions)
        self.applyToAllPushButton.setEnabled(False)
        self.applyToAllPushButton.setMinimumSize(QtCore.QSize(120, 0))
        self.applyToAllPushButton.setObjectName("applyToAllPushButton")
        self.gridLayout.addWidget(self.applyToAllPushButton, 1, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 3, 1, 1)
        self.gridLayout.setRowStretch(0, 1)

        self.retranslateUi(checkinOutOptions)
        QtCore.QObject.connect(self.settingsPerTabCheckBox, QtCore.SIGNAL("toggled(bool)"), self.applyToAllPushButton.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(checkinOutOptions)

    def retranslateUi(self, checkinOutOptions):
        checkinOutOptions.setWindowTitle(u"Form")
        self.settingsPerTabCheckBox.setText(u"Only for This Tab")
        self.applyToAllPushButton.setText(u"Apply to All Tabs")

