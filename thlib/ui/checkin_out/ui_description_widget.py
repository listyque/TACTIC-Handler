# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'checkin_out\ui_description_widget.ui'
#
# Created: Sat Oct  5 00:17:19 2019
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

class Ui_descriptionWidget(object):
    def setupUi(self, descriptionWidget):
        descriptionWidget.setObjectName("descriptionWidget")
        self.verticalLayout = QtGui.QVBoxLayout(descriptionWidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.editorLayout = QtGui.QVBoxLayout()
        self.editorLayout.setSpacing(0)
        self.editorLayout.setObjectName("editorLayout")
        self.verticalLayout.addLayout(self.editorLayout)
        self.descriptionTextEdit = QtGui.QTextEdit(descriptionWidget)
        self.descriptionTextEdit.setObjectName("descriptionTextEdit")
        self.verticalLayout.addWidget(self.descriptionTextEdit)
        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(descriptionWidget)
        QtCore.QMetaObject.connectSlotsByName(descriptionWidget)

    def retranslateUi(self, descriptionWidget):
        descriptionWidget.setWindowTitle(u"Form")

