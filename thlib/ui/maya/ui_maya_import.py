# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'maya/ui_maya_import.ui'
#
# Created: Thu Apr 27 14:15:16 2017
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore

class Ui_importOptions(object):
    def setupUi(self, importOptions):
        importOptions.setObjectName("importOptions")
        importOptions.setWindowModality(QtCore.Qt.ApplicationModal)
        importOptions.resize(400, 100)
        importOptions.setMinimumSize(QtCore.QSize(400, 0))
        importOptions.setMaximumSize(QtCore.QSize(16777215, 100))
        self.gridLayout = QtGui.QGridLayout(importOptions)
        self.gridLayout.setObjectName("gridLayout")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 0, 1, 1)
        self.optionsImportPushButton = QtGui.QPushButton(importOptions)
        self.optionsImportPushButton.setObjectName("optionsImportPushButton")
        self.gridLayout.addWidget(self.optionsImportPushButton, 1, 1, 1, 1)
        self.importPushButton = QtGui.QPushButton(importOptions)
        self.importPushButton.setObjectName("importPushButton")
        self.gridLayout.addWidget(self.importPushButton, 1, 2, 1, 1)
        self.groupBox = QtGui.QGroupBox(importOptions)
        self.groupBox.setFlat(True)
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayout = QtGui.QHBoxLayout(self.groupBox)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalSlider = QtGui.QSlider(self.groupBox)
        self.horizontalSlider.setMinimum(1)
        self.horizontalSlider.setMaximum(100)
        self.horizontalSlider.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider.setObjectName("horizontalSlider")
        self.horizontalLayout.addWidget(self.horizontalSlider)
        self.spinBox = QtGui.QSpinBox(self.groupBox)
        self.spinBox.setAccelerated(True)
        self.spinBox.setMinimum(1)
        self.spinBox.setMaximum(100)
        self.spinBox.setObjectName("spinBox")
        self.horizontalLayout.addWidget(self.spinBox)
        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 3)

        self.retranslateUi(importOptions)
        QtCore.QObject.connect(self.horizontalSlider, QtCore.SIGNAL("valueChanged(int)"), self.spinBox.setValue)
        QtCore.QObject.connect(self.spinBox, QtCore.SIGNAL("valueChanged(int)"), self.horizontalSlider.setValue)
        QtCore.QMetaObject.connectSlotsByName(importOptions)

    def retranslateUi(self, importOptions):
        importOptions.setWindowTitle(QtGui.QApplication.translate("importOptions", "Form", None))
        self.optionsImportPushButton.setText(QtGui.QApplication.translate("importOptions", "Importing options", None))
        self.importPushButton.setText(QtGui.QApplication.translate("importOptions", "Import", None))
        self.groupBox.setTitle(QtGui.QApplication.translate("importOptions", "Import count:", None))

