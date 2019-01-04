# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'misc/ui_create_update.ui'
#
# Created: Thu Apr 27 14:15:16 2017
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore


class Ui_createUpdateDialog(object):
    def setupUi(self, createUpdateDialog):
        createUpdateDialog.setObjectName("createUpdateDialog")
        createUpdateDialog.resize(473, 396)
        createUpdateDialog.setSizeGripEnabled(True)
        createUpdateDialog.setModal(True)
        self.formLayout = QtGui.QFormLayout(createUpdateDialog)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName("formLayout")
        self.versionLabel = QtGui.QLabel(createUpdateDialog)
        self.versionLabel.setObjectName("versionLabel")
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.versionLabel)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.majorSpinBox = QtGui.QSpinBox(createUpdateDialog)
        self.majorSpinBox.setObjectName("majorSpinBox")
        self.horizontalLayout.addWidget(self.majorSpinBox)
        self.minorSpinBox = QtGui.QSpinBox(createUpdateDialog)
        self.minorSpinBox.setObjectName("minorSpinBox")
        self.horizontalLayout.addWidget(self.minorSpinBox)
        self.buildSpinBox = QtGui.QSpinBox(createUpdateDialog)
        self.buildSpinBox.setObjectName("buildSpinBox")
        self.horizontalLayout.addWidget(self.buildSpinBox)
        self.revisionSpinBox = QtGui.QSpinBox(createUpdateDialog)
        self.revisionSpinBox.setObjectName("revisionSpinBox")
        self.horizontalLayout.addWidget(self.revisionSpinBox)
        self.formLayout.setLayout(0, QtGui.QFormLayout.FieldRole, self.horizontalLayout)
        self.dateLabel = QtGui.QLabel(createUpdateDialog)
        self.dateLabel.setObjectName("dateLabel")
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.dateLabel)
        self.changesLabel = QtGui.QLabel(createUpdateDialog)
        self.changesLabel.setObjectName("changesLabel")
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.changesLabel)
        self.changesPlainTextEdit = QtGui.QPlainTextEdit(createUpdateDialog)
        self.changesPlainTextEdit.setObjectName("changesPlainTextEdit")
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.changesPlainTextEdit)
        self.miscLabel = QtGui.QLabel(createUpdateDialog)
        self.miscLabel.setObjectName("miscLabel")
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.miscLabel)
        self.miscPlainTextEdit = QtGui.QPlainTextEdit(createUpdateDialog)
        self.miscPlainTextEdit.setObjectName("miscPlainTextEdit")
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.miscPlainTextEdit)
        self.createUpdatePushButton = QtGui.QPushButton(createUpdateDialog)
        self.createUpdatePushButton.setObjectName("createUpdatePushButton")
        self.formLayout.setWidget(4, QtGui.QFormLayout.SpanningRole, self.createUpdatePushButton)
        self.dateEdit = QtGui.QDateEdit(createUpdateDialog)
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.setObjectName("dateEdit")
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.dateEdit)

        self.retranslateUi(createUpdateDialog)
        QtCore.QMetaObject.connectSlotsByName(createUpdateDialog)

    def retranslateUi(self, createUpdateDialog):
        createUpdateDialog.setWindowTitle(QtGui.QApplication.translate("createUpdateDialog", "Creating new Update", None))
        self.versionLabel.setText(QtGui.QApplication.translate("createUpdateDialog", "Version:", None))
        self.dateLabel.setText(QtGui.QApplication.translate("createUpdateDialog", "Date:", None))
        self.changesLabel.setText(QtGui.QApplication.translate("createUpdateDialog", "Changes:", None))
        self.miscLabel.setText(QtGui.QApplication.translate("createUpdateDialog", "Misc:", None))
        self.createUpdatePushButton.setText(QtGui.QApplication.translate("createUpdateDialog", "Create Update", None))
        self.dateEdit.setDisplayFormat(QtGui.QApplication.translate("createUpdateDialog", "MM.dd.yyyy", None))

