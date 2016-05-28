# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_checkin_options.ui'
#
# Created: Mon May 16 18:48:26 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_checkinOptionsGroupBox(object):
    def setupUi(self, checkinOptionsGroupBox):
        checkinOptionsGroupBox.setObjectName("checkinOptionsGroupBox")
        checkinOptionsGroupBox.setFlat(True)
        self.gridLayout = QtGui.QGridLayout(checkinOptionsGroupBox)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setContentsMargins(0, 0, 0, 4)
        self.gridLayout.setObjectName("gridLayout")
        self.createMayaDirsCheckBox = QtGui.QCheckBox(checkinOptionsGroupBox)
        self.createMayaDirsCheckBox.setChecked(True)
        self.createMayaDirsCheckBox.setObjectName("createMayaDirsCheckBox")
        self.gridLayout.addWidget(self.createMayaDirsCheckBox, 0, 0, 1, 1)
        self.createPlayblastCheckBox = QtGui.QCheckBox(checkinOptionsGroupBox)
        self.createPlayblastCheckBox.setChecked(True)
        self.createPlayblastCheckBox.setObjectName("createPlayblastCheckBox")
        self.gridLayout.addWidget(self.createPlayblastCheckBox, 0, 1, 1, 1)
        self.askBeforeSaveCheckBox = QtGui.QCheckBox(checkinOptionsGroupBox)
        self.askBeforeSaveCheckBox.setChecked(True)
        self.askBeforeSaveCheckBox.setObjectName("askBeforeSaveCheckBox")
        self.gridLayout.addWidget(self.askBeforeSaveCheckBox, 0, 2, 1, 1)
        self.saveAsDefaultsPushButton = QtGui.QPushButton(checkinOptionsGroupBox)
        self.saveAsDefaultsPushButton.setDefault(True)
        self.saveAsDefaultsPushButton.setObjectName("saveAsDefaultsPushButton")
        self.gridLayout.addWidget(self.saveAsDefaultsPushButton, 0, 3, 1, 1)
        self.label = QtGui.QLabel(checkinOptionsGroupBox)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.repositoryComboBox = QtGui.QComboBox(checkinOptionsGroupBox)
        self.repositoryComboBox.setObjectName("repositoryComboBox")
        self.gridLayout.addWidget(self.repositoryComboBox, 1, 1, 1, 2)
        self.updateVersionlessCheckBox = QtGui.QCheckBox(checkinOptionsGroupBox)
        self.updateVersionlessCheckBox.setChecked(True)
        self.updateVersionlessCheckBox.setObjectName("updateVersionlessCheckBox")
        self.gridLayout.addWidget(self.updateVersionlessCheckBox, 1, 3, 1, 1)

        self.retranslateUi(checkinOptionsGroupBox)
        QtCore.QMetaObject.connectSlotsByName(checkinOptionsGroupBox)

    def retranslateUi(self, checkinOptionsGroupBox):
        checkinOptionsGroupBox.setWindowTitle(QtGui.QApplication.translate("checkinOptionsGroupBox", "GroupBox", None, QtGui.QApplication.UnicodeUTF8))
        checkinOptionsGroupBox.setTitle(QtGui.QApplication.translate("checkinOptionsGroupBox", "Checkin Options:", None, QtGui.QApplication.UnicodeUTF8))
        self.createMayaDirsCheckBox.setText(QtGui.QApplication.translate("checkinOptionsGroupBox", "Create Maya Dirs", None, QtGui.QApplication.UnicodeUTF8))
        self.createPlayblastCheckBox.setText(QtGui.QApplication.translate("checkinOptionsGroupBox", "Create playblast", None, QtGui.QApplication.UnicodeUTF8))
        self.askBeforeSaveCheckBox.setText(QtGui.QApplication.translate("checkinOptionsGroupBox", "Ask before save", None, QtGui.QApplication.UnicodeUTF8))
        self.saveAsDefaultsPushButton.setText(QtGui.QApplication.translate("checkinOptionsGroupBox", "Save as Defaults", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("checkinOptionsGroupBox", "Checkin repository:", None, QtGui.QApplication.UnicodeUTF8))
        self.updateVersionlessCheckBox.setText(QtGui.QApplication.translate("checkinOptionsGroupBox", "Update Versionless", None, QtGui.QApplication.UnicodeUTF8))

