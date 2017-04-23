# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'checkin_out\ui_description_widget.ui'
#
# Created: Tue Mar 21 23:24:44 2017
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_descriptionWidget(object):
    def setupUi(self, descriptionWidget):
        descriptionWidget.setObjectName("descriptionWidget")
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(descriptionWidget.sizePolicy().hasHeightForWidth())
        descriptionWidget.setSizePolicy(sizePolicy)
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
        descriptionWidget.setWindowTitle(QtGui.QApplication.translate("descriptionWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))

