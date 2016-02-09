# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_check.ui'
#
# Created: Tue Jan 05 14:28:34 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_checkOut(object):
    def setupUi(self, checkOut):
        checkOut.setObjectName("checkOut")
        checkOut.resize(803, 667)
        checkOut.setMinimumSize(QtCore.QSize(400, 250))
        self.checkOutMainLayout = QtGui.QVBoxLayout(checkOut)
        self.checkOutMainLayout.setSpacing(0)
        self.checkOutMainLayout.setContentsMargins(0, 0, 0, 0)
        self.checkOutMainLayout.setObjectName("checkOutMainLayout")
        self.tabsSplitter = QtGui.QSplitter(checkOut)
        self.tabsSplitter.setOrientation(QtCore.Qt.Vertical)
        self.tabsSplitter.setObjectName("tabsSplitter")
        self.checkOutTabWidget = QtGui.QTabWidget(self.tabsSplitter)
        self.checkOutTabWidget.setMaximumSize(QtCore.QSize(16777215, 20))
        self.checkOutTabWidget.setStyleSheet("QTabBar{\n"
"    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(0,0,0, 0), stop: 1 rgba(0, 0, 0, 0));\n"
"}")
        self.checkOutTabWidget.setTabPosition(QtGui.QTabWidget.North)
        self.checkOutTabWidget.setDocumentMode(True)
        self.checkOutTabWidget.setObjectName("checkOutTabWidget")
        self.commentsSplitter = QtGui.QSplitter(self.tabsSplitter)
        self.commentsSplitter.setOrientation(QtCore.Qt.Horizontal)
        self.commentsSplitter.setObjectName("commentsSplitter")
        self.gridLayoutWidget = QtGui.QWidget(self.commentsSplitter)
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.resultsLayout = QtGui.QGridLayout(self.gridLayoutWidget)
        self.resultsLayout.setContentsMargins(0, 0, 0, 0)
        self.resultsLayout.setObjectName("resultsLayout")
        self.searchLineEdit = QtGui.QLineEdit(self.gridLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.searchLineEdit.setFont(font)
        self.searchLineEdit.setStyleSheet("QLineEdit {\n"
"    color: rgb(192, 192, 192);\n"
"    border: 2px solid darkgray;\n"
"    border-radius: 10px;\n"
"    show-decoration-selected: 1;\n"
"    padding: 0px 8px;\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(128, 128, 128, 255), stop:1 rgba(64, 64,64, 255));\n"
"    background-position: bottom left;\n"
"    background-image: url(\":/ui_check/gliph/search_16.png\");\n"
"    background-repeat: fixed;\n"
"    selection-background-color: darkgray;\n"
"    padding-left: 15px;\n"
"}\n"
"QLineEdit:hover{\n"
"    color: white;\n"
"    background-image: url(\":/ui_check/gliph/searchHover_16.png\");\n"
"}")
        self.searchLineEdit.setFrame(False)
        self.searchLineEdit.setObjectName("searchLineEdit")
        self.resultsLayout.addWidget(self.searchLineEdit, 0, 0, 1, 1)
        self.contextComboBox = QtGui.QComboBox(self.gridLayoutWidget)
        self.contextComboBox.setMinimumSize(QtCore.QSize(80, 0))
        self.contextComboBox.setEditable(True)
        self.contextComboBox.setInsertPolicy(QtGui.QComboBox.NoInsert)
        self.contextComboBox.setObjectName("contextComboBox")
        self.resultsLayout.addWidget(self.contextComboBox, 0, 1, 1, 1)
        self.resultsGroupBox = QtGui.QGroupBox(self.gridLayoutWidget)
        self.resultsGroupBox.setFlat(True)
        self.resultsGroupBox.setObjectName("resultsGroupBox")
        self.verticalLayout = QtGui.QVBoxLayout(self.resultsGroupBox)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.resultsTreeWidget = QtGui.QTreeWidget(self.resultsGroupBox)
        self.resultsTreeWidget.setTabKeyNavigation(True)
        self.resultsTreeWidget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.resultsTreeWidget.setAllColumnsShowFocus(True)
        self.resultsTreeWidget.setHeaderHidden(True)
        self.resultsTreeWidget.setObjectName("resultsTreeWidget")
        self.resultsTreeWidget.headerItem().setText(0, "1")
        self.verticalLayout.addWidget(self.resultsTreeWidget)
        self.resultsLayout.addWidget(self.resultsGroupBox, 1, 0, 1, 2)
        self.gridLayoutWidget_2 = QtGui.QWidget(self.commentsSplitter)
        self.gridLayoutWidget_2.setObjectName("gridLayoutWidget_2")
        self.commentsLayout = QtGui.QGridLayout(self.gridLayoutWidget_2)
        self.commentsLayout.setSpacing(0)
        self.commentsLayout.setContentsMargins(0, 0, 0, 0)
        self.commentsLayout.setObjectName("commentsLayout")
        self.descriptionSplitter = QtGui.QSplitter(self.gridLayoutWidget_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.descriptionSplitter.sizePolicy().hasHeightForWidth())
        self.descriptionSplitter.setSizePolicy(sizePolicy)
        self.descriptionSplitter.setOrientation(QtCore.Qt.Vertical)
        self.descriptionSplitter.setObjectName("descriptionSplitter")
        self.playblastGroupBox = QtGui.QGroupBox(self.descriptionSplitter)
        self.playblastGroupBox.setFlat(True)
        self.playblastGroupBox.setObjectName("playblastGroupBox")
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.playblastGroupBox)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.imagesSplitter = QtGui.QSplitter(self.playblastGroupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.imagesSplitter.sizePolicy().hasHeightForWidth())
        self.imagesSplitter.setSizePolicy(sizePolicy)
        self.imagesSplitter.setMinimumSize(QtCore.QSize(0, 376))
        self.imagesSplitter.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.imagesSplitter.setOrientation(QtCore.Qt.Vertical)
        self.imagesSplitter.setObjectName("imagesSplitter")
        self.layoutWidget = QtGui.QWidget(self.imagesSplitter)
        self.layoutWidget.setObjectName("layoutWidget")
        self.iconsLayout = QtGui.QVBoxLayout(self.layoutWidget)
        self.iconsLayout.setSpacing(0)
        self.iconsLayout.setContentsMargins(0, 0, 0, 0)
        self.iconsLayout.setObjectName("iconsLayout")
        self.verticalLayoutWidget = QtGui.QWidget(self.imagesSplitter)
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.playblastLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.playblastLayout.setSpacing(0)
        self.playblastLayout.setContentsMargins(0, 0, 0, 0)
        self.playblastLayout.setContentsMargins(0, 0, 0, 0)
        self.playblastLayout.setObjectName("playblastLayout")
        self.verticalLayout_4.addWidget(self.imagesSplitter)
        self.commentsGroupBox = QtGui.QGroupBox(self.descriptionSplitter)
        self.commentsGroupBox.setMaximumSize(QtCore.QSize(16777215, 250))
        self.commentsGroupBox.setFlat(True)
        self.commentsGroupBox.setObjectName("commentsGroupBox")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.commentsGroupBox)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.descriptionTextEdit = QtGui.QTextEdit(self.commentsGroupBox)
        self.descriptionTextEdit.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByKeyboard|QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextBrowserInteraction|QtCore.Qt.TextEditable|QtCore.Qt.TextEditorInteraction|QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.descriptionTextEdit.setObjectName("descriptionTextEdit")
        self.verticalLayout_2.addWidget(self.descriptionTextEdit)
        self.saveDescriprionButton = QtGui.QPushButton(self.commentsGroupBox)
        self.saveDescriprionButton.setObjectName("saveDescriprionButton")
        self.verticalLayout_2.addWidget(self.saveDescriprionButton)
        self.commentsLayout.addWidget(self.descriptionSplitter, 0, 0, 1, 1)
        self.checkOutMainLayout.addWidget(self.tabsSplitter)

        self.retranslateUi(checkOut)
        self.checkOutTabWidget.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(checkOut)
        checkOut.setTabOrder(self.searchLineEdit, self.contextComboBox)
        checkOut.setTabOrder(self.contextComboBox, self.resultsTreeWidget)
        checkOut.setTabOrder(self.resultsTreeWidget, self.saveDescriprionButton)
        checkOut.setTabOrder(self.saveDescriprionButton, self.descriptionTextEdit)

    def retranslateUi(self, checkOut):
        checkOut.setWindowTitle(QtGui.QApplication.translate("checkOut", "Checkout", None, QtGui.QApplication.UnicodeUTF8))
        self.resultsGroupBox.setTitle(QtGui.QApplication.translate("checkOut", "Results:", None, QtGui.QApplication.UnicodeUTF8))
        self.playblastGroupBox.setTitle(QtGui.QApplication.translate("checkOut", "Preview images:", None, QtGui.QApplication.UnicodeUTF8))
        self.commentsGroupBox.setTitle(QtGui.QApplication.translate("checkOut", "Description:", None, QtGui.QApplication.UnicodeUTF8))
        self.saveDescriprionButton.setText(QtGui.QApplication.translate("checkOut", "Save description", None, QtGui.QApplication.UnicodeUTF8))

import resources_rc
