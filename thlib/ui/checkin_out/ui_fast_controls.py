# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'checkin_out\ui_fast_controls.ui'
#
# Created: Sat Oct  5 00:17:20 2019
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_fastControls(object):
    def setupUi(self, fastControls):
        fastControls.setObjectName("fastControls")
        fastControls.resize(806, 30)
        self.horizontalLayout = QtGui.QHBoxLayout(fastControls)
        self.horizontalLayout.setContentsMargins(4, 4, 4, 6)
        self.horizontalLayout.setObjectName("horizontalLayout")
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
        self.explicitFilenameLabel = QtGui.QLabel(fastControls)
        self.explicitFilenameLabel.setObjectName("explicitFilenameLabel")
        self.horizontalLayout.addWidget(self.explicitFilenameLabel)
        self.explicitFilenameLineEdit = QtGui.QLineEdit(fastControls)
        self.explicitFilenameLineEdit.setObjectName("explicitFilenameLineEdit")
        self.horizontalLayout.addWidget(self.explicitFilenameLineEdit)
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
        self.horizontalLayout.setStretch(2, 1)
        self.horizontalLayout.setStretch(4, 1)
        self.horizontalLayout.setStretch(8, 1)

        self.retranslateUi(fastControls)
        QtCore.QMetaObject.connectSlotsByName(fastControls)

    def retranslateUi(self, fastControls):
        fastControls.setWindowTitle(QtGui.QApplication.translate("fastControls", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.checkinTypeLabel.setText(QtGui.QApplication.translate("fastControls", "Checkin Type:", None, QtGui.QApplication.UnicodeUTF8))
        self.checkinTypeComboBox.setItemText(0, QtGui.QApplication.translate("fastControls", "A File", None, QtGui.QApplication.UnicodeUTF8))
        self.checkinTypeComboBox.setItemText(1, QtGui.QApplication.translate("fastControls", "A Sequence", None, QtGui.QApplication.UnicodeUTF8))
        self.checkinTypeComboBox.setItemText(2, QtGui.QApplication.translate("fastControls", "A Directory", None, QtGui.QApplication.UnicodeUTF8))
        self.checkinTypeComboBox.setItemText(3, QtGui.QApplication.translate("fastControls", "Miltiple Individual Files", None, QtGui.QApplication.UnicodeUTF8))
        self.checkinTypeComboBox.setItemText(4, QtGui.QApplication.translate("fastControls", "Work Area", None, QtGui.QApplication.UnicodeUTF8))
        self.explicitFilenameLabel.setText(QtGui.QApplication.translate("fastControls", "Explicit Filename:", None, QtGui.QApplication.UnicodeUTF8))
        self.processLabel.setText(QtGui.QApplication.translate("fastControls", "Process:", None, QtGui.QApplication.UnicodeUTF8))
        self.contextLabel.setText(QtGui.QApplication.translate("fastControls", "Context:", None, QtGui.QApplication.UnicodeUTF8))

