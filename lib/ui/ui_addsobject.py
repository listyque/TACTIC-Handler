# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_addsobject.ui'
#
# Created: Sun Dec 13 12:53:37 2015
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_addSObjectForm(object):
    def setupUi(self, addSObjectForm):
        addSObjectForm.setObjectName("addSObjectForm")
        addSObjectForm.setWindowModality(QtCore.Qt.ApplicationModal)
        addSObjectForm.resize(500, 350)
        addSObjectForm.setMinimumSize(QtCore.QSize(500, 350))
        addSObjectForm.setAcceptDrops(True)
        addSObjectForm.setWindowTitle("Adding New items to ")
        addSObjectForm.setToolTip("")
        addSObjectForm.setStatusTip("")
        addSObjectForm.setAccessibleName("")
        addSObjectForm.setAccessibleDescription("")
        addSObjectForm.setWindowFilePath("")
        self.gridLayout = QtGui.QGridLayout(addSObjectForm)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtGui.QLabel(addSObjectForm)
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTop|QtCore.Qt.AlignTrailing)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_2 = QtGui.QLabel(addSObjectForm)
        self.label_2.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTop|QtCore.Qt.AlignTrailing)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.previewImageLineEdit = QtGui.QLineEdit(addSObjectForm)
        self.previewImageLineEdit.setObjectName("previewImageLineEdit")
        self.gridLayout.addWidget(self.previewImageLineEdit, 0, 1, 1, 1)
        self.browseImageButton = QtGui.QPushButton(addSObjectForm)
        self.browseImageButton.setObjectName("browseImageButton")
        self.gridLayout.addWidget(self.browseImageButton, 0, 2, 1, 1)
        self.nameLineEdit = QtGui.QLineEdit(addSObjectForm)
        self.nameLineEdit.setObjectName("nameLineEdit")
        self.gridLayout.addWidget(self.nameLineEdit, 1, 1, 1, 2)
        self.label_3 = QtGui.QLabel(addSObjectForm)
        self.label_3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTop|QtCore.Qt.AlignTrailing)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.label_4 = QtGui.QLabel(addSObjectForm)
        self.label_4.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTop|QtCore.Qt.AlignTrailing)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 3, 0, 1, 1)
        self.descriptionTextEdit = QtGui.QPlainTextEdit(addSObjectForm)
        self.descriptionTextEdit.setTabChangesFocus(True)
        self.descriptionTextEdit.setObjectName("descriptionTextEdit")
        self.gridLayout.addWidget(self.descriptionTextEdit, 2, 1, 1, 2)
        self.keywordsTextEdit = QtGui.QPlainTextEdit(addSObjectForm)
        self.keywordsTextEdit.setTabChangesFocus(True)
        self.keywordsTextEdit.setObjectName("keywordsTextEdit")
        self.gridLayout.addWidget(self.keywordsTextEdit, 3, 1, 1, 2)
        self.cancelButton = QtGui.QPushButton(addSObjectForm)
        self.cancelButton.setObjectName("cancelButton")
        self.gridLayout.addWidget(self.cancelButton, 4, 2, 1, 1)
        self.addNewButton = QtGui.QPushButton(addSObjectForm)
        self.addNewButton.setObjectName("addNewButton")
        self.gridLayout.addWidget(self.addNewButton, 4, 1, 1, 1)

        self.retranslateUi(addSObjectForm)
        QtCore.QMetaObject.connectSlotsByName(addSObjectForm)
        addSObjectForm.setTabOrder(self.previewImageLineEdit, self.browseImageButton)
        addSObjectForm.setTabOrder(self.browseImageButton, self.nameLineEdit)
        addSObjectForm.setTabOrder(self.nameLineEdit, self.descriptionTextEdit)
        addSObjectForm.setTabOrder(self.descriptionTextEdit, self.keywordsTextEdit)
        addSObjectForm.setTabOrder(self.keywordsTextEdit, self.addNewButton)
        addSObjectForm.setTabOrder(self.addNewButton, self.cancelButton)

    def retranslateUi(self, addSObjectForm):
        self.label.setText(QtGui.QApplication.translate("addSObjectForm", "Preview Image:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("addSObjectForm", "Name:", None, QtGui.QApplication.UnicodeUTF8))
        self.browseImageButton.setText(QtGui.QApplication.translate("addSObjectForm", "Browse", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("addSObjectForm", "Description:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("addSObjectForm", "Keywords:", None, QtGui.QApplication.UnicodeUTF8))
        self.cancelButton.setText(QtGui.QApplication.translate("addSObjectForm", "Cancel", None, QtGui.QApplication.UnicodeUTF8))
        self.addNewButton.setText(QtGui.QApplication.translate("addSObjectForm", "Add New", None, QtGui.QApplication.UnicodeUTF8))

