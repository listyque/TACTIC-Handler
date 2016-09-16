# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'conf\ui_checkinPage.ui'
#
# Created: Sun Sep 11 00:16:48 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_checkinPageWidget(object):
    def setupUi(self, checkinPageWidget):
        checkinPageWidget.setObjectName("checkinPageWidget")
        self.checkinPageWidgetLayout = QtGui.QVBoxLayout(checkinPageWidget)
        self.checkinPageWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.checkinPageWidgetLayout.setObjectName("checkinPageWidgetLayout")
        self.customRepoPathsGroupBox = QtGui.QGroupBox(checkinPageWidget)
        self.customRepoPathsGroupBox.setFlat(True)
        self.customRepoPathsGroupBox.setObjectName("customRepoPathsGroupBox")
        self.customRepoPathsLayout = QtGui.QGridLayout(self.customRepoPathsGroupBox)
        self.customRepoPathsLayout.setSpacing(6)
        self.customRepoPathsLayout.setContentsMargins(0, -1, 0, -1)
        self.customRepoPathsLayout.setObjectName("customRepoPathsLayout")
        self.label_7 = QtGui.QLabel(self.customRepoPathsGroupBox)
        self.label_7.setObjectName("label_7")
        self.customRepoPathsLayout.addWidget(self.label_7, 0, 0, 1, 1)
        self.customRepoDirColorToolButton = QtGui.QToolButton(self.customRepoPathsGroupBox)
        self.customRepoDirColorToolButton.setMaximumSize(QtCore.QSize(20, 20))
        self.customRepoDirColorToolButton.setStyleSheet("QToolButton {\n"
"    border: 1px solid rgb(128, 128, 128);\n"
"    border-radius: 4px;\n"
"    background-color:  rgb(64, 64, 64);\n"
"}\n"
"QToolButton:pressed {\n"
"    background-color: rgb(44, 44, 44);\n"
"}")
        self.customRepoDirColorToolButton.setChecked(False)
        self.customRepoDirColorToolButton.setObjectName("customRepoDirColorToolButton")
        self.customRepoPathsLayout.addWidget(self.customRepoDirColorToolButton, 0, 1, 1, 1)
        self.customRepoDirNameLineEdit = QtGui.QLineEdit(self.customRepoPathsGroupBox)
        self.customRepoDirNameLineEdit.setObjectName("customRepoDirNameLineEdit")
        self.customRepoPathsLayout.addWidget(self.customRepoDirNameLineEdit, 0, 2, 1, 3)
        self.label_8 = QtGui.QLabel(self.customRepoPathsGroupBox)
        self.label_8.setObjectName("label_8")
        self.customRepoPathsLayout.addWidget(self.label_8, 1, 0, 1, 1)
        self.customRepoDirPathLineEdit = QtGui.QLineEdit(self.customRepoPathsGroupBox)
        self.customRepoDirPathLineEdit.setObjectName("customRepoDirPathLineEdit")
        self.customRepoPathsLayout.addWidget(self.customRepoDirPathLineEdit, 1, 1, 1, 4)
        self.customRepoComboBox = QtGui.QComboBox(self.customRepoPathsGroupBox)
        self.customRepoComboBox.setObjectName("customRepoComboBox")
        self.customRepoPathsLayout.addWidget(self.customRepoComboBox, 2, 0, 1, 1)
        self.addCustomRepoToListPushButton = QtGui.QPushButton(self.customRepoPathsGroupBox)
        self.addCustomRepoToListPushButton.setObjectName("addCustomRepoToListPushButton")
        self.customRepoPathsLayout.addWidget(self.addCustomRepoToListPushButton, 2, 1, 1, 2)
        self.editCustomRepoPushButton = QtGui.QPushButton(self.customRepoPathsGroupBox)
        self.editCustomRepoPushButton.setObjectName("editCustomRepoPushButton")
        self.customRepoPathsLayout.addWidget(self.editCustomRepoPushButton, 2, 3, 1, 1)
        self.deleteCustomRepoPushButton = QtGui.QPushButton(self.customRepoPathsGroupBox)
        self.deleteCustomRepoPushButton.setObjectName("deleteCustomRepoPushButton")
        self.customRepoPathsLayout.addWidget(self.deleteCustomRepoPushButton, 2, 4, 1, 1)
        self.customRepoCheckBox = QtGui.QCheckBox(self.customRepoPathsGroupBox)
        self.customRepoCheckBox.setObjectName("customRepoCheckBox")
        self.customRepoPathsLayout.addWidget(self.customRepoCheckBox, 3, 0, 1, 1)
        self.customRepoTreeWidget = QtGui.QTreeWidget(self.customRepoPathsGroupBox)
        self.customRepoTreeWidget.setStyleSheet("QTreeView::item {\n"
"    padding: 2px;\n"
"}")
        self.customRepoTreeWidget.setIndentation(0)
        self.customRepoTreeWidget.setRootIsDecorated(False)
        self.customRepoTreeWidget.setObjectName("customRepoTreeWidget")
        self.customRepoPathsLayout.addWidget(self.customRepoTreeWidget, 4, 0, 1, 5)
        self.checkinPageWidgetLayout.addWidget(self.customRepoPathsGroupBox)
        self.defaultRepoPathsGroupBox = QtGui.QGroupBox(checkinPageWidget)
        self.defaultRepoPathsGroupBox.setFlat(True)
        self.defaultRepoPathsGroupBox.setObjectName("defaultRepoPathsGroupBox")
        self.defaultRepoPathsLayout = QtGui.QGridLayout(self.defaultRepoPathsGroupBox)
        self.defaultRepoPathsLayout.setSpacing(6)
        self.defaultRepoPathsLayout.setContentsMargins(0, 9, 0, 0)
        self.defaultRepoPathsLayout.setObjectName("defaultRepoPathsLayout")
        self.assetBaseDirPathLineEdit = QtGui.QLineEdit(self.defaultRepoPathsGroupBox)
        self.assetBaseDirPathLineEdit.setObjectName("assetBaseDirPathLineEdit")
        self.defaultRepoPathsLayout.addWidget(self.assetBaseDirPathLineEdit, 0, 3, 1, 1)
        self.handoffDirPathLineEdit = QtGui.QLineEdit(self.defaultRepoPathsGroupBox)
        self.handoffDirPathLineEdit.setObjectName("handoffDirPathLineEdit")
        self.defaultRepoPathsLayout.addWidget(self.handoffDirPathLineEdit, 4, 2, 1, 2)
        self.sandboxDirPathLineEdit = QtGui.QLineEdit(self.defaultRepoPathsGroupBox)
        self.sandboxDirPathLineEdit.setObjectName("sandboxDirPathLineEdit")
        self.defaultRepoPathsLayout.addWidget(self.sandboxDirPathLineEdit, 1, 3, 1, 1)
        self.localRepoDirPathLineEdit = QtGui.QLineEdit(self.defaultRepoPathsGroupBox)
        self.localRepoDirPathLineEdit.setObjectName("localRepoDirPathLineEdit")
        self.defaultRepoPathsLayout.addWidget(self.localRepoDirPathLineEdit, 2, 3, 1, 1)
        self.clientRepoDirPathLineEdit = QtGui.QLineEdit(self.defaultRepoPathsGroupBox)
        self.clientRepoDirPathLineEdit.setObjectName("clientRepoDirPathLineEdit")
        self.defaultRepoPathsLayout.addWidget(self.clientRepoDirPathLineEdit, 3, 3, 1, 1)
        self.assetBaseDirCheckBox = QtGui.QCheckBox(self.defaultRepoPathsGroupBox)
        self.assetBaseDirCheckBox.setChecked(True)
        self.assetBaseDirCheckBox.setObjectName("assetBaseDirCheckBox")
        self.defaultRepoPathsLayout.addWidget(self.assetBaseDirCheckBox, 0, 0, 1, 1)
        self.sandboxCheckBox = QtGui.QCheckBox(self.defaultRepoPathsGroupBox)
        self.sandboxCheckBox.setObjectName("sandboxCheckBox")
        self.defaultRepoPathsLayout.addWidget(self.sandboxCheckBox, 1, 0, 1, 1)
        self.localRepoCheckBox = QtGui.QCheckBox(self.defaultRepoPathsGroupBox)
        self.localRepoCheckBox.setChecked(True)
        self.localRepoCheckBox.setObjectName("localRepoCheckBox")
        self.defaultRepoPathsLayout.addWidget(self.localRepoCheckBox, 2, 0, 1, 1)
        self.clientRepoCheckBox = QtGui.QCheckBox(self.defaultRepoPathsGroupBox)
        self.clientRepoCheckBox.setObjectName("clientRepoCheckBox")
        self.defaultRepoPathsLayout.addWidget(self.clientRepoCheckBox, 3, 0, 1, 1)
        self.handoffCheckBox = QtGui.QCheckBox(self.defaultRepoPathsGroupBox)
        self.handoffCheckBox.setObjectName("handoffCheckBox")
        self.defaultRepoPathsLayout.addWidget(self.handoffCheckBox, 4, 0, 1, 1)
        self.assetBaseDirNameLineEdit = QtGui.QLineEdit(self.defaultRepoPathsGroupBox)
        self.assetBaseDirNameLineEdit.setObjectName("assetBaseDirNameLineEdit")
        self.defaultRepoPathsLayout.addWidget(self.assetBaseDirNameLineEdit, 0, 2, 1, 1)
        self.sandboxDirNameLineEdit = QtGui.QLineEdit(self.defaultRepoPathsGroupBox)
        self.sandboxDirNameLineEdit.setObjectName("sandboxDirNameLineEdit")
        self.defaultRepoPathsLayout.addWidget(self.sandboxDirNameLineEdit, 1, 2, 1, 1)
        self.localRepoDirNameLineEdit = QtGui.QLineEdit(self.defaultRepoPathsGroupBox)
        self.localRepoDirNameLineEdit.setObjectName("localRepoDirNameLineEdit")
        self.defaultRepoPathsLayout.addWidget(self.localRepoDirNameLineEdit, 2, 2, 1, 1)
        self.clientRepoDirNameLineEdit = QtGui.QLineEdit(self.defaultRepoPathsGroupBox)
        self.clientRepoDirNameLineEdit.setObjectName("clientRepoDirNameLineEdit")
        self.defaultRepoPathsLayout.addWidget(self.clientRepoDirNameLineEdit, 3, 2, 1, 1)
        self.assetBaseDirColorToolButton = QtGui.QToolButton(self.defaultRepoPathsGroupBox)
        self.assetBaseDirColorToolButton.setMaximumSize(QtCore.QSize(20, 20))
        self.assetBaseDirColorToolButton.setStyleSheet("QToolButton {\n"
"    border: 1px solid rgb(128, 128, 128);\n"
"    border-radius: 4px;\n"
"    background-color:  rgb(96, 96, 96);\n"
"}\n"
"QToolButton:pressed {\n"
"    background-color: rgb(64, 64, 64);\n"
"}")
        self.assetBaseDirColorToolButton.setChecked(False)
        self.assetBaseDirColorToolButton.setObjectName("assetBaseDirColorToolButton")
        self.defaultRepoPathsLayout.addWidget(self.assetBaseDirColorToolButton, 0, 1, 1, 1)
        self.sandboxDirColorToolButton = QtGui.QToolButton(self.defaultRepoPathsGroupBox)
        self.sandboxDirColorToolButton.setMaximumSize(QtCore.QSize(20, 20))
        self.sandboxDirColorToolButton.setStyleSheet("QToolButton {\n"
"    border: 1px solid rgb(128, 128, 128);\n"
"    border-radius: 4px;\n"
"    background-color:  rgb(128, 64, 64);\n"
"}\n"
"QToolButton:pressed {\n"
"    background-color: rgb(108, 44, 44);\n"
"}")
        self.sandboxDirColorToolButton.setChecked(False)
        self.sandboxDirColorToolButton.setObjectName("sandboxDirColorToolButton")
        self.defaultRepoPathsLayout.addWidget(self.sandboxDirColorToolButton, 1, 1, 1, 1)
        self.localRepoDirColorToolButton = QtGui.QToolButton(self.defaultRepoPathsGroupBox)
        self.localRepoDirColorToolButton.setMaximumSize(QtCore.QSize(20, 20))
        self.localRepoDirColorToolButton.setStyleSheet("QToolButton {\n"
"    border: 1px solid rgb(128, 128, 128);\n"
"    border-radius: 4px;\n"
"    background-color:  rgb(255, 140, 40);\n"
"}\n"
"QToolButton:pressed {\n"
"    background-color: rgb(235, 120, 20);\n"
"}")
        self.localRepoDirColorToolButton.setChecked(False)
        self.localRepoDirColorToolButton.setObjectName("localRepoDirColorToolButton")
        self.defaultRepoPathsLayout.addWidget(self.localRepoDirColorToolButton, 2, 1, 1, 1)
        self.clientRepoDirColorToolButton = QtGui.QToolButton(self.defaultRepoPathsGroupBox)
        self.clientRepoDirColorToolButton.setMaximumSize(QtCore.QSize(20, 20))
        self.clientRepoDirColorToolButton.setStyleSheet("QToolButton {\n"
"    border: 1px solid rgb(128, 128, 128);\n"
"    border-radius: 4px;\n"
"    background-color:  rgb(31, 143, 0);\n"
"}\n"
"QToolButton:pressed {\n"
"    background-color: rgb(11, 123, 0);\n"
"}")
        self.clientRepoDirColorToolButton.setChecked(False)
        self.clientRepoDirColorToolButton.setObjectName("clientRepoDirColorToolButton")
        self.defaultRepoPathsLayout.addWidget(self.clientRepoDirColorToolButton, 3, 1, 1, 1)
        self.checkinPageWidgetLayout.addWidget(self.defaultRepoPathsGroupBox)
        self.checkinMiscOpitionsGroupBox = QtGui.QGroupBox(checkinPageWidget)
        self.checkinMiscOpitionsGroupBox.setFlat(True)
        self.checkinMiscOpitionsGroupBox.setObjectName("checkinMiscOpitionsGroupBox")
        self.checkinMiscOptionsLayout = QtGui.QGridLayout(self.checkinMiscOpitionsGroupBox)
        self.checkinMiscOptionsLayout.setContentsMargins(0, -1, 0, 0)
        self.checkinMiscOptionsLayout.setObjectName("checkinMiscOptionsLayout")
        self.doubleClickSaveCheckBox = QtGui.QCheckBox(self.checkinMiscOpitionsGroupBox)
        self.doubleClickSaveCheckBox.setObjectName("doubleClickSaveCheckBox")
        self.checkinMiscOptionsLayout.addWidget(self.doubleClickSaveCheckBox, 0, 0, 1, 1)
        self.versionsSeparateCheckinCheckBox = QtGui.QCheckBox(self.checkinMiscOpitionsGroupBox)
        self.versionsSeparateCheckinCheckBox.setObjectName("versionsSeparateCheckinCheckBox")
        self.checkinMiscOptionsLayout.addWidget(self.versionsSeparateCheckinCheckBox, 1, 0, 1, 1)
        self.checkinPageWidgetLayout.addWidget(self.checkinMiscOpitionsGroupBox)

        self.retranslateUi(checkinPageWidget)
        QtCore.QMetaObject.connectSlotsByName(checkinPageWidget)

    def retranslateUi(self, checkinPageWidget):
        self.customRepoPathsGroupBox.setTitle(QtGui.QApplication.translate("checkinPageWidget", "Custom repository path:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_7.setText(QtGui.QApplication.translate("checkinPageWidget", "Custom Repo name:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_8.setText(QtGui.QApplication.translate("checkinPageWidget", "Repo path:", None, QtGui.QApplication.UnicodeUTF8))
        self.addCustomRepoToListPushButton.setText(QtGui.QApplication.translate("checkinPageWidget", "Add", None, QtGui.QApplication.UnicodeUTF8))
        self.editCustomRepoPushButton.setText(QtGui.QApplication.translate("checkinPageWidget", "Edit", None, QtGui.QApplication.UnicodeUTF8))
        self.deleteCustomRepoPushButton.setText(QtGui.QApplication.translate("checkinPageWidget", "Delete", None, QtGui.QApplication.UnicodeUTF8))
        self.customRepoCheckBox.setText(QtGui.QApplication.translate("checkinPageWidget", "Show custom repos", None, QtGui.QApplication.UnicodeUTF8))
        self.customRepoTreeWidget.headerItem().setText(0, QtGui.QApplication.translate("checkinPageWidget", "Visible", None, QtGui.QApplication.UnicodeUTF8))
        self.customRepoTreeWidget.headerItem().setText(1, QtGui.QApplication.translate("checkinPageWidget", "Color", None, QtGui.QApplication.UnicodeUTF8))
        self.customRepoTreeWidget.headerItem().setText(2, QtGui.QApplication.translate("checkinPageWidget", "Name", None, QtGui.QApplication.UnicodeUTF8))
        self.customRepoTreeWidget.headerItem().setText(3, QtGui.QApplication.translate("checkinPageWidget", "Path", None, QtGui.QApplication.UnicodeUTF8))
        self.defaultRepoPathsGroupBox.setTitle(QtGui.QApplication.translate("checkinPageWidget", "Current repository paths:", None, QtGui.QApplication.UnicodeUTF8))
        self.assetBaseDirCheckBox.setText(QtGui.QApplication.translate("checkinPageWidget", "Asset base dir:", None, QtGui.QApplication.UnicodeUTF8))
        self.sandboxCheckBox.setText(QtGui.QApplication.translate("checkinPageWidget", "Sandbox dir:", None, QtGui.QApplication.UnicodeUTF8))
        self.localRepoCheckBox.setText(QtGui.QApplication.translate("checkinPageWidget", "Local repo dir:", None, QtGui.QApplication.UnicodeUTF8))
        self.clientRepoCheckBox.setText(QtGui.QApplication.translate("checkinPageWidget", "Client repo dir:", None, QtGui.QApplication.UnicodeUTF8))
        self.handoffCheckBox.setText(QtGui.QApplication.translate("checkinPageWidget", "Handoff dir:", None, QtGui.QApplication.UnicodeUTF8))
        self.checkinMiscOpitionsGroupBox.setTitle(QtGui.QApplication.translate("checkinPageWidget", "Misc:", None, QtGui.QApplication.UnicodeUTF8))
        self.doubleClickSaveCheckBox.setText(QtGui.QApplication.translate("checkinPageWidget", "DoubleClick for Save", None, QtGui.QApplication.UnicodeUTF8))
        self.versionsSeparateCheckinCheckBox.setText(QtGui.QApplication.translate("checkinPageWidget", "Display versions separate", None, QtGui.QApplication.UnicodeUTF8))

