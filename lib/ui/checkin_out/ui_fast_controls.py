# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'checkin_out/ui_fast_controls.ui'
#
# Created: Fri May  5 19:22:58 2017
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtCore


class Ui_fastControls(object):
    def setupUi(self, fastControls):
        fastControls.setObjectName("fastControls")
        self.fastControlsHorizontalLayout = QtGui.QHBoxLayout(fastControls)
        self.fastControlsHorizontalLayout.setSpacing(4)
        self.fastControlsHorizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.fastControlsHorizontalLayout.setObjectName("fastControlsHorizontalLayout")
        self.savePushButton = QtGui.QToolButton(fastControls)
        self.savePushButton.setEnabled(False)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.savePushButton.sizePolicy().hasHeightForWidth())
        self.savePushButton.setSizePolicy(sizePolicy)
        self.savePushButton.setMinimumSize(QtCore.QSize(75, 22))
        self.savePushButton.setChecked(False)
        self.savePushButton.setPopupMode(QtGui.QToolButton.MenuButtonPopup)
        self.savePushButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.savePushButton.setAutoRaise(True)
        self.savePushButton.setObjectName("savePushButton")
        self.fastControlsHorizontalLayout.addWidget(self.savePushButton)
        self.formatTypeComboBox = QtGui.QComboBox(fastControls)
        self.formatTypeComboBox.setObjectName("formatTypeComboBox")
        self.fastControlsHorizontalLayout.addWidget(self.formatTypeComboBox)
        self.openPushButton = QtGui.QToolButton(fastControls)
        self.openPushButton.setEnabled(False)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.openPushButton.sizePolicy().hasHeightForWidth())
        self.openPushButton.setSizePolicy(sizePolicy)
        self.openPushButton.setMinimumSize(QtCore.QSize(75, 22))
        self.openPushButton.setChecked(False)
        self.openPushButton.setPopupMode(QtGui.QToolButton.MenuButtonPopup)
        self.openPushButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.openPushButton.setAutoRaise(True)
        self.openPushButton.setObjectName("openPushButton")
        self.fastControlsHorizontalLayout.addWidget(self.openPushButton)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        self.fastControlsHorizontalLayout.addItem(spacerItem)
        self.processLabel = QtGui.QLabel(fastControls)
        self.processLabel.setObjectName("processLabel")
        self.fastControlsHorizontalLayout.addWidget(self.processLabel)
        self.processComboBox = QtGui.QComboBox(fastControls)
        self.processComboBox.setObjectName("processComboBox")
        self.fastControlsHorizontalLayout.addWidget(self.processComboBox)
        self.contextLabel = QtGui.QLabel(fastControls)
        self.contextLabel.setTextFormat(QtCore.Qt.PlainText)
        self.contextLabel.setObjectName("contextLabel")
        self.fastControlsHorizontalLayout.addWidget(self.contextLabel)
        self.contextComboBox = QtGui.QComboBox(fastControls)
        self.contextComboBox.setEditable(True)
        self.contextComboBox.setInsertPolicy(QtGui.QComboBox.NoInsert)
        self.contextComboBox.setObjectName("contextComboBox")
        self.fastControlsHorizontalLayout.addWidget(self.contextComboBox)
        self.fastControlsHorizontalLayout.setStretch(3, 1)
        self.fastControlsHorizontalLayout.setStretch(5, 1)
        self.fastControlsHorizontalLayout.setStretch(7, 1)

        self.retranslateUi(fastControls)
        QtCore.QMetaObject.connectSlotsByName(fastControls)

    def retranslateUi(self, fastControls):
        fastControls.setWindowTitle(QtGui.QApplication.translate("fastControls", "Form", None))
        self.savePushButton.setText(QtGui.QApplication.translate("fastControls", "Save", None))
        self.openPushButton.setText(QtGui.QApplication.translate("fastControls", "Open", None))
        self.processLabel.setText(QtGui.QApplication.translate("fastControls", "Process:", None))
        self.contextLabel.setText(QtGui.QApplication.translate("fastControls", "Context:", None))

