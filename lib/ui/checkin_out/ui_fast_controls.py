# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'checkin_out\ui_fast_controls.ui'
#
<<<<<<< HEAD
# Created: Sun Nov 19 03:12:54 2017
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
=======
# Created: Tue Oct 17 18:14:45 2017
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
>>>>>>> origin/master
#
# WARNING! All changes made in this file will be lost!

from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtCore


class Ui_fastControls(object):
    def setupUi(self, fastControls):
        fastControls.setObjectName("fastControls")
        self.horizontalLayout = QtGui.QHBoxLayout(fastControls)
        self.horizontalLayout.setSpacing(4)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.formatTypeComboBox = QtGui.QComboBox(fastControls)
        self.formatTypeComboBox.setObjectName("formatTypeComboBox")
        self.horizontalLayout.addWidget(self.formatTypeComboBox)
        self.checkinTypeLabel = QtGui.QLabel(fastControls)
        self.checkinTypeLabel.setTextFormat(QtCore.Qt.PlainText)
        self.checkinTypeLabel.setObjectName("checkinTypeLabel")
        self.horizontalLayout.addWidget(self.checkinTypeLabel)
        self.checkinTypeComboBox = QtGui.QComboBox(fastControls)
        self.checkinTypeComboBox.setObjectName("checkinTypeComboBox")
        self.checkinTypeComboBox.addItem("")
        self.checkinTypeComboBox.addItem("")
        self.checkinTypeComboBox.addItem("")
        self.checkinTypeComboBox.addItem("")
        self.checkinTypeComboBox.addItem("")
        self.horizontalLayout.addWidget(self.checkinTypeComboBox)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
<<<<<<< HEAD
        self.explicitFilenameLabel = QtGui.QLabel(fastControls)
        self.explicitFilenameLabel.setObjectName("explicitFilenameLabel")
        self.horizontalLayout.addWidget(self.explicitFilenameLabel)
        self.explicitFilenameLineEdit = QtGui.QLineEdit(fastControls)
        self.explicitFilenameLineEdit.setObjectName("explicitFilenameLineEdit")
        self.horizontalLayout.addWidget(self.explicitFilenameLineEdit)
=======
>>>>>>> origin/master
        self.processLabel = QtGui.QLabel(fastControls)
        self.processLabel.setObjectName("processLabel")
        self.horizontalLayout.addWidget(self.processLabel)
        self.processComboBox = QtGui.QComboBox(fastControls)
        self.processComboBox.setObjectName("processComboBox")
        self.horizontalLayout.addWidget(self.processComboBox)
        self.contextLabel = QtGui.QLabel(fastControls)
        self.contextLabel.setTextFormat(QtCore.Qt.PlainText)
        self.contextLabel.setObjectName("contextLabel")
        self.horizontalLayout.addWidget(self.contextLabel)
        self.contextComboBox = QtGui.QComboBox(fastControls)
        self.contextComboBox.setEditable(True)
        self.contextComboBox.setInsertPolicy(QtGui.QComboBox.NoInsert)
        self.contextComboBox.setObjectName("contextComboBox")
        self.horizontalLayout.addWidget(self.contextComboBox)
<<<<<<< HEAD
        self.horizontalLayout.setStretch(3, 1)
        self.horizontalLayout.setStretch(5, 1)
        self.horizontalLayout.setStretch(9, 1)
=======
        self.horizontalLayout.setStretch(2, 1)
        self.horizontalLayout.setStretch(3, 1)
        self.horizontalLayout.setStretch(5, 1)
        self.horizontalLayout.setStretch(7, 1)
>>>>>>> origin/master

        self.retranslateUi(fastControls)
        QtCore.QMetaObject.connectSlotsByName(fastControls)

    def retranslateUi(self, fastControls):
        fastControls.setWindowTitle(QtGui.QApplication.translate("fastControls", "Form", None))
        self.checkinTypeLabel.setText(QtGui.QApplication.translate("fastControls", "Checkin Type:", None))
        self.checkinTypeComboBox.setItemText(0, QtGui.QApplication.translate("fastControls", "A File", None))
        self.checkinTypeComboBox.setItemText(1, QtGui.QApplication.translate("fastControls", "A Sequence", None))
        self.checkinTypeComboBox.setItemText(2, QtGui.QApplication.translate("fastControls", "A Directory", None))
        self.checkinTypeComboBox.setItemText(3, QtGui.QApplication.translate("fastControls", "Miltiple Individual Files", None))
        self.checkinTypeComboBox.setItemText(4, QtGui.QApplication.translate("fastControls", "Work Area", None))
<<<<<<< HEAD
        self.explicitFilenameLabel.setText(QtGui.QApplication.translate("fastControls", "Explicit Filename:", None))
=======
>>>>>>> origin/master
        self.processLabel.setText(QtGui.QApplication.translate("fastControls", "Process:", None))
        self.contextLabel.setText(QtGui.QApplication.translate("fastControls", "Context:", None))

