# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'maya\ui_maya_reference.ui'
#
# Created: Sat Oct  5 00:17:13 2019
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

class Ui_referenceOptions(object):
    def setupUi(self, referenceOptions):
        referenceOptions.setObjectName("referenceOptions")
        referenceOptions.setWindowModality(QtCore.Qt.ApplicationModal)
        referenceOptions.resize(400, 100)
        referenceOptions.setMinimumSize(QtCore.QSize(400, 0))
        referenceOptions.setMaximumSize(QtCore.QSize(16777215, 100))
        self.gridLayout = QtGui.QGridLayout(referenceOptions)
        self.gridLayout.setObjectName("gridLayout")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 0, 1, 1)
        self.optionsReferencePushButton = QtGui.QPushButton(referenceOptions)
        self.optionsReferencePushButton.setObjectName("optionsReferencePushButton")
        self.gridLayout.addWidget(self.optionsReferencePushButton, 1, 1, 1, 1)
        self.referencePushButton = QtGui.QPushButton(referenceOptions)
        self.referencePushButton.setObjectName("referencePushButton")
        self.gridLayout.addWidget(self.referencePushButton, 1, 2, 1, 1)
        self.groupBox = QtGui.QGroupBox(referenceOptions)
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

        self.retranslateUi(referenceOptions)
        QtCore.QObject.connect(self.horizontalSlider, QtCore.SIGNAL("valueChanged(int)"), self.spinBox.setValue)
        QtCore.QObject.connect(self.spinBox, QtCore.SIGNAL("valueChanged(int)"), self.horizontalSlider.setValue)
        QtCore.QMetaObject.connectSlotsByName(referenceOptions)

    def retranslateUi(self, referenceOptions):
        referenceOptions.setWindowTitle(u"Form")
        self.optionsReferencePushButton.setText(u"Referencing options")
        self.referencePushButton.setText(u"Reference")
        self.groupBox.setTitle(u"Reference count:")

