# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'conf\ui_mayaPage.ui'
#
# Created: Sat Oct  5 00:17:17 2019
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

class Ui_mayaScenePageWidget(object):
    def setupUi(self, mayaScenePageWidget):
        mayaScenePageWidget.setObjectName("mayaScenePageWidget")
        self.mayaScenePageWidgetLayout = QtGui.QGridLayout(mayaScenePageWidget)
        self.mayaScenePageWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.mayaScenePageWidgetLayout.setObjectName("mayaScenePageWidgetLayout")
        self.currentWorkdirLable = QtGui.QLabel(mayaScenePageWidget)
        self.currentWorkdirLable.setObjectName("currentWorkdirLable")
        self.mayaScenePageWidgetLayout.addWidget(self.currentWorkdirLable, 0, 0, 1, 1)
        self.currentWorkdirLineEdit = QtGui.QLineEdit(mayaScenePageWidget)
        self.currentWorkdirLineEdit.setReadOnly(True)
        self.currentWorkdirLineEdit.setObjectName("currentWorkdirLineEdit")
        self.mayaScenePageWidgetLayout.addWidget(self.currentWorkdirLineEdit, 0, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.mayaScenePageWidgetLayout.addItem(spacerItem, 4, 0, 1, 2)
        self.createMayaDirsCheckBox = QtGui.QCheckBox(mayaScenePageWidget)
        self.createMayaDirsCheckBox.setChecked(True)
        self.createMayaDirsCheckBox.setObjectName("createMayaDirsCheckBox")
        self.mayaScenePageWidgetLayout.addWidget(self.createMayaDirsCheckBox, 2, 0, 1, 1)
        self.createPlayblastCheckBox = QtGui.QCheckBox(mayaScenePageWidget)
        self.createPlayblastCheckBox.setChecked(True)
        self.createPlayblastCheckBox.setObjectName("createPlayblastCheckBox")
        self.mayaScenePageWidgetLayout.addWidget(self.createPlayblastCheckBox, 3, 0, 1, 1)
        self.mayaSaveFormatLabel = QtGui.QLabel(mayaScenePageWidget)
        self.mayaSaveFormatLabel.setObjectName("mayaSaveFormatLabel")
        self.mayaScenePageWidgetLayout.addWidget(self.mayaSaveFormatLabel, 1, 0, 1, 1)
        self.formatTypeComboBox = QtGui.QComboBox(mayaScenePageWidget)
        self.formatTypeComboBox.setObjectName("formatTypeComboBox")
        self.mayaScenePageWidgetLayout.addWidget(self.formatTypeComboBox, 1, 1, 1, 1)
        self.mayaScenePageWidgetLayout.setColumnMinimumWidth(1, 100)
        self.mayaScenePageWidgetLayout.setColumnStretch(1, 1)

        self.retranslateUi(mayaScenePageWidget)
        QtCore.QMetaObject.connectSlotsByName(mayaScenePageWidget)

    def retranslateUi(self, mayaScenePageWidget):
        self.currentWorkdirLable.setText(u"Current Workdir:")
        self.createMayaDirsCheckBox.setText(u"Create Maya Dirs (worspace.mel)")
        self.createPlayblastCheckBox.setText(u"Create screenshot (playblast)")
        self.mayaSaveFormatLabel.setText(u"Maya Saving Format:")

