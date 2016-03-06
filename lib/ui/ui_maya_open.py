# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_maya_open.ui'
#
# Created: Fri Jan 22 16:24:49 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_openOptions(object):
    def setupUi(self, openOptions):
        openOptions.setObjectName("openOptions")
        openOptions.setWindowModality(QtCore.Qt.ApplicationModal)
        openOptions.resize(400, 100)
        openOptions.setMinimumSize(QtCore.QSize(400, 0))
        openOptions.setMaximumSize(QtCore.QSize(16777215, 200))
        self.gridLayout = QtGui.QGridLayout(openOptions)
        self.gridLayout.setObjectName("gridLayout")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 0, 1, 1)
        self.optionsOpenPushButton = QtGui.QPushButton(openOptions)
        self.optionsOpenPushButton.setObjectName("optionsOpenPushButton")
        self.gridLayout.addWidget(self.optionsOpenPushButton, 1, 1, 1, 1)
        self.openPushButton = QtGui.QPushButton(openOptions)
        self.openPushButton.setObjectName("openPushButton")
        self.gridLayout.addWidget(self.openPushButton, 1, 2, 1, 1)
        self.groupBox = QtGui.QGroupBox(openOptions)
        self.groupBox.setFlat(True)
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayout = QtGui.QHBoxLayout(self.groupBox)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.setWorkdirCheckBox = QtGui.QCheckBox(self.groupBox)
        self.setWorkdirCheckBox.setChecked(True)
        self.setWorkdirCheckBox.setObjectName("setWorkdirCheckBox")
        self.horizontalLayout.addWidget(self.setWorkdirCheckBox)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.savePushButton = QtGui.QPushButton(self.groupBox)
        self.savePushButton.setObjectName("savePushButton")
        self.horizontalLayout.addWidget(self.savePushButton)
        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 3)

        self.retranslateUi(openOptions)
        QtCore.QMetaObject.connectSlotsByName(openOptions)

    def retranslateUi(self, openOptions):
        openOptions.setWindowTitle(QtGui.QApplication.translate("openOptions", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.optionsOpenPushButton.setText(QtGui.QApplication.translate("openOptions", "Opening options", None, QtGui.QApplication.UnicodeUTF8))
        self.openPushButton.setText(QtGui.QApplication.translate("openOptions", "Open", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("openOptions", "Opening:", None, QtGui.QApplication.UnicodeUTF8))
        self.setWorkdirCheckBox.setText(QtGui.QApplication.translate("openOptions", "Setup working directory", None, QtGui.QApplication.UnicodeUTF8))
        self.savePushButton.setText(QtGui.QApplication.translate("openOptions", "Save", None, QtGui.QApplication.UnicodeUTF8))

